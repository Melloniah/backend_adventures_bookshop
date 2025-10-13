import os
from dotenv import load_dotenv

# Load appropriate .env file based on ENVIRONMENT
env = os.getenv("ENVIRONMENT", "development")
if env == "production":
    load_dotenv(".env.production")
else:
    load_dotenv(".env")

class Settings:
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # JWT Settings - Add SECRET_KEY alias
    JWT_SECRET = os.getenv("JWT_SECRET")
    SECRET_KEY = os.getenv("JWT_SECRET")  # ✅ Add this line - alias for JWT_SECRET
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")  # ✅ Add this alias too
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))
    
    # CORS - Fix empty string issue
    _cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
    CORS_ORIGINS = [origin.strip() for origin in _cors_origins.split(",") if origin.strip()]  # ✅ Filter empty strings
    
    # M-Pesa
    MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
    MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
    MPESA_SHORTCODE = os.getenv("MPESA_SHORTCODE")
    MPESA_PASSKEY = os.getenv("MPESA_PASSKEY")
    MPESA_ENVIRONMENT = os.getenv("MPESA_ENVIRONMENT")

    # Email
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
    FROM_EMAIL = os.getenv("FROM_EMAIL")
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    SMTP_HOST = os.getenv("SMTP_HOST")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))

settings = Settings()
