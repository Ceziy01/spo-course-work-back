from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from core.dependencies import get_db, get_current_user, require_admin_or_sales_manager, require_management_or_accountant_read_access
from db.models.user import Users
from db.models.order import Order, OrderStatus, OrderItem
from db.models.item import Item
from schemas.order import OrderResponse, OrderUpdate, OrderItemResponse

router = APIRouter(prefix="/orders", tags=["orders"])


def get_available_quantity(item_id: int, db: Session) -> float:
    """Возвращает доступное количество товара с учётом зарезервированных в заказах со статусом 'created'"""
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return 0
    reserved = db.query(func.sum(OrderItem.quantity)).join(Order).filter(
        OrderItem.item_id == item_id,
        Order.status == OrderStatus.CREATED
    ).scalar() or 0
    return item.quantity - reserved


@router.get("/my", response_model=List[OrderResponse])
def get_my_orders(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Users, Depends(get_current_user)]
):
    orders = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.item)
    ).filter(Order.user_id == current_user.id).all()

    result = []
    for order in orders:
        
        items = [
            OrderItemResponse(
                id=oi.id,
                item_id=oi.item_id,
                quantity=oi.quantity,
                price_at_time=oi.price_at_time,
                name=oi.item.name
            ) for oi in order.items
        ]
        
        result.append(OrderResponse(
            id=order.id,
            user_id=order.user_id,
            status=order.status.value,          
            total_price=order.total_price,
            created_at=order.created_at,
            items=items
        ))
    return result

@router.get("/", response_model=List[OrderResponse])
def get_all_orders(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_management_or_accountant_read_access)]
):
    orders = db.query(Order).options(
        joinedload(Order.items).joinedload(OrderItem.item)
    ).all()

    result = []
    for order in orders:
        items = [
            OrderItemResponse(
                id=oi.id,
                item_id=oi.item_id,
                quantity=oi.quantity,
                price_at_time=oi.price_at_time,
                name=oi.item.name
            ) for oi in order.items
        ]
        result.append(OrderResponse(
            id=order.id,
            user_id=order.user_id,
            status=order.status.value,
            total_price=order.total_price,
            created_at=order.created_at,
            items=items
        ))
    return result

@router.patch("/{order_id}", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    data: OrderUpdate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_admin_or_sales_manager)]
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Заказ не найден")

    old_status = order.status
    new_status = data.status

    
    if new_status not in [s.value for s in OrderStatus]:
        raise HTTPException(400, "Недопустимый статус")

    if new_status == old_status:
        
        items = [
            OrderItemResponse(
                id=oi.id,
                item_id=oi.item_id,
                quantity=oi.quantity,
                price_at_time=oi.price_at_time,
                name=oi.item.name
            ) for oi in order.items
        ]
        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            status=order.status.value,
            total_price=order.total_price,
            created_at=order.created_at,
            items=items
        )

    
    if new_status == OrderStatus.CONFIRMED.value and old_status == OrderStatus.CREATED.value:
        for oi in order.items:
            item = oi.item
            if item.quantity < oi.quantity:
                raise HTTPException(400, f"Недостаточно товара {item.name} на складе")
            item.quantity -= oi.quantity
        db.commit()

    order.status = new_status
    db.commit()
    db.refresh(order)

    
    items = [
        OrderItemResponse(
            id=oi.id,
            item_id=oi.item_id,
            quantity=oi.quantity,
            price_at_time=oi.price_at_time,
            name=oi.item.name
        ) for oi in order.items
    ]
    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status.value,
        total_price=order.total_price,
        created_at=order.created_at,
        items=items
    )
    
@router.delete("/{order_id}", status_code=204)
def delete_order(
    order_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[Users, Depends(require_admin_or_sales_manager)]
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Заказ не найден")

    if order.status == OrderStatus.CONFIRMED:
        for oi in order.items:
            item = oi.item
            item.quantity += oi.quantity
        db.commit()

    db.delete(order)
    db.commit()
    return None