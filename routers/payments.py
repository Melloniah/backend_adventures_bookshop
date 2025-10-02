import base64
import json
import requests
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Payment, Order, PaymentMethod, PaymentStatus
from schemas import PaymentCreate
from config import settings

router = APIRouter(
    redirect_slashes=False  
)

# ==============================
# MPESA FLOW
# ==============================
def get_mpesa_access_token():
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    encoded_credentials = base64.b64encode(f"{consumer_key}:{consumer_secret}".encode()).decode()
    
    headers = {"Authorization": f"Basic {encoded_credentials}"}
    response = requests.get(api_url, headers=headers)
    return response.json().get("access_token")

@router.post("/mpesa")
def initiate_mpesa_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == payment.order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Record payment attempt
    order.payment_method = PaymentMethod.mpesa
    order.payment_status = PaymentStatus.pending
    db.commit()

    # TODO: integrate actual STK Push here
    return {
        "success": True,
        "message": "STK Push sent successfully",
        "checkout_request_id": "sample_request_id"
    }

@router.post("/mpesa/callback")
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    # TODO: handle STK callback logic
    return {"ResultCode": 0, "ResultDesc": "Success"}

@router.get("/verify/{transaction_id}")
def verify_payment(transaction_id: str, db: Session = Depends(get_db)):
    # TODO: verify with Mpesa API
    return {
        "transaction_id": transaction_id,
        "status": "completed",
        "amount": 1000,
        "created_at": datetime.now()
    }


# ==============================
# WHATSAPP FLOW
# ==============================
ADMIN_WHATSAPP_NUMBER = "254724047489"  # ✅ change to your business number

@router.get("/whatsapp")
def whatsapp_payment(order_id: int = Query(...), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Build order summary text
    items_text = "\n".join(
        [f"- {item.product.name} × {item.quantity} = KSh {item.price * item.quantity}" for item in order.order_items]
    )
    
    message = (
        f" New Order - ADVENTURES BOOKSHOP\n\n"
        f" Order Number: {order.order_number}\n"
        f" Name: {order.full_name}\n"
        f"Phone: {order.phone}\n"
        f" Email: {order.email}\n"
        f" Location: {order.location}\n\n"
        f"Items:\n{items_text}\n\n"
        f" Total: KSh {order.total_amount}\n\n"
        f"Please confirm availability and delivery."
    )
    
    whatsapp_url = f"https://wa.me/{ADMIN_WHATSAPP_NUMBER}?text={requests.utils.quote(message)}"
    
    # Mark order as pending via WhatsApp
    order.payment_method = PaymentMethod.whatsapp
    order.payment_status = PaymentStatus.pending
    db.commit()
    
    return {
        "success": True,
        "whatsapp_url": whatsapp_url,
        "order_id": order.id,
        "order_number": order.order_number
    }
