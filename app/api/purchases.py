from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from core.dependencies import get_db, get_current_user
from db.models.user import Users, UserRole
from db.models.purchase import PurchaseOrder, PurchaseStatus
from db.models.item import Item
from db.models.category import Category
from db.models.suppliers import Supplier
from db.models.warehouse import Warehouse
from schemas.purchase import PurchaseOrderCreate, PurchaseOrderUpdate, PurchaseOrderResponse, CompletePurchaseRequest

router = APIRouter(prefix="/purchases", tags=["purchases"])

def can_edit(user: Users) -> bool:
    return user.role in [UserRole.ADMIN, UserRole.PURCHASE_MANAGER]

def can_complete(user: Users) -> bool:
    return user.role in [UserRole.ADMIN, UserRole.PURCHASE_MANAGER, UserRole.WAREHOUSE_KEEPER]

@router.get("/", response_model=List[PurchaseOrderResponse])
def list_purchase_orders(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Users, Depends(get_current_user)]
):
    if current_user.role == UserRole.CUSTOMER:
        return []
    orders = db.query(PurchaseOrder).options(
        joinedload(PurchaseOrder.supplier),
        joinedload(PurchaseOrder.warehouse)
    ).all()
    result = []
    for o in orders:
        result.append(PurchaseOrderResponse(
            id=o.id,
            product_name=o.product_name,
            quantity=o.quantity,
            purchase_price=o.purchase_price,
            supplier_id=o.supplier_id,
            warehouse_id=o.warehouse_id,
            status=o.status.value,
            created_at=o.created_at,
            updated_at=o.updated_at,
            supplier_name=o.supplier.name if o.supplier else None,
            warehouse_name=o.warehouse.name if o.warehouse else None
        ))
    return result

@router.post("/", response_model=PurchaseOrderResponse, status_code=201)
def create_purchase_order(
    data: PurchaseOrderCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Users, Depends(get_current_user)]
):
    if not can_edit(current_user):
        raise HTTPException(403, "Недостаточно прав")
    supplier = db.query(Supplier).filter(Supplier.id == data.supplier_id).first()
    if not supplier:
        raise HTTPException(400, "Поставщик не найден")
    warehouse = db.query(Warehouse).filter(Warehouse.id == data.warehouse_id).first()
    if not warehouse:
        raise HTTPException(400, "Склад не найден")

    order = PurchaseOrder(
        product_name=data.product_name,
        quantity=data.quantity,
        purchase_price=data.purchase_price,
        supplier_id=data.supplier_id,
        warehouse_id=data.warehouse_id,
        status=PurchaseStatus.CREATED
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return PurchaseOrderResponse(
        id=order.id,
        product_name=order.product_name,
        quantity=order.quantity,
        purchase_price=order.purchase_price,
        supplier_id=order.supplier_id,
        warehouse_id=order.warehouse_id,
        status=order.status.value,
        created_at=order.created_at,
        updated_at=order.updated_at,
        supplier_name=supplier.name,
        warehouse_name=warehouse.name
    )

@router.patch("/{order_id}/status")
def change_purchase_status(
    order_id: int,
    status: str,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Users, Depends(get_current_user)]
):
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(404, "Закупка не найдена")
    if status not in [s.value for s in PurchaseStatus]:
        raise HTTPException(400, "Неверный статус")

    if status == PurchaseStatus.INITIATED.value:
        if not can_edit(current_user):
            raise HTTPException(403, "Недостаточно прав")
        order.status = PurchaseStatus.INITIATED
        db.commit()
        return {"message": "Статус изменён на 'Инициирована'"}
    
    if status == PurchaseStatus.CANCELLED.value:
        if not can_edit(current_user):
            raise HTTPException(403, "Недостаточно прав")
        order.status = PurchaseStatus.CANCELLED
        db.commit()
        return {"message": "Статус изменён на 'Отменено'"}

    raise HTTPException(400, "Используйте /complete для завершения закупки")

@router.post("/{order_id}/complete", status_code=200)
def complete_purchase(
    order_id: int,
    data: CompletePurchaseRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Users, Depends(get_current_user)]
):
    if not can_complete(current_user):
        raise HTTPException(403, "Недостаточно прав для завершения закупки")

    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(404, "Закупка не найдена")
    if order.status == PurchaseStatus.COMPLETED:
        raise HTTPException(400, "Закупка уже завершена")
    
    existing = db.query(Item).filter(Item.article == data.article).first()
    if existing:
        raise HTTPException(400, "Товар с таким артикулом уже существует")

    
    category = None
    if data.category_id:
        category = db.query(Category).filter(Category.id == data.category_id).first()
        if not category:
            raise HTTPException(400, "Категория не найдена")

    new_item = Item(
        name=order.product_name,
        description=data.description,
        article=data.article,
        quantity=order.quantity,          
        unit=data.unit,
        shelf_life_days=data.shelf_life_days,
        price=data.selling_price,          
        category_id=data.category_id,
        warehouse_id=order.warehouse_id,
        image_url=data.image_url or "/images/default.png"
    )
    db.add(new_item)

    order.status = PurchaseStatus.COMPLETED
    db.commit()

    return {"message": "Закупка завершена, товар создан", "item_id": new_item.id}

@router.delete("/{order_id}", status_code=204)
def delete_purchase_order(
    order_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Users, Depends(get_current_user)]
):
    if not can_edit(current_user):
        raise HTTPException(403, "Недостаточно прав")
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id).first()
    if not order:
        raise HTTPException(404, "Закупка не найдена")
    if order.status == PurchaseStatus.COMPLETED:
        raise HTTPException(400, "Нельзя удалить завершённую закупку")
    db.delete(order)
    db.commit()
    return None