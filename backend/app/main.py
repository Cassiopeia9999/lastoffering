import os
import threading

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import backend.app.models  # noqa: F401
from backend.app.api.v1 import api_router
from backend.app.core.config import settings
from backend.app.core.database import Base, engine
from backend.app.core.schema_sync import sync_item_columns, sync_user_columns

Base.metadata.create_all(bind=engine)
sync_item_columns(engine)
sync_user_columns(engine)

app = FastAPI(
    title="校园失物招领智能管理系统",
    description="基于图像识别与智能匹配的校园失物招领平台",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(api_router, prefix="/api/v1")


@app.on_event("startup")
async def warmup_ai_models():
    def _load():
        try:
            from backend.app.services.ai_classifier import _load_model as load_cls
            from backend.app.services.ai_feature import _load_model as load_feat

            print("[startup] warming classifier model...")
            load_cls()
            print("[startup] warming feature model...")
            load_feat()
            print("[startup] AI models are ready")
        except Exception as exc:
            print(f"[startup] AI warmup skipped: {exc}")

    threading.Thread(target=_load, daemon=True).start()


@app.get("/", tags=["system"])
def root():
    return {"message": "Lost & Found API is running"}


@app.get("/health", tags=["system"])
def health_check():
    return {"status": "ok"}
