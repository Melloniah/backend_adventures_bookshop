from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import bcrypt

from database import get_db
from models import User
from schemas import UserLogin
from config import settings

router = APIRouter(redirect_slashes=False)



def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash"""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(
        password.encode('utf-8'), 
        bcrypt.gensalt()
    ).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Always use configured expiry from settings unless explicitly overridden"""
    expires_delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Try cookie first
    token = request.cookies.get("token")
    # Fallback: Authorization header
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
    if user is None:
        raise credentials_exception
    return user

async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized as admin")
    return current_user

@router.post("/login")
def login_admin(user_login: UserLogin, db: Session = Depends(get_db)):
    # ADD THIS DEBUG
    print(f"\n{'='*50}")
    print(f"LOGIN ATTEMPT")
    print(f"Email received: '{user_login.email}'")
    print(f"Password received: '{user_login.password}'")
    print(f"Password length: {len(user_login.password)} chars")
    print(f"Password bytes: {len(user_login.password.encode('utf-8'))} bytes")
    print(f"{'='*50}\n")
    
    user = authenticate_user(db, user_login.email, user_login.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized as admin")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)

    user_dict = {"id": user.id, "email": user.email, "role": user.role}

    response = JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_dict,
        }
    )
    response.set_cookie(
        key="token",
        value=access_token,
        httponly=True,
        path="/",
        samesite="Lax",
        secure=False,
    )
    return response


@router.post("/logout")
def logout_admin():
    response = JSONResponse(content={"detail": "Logged out successfully"})
    response.delete_cookie(
        key="token",
        path="/",
        samesite="Lax",
        secure=False,  # change to True in production
    )
    return response

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "email": current_user.email, "role": current_user.role}
