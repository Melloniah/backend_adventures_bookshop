from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from typing import List
from datetime import datetime

from database import get_db
from models import Order, User, OrderStatusLog, OrderItem
from schemas import Order as OrderSchema, OrderStatusUpdate
from routers.auth import get_current_admin_user

router = APIRouter(redirect_slashes=False)

# Allowed transitions
ALLOWED_TRANSITIONS = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["processing", "cancelled"],
    "processing": ["shipped", "cancelled"],
    "shipped": ["delivered", "cancelled"],
    "delivered": [],
    "cancelled": []
}

# -------------------------------
# Get all orders
# -------------------------------
@router.get("", response_model=List[OrderSchema])
def get_all_orders(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    # Eagerly load relationships including delivery info
    orders = db.query(Order).options(
        joinedload(Order.status_logs),
        joinedload(Order.order_items).joinedload(OrderItem.product),
        joinedload(Order.delivery_route),
        joinedload(Order.delivery_stop)
    ).order_by(Order.created_at.desc()).all()

    return orders



# -------------------------------
# Get single order
# -------------------------------
@router.get("/{order_id}", response_model=OrderSchema)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    order = db.query(Order).options(
        joinedload(Order.status_logs),
        joinedload(Order.order_items).joinedload(OrderItem.product),
        joinedload(Order.delivery_route),
        joinedload(Order.delivery_stop)
    ).filter(Order.id == order_id).first()  # ✅ get single order

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order




# -------------------------------
# Update order status with validation & logging
# -------------------------------
@router.put("/{order_id}/status", response_model=OrderSchema)
def update_order_status(
    order_id: int,
    update: OrderStatusUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    order = db.query(Order).options(joinedload(Order.status_logs)).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Update status if provided
    if update.status:
        old_status = order.status
        new_status = update.status

        if new_status not in ALLOWED_TRANSITIONS.get(old_status, []):
            allowed = ", ".join(ALLOWED_TRANSITIONS.get(old_status, []))
            raise HTTPException(
                status_code=400,
                detail=f"Cannot change status from {old_status} to {new_status}. Allowed: {allowed}"
            )

        order.status = new_status

        # Log status change
        log = OrderStatusLog(
            order_id=order.id,
            old_status=old_status,
            new_status=new_status,
            changed_at=datetime.utcnow(),
            changed_by_admin_id=admin_user.id
        )
        db.add(log)

    # Update payment status if provided
    if update.payment_status is not None:
        order.payment_status = update.payment_status

    db.commit()
    db.refresh(order)

    return order  # ✅ raw SQLAlchemy object serialized automatically
