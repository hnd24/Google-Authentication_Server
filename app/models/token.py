from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime, timezone

class Token(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    refresh_token: str = Field(index=True, unique=True)
    user_id: int = Field(foreign_key="user.id")
    
    # Thông tin bổ sung để quản lý bảo mật
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_revoked: bool = Field(default=False) # Dùng để hủy token khi logout