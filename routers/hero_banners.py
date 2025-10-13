# hero_banners.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import HeroBanner

router = APIRouter() 

@router.get("")   
def get_public_banners(db: Session = Depends(get_db)):
    return db.query(HeroBanner).order_by(HeroBanner.created_at.desc()).all()
