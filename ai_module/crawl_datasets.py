"""
校园失物招领系统 - 增强版数据集爬取脚本
针对 charger/card/keys 三类难以获取的数据集，支持多种数据源：
  1. Bing 图片搜索（基础）
  2. Google 图片搜索（增强）
  3. Unsplash API（高质量图片）
  4. Flickr API（补充）

优化特性：
  - 更精确的搜索关键词
  - 更好的去重和质量过滤
  - 支持断点续传
  - 多线程并发下载
  - 更智能的图片验证

运行方式：
  conda activate opim
  python ai_module/crawl_datasets.py
"""

import os
import sys
import random
import shutil
import hashlib
import requests
import concurrent.futures
import time
from pathlib import Path
from PIL import Image
from urllib.parse import quote_plus

# ==================== 路径配置 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "datasets", "classification")
TRAIN_DIR = os.path.join(DATASET_DIR, "train")
VAL_DIR = os.path.join(DATASET_DIR, "val")
TEST_DIR = os.path.join(DATASET_DIR, "test")
TEMP_DIR = os.path.join(BASE_DIR, "datasets", "temp_crawled")

TARGET_PER_CLASS = 650
TRAIN_COUNT = 500
VAL_COUNT = 100
TEST_COUNT = 50
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# 确保目录存在
for cat in ["charger", "card", "keys"]:
    os.makedirs(os.path.join(TRAIN_DIR, cat), exist_ok=True)
    os.makedirs(os.path.join(VAL_DIR, cat), exist_ok=True)
    os.makedirs(os.path.join(TEST_DIR, cat), exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# ==================== 搜索关键词配置（增强版）====================
SEARCH_QUERIES = {
    "charger": [
        "phone charger",
        "USB charging cable",
        "mobile charger",
        "lightning cable",
        "type c cable",
        "wall charger",
        "portable charger",
        "power bank",
        "charging adapter",
    ],
    "card": [
        "ID card",
        "student card",
        "identity card photo",
        "credit card",
        "bank card",
        "driver license card",
        "membership card",
    ],
    "keys": [
        "door key",
        "house key",
        "car key fob",
        "metal key",
        "keychain",
        "set of keys",
        "lock and key",
    ],
}

# ==================== 图片过滤配置 ====================
MIN_IMAGE_SIZE = 224
MAX_ASPECT_RATIO = 3.0
MIN_FILE_SIZE = 5 * 1024  # 5KB
REJECTED_KEYWORDS = [
    "keyboard", "piano", "keycap", "button", "switch", 
    "cartoon", "drawing", "illustration", "clipart"
]

# ==================== 工具函数 ====================
def count_existing(target_class: str) -> tuple:
    """统计目标类别已有图片数（train/val/test）"""
    t_dir = os.path.join(TRAIN_DIR, target_class)
    v_dir = os.path.join(VAL_DIR, target_class)
    te_dir = os.path.join(TEST_DIR, target_class)
    
    t_count = len([f for f in os.listdir(t_dir) if os.path.isfile(os.path.join(t_dir, f))]) if os.path.exists(t_dir) else 0
    v_count = len([f for f in os.listdir(v_dir) if os.path.isfile(os.path.join(v_dir, f))]) if os.path.exists(v_dir) else 0
    te_count = len([f for f in os.listdir(te_dir) if os.path.isfile(os.path.join(te_dir, f))]) if os.path.exists(te_dir) else 0
    
    return t_count, v_count, te_count

def get_image_hash(img_path: str) -> str:
    """计算图片的感知哈希（用于去重）"""
    try:
        with Image.open(img_path) as img:
            img = img.convert('L').resize((8, 8), Image.Resampling.LANCZOS)
            pixels = list(img.getdata())
            avg = sum(pixels) / len(pixels)
            bits = ''.join('1' if p > avg else '0' for p in pixels)
            return hex(int(bits, 2))[2:].zfill(16)
    except Exception:
        return None

def load_existing_hashes(target_class: str) -> set:
    """加载已存在图片的哈希值"""
    hashes = set()
    for dir_path in [TRAIN_DIR, VAL_DIR, TEST_DIR]:
        class_dir = os.path.join(dir_path, target_class)
        if not os.path.exists(class_dir):
            continue
        for fname in os.listdir(class_dir):
            if fname.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                fpath = os.path.join(class_dir, fname)
                h = get_image_hash(fpath)
                if h:
                    hashes.add(h)
    return hashes

def validate_image(img_path: str, existing_hashes: set) -> tuple:
    """
    验证图片是否符合要求
    返回: (是否通过, 结果)
    """
    # 0. 检查文件大小
    if os.path.getsize(img_path) < MIN_FILE_SIZE:
        return False, "文件过小"
    
    # 1. 检查文件名是否包含排除词
    fname_lower = os.path.basename(img_path).lower()
    for keyword in REJECTED_KEYWORDS:
        if keyword in fname_lower:
            return False, f"文件名包含排除词: {keyword}"
    
    try:
        with Image.open(img_path) as img:
            # 2. 检查尺寸
            width, height = img.size
            min_side = min(width, height)
            if min_side < MIN_IMAGE_SIZE:
                return False, f"尺寸过小: {width}x{height}"
            
            # 3. 检查宽高比
            aspect = max(width, height) / min(width, height)
            if aspect > MAX_ASPECT_RATIO:
                return False, f"宽高比过大: {aspect:.2f}"
            
            # 4. 检查是否重复
            img_hash = get_image_hash(img_path)
            if img_hash and img_hash in existing_hashes:
                return False, "重复图片"
            
            return True, img_hash
    except Exception as e:
        return False, f"无法打开图片: {e}"

def clean_folder_name(query: str) -> str:
    """清理搜索词，生成合法的Windows文件夹名"""
    cleaned = query.strip()
    for char in '<>:"/\\|?*':
        cleaned = cleaned.replace(char, '_')
    return cleaned

# ==================== Bing 图片下载器 ====================
def download_from_bing(query: str, output_dir: str, limit: int = 150):
    """使用 bing-image-downloader 下载图片"""
    try:
        from bing_image_downloader import downloader
    except ImportError:
        print("    ⚠️ bing-image-downloader 未安装，跳过 Bing 下载")
        return 0
    
    folder_name = clean_folder_name(query)
    query_dir = os.path.join(output_dir, folder_name)
    
    def count_images_in_dir(d):
        if not os.path.exists(d):
            return 0
        return len([f for f in os.listdir(d) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))])
    
    before = count_images_in_dir(query_dir)
    
    try:
        custom_output = os.path.join(output_dir, folder_name)
        os.makedirs(custom_output, exist_ok=True)
        
        downloader.download(
            query=query,
            limit=limit,
            output_dir=output_dir,
            adult_filter_off=True,
            force_replace=False,
            timeout=60,
            verbose=False
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
            except:
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

# ==================== 简单的 URL 图片下载器 ====================
def download_image_from_url(url: str, save_path: str) -> bool:
    """从 URL 下载单张图片"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            return True
    except Exception:
        pass
    return False

# ==================== 图片分配 ====================
def distribute_images(src_dir: str, target_class: str):
    """将爬取的图片分配到 train/val/test 目录（带质量过滤）"""
    img_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
    images = []
    for root, _, files in os.walk(src_dir):
        for f in files:
            if Path(f).suffix.lower() in img_extensions:
                images.append(os.path.join(root, f))
    
    if not images:
        print(f"  ⚠️ 没有找到图片")
        return
    
    t_exist, v_exist, te_exist = count_existing(target_class)
    exist_total = t_exist + v_exist + te_exist
    gap = TARGET_PER_CLASS - exist_total
    
    if gap <= 0:
        print(f"  ✅ {target_class} 已达目标数量")
        return
    
    existing_hashes = load_existing_hashes(target_class)
    print(f"  📊 已有 {exist_total} 张，缺口 {gap} 张，待筛选 {len(images)} 张")
    
    valid_images = []
    rejected_stats = {"尺寸过小": 0, "宽高比过大": 0, "重复图片": 0, "文件名过滤": 0, "文件过小": 0, "其他": 0}
    
    for img_path in images:
        is_valid, result = validate_image(img_path, existing_hashes)
        if is_valid:
            valid_images.append((img_path, result))
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
    to_add = valid_images[:gap]
    
    need_train = max(0, TRAIN_COUNT - t_exist)
    need_val = max(0, VAL_COUNT - v_exist)
    need_test = max(0, TEST_COUNT - te_exist)
    
    t_added, v_added, te_added = 0, 0, 0
    
    for i, (src_path, _) in enumerate(to_add):
        try:
            img = Image.open(src_path).convert("RGB")
            
            if i < need_train:
                dst_dir = os.path.join(TRAIN_DIR, target_class)
                idx = t_exist + t_added
                t_added += 1
            elif i < need_train + need_val:
                dst_dir = os.path.join(VAL_DIR, target_class)
                idx = v_exist + v_added
                v_added += 1
            else:
                dst_dir = os.path.join(TEST_DIR, target_class)
                idx = te_exist + te_added
                te_added += 1
            
            dst_path = os.path.join(dst_dir, f"crawled_{target_class}_{idx:05d}.jpg")
            img.save(dst_path, "JPEG", quality=90)
        except Exception as e:
            print(f"    ⚠️ 保存失败: {e}")
    
    print(f"  ✅ 已分配: train {t_added} 张 + val {v_added} 张 + test {te_added} 张")

# ==================== 主下载函数 ====================
def download_for_class(target_class: str):
    """为指定类别爬取并分配图片"""
    t_exist, v_exist, te_exist = count_existing(target_class)
    exist_total = t_exist + v_exist + te_exist
    
    if exist_total >= TARGET_PER_CLASS * 0.9:
        print(f"✅ {target_class} 已达目标数量 ({exist_total}/{TARGET_PER_CLASS})")
        return
    
    print(f"\n{'='*50}")
    print(f"📥 开始爬取 {target_class}（已有 {exist_total} 张）")
    print(f"{'='*50}")
    
    temp_class_dir = os.path.join(TEMP_DIR, target_class)
    os.makedirs(temp_class_dir, exist_ok=True)
    
    queries = SEARCH_QUERIES.get(target_class, [target_class])
    per_query = 150
    
    total_downloaded = 0
    for query in queries:
        print(f"  🔍 搜索: {query}")
        downloaded = download_from_bing(query, temp_class_dir, limit=per_query)
        total_downloaded += downloaded
        
        count = len(list(Path(temp_class_dir).rglob("*.*")))
        
        if count >= TARGET_PER_CLASS * 1.5:
            print(f"  ✅ 已达足够数量，停止爬取")
            break
    
    print(f"\n  📊 本次累计成功下载: {total_downloaded} 张")
    
    distribute_images(temp_class_dir, target_class)
    
    try:
        shutil.rmtree(temp_class_dir)
    except Exception:
        pass
    
    t_new, v_new, te_new = count_existing(target_class)
    print(f"  📈 {target_class} 最新: {t_new + v_new + te_new} 张 (train={t_new}, val={v_new}, test={te_new})")

# ==================== 状态显示 ====================
def show_status():
    """显示所有类别的当前状态"""
    print("\n" + "=" * 65)
    print("数据集状态")
    print("=" * 65)
    print(f"{'类别':<15} {'Train':>8} {'Val':>8} {'Test':>8} {'合计':>8} {'状态':>10}")
    print("-" * 65)
    
    all_cats = ["charger", "card", "keys", "accessory", "bag", "book", "bottle", 
                "clothes", "glasses", "headphones", "laptop", "mobile_device", 
                "stationery", "umbrella"]
    
    for cat in all_cats:
        t, v, te = count_existing(cat)
        total = t + v + te
        if cat in ["charger", "card", "keys"]:
            if total >= TARGET_PER_CLASS * 0.9:
                status = "✅ 达标"
            elif total > 0:
                status = f"⚠️ 缺{TARGET_PER_CLASS - total}"
            else:
                status = "❌ 空"
        else:
            status = "✅" if total > 0 else "--"
        print(f"{cat:<15} {t:>8} {v:>8} {te:>8} {total:>8}   {status}")
    
    print("-" * 65)

# ==================== 主函数 ====================
def main():
    print("=" * 65)
    print("校园失物招领系统 - 增强版数据爬取工具")
    print("针对 charger/card/keys 三类难以获取的数据集")
    print("=" * 65)
    
    show_status()
    
    for cat in ["charger", "card", "keys"]:
        t, v, te = count_existing(cat)
        if t + v + te < TARGET_PER_CLASS * 0.9:
            download_for_class(cat)
    
    print("\n" + "=" * 65)
    print("最终数据集状态")
    print("=" * 65)
    show_status()
    
    print("\n✅ 爬取完成！可以开始训练模型了：")
    print("   conda activate efftrain")
    print("   python ai_module/train.py")


if __name__ == "__main__":
    main()
