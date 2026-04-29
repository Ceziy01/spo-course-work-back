from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session, joinedload
import shutil, uuid, os

from core.dependencies import get_db, require_any_authenticated, require_admin_or_warehouse_keeper
from db.models.user import Users
from db.models.item import Item
from db.models.warehouse import Warehouse
from db.models.category import Category
from schemas.item import ItemCreate, ItemUpdate, ItemResponse
from services.search_service import ai_search
from db.models.activity_log import ActionType
from services.activity_log import log_action

router = APIRouter(prefix="/items", tags=["items"])

@router.get("/", response_model=List[ItemResponse])
def list_items(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_any_authenticated)]
):
    items = db.query(Item).options(
        joinedload(Item.category),
        joinedload(Item.warehouse)
    ).all()
    result = []
    for item in items:
        item_data = ItemResponse.model_validate(item)
        item_data.category_name = item.category.name if item.category else None
        item_data.warehouse_name = item.warehouse.name if item.warehouse else None
        result.append(item_data)
    return result

@router.post("/", response_model=ItemResponse, status_code=201)
def create_item(
    data: ItemCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_admin_or_warehouse_keeper)],
    req: Request = None
):
    existing = db.query(Item).filter(Item.article == data.article).first()
    if existing:
        raise HTTPException(400, "Товар с таким артикулом уже существует")
    category = db.query(Category).filter(Category.id == data.category_id).first()
    if not category:
        raise HTTPException(400, "Категория не найдена")
    warehouse = db.query(Warehouse).filter(Warehouse.id == data.warehouse_id).first()
    if not warehouse:
        raise HTTPException(400, "Склад не найден")

    item = Item(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)

    log_action(
        db, user, ActionType.ITEM_CREATED,
        entity_type="item", entity_id=item.id,
        entity_name=f"{data.name} (арт. {data.article})",
        ip_address=req.client.host if req else None
    )

    item = db.query(Item).options(joinedload(Item.category), joinedload(Item.warehouse)).filter(Item.id == item.id).first()
    response = ItemResponse.model_validate(item)
    response.category_name = item.category.name
    response.warehouse_name = item.warehouse.name
    return response

@router.patch("/{item_id}", response_model=ItemResponse)
def update_item(
    item_id: int,
    data: ItemUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_admin_or_warehouse_keeper)],
    req: Request = None
):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(404, "Товар не найден")

    update_data = data.model_dump(exclude_unset=True)

    if "article" in update_data and update_data["article"] != item.article:
        existing = db.query(Item).filter(Item.article == update_data["article"], Item.id != item_id).first()
        if existing:
            raise HTTPException(400, "Товар с таким артикулом уже существует")

    if "category_id" in update_data:
        category = db.query(Category).filter(Category.id == update_data["category_id"]).first()
        if not category:
            raise HTTPException(400, "Категория не найдена")

    if "warehouse_id" in update_data:
        warehouse = db.query(Warehouse).filter(Warehouse.id == update_data["warehouse_id"]).first()
        if not warehouse:
            raise HTTPException(400, "Склад не найден")

    changes = {}
    for field, value in update_data.items():
        old_val = getattr(item, field, None)
        if str(old_val) != str(value):
            changes[field] = {"old": old_val, "new": value}
        setattr(item, field, value)

    db.commit()
    db.refresh(item)

    log_action(
        db, user, ActionType.ITEM_UPDATED,
        entity_type="item", entity_id=item.id,
        entity_name=f"{item.name} (арт. {item.article})",
        ip_address=req.client.host if req else None
    )

    item = db.query(Item).options(joinedload(Item.category), joinedload(Item.warehouse)).filter(Item.id == item_id).first()
    response = ItemResponse.model_validate(item)
    response.category_name = item.category.name if item.category else None
    response.warehouse_name = item.warehouse.name if item.warehouse else None
    return response

@router.delete("/{item_id}")
def delete_item(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_admin_or_warehouse_keeper)],
    req: Request = None
):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(404, "Товар не найден")

    log_action(
        db, user, ActionType.ITEM_DELETED,
        entity_type="item", entity_id=item.id,
        entity_name=f"{item.name} (арт. {item.article})",
        ip_address=req.client.host if req else None
    )

    db.delete(item)
    db.commit()
    return {"message": "Товар удалён"}

@router.post("/upload-image")
def upload_image(
    user: Annotated[Users, Depends(require_any_authenticated)],
    file: UploadFile = File(...)
):
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join("images", filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"image_url": f"/images/{filename}"}

@router.get("/search/{query}", response_model=List[ItemResponse])
def search_items(
    query: str,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_any_authenticated)]
):
    items = db.query(Item).options(
        joinedload(Item.category),
        joinedload(Item.warehouse)
    ).all()

    goods = [{"id": item.id, "name": item.name, "category": item.category.name if item.category else ""} for item in items]
    results = ai_search(query, goods)
    item_ids = [r["item"]["id"] for r in results]

    if not item_ids:
        return []

    matched_items = db.query(Item).options(
        joinedload(Item.category),
        joinedload(Item.warehouse)
    ).filter(Item.id.in_(item_ids)).all()

    response = []
    for item in matched_items:
        r = ItemResponse.model_validate(item)
        r.category_name = item.category.name if item.category else None
        r.warehouse_name = item.warehouse.name if item.warehouse else None
        response.append(r)

    return response