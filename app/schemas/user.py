from sqlmodel import SQLModel
from typing import Optional
from uuid import UUID

# Schema dùng để trả thông tin User về cho React (Response)
class UserRead(SQLModel):
    id: int
    email: str
    full_name: Optional[str] = None
    picture: Optional[str] = None
    is_active: bool

# Schema dùng để định nghĩa cấu trúc Access Token trả về cho React
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"

# Schema chứa thông tin giải mã từ Token (Dùng nội bộ ở Backend)
class TokenData(SQLModel):
    user_id: Optional[str] = None