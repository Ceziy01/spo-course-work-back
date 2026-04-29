from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from core.dependencies import get_db, require_any_authenticated, require_admin_or_purchase_manager
from db.models.user import Users
from db.models.suppliers import Supplier
from schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse
from db.models.activity_log import ActionType
from services.activity_log import log_action

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
    user: Annotated[Users, Depends(require_admin_or_purchase_manager)],
    req: Request = None
):
    existing = db.query(Supplier).filter(Supplier.name == data.name).first()
    if existing:
        raise HTTPException(400, "Поставщик с таким названием уже существует")
    supplier = Supplier(**data.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)

    log_action(
        db, user, ActionType.SUPPLIER_CREATED,
        entity_type="supplier", entity_id=supplier.id,
        entity_name=supplier.name,
        ip_address=req.client.host if req else None
    )

    return supplier


@router.patch("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_admin_or_purchase_manager)],
    req: Request = None
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

    changes = {}
    for field, value in update_data.items():
        old_val = getattr(supplier, field, None)
        if old_val != value:
            changes[field] = {"old": old_val, "new": value}
        setattr(supplier, field, value)

    db.commit()
    db.refresh(supplier)

    log_action(
        db, user, ActionType.SUPPLIER_UPDATED,
        entity_type="supplier", entity_id=supplier.id,
        entity_name=supplier.name,
        ip_address=req.client.host if req else None
    )

    return supplier


@router.delete("/{supplier_id}")
def delete_supplier(
    supplier_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_admin_or_purchase_manager)],
    req: Request = None
):
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(404, "Поставщик не найден")

    log_action(
        db, user, ActionType.SUPPLIER_DELETED,
        entity_type="supplier", entity_id=supplier.id,
        entity_name=supplier.name,
        ip_address=req.client.host if req else None
    )

    db.delete(supplier)
    db.commit()
    return {"message": "Поставщик удалён"}