from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
import os, uuid

from database import get_db
from models import User, Product, Order
from schemas import ProductCreate, ProductUpdate, Product as ProductSchema, Order as OrderSchema
from routers.auth import get_current_admin_user

router = APIRouter()

# Admin-only routes
@router.get("/orders", response_model=List[OrderSchema])
def get_all_orders(db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    return db.query(Order).order_by(Order.created_at.desc()).all()

@router.get("/dashboard")
def get_dashboard_stats(db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    total_products = db.query(Product).filter(Product.is_active == True).count()
    total_orders = db.query(Order).count()
    total_users = db.query(User).count()
    recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(5).all()
    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "total_users": total_users,
        "recent_orders": recent_orders
    }

@router.post("/products", response_model=ProductSchema)
def create_product(product: ProductCreate, db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.put("/products/{product_id}", response_model=ProductSchema)
def update_product(product_id: int, product_update: ProductUpdate, db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in product_update.dict(exclude_unset=True).items():
        setattr(db_product, field, value)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    db_product.is_active = False
    db.commit()
    return {"message": "Product deleted successfully"}

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), admin_user: User = Depends(get_current_admin_user)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    os.makedirs("static/images", exist_ok=True)
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{file_extension}"
    file_path = f"static/images/{filename}"
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    
    return {"filename": filename, "url": f"/static/images/{filename}"}
