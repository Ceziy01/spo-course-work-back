from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from core.dependencies import get_db, require_any_authenticated, require_admin_or_warehouse_keeper
from db.models.user import Users
from db.models.warehouse import Warehouse
from schemas.warehouse import WarehouseCreate, WarehouseUpdate, WarehouseResponse
from db.models.activity_log import ActionType
from services.activity_log import log_action

router = APIRouter(prefix="/warehouses", tags=["warehouses"])

@router.get("/", response_model=List[WarehouseResponse])
def list_warehouses(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_any_authenticated)]
):
    return db.query(Warehouse).all()

@router.post("/", response_model=WarehouseResponse, status_code=201)
def create_warehouse(
    data: WarehouseCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_admin_or_warehouse_keeper)],
    req: Request = None
):
    existing = db.query(Warehouse).filter(Warehouse.name == data.name).first()
    if existing:
        raise HTTPException(400, "Склад с таким названием уже существует")
    warehouse = Warehouse(**data.model_dump())
    db.add(warehouse)
    db.commit()
    db.refresh(warehouse)

    log_action(
        db, user, ActionType.WAREHOUSE_CREATED,
        entity_type="warehouse", entity_id=warehouse.id,
        entity_name=warehouse.name,
        ip_address=req.client.host if req else None
    )

    return warehouse

@router.patch("/{warehouse_id}", response_model=WarehouseResponse)
def update_warehouse(
    warehouse_id: int,
    data: WarehouseUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_admin_or_warehouse_keeper)],
    req: Request = None
):
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(404, "Склад не найден")
    update_data = data.model_dump(exclude_unset=True)
    if "name" in update_data:
        existing = db.query(Warehouse).filter(
            Warehouse.name == update_data["name"],
            Warehouse.id != warehouse_id
        ).first()
        if existing:
            raise HTTPException(400, "Склад с таким названием уже существует")

    changes = {}
    for field, value in update_data.items():
        old_val = getattr(warehouse, field, None)
        if old_val != value:
            changes[field] = {"old": old_val, "new": value}
        setattr(warehouse, field, value)

    db.commit()
    db.refresh(warehouse)

    log_action(
        db, user, ActionType.WAREHOUSE_UPDATED,
        entity_type="warehouse", entity_id=warehouse.id,
        entity_name=warehouse.name,
        ip_address=req.client.host if req else None
    )

    return warehouse


@router.delete("/{warehouse_id}")
def delete_warehouse(
    warehouse_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_admin_or_warehouse_keeper)],
    req: Request = None
):
    warehouse = db.query(Warehouse).filter(Warehouse.id == warehouse_id).first()
    if not warehouse:
        raise HTTPException(404, "Склад не найден")
    from db.models.item import Item
    items_count = db.query(Item).filter(Item.warehouse_id == warehouse_id).count()
    if items_count:
        raise HTTPException(400, "Нельзя удалить склад, на котором есть товары")

    log_action(
        db, user, ActionType.WAREHOUSE_DELETED,
        entity_type="warehouse", entity_id=warehouse.id,
        entity_name=warehouse.name,
        ip_address=req.client.host if req else None
    )

    db.delete(warehouse)
    db.commit()
    return {"message": "Склад удалён"}