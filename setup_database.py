

import os
import bcrypt
from sqlalchemy.exc import SQLAlchemyError
from database import SessionLocal, Base, engine
from models import User, Category, Product, DeliveryRoute, DeliveryStop
from dotenv import load_dotenv

# --- Load environment variables ---
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "adventuresbooks@gmail.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ChangeMe123")  # Will prompt you to change in prod
BCRYPT_MAX_BYTES = 72
DEFAULT_ROUNDS = 12

# --- Password hashing ---
def get_password_hash(password: str) -> str:
    password_bytes = password.encode("utf-8")[:BCRYPT_MAX_BYTES]
    salt = bcrypt.gensalt(rounds=DEFAULT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")

# --- Ensure tables exist ---
Base.metadata.create_all(bind=engine)

# --- Seed data ---
def seed_data():
    db = SessionLocal()
    try:
        # --- ADMIN USER ---
        admin_user = db.query(User).filter_by(email=ADMIN_EMAIL).first()
        if not admin_user:
            db.add(User(
                email=ADMIN_EMAIL,
                full_name="Admin User",
                phone="+254724047489",
                hashed_password=get_password_hash(ADMIN_PASSWORD),
                role="admin"
            ))
            db.commit()
            print(f"✅ Admin user '{ADMIN_EMAIL}' created")
        else:
            print(f"ℹ️ Admin user '{ADMIN_EMAIL}' already exists")

        # --- CATEGORIES ---
        categories = [
            {"name": "Pre-school", "slug": "pre-school", "description": "Activities for pre-schoolers"},
            {"name": "Grade 1", "slug": "grade 1", "description": "Grade 1 textbooks & stationery"},
            {"name": "Grade 2", "slug": "grade 2", "description": "Grade 2 materials"},
            {"name": "Grade 3", "slug": "grade 3", "description": "Grade 3 materials"},
            {"name": "Grade 4", "slug": "grade 4", "description": "Grade 4 textbooks & materials"},
            {"name": "Grade 5", "slug": "grade 5", "description": "Grade 5 textbooks & materials"},
            {"name": "Grade 6", "slug": "grade 6", "description": "Grade 6 textbooks & materials"},
            {"name": "Grade 7", "slug": "grade 7", "description": "Grade 7 textbooks & materials"},
            {"name": "Grade 8", "slug": "grade 8", "description": "Grade 8 textbooks & materials"},
            {"name": "Grade 9", "slug": "grade 9", "description": "Grade 9 textbooks & materials"},
            {"name": "Grade 10", "slug": "grade 10", "description": "Grade 10 textbooks & materials"},
            {"name": "Art Supply", "slug": "arts", "description": "Everything to do with painting"},
            {"name": "Stationery", "slug": "stationery", "description": "Pens, pencils, notebooks"},
            {"name": "Toys", "slug": "toys", "description": "Educational toys for kids"},
            {"name": "Technology", "slug": "technology", "description": "Computers and tech accessories"},
            {"name": "Books", "slug": "books", "description": "Educational books and guides"}
        ]

        for cat in categories:
            existing = db.query(Category).filter_by(name=cat["name"]).first()
            if existing:
                existing.slug = cat["slug"]
                existing.description = cat["description"]
                existing.is_active = True
            else:
                db.add(Category(**cat))
        db.commit()
        print("✅ Categories seeded/updated successfully")

        # --- PRODUCTS ---
        products = [
           
            {
                "name": "KCPE English Made Easy",
                "slug": "kcpe-english-easy",
                "description": "Step-by-step guide to mastering KCPE English",
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
        ]
        for prod in products:
            existing = db.query(Product).filter_by(slug=prod["slug"]).first()
            if not existing:
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
        db.commit()
        print("✅ Products seeded")

        # --- DELIVERY ROUTES & STOPS ---
        routes_data = {
            "CBD Route": [{"name": "CBD", "price": 100}],
            "Mombasa Road": [
                {"name": "South B", "price": 300},
                {"name": "South C", "price": 300},
                {"name": "Imara Daima", "price": 350}
            ],
               "Langata Road": [
                {"name": "Madaraka", "price": 300},
                {"name": "Tmall", "price": 350},
                {"name": "Nairobi West Shopping Center", "price": 380},
                {"name": "Langata", "price": 400},
                {"name": "Kiserian", "price": 420},
                {"name": "Rongai Maasai Lodge", "price": 450},
                {"name": "Karen Galleria", "price": 420}
            ],
            "Waiyaki Way": [
                {"name": "Westlands", "price": 350},
                {"name": "Loresho", "price": 380},
                {"name": "Kangemi", "price": 400},
                {"name": "Uthiru", "price": 420},
                {"name": "Lower Kabete", "price": 450},
                {"name": "Kinoo", "price": 450},
                {"name": "Kikuyu", "price": 480}
            ],
            "Kiambu Road": [
                {"name": "Thindigua", "price": 350},
                {"name": "Kiambu Town", "price": 400},
                {"name": "Kirigiti", "price": 430}
            ],
            "Limuru Road": [
                {"name": "Ruaka Arcade", "price": 350},
                {"name": "Ruaka Business Park", "price": 380},
                {"name": "Village Market", "price": 400},
                {"name": "Two Rivers Mall", "price": 420}
            ],
            "Jogoo Road": [
                {"name": "Buruburu", "price": 350},
                {"name": "Umoja Market", "price": 380},
                {"name": "Umoja 1", "price": 400},
                {"name": "Umoja Kwa Chief", "price": 400},
                {"name": "Komarock Kmall", "price": 420},
                {"name": "Donholm", "price": 420},
                {"name": "Fedha Estate", "price": 420},
                {"name": "Nyayo Embakasi", "price": 450},
                {"name": "Utawala Shooters", "price": 500},
                {"name": "Utawala Benedicta", "price": 520},
                {"name": "Choka", "price": 500},
                {"name": "Ruai", "price": 550}
            ],
            "Thika Road": [
                {"name": "Alsops-Ruaraka", "price": 300},
                {"name": "Lucky Summer", "price": 300},
                {"name": "Roasters", "price": 320},
                {"name": "Marurui", "price": 320},
                {"name": "Kasarani Police Station", "price": 350},
                {"name": "Kasarani Seasons", "price": 360},
                {"name": "Kasarani Maternity", "price": 380},
                {"name": "Gumba Estate", "price": 400},
                {"name": "TRM Drive", "price": 360},
                {"name": "Roysambu", "price": 350},
                {"name": "Zimmerman", "price": 380},
                {"name": "USIU", "price": 380},
                {"name": "Wendani", "price": 400},
                {"name": "Sukari", "price": 420},
                {"name": "KU", "price": 430},
                {"name": "Ruiru Bypass", "price": 450},
                {"name": "Ruiru Ndani", "price": 450},
                {"name": "Juja Stage", "price": 480}
            ],
            "Ngong Road": [
                {"name": "Upper Hill", "price": 300},
                {"name": "Jamhuru Shopping Center", "price": 320},
                {"name": "Kilimani", "price": 350},
                {"name": "Lavington", "price": 380},
                {"name": "Wanyee Road", "price": 390},
                {"name": "Ngong Racecourse", "price": 400},
                {"name": "Karen", "price": 450}
            ]
        }

        print("🚚 Seeding delivery routes & stops...")
        for route_name, stops in routes_data.items():
            try:
                existing_route = db.query(DeliveryRoute).filter_by(name=route_name).first()
                if not existing_route:
                    route = DeliveryRoute(name=route_name)
                    db.add(route)
                    db.flush()  # get route.id

                    for stop_data in stops:
                        db.add(DeliveryStop(
                            name=stop_data["name"],
                            price=stop_data["price"],
                            route_id=route.id
                        ))
                    db.commit()
                    print(f"✅ Added route '{route_name}' with {len(stops)} stops")
                else:
                    print(f"ℹ️ Route '{route_name}' already exists")
            except SQLAlchemyError as e:
                db.rollback()
                print(f"❌ Failed to seed route '{route_name}': {e}")

    except SQLAlchemyError as e:
        db.rollback()
        print(f"❌ Seeding failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
