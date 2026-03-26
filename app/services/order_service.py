from sqlalchemy.orm import Session
from sqlalchemy import func
from db.models.order import Order, OrderStatus, OrderItem
from db.models.item import Item

def get_available_quantity(item_id: int, db: Session) -> float:
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        return 0
    reserved = db.query(func.sum(OrderItem.quantity)).join(Order).filter(
        OrderItem.item_id == item_id,
        Order.status == OrderStatus.CREATED
    ).scalar() or 0
    return item.quantity - reserved