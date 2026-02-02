from sqlmodel import create_engine, Session, SQLModel
from app.core.config import settings # Sử dụng Dataclass Config

# Echo=True giúp bạn theo dõi các câu lệnh SQL trong terminal (tốt khi dev)
engine = create_engine(
    settings.DATABASE_URL, 
    echo=True,
    # Cấu hình pool giúp tối ưu hóa kết nối khi có nhiều request cùng lúc
    pool_pre_ping=True 
)

def init_db():
    """Khởi tạo toàn bộ bảng trong database từ các SQLModel"""
    SQLModel.metadata.create_all(engine)

def dispose_engine():
    """Đóng toàn bộ kết nối tới database khi server tắt"""
    engine.dispose()

def get_session():
    """Dependency injection để lấy session cho mỗi request"""
    with Session(engine) as session:
        yield session