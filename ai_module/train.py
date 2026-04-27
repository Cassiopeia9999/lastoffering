"""
校园失物招领系统 - 图像分类模型训练脚本

功能：
1. 基于 EfficientNet-B0 进行 14 类失物分类微调
2. 同时保留 512 维特征投影层，供以图搜图等模块使用
3. 输出版本化模型、训练历史、PNG 曲线图、TensorBoard runs 日志

运行方式：
  conda activate lostfound
  python ai_module/train.py
"""

import csv
import glob
import json
import os
import shutil
import time
from datetime import datetime

import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms
from tqdm import tqdm

try:
    from torch.utils.tensorboard import SummaryWriter
except Exception:
    SummaryWriter = None

try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None


def get_next_version(model_dir: str) -> str:
    existing_models = glob.glob(os.path.join(model_dir, "lost_item_model_V*.pth"))
    if not existing_models:
        return "V1"

    versions = []
    for model_path in existing_models:
        filename = os.path.basename(model_path)
        try:
            version = int(filename.replace("lost_item_model_V", "").replace(".pth", ""))
            versions.append(version)
        except ValueError:
            continue

    return f"V{max(versions, default=0) + 1}"


class LostItemModel(nn.Module):
    """EfficientNet-B0 分类模型，同时保留特征向量输出能力。"""

    def __init__(self, num_classes: int, feature_dim: int = 512):
        super().__init__()
        backbone = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.DEFAULT)
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

    def forward_features(self, x: torch.Tensor) -> torch.Tensor:
        x = self.backbone(x)
        x = self.pool(x)
        x = x.flatten(1)
        feat = self.feature_head(x)
        return nn.functional.normalize(feat, p=2, dim=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.forward_features(x)
        return self.classifier(feat)


def calc_macro_metrics_from_predictions(labels_list, preds_list, num_classes):
    if not labels_list or not preds_list or num_classes <= 0:
        return 0.0, 0.0, 0.0

    precision_sum = 0.0
    recall_sum = 0.0
    f1_sum = 0.0

    for class_idx in range(num_classes):
        tp = sum(1 for y_true, y_pred in zip(labels_list, preds_list) if y_true == class_idx and y_pred == class_idx)
        fp = sum(1 for y_true, y_pred in zip(labels_list, preds_list) if y_true != class_idx and y_pred == class_idx)
        fn = sum(1 for y_true, y_pred in zip(labels_list, preds_list) if y_true == class_idx and y_pred != class_idx)

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        precision_sum += precision
        recall_sum += recall
        f1_sum += f1

    return (
        precision_sum / num_classes,
        recall_sum / num_classes,
        f1_sum / num_classes,
    )


def train_one_epoch(model, loader, criterion, optimizer, device, epoch, total_epochs):
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    pbar = tqdm(
        loader,
        desc=f"Epoch [{epoch:02d}/{total_epochs}] Train",
        ncols=100,
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
    )

    for imgs, labels in pbar:
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

        current_loss = total_loss / total if total else 0.0
        current_acc = correct / total if total else 0.0
        pbar.set_postfix({"Loss": f"{current_loss:.4f}", "Acc": f"{current_acc:.4f}"})

    return (total_loss / total if total else 0.0), (correct / total if total else 0.0)


def evaluate(model, loader, criterion, device, epoch, total_epochs):
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    all_labels = []
    all_preds = []

    pbar = tqdm(
        loader,
        desc=f"Epoch [{epoch:02d}/{total_epochs}] Val  ",
        ncols=100,
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]",
    )

    with torch.no_grad():
        for imgs, labels in pbar:
            imgs, labels = imgs.to(device), labels.to(device)
            logits = model(imgs)
            loss = criterion(logits, labels)
            preds = logits.argmax(1)

            total_loss += loss.item() * imgs.size(0)
            correct += (preds == labels).sum().item()
            total += imgs.size(0)
            all_labels.extend(labels.cpu().tolist())
            all_preds.extend(preds.cpu().tolist())

            current_loss = total_loss / total if total else 0.0
            current_acc = correct / total if total else 0.0
            pbar.set_postfix({"Loss": f"{current_loss:.4f}", "Acc": f"{current_acc:.4f}"})

    num_classes = len(loader.dataset.classes) if hasattr(loader.dataset, "classes") else len(set(all_labels))
    macro_precision, macro_recall, macro_f1 = calc_macro_metrics_from_predictions(
        all_labels,
        all_preds,
        num_classes,
    )

    return (
        total_loss / total if total else 0.0,
        correct / total if total else 0.0,
        macro_precision,
        macro_recall,
        macro_f1,
    )


def save_history_csv(path, history):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        csv_writer = csv.DictWriter(
            f,
            fieldnames=[
                "epoch",
                "lr",
                "train_loss",
                "train_acc",
                "val_loss",
                "val_acc",
                "val_macro_precision",
                "val_macro_recall",
                "val_macro_f1",
            ],
        )
        csv_writer.writeheader()
        csv_writer.writerows(history)


def save_training_plot(path, version, history):
    if plt is None or not history:
        return

    epochs_axis = [row["epoch"] for row in history]
    train_loss_axis = [row["train_loss"] for row in history]
    val_loss_axis = [row["val_loss"] for row in history]
    train_acc_axis = [row["train_acc"] for row in history]
    val_acc_axis = [row["val_acc"] for row in history]
    val_f1_axis = [row["val_macro_f1"] for row in history]

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))

    axes[0].plot(epochs_axis, train_loss_axis, label="Train Loss", color="#D55E00", linewidth=2)
    axes[0].plot(epochs_axis, val_loss_axis, label="Val Loss", color="#0072B2", linewidth=2)
    axes[0].set_title(f"Loss Curves ({version})")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[0].grid(alpha=0.25)
    axes[0].legend()

    axes[1].plot(epochs_axis, train_acc_axis, label="Train Acc", color="#009E73", linewidth=2)
    axes[1].plot(epochs_axis, val_acc_axis, label="Val Acc", color="#CC79A7", linewidth=2)
    axes[1].plot(epochs_axis, val_f1_axis, label="Val Macro F1", color="#E69F00", linewidth=2, linestyle="--")
    axes[1].set_title(f"Accuracy Curves ({version})")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Score")
    axes[1].set_ylim(0, 1.0)
    axes[1].grid(alpha=0.25)
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "datasets", "classification")
    train_dir = os.path.join(data_dir, "train")
    val_dir = os.path.join(data_dir, "val")
    model_dir = os.path.join(base_dir, "models")
    runs_dir = os.path.join(base_dir, "runs")

    os.makedirs(model_dir, exist_ok=True)
    os.makedirs(runs_dir, exist_ok=True)

    img_size = 224
    batch_size = 32
    epochs = 45
    lr = 5e-4
    feature_dim = 512
    early_stop_patience = 8
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

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

    if not os.path.exists(train_dir):
        raise FileNotFoundError(f"训练目录不存在: {train_dir}")
    if not os.path.exists(val_dir):
        raise FileNotFoundError(f"验证目录不存在: {val_dir}")

    train_dataset = datasets.ImageFolder(train_dir, transform=train_transform)
    val_dataset = datasets.ImageFolder(val_dir, transform=val_transform)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0, pin_memory=False)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0, pin_memory=False)

    num_classes = len(train_dataset.classes)
    class_to_idx = train_dataset.class_to_idx
    idx_to_class = {v: k for k, v in class_to_idx.items()}

    print(f"设备        : {device}")
    print(f"类别数      : {num_classes}")
    print(f"训练样本    : {len(train_dataset)}")
    print(f"验证样本    : {len(val_dataset)}")
    print(f"类别列表    : {train_dataset.classes}")

    model = LostItemModel(num_classes, feature_dim).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)

    version = get_next_version(model_dir)
    model_filename = f"lost_item_model_{version}.pth"
    meta_filename = f"model_meta_{version}.json"
    history_filename = f"training_history_{version}.json"
    history_csv_filename = f"training_history_{version}.csv"
    history_plot_filename = f"training_curves_{version}.png"

    model_path = os.path.join(model_dir, model_filename)
    meta_path = os.path.join(model_dir, meta_filename)
    history_path = os.path.join(model_dir, history_filename)
    history_csv_path = os.path.join(model_dir, history_csv_filename)
    history_plot_path = os.path.join(model_dir, history_plot_filename)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_name = f"{version}_{timestamp}"
    run_dir = os.path.join(runs_dir, run_name)
    tb_writer = SummaryWriter(log_dir=run_dir) if SummaryWriter is not None else None

    print(f"\n本次训练版本: {version}")
    print(f"模型保存为  : {model_filename}")
    print(f"TensorBoard : {run_dir if tb_writer is not None else '未启用'}")
    print("\n" + "=" * 60)
    print("开始训练...")
    print("=" * 60)
    print(f"\n总 batch 数 : 训练 {len(train_loader)} | 验证 {len(val_loader)}")
    print("=" * 60)

    start_time = time.time()
    history = []
    best_val_acc = 0.0
    best_val_macro_f1 = 0.0
    best_epoch = 0
    best_model_updated = False
    epochs_without_improvement = 0
    stopped_early = False

    for epoch in range(1, epochs + 1):
        current_lr = optimizer.param_groups[0]["lr"]

        train_loss, train_acc = train_one_epoch(model, train_loader, criterion, optimizer, device, epoch, epochs)
        val_loss, val_acc, val_macro_precision, val_macro_recall, val_macro_f1 = evaluate(
            model, val_loader, criterion, device, epoch, epochs
        )
        scheduler.step()

        print(f"  Epoch [{epoch:02d}/{epochs}]")
        print(f"    Train - Loss: {train_loss:.4f} | Acc: {train_acc:.4f}")
        print(f"    Val   - Loss: {val_loss:.4f} | Acc: {val_acc:.4f}")
        print(
            f"    Val   - Macro Precision: {val_macro_precision:.4f} | "
            f"Macro Recall: {val_macro_recall:.4f} | Macro F1: {val_macro_f1:.4f}"
        )

        row = {
            "epoch": epoch,
            "lr": round(float(current_lr), 8),
            "train_loss": round(float(train_loss), 6),
            "train_acc": round(float(train_acc), 6),
            "val_loss": round(float(val_loss), 6),
            "val_acc": round(float(val_acc), 6),
            "val_macro_precision": round(float(val_macro_precision), 6),
            "val_macro_recall": round(float(val_macro_recall), 6),
            "val_macro_f1": round(float(val_macro_f1), 6),
        }
        history.append(row)

        if tb_writer is not None:
            tb_writer.add_scalar("loss/train", train_loss, epoch)
            tb_writer.add_scalar("loss/val", val_loss, epoch)
            tb_writer.add_scalar("accuracy/train", train_acc, epoch)
            tb_writer.add_scalar("accuracy/val", val_acc, epoch)
            tb_writer.add_scalar("macro/precision", val_macro_precision, epoch)
            tb_writer.add_scalar("macro/recall", val_macro_recall, epoch)
            tb_writer.add_scalar("macro/f1", val_macro_f1, epoch)
            tb_writer.add_scalar("lr/current", current_lr, epoch)

        improved = False
        if (
            val_macro_f1 > best_val_macro_f1
            or (
                abs(val_macro_f1 - best_val_macro_f1) < 1e-8
                and val_acc > best_val_acc
            )
        ):
            improved = True
            best_val_acc = val_acc
            best_val_macro_f1 = val_macro_f1
            best_epoch = epoch
            torch.save(model.state_dict(), model_path)
            best_model_updated = True
            epochs_without_improvement = 0
            print(
                f"    Best model updated: val_macro_f1={val_macro_f1:.4f}, "
                f"val_acc={val_acc:.4f}"
            )

        if not improved:
            epochs_without_improvement += 1
            print(f"    No improvement for {epochs_without_improvement} epoch(s)")

        print("-" * 60)

        if epochs_without_improvement >= early_stop_patience:
            stopped_early = True
            print(
                f"Early stopping triggered at epoch {epoch}: "
                f"val_macro_f1 has not improved for {early_stop_patience} epochs."
            )
            break

    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    save_history_csv(history_csv_path, history)
    save_training_plot(history_plot_path, version, history)

    total_time = time.time() - start_time
    meta = {
        "version": version,
        "num_classes": num_classes,
        "feature_dim": feature_dim,
        "img_size": img_size,
        "class_to_idx": class_to_idx,
        "idx_to_class": idx_to_class,
        "best_val_acc": best_val_acc,
        "best_val_macro_f1": best_val_macro_f1,
        "best_epoch": best_epoch,
        "epochs": epochs,
        "actual_epochs_ran": len(history),
        "early_stop_patience": early_stop_patience,
        "stopped_early": stopped_early,
        "training_time": total_time,
        "history_file": history_filename,
        "history_csv_file": history_csv_filename,
        "curves_file": history_plot_filename if plt is not None else None,
        "tensorboard_run_dir": run_dir if tb_writer is not None else None,
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    hours = int(total_time // 3600)
    minutes = int((total_time % 3600) // 60)
    seconds = int(total_time % 60)

    print(
        f"\n训练完成，最佳验证准确率: {best_val_acc:.4f} | "
        f"最佳验证 Macro F1: {best_val_macro_f1:.4f}"
    )
    print(f"总训练时间: {hours:02d}:{minutes:02d}:{seconds:02d} ({total_time:.1f}s)")
    print(f"实际训练轮数: {len(history)} / {epochs}")
    print(f"平均每轮: {total_time / max(len(history), 1):.1f}s")
    print(f"模型文件: {model_path}")
    print(f"元数据  : {meta_path}")
    print(f"历史数据: {history_path}")
    print(f"CSV结果 : {history_csv_path}")
    if plt is not None:
        print(f"曲线图片: {history_plot_path}")
    if tb_writer is not None:
        print(f"runs日志: {run_dir}")

    latest_model_path = os.path.join(model_dir, "lost_item_model.pth")
    latest_meta_path = os.path.join(model_dir, "model_meta.json")
    latest_history_path = os.path.join(model_dir, "training_history.json")
    latest_history_csv_path = os.path.join(model_dir, "training_history.csv")
    latest_plot_path = os.path.join(model_dir, "training_curves.png")

    if best_model_updated and os.path.exists(model_path):
        shutil.copyfile(model_path, latest_model_path)
    else:
        torch.save(model.state_dict(), latest_model_path)
    with open(latest_meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    with open(latest_history_path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    save_history_csv(latest_history_csv_path, history)
    if plt is not None and os.path.exists(history_plot_path):
        with open(history_plot_path, "rb") as src, open(latest_plot_path, "wb") as dst:
            dst.write(src.read())

    if tb_writer is not None:
        tb_writer.add_hparams(
            {
                "img_size": img_size,
                "batch_size": batch_size,
                "epochs": epochs,
                "lr": lr,
                "feature_dim": feature_dim,
                "early_stop_patience": early_stop_patience,
            },
            {
                "hparam/best_val_acc": best_val_acc,
                "hparam/best_val_macro_f1": best_val_macro_f1,
                "hparam/best_epoch": best_epoch,
                "hparam/final_val_macro_f1": history[-1]["val_macro_f1"] if history else 0.0,
            },
        )
        tb_writer.close()

    print(f"\nlatest 已同步更新: {latest_model_path}")


if __name__ == "__main__":
    main()
