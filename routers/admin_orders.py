from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Order, User
from schemas import Order as OrderSchema, OrderStatusUpdate
from routers.auth import get_current_admin_user

router = APIRouter(
    redirect_slashes=False  
)

# Get all orders
@router.get("", response_model=List[OrderSchema])
def get_all_orders(db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    return db.query(Order).order_by(Order.created_at.desc()).all()

# Get single order
@router.get("/{order_id}", response_model=OrderSchema)
def get_order(order_id: int, db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

# Update order status
@router.put("/{order_id}/status", response_model=OrderSchema)
def update_order_status(order_id: int, update: OrderStatusUpdate, db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if update.status is not None:
        order.status = update.status
    if update.payment_status is not None:
        order.payment_status = update.payment_status

    db.commit()
    db.refresh(order)
    return order
