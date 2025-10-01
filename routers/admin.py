from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Form
from sqlalchemy.orm import Session
import os, uuid

from database import get_db
from models import User, Product, Order, HeroBanner
from schemas import ProductCreate, ProductUpdate, Product as ProductSchema, Order as OrderSchema
from routers.auth import get_current_admin_user
from utils.delete_file import delete_file_if_exists 



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


# UPDATE product
@router.put("/products/{product_id}")
async def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    old_image = product.image  # save old image

    # update fields from payload
    for key, value in payload.dict(exclude_unset=True).items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)

    # delete old image if replaced
    if payload.image and old_image and old_image != payload.image:
        delete_file_if_exists(old_image)

    return product

# DELETE product
@router.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # delete product image
    delete_file_if_exists(product.image)

    db.delete(product)
    db.commit()
    return {"detail": "Product deleted"}

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

@router.get("/hero-banners/{banner_id}")
def get_banner_by_id(banner_id: int, db: Session = Depends(get_db)):
    banner = db.query(HeroBanner).filter(HeroBanner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    return banner


@router.post("/hero-banners")
async def create_banner(
    title: str = Form(...),
    subtitle: str = Form(None),
    description: str = Form(None),
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


@router.delete("/hero-banners/{banner_id}")
def delete_hero_banner(
    banner_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)  # ✅ protect with admin auth
):
    banner = db.query(HeroBanner).filter(HeroBanner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")

    # delete old image file
    if banner.image:
        file_path = banner.image.lstrip("/")  # remove leading slash if present
        if os.path.exists(file_path):
            os.remove(file_path)

    db.delete(banner)
    db.commit()
    return {"detail": "Banner deleted successfully"}


@router.put("/hero-banners/{banner_id}")
async def update_banner(
    banner_id: int,
    title: str = Form(...),
    subtitle: str = Form(None),
    description: str = Form(None),
    file: UploadFile = File(None),   # <-- optional now
    db: Session = Depends(get_db),
    admin_user=Depends(get_current_admin_user)
):
    banner = db.query(HeroBanner).filter(HeroBanner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")

    # Update text fields
    banner.title = title
    banner.subtitle = subtitle
    banner.description = description

    # If a new image was uploaded, replace the old one
    if file:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Delete old image file (optional but clean)
        if banner.image and os.path.exists(banner.image.lstrip("/")):
            os.remove(banner.image.lstrip("/"))

        # Save new image
        os.makedirs("static/images", exist_ok=True)
        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join("static/images", filename)

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        banner.image = f"/static/images/{filename}"

    db.commit()
    db.refresh(banner)
    return banner



