from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from backend.app.core.deps import get_db, get_current_user
from backend.app.models.user import User
from backend.app.schemas.item import ItemOut
from backend.app.services.ai_classifier import classify_image, classify_image_topk
from backend.app.services.ai_feature import extract_feature, feature_to_str
from backend.app.services.ai_search import batch_search
from backend.app.utils.file_utils import save_upload_image
from backend.app.crud import item as crud_item

router = APIRouter(prefix="/search", tags=["以图搜物"])


class SearchResultItem(BaseModel):
    item: ItemOut
    similarity: float

    model_config = ConfigDict(from_attributes=True)


class SearchResponse(BaseModel):
    query_category: Optional[str] = None
    query_category_confidence: Optional[float] = None
    top_categories: Optional[List[dict]] = None
    total: int
    results: List[SearchResultItem]


@router.post("/by-image", response_model=SearchResponse, summary="以图搜物（上传图片→返回相似物品列表）")
async def search_by_image(
    image: UploadFile = File(..., description="用于搜索的图片"),
    search_type: str = Form("found", description="found=在招领库中找 / lost=在失物库中找"),
    top_k: int = Form(10, ge=1, le=20, description="返回结果数量"),
    threshold: float = Form(0.3, ge=0.0, le=1.0, description="相似度阈值（占位模式建议用0.0）"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    以图搜物核心接口。

    流程：
    1. 保存上传图片
    2. YOLOv8 识别物品类别
    3. ResNet 提取特征向量
    4. 余弦相似度检索数据库，返回 Top-K 相似物品
    """
    if search_type not in ("lost", "found"):
        raise HTTPException(status_code=400, detail="search_type 只能是 lost 或 found")
    if not image.filename:
        raise HTTPException(status_code=400, detail="请上传图片文件")

    # 1. 保存图片
    image_url = save_upload_image(image)

    # 2. AI 识别类别（Top-3 供前端展示候选）
    top_cats = classify_image_topk(image_url, k=3)
    query_category, query_confidence = top_cats[0] if top_cats else ("其他", 0.0)
    top_categories = [{"category": c, "confidence": conf} for c, conf in top_cats]

    # 3. 提取特征向量
    feature_vec = extract_feature(image_url)
    if feature_vec is None:
        raise HTTPException(status_code=500, detail="特征提取失败，请重试")

    # 4. 余弦相似度检索
    raw_results = batch_search(
        db=db,
        query_feature=feature_vec,
        search_type=search_type,
        top_k=top_k,
        threshold=threshold,
    )

    results = [
        SearchResultItem(item=r["item"], similarity=r["similarity"])
        for r in raw_results
    ]

    return SearchResponse(
        query_category=query_category,
        query_category_confidence=query_confidence,
        top_categories=top_categories,
        total=len(results),
        results=results,
    )


@router.post("/classify", summary="仅识别图片类别（不做相似度检索）")
async def classify_only(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    单独调用 AI 分类，返回 Top-3 类别建议。
    用于发布物品时的自动类别填充（前端可让用户确认或修改）。
    """
    if not image.filename:
        raise HTTPException(status_code=400, detail="请上传图片文件")

    image_url = save_upload_image(image)
    top_cats = classify_image_topk(image_url, k=3)

    return {
        "suggested_category": top_cats[0][0] if top_cats else "其他",
        "confidence": top_cats[0][1] if top_cats else 0.0,
        "top3": [{"category": c, "confidence": conf} for c, conf in top_cats],
    }
