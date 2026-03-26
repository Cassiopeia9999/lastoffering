"""
相似度检索服务 —— 余弦相似度 Top-K 检索

这部分是纯数学算法，不依赖任何模型，现在就是完整实现。
输入：查询图片的特征向量 + 数据库中所有候选物品的特征向量
输出：按相似度降序排列的 Top-K 结果列表
"""

from typing import List, Tuple, Optional

import numpy as np
from sqlalchemy.orm import Session

from backend.app.crud.item import get_items_with_features
from backend.app.models.item import Item
from backend.app.services.ai_feature import str_to_feature

# 默认相似度阈值：低于此值的结果不返回
DEFAULT_THRESHOLD = 0.5
DEFAULT_TOP_K = 10


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """计算两个向量的余弦相似度（假设已 L2 归一化，直接点积即可）"""
    # 检查维度是否匹配
    if vec_a.shape != vec_b.shape:
        print(f"[WARNING] 特征维度不匹配: {vec_a.shape} vs {vec_b.shape}, 跳过此项")
        return 0.0
    
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a < 1e-8 or norm_b < 1e-8:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def search_similar_items(
    db: Session,
    query_feature: List[float],
    search_type: str,           # 查询失物时传 "found"，查询招领时传 "lost"
    top_k: int = DEFAULT_TOP_K,
    threshold: float = DEFAULT_THRESHOLD,
    exclude_item_id: Optional[int] = None,
) -> List[Tuple[Item, float]]:
    """
    在数据库中检索与查询特征最相似的物品。

    Args:
        db:               数据库 Session
        query_feature:    查询图片的特征向量（List[float]）
        search_type:      检索范围，"found" = 在招领库中找 / "lost" = 在失物库中找
        top_k:            返回前 K 个结果
        threshold:        相似度阈值，低于此值过滤掉
        exclude_item_id:  排除某个物品（如排除查询物品本身）

    Returns:
        [(Item, similarity), ...] 按相似度降序排列
    """
    query_vec = np.array(query_feature, dtype=np.float32)

    # 从数据库取出所有有特征向量的候选物品
    candidates: List[Item] = get_items_with_features(db, type=search_type)

    results: List[Tuple[Item, float]] = []

    for item in candidates:
        if exclude_item_id and item.id == exclude_item_id:
            continue
        if not item.feature_vector:
            continue

        db_vec = str_to_feature(item.feature_vector)
        if db_vec is None:
            continue

        sim = cosine_similarity(query_vec, db_vec)
        if sim >= threshold:
            results.append((item, round(sim, 4)))

    # 按相似度降序排列，取 Top-K
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


def batch_search(
    db: Session,
    query_feature: List[float],
    search_type: str,
    top_k: int = DEFAULT_TOP_K,
    threshold: float = DEFAULT_THRESHOLD,
) -> List[dict]:
    """
    对外暴露的检索接口，返回结构化结果（供 API 路由直接使用）。

    Returns:
        [{"item": Item, "similarity": float}, ...]
    """
    results = search_similar_items(db, query_feature, search_type, top_k, threshold)
    return [{"item": item, "similarity": sim} for item, sim in results]
