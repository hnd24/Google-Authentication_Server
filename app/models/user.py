from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, timezone

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    picture: Optional[str] = None
    google_id: str = Field(unique=True)
    
    # Lưu Refresh Token của Google để dùng cho các tác vụ nền sau này
    google_refresh_token: Optional[str] = None 
    
    is_active: bool = Field(default=True)
    # Dùng timezone-aware datetime như bạn đã sửa ở file security
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )