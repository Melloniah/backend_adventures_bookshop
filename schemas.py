from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from models import UserRole, OrderStatus, PaymentStatus


# -------------------------------
# User Schemas
# -------------------------------
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
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: User


# -------------------------------
# Category & Product Schemas
# -------------------------------
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
        orm_mode = True


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
        orm_mode = True


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    stock_quantity: Optional[int] = None
    category_id: Optional[int] = None
    image: Optional[str] = None
    is_featured: Optional[bool] = None
    on_sale: Optional[bool] = None
    is_active: Optional[bool] = None


# ----------------------------
# STOP SCHEMAS
# ----------------------------
class DeliveryStopBase(BaseModel):
    name: str
    price: float


class DeliveryStopCreate(DeliveryStopBase):
    pass


class DeliveryStopRead(DeliveryStopBase):
    id: int
    name: str

    class Config:
        from_attributes = True


# ----------------------------
# ROUTE SCHEMAS
# ----------------------------
class DeliveryRouteBase(BaseModel):
    name: str


class DeliveryRouteCreate(DeliveryRouteBase):
    stops: List[DeliveryStopCreate]


class DeliveryRouteUpdate(BaseModel):
    name: Optional[str] = None
    stops: Optional[List[DeliveryStopCreate]] = None


class DeliveryRouteRead(DeliveryRouteBase):
    id: int
    stops: List[DeliveryStopRead]

    class Config:
        from_attributes= True

# -------------------------------
# Order Schemas
class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    price: float  # lock price from cart


class OrderCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    location: str
    estate: Optional[str] = None
    delivery_fee: Optional[float] = 0.0
    notes: Optional[str] = None
    payment_method: str
    items: List[OrderItemCreate]
    delivery_route_id: Optional[int] = None
    delivery_stop_id: Optional[int] = None


class OrderItem(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    product: Product

    class Config:
        from_attributes = True


class OrderStatusLog(BaseModel):
    old_status: OrderStatus
    new_status: OrderStatus
    changed_at: datetime

    class Config:
        from_attributes = True


class Order(BaseModel):
    id: int
    order_number: str
    full_name: str
    email: EmailStr
    phone: str
    location: str
    estate: Optional[str] = None
    delivery_fee: Optional[float] = 0.0
    total_amount: float
    status: OrderStatus
    payment_status: PaymentStatus
    created_at: datetime
    order_items: List[OrderItem] = []
    status_logs: List[OrderStatusLog] = []

    # --- nested delivery info ---
    delivery_route: Optional[DeliveryRouteRead] = None
    delivery_stop: Optional[DeliveryStopRead] = None

    class Config:
        from_attributes= True


# -------------------------------
# Admin Order Update Schema
# -------------------------------
class OrderStatusUpdate(BaseModel):
    status: Optional[OrderStatus] = None        # e.g. pending, shipped, delivered
    payment_status: Optional[PaymentStatus] = None  # e.g. pending, completed, refunded


# -------------------------------
# Payments
# -------------------------------
class PaymentCreate(BaseModel):
    order_id: int
    phone_number: str
    amount: float
    method: str   # "mpesa" | "whatsapp"



