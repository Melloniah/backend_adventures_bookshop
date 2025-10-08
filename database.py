# """
# Sets up SQLAlchemy database connection and session management
# """
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker, declarative_base
# from decouple import config

# # Load DATABASE_URL from .env
# DATABASE_URL = config("DATABASE_URL", default="sqlite:///./dev.db")

# # SQLite needs extra args
# if DATABASE_URL.startswith("sqlite"):
#     engine = create_engine(
#         DATABASE_URL, connect_args={"check_same_thread": False}
#     )
# else:
#     engine = create_engine(DATABASE_URL)

# # Session factory
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# # Base class for models
# Base = declarative_base()

# # Dependency for FastAPI routes
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv
load_dotenv()


# Load DATABASE_URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")

# Convert postgres:// → postgresql:// if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite for development
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
# PostgreSQL for production
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        pool_recycle=3600,
    )

# ✅ Define Base here
Base = declarative_base()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
