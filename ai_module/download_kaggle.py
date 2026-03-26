"""
校园失物招领系统 - 自动图片爬取脚本（带备用库版本）
用途：使用 bing-image-downloader 自动下载 charger / card / keys 类别图片
划分比例：训练集 500 / 验证集 100 / 测试集 50（共650张/类）
备用库：额外下载 350 张作为备用，存储在 backup 目录

优化内容：
  1. 并发下载提升速度
  2. 优化搜索词，添加排除词过滤
  3. 图片质量过滤（最小尺寸、宽高比）
  4. 基于内容哈希去重
  5. 建立备用图片库（1000张总下载，650张使用，350张备用）

运行方式：
  conda activate opim
  python ai_module/download_kaggle.py
"""

import os
import sys
import random
import shutil
import hashlib
import concurrent.futures
from pathlib import Path
from PIL import Image

# ==================== 路径配置 ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "datasets", "classification")
TRAIN_DIR = os.path.join(DATASET_DIR, "train")
VAL_DIR = os.path.join(DATASET_DIR, "val")
TEST_DIR = os.path.join(DATASET_DIR, "test")
TEMP_DIR = os.path.join(BASE_DIR, "datasets", "temp_crawled")
BACKUP_DIR = os.path.join(DATASET_DIR, "backup")  # 备用图片库（放在classification目录下）

# 目标数量配置
TARGET_PER_CLASS = 650       # 正式数据集每类数量
TRAIN_COUNT = 500
VAL_COUNT = 100
TEST_COUNT = 50

# 备用库配置
BACKUP_PER_CLASS = 350       # 每类备用图片数量
TOTAL_TARGET_PER_CLASS = TARGET_PER_CLASS + BACKUP_PER_CLASS  # 总计下载 1000 张

RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# 确保目录存在
for cat in ["charger", "card", "keys"]:
    os.makedirs(os.path.join(TRAIN_DIR, cat), exist_ok=True)
    os.makedirs(os.path.join(VAL_DIR, cat), exist_ok=True)
    os.makedirs(os.path.join(TEST_DIR, cat), exist_ok=True)
    os.makedirs(os.path.join(BACKUP_DIR, cat), exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# ==================== 搜索关键词配置 ====================
# 搜索词（不在代码中加引号，避免Windows文件名问题）
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

# ==================== 图片过滤配置 ====================
MIN_IMAGE_SIZE = 224  # 最小边长
MAX_ASPECT_RATIO = 3.0  # 最大宽高比
REJECTED_KEYWORDS = ["keyboard", "piano", "keycap", "button", "switch"]  # 文件名中排除的关键词


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


def validate_image(img_path: str, existing_hashes: set) -> bool:
    """
    验证图片是否符合要求
    返回: (是否通过, 失败原因)
    """
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
    # 替换Windows非法字符
    for char in '<>:"/\\|?*':
        cleaned = cleaned.replace(char, '_')
    return cleaned


def download_from_bing(query: str, output_dir: str, limit: int = 100):
    """
    使用 bing-image-downloader 下载图片
    使用清理后的文件夹名避免Windows文件名错误
    """
    from bing_image_downloader import downloader
    from pathlib import Path
    
    # 生成合法的文件夹名
    folder_name = clean_folder_name(query)
    query_dir = os.path.join(output_dir, folder_name)
    
    # 统计下载前的图片数
    def count_images_in_dir(d):
        if not os.path.exists(d):
            return 0
        return len([f for f in os.listdir(d) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))])
    
    before = count_images_in_dir(query_dir)
    
    try:
        # 使用自定义输出目录，避免bing_image_downloader用原始query创建文件夹
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
        
        # 如果下载器创建了原始query名称的文件夹，移动文件到清理后的文件夹
        raw_query_dir = os.path.join(output_dir, query)
        if os.path.exists(raw_query_dir) and raw_query_dir != query_dir:
            for fname in os.listdir(raw_query_dir):
                src = os.path.join(raw_query_dir, fname)
                dst = os.path.join(query_dir, fname)
                if os.path.isfile(src) and not os.path.exists(dst):
                    shutil.move(src, dst)
            # 删除空文件夹
            try:
                os.rmdir(raw_query_dir)
            except:
                pass
        
        # 统计下载后的图片数
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


def count_backup_images(target_class: str) -> int:
    """统计备用库已有图片数"""
    backup_class_dir = os.path.join(BACKUP_DIR, target_class)
    if not os.path.exists(backup_class_dir):
        return 0
    return len([f for f in os.listdir(backup_class_dir) 
                if os.path.isfile(os.path.join(backup_class_dir, f)) 
                and f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])


def distribute_images(src_dir: str, target_class: str):
    """
    将爬取的图片分配到 train/val/test 目录和备用库
    策略：先填满正式数据集（650张），剩余放入备用库（350张）
    """
    # 收集图片
    img_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}
    images = []
    for root, _, files in os.walk(src_dir):
        for f in files:
            if Path(f).suffix.lower() in img_extensions:
                images.append(os.path.join(root, f))
    
    if not images:
        print(f"  ⚠️ 没有找到图片")
        return
    
    # 计算正式数据集已有数量和缺口
    t_exist, v_exist, te_exist = count_existing(target_class)
    exist_total = t_exist + v_exist + te_exist
    main_gap = TARGET_PER_CLASS - exist_total
    
    # 计算备用库已有数量和缺口
    backup_exist = count_backup_images(target_class)
    backup_gap = BACKUP_PER_CLASS - backup_exist
    
    # 加载已有图片的哈希值（用于去重，包括正式库和备用库）
    existing_hashes = load_existing_hashes(target_class)
    # 也加载备用库的哈希值
    backup_dir = os.path.join(BACKUP_DIR, target_class)
    if os.path.exists(backup_dir):
        for fname in os.listdir(backup_dir):
            if fname.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                fpath = os.path.join(backup_dir, fname)
                h = get_image_hash(fpath)
                if h:
                    existing_hashes.add(h)
    
    print(f"  📊 正式库: {exist_total}/{TARGET_PER_CLASS} 张，备用库: {backup_exist}/{BACKUP_PER_CLASS} 张")
    print(f"  📊 待筛选: {len(images)} 张")
    
    # 验证并过滤图片
    valid_images = []
    rejected_stats = {"尺寸过小": 0, "宽高比过大": 0, "重复图片": 0, "文件名过滤": 0, "其他": 0}
    
    for img_path in images:
        is_valid, result = validate_image(img_path, existing_hashes)
        if is_valid:
            valid_images.append((img_path, result))  # result 是哈希值
            existing_hashes.add(result)  # 添加到已存在集合防止本次重复
        else:
            # 统计拒绝原因
            if "尺寸过小" in result:
                rejected_stats["尺寸过小"] += 1
            elif "宽高比" in result:
                rejected_stats["宽高比过大"] += 1
            elif "重复" in result:
                rejected_stats["重复图片"] += 1
            elif "排除词" in result:
                rejected_stats["文件名过滤"] += 1
            else:
                rejected_stats["其他"] += 1
    
    print(f"  ✅ 通过验证: {len(valid_images)} 张")
    if sum(rejected_stats.values()) > 0:
        print(f"  ❌ 被拒绝: {rejected_stats}")
    
    # 随机打乱
    random.shuffle(valid_images)
    
    # ========== 第一步：填充正式数据集 ==========
    to_main = valid_images[:max(0, main_gap)] if main_gap > 0 else []
    remaining = valid_images[max(0, main_gap):]
    
    # 计算各类别还需要多少
    need_train = max(0, TRAIN_COUNT - t_exist)
    need_val = max(0, VAL_COUNT - v_exist)
    need_test = max(0, TEST_COUNT - te_exist)
    
    # 按比例分配到 train/val/test
    t_added, v_added, te_added = 0, 0, 0
    
    for i, (src_path, _) in enumerate(to_main):
        try:
            img = Image.open(src_path).convert("RGB")
            
            # 决定分配到哪个集合
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
    
    if to_main:
        print(f"  ✅ 正式库: train {t_added} 张 + val {v_added} 张 + test {te_added} 张")
    
    # ========== 第二步：填充备用库 ==========
    to_backup = remaining[:max(0, backup_gap)] if backup_gap > 0 else []
    backup_added = 0
    
    for i, (src_path, _) in enumerate(to_backup):
        try:
            img = Image.open(src_path).convert("RGB")
            dst_dir = os.path.join(BACKUP_DIR, target_class)
            idx = backup_exist + i
            dst_path = os.path.join(dst_dir, f"backup_{target_class}_{idx:05d}.jpg")
            img.save(dst_path, "JPEG", quality=90)
            backup_added += 1
        except Exception as e:
            print(f"    ⚠️ 备用库保存失败: {e}")
    
    if backup_added > 0:
        print(f"  📦 备用库: 新增 {backup_added} 张")
    
    # 报告最终状态
    t_new, v_new, te_new = count_existing(target_class)
    backup_new = count_backup_images(target_class)
    print(f"  📈 {target_class} 总计: 正式库 {t_new + v_new + te_new} 张 + 备用库 {backup_new} 张")


def download_for_class(target_class: str):
    """
    为指定类别爬取并分配图片（包含备用库）
    总计目标：正式库 650 张 + 备用库 350 张 = 1000 张
    """
    t_exist, v_exist, te_exist = count_existing(target_class)
    exist_total = t_exist + v_exist + te_exist
    backup_exist = count_backup_images(target_class)
    total_exist = exist_total + backup_exist
    
    # 如果正式库和备用库都满了，跳过
    if exist_total >= TARGET_PER_CLASS and backup_exist >= BACKUP_PER_CLASS:
        print(f"✅ {target_class} 正式库({exist_total})和备用库({backup_exist})均已满")
        return
    
    # 计算还需要下载多少
    need_total = TOTAL_TARGET_PER_CLASS - total_exist
    if need_total <= 0:
        print(f"✅ {target_class} 已达总目标数量 ({total_exist}/{TOTAL_TARGET_PER_CLASS})")
        return
    
    print(f"\n{'='*60}")
    print(f"📥 开始爬取 {target_class}")
    print(f"   正式库: {exist_total}/{TARGET_PER_CLASS} 张")
    print(f"   备用库: {backup_exist}/{BACKUP_PER_CLASS} 张")
    print(f"   本次目标: 下载约 {need_total} 张")
    print(f"{'='*60}")
    
    # 创建临时目录
    temp_class_dir = os.path.join(TEMP_DIR, target_class)
    os.makedirs(temp_class_dir, exist_ok=True)
    
    queries = SEARCH_QUERIES.get(target_class, [target_class])
    per_query = 150  # 每个关键词下载数量（增加以获取更多备用图片）
    
    total_downloaded = 0
    for query in queries:
        print(f"  🔍 搜索: {query}")
        downloaded = download_from_bing(query, temp_class_dir, limit=per_query)
        total_downloaded += downloaded
        
        # 检查是否达到总目标
        count = len(list(Path(temp_class_dir).rglob("*.*")))
        
        if count >= need_total:
            print(f"  ✅ 已下载足够数量，停止爬取")
            break
    
    print(f"\n  📊 本次累计成功下载: {total_downloaded} 张")
    
    # 分配到正式库和备用库
    distribute_images(temp_class_dir, target_class)
    
    # 清理临时目录
    try:
        shutil.rmtree(temp_class_dir)
    except Exception:
        pass
    
    # 报告最新状态
    t_new, v_new, te_new = count_existing(target_class)
    backup_new = count_backup_images(target_class)
    print(f"  📈 {target_class} 最终状态:")
    print(f"      正式库: {t_new + v_new + te_new} 张 (train={t_new}, val={v_new}, test={te_new})")
    print(f"      备用库: {backup_new} 张")


def show_status():
    """显示所有类别的当前状态（包含备用库）"""
    print("\n" + "=" * 75)
    print("数据集状态")
    print("=" * 75)
    print(f"{'类别':<15} {'Train':>8} {'Val':>8} {'Test':>8} {'正式库':>8} {'备用库':>8} {'状态':>10}")
    print("-" * 75)
    
    crawl_cats = ["charger", "card", "keys"]  # 需要爬取的类别
    all_cats = ["charger", "card", "keys", "accessory", "bag", "book", "bottle", 
                "clothes", "glasses", "headphones", "laptop", "mobile_device", 
                "stationery", "umbrella"]
    
    for cat in all_cats:
        t, v, te = count_existing(cat)
        total = t + v + te
        
        if cat in crawl_cats:
            backup_count = count_backup_images(cat)
            if total >= TARGET_PER_CLASS:
                if backup_count >= BACKUP_PER_CLASS:
                    status = "✅ 完整"
                else:
                    status = f"📦 缺备用{BACKUP_PER_CLASS - backup_count}"
            elif total > 0:
                status = f"⚠️ 缺正式{TARGET_PER_CLASS - total}"
            else:
                status = "❌ 空"
            print(f"{cat:<15} {t:>8} {v:>8} {te:>8} {total:>8} {backup_count:>8}   {status}")
        else:
            status = "✅" if total > 0 else "--"
            print(f"{cat:<15} {t:>8} {v:>8} {te:>8} {total:>8} {'-':>8}   {status}")
    
    print("-" * 75)
    print("注：正式库=训练集+验证集+测试集（共650张），备用库=额外备用图片（共350张）")


def main():
    print("=" * 75)
    print("校园失物招领系统 - 自动图片爬取工具（带备用库）")
    print("使用 bing-image-downloader 爬取图片")
    print("正式库：训练500 / 验证100 / 测试50（共650张）")
    print("备用库：额外350张（用于人工筛选后补充）")
    print("=" * 75)
    
    show_status()
    
    # 下载缺失的类别（包括正式库和备用库）
    for cat in ["charger", "card", "keys"]:
        t, v, te = count_existing(cat)
        backup_count = count_backup_images(cat)
        total = t + v + te
        
        # 如果正式库未满 或 备用库未满，都进行下载
        if total < TARGET_PER_CLASS or backup_count < BACKUP_PER_CLASS:
            download_for_class(cat)
    
    print("\n" + "=" * 75)
    print("最终数据集状态")
    print("=" * 75)
    show_status()
    
    print("\n✅ 全部完成！")
    print("\n备用图片存储位置: ai_module/datasets/backup/")
    print("当正式数据集中有图片被删除时，可从备用库中补充")
    print("\n开始训练模型:")
    print("   conda activate efftrain")
    print("   python ai_module/train.py")


if __name__ == "__main__":
    main()
