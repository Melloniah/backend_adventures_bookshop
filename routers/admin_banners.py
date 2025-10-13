from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import os, uuid

from database import get_db
from models import HeroBanner, User
from routers.auth import get_current_admin_user
from utils.cloudinary_config import upload_image_to_cloudinary


router = APIRouter() 


@router.get("")
def get_banners(db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    return db.query(HeroBanner).order_by(HeroBanner.created_at.desc()).all()

@router.get("/{banner_id}")
def get_banner_by_id(banner_id: int, db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    banner = db.query(HeroBanner).filter(HeroBanner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")
    return banner

@router.post("")
async def create_banner(
    title: str = Form(...),
    subtitle: str = Form(None),
    description: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        file_content = await file.read()
        image_url = upload_image_to_cloudinary(
            file_content, 
            file.filename, 
            folder="ecommerce/banners"
        )
        
        banner = HeroBanner(
            title=title, 
            subtitle=subtitle, 
            description=description, 
            image=image_url  # Store Cloudinary URL
        )
        db.add(banner)
        db.commit()
        db.refresh(banner)
        return banner
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create banner: {str(e)}")


@router.put("/{banner_id}")
async def update_banner(
    banner_id: int,
    title: str = Form(...),
    subtitle: str = Form(None),
    description: str = Form(None),
    file: UploadFile = File(None),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    banner = db.query(HeroBanner).filter(HeroBanner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")

    banner.title = title
    banner.subtitle = subtitle
    banner.description = description

    if file:
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Delete old image from Cloudinary
        if banner.image:
            delete_file_if_exists(banner.image)

        # Upload new image
        try:
            file_content = await file.read()
            image_url = upload_image_to_cloudinary(
                file_content, 
                file.filename, 
                folder="ecommerce/banners"
            )
            banner.image = image_url
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

    db.commit()
    db.refresh(banner)
    return banner


@router.delete("/{banner_id}")
def delete_banner(banner_id: int, db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    banner = db.query(HeroBanner).filter(HeroBanner.id == banner_id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner not found")

    if banner.image and os.path.exists(banner.image.lstrip("/")):
        os.remove(banner.image.lstrip("/"))

    db.delete(banner)
    db.commit()
    return {"detail": "Banner deleted successfully"}
