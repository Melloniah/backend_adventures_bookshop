# routers/admin_categories.py
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_
from slugify import slugify

from database import get_db
from models import Category, Product
from schemas import CategoryCreate, CategoryOut, CategoryListOut
from routers.auth import get_current_admin_user, User

from utils.cloudinary_config import upload_image_to_cloudinary
from utils.delete_file import delete_file_if_exists
from utils.slugify_helper import generate_unique_slug



router = APIRouter(
)

# ---------------- CREATE CATEGORY ---------------- #
@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)  # Only admin can create
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
        slug=generate_unique_slug(name, db),
        description=description,
        image=image_url,
        is_active=True
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

# ---------------- LIST CATEGORIES (PAGINATED) ---------------- #
@router.get("", response_model=CategoryListOut)
def get_admin_categories(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    admin_user: User = Depends(get_current_admin_user)  # Only admin can view
):
    categories = db.query(Category).offset(skip).limit(limit).all()
    total = db.query(Category).count()
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "categories": categories
    }

# ---------------- DELETE CATEGORY ---------------- #
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    # Delete category image if exists
    if category.image:
        delete_file_if_exists(category.image)
    db.delete(category)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# ---------------- PATCH PRODUCT ---------------- #
@router.patch("/products/{product_id}", response_model=Dict[str, Any])
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

    if name is not None:
        product.name = name
    if description is not None:
        product.description = description
    if price is not None:
        product.price = price
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

# ---------------- SEARCH CATEGORIES ---------------- #
from sqlalchemy import or_

@router.get("/search", response_model=CategoryListOut)
def search_categories(
    q: str,
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    admin_user: User = Depends(get_current_admin_user)
):
    # Search by name OR slug
    query = db.query(Category).filter(
        or_(
            Category.name.ilike(f"%{q}%"),
            Category.slug.ilike(f"%{q}%")
        )
    )
    total = query.count()
    categories = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "categories": categories
    }
