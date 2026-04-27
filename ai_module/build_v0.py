"""
构建 V0 基线模型：ImageNet 预训练 EfficientNet-B0 + 类别原型

V0 不做你当前 14 类任务上的完整微调，而是直接使用预训练特征提取器，
对训练集每个类别计算一个原型向量。预测时以特征余弦相似度作为分类依据。

运行方式：
  conda activate efftrain
  python ai_module/build_v0.py
"""

import json
import os
from collections import defaultdict

import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    train_dir = os.path.join(base_dir, "datasets", "classification", "train")
    model_dir = os.path.join(base_dir, "models")
    os.makedirs(model_dir, exist_ok=True)

    if not os.path.exists(train_dir):
        raise FileNotFoundError(f"训练集目录不存在: {train_dir}")

    img_size = 224
    batch_size = 32
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    transform = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    dataset = datasets.ImageFolder(train_dir, transform=transform)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=0)

    backbone = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT).to(device)
    backbone.eval()

    feature_buckets = defaultdict(list)
    sample_counts = defaultdict(int)

    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            features = backbone.features(images)
            features = backbone.avgpool(features)
            features = features.flatten(1)
            features = F.normalize(features, p=2, dim=1).cpu().numpy()

            for feature, label in zip(features, labels.numpy()):
                label = int(label)
                feature_buckets[label].append(feature)
                sample_counts[label] += 1

    idx_to_class = {v: k for k, v in dataset.class_to_idx.items()}
    prototypes = []
    samples_per_class = {}

    for idx in range(len(idx_to_class)):
        class_features = np.stack(feature_buckets[idx], axis=0)
        prototype = class_features.mean(axis=0)
        prototype = prototype / max(np.linalg.norm(prototype), 1e-12)
        prototypes.append(prototype.astype(np.float32))
        samples_per_class[idx_to_class[idx]] = sample_counts[idx]

    prototypes = np.stack(prototypes, axis=0)

    prototype_file = "class_prototypes_V0.npz"
    np.savez(os.path.join(model_dir, prototype_file), prototypes=prototypes)

    torch.save(
        {"model_type": "prototype", "source": "imagenet_pretrained_backbone"},
        os.path.join(model_dir, "lost_item_model_V0.pth"),
    )

    meta = {
        "version": "V0",
        "model_type": "prototype",
        "source": "ImageNet pretrained EfficientNet-B0 feature extractor",
        "prototype_file": prototype_file,
        "num_classes": len(dataset.classes),
        "feature_dim": int(prototypes.shape[1]),
        "img_size": img_size,
        "class_to_idx": dataset.class_to_idx,
        "idx_to_class": {str(k): v for k, v in idx_to_class.items()},
        "samples_per_class": samples_per_class,
        "temperature": 12.0,
    }

    with open(os.path.join(model_dir, "model_meta_V0.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print("V0 构建完成")
    print(f"device={device} classes={len(dataset.classes)} feature_dim={prototypes.shape[1]}")
    for class_name, count in samples_per_class.items():
        print(f"{class_name}: {count}")


if __name__ == "__main__":
    main()
