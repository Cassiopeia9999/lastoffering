"""
物品类别识别服务 —— EfficientNet-B0 分类模型

当前状态：真实模型优先，失败时回退到占位实现
  - 默认使用 ai_module 训练的 EfficientNet-B0 模型进行分类
  - 若模型文件缺失、推理失败或显式开启占位模式，则回退到规则/随机占位逻辑
  - 真实模型依赖 PyTorch 与 torchvision

模型文件：
  - 优先读取 ai_module/models/lost_item_model.pth + model_meta.json
  - 若 latest 文件不存在，则依次回退到 V2、V1
"""

import os
import sys
import json
import random
from pathlib import Path
from typing import Tuple, List

from backend.app.models.item import ITEM_CATEGORIES

# ── 切换开关 ──────────────────────────────────────────────
USING_PLACEHOLDER = False         # False=使用真实模型, True=使用占位实现
# ─────────────────────────────────────────────────────────

# 添加 ai_module 到路径
AI_MODULE_DIR = Path(__file__).parent.parent.parent.parent / "ai_module"
if str(AI_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_MODULE_DIR))

# 全局变量（延迟初始化）
_model = None
_transform = None
_idx_to_class = None
_device = None
_LostItemModel = None  # 延迟导入的模型类


def _import_torch_modules():
    """延迟导入 PyTorch 模块（占位模式不需要调用）"""
    global _LostItemModel
    if _LostItemModel is not None:
        return
    
    import torch
    import torch.nn as nn
    from torchvision import models, transforms
    
    class LostItemModel(nn.Module):
        """与 train.py 一致的模型结构"""
        def __init__(self, num_classes: int, feature_dim: int = 512):
            super().__init__()
            backbone = models.efficientnet_b0(weights=None)
            in_features = backbone.classifier[1].in_features

            self.backbone = backbone.features
            self.pool = backbone.avgpool

            self.feature_head = nn.Sequential(
                nn.Linear(in_features, feature_dim),
                nn.BatchNorm1d(feature_dim),
                nn.ReLU(inplace=True),
                nn.Dropout(0.3),
            )
            self.classifier = nn.Linear(feature_dim, num_classes)

        def forward(self, x):
            x = self.backbone(x)
            x = self.pool(x)
            x = x.flatten(1)
            feat = self.feature_head(x)
            feat_norm = torch.nn.functional.normalize(feat, p=2, dim=1)
            return self.classifier(feat_norm)
    
    _LostItemModel = LostItemModel


def _load_model():
    """加载 EfficientNet-B0 分类模型（单例）"""
    global _model, _transform, _idx_to_class, _device
    
    if _model is not None:
        return _model, _transform, _idx_to_class, _device
    
    # 延迟导入
    _import_torch_modules()
    
    import torch
    from torchvision import transforms
    from PIL import Image
    
    try:
        model_dir = AI_MODULE_DIR / "models"
        
        # 自动选择最新版本：先找 latest，再找 V2/V1
        model_path = model_dir / "lost_item_model.pth"
        meta_path = model_dir / "model_meta.json"
        
        if not model_path.exists() or not meta_path.exists():
            # 尝试 V2
            model_path = model_dir / "lost_item_model_V2.pth"
            meta_path = model_dir / "model_meta_V2.json"
        
        if not model_path.exists() or not meta_path.exists():
            # 尝试 V1
            model_path = model_dir / "lost_item_model_V1.pth"
            meta_path = model_dir / "model_meta_V1.json"
        
        if not model_path.exists() or not meta_path.exists():
            raise FileNotFoundError(f"模型文件不存在，请确保 ai_module/models/ 目录下有模型文件")
        
        # 加载元数据
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        
        num_classes = meta["num_classes"]
        feature_dim = meta["feature_dim"]
        img_size = meta["img_size"]
        _idx_to_class = {int(k): v for k, v in meta["idx_to_class"].items()}
        
        # 加载模型
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _model = _LostItemModel(num_classes, feature_dim).to(_device)
        _model.load_state_dict(torch.load(model_path, map_location=_device))
        _model.eval()
        
        # 预处理
        _transform = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        
        print(f"[AI] EfficientNet-B0 分类模型加载成功，类别数：{num_classes}")
        return _model, _transform, _idx_to_class, _device
    except Exception as e:
        print(f"[AI] 模型加载失败，将使用占位实现: {e}")
        return None, None, None, None


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

    # ── 真实模型推理 ──────────────────────────────────
    model, transform, idx_to_class, device = _load_model()
    if model is None:
        return _placeholder_classify(image_path)
    
    from PIL import Image
    import torch

    try:
        img = Image.open(image_path).convert("RGB")
        tensor = transform(img).unsqueeze(0).to(device)
        
        with torch.no_grad():
            logits = model(tensor)
            probs = torch.softmax(logits, dim=1)
            confidence, idx = probs.max(dim=1)
        
        class_id = idx_to_class.get(idx.item(), "unknown")
        # 映射到系统类别
        category = _map_to_system_category(class_id)
        return category, round(confidence.item(), 4)
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

    model, transform, idx_to_class, device = _load_model()
    if model is None:
        return [classify_image(image_path)]  # fallback
    
    from PIL import Image
    import torch

    try:
        img = Image.open(image_path).convert("RGB")
        tensor = transform(img).unsqueeze(0).to(device)
        
        with torch.no_grad():
            logits = model(tensor)
            probs = torch.softmax(logits, dim=1)
            topk = probs.topk(k=min(k, len(idx_to_class)))
        
        results = []
        for conf, idx in zip(topk.values[0], topk.indices[0]):
            class_id = idx_to_class.get(idx.item(), "unknown")
            category = _map_to_system_category(class_id)
            results.append((category, round(conf.item(), 4)))
        return results
    except Exception as e:
        print(f"[AI] Top-K 分类失败: {e}")
        return [classify_image(image_path)]


def _map_to_system_category(raw_name: str) -> str:
    """
    将模型输出的英文/原始类别名映射到系统定义的中文类别。
    """
    mapping = {
        # 模型类别 -> 系统类别（15类新体系）
        "mobile_device": "移动电子设备",
        "laptop": "笔记本电脑",
        "headphones": "耳机",
        "charger": "充电器/数据线",
        "bag": "包类",
        "book": "书籍",
        "stationery": "文具",
        "card": "证件",
        "keys": "钥匙",
        "glasses": "眼镜",
        "accessory": "饰品",
        "bottle": "水杯",
        "umbrella": "雨伞",
        "clothes": "衣物",
    }
    return mapping.get(raw_name.lower(), "其他")
