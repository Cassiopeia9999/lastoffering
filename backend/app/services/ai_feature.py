"""
图像特征提取服务 —— EfficientNet-B0 特征提取

当前状态：真实模型优先，失败时回退到占位实现
  - 默认使用 ai_module 训练的 EfficientNet-B0 特征头提取 512 维向量
  - 输出特征会做 L2 归一化，用于余弦相似度检索
  - 若模型文件缺失、推理失败或显式开启占位模式，则回退到随机归一化向量
  - 真实模型依赖 PyTorch 与 torchvision

模型文件：
  - 优先读取 ai_module/models/lost_item_model.pth + model_meta.json
  - 若 latest 文件不存在，则依次回退到 V2、V1
"""

import json
import os
import sys
from pathlib import Path
from typing import List, Optional

import numpy as np

# ── 切换开关 ──────────────────────────────────────────────
USING_PLACEHOLDER = False  # False=使用真实模型, True=使用占位实现
FEATURE_DIM = 512          # EfficientNet-B0 输出维度
# ─────────────────────────────────────────────────────────

# 添加 ai_module 到路径
AI_MODULE_DIR = Path(__file__).parent.parent.parent.parent / "ai_module"
if str(AI_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(AI_MODULE_DIR))

# 全局变量（延迟初始化）
_model = None
_transform = None
_device = None
_FeatureExtractor = None  # 延迟导入的模型类


def _import_torch_modules():
    """延迟导入 PyTorch 模块（占位模式不需要调用）"""
    global _FeatureExtractor
    if _FeatureExtractor is not None:
        return
    
    import torch
    import torch.nn as nn
    from torchvision import models
    
    class LostItemFeatureExtractor(nn.Module):
        """特征提取器（与 train.py 一致）"""
        def __init__(self, feature_dim: int = 512):
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

        def forward(self, x):
            x = self.backbone(x)
            x = self.pool(x)
            x = x.flatten(1)
            feat = self.feature_head(x)
            return torch.nn.functional.normalize(feat, p=2, dim=1)
    
    _FeatureExtractor = LostItemFeatureExtractor


def _load_model():
    """加载 EfficientNet-B0 特征提取模型（单例）"""
    global _model, _transform, _device
    
    if _model is not None:
        return _model, _transform, _device
    
    # 延迟导入
    _import_torch_modules()
    
    import torch
    from torchvision import transforms
    
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
        
        feature_dim = meta["feature_dim"]
        img_size = meta["img_size"]
        
        # 加载模型
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 加载完整模型权重
        full_state_dict = torch.load(model_path, map_location=_device)
        
        # 创建特征提取器
        _model = _FeatureExtractor(feature_dim).to(_device)
        
        # 提取特征相关权重
        feature_state = {}
        for k, v in full_state_dict.items():
            if k.startswith('backbone.') or k.startswith('pool.') or k.startswith('feature_head.'):
                feature_state[k] = v
        
        _model.load_state_dict(feature_state, strict=False)
        _model.eval()
        
        # 预处理
        _transform = transforms.Compose([
            transforms.Resize((img_size, img_size)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        
        print(f"[AI] EfficientNet-B0 特征提取模型加载成功，维度：{feature_dim}")
        return _model, _transform, _device
    except Exception as e:
        print(f"[AI] 特征提取模型加载失败，将使用占位实现: {e}")
        return None, None, None


def _placeholder_extract(image_path: str) -> List[float]:
    """
    占位特征提取：返回随机归一化向量。
    同一张图片每次调用结果不同（占位阶段不影响功能验证）。
    真实模型接入后此函数不再被调用。
    """
    vec = np.random.randn(FEATURE_DIM).astype(np.float32)
    vec = vec / (np.linalg.norm(vec) + 1e-8)   # L2 归一化
    return vec.tolist()


def extract_feature(image_path: str) -> Optional[List[float]]:
    """
    提取图片的特征向量。

    Args:
        image_path: 图片文件路径

    Returns:
        长度为 FEATURE_DIM 的 float 列表（已 L2 归一化），失败返回 None
    """
    if not os.path.exists(image_path):
        return None

    if USING_PLACEHOLDER:
        return _placeholder_extract(image_path)

    model, transform, device = _load_model()
    if model is None:
        return _placeholder_extract(image_path)
    
    from PIL import Image
    import torch

    try:
        img = Image.open(image_path).convert("RGB")
        tensor = transform(img).unsqueeze(0).to(device)

        with torch.no_grad():
            feat = model(tensor)               # (1, 512)
            feat = feat.squeeze()              # (512,)

        return feat.cpu().numpy().tolist()
    except Exception as e:
        print(f"[AI] 特征提取失败: {e}")
        return _placeholder_extract(image_path)


def feature_to_str(feature: List[float]) -> str:
    """将特征向量序列化为 JSON 字符串存入数据库"""
    return json.dumps(feature)


def str_to_feature(feature_str: str) -> Optional[np.ndarray]:
    """从数据库读出的 JSON 字符串反序列化为 numpy 数组"""
    try:
        return np.array(json.loads(feature_str), dtype=np.float32)
    except Exception:
        return None
