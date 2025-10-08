from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

from database import get_db
from models import Product as ProductModel, Category
from schemas import Product as ProductSchema

router = APIRouter(
    redirect_slashes=False  
)

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

    if category:
        cat = db.query(Category).filter(Category.slug == category, Category.is_active == True).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")
        query = query.filter(ProductModel.category_id == cat.id)

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

    # ✅ Convert to Pydantic models
    product_list = [ProductSchema.model_validate(p) for p in products]

    return {
        "products": product_list,
        "total_items": total_items,
        "total_pages": total_pages,
        "current_page": page
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
    return product  # ✅ This one is fine because response_model handles it