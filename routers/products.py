from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from database import get_db
from models import Product as ProductModel, Category
from schemas import Product as ProductSchema

router = APIRouter() 

# ----------------------------
# Public: Get all active products (paginated)
# ----------------------------
@router.get("", response_model=Dict[str, Any])
def get_products(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    on_sale: Optional[bool] = Query(None),
    is_featured: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(ProductModel).filter(ProductModel.is_active == True)
    subcategories_data = []
    category_data = None

    if category:
        cat = db.query(Category).filter(Category.slug == category, Category.is_active == True).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")

        # Collect all descendant IDs for filtering
        all_ids = get_all_descendant_ids(cat)
        query = query.filter(ProductModel.category_id.in_(all_ids))

        # Prepare subcategory data
        subcategories_data = [
            {"id": sub.id, "name": sub.name, "slug": sub.slug, "image": sub.image}
            for sub in cat.subcategories if sub.is_active
        ]

        # Store category info for breadcrumb building
        category_data = {"id": cat.id, "name": cat.name, "slug": cat.slug}

    if on_sale is not None:
        query = query.filter(ProductModel.on_sale == on_sale)
    if is_featured is not None:
        query = query.filter(ProductModel.is_featured == is_featured)
    if search:
        query = query.filter(ProductModel.name.ilike(f"%{search}%"))

    query = query.order_by(ProductModel.created_at.desc())
    total_items = query.count()
    total_pages = (total_items + limit - 1) // limit
    products = query.offset((page - 1) * limit).limit(limit).all()

    product_list = [ProductSchema.model_validate(p) for p in products]

    # ✅ Important: Return both products + subcategories
    return {
        "products": product_list,
        "subcategories": subcategories_data,
        "category": category_data,
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page,
    }

# ----------------------------
# Public: Get one active product by ID
# ----------------------------
@router.get("/{product_id}", response_model=ProductSchema)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(ProductModel).filter(
        ProductModel.id == product_id,
        ProductModel.is_active == True
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product  
    

def get_all_descendant_ids(category: Category, collected=None):
    if collected is None:
        collected = []
    collected.append(category.id)
    for sub in category.subcategories:
        get_all_descendant_ids(sub, collected)
    return collected
