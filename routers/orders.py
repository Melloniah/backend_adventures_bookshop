from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import Order, OrderItem, Product, DeliveryRoute, DeliveryStop
from schemas import Order as OrderSchema, OrderCreate
import uuid

router = APIRouter(
    redirect_slashes=False  
)

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

    # Calculate total and lock prices
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

    # Map delivery route & stop names
    
    route_name = None
    stop_name = None
    if order.delivery_route_id:
        route = db.query(DeliveryRoute).filter(DeliveryRoute.id == order.delivery_route_id).first()
        route_name = route.name if route else str(order.delivery_route_id)

    if order.delivery_stop_id:
        stop = db.query(DeliveryStop).filter(DeliveryStop.id == order.delivery_stop_id).first()
        stop_name = stop.name if stop else str(order.delivery_stop_id)


    # Create order
    db_order = Order(
        order_number=generate_order_number(),
        email=order.email,
        phone=order.phone,
        full_name=order.full_name,
        location=order.location,
        estate=order.estate,
        delivery_fee=order.delivery_fee,
        total_amount=total_amount + (order.delivery_fee or 0),
        notes=order.notes,
        payment_method=order.payment_method,
        delivery_route_id=order.delivery_route_id,
        delivery_stop_id=order.delivery_stop_id,
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    # Create order items and update stock
    for item_data in order_items_data:
        db_item = OrderItem(order_id=db_order.id, **item_data)
        db.add(db_item)
        product = db.query(Product).filter(Product.id == item_data["product_id"]).first()
        product.stock_quantity -= item_data["quantity"]

    db.commit()
    db.refresh(db_order)

    # Load nested relationships for automatic serialization
    db_order = db.query(Order).options(
        joinedload(Order.order_items).joinedload(OrderItem.product),
        joinedload(Order.delivery_route),
        joinedload(Order.delivery_stop)
    ).filter(Order.id == db_order.id).first()

    return db_order  # ✅ FastAPI handles nested serialization


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
