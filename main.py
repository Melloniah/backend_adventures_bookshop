"""
Main application file that:
- Creates FastAPI app instance
- Sets up CORS for frontend communication
- Includes all route modules
- Serves static files (images)
- Creates database tables on startup
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import Depends
from database import engine
from models import Base
from routers import products, orders, auth, admin, payments
from routers.auth import get_current_admin_user

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Zeus technologie API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded images
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routes
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])
# app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(payments.router, prefix="/payments", tags=["Payments"])
# app.include_router(categories.router, prefix="/categories", tags=["Categories"])

# Admin routes with global admin dependency
app.include_router(
    admin.router,
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(get_current_admin_user)]
)

@app.get("/")
async def root():
    return {"message": "AdventurersBookshop API is running!"}
