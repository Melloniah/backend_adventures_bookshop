from database import SessionLocal
from models import User, Category, Product
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed_data():
    db = SessionLocal()
    try:
        # admin user
        if not db.query(User).filter_by(email="admin@schoolmall.co.ke").first():
            db.add(User(
                email="admin@schoolmall.co.ke",
                full_name="Admin User",
                phone="+254793488207",
                hashed_password=pwd_context.hash("admin123"),
                role="admin"
            ))
            print("✅ Admin user created")
        else:
            print("ℹ️ Admin user already exists")    

       # Categories
        categories = [
            {"name": "Pre-school", "slug": "pre-school", "description": "Activities for pre-schoolers"},
            {"name": "Grade 1", "slug": "grade-1", "description": "Grade 1 textbooks & stationery"},
            {"name": "Grade 2", "slug": "grade-2", "description": "Grade 2 materials"},
            {"name": "Grade 3", "slug": "grade-3", "description": "Grade 3 materials"},
            {"name": "Art Supply", "slug": "arts", "description": "Everything to do with painting"},
            {"name": "Stationery", "slug": "stationery", "description": "Pens, pencils, notebooks"},
            {"name": "Technology", "slug": "technology", "description": "Computers and tech accessories"},
            {"name": "Grade 4", "slug": "grade-4", "description": "Grade 4 textbooks & materials"},
            {"name": "Grade 5", "slug": "grade-5", "description": "Grade 5 textbooks & materials"},
            {"name": "Grade 6", "slug": "grade-6", "description": "Grade 6 textbooks & materials"},
            {"name": "Grade 7", "slug": "grade-7", "description": "Grade 7 textbooks & materials"},
            {"name": "Grade 8", "slug": "grade-8", "description": "Grade 8 textbooks & materials"},
            {"name": "High School", "slug": "high-school", "description": "High school textbooks & stationery"}
        ]

        for cat in categories:
            if not db.query(Category).filter_by(slug=cat["slug"]).first():
                db.add(Category(**cat))
        print("✅ Categories seeded")

        # products - WITHOUT images (admin will add them)
        products = [
            {
                "name": "TRS Guide Top Scholar Mathematics 7",
                "slug": "trs-guide-math-7",
                "description": "Comprehensive mathematics guide for Grade 7",
                "price": 525.00,
                "original_price": 550.00,
                "stock_quantity": 50,
                "category_slug": "books",
                "is_featured": True,
                "on_sale": True,
                "image": None  # Admin will add image
            },
            {
                "name": "KCPE English Made Easy",
                "slug": "kcpe-english-easy",
                "description": "A step-by-step guide to mastering KCPE English",
                "price": 400.00,
                "original_price": 450.00,
                "stock_quantity": 30,
                "category_slug": "books",
                "is_featured": False,
                "on_sale": True,
                "image": None
            },
            {
                "name": "A4 Exercise Book (96 Pages)",
                "slug": "exercise-book-96",
                "description": "High quality A4 exercise book with 96 pages",
                "price": 55.00,
                "original_price": 60.00,
                "stock_quantity": 200,
                "category_slug": "stationery",
                "is_featured": True,
                "on_sale": False,
                "image": None
            },
            {
                "name": "Blue Ballpoint Pen (Pack of 10)",
                "slug": "blue-pen-pack-10",
                "description": "Durable blue pens, smooth writing experience",
                "price": 150.00,
                "original_price": 180.00,
                "stock_quantity": 100,
                "category_slug": "stationery",
                "is_featured": False,
                "on_sale": False,
                "image": None
            },
            {
                "name": "Scientific Calculator Casio fx-991EX",
                "slug": "casio-fx-991ex",
                "description": "Advanced scientific calculator, perfect for high school & college",
                "price": 2950.00,
                "original_price": 3100.00,
                "stock_quantity": 15,
                "category_slug": "technology",
                "is_featured": True,
                "on_sale": True,
                "image": None
            },
            {
                "name": "HP 250 G8 Laptop (Core i5, 8GB RAM, 256GB SSD)",
                "slug": "hp-250-g8",
                "description": "Reliable and affordable laptop for students & professionals",
                "price": 61500.00,
                "original_price": 65000.00,
                "stock_quantity": 5,
                "category_slug": "technology",
                "is_featured": False,
                "on_sale": True,
                "image": None
            },
        ]

        for prod in products:
            if not db.query(Product).filter_by(slug=prod["slug"]).first():
                category = db.query(Category).filter_by(slug=prod["category_slug"]).first()
                if category:
                    db.add(Product(
                        name=prod["name"],
                        slug=prod["slug"],
                        description=prod["description"],
                        price=prod["price"],
                        original_price=prod["original_price"],
                        stock_quantity=prod["stock_quantity"],
                        category_id=category.id,
                        is_featured=prod["is_featured"],
                        on_sale=prod["on_sale"],
                        image=prod["image"]
                    ))
        print(" Products seeded")

        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()