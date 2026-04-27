"""
校园失物招领系统 - 自动图片爬取脚本（已弃用，保留 legacy 代码）

默认行为：
  仅提示当前脚本已弃用，请改用：
    python ai_module/crawl_datasets.py

如需临时启用旧逻辑进行对照测试，可显式执行：
  python ai_module/download_kaggle.py --legacy
"""

import os
import random
import shutil
import sys
from pathlib import Path

from PIL import Image

# ==================== 路径配置 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "datasets", "classification")
TRAIN_DIR = os.path.join(DATASET_DIR, "train")
VAL_DIR = os.path.join(DATASET_DIR, "val")
TEST_DIR = os.path.join(DATASET_DIR, "test")
TEMP_DIR = os.path.join(BASE_DIR, "datasets", "temp_crawled")
BACKUP_DIR = os.path.join(DATASET_DIR, "backup")

TARGET_PER_CLASS = 650
TRAIN_COUNT = 500
VAL_COUNT = 100
TEST_COUNT = 50

# legacy 旧版参数，保留作对照
BACKUP_PER_CLASS = 350
TOTAL_TARGET_PER_CLASS = TARGET_PER_CLASS + BACKUP_PER_CLASS

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

for cat in ["charger", "card", "keys"]:
    os.makedirs(os.path.join(TRAIN_DIR, cat), exist_ok=True)
    os.makedirs(os.path.join(VAL_DIR, cat), exist_ok=True)
    os.makedirs(os.path.join(TEST_DIR, cat), exist_ok=True)
    os.makedirs(os.path.join(BACKUP_DIR, cat), exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

SEARCH_QUERIES = {
    "charger": [
        "phone charger",
        "USB charging cable",
        "mobile charger",
        "lightning cable",
        "type c cable",
    ],
    "card": [
        "ID card",
        "student card",
        "identity card photo",
        "credit card",
        "bank card",
    ],
    "keys": [
        "door key",
        "house key",
        "car key fob",
        "metal key",
        "keychain",
    ],
}

MIN_IMAGE_SIZE = 224
MAX_ASPECT_RATIO = 3.0
REJECTED_KEYWORDS = ["keyboard", "piano", "keycap", "button", "switch"]


def count_existing(target_class: str) -> tuple:
    t_dir = os.path.join(TRAIN_DIR, target_class)
    v_dir = os.path.join(VAL_DIR, target_class)
    te_dir = os.path.join(TEST_DIR, target_class)

    t_count = len([f for f in os.listdir(t_dir) if os.path.isfile(os.path.join(t_dir, f))]) if os.path.exists(t_dir) else 0
    v_count = len([f for f in os.listdir(v_dir) if os.path.isfile(os.path.join(v_dir, f))]) if os.path.exists(v_dir) else 0
    te_count = len([f for f in os.listdir(te_dir) if os.path.isfile(os.path.join(te_dir, f))]) if os.path.exists(te_dir) else 0
    return t_count, v_count, te_count


def get_image_hash(img_path: str) -> str:
    try:
        with Image.open(img_path) as img:
            img = img.convert("L").resize((8, 8), Image.Resampling.LANCZOS)
            pixels = list(img.getdata())
            avg = sum(pixels) / len(pixels)
            bits = "".join("1" if p > avg else "0" for p in pixels)
            return hex(int(bits, 2))[2:].zfill(16)
    except Exception:
        return None


def count_backup_images(target_class: str) -> int:
    backup_class_dir = os.path.join(BACKUP_DIR, target_class)
    if not os.path.exists(backup_class_dir):
        return 0
    return len([
        f for f in os.listdir(backup_class_dir)
        if os.path.isfile(os.path.join(backup_class_dir, f))
        and f.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))
    ])


def load_existing_hashes(target_class: str) -> set:
    hashes = set()
    for dir_path in [TRAIN_DIR, VAL_DIR, TEST_DIR]:
        class_dir = os.path.join(dir_path, target_class)
        if not os.path.exists(class_dir):
            continue
        for fname in os.listdir(class_dir):
            if fname.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                fpath = os.path.join(class_dir, fname)
                h = get_image_hash(fpath)
                if h:
                    hashes.add(h)
    return hashes


def validate_image(img_path: str, existing_hashes: set) -> tuple:
    fname_lower = os.path.basename(img_path).lower()
    for keyword in REJECTED_KEYWORDS:
        if keyword in fname_lower:
            return False, f"文件名包含排除词: {keyword}"

    try:
        with Image.open(img_path) as img:
            width, height = img.size
            min_side = min(width, height)
            if min_side < MIN_IMAGE_SIZE:
                return False, f"尺寸过小: {width}x{height}"

            aspect = max(width, height) / min(width, height)
            if aspect > MAX_ASPECT_RATIO:
                return False, f"宽高比过大: {aspect:.2f}"

            img_hash = get_image_hash(img_path)
            if img_hash and img_hash in existing_hashes:
                return False, "重复图片"
            return True, img_hash
    except Exception as e:
        return False, f"无法打开图片: {e}"


def clean_folder_name(query: str) -> str:
    cleaned = query.strip()
    for char in '<>:"/\\|?*':
        cleaned = cleaned.replace(char, "_")
    return cleaned


def download_from_bing(query: str, output_dir: str, limit: int = 100):
    from bing_image_downloader import downloader

    folder_name = clean_folder_name(query)
    query_dir = os.path.join(output_dir, folder_name)

    def count_images_in_dir(d):
        if not os.path.exists(d):
            return 0
        return len([f for f in os.listdir(d) if f.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))])

    before = count_images_in_dir(query_dir)

    try:
        os.makedirs(query_dir, exist_ok=True)
        downloader.download(
            query=query,
            limit=limit,
            output_dir=output_dir,
            adult_filter_off=True,
            force_replace=False,
            timeout=60,
            verbose=False,
        )

        raw_query_dir = os.path.join(output_dir, query)
        if os.path.exists(raw_query_dir) and raw_query_dir != query_dir:
            for fname in os.listdir(raw_query_dir):
                src = os.path.join(raw_query_dir, fname)
                dst = os.path.join(query_dir, fname)
                if os.path.isfile(src) and not os.path.exists(dst):
                    shutil.move(src, dst)
            try:
                os.rmdir(raw_query_dir)
            except Exception:
                pass

        after = count_images_in_dir(query_dir)
        downloaded = after - before
        if downloaded > 0:
            print(f"    ✅ 成功下载 {downloaded} 张（共 {after} 张）")
        else:
            print(f"    ℹ️ 未获取新图片（共 {after} 张）")
        return downloaded
    except Exception as e:
        print(f"    ⚠️ 下载出错: {e}")
        return 0


def distribute_images_legacy(src_dir: str, target_class: str):
    img_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
    images = []
    for root, _, files in os.walk(src_dir):
        for f in files:
            if Path(f).suffix.lower() in img_extensions:
                images.append(os.path.join(root, f))

    if not images:
        print("  ⚠️ 没有找到图片")
        return

    t_exist, v_exist, te_exist = count_existing(target_class)
    exist_total = t_exist + v_exist + te_exist
    main_gap = TARGET_PER_CLASS - exist_total
    backup_exist = count_backup_images(target_class)
    backup_gap = BACKUP_PER_CLASS - backup_exist

    existing_hashes = load_existing_hashes(target_class)
    valid_images = []
    for img_path in images:
        is_valid, result = validate_image(img_path, existing_hashes)
        if is_valid:
            valid_images.append((img_path, result))
            existing_hashes.add(result)

    random.shuffle(valid_images)
    to_main = valid_images[:max(0, main_gap)]
    remaining = valid_images[max(0, main_gap):]
    to_backup = remaining[:max(0, backup_gap)]

    need_train = max(0, TRAIN_COUNT - t_exist)
    need_val = max(0, VAL_COUNT - v_exist)
    need_test = max(0, TEST_COUNT - te_exist)

    idx = 0
    for img_path, _ in to_main[:need_train]:
        img = Image.open(img_path).convert("RGB")
        img.save(os.path.join(TRAIN_DIR, target_class, f"legacy_{target_class}_{idx:05d}.jpg"), "JPEG", quality=90)
        idx += 1
    for img_path, _ in to_main[need_train:need_train + need_val]:
        img = Image.open(img_path).convert("RGB")
        img.save(os.path.join(VAL_DIR, target_class, f"legacy_{target_class}_{idx:05d}.jpg"), "JPEG", quality=90)
        idx += 1
    for img_path, _ in to_main[need_train + need_val:need_train + need_val + need_test]:
        img = Image.open(img_path).convert("RGB")
        img.save(os.path.join(TEST_DIR, target_class, f"legacy_{target_class}_{idx:05d}.jpg"), "JPEG", quality=90)
        idx += 1

    for i, (img_path, _) in enumerate(to_backup):
        img = Image.open(img_path).convert("RGB")
        img.save(os.path.join(BACKUP_DIR, target_class, f"legacy_backup_{target_class}_{backup_exist + i:05d}.jpg"), "JPEG", quality=90)

    print(f"  ✅ legacy 分配完成: formal={len(to_main[:TARGET_PER_CLASS])} backup={len(to_backup)}")


def run_legacy():
    print("=" * 72)
    print("正在运行 download_kaggle.py 的 legacy 逻辑")
    print("注意：该逻辑已不推荐使用，仅保留用于对照或回滚测试")
    print("=" * 72)

    for cat in ["charger", "card", "keys"]:
        temp_class_dir = os.path.join(TEMP_DIR, cat)
        os.makedirs(temp_class_dir, exist_ok=True)
        total_downloaded = 0
        for query in SEARCH_QUERIES.get(cat, [cat]):
            print(f"  🔍 {cat}: {query}")
            total_downloaded += download_from_bing(query, temp_class_dir, limit=150)
        print(f"  📊 本次累计成功下载: {total_downloaded} 张")
        distribute_images_legacy(temp_class_dir, cat)
        try:
            shutil.rmtree(temp_class_dir)
        except Exception:
            pass


def main():
    if "--legacy" in sys.argv:
        run_legacy()
        return

    print("=" * 72)
    print("download_kaggle.py 已弃用（代码已保留，但默认禁用）")
    print("=" * 72)
    print("请改用以下脚本补充 charger / card / keys 三类数据：")
    print("  python ai_module/crawl_datasets.py")
    print("")
    print("如确实需要运行旧逻辑进行对照测试，可显式执行：")
    print("  python ai_module/download_kaggle.py --legacy")
    print("=" * 72)


if __name__ == "__main__":
    main()
