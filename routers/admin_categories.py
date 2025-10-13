# routers/admin_categories.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Category
from pydantic import BaseModel
from schemas import CategoryCreate, CategoryOut, CategoryListOut 
from slugify import slugify  
from typing import Dict, Any, Optional, List
from routers.auth import get_current_admin_user, User


router = APIRouter()

from fastapi import UploadFile, File, Form

@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    name: str = Form(...),
    description: str = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    existing = db.query(Category).filter(Category.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")

    image_url = None
    if image:
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        content = await image.read()
        image_url = upload_image_to_cloudinary(content, image.filename, folder="ecommerce/categories")

    new_category = Category(
        name=name,
        slug=slugify(name),
        description=description,
        image=image_url,
        is_active=True
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

# Paginated list of categories
@router.get("", response_model=CategoryListOut)
def get_admin_categories(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    categories = db.query(Category).offset(skip).limit(limit).all()
    total = db.query(Category).count()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "categories": categories
    }

# Delete category by ID
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()
    return {"detail": "Category deleted successfully"}


@router.patch("/{product_id}", response_model=Dict[str, Any])
async def patch_product(
    product_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    old_image = product.image

    # Update fields if provided
    if name is not None:
        product.name = name
    if description is not None:
        product.description = description
    if price is not None:
        product.price = price
    if image is not None:
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        file_content = await image.read()
        image_url = upload_image_to_cloudinary(file_content, image.filename, folder="ecommerce/products")
        product.image = image_url

        # Delete old image if exists
        if old_image:
            delete_file_if_exists(old_image)

    db.commit()
    db.refresh(product)

    return {"detail": "Product updated", "product": product}


    # Search categories (paginated)
@router.get("/search", response_model=CategoryListOut)
def search_categories(
    q: str,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    query = db.query(Category).filter(Category.name.ilike(f"%{q}%"))
    total = query.count()
    categories = query.offset(skip).limit(limit).all()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "categories": categories
    }

