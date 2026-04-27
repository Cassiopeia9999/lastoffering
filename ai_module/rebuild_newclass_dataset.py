#!/usr/bin/env python3
"""
Rebuild and screen a new classification dataset.

Pipeline:
1. Merge train/val/test/backup into datasets/classification/newclass/raw/<class>
2. Run model-based screening for all images in raw:
   - label consistency (top1 / top3)
   - low gt probability
   - class outlier (feature-to-centroid cosine similarity)
   - extra heuristic for keys-like noisy samples
3. Split results into:
   - newclass/clean/<class>
   - newclass/suspect/<class>
4. Export report files under newclass/reports

Run (recommended in efftrain):
  conda activate efftrain
  python ai_module/rebuild_newclass_dataset.py --model-version V2
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from PIL import Image


IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


@dataclass
class ImageRecord:
    cls: str
    path: Path
    top1: str
    top1_prob: float
    top3: List[Tuple[str, float]]
    gt_prob: float
    sim_to_center: float
    sim_threshold: float
    reason_codes: List[str]


def is_image_file(path: Path) -> bool:
    return path.suffix.lower() in IMG_EXTS


def read_classes(root: Path) -> List[str]:
    classes_txt = root / "classes.txt"
    if classes_txt.exists():
        classes = []
        for line in classes_txt.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                classes.append(parts[1])
        if classes:
            return classes

    # fallback: infer from train folder
    train_dir = root / "train"
    return sorted([p.name for p in train_dir.iterdir() if p.is_dir()]) if train_dir.exists() else []


def sha1_of_file(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_image(path: Path) -> bool:
    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except Exception:
        return False


def gather_sources(root: Path, cls: str) -> List[Path]:
    srcs: List[Path] = []
    for split in ("train", "val", "test"):
        d = root / split / cls
        if d.exists():
            srcs.extend([p for p in d.iterdir() if p.is_file() and is_image_file(p)])
    backup_d = root / "backup" / cls
    if backup_d.exists():
        srcs.extend([p for p in backup_d.iterdir() if p.is_file() and is_image_file(p)])
    return srcs


def rebuild_raw_dataset(root: Path, classes: List[str]) -> Dict[str, int]:
    newclass = root / "newclass"
    raw_dir = newclass / "raw"
    reports = newclass / "reports"
    raw_dir.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    copied_stats: Dict[str, int] = {}
    global_hashes: set[str] = set()

    for cls in classes:
        target = raw_dir / cls
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True, exist_ok=True)

        copied = 0
        skipped_bad = 0
        skipped_dup = 0
        for src in gather_sources(root, cls):
            if not verify_image(src):
                skipped_bad += 1
                continue
            digest = sha1_of_file(src)
            if digest in global_hashes:
                skipped_dup += 1
                continue
            global_hashes.add(digest)

            dst = target / f"{digest}{src.suffix.lower()}"
            shutil.copy2(src, dst)
            copied += 1

        copied_stats[cls] = copied
        print(f"[raw] {cls:<14} copied={copied:4d} bad={skipped_bad:3d} dup={skipped_dup:4d}")

    (reports / "raw_stats.json").write_text(
        json.dumps(copied_stats, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return copied_stats


def screen_dataset(
    root: Path,
    classes: List[str],
    model_version: str,
    min_gt_prob: float,
    outlier_quantile: float,
) -> Dict[str, Dict[str, int]]:
    # local import to keep script importable without torch in base env
    from predict import LostItemAI  # pylint: disable=import-outside-toplevel

    newclass = root / "newclass"
    raw_dir = newclass / "raw"
    clean_dir = newclass / "clean"
    suspect_dir = newclass / "suspect"
    reports = newclass / "reports"
    clean_dir.mkdir(parents=True, exist_ok=True)
    suspect_dir.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    ai = LostItemAI(version=model_version)
    if ai.model is None and not ai.prototype_mode:
        raise RuntimeError(f"Model load failed: {model_version}")

    print(f"[screen] model={ai.version}, prototype_mode={ai.prototype_mode}, device={ai.device}")

    per_class_rows: Dict[str, List[dict]] = {c: [] for c in classes}
    per_class_feats: Dict[str, List[np.ndarray]] = {c: [] for c in classes}
    per_class_files: Dict[str, List[Path]] = {c: [] for c in classes}

    # phase-1: topk and feature extraction
    for cls in classes:
        cls_raw = raw_dir / cls
        if not cls_raw.exists():
            continue
        images = sorted([p for p in cls_raw.iterdir() if p.is_file() and is_image_file(p)])
        for p in images:
            top3 = ai.predict_topk(str(p), k=3)
            if not top3:
                continue
            top1, top1_prob = top3[0]
            gt_prob = 0.0
            for lbl, pr in top3:
                if lbl == cls:
                    gt_prob = float(pr)
                    break
            feat = ai.extract_features(str(p))
            if feat is None:
                continue
            per_class_feats[cls].append(feat.astype(np.float32))
            per_class_files[cls].append(p)
            per_class_rows[cls].append(
                {
                    "file": p,
                    "top1": top1,
                    "top1_prob": float(top1_prob),
                    "top3": top3,
                    "gt_prob": gt_prob,
                }
            )

    # phase-2: centroid and outlier
    records: List[ImageRecord] = []
    for cls in classes:
        rows = per_class_rows[cls]
        if not rows:
            continue
        feats = np.stack(per_class_feats[cls], axis=0)
        centroid = feats.mean(axis=0)
        centroid /= max(np.linalg.norm(centroid), 1e-12)
        sims = feats @ centroid
        threshold = float(np.quantile(sims, outlier_quantile))

        for i, row in enumerate(rows):
            reasons: List[str] = []
            top3_labels = [x[0] for x in row["top3"]]
            if row["top1"] != cls:
                reasons.append("top1_mismatch")
            if cls not in top3_labels:
                reasons.append("not_in_top3")
            if row["gt_prob"] < min_gt_prob:
                reasons.append("low_gt_prob")
            if float(sims[i]) < threshold:
                reasons.append("outlier")

            # extra noisy-keys heuristic
            if cls == "keys" and row["top1"] in {"laptop", "stationery", "mobile_device"} and row["top1_prob"] >= 0.6:
                reasons.append("keys_noise_possible")

            records.append(
                ImageRecord(
                    cls=cls,
                    path=row["file"],
                    top1=row["top1"],
                    top1_prob=row["top1_prob"],
                    top3=row["top3"],
                    gt_prob=row["gt_prob"],
                    sim_to_center=float(sims[i]),
                    sim_threshold=threshold,
                    reason_codes=reasons,
                )
            )

    # reset output dirs
    for cls in classes:
        cdir = clean_dir / cls
        sdir = suspect_dir / cls
        if cdir.exists():
            shutil.rmtree(cdir)
        if sdir.exists():
            shutil.rmtree(sdir)
        cdir.mkdir(parents=True, exist_ok=True)
        sdir.mkdir(parents=True, exist_ok=True)

    # write CSV + copy files
    csv_path = reports / "suspects.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "class",
                "filename",
                "top1",
                "top1_prob",
                "gt_prob",
                "sim_to_center",
                "sim_threshold",
                "reason_codes",
                "top3",
            ]
        )
        for rec in records:
            rel_name = rec.path.name
            is_suspect = len(rec.reason_codes) > 0
            dst_root = suspect_dir if is_suspect else clean_dir
            shutil.copy2(rec.path, dst_root / rec.cls / rel_name)

            writer.writerow(
                [
                    rec.cls,
                    rel_name,
                    rec.top1,
                    f"{rec.top1_prob:.4f}",
                    f"{rec.gt_prob:.4f}",
                    f"{rec.sim_to_center:.6f}",
                    f"{rec.sim_threshold:.6f}",
                    "|".join(rec.reason_codes),
                    json.dumps(rec.top3, ensure_ascii=False),
                ]
            )

    # summary
    summary: Dict[str, Dict[str, int]] = {}
    for cls in classes:
        clean_n = len(list((clean_dir / cls).glob("*")))
        suspect_n = len(list((suspect_dir / cls).glob("*")))
        summary[cls] = {"clean": clean_n, "suspect": suspect_n, "total": clean_n + suspect_n}
        print(f"[screen] {cls:<14} clean={clean_n:4d} suspect={suspect_n:4d} total={clean_n + suspect_n:4d}")

    (reports / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return summary


def main():
    parser = argparse.ArgumentParser(description="Rebuild and screen newclass dataset")
    parser.add_argument(
        "--root",
        type=str,
        default=str(Path(__file__).resolve().parent / "datasets" / "classification"),
        help="classification dataset root",
    )
    parser.add_argument("--model-version", type=str, default="V2", help="V0/V1/V2/latest")
    parser.add_argument("--min-gt-prob", type=float, default=0.20, help="flag low gt prob")
    parser.add_argument("--outlier-quantile", type=float, default=0.10, help="outlier quantile per class")
    parser.add_argument("--build-only", action="store_true", help="only rebuild raw dataset")
    args = parser.parse_args()

    root = Path(args.root)
    classes = read_classes(root)
    if not classes:
        raise RuntimeError(f"No classes found under {root}")

    print(f"[info] classes={len(classes)}: {classes}")
    rebuild_raw_dataset(root, classes)
    if args.build_only:
        print("[done] build-only finished.")
        return

    screen_dataset(
        root=root,
        classes=classes,
        model_version=args.model_version,
        min_gt_prob=args.min_gt_prob,
        outlier_quantile=args.outlier_quantile,
    )
    print("[done] rebuild + screening finished.")


if __name__ == "__main__":
    main()

