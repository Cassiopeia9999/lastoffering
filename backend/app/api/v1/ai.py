from fastapi import APIRouter, UploadFile, File, HTTPException, Query
import os
import tempfile
import numpy as np
from ai_module.predict import LostItemAI, DescriptionGenerator

router = APIRouter()

# 初始化AI模型
lost_item_ai = LostItemAI()
description_generator = DescriptionGenerator()

@router.post("/predict")
async def predict_item(file: UploadFile = File(...)):
    """预测上传的失物图像类别"""
    if lost_item_ai.classification_model is None:
        raise HTTPException(status_code=500, detail="分类模型未加载，请先训练模型")
    
    # 保存上传的文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        # 预测
        class_name, score = lost_item_ai.predict(temp_file_path)
        if class_name:
            # 生成描述
            description = description_generator.generate_description(temp_file_path, class_name)
            return {
                "prediction": class_name,
                "confidence": float(score),
                "description": description
            }
        else:
            raise HTTPException(status_code=500, detail="预测失败")
    finally:
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@router.post("/search")
async def search_similar_items(file: UploadFile = File(...), top_k: int = Query(5, ge=1, le=20)):
    """以图搜图，查找相似物品"""
    if lost_item_ai.feature_extractor is None:
        raise HTTPException(status_code=500, detail="特征提取模型未加载，请先训练模型")
    
    # 保存上传的文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        # 提取查询图像的特征
        query_features = lost_item_ai.extract_features(temp_file_path)
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