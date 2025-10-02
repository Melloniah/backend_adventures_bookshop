from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import Product as ProductModel, Category
from schemas import Product as ProductSchema

router = APIRouter()

# ----------------------------
# Public: Get all active products
# ----------------------------
@router.get("/", response_model=List[ProductSchema])
def get_products(
    category: Optional[str] = Query(None, description="Category slug"),
    search: Optional[str] = Query(None, description="Search term"),
    db: Session = Depends(get_db)
):
    query = db.query(ProductModel).filter(ProductModel.is_active == True)

    # Filter by category slug if provided
    if category:
        cat = db.query(Category).filter(Category.slug == category, Category.is_active == True).first()
        if not cat:
            raise HTTPException(status_code=404, detail="Category not found")
        query = query.filter(ProductModel.category_id == cat.id)

    # Search functionality
    if search:
        query = query.filter(ProductModel.name.ilike(f"%{search}%"))

    return query.all()


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
