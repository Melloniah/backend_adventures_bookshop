from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Dict, Any
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
# Get all orders (paginated)
# -------------------------------
@router.get("", response_model=Dict[str, Any])
def get_all_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(None, description="Filter by order status"),
    search: str = Query(None, description="Search by order number, customer name, or email"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    # Base query with eager loading
    query = db.query(Order).options(
        joinedload(Order.status_logs),
        joinedload(Order.order_items).joinedload(OrderItem.product),
        joinedload(Order.delivery_route),
        joinedload(Order.delivery_stop)
    )

    # Filter by status if provided
    if status:
        query = query.filter(Order.status == status)

    # Search functionality
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Order.order_number.ilike(search_term)) |
            (Order.full_name.ilike(search_term)) |
            (Order.email.ilike(search_term))
        )

    # Order by newest first
    query = query.order_by(Order.created_at.desc())

    # Get total count
    total_items = query.count()
    total_pages = (total_items + limit - 1) // limit

    # Paginate
    orders = query.offset((page - 1) * limit).limit(limit).all()

    # Convert to Pydantic models
    order_list = [OrderSchema.model_validate(o) for o in orders]

    return {
        "orders": order_list,
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page,
        "limit": limit
    }


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
    ).filter(Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order


# -------------------------------
# Update order status
# -------------------------------
@router.put("/{order_id}/status", response_model=OrderSchema)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Update status if provided
    if payload.status:
        old_status = order.status
        new_status = payload.status

        # Validate transition
        if new_status not in ALLOWED_TRANSITIONS.get(old_status, []):
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition from {old_status} to {new_status}"
            )

        # Log status change
        status_log = OrderStatusLog(
            order_id=order.id,
            old_status=old_status,
            new_status=new_status,
            changed_at=datetime.utcnow()
        )
        db.add(status_log)
        order.status = new_status

    # Update payment status if provided
    if payload.payment_status:
        order.payment_status = payload.payment_status

    db.commit()
    db.refresh(order)

    # Reload with relationships
    order = db.query(Order).options(
        joinedload(Order.status_logs),
        joinedload(Order.order_items).joinedload(OrderItem.product),
        joinedload(Order.delivery_route),
        joinedload(Order.delivery_stop)
    ).filter(Order.id == order_id).first()

    return order