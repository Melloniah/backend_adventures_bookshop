# routers/categories.py - User-facing category and product endpoints
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import Category, Product
from schemas import CategoryOut, CategoryTree, ProductMinimal, Product as ProductSchema

router = APIRouter()


@router.get("", response_model=List[CategoryOut])
def get_categories(
    db: Session = Depends(get_db),
    active_only: bool = Query(True, description="Show only active categories")
):
    """
    Get all active categories with their subcategories and products.
    Returns flat list of all categories.
    """
    query = db.query(Category)
    if active_only:
        query = query.filter(Category.is_active == True)
    
    return query.all()


@router.get("/tree", response_model=List[CategoryTree])
def get_category_tree(
    db: Session = Depends(get_db)
):
    """
    Get hierarchical category tree (parent categories with nested subcategories).
    Useful for navigation menus and category browsers.
    """
    parents = db.query(Category).filter(
        Category.parent_id == None,
        Category.is_active == True
    ).all()
    return parents


@router.get("/parents", response_model=List[CategoryOut])
def get_parent_categories(
    db: Session = Depends(get_db)
):
    """
    Get only top-level parent categories.
    Useful for main navigation.
    """
    parents = db.query(Category).filter(
        Category.parent_id == None,
        Category.is_active == True
    ).all()
    return parents


@router.get("/{category_id}", response_model=CategoryOut)
def get_category(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Get single category with its subcategories and products.
    """
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.is_active == True
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category


@router.get("/slug/{slug}", response_model=CategoryOut)
def get_category_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """
    Get category by slug (URL-friendly identifier).
    """
    category = db.query(Category).filter(
        Category.slug == slug,
        Category.is_active == True
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return category


@router.get("/{category_id}/subcategories", response_model=List[CategoryOut])
def get_subcategories(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all subcategories of a parent category.
    """
    parent = db.query(Category).filter(
        Category.id == category_id,
        Category.is_active == True
    ).first()
    
    if not parent:
        raise HTTPException(status_code=404, detail="Parent category not found")
    
    # Return only active subcategories
    return [sub for sub in parent.subcategories if sub.is_active]


@router.get("/{category_id}/products", response_model=List[ProductSchema])
def get_category_products(
    category_id: int,
    db: Session = Depends(get_db),
    include_subcategories: bool = Query(
        False, 
        description="Include products from subcategories"
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get products in a category.
    
    - If include_subcategories=False: Returns only products directly in this category
    - If include_subcategories=True: Returns products from this category AND all subcategories
    
    Example use cases:
    - Books category with include_subcategories=True: Shows Grade 1 Books + Revision Books products
    - Grade 1 Books subcategory: Shows only Grade 1 books
    """
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.is_active == True
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if include_subcategories:
        # Collect this category ID and all subcategory IDs
        category_ids = [category.id]
        category_ids.extend([sub.id for sub in category.subcategories if sub.is_active])
        
        # Query products from all these categories
        products = db.query(Product).filter(
            Product.category_id.in_(category_ids),
            Product.is_active == True
        ).offset(skip).limit(limit).all()
    else:
        # Get only products directly in this category
        products = db.query(Product).filter(
            Product.category_id == category_id,
            Product.is_active == True
        ).offset(skip).limit(limit).all()
    
    return products


@router.get("/slug/{slug}/products", response_model=List[ProductSchema])
def get_category_products_by_slug(
    slug: str,
    db: Session = Depends(get_db),
    include_subcategories: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Get products in a category using slug instead of ID.
    More user-friendly for frontend routes like /categories/books/products
    """
    category = db.query(Category).filter(
        Category.slug == slug,
        Category.is_active == True
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if include_subcategories:
        category_ids = [category.id]
        category_ids.extend([sub.id for sub in category.subcategories if sub.is_active])
        
        products = db.query(Product).filter(
            Product.category_id.in_(category_ids),
            Product.is_active == True
        ).offset(skip).limit(limit).all()
    else:
        products = db.query(Product).filter(
            Product.category_id == category_id,
            Product.is_active == True
        ).offset(skip).limit(limit).all()
    
    return products


@router.get("/{category_id}/all-products", response_model=List[ProductSchema])
def get_all_category_products_recursive(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Get ALL products from a category and all its nested subcategories recursively.
    Useful for "show me everything under Books" regardless of depth.
    """
    def get_all_subcategory_ids(cat_id: int) -> List[int]:
        """Recursively collect all subcategory IDs"""
        category = db.query(Category).filter(Category.id == cat_id).first()
        if not category:
            return []
        
        ids = [cat_id]
        for subcat in category.subcategories:
            if subcat.is_active:
                ids.extend(get_all_subcategory_ids(subcat.id))
        return ids
    
    category = db.query(Category).filter(
        Category.id == category_id,
        Category.is_active == True
    ).first()
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Get all category IDs in the tree
    all_category_ids = get_all_subcategory_ids(category_id)
    
    # Get all products
    products = db.query(Product).filter(
        Product.category_id.in_(all_category_ids),
        Product.is_active == True
    ).all()
    
    return products


@router.get("/{category_id}/breadcrumbs")
def get_category_breadcrumbs(
    category_id: int,
    db: Session = Depends(get_db)
):
    """
    Get breadcrumb trail for a category.
    Returns path from root to current category.
    
    Example: Grade 1 Books -> [Books, Grade 1 Books]
    """
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    breadcrumbs = []
    current = category
    
    # Walk up the tree
    while current:
        breadcrumbs.insert(0, {
            "id": current.id,
            "name": current.name,
            "slug": current.slug
        })
        if current.parent_id:
            current = db.query(Category).filter(Category.id == current.parent_id).first()
        else:
            current = None
    
    return breadcrumbs
    
@router.get("/slug/{slug}/breadcrumbs")
def get_category_breadcrumbs_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """
    Get breadcrumb trail for a category using slug instead of ID.
    Returns path from root to current category.
    Example: /slug/books/grade-1 -> [Books, Grade 1 Books]
    """
    category = db.query(Category).filter(Category.slug == slug).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    breadcrumbs = []
    current = category

    # Walk up the hierarchy
    while current:
        breadcrumbs.insert(0, {
            "id": current.id,
            "name": current.name,
            "slug": current.slug
        })
        if current.parent_id:
            current = db.query(Category).filter(Category.id == current.parent_id).first()
        else:
            current = None

    return breadcrumbs