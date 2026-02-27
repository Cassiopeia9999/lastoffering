"""
物品类别识别服务 —— YOLOv8 分类模型

当前状态：占位实现
  - 接口与最终版本完全一致，后期只需替换 _load_model() 和 _predict() 内部实现
  - 占位逻辑：对图片文件名/路径做简单规则匹配，模拟返回类别

最终实现：
  - 使用 ultralytics YOLOv8-cls 模型
  - 模型权重放在 models/weights/classifier.pt
  - 替换步骤：
      1. pip install ultralytics
      2. 将训练好的 .pt 文件放到 models/weights/classifier.pt
      3. 将下方 USING_PLACEHOLDER 改为 False 即可自动切换
"""

import os
import random
from pathlib import Path
from typing import Tuple, List

from backend.app.models.item import ITEM_CATEGORIES

# ── 切换开关 ──────────────────────────────────────────────
USING_PLACEHOLDER = True          # 改为 False 后使用真实 YOLOv8 模型
MODEL_PATH = "models/weights/classifier.pt"
# ─────────────────────────────────────────────────────────

_model = None  # 全局单例，避免重复加载


def _load_model():
    """加载 YOLOv8 分类模型（单例）"""
    global _model
    if _model is not None:
        return _model
    try:
        from ultralytics import YOLO
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"模型文件不存在: {MODEL_PATH}")
        _model = YOLO(MODEL_PATH)
        print(f"[AI] YOLOv8 分类模型加载成功: {MODEL_PATH}")
        return _model
    except Exception as e:
        print(f"[AI] YOLOv8 模型加载失败，将使用占位实现: {e}")
        return None


def _placeholder_classify(image_path: str) -> Tuple[str, float]:
    """
    占位分类逻辑：根据文件名关键词做简单映射，模拟 AI 输出。
    真实模型接入后此函数不再被调用。
    """
    name = Path(image_path).stem.lower()
    keyword_map = {
        "phone": "电子产品", "mobile": "电子产品", "laptop": "电子产品",
        "earphone": "电子产品", "charger": "电子产品",
        "card": "证件", "id": "证件", "student": "证件",
        "key": "钥匙", "keys": "钥匙",
        "wallet": "钱包/包", "bag": "钱包/包", "purse": "钱包/包",
        "book": "书籍/文具", "pen": "书籍/文具", "notebook": "书籍/文具",
        "cloth": "衣物", "shirt": "衣物", "jacket": "衣物",
        "glass": "眼镜", "glasses": "眼镜",
        "umbrella": "雨伞",
        "cup": "水杯/水壶", "bottle": "水杯/水壶",
        "sport": "运动用品", "ball": "运动用品",
        "jewelry": "首饰/饰品", "ring": "首饰/饰品", "necklace": "首饰/饰品",
    }
    for kw, category in keyword_map.items():
        if kw in name:
            confidence = round(random.uniform(0.75, 0.95), 4)
            return category, confidence

    # 无匹配时随机返回一个类别（模拟低置信度）
    category = random.choice(ITEM_CATEGORIES)
    confidence = round(random.uniform(0.40, 0.65), 4)
    return category, confidence


def classify_image(image_path: str) -> Tuple[str, float]:
    """
    对图片进行物品类别识别。

    Args:
        image_path: 图片文件路径

    Returns:
        (category, confidence) —— 类别名称 + 置信度 (0~1)
    """
    if not os.path.exists(image_path):
        return "其他", 0.0

    if USING_PLACEHOLDER:
        return _placeholder_classify(image_path)

    # ── 真实 YOLOv8 推理 ──────────────────────────────────
    model = _load_model()
    if model is None:
        return _placeholder_classify(image_path)

    try:
        results = model(image_path, verbose=False)
        top1_idx = results[0].probs.top1
        top1_conf = float(results[0].probs.top1conf)
        # 将模型输出的类别名映射到系统类别（需根据训练数据集调整）
        model_names = results[0].names
        raw_name = model_names[top1_idx]
        category = _map_to_system_category(raw_name)
        return category, round(top1_conf, 4)
    except Exception as e:
        print(f"[AI] 分类推理失败: {e}")
        return _placeholder_classify(image_path)


def classify_image_topk(image_path: str, k: int = 3) -> List[Tuple[str, float]]:
    """
    返回 Top-K 类别预测结果，用于前端展示候选类别供用户选择。

    Returns:
        [(category, confidence), ...] 按置信度降序排列
    """
    if not os.path.exists(image_path):
        return [("其他", 0.0)]

    if USING_PLACEHOLDER:
        # 占位：返回 k 个随机类别（不重复）
        categories = random.sample(ITEM_CATEGORIES, min(k, len(ITEM_CATEGORIES)))
        confidences = sorted(
            [round(random.uniform(0.3, 0.95), 4) for _ in range(k)],
            reverse=True
        )
        return list(zip(categories, confidences))

    model = _load_model()
    if model is None:
        return classify_image_topk.__wrapped__(image_path, k)  # fallback

    try:
        results = model(image_path, verbose=False)
        top_indices = results[0].probs.top5[:k]
        top_confs = results[0].probs.data[top_indices].tolist()
        model_names = results[0].names
        return [
            (_map_to_system_category(model_names[idx]), round(conf, 4))
            for idx, conf in zip(top_indices, top_confs)
        ]
    except Exception as e:
        print(f"[AI] Top-K 分类失败: {e}")
        return [classify_image(image_path)]


def _map_to_system_category(raw_name: str) -> str:
    """
    将模型输出的英文/原始类别名映射到系统定义的中文类别。
    训练自己的模型后，根据数据集的类别标签调整此映射表。
    """
    mapping = {
        # 示例映射，根据实际训练数据集的类别名填写
        "cell_phone": "电子产品",
        "laptop": "电子产品",
        "earphones": "电子产品",
        "id_card": "证件",
        "student_card": "证件",
        "key": "钥匙",
        "wallet": "钱包/包",
        "handbag": "钱包/包",
        "backpack": "钱包/包",
        "book": "书籍/文具",
        "pen": "书籍/文具",
        "clothing": "衣物",
        "glasses": "眼镜",
        "umbrella": "雨伞",
        "bottle": "水杯/水壶",
        "sports_equipment": "运动用品",
        "jewelry": "首饰/饰品",
    }
    return mapping.get(raw_name.lower(), "其他")
