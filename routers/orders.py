from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Order, OrderItem, Product
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
    # Calculate total amount
    total_amount = 0
    order_items_data = []

    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")

        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.name}. Available: {product.stock_quantity}"
            )

        item_total = product.price * item.quantity
        total_amount += item_total

        order_items_data.append({
            "product_id": product.id,
            "quantity": item.quantity,
            "price": product.price,  # lock current price
        })

    # Create order
    db_order = Order(
        order_number=generate_order_number(),
        email=order.email,
        phone=order.phone,
        full_name=order.full_name,
        location=order.location,
        total_amount=total_amount,
        notes=order.notes,
    )

    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    # Create order items + update stock
    for item_data in order_items_data:
        db_item = OrderItem(
            order_id=db_order.id,
            **item_data
        )
        db.add(db_item)

        product = db.query(Product).filter(Product.id == item_data["product_id"]).first()
        product.stock_quantity -= item_data["quantity"]

    db.commit()
    db.refresh(db_order)

    return db_order


# -------------------------
# Track Order (customer-facing)
# -------------------------
@router.get("/track", response_model=OrderSchema)
def track_order(
    email: str = Query(..., description="Customer email used when placing order"),
    order_number: str = Query(..., description="Order number to track"),  # better UX than ID
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(
        Order.order_number == order_number,
        Order.email == email
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found for this email")

    return order
