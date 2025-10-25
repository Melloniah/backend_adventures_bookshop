# routers/admin_categories.py
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form, Response
from sqlalchemy.orm import Session
from sqlalchemy import or_

from database import get_db
from models import Category, Product
from schemas import (
    CategoryCreate, CategoryOut, CategoryListOut, CategoryUpdate,
    CategorySimple, CategoryTree, ProductMinimal
)
from routers.auth import get_current_admin_user, User
from utils.cloudinary_config import upload_image_to_cloudinary
from utils.delete_file import delete_file_if_exists
from utils.slugify_helper import generate_unique_slug

router = APIRouter()


# ============================================
# CATEGORY ENDPOINTS
# ============================================

@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    parent_id: Optional[int] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Create a new category (parent or subcategory)"""
    existing = db.query(Category).filter(Category.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category with this name already exists")

    if parent_id:
        parent = db.query(Category).filter(Category.id == parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent category not found")

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
        parent_id=parent_id,
        is_active=True
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


@router.get("", response_model=CategoryListOut)
def get_all_categories(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    admin_user: User = Depends(get_current_admin_user)
):
    """Get all categories with pagination"""
    query = db.query(Category)
    if not include_inactive:
        query = query.filter(Category.is_active == True)
    
    total = query.count()
    categories = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "categories": categories
    }


@router.get("/tree", response_model=List[CategoryTree])
def get_category_tree(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Get hierarchical tree of categories with subcategories."""

    def build_tree(category):
        return {
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "description": category.description,
            "image": category.image,
            "is_active": category.is_active,
            "parent_id": category.parent_id,
            "subcategories": [build_tree(sub) for sub in category.subcategories],
        }

    parents = db.query(Category).filter(Category.parent_id == None).all()
    return [build_tree(parent) for parent in parents]


@router.get("/parents", response_model=List[CategorySimple])
def get_parent_categories(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Get only parent categories for dropdown"""
    parents = db.query(Category).filter(Category.parent_id == None).all()
    return parents


@router.get("/search", response_model=CategoryListOut)
def search_categories(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    admin_user: User = Depends(get_current_admin_user)
):
    """Search categories by name or slug"""
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

@router.get("/{category_id}", response_model=CategoryOut)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Get single category with subcategories and products"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.patch("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    parent_id: Optional[int] = Form(None),
    is_active: Optional[bool] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Update category details"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    old_image = category.image

    if name is not None and name != category.name:
        existing = db.query(Category).filter(
            Category.name == name,
            Category.id != category_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Category name already exists")

        category.name = name
        category.slug = generate_unique_slug(name, db, exclude_id=category_id)
        
    if description is not None:
        category.description = description

    if parent_id is not None:
        # Enhanced validation
        if parent_id == category_id:
            raise HTTPException(status_code=400, detail="Category cannot be its own parent")
        
        # Check for circular references
        if check_circular_parent(db, category_id, parent_id):
            raise HTTPException(
                status_code=400, 
                detail="Cannot set parent: would create circular reference"
            )
        
        parent = db.query(Category).filter(Category.id == parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent category not found")
        category.parent_id = parent_id

    if is_active is not None:
        category.is_active = is_active

    if image:
        if not image.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        content = await image.read()
        image_url = upload_image_to_cloudinary(content, image.filename, folder="ecommerce/categories")
        category.image = image_url
        if old_image:
            delete_file_if_exists(old_image)

    db.commit()
    db.refresh(category)
    return category

@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Delete category (will also delete subcategories due to cascade)"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if category has products
    product_count = db.query(Product).filter(Product.category_id == category_id).count()
    if product_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete category with {product_count} products. Move or delete products first."
        )
    
    # Check if subcategories have products
    for subcat in category.subcategories:
        sub_product_count = db.query(Product).filter(Product.category_id == subcat.id).count()
        if sub_product_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Subcategory '{subcat.name}' has {sub_product_count} products. Cannot delete."
            )
    
    if category.image:
        delete_file_if_exists(category.image)
    
    db.delete(category)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

def check_circular_parent(db: Session, category_id: int, new_parent_id: int) -> bool:
    """
    Recursively check if setting new_parent_id would create a circular reference
    Returns True if circular, False if safe
    """
    if category_id == new_parent_id:
        return True
    
    current_id = new_parent_id
    visited = set()
    
    while current_id is not None:
        if current_id in visited or current_id == category_id:
            return True
        visited.add(current_id)
        
        parent = db.query(Category).filter(Category.id == current_id).first()
        if not parent:
            break
        current_id = parent.parent_id
    
    return False


@router.get("/{category_id}/products", response_model=List[ProductMinimal])
def get_category_products(
    category_id: int,
    db: Session = Depends(get_db),
    include_subcategory_products: bool = Query(False),
    admin_user: User = Depends(get_current_admin_user)
):
    """Get all products in a category (optionally include subcategory products)"""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if include_subcategory_products:
        # Get products from this category and all subcategories
        category_ids = [category.id]
        category_ids.extend([sub.id for sub in category.subcategories])
        products = db.query(Product).filter(Product.category_id.in_(category_ids)).all()
    else:
        # Get only products directly in this category
        products = category.products
    
    return products


def calculate_category_stats(db: Session) -> Dict[str, Any]:
    total_categories = db.query(Category).count()
    parent_categories = db.query(Category).filter(Category.parent_id == None).count()
    active_categories = db.query(Category).filter(Category.is_active == True).count()
    categories_with_products = db.query(Category).join(Product).distinct().count()

    return {
        "total": total_categories,
        "parents": parent_categories,
        "subcategories": total_categories - parent_categories,
        "active": active_categories,
        "inactive": total_categories - active_categories,
        "with_products": categories_with_products,
        "empty": total_categories - categories_with_products,
    }


@router.get("/stats", response_model=Dict[str, Any])
def get_category_stats(
    db: Session = Depends(get_db),
    admin_user = Depends(get_current_admin_user)
):
    return calculate_category_stats(db)
       


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