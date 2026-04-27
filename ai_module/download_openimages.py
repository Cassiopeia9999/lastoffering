"""
校园失物招领系统 - OpenImages 数据集下载脚本
目标：下载 OpenImages 数据 → 按 bbox 裁剪 → 映射到系统14类 → 全部沉淀到备用库
正式数据集划分：由 check_dataset.py 按 500 / 100 / 50 自动从备用库补齐
备用库：每类最多 2000 张
运行环境：conda opim
"""

import os
import random

import fiftyone as fo
import fiftyone.zoo as foz
from PIL import Image

# ==================== 路径配置 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "datasets")
RAW_DIR = os.path.join(DATASET_DIR, "open-images-v6-raw")
CLASSIFICATION_DIR = os.path.join(DATASET_DIR, "classification")
TRAIN_DIR = os.path.join(CLASSIFICATION_DIR, "train")
VAL_DIR = os.path.join(CLASSIFICATION_DIR, "val")
TEST_DIR = os.path.join(CLASSIFICATION_DIR, "test")
BACKUP_DIR = os.path.join(CLASSIFICATION_DIR, "backup")

for d in [DATASET_DIR, RAW_DIR, TRAIN_DIR, VAL_DIR, TEST_DIR, BACKUP_DIR]:
    os.makedirs(d, exist_ok=True)

fo.config.dataset_zoo_dir = DATASET_DIR

# ==================== 参数 ====================
TARGET_PER_CLASS = 650
BACKUP_PER_CLASS = 2000
TRAIN_COUNT = 500
VAL_COUNT = 100
TEST_COUNT = 50
MAX_SAMPLES = 150000
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# ==================== 系统14类定义 ====================
SYSTEM_CATEGORIES = {
    "mobile_device": {"name": "移动电子设备", "openimages": ["Mobile phone", "Tablet computer"]},
    "laptop": {"name": "笔记本电脑", "openimages": ["Laptop"]},
    "headphones": {"name": "耳机", "openimages": ["Headphones"]},
    "charger": {"name": "充电器/数据线", "openimages": []},
    "bag": {"name": "包类", "openimages": ["Backpack", "Handbag", "Briefcase", "Suitcase"]},
    "book": {"name": "书籍", "openimages": ["Book"]},
    "stationery": {"name": "文具", "openimages": ["Pen", "Pencil case", "Scissors"]},
    "card": {"name": "证件", "openimages": []},
    "keys": {"name": "钥匙", "openimages": []},
    "glasses": {"name": "眼镜", "openimages": ["Glasses", "Sunglasses"]},
    "accessory": {"name": "饰品", "openimages": ["Necklace", "Watch", "Earrings"]},
    "bottle": {"name": "水杯", "openimages": ["Bottle", "Coffee cup", "Mug"]},
    "umbrella": {"name": "雨伞", "openimages": ["Umbrella"]},
    "clothes": {"name": "衣物", "openimages": ["Clothing", "Shirt", "Trousers", "Dress", "Jacket", "Coat"]},
}

OI_TO_SYSTEM = {}
for sys_cat, info in SYSTEM_CATEGORIES.items():
    for oi_cat in info["openimages"]:
        OI_TO_SYSTEM[oi_cat] = sys_cat
OPENIMAGES_CLASSES = list(OI_TO_SYSTEM.keys())


def count_existing(cat):
    t = len([f for f in os.listdir(os.path.join(TRAIN_DIR, cat))
             if os.path.isfile(os.path.join(TRAIN_DIR, cat, f))]) if os.path.exists(os.path.join(TRAIN_DIR, cat)) else 0
    v = len([f for f in os.listdir(os.path.join(VAL_DIR, cat))
             if os.path.isfile(os.path.join(VAL_DIR, cat, f))]) if os.path.exists(os.path.join(VAL_DIR, cat)) else 0
    te = len([f for f in os.listdir(os.path.join(TEST_DIR, cat))
              if os.path.isfile(os.path.join(TEST_DIR, cat, f))]) if os.path.exists(os.path.join(TEST_DIR, cat)) else 0
    return t, v, te


def count_backup(cat):
    backup_cat_dir = os.path.join(BACKUP_DIR, cat)
    if not os.path.exists(backup_cat_dir):
        return 0
    return len([f for f in os.listdir(backup_cat_dir) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))])


print("=" * 60)
print("校园失物招领系统 - OpenImages 数据集下载")
print("=" * 60)
print(f"目标目录     : {DATASET_DIR}")
print(f"正式集目标   : {TARGET_PER_CLASS} (训练{TRAIN_COUNT}/验证{VAL_COUNT}/测试{TEST_COUNT})")
print(f"备用库上限   : {BACKUP_PER_CLASS}")
print(f"OpenImages类 : {len(OPENIMAGES_CLASSES)}")
manual = [f"{k}" for k, v in SYSTEM_CATEGORIES.items() if not v["openimages"]]
print(f"需Kaggle补充 : {manual}")

print("\n" + "=" * 60)
print(f"下载 OpenImages 训练集（最多 {MAX_SAMPLES} 张原图）...")
print("=" * 60)

dataset = foz.load_zoo_dataset(
    "open-images-v6",
    split="train",
    label_types=["detections"],
    classes=OPENIMAGES_CLASSES,
    max_samples=MAX_SAMPLES,
    shuffle=True,
    dataset_dir=os.path.join(RAW_DIR, "train"),
)
print(f"\n下载完成，共 {len(dataset)} 张原图")

print("\n" + "=" * 60)
print("按 bbox 裁剪，映射到系统类别，并只补充到备用库...")
print("=" * 60)

need_backup = {}
for cat, info in SYSTEM_CATEGORIES.items():
    if not info["openimages"]:
        continue
    b = count_backup(cat)
    backup_gap = BACKUP_PER_CLASS - b
    if backup_gap > 0:
        need_backup[cat] = backup_gap

if not need_backup:
    print("所有 OpenImages 类别备用库均已达标，跳过裁剪。")
else:
    print(f"备用库需要补充的类别：{ {k: v for k, v in need_backup.items()} }")

saved_count = {cat: 0 for cat in need_backup}
current_backup = {cat: count_backup(cat) for cat in need_backup}
processed_samples = 0
matched_samples = 0
total_samples = len(dataset)

for cat in SYSTEM_CATEGORIES:
    os.makedirs(os.path.join(BACKUP_DIR, cat), exist_ok=True)

for sample in dataset:
    processed_samples += 1
    if not sample.ground_truth:
        if processed_samples % 1000 == 0:
            progress = {cat: f"{current_backup[cat] + saved_count[cat]}/{BACKUP_PER_CLASS}" for cat in sorted(saved_count.keys())}
            print(f"[crop] processed={processed_samples}/{total_samples} matched={matched_samples} saved={progress}")
        continue

    all_backup_satisfied = all(current_backup[cat] + saved_count[cat] >= BACKUP_PER_CLASS for cat in need_backup)
    if all_backup_satisfied:
        print(f"[crop] all backup targets reached at sample {processed_samples}/{total_samples}, stop early")
        break

    relevant_detections = []
    for det in sample.ground_truth.detections:
        if det.label not in OI_TO_SYSTEM:
            continue
        sys_label = OI_TO_SYSTEM[det.label]
        if sys_label not in need_backup:
            continue
        if current_backup[sys_label] + saved_count[sys_label] >= BACKUP_PER_CLASS:
            continue
        relevant_detections.append((sys_label, det))

    if not relevant_detections:
        if processed_samples % 1000 == 0:
            progress = {cat: f"{current_backup[cat] + saved_count[cat]}/{BACKUP_PER_CLASS}" for cat in sorted(saved_count.keys())}
            print(f"[crop] processed={processed_samples}/{total_samples} matched={matched_samples} saved={progress}")
        continue

    try:
        with Image.open(sample.filepath) as opened:
            img = opened.convert("RGB")
            W, H = img.size
            matched_samples += 1

            for sys_label, det in relevant_detections:
                if current_backup[sys_label] + saved_count[sys_label] >= BACKUP_PER_CLASS:
                    continue

                bx, by, bw, bh = det.bounding_box
                x1, y1 = max(0, int(bx * W)), max(0, int(by * H))
                x2, y2 = min(W, int((bx + bw) * W)), min(H, int((by + bh) * H))
                if x2 <= x1 or y2 <= y1:
                    continue

                try:
                    crop = img.crop((x1, y1, x2, y2))
                    dst_idx = current_backup[sys_label] + saved_count[sys_label]
                    backup_fname = f"backup_{sample.id}_{det.id}_{dst_idx:05d}.jpg"
                    path = os.path.join(BACKUP_DIR, sys_label, backup_fname)
                    if os.path.exists(path):
                        continue
                    crop.save(path, "JPEG")
                    crop.close()
                    saved_count[sys_label] += 1
                except Exception:
                    continue
    except Exception:
        continue

    if processed_samples % 1000 == 0:
        progress = {cat: f"{current_backup[cat] + saved_count[cat]}/{BACKUP_PER_CLASS}" for cat in sorted(saved_count.keys())}
        print(f"[crop] processed={processed_samples}/{total_samples} matched={matched_samples} saved={progress}")

print("\n本次新裁剪各类别数量：")
for cat in sorted(need_backup.keys()):
    before = current_backup[cat]
    added = saved_count[cat]
    flag = "✅" if before + added >= BACKUP_PER_CLASS else "⚠️ "
    print(f"  {flag} {cat:<20} 备用已有 {before:>4} + 新增 {added:>5} = {before + added:>5} 张")

print("\n" + "=" * 75)
print("数据集统计（OpenImages 部分，基于备用库实际文件数）")
print("=" * 75)
print(f"{'类别':<18} {'训练':>6} {'验证':>6} {'测试':>6} {'正式库':>8} {'备用库':>8} {'状态':>10}")
print("-" * 75)
total_t, total_v, total_te, total_b = 0, 0, 0, 0
for cat in SYSTEM_CATEGORIES:
    if not SYSTEM_CATEGORIES[cat]["openimages"]:
        print(f"{cat:<18} {'--':>6} {'--':>6} {'--':>6} {'--':>8} {'--':>8}   Kaggle")
        continue
    t, v, te = count_existing(cat)
    b = count_backup(cat)
    total_t += t
    total_v += v
    total_te += te
    total_b += b
    total = t + v + te

    if b >= BACKUP_PER_CLASS:
        status = "✅ 备用达标"
    elif b > 0:
        status = f"⚠️ 缺{BACKUP_PER_CLASS - b}"
    else:
        status = "❌ 无备用"
    print(f"{cat:<18} {t:>6} {v:>6} {te:>6} {total:>8} {b:>8}   {status}")
print("-" * 75)
print(f"{'合计':<18} {total_t:>6} {total_v:>6} {total_te:>6} {total_t+total_v+total_te:>8} {total_b:>8}")

print(f"\n分类数据集路径: {CLASSIFICATION_DIR}")
print("\n下一步：运行 download_kaggle.py 补充 charger / card / keys 类别")
print("之后运行 check_dataset.py 自动从备用库补齐正式的 train / val / test")
