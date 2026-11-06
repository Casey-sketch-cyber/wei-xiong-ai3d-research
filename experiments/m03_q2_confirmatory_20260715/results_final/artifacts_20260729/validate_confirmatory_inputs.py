from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    return parser.parse_args()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def array_sha256(array: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def main() -> int:
    args = parse_args()
    with args.manifest.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    errors: list[str] = []
    split_counts = Counter(row["split"] for row in rows)
    expected_counts = {"main": 720, "view": 180, "severity": 180}
    if dict(split_counts) != expected_counts:
        errors.append(f"split counts {dict(split_counts)} != {expected_counts}")

    identities = [
        (row["object_id"], row["split"], row["view_id"], row["style"], row["severity"])
        for row in rows
    ]
    if len(identities) != len(set(identities)):
        errors.append("duplicate manifest identities")

    image_cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    file_hash_cache: dict[str, str] = {}
    alpha_hashes: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    main_alpha: dict[str, str] = {}
    edge_high_dark_fractions: list[float] = []
    for index, row in enumerate(rows, start=1):
        path = Path(row["input_path"])
        gt_path = Path(row["gt_view_path"])
        if not path.is_file() or not gt_path.is_file():
            errors.append(f"missing file at row {index}")
            continue
        input_key = str(path)
        gt_key = str(gt_path)
        if input_key not in file_hash_cache:
            file_hash_cache[input_key] = file_sha256(path)
        if gt_key not in file_hash_cache:
            file_hash_cache[gt_key] = file_sha256(gt_path)
        if file_hash_cache[input_key] != row["input_sha256"]:
            errors.append(f"input hash mismatch at row {index}")
        if file_hash_cache[gt_key] != row["gt_view_sha256"]:
            errors.append(f"GT hash mismatch at row {index}")

        cache_key = str(path)
        if cache_key not in image_cache:
            rgba = np.asarray(Image.open(path).convert("RGBA"))
            image_cache[cache_key] = (rgba[:, :, :3], rgba[:, :, 3])
        rgb, alpha = image_cache[cache_key]
        foreground = alpha > 0
        if not np.any(foreground):
            errors.append(f"empty alpha at row {index}")
            continue
        if not np.all(rgb[~foreground] == 255):
            errors.append(f"non-white RGB outside alpha at row {index}")
        ys, xs = np.nonzero(foreground)
        bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
        if bbox != json.loads(row["alpha_bbox"]):
            errors.append(f"bbox mismatch at row {index}")
        observed_fraction = float(np.mean(foreground))
        if abs(observed_fraction - float(row["foreground_fraction"])) > 1e-12:
            errors.append(f"foreground fraction mismatch at row {index}")

        alpha_hash = array_sha256(alpha)
        group = (row["object_id"], row["split"], row["view_id"])
        alpha_hashes[group].add(alpha_hash)
        if row["split"] == "main":
            main_alpha[row["object_id"]] = alpha_hash
        if row["split"] == "severity" and row["view_id"] == "canonical":
            if main_alpha.get(row["object_id"]) != alpha_hash:
                errors.append(f"severity alpha differs from main for {row['object_id']}")
        if row["split"] == "severity" and row["style"] == "edge" and row["severity"] == "high":
            grayscale = np.mean(rgb, axis=2)
            dark_fraction = float(np.mean(grayscale[foreground] < 128))
            edge_high_dark_fractions.append(dark_fraction)
            if not (0.001 <= dark_fraction <= 0.25):
                errors.append(
                    f"edge-high dark fraction out of range for {row['object_id']}: {dark_fraction}"
                )

    inconsistent_alpha_groups = {
        "|".join(key): len(values) for key, values in alpha_hashes.items() if len(values) != 1
    }
    if inconsistent_alpha_groups:
        errors.append(f"inconsistent alpha groups: {inconsistent_alpha_groups}")

    report = {
        "status": "pass" if not errors else "fail",
        "manifest": str(args.manifest),
        "manifest_sha256": file_sha256(args.manifest),
        "rows": len(rows),
        "unique_image_files": len(image_cache),
        "split_counts": dict(split_counts),
        "main_objects": len({row["object_id"] for row in rows if row["split"] == "main"}),
        "view_objects": len({row["object_id"] for row in rows if row["split"] == "view"}),
        "severity_objects": len(
            {row["object_id"] for row in rows if row["split"] == "severity"}
        ),
        "alpha_groups": len(alpha_hashes),
        "edge_high_dark_fraction_min": min(edge_high_dark_fractions, default=None),
        "edge_high_dark_fraction_median": float(np.median(edge_high_dark_fractions))
        if edge_high_dark_fractions
        else None,
        "edge_high_dark_fraction_max": max(edge_high_dark_fractions, default=None),
        "errors": errors,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.report.with_suffix(args.report.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, args.report)
    print("INPUT_VALIDATION", json.dumps(report, ensure_ascii=False), flush=True)
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
