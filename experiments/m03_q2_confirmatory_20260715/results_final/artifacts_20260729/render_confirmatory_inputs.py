from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parent))
import render_and_style_inputs_base as base


CANONICAL_ROTATION = np.array(
    [
        [0.8192, 0.0, 0.5736],
        [0.2962, 0.8563, -0.4234],
        [-0.4912, 0.5165, 0.7010],
    ],
    dtype=np.float64,
)
MAIN_STYLES = ("photo", "edge", "flat", "low_detail", "sketch", "watercolor")
VIEW_STYLES = ("photo", "edge", "sketch")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", type=int, default=512)
    parser.add_argument("--seed", type=int, default=20260715)
    parser.add_argument("--robustness-count", type=int, default=30)
    parser.add_argument("--limit", type=int, default=0)
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else None
    return parser.parse_args(argv)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(4 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, payload: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(temporary, path)


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def rotation_y(degrees: float) -> np.ndarray:
    angle = math.radians(degrees)
    cosine, sine = math.cos(angle), math.sin(angle)
    return np.array(
        [[cosine, 0.0, sine], [0.0, 1.0, 0.0], [-sine, 0.0, cosine]],
        dtype=np.float64,
    )


def alpha_stats(path: Path) -> tuple[list[int], float]:
    alpha = np.asarray(Image.open(path).convert("RGBA").getchannel("A"))
    ys, xs = np.nonzero(alpha > 0)
    if len(xs) == 0:
        raise ValueError(f"Empty alpha mask: {path}")
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    return bbox, float(np.mean(alpha > 0))


def add_record(
    records: list[dict[str, object]],
    row: dict[str, str],
    split: str,
    view_id: str,
    style: str,
    severity: str,
    input_path: Path,
    gt_path: Path,
) -> None:
    bbox, foreground_fraction = alpha_stats(input_path)
    records.append(
        {
            "object_id": row["object_id"],
            "object_name": row["object_name"],
            "split": split,
            "view_id": view_id,
            "style": style,
            "severity": severity,
            "input_path": str(input_path),
            "input_sha256": file_sha256(input_path),
            "gt_view_path": str(gt_path),
            "gt_view_sha256": file_sha256(gt_path),
            "alpha_bbox": json.dumps(bbox),
            "foreground_fraction": foreground_fraction,
        }
    )


def render_view(
    row: dict[str, str],
    output: Path,
    rotation: np.ndarray,
    styles: tuple[str, ...],
    size: int,
    seed: int,
) -> tuple[dict[str, Path], Path]:
    base.VIEW_ROTATION = rotation.copy()
    raw_photo = output / "photo_render.png"
    if not raw_photo.exists() or raw_photo.stat().st_size == 0:
        base.render_photo(Path(row["input_mesh_path"]), raw_photo, size)
    photo = Image.open(raw_photo).convert("RGBA")
    rgb, alpha = base.rgba_on_white(photo)
    makers = {
        "photo": lambda: base.attach_alpha(rgb, alpha),
        "edge": lambda: base.edge_style(rgb, alpha),
        "flat": lambda: base.flat_style(rgb, alpha, seed),
        "low_detail": lambda: base.low_detail_style(rgb, alpha),
        "sketch": lambda: base.sketch_style(rgb, alpha),
        "watercolor": lambda: base.watercolor_style(rgb, alpha),
    }
    variants = output / "variants"
    variants.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for style in styles:
        path = variants / f"{style}.png"
        makers[style]().save(path)
        paths[style] = path
    gt_path = output / "solid_gt_view.ply"
    base.make_view_gt(Path(row["gt_path"]), gt_path)
    return paths, gt_path


def blend_inside_alpha(photo: Image.Image, stylized: Image.Image, alpha: Image.Image) -> Image.Image:
    blended = Image.blend(photo.convert("RGB"), stylized.convert("RGB"), 0.35)
    return base.attach_alpha(blended, alpha)


def high_edge(photo_rgb: Image.Image, alpha: Image.Image) -> Image.Image:
    del photo_rgb
    mask = np.uint8(np.asarray(alpha) > 0) * 255
    eroded = cv2.erode(mask, np.ones((5, 5), np.uint8), iterations=1)
    contour = cv2.subtract(mask, eroded)
    drawing = np.full((*contour.shape, 3), 255, dtype=np.uint8)
    drawing[contour > 0] = 20
    return base.attach_alpha(Image.fromarray(drawing), alpha)


def high_sketch(photo_rgb: Image.Image, alpha: Image.Image, size: int) -> Image.Image:
    gray = ImageOps.grayscale(photo_rgb)
    inverted = ImageOps.invert(gray)
    blurred = inverted.filter(ImageFilter.GaussianBlur(radius=15))
    gray_array = np.asarray(gray, dtype=np.float32)
    blur_array = np.asarray(blurred, dtype=np.float32)
    dodge = np.minimum(
        255.0,
        gray_array * 255.0 / (255.0 - blur_array + 1.0),
    ).astype(np.uint8)
    result = Image.fromarray(dodge).convert("RGB")
    result = result.resize((128, 128), Image.Resampling.BILINEAR)
    result = result.resize((size, size), Image.Resampling.BILINEAR).filter(ImageFilter.SMOOTH_MORE)
    return base.attach_alpha(result, alpha)


def make_severity_inputs(
    row: dict[str, str],
    main_paths: dict[str, Path],
    output: Path,
    size: int,
) -> dict[tuple[str, str], Path]:
    photo = Image.open(main_paths["photo"]).convert("RGBA")
    photo_rgb, alpha = base.rgba_on_white(photo)
    edge_medium = Image.open(main_paths["edge"]).convert("RGBA")
    sketch_medium = Image.open(main_paths["sketch"]).convert("RGBA")
    severity_dir = output / "severity"
    severity_dir.mkdir(parents=True, exist_ok=True)
    images = {
        ("edge", "low"): blend_inside_alpha(photo_rgb, edge_medium, alpha),
        ("edge", "high"): high_edge(photo_rgb, alpha),
        ("sketch", "low"): blend_inside_alpha(photo_rgb, sketch_medium, alpha),
        ("sketch", "high"): high_sketch(photo_rgb, alpha, size),
    }
    paths: dict[tuple[str, str], Path] = {
        ("edge", "medium"): main_paths["edge"],
        ("sketch", "medium"): main_paths["sketch"],
    }
    for (style, severity), image in images.items():
        path = severity_dir / f"{style}_{severity}.png"
        image.save(path)
        paths[(style, severity)] = path
    return paths


def write_manifest(path: Path, records: list[dict[str, object]]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
    os.replace(temporary, path)


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    all_rows = load_rows(args.manifest)
    if len(all_rows) != 120:
        raise RuntimeError(f"Expected exactly 120 C120 rows, found {len(all_rows)}")
    rows = all_rows[: args.limit] if args.limit > 0 else all_rows
    if args.robustness_count > len(rows):
        raise ValueError("robustness-count exceeds cohort size")

    records: list[dict[str, object]] = []
    main_assets: dict[str, tuple[dict[str, Path], Path]] = {}
    for index, row in enumerate(rows, start=1):
        output = args.output / "main" / row["object_id"]
        paths, gt_path = render_view(
            row,
            output,
            CANONICAL_ROTATION,
            MAIN_STYLES,
            args.size,
            args.seed + index,
        )
        main_assets[row["object_id"]] = (paths, gt_path)
        for style, input_path in paths.items():
            add_record(records, row, "main", "canonical", style, "medium", input_path, gt_path)
        print("MAIN_INPUT", index, len(rows), row["object_id"], row["object_name"], flush=True)
        write_manifest(args.output / "confirmatory_inputs_manifest.csv", records)

    view_rotations = {
        "yaw_m30": rotation_y(-30.0) @ CANONICAL_ROTATION,
        "yaw_p30": rotation_y(30.0) @ CANONICAL_ROTATION,
    }
    for index, row in enumerate(rows[: args.robustness_count], start=1):
        for view_id, rotation in view_rotations.items():
            output = args.output / "views" / view_id / row["object_id"]
            paths, gt_path = render_view(
                row,
                output,
                rotation,
                VIEW_STYLES,
                args.size,
                args.seed + index,
            )
            for style, input_path in paths.items():
                add_record(records, row, "view", view_id, style, "medium", input_path, gt_path)
        print("VIEW_INPUT", index, args.robustness_count, row["object_id"], flush=True)
        write_manifest(args.output / "confirmatory_inputs_manifest.csv", records)

    for index, row in enumerate(rows[: args.robustness_count], start=1):
        main_paths, gt_path = main_assets[row["object_id"]]
        severity_paths = make_severity_inputs(
            row,
            main_paths,
            args.output / "severity" / row["object_id"],
            args.size,
        )
        for (style, severity), input_path in sorted(severity_paths.items()):
            add_record(
                records,
                row,
                "severity",
                "canonical",
                style,
                severity,
                input_path,
                gt_path,
            )
        print("SEVERITY_INPUT", index, args.robustness_count, row["object_id"], flush=True)
        write_manifest(args.output / "confirmatory_inputs_manifest.csv", records)

    summary = {
        "objects_main": len(rows),
        "main_images": len(rows) * len(MAIN_STYLES),
        "objects_view": args.robustness_count,
        "view_images": args.robustness_count * 2 * len(VIEW_STYLES),
        "objects_severity": args.robustness_count,
        "severity_rows": args.robustness_count * 2 * 3,
        "manifest_rows": len(records),
        "image_size": args.size,
        "seed": args.seed,
        "canonical_rotation": CANONICAL_ROTATION.tolist(),
        "view_rotations": {key: value.tolist() for key, value in view_rotations.items()},
        "main_styles": list(MAIN_STYLES),
        "view_styles": list(VIEW_STYLES),
        "alpha_policy": "same rendered alpha within each view; white RGB outside foreground",
    }
    atomic_json(args.output / "confirmatory_inputs_summary.json", summary)
    write_manifest(args.output / "confirmatory_inputs_manifest.csv", records)
    print("INPUT_SUMMARY", json.dumps(summary, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
