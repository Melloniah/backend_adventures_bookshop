from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import engine
from models import Base
from routers import products, orders, auth, admin, payments, categories, hero_banners
from routers.auth import get_current_admin_user

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Zeus technologie API")

# CORS middleware - add this FIRST
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    #  allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])
app.include_router(payments.router, prefix="/payments", tags=["Payments"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(hero_banners.router, prefix="/hero-banners", tags=["HeroBanners"])


app.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin"],
    # dependencies=[Depends(get_current_admin_user)]
)

@app.get("/")
async def root():
    return {"message": "AdventurersBookshop API is running!"}