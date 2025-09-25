from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import Product as ProductModel
from schemas import Product as ProductSchema

router = APIRouter()

# ----------------------------
# Public: Get all active products
# ----------------------------
@router.get("/", response_model=List[ProductSchema])
def list_products(db: Session = Depends(get_db)):
    return db.query(ProductModel).filter(ProductModel.is_active == True).all()

# ----------------------------
# Public: Get one active product by ID
# ----------------------------
@router.get("/{product_id}", response_model=ProductSchema)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(ProductModel)
        .filter(ProductModel.id == product_id, ProductModel.is_active == True)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

# UPDATE, POST AND DELETE IS FOR ADMIN
