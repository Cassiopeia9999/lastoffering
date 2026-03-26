"""
校园失物招领系统 - OpenImages 数据集下载与均衡脚本
目标：下载 OpenImages 数据 → 按 bbox 裁剪 → 映射到系统14类 → 均衡到每类目标数量
划分比例：训练集 500 / 验证集 100 / 测试集 50（共650张/类）
备用库：额外350张/类
运行环境：conda opim
"""

import fiftyone as fo
import fiftyone.zoo as foz
import os
import random
from PIL import Image
from collections import defaultdict

# ==================== 路径配置 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "datasets")
RAW_DIR = os.path.join(DATASET_DIR, "open-images-v6-raw")
CLASSIFICATION_DIR = os.path.join(DATASET_DIR, "classification")
TRAIN_DIR = os.path.join(CLASSIFICATION_DIR, "train")
VAL_DIR = os.path.join(CLASSIFICATION_DIR, "val")
TEST_DIR = os.path.join(CLASSIFICATION_DIR, "test")
BACKUP_DIR = os.path.join(CLASSIFICATION_DIR, "backup")  # 备用库

for d in [DATASET_DIR, RAW_DIR, TRAIN_DIR, VAL_DIR, TEST_DIR, BACKUP_DIR]:
    os.makedirs(d, exist_ok=True)

fo.config.dataset_zoo_dir = DATASET_DIR

# ==================== 均衡参数 ====================
TARGET_PER_CLASS = 650   # 每个类别的目标图片数（train+val+test合计）
BACKUP_PER_CLASS = 350   # 备用库目标
TRAIN_COUNT = 500        # 训练集目标
VAL_COUNT = 100           # 验证集目标
TEST_COUNT = 50          # 测试集目标
MAX_SAMPLES = 100000     # 向 OpenImages 请求的最大原图数
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# ==================== 系统14类定义 ====================
SYSTEM_CATEGORIES = {
    "mobile_device": {
        "name": "移动电子设备",
        "openimages": ["Mobile phone", "Tablet computer"],
    },
    "laptop": {
        "name": "笔记本电脑",
        "openimages": ["Laptop"],
    },
    "headphones": {
        "name": "耳机",
        "openimages": ["Headphones"],
    },
    "charger": {
        "name": "充电器/数据线",
        "openimages": [],  # OpenImages 无此类，由 download_kaggle.py 补充
    },
    "bag": {
        "name": "包类",
        "openimages": ["Backpack", "Handbag", "Briefcase", "Suitcase"],
    },
    "book": {
        "name": "书籍",
        "openimages": ["Book"],
    },
    "stationery": {
        "name": "文具",
        "openimages": ["Pen", "Pencil case", "Scissors"],
    },
    "card": {
        "name": "证件",
        "openimages": [],  # OpenImages 无此类，由 download_kaggle.py 补充
    },
    "keys": {
        "name": "钥匙",
        "openimages": [],  # OpenImages 无此类，由 download_kaggle.py 补充
    },
    "glasses": {
        "name": "眼镜",
        "openimages": ["Glasses", "Sunglasses"],
    },
    "accessory": {
        "name": "饰品",
        "openimages": ["Necklace", "Watch", "Earrings"],
    },
    "bottle": {
        "name": "水杯",
        "openimages": ["Bottle", "Coffee cup", "Mug"],
    },
    "umbrella": {
        "name": "雨伞",
        "openimages": ["Umbrella"],
    },
    "clothes": {
        "name": "衣物",
        "openimages": ["Clothing", "Shirt", "Trousers", "Dress", "Jacket", "Coat"],
    },
}

# OpenImages 类别 → 系统类别 反向映射
OI_TO_SYSTEM = {}
for sys_cat, info in SYSTEM_CATEGORIES.items():
    for oi_cat in info["openimages"]:
        OI_TO_SYSTEM[oi_cat] = sys_cat

OPENIMAGES_CLASSES = list(OI_TO_SYSTEM.keys())

# ==================== 打印配置 ====================
print("=" * 60)
print("校园失物招领系统 - OpenImages 数据集下载与均衡")
print("=" * 60)
print(f"目标目录     : {DATASET_DIR}")
print(f"每类目标数量 : {TARGET_PER_CLASS} (训练{TRAIN_COUNT}/验证{VAL_COUNT}/测试{TEST_COUNT})")
print(f"OpenImages类 : {len(OPENIMAGES_CLASSES)}")
manual = [f"{k}" for k, v in SYSTEM_CATEGORIES.items() if not v["openimages"]]
print(f"需Kaggle补充 : {manual}")

# ==================== 统计各类别已有文件数 ====================
def count_existing(cat):
    """统计某类别在 train/val/test 中已有的文件数"""
    t = len([f for f in os.listdir(os.path.join(TRAIN_DIR, cat))
             if os.path.isfile(os.path.join(TRAIN_DIR, cat, f))]) if os.path.exists(os.path.join(TRAIN_DIR, cat)) else 0
    v = len([f for f in os.listdir(os.path.join(VAL_DIR, cat))
             if os.path.isfile(os.path.join(VAL_DIR, cat, f))]) if os.path.exists(os.path.join(VAL_DIR, cat)) else 0
    te = len([f for f in os.listdir(os.path.join(TEST_DIR, cat))
              if os.path.isfile(os.path.join(TEST_DIR, cat, f))]) if os.path.exists(os.path.join(TEST_DIR, cat)) else 0
    return t, v, te


def count_backup(cat):
    """统计备用库已有图片数"""
    backup_cat_dir = os.path.join(BACKUP_DIR, cat)
    if not os.path.exists(backup_cat_dir):
        return 0
    return len([f for f in os.listdir(backup_cat_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])


# ==================== 下载 ====================
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

# ==================== 按 bbox 裁剪 ====================
print("\n" + "=" * 60)
print("按 bbox 裁剪，映射到系统类别...")
print("=" * 60)

# 哪些类别还有缺口
need_more = {}
for cat, info in SYSTEM_CATEGORIES.items():
    if not info["openimages"]:
        continue
    t, v, te = count_existing(cat)
    gap = TARGET_PER_CLASS - (t + v + te)
    if gap > 0:
        need_more[cat] = gap

# 检查哪些类别需要补充（正式库 + 备用库）
need_more = {}
need_backup = {}
for cat, info in SYSTEM_CATEGORIES.items():
    if not info["openimages"]:
        continue
    t, v, te = count_existing(cat)
    b = count_backup(cat)
    already_main = t + v + te
    
    # 正式库缺口
    main_gap = TARGET_PER_CLASS - already_main
    if main_gap > 0:
        need_more[cat] = main_gap
    
    # 备用库缺口
    backup_gap = BACKUP_PER_CLASS - b
    if backup_gap > 0:
        need_backup[cat] = backup_gap

# 需要处理的类别 = 正式库有缺口的 + 备用库有缺口的
all_needed_cats = set(need_more.keys()) | set(need_backup.keys())

if not all_needed_cats:
    print("所有 OpenImages 类别正式库和备用库均已达标，跳过裁剪。")
else:
    if need_more:
        print(f"正式库需要补充的类别：{ {k: v for k, v in need_more.items()} }")
    if need_backup:
        print(f"备用库需要补充的类别：{ {k: v for k, v in need_backup.items()} }")

# 收集裁剪图（处理正式库或备用库有缺口的类别）
class_images = defaultdict(list)

for sample in dataset:
    if not sample.ground_truth:
        continue
    # 如果所有需要的类别都收够了，提前退出
    # 正式库需要 need_more[cat] 张，备用库需要 need_backup[cat] 张
    # 为保险起见，多收集一些（乘以系数3）
    all_main_satisfied = all(len(class_images[cat]) >= need_more.get(cat, 0) * 3 
                             for cat in need_more)
    all_backup_satisfied = all(len(class_images[cat]) >= need_backup.get(cat, 0) * 3 
                               for cat in need_backup)
    if all_main_satisfied and all_backup_satisfied:
        break
    try:
        img = Image.open(sample.filepath)
        W, H = img.size
    except Exception:
        continue

    for det in sample.ground_truth.detections:
        if det.label not in OI_TO_SYSTEM:
            continue
        sys_label = OI_TO_SYSTEM[det.label]
        # 只处理正式库或备用库有缺口的类别
        if sys_label not in all_needed_cats:
            continue

        bx, by, bw, bh = det.bounding_box
        x1, y1 = max(0, int(bx * W)), max(0, int(by * H))
        x2, y2 = min(W, int((bx + bw) * W)), min(H, int((by + bh) * H))
        if x2 <= x1 or y2 <= y1:
            continue

        try:
            crop = img.crop((x1, y1, x2, y2))
            fname = f"{sample.id}_{det.id}.jpg"
            class_images[sys_label].append((crop, fname))
        except Exception:
            continue

print("\n本次新裁剪各类别数量：")
for cat, imgs in sorted(class_images.items()):
    already_t, already_v, already_te = count_existing(cat)
    already = already_t + already_v + already_te
    flag = "✅" if already + len(imgs) >= TARGET_PER_CLASS else "⚠️ "
    print(f"  {flag} {cat:<20} 已有 {already:>4} + 新增 {len(imgs):>5} = {already+len(imgs):>5} 张")

# ==================== 均衡截断（含备用库）====================
print("\n" + "=" * 60)
print(f"均衡截断：正式库最多补到 {TARGET_PER_CLASS} 张，备用库最多 {BACKUP_PER_CLASS} 张...")
print("=" * 60)

for cat in class_images:
    existing_t, existing_v, existing_te = count_existing(cat)
    already_main = existing_t + existing_v + existing_te
    already_backup = count_backup(cat)
    
    # 正式库缺口
    main_gap = max(0, TARGET_PER_CLASS - already_main)
    # 备用库缺口
    backup_gap = max(0, BACKUP_PER_CLASS - already_backup)
    # 总共需要的数量
    total_need = main_gap + backup_gap
    
    imgs = class_images[cat]
    random.shuffle(imgs)
    # 只取需要的数量（正式库+备用库）
    class_images[cat] = imgs[:total_need]

# ==================== 创建类别目录 ====================
for cat in SYSTEM_CATEGORIES:
    os.makedirs(os.path.join(TRAIN_DIR, cat), exist_ok=True)
    os.makedirs(os.path.join(VAL_DIR, cat), exist_ok=True)
    os.makedirs(os.path.join(TEST_DIR, cat), exist_ok=True)
    os.makedirs(os.path.join(BACKUP_DIR, cat), exist_ok=True)

# ==================== 划分并保存（正式库 + 备用库）====================
print("\n划分训练/验证/测试集并保存图片...")

train_count = defaultdict(int)
val_count = defaultdict(int)
test_count = defaultdict(int)
backup_count = defaultdict(int)

for cat, images in class_images.items():
    existing_t, existing_v, existing_te = count_existing(cat)
    existing_backup = count_backup(cat)
    
    # 计算各类别还需要多少
    need_train = max(0, TRAIN_COUNT - existing_t)
    need_val = max(0, VAL_COUNT - existing_v)
    need_test = max(0, TEST_COUNT - existing_te)
    need_backup = max(0, BACKUP_PER_CLASS - existing_backup)
    
    # 随机打乱后分配
    random.shuffle(images)
    
    idx = 0
    # 分配给训练集
    for img, fname in images[idx:idx+need_train]:
        path = os.path.join(TRAIN_DIR, cat, fname)
        if not os.path.exists(path):
            try:
                img.save(path, "JPEG")
                train_count[cat] += 1
            except Exception:
                continue
    idx += need_train
    
    # 分配给验证集
    for img, fname in images[idx:idx+need_val]:
        path = os.path.join(VAL_DIR, cat, fname)
        if not os.path.exists(path):
            try:
                img.save(path, "JPEG")
                val_count[cat] += 1
            except Exception:
                continue
    idx += need_val
    
    # 分配给测试集
    for img, fname in images[idx:idx+need_test]:
        path = os.path.join(TEST_DIR, cat, fname)
        if not os.path.exists(path):
            try:
                img.save(path, "JPEG")
                test_count[cat] += 1
            except Exception:
                continue
    idx += need_test
    
    # 分配给备用库
    for img, fname in images[idx:idx+need_backup]:
        backup_fname = f"backup_{fname}"
        path = os.path.join(BACKUP_DIR, cat, backup_fname)
        if not os.path.exists(path):
            try:
                img.save(path, "JPEG")
                backup_count[cat] += 1
            except Exception:
                continue

# ==================== 统计报告 ====================
print("\n" + "=" * 75)
print("数据集统计（OpenImages 部分，基于目录实际文件数）")
print("=" * 75)
print(f"{'类别':<18} {'训练':>6} {'验证':>6} {'测试':>6} {'正式库':>8} {'备用库':>8} {'状态':>8}")
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
    
    if total >= TARGET_PER_CLASS:
        if b >= BACKUP_PER_CLASS:
            status = "✅ 完整"
        else:
            status = f"📦 备用{b}"
    elif total > 0:
        status = "⚠️ 不足"
    else:
        status = "❌ 无"
    print(f"{cat:<18} {t:>6} {v:>6} {te:>6} {total:>8} {b:>8}   {status}")
print("-" * 75)
print(f"{'合计':<18} {total_t:>6} {total_v:>6} {total_te:>6} {total_t+total_v+total_te:>8} {total_b:>8}")

print(f"\n分类数据集路径: {CLASSIFICATION_DIR}")
print("\n下一步：运行 download_kaggle.py 补充 charger / card / keys 类别")
