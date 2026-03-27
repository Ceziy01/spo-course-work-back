from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.dependencies import get_db, require_any_authenticated, require_admin_or_purchase_manager, require_admin_or_purchase_manager
from db.models.user import Users
from db.models.suppliers import Supplier
from schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse

router = APIRouter(prefix="/suppliers", tags=["suppliers"])

@router.get("/", response_model=List[SupplierResponse])
def list_suppliers(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_any_authenticated)]
):
    return db.query(Supplier).all()

@router.post("/", response_model=SupplierResponse, status_code=201)
def create_supplier(
    data: SupplierCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_admin_or_purchase_manager)]
):
    existing = db.query(Supplier).filter(Supplier.name == data.name).first()
    if existing:
        raise HTTPException(400, "Поставщик с таким названием уже существует")
    supplier = Supplier(**data.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier

@router.patch("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_admin_or_purchase_manager)]
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(404, "Поставщик не найден")
    update_data = data.model_dump(exclude_unset=True)
    if "name" in update_data:
        existing = db.query(Supplier).filter(
            Supplier.name == update_data["name"],
            Supplier.id != supplier_id
        ).first()
        if existing:
            raise HTTPException(400, "Поставщик с таким названием уже существует")
    for field, value in update_data.items():
        setattr(supplier, field, value)
    db.commit()
    db.refresh(supplier)
    return supplier

@router.delete("/{supplier_id}")
def delete_supplier(
    supplier_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_admin_or_purchase_manager)]
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(404, "Поставщик не найден")
    db.delete(supplier)
    db.commit()
    return {"message": "Поставщик удалён"}