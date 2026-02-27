import os
import uuid
from pathlib import Path

from fastapi import UploadFile, HTTPException

from backend.app.core.config import settings

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def save_upload_image(file: UploadFile) -> str:
    """
    保存上传的图片到 UPLOAD_DIR，返回相对路径（用于存库和拼接访问URL）。
    返回格式：media/images/xxxx.jpg
    """
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的图片格式，请上传 {ALLOWED_EXTENSIONS}")

    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过 10MB")

    filename = f"{uuid.uuid4().hex}{suffix}"
    save_dir = Path(settings.UPLOAD_DIR)
    save_dir.mkdir(parents=True, exist_ok=True)

    save_path = save_dir / filename
    with open(save_path, "wb") as f:
        f.write(content)

    # 返回可通过 /media/images/xxx.jpg 访问的相对路径
    return str(save_path).replace("\\", "/")


def delete_image(image_url: str) -> None:
    """删除本地图片文件（下架时可选调用）"""
    if image_url and os.path.exists(image_url):
        os.remove(image_url)
