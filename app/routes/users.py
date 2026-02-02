from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from app.core.database import get_session
from app.core.security import verify_token
from app.models.user import User
from app.schemas.user import UserRead
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated

router = APIRouter(prefix="/users", tags=["Users"])

# Định nghĩa cách lấy token từ header Authorization: Bearer <token>
reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(
    token: Annotated[str, Depends(reusable_oauth2)],
    db: Annotated[Session, Depends(get_session)]
) -> User:
    """Dependency: Xác thực người dùng qua JWT"""
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token không hợp lệ")
    
    user_id = payload.get("sub")
    user = db.get(User, int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
    
    return user

@router.get("/me", response_model=UserRead)
async def read_user_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Lấy thông tin cá nhân của người dùng hiện tại"""
    # Nhờ response_model=UserRead, các thông tin nhạy cảm như google_refresh_token sẽ bị loại bỏ
    return current_user