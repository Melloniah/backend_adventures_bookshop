"""
Pydantic models for API request/response validation
Ensures data types and formats are correct
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from models import UserRole, OrderStatus, PaymentStatus

class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    role: UserRole
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class CategoryCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None

class Category(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    class Config:
        from_attributes = True

class ProductCreate(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    stock_quantity: int = 0
    category_id: Optional[int] = None
    image: Optional[str] = None
    is_featured: bool = False
    on_sale: bool = False

class Product(BaseModel):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    stock_quantity: int
    image: Optional[str] = None
    is_active: bool
    is_featured: bool
    on_sale: bool
    created_at: datetime
    category: Optional[Category] = None
    class Config:
        from_attributes = True

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class OrderCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    address: str
    city: str
    notes: Optional[str] = None
    items: List[OrderItemCreate]

class OrderItem(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    product: Product
    class Config:
        from_attributes = True

class Order(BaseModel):
    id: int
    order_number: str
    full_name: str
    email: EmailStr
    phone: str
    address: str
    city: str
    total_amount: float
    status: OrderStatus
    payment_status: PaymentStatus
    created_at: datetime
    order_items: List[OrderItem] = []
    class Config:
        from_attributes = True

class PaymentCreate(BaseModel):
    order_id: int
    phone_number: str
    amount: float