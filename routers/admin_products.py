from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form, Body
from sqlalchemy.orm import Session
import os
from typing import List, Dict, Any, Optional
import uuid

from database import get_db
from models import Product, User
from schemas import ProductCreate, ProductUpdate, Product as ProductSchema
from routers.auth import get_current_admin_user
from utils.delete_file import delete_file_if_exists
from utils.cloudinary_config import upload_image_to_cloudinary

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

@router.patch("/products/{product_id}", response_model=Dict[str, Any])
async def update_product(
    product_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    original_price: Optional[float] = Form(None),
    stock_quantity: Optional[int] = Form(None),
    category_id: Optional[int] = Form(None),
    is_featured: Optional[bool] = Form(None),
    on_sale: Optional[bool] = Form(None),
    is_active: Optional[bool] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Update product details including category assignment"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    old_image = product.image

    if name is not None:
        product.name = name
    if description is not None:
        product.description = description
    if price is not None:
        product.price = price
    if original_price is not None:
        product.original_price = original_price
    if stock_quantity is not None:
        product.stock_quantity = stock_quantity
    if is_featured is not None:
        product.is_featured = is_featured
    if on_sale is not None:
        product.on_sale = on_sale
    if is_active is not None:
        product.is_active = is_active
    
    if category_id is not None:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        product.category_id = category_id

    if image:
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        content = await image.read()
        image_url = upload_image_to_cloudinary(content, image.filename, folder="ecommerce/products")
        product.image = image_url
        if old_image:
            delete_file_if_exists(old_image)

    db.commit()
    db.refresh(product)
    return {"detail": "Product updated", "product": product}


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

    try:
        # Read file content
        file_content = await file.read()
        
        # Upload to Cloudinary
        image_url = upload_image_to_cloudinary(
            file_content, 
            file.filename, 
            folder="ecommerce/products"
        )
        
        return {
            "filename": file.filename,
            "url": image_url  # Now returns Cloudinary URL
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

@router.post("/products/{product_id}/move", response_model=Dict[str, str])
def move_product_to_category(
    product_id: int,
    new_category_id: int = Form(...),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Move a product to a different category"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    new_category = db.query(Category).filter(Category.id == new_category_id).first()
    if not new_category:
        raise HTTPException(status_code=404, detail="Target category not found")
    
    product.category_id = new_category_id
    db.commit()
    
    return {"detail": f"Product moved to category '{new_category.name}'"}

@router.post("/bulk/reorder", response_model=Dict[str, str])
def reorder_categories(
    orders: List[Dict[str, int]] = Body(...),  # [{"id": 1, "order": 0}, ...]
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Bulk update display order for categories
    Expects: [{"id": category_id, "order": new_order}, ...]
    """
    try:
        for item in orders:
            category = db.query(Category).filter(Category.id == item["id"]).first()
            if category:
                # Assuming you add a display_order column to your Category model
                category.display_order = item["order"]
        
        db.commit()
        return {"detail": f"Reordered {len(orders)} categories successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to reorder: {str(e)}")
