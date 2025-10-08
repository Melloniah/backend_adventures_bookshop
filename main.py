# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles

# from database import engine
# from models import Base
# from routers import (
#     products, orders, auth, payments, categories,
#     admin, admin_products, admin_orders, admin_banners, hero_banners, delivery_routes, admin_delivery_routes
# )


# # Create database tables
# Base.metadata.create_all(bind=engine)

# app = FastAPI(title="Adventures Bookshop API", redirect_slashes=False)  # optional: disable auto-redirect

# # CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["http://localhost:3000"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Static files
# app.mount("/static", StaticFiles(directory="static"), name="static")

# # Public routes
# app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
# app.include_router(products.router, prefix="/products", tags=["Products"])
# app.include_router(orders.router, prefix="/orders", tags=["Orders"])
# app.include_router(payments.router, prefix="/payments", tags=["Payments"])
# app.include_router(categories.router, prefix="/categories", tags=["Categories"])
# app.include_router(hero_banners.router, prefix="/hero-banners", tags=["HeroBanners"])  # public
# app.include_router(delivery_routes.router, prefix="/delivery", tags=["DeliveryRoutes"])


# # Admin routes
# app.include_router(admin.router, prefix="/admin", tags=["Admin"])
# app.include_router(admin_products.router, prefix="/admin/products", tags=["Admin Products"])
# app.include_router(admin_orders.router, prefix="/admin/orders", tags=["Admin Orders"])
# app.include_router(admin_banners.router, prefix="/admin/hero-banners", tags=["Admin Banners"])
# app.include_router(admin_delivery_routes.router, prefix="/admin/delivery-routes", tags=["Admin Delivery Routes"])


# @app.get("/")
# async def root():
#     return {"message": "AdventurersBookshop API is running!"}


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import engine
from models import Base
from routers import (
    products, orders, auth, payments, categories,
    admin, admin_products, admin_orders, admin_banners, 
    hero_banners, delivery_routes, admin_delivery_routes
)

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# Only auto-create tables in development
if ENVIRONMENT == "development":
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Adventures Bookshop API",
    redirect_slashes=False,
    docs_url="/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/redoc" if ENVIRONMENT == "development" else None,
)

# CORS configuration
cors_origins = [
    origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Public routes
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])
app.include_router(payments.router, prefix="/payments", tags=["Payments"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(hero_banners.router, prefix="/hero-banners", tags=["HeroBanners"])
app.include_router(delivery_routes.router, prefix="/delivery", tags=["DeliveryRoutes"])

# Admin routes
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(admin_products.router, prefix="/admin/products", tags=["Admin Products"])
app.include_router(admin_orders.router, prefix="/admin/orders", tags=["Admin Orders"])
app.include_router(admin_banners.router, prefix="/admin/hero-banners", tags=["Admin Banners"])
app.include_router(admin_delivery_routes.router, prefix="/admin/delivery-routes", tags=["Admin Delivery Routes"])

@app.get("/")
async def root():
    return {"message": "AdventurersBookshop API is running!", "environment": ENVIRONMENT}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "environment": ENVIRONMENT, "database": "connected"}
