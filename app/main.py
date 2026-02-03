from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_db, dispose_engine
# Import cả hai router auth và users
from app.routes import auth, users 

# Quản lý vòng đời ứng dụng (Lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP: Chạy khi khởi động server ---
    print("🚀 Khởi động hệ thống...")
    init_db() # Tự động tạo các bảng User, Token nếu chưa có
    print("🍀 Database đã sẵn sàng.")
    yield
    # --- SHUTDOWN: Chạy khi tắt server ---
    print("🛑 Đang tắt hệ thống...")
    dispose_engine() # Giải phóng tài nguyên kết nối
    print("🍀 Kết nối Database đã đóng sạch sẽ.")

app = FastAPI(
    title="Google OAuth2 Server", 
    version="1.0.0",
    lifespan=lifespan # Gắn lifespan vào app
)

# --- Cấu hình Middleware (Theo thứ tự ưu tiên) ---

# 1. SessionMiddleware: Bắt buộc cho Authlib để lưu state tạm thời trong luồng OAuth
app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.SECRET_KEY,
    session_cookie="auth_session",
    max_age=3600,
    same_site="lax",   # Cho phép gửi cookie khi chuyển hướng từ Google về
    https_only=False,  # Bắt buộc là False vì bạn đang dùng HTTP (127.0.0.1)
)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    settings.CLIENT_URL, # Đảm bảo biến này trong .env là http://127.0.0.1:3000
]

# 2. CORSMiddleware: Cho phép React kết nối an toàn từ CLIENT_URL (http://127.0.0.1:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Đảm bảo biến này là http://127.0.0.1:3000
    allow_credentials=True, # Cho phép gửi nhận Cookie http-only (Refresh Token)
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Đăng ký các Router ---
app.include_router(auth.router)  # Chứa các route: /auth/login, /auth/callback, /auth/logout
app.include_router(users.router) # Chứa các route: /users/me, /users/all

@app.get("/health")
def health_check():
    """API kiểm tra nhanh trạng thái server"""
    return {"status": "healthy", "database": "connected"}

# app/routes/auth.py
print(f"DEBUG: Redirect URI đang dùng là: {settings.GOOGLE_REDIRECT_URI}") # Thêm dòng này