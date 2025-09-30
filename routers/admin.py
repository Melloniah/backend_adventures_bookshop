from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form
from sqlalchemy.orm import Session
import os, uuid

from database import get_db
from models import User, Product, Order, HeroBanner
from schemas import ProductCreate, ProductUpdate, Product as ProductSchema, Order as OrderSchema
from routers.auth import get_current_admin_user



router = APIRouter()

STATIC_DIR = "static/images"

# Admin-only routes
@router.get("/orders", response_model=List[OrderSchema])
def get_all_orders(db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    return db.query(Order).order_by(Order.created_at.desc()).all()

@router.get("/dashboard")
def get_dashboard_stats(db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    total_products = db.query(Product).filter(Product.is_active == True).count()
    total_orders = db.query(Order).count()
    total_users = db.query(User).count()
    recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(5).all()
    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "total_users": total_users,
        "recent_orders": recent_orders
    }


@router.get("/products", response_model=List[ProductSchema])
def get_all_products(db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    return db.query(Product).order_by(Product.created_at.desc()).all()

    # to enable searching products by fetching api
@router.get("/products/search", response_model=List[ProductSchema])
def search_products(
    q: str = Query(..., description="Search term"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    return (
        db.query(Product)
        .filter(Product.name.ilike(f"%{q}%"))  # case-insensitive search
        .order_by(Product.created_at.desc())
        .all()
    ) 

@router.post("/products", response_model=ProductSchema)
def create_product(product: ProductCreate, db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    # Check if slug already exists
    if db.query(Product).filter(Product.slug == product.slug).first():
        raise HTTPException(status_code=400, detail="Slug already exists")

    db_product = Product(**product.dict(exclude_unset=True))
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.put("/products/{product_id}", response_model=ProductSchema)
def update_product(product_id: int, product_update: ProductUpdate, db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    # If updating slug, check uniqueness
    if product_update.slug and product_update.slug != db_product.slug:
        if db.query(Product).filter(Product.slug == product_update.slug).first():
            raise HTTPException(status_code=400, detail="Slug already exists")

    for field, value in product_update.dict(exclude_unset=True).items():
        setattr(db_product, field, value)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)  # ✅ Hard delete
    db.commit()
    return {"message": "Product deleted successfully"}

# ----------------------
# Image Upload
# ----------------------

@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), admin_user: User = Depends(get_current_admin_user)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    os.makedirs("static/images", exist_ok=True)
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join("static/images", filename)

    try:
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")

    return {"filename": filename, "url": f"/static/images/{filename}"}

    #Admin to be able to add or delete hero banners
@router.get("/hero-banners")
def get_banners(db: Session = Depends(get_db)):
    return db.query(HeroBanner).order_by(HeroBanner.created_at.desc()).all()


@router.post("/hero-banners")
async def create_banner(
    title: str,
    subtitle: str = None,
    description: str = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin_user = Depends(get_current_admin_user)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    os.makedirs("static/images", exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join("static/images", filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    banner = HeroBanner(
        title=title,
        subtitle=subtitle,
        description=description,
        image=f"/static/images/{filename}"
    )
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return banner

@router.delete("/admin/hero-banners/{banner_id}")
def delete_hero_banner(banner_id: int, db: Session = Depends(get_db)):
    banner = db.query(HeroBanner).filter(HeroBanner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")

    # Remove old image file
    if banner.image:
        # remove leading "/" if stored like "/static/images/file.jpg"
        file_path = banner.image.lstrip("/")
        if os.path.exists(file_path):
            os.remove(file_path)

    db.delete(banner)
    db.commit()
    return {"message": "Banner and image deleted successfully"}


from fastapi import UploadFile, Form

@router.put("/admin/hero-banners/{banner_id}")
async def update_hero_banner(
    banner_id: int,
    title: str = Form(...),
    subtitle: str = Form(None),
    description: str = Form(None),
    image: UploadFile = None,
    db: Session = Depends(get_db),
):
    banner = db.query(HeroBanner).filter(HeroBanner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")

    # Update fields
    banner.title = title
    banner.subtitle = subtitle
    banner.description = description

    # If new image is uploaded → delete old file and save new
    if image:
        if banner.image:
            old_path = banner.image.lstrip("/")
            if os.path.exists(old_path):
                os.remove(old_path)

        file_location = f"static/images/{image.filename}"
        with open(file_location, "wb+") as f:
            f.write(await image.read())
        banner.image = f"/{file_location}"  # keep format /static/images/filename

    db.commit()
    db.refresh(banner)
    return banner
