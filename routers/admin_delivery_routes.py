# routers/admin_delivery_routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import DeliveryRoute, DeliveryStop
from schemas import DeliveryRouteCreate, DeliveryRouteUpdate, DeliveryRouteRead
from routers.auth import get_current_admin_user
from schemas import User

router = APIRouter(tags=["Admin Delivery Routes"])



@router.get("/", response_model=list[DeliveryRouteRead])
def get_all_delivery_routes(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Fetch all delivery routes including their stops."""
    routes = db.query(DeliveryRoute).all()
    return routes

@router.get("/{route_id}", response_model=DeliveryRouteRead)
def get_delivery_route_by_id(
    route_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """Fetch a single delivery route by ID."""
    route = db.query(DeliveryRoute).filter_by(id=route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route

@router.post("/", response_model=DeliveryRouteRead, status_code=201)
def create_delivery_route(
    route_data: DeliveryRouteCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    if db.query(DeliveryRoute).filter_by(name=route_data.name).first():
        raise HTTPException(status_code=400, detail="Route name already exists")

    route = DeliveryRoute(name=route_data.name)
    db.add(route)
    db.flush()

    for s in route_data.stops:
        if any(existing.name.lower() == s.name.lower() for existing in route.stops):
            raise HTTPException(status_code=400, detail=f"Duplicate stop '{s.name}' in route '{route.name}'")
        stop = DeliveryStop(name=s.name, price=s.price, route_id=route.id)
        db.add(stop)
    

    db.commit()
    db.refresh(route)
    return route


@router.put("/{route_id}", response_model=DeliveryRouteRead)
def update_delivery_route(
    route_id: int,
    route_data: DeliveryRouteUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    route = db.query(DeliveryRoute).filter_by(id=route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    if route_data.name:
        route.name = route_data.name

    if route_data.stops is not None:
        db.query(DeliveryStop).filter_by(route_id=route.id).delete()
        for s in route_data.stops:
            stop = DeliveryStop(name=s.name, price=s.price, route_id=route.id)
            db.add(stop)

    db.commit()
    db.refresh(route)
    return route


@router.delete("/{route_id}")
def delete_delivery_route(
    route_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    route = db.query(DeliveryRoute).filter_by(id=route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    db.delete(route)
    db.commit()
    return {"message": f"Route '{route.name}' deleted successfully"}

    
