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
            print(" Admin user already exists")    

        # categories
        categories = [
            {"name": "Books", "slug": "books", "description": "Educational books and textbooks"},
            {"name": "Stationery", "slug": "stationery", "description": "Pens, pencils, notebooks"},
            {"name": "Technology", "slug": "technology", "description": "Computers and tech accessories"},
        ]
        for cat in categories:
            if not db.query(Category).filter_by(slug=cat["slug"]).first():
                db.add(Category(**cat))
        print("✅ Categories seeded")

        # products
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
                "image": "/maths7.jpg"
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
                "on_sale": False,
                "image": "/english.jpg"
            },
            {
                "name": "A4 Exercise Book (96 Pages)",
                "slug": "exercise-book-96",
                "description": "High quality A4 exercise book with 96 pages",
                "price": 55.00,
                "original_price": 60.00,
                "stock_quantity": 200,
                "category_slug": "stationery",
                "is_featured": False,
                "on_sale": True,
                "image": "/exercise-book.jpg"
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
                "image": "/blue-pen.jpg"
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
                "image": "/casio.jpg"
            },
            {
                "name": "HP 250 G8 Laptop (Core i5, 8GB RAM, 256GB SSD)",
                "slug": "hp-250-g8",
                "description": "Reliable and affordable laptop for students & professionals",
                "price": 61500.00,
                "original_price": 65000.00,
                "stock_quantity": 5,
                "category_slug": "technology",
                "is_featured": True,
                "on_sale": False,
                "image": "/hp-250.jpg"
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
        print("✅ Products seeded")

        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
