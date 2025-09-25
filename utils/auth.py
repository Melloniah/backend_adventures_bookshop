# utils/auth.py
from fastapi import Depends, HTTPException, status
from routers.auth import get_current_active_user
from models import User

# Admin guard
def get_current_admin(current_user: User = Depends(get_current_active_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
