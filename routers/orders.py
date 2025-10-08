from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import Order, OrderItem, Product, DeliveryRoute, DeliveryStop
from schemas import Order as OrderSchema, OrderCreate
import uuid
from services.email_service import send_admin_order_email

router = APIRouter() 

def generate_order_number():
    return f"SM{uuid.uuid4().hex[:8].upper()}"


# -------------------------
# Create Order (customer checkout)
# -------------------------
@router.post("", response_model=OrderSchema)
def create_order(
    order: OrderCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    total_amount = 0
    order_items_data = []

    # --- Calculate total and lock prices ---
    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}. Available: {product.stock_quantity}"
            )
        total_amount += product.price * item.quantity
        order_items_data.append({
            "product_id": product.id,
            "quantity": item.quantity,
            "price": product.price
        })

    # --- Determine delivery info ---
    delivery_fee = order.delivery_fee or 0
    location = order.location if order.delivery_route_id and order.delivery_stop_id else None
    route = db.query(DeliveryRoute).filter(DeliveryRoute.id == order.delivery_route_id).first() if order.delivery_route_id else None
    stop = db.query(DeliveryStop).filter(DeliveryStop.id == order.delivery_stop_id).first() if order.delivery_stop_id else None

    # --- Create order ---
    db_order = Order(
        order_number=generate_order_number(),
        email=order.email,
        phone=order.phone,
        full_name=order.full_name,
        location=location,
        estate=order.estate,
        delivery_fee=delivery_fee,
        total_amount=total_amount + delivery_fee,
        notes=order.notes,
        payment_method=order.payment_method,
        delivery_route_id=order.delivery_route_id,
        delivery_stop_id=order.delivery_stop_id,
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    # --- Create order items and update stock ---
    for item_data in order_items_data:
        db_item = OrderItem(order_id=db_order.id, **item_data)
        db.add(db_item)
        product = db.query(Product).filter(Product.id == item_data["product_id"]).first()
        product.stock_quantity -= item_data["quantity"]
    db.commit()
    db.refresh(db_order)

    # --- Send admin email in the background ---
    background_tasks.add_task(send_admin_order_email, db_order.order_number, db_order.total_amount)

    # --- Load nested relationships for serialization ---
    db_order = db.query(Order).options(
        joinedload(Order.order_items).joinedload(OrderItem.product),
        joinedload(Order.delivery_route),
        joinedload(Order.delivery_stop)
    ).filter(Order.id == db_order.id).first()

    return db_order



# -------------------------
# Track Order (customer-facing)
# -------------------------
@router.get("/track", response_model=OrderSchema)
def track_order(
    email: str = Query(..., description="Customer email used when placing order"),
    order_number: str = Query(..., description="Order number to track"),
    db: Session = Depends(get_db),
):
    order = db.query(Order).options(
        joinedload(Order.order_items).joinedload(OrderItem.product)
    ).filter(
        Order.order_number == order_number,
        Order.email == email
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found for this email")

    return order  # ✅ automatic serialization
