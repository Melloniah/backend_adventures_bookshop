from database import SessionLocal
from models import User

db = SessionLocal()
admin = db.query(User).filter(User.email == "admin@schoolmall.co.ke").first()

if admin:
    print(f"Email: {admin.email}")
    print(f"Password hash: {admin.hashed_password}")
    print(f"Hash length: {len(admin.hashed_password)}")
    print(f"Starts with: {admin.hashed_password[:10] if len(admin.hashed_password) >= 10 else admin.hashed_password}")
    print(f"Is bcrypt format: {admin.hashed_password.startswith('$2')}")
else:
    print("Admin user not found")

db.close()