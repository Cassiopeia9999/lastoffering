"""
校园失物招领系统 - 增强版数据爬取脚本（backup 版）

针对 charger / card / keys 三类难以获取的数据集，统一沉淀到 backup，
正式数据集由 check_dataset.py 再按 500 / 100 / 50 随机分配。

当前实现：
1. Bing 图片搜索下载
2. 多关键词补充
3. 感知哈希去重
4. 尺寸 / 宽高比 / 文件名过滤
5. 统一写入 backup，目标每类最多 2000 张

运行方式：
  conda activate opim
  python ai_module/crawl_datasets.py
"""

import os
import random
import shutil
from pathlib import Path

from PIL import Image

# ==================== 路径配置 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "datasets", "classification")
TRAIN_DIR = os.path.join(DATASET_DIR, "train")
VAL_DIR = os.path.join(DATASET_DIR, "val")
TEST_DIR = os.path.join(DATASET_DIR, "test")
BACKUP_DIR = os.path.join(DATASET_DIR, "backup")
TEMP_DIR = os.path.join(BASE_DIR, "datasets", "temp_crawled")

TARGET_PER_CLASS = 650
BACKUP_PER_CLASS = 2000
TRAIN_COUNT = 500
VAL_COUNT = 100
TEST_COUNT = 50
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

for cat in ["charger", "card", "keys"]:
    os.makedirs(os.path.join(TRAIN_DIR, cat), exist_ok=True)
    os.makedirs(os.path.join(VAL_DIR, cat), exist_ok=True)
    os.makedirs(os.path.join(TEST_DIR, cat), exist_ok=True)
    os.makedirs(os.path.join(BACKUP_DIR, cat), exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# ==================== 搜索关键词配置（增强版）====================
SEARCH_QUERIES = {
    "charger": [
        "phone charger",
        "USB charging cable",
        "mobile charger",
        "lightning cable",
        "type c cable",
        "wall charger adapter",
        "charging cable on table",
        "charger plug close-up",
        "phone charging adapter",
    ],
    "card": [
        "student ID card",
        "campus card",
        "ID card photo",
        "bank card close-up",
        "membership card on desk",
        "access card badge",
        "plastic card object",
        "identity card mockup",
    ],
    "keys": [
        "door key",
        "house key",
        "metal key",
        "keychain with keys",
        "set of keys",
        "car key with metal key",
        "single key object",
        "keys on desk",
        "lock and key object",
    ],
}

# ==================== 图片过滤配置 ====================
MIN_IMAGE_SIZE = 224
MAX_ASPECT_RATIO = 3.0
MIN_FILE_SIZE = 5 * 1024
REJECTED_KEYWORDS = [
    "keyboard", "piano", "keycap", "button", "switch",
    "cartoon", "drawing", "illustration", "clipart",
]

IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}


def count_existing(target_class: str) -> tuple:
    t_dir = os.path.join(TRAIN_DIR, target_class)
    v_dir = os.path.join(VAL_DIR, target_class)
    te_dir = os.path.join(TEST_DIR, target_class)

    t_count = len([f for f in os.listdir(t_dir) if os.path.isfile(os.path.join(t_dir, f))]) if os.path.exists(t_dir) else 0
    v_count = len([f for f in os.listdir(v_dir) if os.path.isfile(os.path.join(v_dir, f))]) if os.path.exists(v_dir) else 0
    te_count = len([f for f in os.listdir(te_dir) if os.path.isfile(os.path.join(te_dir, f))]) if os.path.exists(te_dir) else 0
    return t_count, v_count, te_count


def count_backup(target_class: str) -> int:
    backup_dir = os.path.join(BACKUP_DIR, target_class)
    if not os.path.exists(backup_dir):
        return 0
    return len([f for f in os.listdir(backup_dir) if os.path.isfile(os.path.join(backup_dir, f)) and Path(f).suffix.lower() in IMG_EXTS])


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


def load_existing_hashes(target_class: str) -> set:
    hashes = set()
    for dir_path in [TRAIN_DIR, VAL_DIR, TEST_DIR, BACKUP_DIR]:
        class_dir = os.path.join(dir_path, target_class)
        if not os.path.exists(class_dir):
            continue
        for fname in os.listdir(class_dir):
            fpath = os.path.join(class_dir, fname)
            if os.path.isfile(fpath) and Path(fname).suffix.lower() in IMG_EXTS:
                h = get_image_hash(fpath)
                if h:
                    hashes.add(h)
    return hashes


def validate_image(img_path: str, existing_hashes: set) -> tuple:
    if os.path.getsize(img_path) < MIN_FILE_SIZE:
        return False, "文件过小"

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


def count_images_in_dir(d: str) -> int:
    if not os.path.exists(d):
        return 0
    return len([f for f in os.listdir(d) if Path(f).suffix.lower() in IMG_EXTS])


def download_from_bing(query: str, output_dir: str, limit: int = 220):
    try:
        from bing_image_downloader import downloader
    except ImportError:
        print("    ⚠️ bing-image-downloader 未安装，跳过 Bing 下载")
        return 0

    folder_name = clean_folder_name(query)
    query_dir = os.path.join(output_dir, folder_name)
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
            print(f"    ✅ Bing 成功下载 {downloaded} 张（共 {after} 张）")
        else:
            print(f"    ℹ️ Bing 未获取新图片（共 {after} 张）")
        return downloaded
    except Exception as e:
        print(f"    ⚠️ Bing 下载出错: {e}")
        return 0


def collect_temp_images(src_dir: str):
    images = []
    for root, _, files in os.walk(src_dir):
        for f in files:
            if Path(f).suffix.lower() in IMG_EXTS:
                images.append(os.path.join(root, f))
    return images


def distribute_images_to_backup(src_dir: str, target_class: str):
    images = collect_temp_images(src_dir)
    if not images:
        print("  ⚠️ 没有找到图片")
        return

    backup_exist = count_backup(target_class)
    backup_gap = BACKUP_PER_CLASS - backup_exist
    if backup_gap <= 0:
        print(f"  ✅ {target_class} 备用库已满")
        return

    existing_hashes = load_existing_hashes(target_class)
    print(f"  📊 正式库: {sum(count_existing(target_class))}/{TARGET_PER_CLASS} 张，备用库: {backup_exist}/{BACKUP_PER_CLASS} 张")
    print(f"  📊 待筛选: {len(images)} 张")

    valid_images = []
    rejected_stats = {"尺寸过小": 0, "宽高比过大": 0, "重复图片": 0, "文件名过滤": 0, "文件过小": 0, "其他": 0}

    for img_path in images:
        is_valid, result = validate_image(img_path, existing_hashes)
        if is_valid:
            valid_images.append(img_path)
            existing_hashes.add(result)
        else:
            if "尺寸过小" in result:
                rejected_stats["尺寸过小"] += 1
            elif "宽高比" in result:
                rejected_stats["宽高比过大"] += 1
            elif "重复" in result:
                rejected_stats["重复图片"] += 1
            elif "排除词" in result:
                rejected_stats["文件名过滤"] += 1
            elif "文件过小" in result:
                rejected_stats["文件过小"] += 1
            else:
                rejected_stats["其他"] += 1

    print(f"  ✅ 通过验证: {len(valid_images)} 张")
    if sum(rejected_stats.values()) > 0:
        print(f"  ❌ 被拒绝: {rejected_stats}")

    random.shuffle(valid_images)
    to_backup = valid_images[:backup_gap]
    backup_added = 0

    for i, src_path in enumerate(to_backup):
        try:
            img = Image.open(src_path).convert("RGB")
            dst_dir = os.path.join(BACKUP_DIR, target_class)
            idx = backup_exist + i
            dst_path = os.path.join(dst_dir, f"crawl_{target_class}_{idx:05d}.jpg")
            img.save(dst_path, "JPEG", quality=90)
            backup_added += 1
        except Exception as e:
            print(f"    ⚠️ 备用库保存失败: {e}")

    print(f"  📦 备用库: 新增 {backup_added} 张")
    print(f"  📈 {target_class} 当前备用总数: {count_backup(target_class)} 张")


def download_for_class(target_class: str):
    backup_exist = count_backup(target_class)
    formal_exist = sum(count_existing(target_class))
    if backup_exist >= BACKUP_PER_CLASS:
        print(f"✅ {target_class} 备用库已满 ({backup_exist}/{BACKUP_PER_CLASS})")
        return

    print(f"\n{'=' * 60}")
    print(f"📥 开始爬取 {target_class}")
    print(f"   正式库: {formal_exist}/{TARGET_PER_CLASS} 张")
    print(f"   备用库: {backup_exist}/{BACKUP_PER_CLASS} 张")
    print(f"{'=' * 60}")

    temp_class_dir = os.path.join(TEMP_DIR, target_class)
    os.makedirs(temp_class_dir, exist_ok=True)

    queries = SEARCH_QUERIES.get(target_class, [target_class])
    per_query = 260
    total_downloaded = 0

    for query in queries:
        print(f"  🔍 搜索: {query}")
        downloaded = download_from_bing(query, temp_class_dir, limit=per_query)
        total_downloaded += downloaded

        count = len(list(Path(temp_class_dir).rglob("*.*")))
        print(f"    📁 临时目录累计图片: {count} 张")
        if count >= max(600, BACKUP_PER_CLASS - backup_exist):
            print("  ✅ 临时目录已达到本轮足够数量，停止追加搜索")
            break

    print(f"\n  📊 本次累计成功下载: {total_downloaded} 张")
    distribute_images_to_backup(temp_class_dir, target_class)

    try:
        shutil.rmtree(temp_class_dir)
    except Exception:
        pass

    print(f"  📈 {target_class} 最终备用数: {count_backup(target_class)} 张")


def show_status():
    print("\n" + "=" * 75)
    print("数据集状态")
    print("=" * 75)
    print(f"{'类别':<15} {'Train':>8} {'Val':>8} {'Test':>8} {'正式库':>8} {'备用库':>8} {'状态':>12}")
    print("-" * 75)

    all_cats = ["charger", "card", "keys", "accessory", "bag", "book", "bottle",
                "clothes", "glasses", "headphones", "laptop", "mobile_device",
                "stationery", "umbrella"]

    for cat in all_cats:
        t, v, te = count_existing(cat)
        total = t + v + te
        if cat in ["charger", "card", "keys"]:
            backup_count = count_backup(cat)
            if backup_count >= BACKUP_PER_CLASS:
                status = "✅ 备用达标"
            elif backup_count > 0:
                status = f"⚠️ 缺{BACKUP_PER_CLASS - backup_count}"
            else:
                status = "❌ 无备用"
            print(f"{cat:<15} {t:>8} {v:>8} {te:>8} {total:>8} {backup_count:>8}   {status}")
        else:
            status = "✅" if total > 0 else "--"
            print(f"{cat:<15} {t:>8} {v:>8} {te:>8} {total:>8} {'-':>8}   {status}")
    print("-" * 75)
    print("注：本脚本只补 backup，正式集由 check_dataset.py 分发")


def main():
    print("=" * 75)
    print("校园失物招领系统 - 增强版数据爬取工具（backup 版）")
    print("针对 charger/card/keys 三类难以获取的数据集")
    print("正式库：训练500 / 验证100 / 测试50（共650张）")
    print("备用库：每类最多2000张")
    print("=" * 75)

    show_status()
    for cat in ["charger", "card", "keys"]:
        if count_backup(cat) < BACKUP_PER_CLASS:
            download_for_class(cat)

    print("\n" + "=" * 75)
    print("最终数据集状态")
    print("=" * 75)
    show_status()
    print("\n✅ 爬取完成！")
    print("之后运行 check_dataset.py 从 backup 分配正式数据集")


if __name__ == "__main__":
    main()
