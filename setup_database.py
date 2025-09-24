"""
Creates initial database data:
- Admin user
- Categories
- Sample products
Run this once after setting up the database
"""

from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import SessionLocal, engine
from models import Base, User, Category, Product

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")

def create_admin_user():
    """Create default admin user"""
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == "admin@schoolmall.co.ke").first()
        if not admin:
            hashed_password = pwd_context.hash("admin123")
            admin = User(
                email="admin@schoolmall.co.ke",
                full_name="Admin User",
                phone="+254793488207",
                hashed_password=hashed_password,
                role="admin"
            )
            db.add(admin)
            db.commit()
            print("✅ Admin user created!")
            print("   Email: admin@schoolmall.co.ke")
            print("   Password: admin123")
        else:
            print("ℹ️  Admin user already exists")
    finally:
        db.close()

def create_categories():
    """Create default categories"""
    db = SessionLocal()
    try:
        categories = [
            {"name": "Books", "slug": "books", "description": "Educational books and textbooks"},
            {"name": "Stationery", "slug": "stationery", "description": "Pens, pencils, notebooks"},
            {"name": "Technology", "slug": "technology", "description": "Computers and tech accessories"},
            {"name": "Art Supplies", "slug": "art-supplies", "description": "Art materials and craft supplies"},
            {"name": "Pre-school", "slug": "pre-school", "description": "Early childhood materials"},
            {"name": "Grade 1", "slug": "grade-1", "description": "Grade 1 materials"},
            {"name": "Grade 2", "slug": "grade-2", "description": "Grade 2 materials"},
            {"name": "Grade 3", "slug": "grade-3", "description": "Grade 3 materials"},
        ]
        
        for cat_data in categories:
            existing = db.query(Category).filter(Category.slug == cat_data["slug"]).first()
            if not existing:
                category = Category(**cat_data)
                db.add(category)
        
        db.commit()
        print("✅ Categories created successfully!")
    finally:
        db.close()

def create_sample_products():
    """Create sample products"""
    db = SessionLocal()
    try:
        books_cat = db.query(Category).filter(Category.slug == "books").first()
        stationery_cat = db.query(Category).filter(Category.slug == "stationery").first()
        tech_cat = db.query(Category).filter(Category.slug == "technology").first()
        
        products = [
            {
                "name": "TRS Guide Top Scholar Mathematics 7",
                "slug": "trs-guide-math-7",
                "description": "Comprehensive mathematics guide for Grade 7",
                "price": 525.00,
                "original_price": 550.00,
                "stock_quantity": 50,
                "category_id": books_cat.id if books_cat else None,
                "is_featured": True,
                "on_sale": True
            },
            {
                "name": "Crayola Crayon NO.24",
                "slug": "crayola-crayon-24",
                "description": "Pack of 24 vibrant colored crayons",
                "price": 700.00,
                "original_price": 720.00,
                "stock_quantity": 100,
                "category_id": stationery_cat.id if stationery_cat else None,
                "on_sale": True
            },
            {
                "name": "HP EliteBook Laptop",
                "slug": "hp-elitebook",
                "description": "Professional laptop for students",
                "price": 45000.00,
                "stock_quantity": 10,
                "category_id": tech_cat.id if tech_cat else None,
                "is_featured": True
            }
        ]
        
        for prod_data in products:
            existing = db.query(Product).filter(Product.slug == prod_data["slug"]).first()
            if not existing:
                product = Product(**prod_data)
                db.add(product)
        
        db.commit()
        print("✅ Sample products created!")
    finally:
        db.close()

def main():
    print("🚀 Setting up SchoolMall database...")
    create_tables()
    create_admin_user()
    create_categories()
    create_sample_products()
    print("\n🎉 Database setup complete!")

if __name__ == "__main__":
    main()