from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.dependencies import get_db, require_any_authenticated, require_admin_or_warehouse_keeper
from db.models.user import Users
from db.models.category import Category
from schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse

router = APIRouter(prefix="/categories", tags=["categories"])

@router.get("/", response_model=List[CategoryResponse])
def list_categories(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_any_authenticated)]
):
    return db.query(Category).all()

@router.post("/", response_model=CategoryResponse, status_code=201)
def create_category(
    data: CategoryCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_admin_or_warehouse_keeper)]
):
    existing = db.query(Category).filter(Category.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Категория с таким названием уже существует")
    category = Category(**data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_admin_or_warehouse_keeper)]
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")

    update_data = data.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] != category.name:
        existing = db.query(Category).filter(
            Category.name == update_data["name"],
            Category.id != category_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Категория с таким названием уже существует")

    for field, value in update_data.items():
        setattr(category, field, value)

    db.commit()
    db.refresh(category)
    return category

@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_admin_or_warehouse_keeper)]
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Категория не найдена")

    from db.models.item import Item
    items_count = db.query(Item).filter(Item.category_id == category_id).count()
    if items_count:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить категорию, к которой привязаны товары. Сначала переназначьте или удалите товары."
        )

    db.delete(category)
    db.commit()
    return {"message": "Категория удалена"}