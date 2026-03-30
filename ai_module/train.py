"""
校园失物招领系统 - 模型训练脚本
框架：PyTorch + EfficientNet-B0（预训练迁移学习）
功能：14类物品分类 + 特征提取器（用于以图搜图）
运行环境：conda efftrain

运行方式：
  conda activate efftrain
  python ai_module/train.py
"""

import os
import json
import time
import glob
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from torch.optim.lr_scheduler import CosineAnnealingLR
from tqdm import tqdm


def get_next_version(model_dir):
    """获取下一个模型版本号 (V1, V2, V3...)"""
    existing_models = glob.glob(os.path.join(model_dir, "lost_item_model_V*.pth"))
    if not existing_models:
        return "V1"
    
    versions = []
    for model_path in existing_models:
        filename = os.path.basename(model_path)
        # 提取版本号，如 lost_item_model_V3.pth -> 3
        try:
            version = int(filename.replace("lost_item_model_V", "").replace(".pth", ""))
            versions.append(version)
        except ValueError:
            continue
    
    next_version = max(versions, default=0) + 1
    return f"V{next_version}"


# ==================== 模型定义 ====================

class LostItemModel(nn.Module):
    """
    基于 EfficientNet-B0 的失物分类模型。
    输出两个分支：
      - classifier：14类 softmax 分类头
      - feature_extractor：L2 归一化的 512 维特征向量（用于以图搜图）
    """
    def __init__(self, num_classes: int, feature_dim: int = 512):
        super().__init__()
        backbone = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
        in_features = backbone.classifier[1].in_features  # 1280

        # 去掉原分类头，保留特征提取部分
        self.backbone = backbone.features
        self.pool = backbone.avgpool  # AdaptiveAvgPool2d

        # 特征投影层（降维 + 归一化，供余弦相似度检索）
        self.feature_head = nn.Sequential(
            nn.Linear(in_features, feature_dim),
            nn.BatchNorm1d(feature_dim),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
        )

        # 分类头
        self.classifier = nn.Linear(feature_dim, num_classes)

    def forward_features(self, x):
        x = self.backbone(x)
        x = self.pool(x)
        x = x.flatten(1)
        feat = self.feature_head(x)
        # L2 归一化（用于余弦相似度）
        feat_norm = nn.functional.normalize(feat, p=2, dim=1)
        return feat_norm

    def forward(self, x):
        feat = self.forward_features(x)
        logits = self.classifier(feat)
        return logits


# ==================== 训练函数 ====================

def train_one_epoch(model, loader, criterion, optimizer, device, epoch, total_epochs):
    model.train()
    total_loss, correct, total = 0.0, 0, 0
    
    # 使用 tqdm 显示进度条
    pbar = tqdm(loader, desc=f"Epoch [{epoch:02d}/{total_epochs}] Train", 
                ncols=100, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]')
    
    for imgs, labels in pbar:
        # 跳过只有 1 个样本的 batch（BatchNorm 需要至少 2 个）
        if imgs.size(0) <= 1:
            continue
            
        imgs, labels = imgs.to(device), labels.to(device)
        optimizer.zero_grad()
        logits = model(imgs)
        loss = criterion(logits, labels)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item() * imgs.size(0)
        correct += (logits.argmax(1) == labels).sum().item()
        total += imgs.size(0)
        
        # 更新进度条显示
        current_loss = total_loss / total
        current_acc = correct / total
        pbar.set_postfix({'Loss': f'{current_loss:.4f}', 'Acc': f'{current_acc:.4f}'})
    
    return total_loss / total, correct / total


def evaluate(model, loader, criterion, device, epoch, total_epochs):
    model.eval()
    total_loss, correct, total = 0.0, 0, 0
    
    # 使用 tqdm 显示进度条
    pbar = tqdm(loader, desc=f"Epoch [{epoch:02d}/{total_epochs}] Val  ", 
                ncols=100, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]')
    
    with torch.no_grad():
        for imgs, labels in pbar:
            imgs, labels = imgs.to(device), labels.to(device)
            logits = model(imgs)
            loss = criterion(logits, labels)
            total_loss += loss.item() * imgs.size(0)
            correct += (logits.argmax(1) == labels).sum().item()
            total += imgs.size(0)
            
            # 更新进度条显示
            current_loss = total_loss / total
            current_acc = correct / total
            pbar.set_postfix({'Loss': f'{current_loss:.4f}', 'Acc': f'{current_acc:.4f}'})
    
    return total_loss / total, correct / total


# ==================== 主函数 ====================

def main():
    # 路径配置
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "datasets", "classification")
    train_dir = os.path.join(data_dir, "train")
    val_dir = os.path.join(data_dir, "val")
    model_dir = os.path.join(base_dir, "models")
    os.makedirs(model_dir, exist_ok=True)

    # 超参数
    img_size = 224
    batch_size = 32
    epochs = 30
    lr = 1e-3
    feature_dim = 512
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # 数据增强
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop(img_size),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
        transforms.RandomRotation(15),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    val_transform = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    # 加载数据集
    if not os.path.exists(train_dir):
        raise FileNotFoundError(f"训练目录不存在: {train_dir}\n请先运行数据集下载脚本！")
    if not os.path.exists(val_dir):
        raise FileNotFoundError(f"验证目录不存在: {val_dir}\n请先运行数据集下载脚本！")

    train_dataset = datasets.ImageFolder(train_dir, transform=train_transform)
    val_dataset = datasets.ImageFolder(val_dir, transform=val_transform)

    # Windows 下 num_workers=0，避免多进程问题
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True,
                              num_workers=0, pin_memory=False)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False,
                            num_workers=0, pin_memory=False)

    num_classes = len(train_dataset.classes)
    class_to_idx = train_dataset.class_to_idx
    idx_to_class = {v: k for k, v in class_to_idx.items()}

    print(f"设备      : {device}")
    print(f"类别数    : {num_classes}")
    print(f"训练样本  : {len(train_dataset)}")
    print(f"验证样本  : {len(val_dataset)}")
    print(f"类别列表  : {train_dataset.classes}")

    # 创建模型
    model = LostItemModel(num_classes, feature_dim).to(device)

    # 损失 / 优化器
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    # 获取版本号
    version = get_next_version(model_dir)
    model_filename = f"lost_item_model_{version}.pth"
    meta_filename = f"model_meta_{version}.json"
    model_path = os.path.join(model_dir, model_filename)
    meta_path = os.path.join(model_dir, meta_filename)
    
    print(f"\n本次训练版本: {version}")
    print(f"模型将保存为: {model_filename}")
    
    # 训练循环
    best_val_acc = 0.0
    print("\n" + "=" * 60)
    print("开始训练...")
    print("=" * 60)

    print(f"\n总 batch 数: 训练 {len(train_loader)} | 验证 {len(val_loader)}")
    print("=" * 60)
    
    start_time = time.time()  # 记录开始时间
    
    for epoch in range(1, epochs + 1):
        # 训练
        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device, epoch, epochs)
        
        # 验证
        val_loss, val_acc = evaluate(model, val_loader, criterion, device, epoch, epochs)
        
        scheduler.step()

        # 显示本轮结果
        print(f"  📊 Epoch [{epoch:02d}/{epochs}] 结果:")
        print(f"      Train - Loss: {train_loss:.4f} | Acc: {train_acc:.4f}")
        print(f"      Val   - Loss: {val_loss:.4f} | Acc: {val_acc:.4f}")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), model_path)
            print(f"      ✅ 保存最佳模型（val_acc={val_acc:.4f}）")
        print("-" * 60)

    # 保存类别信息
    meta = {
        "version": version,
        "num_classes": num_classes,
        "feature_dim": feature_dim,
        "img_size": img_size,
        "class_to_idx": class_to_idx,
        "idx_to_class": idx_to_class,
        "best_val_acc": best_val_acc,
        "epochs": epochs,
        "training_time": time.time() - start_time,
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    total_time = time.time() - start_time
    hours = int(total_time // 3600)
    minutes = int((total_time % 3600) // 60)
    seconds = int(total_time % 60)
    
    print(f"\n训练完成！最佳验证准确率：{best_val_acc:.4f}")
    print(f"总训练时间：{hours:02d}:{minutes:02d}:{seconds:02d} ({total_time:.1f}秒)")
    print(f"平均每轮：{total_time/epochs:.1f}秒")
    print(f"模型文件：{model_path}")
    print(f"元数据  ：{meta_path}")
    
    # 同时更新 latest 版本（不带版本号，供推理时默认加载）
    latest_model_path = os.path.join(model_dir, "lost_item_model.pth")
    latest_meta_path = os.path.join(model_dir, "model_meta.json")  # 固定名称，始终指向最新
    torch.save(model.state_dict(), latest_model_path)
    with open(latest_meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 同时更新 latest 版本: {latest_model_path}")


if __name__ == "__main__":
    main()
