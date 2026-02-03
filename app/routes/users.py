from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.user import User
from app.schemas.user import UserRead
from app.routes.deps import get_current_user

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/me", response_model=UserRead)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Lấy thông tin profile của chính mình sau khi login"""
    return current_user

@router.get("/all", response_model=list[UserRead])
async def get_all_users(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Lấy danh sách tất cả người dùng trong hệ thống"""
    users = db.exec(select(User)).all()
    return users