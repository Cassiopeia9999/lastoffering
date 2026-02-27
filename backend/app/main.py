import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api.v1 import api_router
from backend.app.core.config import settings
from backend.app.core.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="校园失物招领智能管理系统",
    description="基于图像识别的失物招领平台",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确保媒体目录存在，并挂载为静态文件服务
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["系统"])
def root():
    return {"message": "Lost & Found API is running"}


@app.get("/health", tags=["系统"])
def health_check():
    return {"status": "ok"}
