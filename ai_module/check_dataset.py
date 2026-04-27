#!/usr/bin/env python3
"""
数据集状态检查与重分配脚本

支持两种模式：
1. 补充数据集：仅在 train / val / test 不足时，从 backup 随机复制补齐
2. 重新随机数据集：清空正式数据集后，从 backup 重新随机分配 500 / 100 / 50
"""

import random
import shutil
from pathlib import Path

# 配置
DATASET_DIR = Path(__file__).parent / "datasets"
CLASSIFICATION_DIR = DATASET_DIR / "classification"
BACKUP_DIR = CLASSIFICATION_DIR / "backup"
TARGET_PER_CLASS = 650
BACKUP_TARGET = 2000
TRAIN_TARGET = 500
VAL_TARGET = 100
TEST_TARGET = 50
RANDOM_SEED = 42

SYSTEM_CATEGORIES = [
    "mobile_device", "laptop", "headphones", "charger", "bag",
    "book", "stationery", "card", "keys", "glasses",
    "accessory", "bottle", "umbrella", "clothes"
]

IMG_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}


def count_images(directory: Path) -> int:
    if not directory.exists():
        return 0
    return len([p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXTS])


def list_images(directory: Path):
    if not directory.exists():
        return []
    return [p for p in directory.iterdir() if p.is_file() and p.suffix.lower() in IMG_EXTS]


def ensure_dirs():
    for split in ["train", "val", "test", "backup"]:
        for category in SYSTEM_CATEGORIES:
            (CLASSIFICATION_DIR / split / category).mkdir(parents=True, exist_ok=True)


def clear_formal_dataset():
    print("\n🧹 清空正式数据集（train / val / test）...")
    print("-" * 80)
    removed = 0
    for category in SYSTEM_CATEGORIES:
        for split in ["train", "val", "test"]:
            split_dir = CLASSIFICATION_DIR / split / category
            for src in list_images(split_dir):
                try:
                    src.unlink()
                    removed += 1
                except Exception:
                    continue
    print(f"  已清空 {removed} 张正式数据集图片")
    print("-" * 80)


def available_backup_candidates(category: str):
    return list_images(BACKUP_DIR / category)


def copy_random_to_split(category: str, split: str, need_count: int):
    if need_count <= 0:
        return 0

    target_dir = CLASSIFICATION_DIR / split / category
    target_dir.mkdir(parents=True, exist_ok=True)
    current_count = count_images(target_dir)
    candidates = available_backup_candidates(category)
    if not candidates:
        return 0

    random.shuffle(candidates)
    copied = 0
    for src in candidates:
        if copied >= need_count:
            break
        dst = target_dir / f"autofill_{category}_{current_count + copied:05d}{src.suffix.lower()}"
        try:
            shutil.copy2(src, dst)
            copied += 1
        except Exception:
            continue
    return copied


def autofill_from_backup():
    print("\n🔧 开始自动从 backup 补充不足项...")
    print("-" * 80)
    fill_stats = {}
    for category in SYSTEM_CATEGORIES:
        t_count = count_images(CLASSIFICATION_DIR / "train" / category)
        v_count = count_images(CLASSIFICATION_DIR / "val" / category)
        te_count = count_images(CLASSIFICATION_DIR / "test" / category)

        need_train = max(0, TRAIN_TARGET - t_count)
        need_val = max(0, VAL_TARGET - v_count)
        need_test = max(0, TEST_TARGET - te_count)

        filled_train = copy_random_to_split(category, "train", need_train)
        filled_val = copy_random_to_split(category, "val", need_val)
        filled_test = copy_random_to_split(category, "test", need_test)

        fill_stats[category] = {"train": filled_train, "val": filled_val, "test": filled_test}
        if filled_train or filled_val or filled_test:
            print(f"  {category:<15} 补齐 train={filled_train:>3} val={filled_val:>3} test={filled_test:>3}")
    if not any(sum(v.values()) > 0 for v in fill_stats.values()):
        print("  无需补齐，或 backup 不足。")
    print("-" * 80)
    return fill_stats


def rebuild_from_backup():
    print("\n🎲 开始从 backup 重新随机生成正式数据集...")
    print("-" * 80)
    clear_formal_dataset()
    fill_stats = {}
    for category in SYSTEM_CATEGORIES:
        filled_train = copy_random_to_split(category, "train", TRAIN_TARGET)
        filled_val = copy_random_to_split(category, "val", VAL_TARGET)
        filled_test = copy_random_to_split(category, "test", TEST_TARGET)
        fill_stats[category] = {"train": filled_train, "val": filled_val, "test": filled_test}
        print(f"  {category:<15} 重建 train={filled_train:>3} val={filled_val:>3} test={filled_test:>3}")
    print("-" * 80)
    return fill_stats


def print_status():
    total_train = 0
    total_val = 0
    total_test = 0
    total_backup = 0
    all_complete = True

    print("=" * 90)
    print("📊 数据集状态检查")
    print(f"   正式库目标: 训练{TRAIN_TARGET} / 验证{VAL_TARGET} / 测试{TEST_TARGET}（共{TARGET_PER_CLASS}张）")
    print(f"   备用库目标: 每类{BACKUP_TARGET}张")
    print("=" * 90)

    print("\n📋 各类别汇总:")
    print("-" * 90)
    print(f"  {'类别':<15} {'训练':>6} {'验证':>6} {'测试':>6} {'正式库':>8} {'备用库':>8} {'状态':>14}")
    print("-" * 90)

    for category in SYSTEM_CATEGORIES:
        train_count = count_images(CLASSIFICATION_DIR / "train" / category)
        val_count = count_images(CLASSIFICATION_DIR / "val" / category)
        test_count = count_images(CLASSIFICATION_DIR / "test" / category)
        main_total = train_count + val_count + test_count
        backup_count = count_images(BACKUP_DIR / category)

        total_train += train_count
        total_val += val_count
        total_test += test_count
        total_backup += backup_count

        train_ok = train_count >= TRAIN_TARGET
        val_ok = val_count >= VAL_TARGET
        test_ok = test_count >= TEST_TARGET
        main_ok = train_ok and val_ok and test_ok

        if main_ok:
            status = "✅ 达标"
        elif main_total > 0:
            status = "⚠️ 不足"
            all_complete = False
        else:
            status = "❌ 缺失"
            all_complete = False

        print(f"  {category:<15} {train_count:>6} {val_count:>6} {test_count:>6} {main_total:>8} {backup_count:>8} {status:>14}")

    print("-" * 90)
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
    else:
        print("\n⚠️ 部分类别图片数量仍不足，可继续补充 backup 或重新随机生成。")
    print("=" * 90)


def choose_mode():
    print("\n请选择操作模式：")
    print("  1. 补充数据集：检测不足时，从 backup 随机复制补齐")
    print("  2. 重新随机数据集：清空正式数据集后，从 backup 重新分配")
    print("  3. 仅检查状态，不做修改")
    choice = input("\n请输入选项 (1/2/3): ").strip()
    return choice


def main():
    ensure_dirs()
    random.seed(RANDOM_SEED)
    choice = choose_mode()

    if choice == "1":
        autofill_from_backup()
    elif choice == "2":
        rebuild_from_backup()
    elif choice == "3":
        pass
    else:
        print("无效选项，默认仅检查状态。")

    print_status()


if __name__ == "__main__":
    main()
