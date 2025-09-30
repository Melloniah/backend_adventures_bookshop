"""
Manages all environment variables and configuration
Uses python-decouple to read from .env file
"""

from decouple import config

class Settings:
    # Database
    DATABASE_URL: str = config("DATABASE_URL", default="postgresql://user:password@localhost/schoolmall")
    
    # Security
    SECRET_KEY: str = config("JWT_SECRET", default="your-secret-key-change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email Configuration
    MAIL_USERNAME: str = config("MAIL_USERNAME", default="")
    MAIL_PASSWORD: str = config("MAIL_PASSWORD", default="")
    MAIL_FROM: str = config("MAIL_FROM", default="noreply@schoolmall.co.ke")
    MAIL_PORT: int = config("MAIL_PORT", default=587, cast=int)
    MAIL_SERVER: str = config("MAIL_SERVER", default="smtp.gmail.com")
    
    # M-Pesa Configuration
    MPESA_CONSUMER_KEY: str = config("MPESA_CONSUMER_KEY", default="")
    MPESA_CONSUMER_SECRET: str = config("MPESA_CONSUMER_SECRET", default="")
    MPESA_SHORTCODE: str = config("MPESA_SHORTCODE", default="174379")
    MPESA_PASSKEY: str = config("MPESA_PASSKEY", default="")
    MPESA_CALLBACK_URL: str = config("MPESA_CALLBACK_URL", default="https://yourdomain.com/payments/callback")
    
    # WhatsApp Configuration
    WHATSAPP_TOKEN: str = config("WHATSAPP_TOKEN", default="")
    WHATSAPP_PHONE_NUMBER_ID: str = config("WHATSAPP_PHONE_NUMBER_ID", default="")

settings = Settings()