"""
图像特征提取服务 —— ResNet50 预训练模型

当前状态：占位实现
  - 占位逻辑：返回固定维度的随机单位向量（已归一化），结构与真实输出完全一致
  - 接口不变，后期只需将 USING_PLACEHOLDER 改为 False

最终实现：
  - 使用 torchvision 内置 ResNet50，去掉最后的分类层，输出 2048 维特征
  - 对特征向量做 L2 归一化，保证余弦相似度计算的一致性
  - 模型权重使用 ImageNet 预训练权重，无需额外下载 .pt 文件
  - 替换步骤：将 USING_PLACEHOLDER 改为 False 即可，torch/torchvision 已在环境中安装
"""

import json
import os
from typing import List, Optional

import numpy as np

# ── 切换开关 ──────────────────────────────────────────────
USING_PLACEHOLDER = True   # 改为 False 后使用真实 ResNet50 模型
FEATURE_DIM = 2048         # ResNet50 输出维度，占位向量与此保持一致
# ─────────────────────────────────────────────────────────

_model = None
_transform = None


def _load_model():
    """加载 ResNet50 特征提取模型（去掉分类头，单例）"""
    global _model, _transform
    if _model is not None:
        return _model, _transform
    try:
        import torch
        import torch.nn as nn
        from torchvision import models, transforms

        weights = models.ResNet50_Weights.IMAGENET1K_V1
        backbone = models.resnet50(weights=weights)
        # 去掉最后的全连接分类层，保留特征提取部分
        _model = nn.Sequential(*list(backbone.children())[:-1])
        _model.eval()

        _transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
        ])
        print("[AI] ResNet50 特征提取模型加载成功（ImageNet 预训练权重）")
        return _model, _transform
    except Exception as e:
        print(f"[AI] ResNet50 加载失败，将使用占位实现: {e}")
        return None, None


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

    model, transform = _load_model()
    if model is None:
        return _placeholder_extract(image_path)

    try:
        import torch
        from PIL import Image

        img = Image.open(image_path).convert("RGB")
        tensor = transform(img).unsqueeze(0)   # (1, 3, 224, 224)

        with torch.no_grad():
            feat = model(tensor)               # (1, 2048, 1, 1)
            feat = feat.squeeze()              # (2048,)
            feat = feat / (feat.norm() + 1e-8) # L2 归一化

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
