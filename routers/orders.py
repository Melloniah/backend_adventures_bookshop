from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import Order, OrderItem, Product, User
from schemas import Order as OrderSchema, OrderCreate
from routers.auth import get_current_user
import uuid

router = APIRouter()

def generate_order_number():
    return f"SM{uuid.uuid4().hex[:8].upper()}"

@router.post("/", response_model=OrderSchema)
def create_order(
    order: OrderCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Calculate total amount
    total_amount = 0
    order_items = []
    
    for item in order.items:
        product = db.Query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
        
        if product.stock_quantity < item.quantity:
            raise HTTPException(
                status_code=400, 
                detail=f"Insufficient stock for {product.name}. Available: {product.stock_quantity}"
            )
        
        item_total = product.price * item.quantity
        total_amount += item_total
        
        order_items.append({
            "product_id": product.id,
            "quantity": item.quantity,
            "price": product.price
        })
    
    # Create order
    db_order = Order(
        order_number=generate_order_number(),
        email=order.email,
        phone=order.phone,
        full_name=order.full_name,
        address=order.address,
        city=order.city,
        total_amount=total_amount,
        notes=order.notes
    )
    
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    
    # Create order items
    for item_data in order_items:
        db_item = OrderItem(
            order_id=db_order.id,
            **item_data
        )
        db.add(db_item)
        
        # Update product stock
        product = db.query(Product).filter(Product.id == item_data["product_id"]).first()
        product.stock_quantity -= item_data["quantity"]
    
    db.commit()
    db.refresh(db_order)
    return db_order

@router.get("/", response_model=List[OrderSchema])
def get_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    orders = db.query(Order).offset(skip).limit(limit).all()
    return orders

@router.get("/{order_id}", response_model=OrderSchema)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

# Track an order (open, by email + order_id)
@router.get("/track", response_model=OrderSchema)
def track_order(
    email: str = Query(..., description="Customer email used when placing order"),
    order_id: int = Query(..., description="Order ID to track"),
    db: Session = Depends(get_db),
):
    order = db.Query(OrderModel).filter(
        OrderModel.id == order_id,
        OrderModel.customer_email == email
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found for this email")

    return order    