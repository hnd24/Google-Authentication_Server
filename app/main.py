from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db, dispose_engine
from app.routes import auth

# Quản lý vòng đời ứng dụng (Lifespan)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP: Chạy khi khởi động server ---
    print("🚀 Khởi động hệ thống...")
    init_db() # Tự động tạo bảng User nếu chưa có
    print("🍀 Database đã sẵn sàng.")
    yield
    # --- SHUTDOWN: Chạy khi tắt server ---
    print("🛑 Đang tắt hệ thống...")
    dispose_engine() # Giải phóng tài nguyên
    print("🍀 Kết nối Database đã đóng sạch sẽ.")

app = FastAPI(
    title="Google OAuth2 Server", 
    version="1.0.0",
    lifespan=lifespan # Gắn lifespan vào app
)

# Cấu hình Middleware (Theo thứ tự ưu tiên)

# 1. SessionMiddleware: Bắt buộc cho Authlib để lưu state tạm thời
app.add_middleware(
    SessionMiddleware, 
    secret_key=settings.SECRET_KEY,
    session_cookie="auth_session", # Tên cookie cho session
    max_age= 300 # Hạn 1 giờ khớp với Google Access Token
)

# 2. CORSMiddleware: Cho phép React kết nối an toàn
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], # URL của frontend
    allow_credentials=True, # Quan trọng để gửi nhận Cookie http-only
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các Router
app.include_router(auth.router)

@app.get("/health")
def health_check():
    """API kiểm tra nhanh trạng thái server"""
    return {"status": "healthy", "database": "connected"}