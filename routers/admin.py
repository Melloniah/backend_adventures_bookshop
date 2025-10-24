from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User, Product, Order
from routers.auth import get_current_admin_user
from routers.admin_categories import get_category_stats  # ✅ import this

router = APIRouter()

@router.get("/dashboard")
def get_dashboard_stats(db: Session = Depends(get_db), admin_user: User = Depends(get_current_admin_user)):
    total_products = db.query(Product).filter(Product.is_active == True).count()
    total_orders = db.query(Order).count()
    recent_orders = db.query(Order).order_by(Order.created_at.desc()).limit(5).all()

    
    category_stats = get_category_stats(db, admin_user)

    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "recent_orders": recent_orders,
        "category_stats": category_stats,  # 👈 this is new
    }
