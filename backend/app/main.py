from fastapi import FastAPI

from backend.app.api.v1 import api_router

from backend.app.core.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="校园失物招领智能管理系统",
    description="基于图像识别的失物招领平台",
    version="1.0.0"
)

# 健康检查（防 404 心态爆炸用）
@app.get("/")
def root():
    return {"message": "Lost & Found API is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

# 注册 API 路由
app.include_router(api_router, prefix="/api/v1")
