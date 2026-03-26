from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Form
from typing import Optional
import os
import tempfile
import numpy as np
from backend.app.services.ark_ai import generate_item_description

router = APIRouter()

# 延迟初始化AI模型（避免导入时失败影响整个路由）
lost_item_ai = None
def get_ai_model():
    global lost_item_ai
    if lost_item_ai is None:
        from ai_module.predict import LostItemAI
        lost_item_ai = LostItemAI()
    return lost_item_ai

@router.post("/predict")
async def predict_item(file: UploadFile = File(...)):
    """预测上传的失物图像类别"""
    ai = get_ai_model()
    if ai.model is None:
        raise HTTPException(status_code=500, detail="分类模型未加载，请先训练模型")
    
    # 保存上传的文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        # 预测
        class_name, score = ai.predict(temp_file_path)
        if class_name:
            return {
                "prediction": class_name,
                "confidence": float(score),
            }
        else:
            raise HTTPException(status_code=500, detail="预测失败")
    finally:
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)


@router.post("/generate-description", summary="AI帮写：根据图片生成物品描述")
async def ai_generate_description(
    image: Optional[UploadFile] = File(None),
    item_type: str = Form("lost", description="lost=失物 / found=招领"),
    category: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
):
    """
    使用火山方舟 AI 根据图片和物品信息生成描述文本
    """
    temp_file_path = None
    
    try:
        # 如果有图片，保存临时文件
        if image and image.filename:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
                content = await image.read()
                temp_file.write(content)
                temp_file_path = temp_file.name
        
        # 调用火山方舟 AI 生成描述
        description = generate_item_description(
            image_path=temp_file_path,
            item_type=item_type,
            category=category,
            title=title
        )
        
        if description:
            return {
                "success": True,
                "description": description,
                "message": "生成成功"
            }
        else:
            return {
                "success": False,
                "description": "",
                "message": "生成失败，请稍后重试"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI生成失败: {str(e)}")
    finally:
        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@router.post("/search")
async def search_similar_items(file: UploadFile = File(...), top_k: int = Query(5, ge=1, le=20)):
    """以图搜图，查找相似物品"""
    ai = get_ai_model()
    if ai.model is None:
        raise HTTPException(status_code=500, detail="特征提取模型未加载，请先训练模型")
    
    # 保存上传的文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        # 提取查询图像的特征
        query_features = ai.extract_features(temp_file_path)
        if query_features is None:
            raise HTTPException(status_code=500, detail="特征提取失败")
        
        # 这里应该从数据库中加载所有物品的特征向量进行比较
        # 由于是示例，我们返回模拟的结果
        # 实际项目中，需要在物品上传时提取特征并存储到数据库
        similar_items = [
            {"id": 1, "name": "黑色iPhone", "similarity": 0.95},
            {"id": 2, "name": "蓝色iPhone", "similarity": 0.87},
            {"id": 3, "name": "黑色Android手机", "similarity": 0.78},
            {"id": 4, "name": "银色iPhone", "similarity": 0.72},
            {"id": 5, "name": "黑色手机壳", "similarity": 0.65}
        ]
        
        # 按相似度排序并返回前top_k个结果
        similar_items.sort(key=lambda x: x["similarity"], reverse=True)
        return {
            "query_item": "上传的物品",
            "similar_items": similar_items[:top_k]
        }
    finally:
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)