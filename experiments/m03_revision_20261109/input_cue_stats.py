"""Measure how much visual evidence each input image carries (numpy + Pillow only).

For every unique input in the schedule, inside the alpha foreground:

* ``ink_coverage``: fraction of foreground pixels with luminance < 200 (0-255)
* ``mean_luminance`` and ``luminance_std`` (contrast inside the object)
* ``fg_bg_contrast``: (255 - mean foreground luminance) / 255 on a white background
* ``edge_density``: fraction of interior foreground pixels (mask eroded by 3 px,
  so the silhouette outline is excluded) whose Sobel gradient magnitude > 40
* ``foreground_fraction``: alpha area / image area

These are descriptive covariates for the analysis of degradation versus input
evidence (03_ANALYSIS.md, A4). They are not quality judgements.

    python -I experiments/m03_revision_20261109/input_cue_stats.py \
        --schedule experiments/m03_q2_confirmatory_20260715/inference_schedule_deterministic.csv \
        --output /root/autodl-tmp/m03_q2_confirmatory_20260715/revision_20261109/input_cues.csv
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
from PIL import Image

INK_THRESHOLD = 200.0
EDGE_THRESHOLD = 40.0
ALPHA_THRESHOLD = 127
EROSION_PIXELS = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schedule", type=Path, required=True,
                        help="any schedule CSV with job_id,input_path,input_sha256 columns")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--path-prefix-from", type=str, default="",
                        help="optional prefix rewrite for input_path (from)")
    parser.add_argument("--path-prefix-to", type=str, default="")
    parser.add_argument("--extra-inputs", type=Path, default=None,
                        help="optional CSV with job_id,input_path for new conditions (e.g. lineart)")
    return parser.parse_args()


def luminance(rgb: np.ndarray) -> np.ndarray:
    return 0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]


def sobel_magnitude(gray: np.ndarray) -> np.ndarray:
    padded = np.pad(gray, 1, mode="edge")
    gx = (
        padded[:-2, 2:] + 2 * padded[1:-1, 2:] + padded[2:, 2:]
        - padded[:-2, :-2] - 2 * padded[1:-1, :-2] - padded[2:, :-2]
    )
    gy = (
        padded[2:, :-2] + 2 * padded[2:, 1:-1] + padded[2:, 2:]
        - padded[:-2, :-2] - 2 * padded[:-2, 1:-1] - padded[:-2, 2:]
    )
    return np.hypot(gx, gy) / 4.0


def erode(mask: np.ndarray, pixels: int) -> np.ndarray:
    result = mask.copy()
    for _ in range(pixels):
        padded = np.pad(result, 1, mode="constant", constant_values=False)
        result = (
            padded[1:-1, 1:-1] & padded[:-2, 1:-1] & padded[2:, 1:-1]
            & padded[1:-1, :-2] & padded[1:-1, 2:]
        )
    return result


def cue_stats(path: Path) -> dict:
    image = Image.open(path).convert("RGBA")
    array = np.asarray(image, dtype=np.float64)
    alpha = array[..., 3]
    mask = alpha > ALPHA_THRESHOLD
    # composite on white, as the images are presented to the models
    weight = alpha[..., None] / 255.0
    rgb = array[..., :3] * weight + 255.0 * (1.0 - weight)
    gray = luminance(rgb)
    if not mask.any():
        return {"foreground_fraction": 0.0, "ink_coverage": 0.0, "mean_luminance": 255.0,
                "luminance_std": 0.0, "fg_bg_contrast": 0.0, "edge_density": 0.0}
    fg = gray[mask]
    # interior edges only: erode the mask so the silhouette boundary itself does not count
    interior = erode(mask, EROSION_PIXELS)
    edges = sobel_magnitude(gray)[interior] if interior.any() else np.zeros(1)
    return {
        "foreground_fraction": float(mask.mean()),
        "ink_coverage": float(np.mean(fg < INK_THRESHOLD)),
        "mean_luminance": float(fg.mean()),
        "luminance_std": float(fg.std()),
        "fg_bg_contrast": float((255.0 - fg.mean()) / 255.0),
        "edge_density": float(np.mean(edges > EDGE_THRESHOLD)),
    }


def read_rows(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    args = parse_args()
    rows = read_rows(args.schedule)
    if args.extra_inputs:
        rows += read_rows(args.extra_inputs)
    seen = set()
    output_rows = []
    for row in rows:
        key = row["job_id"]
        if key in seen:
            continue
        seen.add(key)
        path_text = row["input_path"]
        if args.path_prefix_from and path_text.startswith(args.path_prefix_from):
            path_text = args.path_prefix_to + path_text[len(args.path_prefix_from):]
        record = {key_name: row.get(key_name, "") for key_name in
                  ("job_id", "object_id", "split", "view_id", "style", "severity", "input_sha256")}
        record["input_path"] = path_text
        try:
            record.update(cue_stats(Path(path_text)))
            record["status"] = "success"
        except Exception as error:
            record["status"] = f"failed: {error!r}"
        output_rows.append(record)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    columns = sorted({name for record in output_rows for name in record})
    with args.output.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(output_rows)
    failed = sum(record["status"] != "success" for record in output_rows)
    print(f"inputs={len(output_rows)} failed={failed} -> {args.output}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
