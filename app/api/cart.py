from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.dependencies import get_db, get_current_user
from db.models.user import Users
from db.models.item import Item
from db.models.cart import CartItem
from schemas.cart import CartItemCreate, CartItemUpdate, CartItemResponse
from services.order_service import get_available_quantity
from sqlalchemy import func
from db.models.order import Order, OrderStatus, OrderItem
from services.order_service import get_available_quantity

router = APIRouter(prefix="/cart", tags=["cart"])

@router.post("/items", response_model=CartItemResponse, status_code=201)
def add_to_cart(
    data: CartItemCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Users, Depends(get_current_user)]
):  
    available = get_available_quantity(data.item_id, db)
    if available < data.quantity:
        raise HTTPException(400, "Недостаточно товара на складе с учётом активных заказов")
    item = db.query(Item).filter(Item.id == data.item_id).first()
    if not item: raise HTTPException(status_code=404, detail="Товар не найден")

    if item.quantity < data.quantity: raise HTTPException(status_code=400, detail="Недостаточно товара на складе")

    cart_item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.item_id == data.item_id
    ).first()
    
    if cart_item:
        cart_item.quantity += data.quantity
        if cart_item.quantity <= 0:
            db.delete(cart_item)
            db.commit()
            raise HTTPException(status_code=204, detail="Товар удалён из корзины")
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            item_id=data.item_id,
            quantity=data.quantity
        )
        db.add(cart_item)
    
    db.commit()
    db.refresh(cart_item)

    return {
        "id": cart_item.id,
        "item_id": item.id,
        "name": item.name,
        "article": item.article,
        "quantity": cart_item.quantity,
        "price": item.price,
        "image_url": item.image_url,
        "total_price": item.price * cart_item.quantity
    }

@router.get("/", response_model=List[CartItemResponse])
def get_cart(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Users, Depends(get_current_user)]
):
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    result = []
    for ci in cart_items:
        item = ci.item 
        result.append({
            "id": ci.id,
            "item_id": item.id,
            "name": item.name,
            "article": item.article,
            "quantity": ci.quantity,
            "price": item.price,
            "image_url": item.image_url,
            "total_price": item.price * ci.quantity
        })
    return result

@router.patch("/items/{item_id}", response_model=CartItemResponse)
def update_cart_item(
    item_id: int,
    data: CartItemUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Users, Depends(get_current_user)]
):
    available = get_available_quantity(item_id, db)
    if available < data.quantity:
        raise HTTPException(400, "Недостаточно товара на складе с учётом активных заказов")
    cart_item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.item_id == item_id
    ).first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Товар не найден в корзине")
    
    if data.quantity <= 0:
        db.delete(cart_item)
        db.commit()
        raise HTTPException(status_code=204, detail="Товар удалён из корзины")
    
    cart_item.quantity = data.quantity
    db.commit()
    db.refresh(cart_item)
    
    item = cart_item.item
    return {
        "id": cart_item.id,
        "item_id": item.id,
        "name": item.name,
        "article": item.article,
        "quantity": cart_item.quantity,
        "price": item.price,
        "image_url": item.image_url,
        "total_price": item.price * cart_item.quantity
    }

@router.delete("/items/{item_id}", status_code=204)
def delete_cart_item(
    item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Users, Depends(get_current_user)]
):
    cart_item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.item_id == item_id
    ).first()
    if not cart_item:
        raise HTTPException(status_code=404, detail="Товар не найден в корзине")
    db.delete(cart_item)
    db.commit()
    return None

@router.post("/checkout", status_code=204)
def checkout(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[Users, Depends(get_current_user)]
):
    
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(400, "Корзина пуста")

    
    for ci in cart_items:
        available = get_available_quantity(ci.item_id, db)
        if available < ci.quantity:
            raise HTTPException(400, f"Недостаточно товара '{ci.item.name}' на складе")

    
    total_price = 0.0
    order = Order(user_id=current_user.id, status=OrderStatus.CREATED, total_price=0)
    db.add(order)
    db.flush()  

    
    for ci in cart_items:
        item = ci.item
        price = item.price
        order_item = OrderItem(
            order_id=order.id,
            item_id=ci.item_id,
            quantity=ci.quantity,
            price_at_time=price
        )
        db.add(order_item)
        total_price += price * ci.quantity

    order.total_price = total_price
    db.commit()

    
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()

    return None