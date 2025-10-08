from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import os, uuid

from database import get_db
from models import HeroBanner, User
from routers.auth import get_current_admin_user

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

    os.makedirs("static/images", exist_ok=True)
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join("static/images", filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    banner = HeroBanner(title=title, subtitle=subtitle, description=description, image=f"/static/images/{filename}")
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return banner

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

        if banner.image and os.path.exists(banner.image.lstrip("/")):
            os.remove(banner.image.lstrip("/"))

        ext = os.path.splitext(file.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        file_path = os.path.join("static/images", filename)

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        banner.image = f"/static/images/{filename}"

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
