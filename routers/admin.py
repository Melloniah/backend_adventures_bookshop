from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models import User, Product, Order
from routers.auth import get_current_admin_user
from routers.admin_categories import calculate_category_stats

router = APIRouter()

@router.get("/dashboard")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    admin_user = Depends(get_current_admin_user)
):
    total_products = db.query(Product).filter(Product.is_active == True).count()
    total_orders = db.query(Order).count()

    #  Convert ORM objects into dicts
    recent_orders = [
        {
            "id": o.id,
            "customer_name": o.customer_name,
            "customer_phone": o.customer_phone,
            "total_amount": o.total_amount,
            "status": o.status,
            "created_at": o.created_at,
        }
        for o in db.query(Order).order_by(Order.created_at.desc()).limit(5).all()
    ]

    category_stats = calculate_category_stats(db)

    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "recent_orders": recent_orders,
        "category_stats": category_stats,
    }
