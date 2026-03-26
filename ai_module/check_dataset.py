#!/usr/bin/env python3
"""
数据集状态检查脚本
查看各类别图片数量、分布情况（训练500/验证100/测试50）
包含正式库和备用库统计
"""

import os
from pathlib import Path
from collections import defaultdict

# 配置
DATASET_DIR = Path(__file__).parent / "datasets"
CLASSIFICATION_DIR = DATASET_DIR / "classification"
BACKUP_DIR = CLASSIFICATION_DIR / "backup"  # 备用库目录
TARGET_PER_CLASS = 650  # 正式库目标
BACKUP_TARGET = 350      # 备用库目标
TRAIN_TARGET = 500
VAL_TARGET = 100
TEST_TARGET = 50

# 系统类别
SYSTEM_CATEGORIES = [
    "mobile_device", "laptop", "headphones", "charger", "bag",
    "book", "stationery", "card", "keys", "glasses",
    "accessory", "bottle", "umbrella", "clothes"
]

# 需要爬取的类别（有备用库）
CRAWL_CATEGORIES = ["charger", "card", "keys"]


def count_images(directory: Path) -> int:
    """统计目录中的图片数量"""
    if not directory.exists():
        return 0
    exts = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.bmp', '*.webp']
    count = 0
    for ext in exts:
        count += len(list(directory.glob(ext)))
        count += len(list(directory.glob(ext.upper())))
    return count


def check_dataset():
    """检查数据集状态（包含备用库）"""
    print("=" * 80)
    print("📊 数据集状态检查")
    print("   正式库目标: 训练500 / 验证100 / 测试50（共650张）")
    print("   备用库目标: 每类350张")
    print("=" * 80)
    
    total_train = 0
    total_val = 0
    total_test = 0
    total_backup = 0
    
    # 各类别汇总表
    print("\n📋 各类别汇总:")
    print("-" * 80)
    print(f"  {'类别':<15} {'训练':>6} {'验证':>6} {'测试':>6} {'正式库':>8} {'备用库':>8} {'状态':>12}")
    print("-" * 80)
    
    all_complete = True
    for category in SYSTEM_CATEGORIES:
        train_count = count_images(CLASSIFICATION_DIR / "train" / category)
        val_count = count_images(CLASSIFICATION_DIR / "val" / category)
        test_count = count_images(CLASSIFICATION_DIR / "test" / category)
        main_total = train_count + val_count + test_count
        
        total_train += train_count
        total_val += val_count
        total_test += test_count
        
        # 检查备用库
        backup_count = 0
        if category in CRAWL_CATEGORIES:
            backup_count = count_images(BACKUP_DIR / category)
            total_backup += backup_count
        
        # 检查是否达标
        train_ok = train_count >= TRAIN_TARGET * 0.9
        val_ok = val_count >= VAL_TARGET * 0.8
        test_ok = test_count >= TEST_TARGET * 0.8
        main_ok = train_ok and val_ok and test_ok
        
        if category in CRAWL_CATEGORIES:
            backup_ok = backup_count >= BACKUP_TARGET * 0.8
            if main_ok and backup_ok:
                status = "✅ 完整"
            elif main_ok:
                status = f"📦 缺备用{BACKUP_TARGET - backup_count}"
                all_complete = False
            elif main_total > 0:
                status = f"⏳ 缺正式{TARGET_PER_CLASS - main_total}"
                all_complete = False
            else:
                status = "❌ 缺失"
                all_complete = False
            print(f"  {category:<15} {train_count:>6} {val_count:>6} {test_count:>6} {main_total:>8} {backup_count:>8} {status:>12}")
        else:
            if main_ok:
                status = "✅ 达标"
            elif main_total > 0:
                status = "⏳ 不足"
                all_complete = False
            else:
                status = "❌ 缺失"
                all_complete = False
            print(f"  {category:<15} {train_count:>6} {val_count:>6} {test_count:>6} {main_total:>8} {'-':>8} {status:>12}")
    
    print("-" * 80)
    
    # 汇总统计
    print("\n📈 汇总统计:")
    print("-" * 40)
    print(f"  Train 集:  {total_train:>6} 张 (目标 {TRAIN_TARGET * len(SYSTEM_CATEGORIES)})")
    print(f"  Val 集:    {total_val:>6} 张 (目标 {VAL_TARGET * len(SYSTEM_CATEGORIES)})")
    print(f"  Test 集:   {total_test:>6} 张 (目标 {TEST_TARGET * len(SYSTEM_CATEGORIES)})")
    print(f"  正式库总计: {total_train + total_val + total_test:>6} 张")
    print(f"  备用库总计: {total_backup:>6} 张")
    print("-" * 40)
    
    if all_complete:
        print("\n🎉 所有类别已达到目标数量！可以开始训练了。")
        print(f"\n运行训练命令:")
        print(f"  conda activate efftrain")
        print(f"  python ai_module/train.py")
    else:
        print("\n⚠️ 部分类别图片数量不足，建议继续下载。")
        print(f"\n下载 OpenImages 数据:")
        print(f"  conda activate opim")
        print(f"  python ai_module/download_openimages.py")
        print(f"\n爬取缺失类别 (charger/card/keys):")
        print(f"  python ai_module/download_kaggle.py")
    
    print("=" * 80)


if __name__ == "__main__":
    check_dataset()
