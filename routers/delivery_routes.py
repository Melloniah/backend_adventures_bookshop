# routers/delivery_routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import DeliveryRoute, DeliveryStop
from schemas import DeliveryRouteRead, DeliveryStopRead
from typing import List

router = APIRouter(tags=["Delivery"])

# -------------------------------
# Get all routes with stops
# -------------------------------
@router.get("/routes", response_model=List[DeliveryRouteRead])
def get_all_routes(db: Session = Depends(get_db)):
    routes = db.query(DeliveryRoute).options(joinedload(DeliveryRoute.stops)).all()
    return routes


# -------------------------------
# Get single route by ID
# -------------------------------
@router.get("/routes/{route_id}", response_model=DeliveryRouteRead)
def get_route_by_id(route_id: int, db: Session = Depends(get_db)):
    route = db.query(DeliveryRoute).options(joinedload(DeliveryRoute.stops)).filter_by(id=route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")
    return route


# -------------------------------
# Search stops by name (case-insensitive)
# -------------------------------
@router.get("/stops/{stop_name}", response_model=List[DeliveryStopRead])
def get_stops_by_name(stop_name: str, db: Session = Depends(get_db)):
    stops = db.query(DeliveryStop).filter(DeliveryStop.name.ilike(f"%{stop_name}%")).all()
    if not stops:
        raise HTTPException(status_code=404, detail="No matching stops found")
    return stops
