from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import bcrypt
import os

from database import get_db
from models import User
from schemas import UserLogin
from config import settings

# --- Constants ---
BCRYPT_MAX_BYTES = 72
DEFAULT_ROUNDS = 12
IS_PRODUCTION = os.getenv("ENVIRONMENT") == "production"


# ----- PASSWORD UTILS -----
def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt directly."""
    password_bytes = password.encode('utf-8')[:BCRYPT_MAX_BYTES]
    salt = bcrypt.gensalt(rounds=DEFAULT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash."""
    try:
        password_bytes = plain_password.encode('utf-8')[:BCRYPT_MAX_BYTES]
        hashed_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


# ----- JWT UTILS -----
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    expires_delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = data.copy()
    to_encode.update({"exp": datetime.utcnow() + expires_delta})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ----- USER HELPERS -----
def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


# ----- DEPENDENCIES -----
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = request.cookies.get("token")
    if not token:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_email(db, email=email)
    if not user:
        raise credentials_exception
    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    """Admin check: allow env-based or DB role-based admin."""
    env_email = os.getenv("ADMIN_EMAIL")
    if current_user.email == env_email:
        return current_user
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=403, detail="Not authorized as admin")
    return current_user


# ----- ROUTER -----
router = APIRouter()


# --- LOGIN ---
@router.post("/login")
def login_admin(user_login: UserLogin, db: Session = Depends(get_db)):
    env_email = os.getenv("ADMIN_EMAIL")
    env_password = os.getenv("ADMIN_PASSWORD")

    # Determine admin user (env or DB)
    user_dict = None
    if env_email and env_password and user_login.email == env_email and user_login.password == env_password:
        # Env admin
        user_dict = {"id": 0, "email": env_email, "role": "admin"}
        user_email = env_email
    else:
        # DB admin
        user_obj = authenticate_user(db, user_login.email, user_login.password)
        if not user_obj:
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        if user_obj.role != "admin":
            raise HTTPException(status_code=403, detail="Not authorized as admin")
        user_dict = {"id": user_obj.id, "email": user_obj.email, "role": user_obj.role}
        user_email = user_obj.email

    # Create JWT token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user_email}, expires_delta=access_token_expires)

    # Unified cookie params
    cookie_params = {
        "key": "token",
        "value": access_token,
        "httponly": True,
        "path": "/",
        "samesite": "None" if IS_PRODUCTION else "Lax",
        "secure": IS_PRODUCTION,
    }
    if IS_PRODUCTION:
        cookie_params["domain"] = ".adventuresbookshop.org"

    response = JSONResponse(
        content={"access_token": access_token, "token_type": "bearer", "user": user_dict}
    )
    response.set_cookie(**cookie_params)
    return response


# --- LOGOUT ---
@router.post("/logout")
def logout_admin():
    cookie_params = {
        "key": "token",
        "value": "",
        "httponly": True,
        "path": "/",
        "samesite": "None" if IS_PRODUCTION else "Lax",
        "secure": IS_PRODUCTION,
        "max_age": 0,
    }
    if IS_PRODUCTION:
        cookie_params["domain"] = ".adventuresbookshop.org"

    response = JSONResponse(content={"detail": "Logged out successfully"})
    response.delete_cookie(key="token", path=cookie_params["path"])
    return response


# --- CURRENT USER ---
@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email, "role": current_user.role}
