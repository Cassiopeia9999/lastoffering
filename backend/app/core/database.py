from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite 数据库地址
SQLALCHEMY_DATABASE_URL = "sqlite:///./lostfound.db"

# SQLite 特殊配置
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Session 工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ORM 基类
Base = declarative_base()


# FastAPI 依赖用的 DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
