from fastapi import APIRouter, Request, Depends, Response, HTTPException, Cookie
from fastapi.responses import HTMLResponse
from authlib.integrations.starlette_client import OAuth
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from sqlmodel import Session, select
from typing import Optional

from app.core.config import settings
from app.core.database import get_session
from app.core.security import create_access_token, create_refresh_token, verify_token
from app.models.user import User
from app.schemas.user import Token

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Cấu hình Authlib
oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

@router.get("/login")
async def login(request: Request):
    """Bắt đầu luồng OAuth bằng cách điều hướng sang Google"""
    return await oauth.google.authorize_redirect(request, settings.GOOGLE_REDIRECT_URI)

@router.get("/callback")
async def auth_callback(request: Request, response: Response, db: Session = Depends(get_session)):
    """Xử lý kết quả trả về từ Google"""
    # 1. Trao đổi mã 'code' lấy bộ token từ Google
    token_data = await oauth.google.authorize_access_token(request)
    
    # 2. Giám định tính nguyên vẹn của id_token bằng google-auth
    try:
        id_info = id_token.verify_oauth2_token(
            token_data['id_token'], 
            google_requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Xác thực Google thất bại")

    # 3. Tìm hoặc tạo User trong database
    user = db.exec(select(User).where(User.email == id_info['email'])).first()
    
    if not user:
        user = User(
            email=id_info['email'],
            full_name=id_info.get('name'),
            picture=id_info.get('picture'),
            google_id=id_info.get('sub'),
            google_refresh_token=token_data.get('refresh_token') # Lưu cho tác vụ nền
        )
        db.add(user)
    else:
        # Cập nhật thông tin mới nhất
        user.full_name = id_info.get('name')
        user.picture = id_info.get('picture')
        if token_data.get('refresh_token'):
            user.google_refresh_token = token_data.get('refresh_token')
        db.add(user)

    db.commit()
    db.refresh(user)

    # 4. Cấp phát App JWT
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})

    # 5. Thiết lập Http-only Cookie (Bảo mật tuyệt đối)
    response.set_cookie(
        key="app_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False, # Đổi thành True khi chạy HTTPS
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )

    # 6. Gửi tín hiệu về cửa sổ cha (React) và tự đóng popup
    return HTMLResponse(content=f"""
        <script>
            window.opener.postMessage({{ 
                type: "AUTH_SUCCESS", 
                access_token: "{access_token}" 
            }}, "http://localhost:3000");
            window.close();
        </script>
    """)

@router.post("/refresh", response_model=Token)
async def refresh_session(
    response: Response,
    app_refresh_token: Optional[str] = Cookie(None)
):
    """Cơ chế Sliding Window: Làm mới phiên mà không cần login lại"""
    if not app_refresh_token:
        raise HTTPException(status_code=401, detail="Phiên đăng nhập hết hạn")
    
    payload = verify_token(app_refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn")

    user_id = payload.get("sub")
    
    # Tạo cặp token mới để kéo dài thời gian sống (Sliding Window)
    new_access = create_access_token({"sub": user_id})
    new_refresh = create_refresh_token({"sub": user_id})

    # Cập nhật lại Cookie mới
    response.set_cookie(
        key="app_refresh_token", value=new_refresh,
        httponly=True, samesite="lax", max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    )
    
    return {"access_token": new_access, "token_type": "bearer"}

@router.post("/logout")
async def logout(response: Response):
    """Xóa bỏ cookie để đăng xuất"""
    response.delete_cookie("app_refresh_token")
    return {"detail": "Logged out successfully"}