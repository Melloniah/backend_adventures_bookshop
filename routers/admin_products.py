from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from sqlalchemy.orm import Session
import os
from typing import List, Dict, Any
import uuid

from database import get_db
from models import Product, User
from schemas import ProductCreate, ProductUpdate, Product as ProductSchema
from routers.auth import get_current_admin_user
from utils.delete_file import delete_file_if_exists


router = APIRouter() 

# ----------------------------
# Get all products (paginated)
# ----------------------------
@router.get("", response_model=Dict[str, Any])
def get_all_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    query = db.query(Product).order_by(Product.created_at.desc())
    total_items = query.count()
    total_pages = (total_items + limit - 1) // limit

    products = query.offset((page - 1) * limit).limit(limit).all()

    # Convert to Pydantic models
    product_list = [ProductSchema.model_validate(p) for p in products]

    return {
        "products": product_list,
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page
    }

# ----------------------------
# Search products (paginated)
# ----------------------------
@router.get("/search", response_model=Dict[str, Any])
def search_products(
    q: str = Query(..., description="Search term"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    query = db.query(Product).filter(Product.name.ilike(f"%{q}%")).order_by(Product.created_at.desc())
    total_items = query.count()
    total_pages = (total_items + limit - 1) // limit

    products = query.offset((page - 1) * limit).limit(limit).all()

    # Convert to Pydantic models
    product_list = [ProductSchema.model_validate(p) for p in products]

    return {
        "products": product_list,
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page
    }


# Create product
@router.post("", response_model=ProductSchema)
def create_product(product: ProductCreate, db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    if db.query(Product).filter(Product.slug == product.slug).first():
        raise HTTPException(status_code=400, detail="Slug already exists")

    db_product = Product(**product.dict(exclude_unset=True))
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

# Update product
@router.put("/{product_id}", response_model=ProductSchema)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    old_image = product.image
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)

    if payload.image and old_image and old_image != payload.image:
        delete_file_if_exists(old_image)

    return product

# Delete product
@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    delete_file_if_exists(product.image)
    db.delete(product)
    db.commit()
    return {"detail": "Product deleted"}


# IMAGE UPLOAD
@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    admin_user: User = Depends(get_current_admin_user)
):
    # Check file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Ensure directory exists
    os.makedirs("static/images", exist_ok=True)

    # Generate unique filename
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join("static/images", filename)

    # Save file
    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")

    return {"filename": filename, "url": f"/static/images/{filename}"}