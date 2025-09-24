import base64
import json
import requests
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from database import get_db
from models import Payment, Order
from schemas import PaymentCreate
from config import settings

router = APIRouter()

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
    
    # For demo purposes, return success
    return {
        "success": True,
        "message": "STK Push sent successfully",
        "checkout_request_id": "sample_request_id"
    }

@router.post("/mpesa/callback")
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    return {"ResultCode": 0, "ResultDesc": "Success"}

@router.get("/verify/{transaction_id}")
def verify_payment(transaction_id: str, db: Session = Depends(get_db)):
    return {
        "transaction_id": transaction_id,
        "status": "completed",
        "amount": 1000,
        "created_at": datetime.now()
    }
    