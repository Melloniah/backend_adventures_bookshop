"""
Safe database setup script for production.

Ensures an admin user exists.
Keeps hierarchical category support (but seeds no categories/products/routes).
Does NOT drop or recreate tables.
"""

import os
import bcrypt
from sqlalchemy.exc import SQLAlchemyError
from database import SessionLocal
from models import User
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "adventuresbooks@gmail.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "ChangeMe123")
BCRYPT_MAX_BYTES = 72
DEFAULT_ROUNDS = 12


def get_password_hash(password: str) -> str:
    password_bytes = password.encode("utf-8")[:BCRYPT_MAX_BYTES]
    salt = bcrypt.gensalt(rounds=DEFAULT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def seed_data():
    """Ensure admin user exists. Does not drop tables or seed other data."""
    with SessionLocal() as db:
        try:
            admin = db.query(User).filter_by(email=ADMIN_EMAIL).first()
            if not admin:
                db.add(
                    User(
                        email=ADMIN_EMAIL,
                        full_name="Admin User",
                        phone="+254724047489",
                        hashed_password=get_password_hash(ADMIN_PASSWORD),
                        role="admin",
                    )
                )
                db.commit()
                print(f"✅ Admin user '{ADMIN_EMAIL}' created successfully.")
            else:
                print(f"ℹ️ Admin user '{ADMIN_EMAIL}' already exists. No changes made.")
        except SQLAlchemyError as e:
            db.rollback()
            print(f"❌ Failed to seed admin user: {e}")
            raise


if __name__ == "__main__":
    seed_data()
