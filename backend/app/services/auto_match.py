"""
后台自动匹配服务

拾得者发布招领信息后，在后台异步执行：
  1. 用招领物品的特征向量检索失物库
  2. 对相似度超过阈值的失物发布者推送通知
  3. 同时创建 Match 记录（status=pending）

遗失者发布失物信息后，同样异步检索招领库并通知。
"""

import json
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.core.database import SessionLocal
from backend.app.crud import item as crud_item
from backend.app.crud import match as crud_match
from backend.app.crud import notification as crud_notif
from backend.app.services.ai_feature import str_to_feature
from backend.app.services.ai_search import search_similar_items

AUTO_MATCH_THRESHOLD = 0.6   # 自动通知阈值，占位模式下可调低测试
AUTO_MATCH_TOP_K = 5         # 最多推送几条匹配结果


def run_auto_match(item_id: int, item_type: str) -> None:
    """
    后台异步任务入口，使用独立 DB Session（不依赖请求上下文）。

    Args:
        item_id:   刚发布的物品 ID
        item_type: "found" 或 "lost"
    """
    db: Session = SessionLocal()
    try:
        _do_match(db, item_id, item_type)
    except Exception as e:
        print(f"[AutoMatch] 自动匹配任务异常 item_id={item_id}: {e}")
    finally:
        db.close()


def _do_match(db: Session, item_id: int, item_type: str) -> None:
    new_item = crud_item.get_item_by_id(db, item_id)
    if not new_item or not new_item.feature_vector:
        print(f"[AutoMatch] item_id={item_id} 无特征向量，跳过匹配")
        return

    query_vec = str_to_feature(new_item.feature_vector)
    if query_vec is None:
        return

    # 检索方向：招领物品 → 搜失物库；失物 → 搜招领库
    search_type = "lost" if item_type == "found" else "found"

    results = search_similar_items(
        db=db,
        query_feature=query_vec.tolist(),
        search_type=search_type,
        top_k=AUTO_MATCH_TOP_K,
        threshold=AUTO_MATCH_THRESHOLD,
        exclude_item_id=item_id,
    )

    if not results:
        print(f"[AutoMatch] item_id={item_id} 未找到相似度≥{AUTO_MATCH_THRESHOLD}的物品")
        return

    print(f"[AutoMatch] item_id={item_id} 找到 {len(results)} 条相似物品，开始推送通知")

    for matched_item, similarity in results:
        # 创建 Match 记录
        if item_type == "found":
            lost_id, found_id = matched_item.id, item_id
        else:
            lost_id, found_id = item_id, matched_item.id

        crud_match.create_match(db, lost_id, found_id, similarity=float(similarity))

        # 给匹配到的物品发布者推送通知
        if item_type == "found":
            # 拾得者发布招领 → 通知失物发布者
            crud_notif.create_notification(
                db,
                user_id=matched_item.owner_id,
                type="match_found",
                content=(
                    f"系统发现一条疑似你遗失物品的招领信息！\n"
                    f"招领物品：【{new_item.title}】\n"
                    f"相似度：{similarity:.0%}，请前往查看是否为你的失物。"
                ),
                related_item_id=new_item.id,
            )
        else:
            # 遗失者发布失物 → 通知招领发布者
            crud_notif.create_notification(
                db,
                user_id=matched_item.owner_id,
                type="match_found",
                content=(
                    f"系统发现一条疑似你招领物品的失物信息！\n"
                    f"失物：【{new_item.title}】\n"
                    f"相似度：{similarity:.0%}，请前往查看是否为同一物品。"
                ),
                related_item_id=new_item.id,
            )

        print(f"[AutoMatch]   → 已通知 user_id={matched_item.owner_id}，相似度={similarity:.4f}")
