"""Audit latent-grid mask coverage using only saved painting inpainting outputs."""

import argparse
from collections import defaultdict
from hashlib import file_digest
import json
import math
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np
from PIL import Image


GRID_STRIDES = {
    "lama": 8,
    "mat": 8,
    "sd15": 8,
    "sdxl": 8,
    "sdxl_empty": 8,
    "sdxl_1024": 4,
    "powerpaint": 8,
}
LUMA_WEIGHTS = np.array([0.2126, 0.7152, 0.0722], dtype=np.float64)
BLACK_LUMA = 0.05
METRICS = ("mae", "reference_luma", "output_luma", "reference_black_fraction", "output_black_fraction")


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def read_pixels(path: Path, expected_sha256: str | None = None) -> np.ndarray:
    if expected_sha256 is not None and digest(path) != expected_sha256:
        raise ValueError(f"Frozen file checksum mismatch: {path}")
    with Image.open(path) as image:
        return np.array(image)


def split_mask(mask: np.ndarray, stride: int) -> tuple[np.ndarray, np.ndarray]:
    """Partition original hole pixels on a top-left-aligned nearest grid."""
    if mask.ndim != 2 or any(size % stride for size in mask.shape):
        raise ValueError(f"Mask dimensions {mask.shape} are incompatible with stride {stride}")
    sampled = mask[::stride, ::stride].repeat(stride, axis=0).repeat(stride, axis=1)
    return mask & sampled, mask & ~sampled


def subset_metrics(reference: np.ndarray, restored: np.ndarray, subset: np.ndarray) -> dict:
    count = int(subset.sum())
    if count == 0:
        return {"pixels": 0, **dict.fromkeys(METRICS)}

    source = reference[subset].astype(np.float64) / 255
    result = restored[subset].astype(np.float64) / 255
    source_luma = source @ LUMA_WEIGHTS
    result_luma = result @ LUMA_WEIGHTS
    return {
        "pixels": count,
        "mae": float(np.abs(result - source).mean()),
        "reference_luma": float(source_luma.mean()),
        "output_luma": float(result_luma.mean()),
        "reference_black_fraction": float((source_luma <= BLACK_LUMA).mean()),
        "output_black_fraction": float((result_luma <= BLACK_LUMA).mean()),
    }


def saved_pairs(run_dir: Path, cases: dict, models: tuple[str, ...] | None) -> dict:
    scores = {path.stem: path for path in (run_dir / "scores").glob("*.json")}
    images = {path.stem: path for path in (run_dir / "restored").glob("*.png")}
    pairs = defaultdict(list)
    for name in sorted(scores.keys() | images.keys()):
        parts = name.rsplit("__", 2)
        if len(parts) != 3:
            raise ValueError(f"Unexpected saved output name: {name}")
        case_id, model, _ = parts
        if models is not None and model not in models:
            continue
        if model not in GRID_STRIDES:
            raise ValueError(f"No mask-grid mapping for saved model: {model}")
        if name not in scores or name not in images:
            raise ValueError(f"Missing saved score or restored PNG for {name}")
        score = json.loads(scores[name].read_text(encoding="utf-8"))
        if (case_id not in cases or score["case_id"] != case_id or score["model"] != model
                or name != f"{case_id}__{model}__s{score['seed']}"):
            raise ValueError(f"Saved score identity mismatch for {name}")
        pairs[case_id].append((score, images[name]))
    if not pairs:
        raise ValueError("No selected saved score/PNG pairs were found")
    return pairs


def aggregate_subset(rows: list[dict], name: str) -> dict:
    defined = [row[name] for row in rows if row[name]["pixels"]]
    pixels = sum(row["pixels"] for row in defined)
    return {
        "pixels": pixels,
        "outputs_with_pixels": len(defined),
        "pixel_weighted": {
            key: math.fsum(row[key] * row["pixels"] for row in defined) / pixels if pixels else None
            for key in METRICS
        },
        "mean_per_output": {
            key: math.fsum(row[key] for row in defined) / len(defined) if defined else None
            for key in METRICS
        },
    }


def summarize(rows: list[dict]) -> list[dict]:
    by_condition = defaultdict(list)
    for row in rows:
        by_condition[row["model"], row["family"], row["target_area"]].append(row)

    summaries = []
    for (model, family, target_area), outputs in sorted(by_condition.items()):
        mask_pixels = sum(row["mask_pixels"] for row in outputs)
        missed_pixels = sum(row["missed_pixels"] for row in outputs)
        summaries.append({
            "model": model, "family": family, "target_area": target_area,
            "grid_stride_px": GRID_STRIDES[model],
            "outputs": len(outputs),
            "cases": len({row["case_id"] for row in outputs}),
            "artworks": len({row["artwork_id"] for row in outputs}),
            "mask_pixels": mask_pixels,
            "covered_pixels": mask_pixels - missed_pixels,
            "missed_pixels": missed_pixels,
            "missed_fraction": missed_pixels / mask_pixels,
            "mean_per_output_missed_fraction": math.fsum(row["missed_fraction"] for row in outputs) / len(outputs),
            "covered": aggregate_subset(outputs, "covered"),
            "missed": aggregate_subset(outputs, "missed"),
        })
    return summaries


def analyze(run_dir: Path, models: tuple[str, ...] | None = None) -> dict:
    prepared = run_dir / "prepared.json"
    plan = json.loads(prepared.read_text(encoding="utf-8"))
    cases = {case["case_id"]: case for case in plan["cases"]}
    if len(cases) != len(plan["cases"]):
        raise ValueError("The prepared plan contains duplicate case IDs")
    outputs = saved_pairs(run_dir, cases, models)
    rows = []
    for case_id, pairs in outputs.items():
        case = cases[case_id]
        identity = {key: case[key] for key in ("case_id", "artwork_id", "stratum")}
        original = read_pixels(run_dir / "originals" / f"{case_id}.png", case.get("crop_sha256"))
        mask_name = case["mask_file"]
        if Path(mask_name).name != mask_name or not mask_name.endswith(".png"):
            raise ValueError(f"Unexpected mask filename for {case_id}: {mask_name}")
        mask = read_pixels(run_dir / "masks" / mask_name, case.get("mask_sha256")) > 0
        if mask.ndim != 2 or original.shape != (*mask.shape, 3) or original.dtype != np.uint8:
            raise ValueError(f"Invalid reference RGB image or grayscale mask for {case_id}")
        count = int(mask.sum())
        if count == 0 or case.get("mask_pixels", count) != count:
            raise ValueError(f"Empty frozen mask or mask count mismatch for {case_id}")

        family = case.get("family", "roundish")
        target_area = float(case.get("target_area", 0.05))
        for score, path in pairs:
            if any(score.get(key, value) != value for key, value in identity.items()):
                raise ValueError(f"Prepared and saved identities differ for {path.name}")
            if score.get("mask_pixels", count) != count:
                raise ValueError(f"Saved mask count differs for {path.name}")
            result = read_pixels(path)
            if result.shape != original.shape or result.dtype != np.uint8:
                raise ValueError(f"Restored PNG and reference shape or dtype differ: {path.name}")

            model = score["model"]
            stride = GRID_STRIDES[model]
            covered, missed = split_mask(mask, stride)
            covered_metrics = subset_metrics(original, result, covered)
            missed_metrics = subset_metrics(original, result, missed)
            rows.append({
                **identity,
                "model": model, "seed": score["seed"], "family": family, "target_area": target_area,
                "grid_stride_px": stride, "mask_pixels": count,
                "covered_pixels": covered_metrics["pixels"], "missed_pixels": missed_metrics["pixels"],
                "missed_fraction": missed_metrics["pixels"] / count,
                "covered": covered_metrics, "missed": missed_metrics,
            })

    return {
        "protocol": "latent-mask-diagnostic-v1",
        "source_protocol": plan.get("protocol"),
        "prepared_sha256": digest(prepared),
        "models": sorted({row["model"] for row in rows}),
        "models_without_outputs": sorted(set(models or ()) - {row["model"] for row in rows}),
        "cases_without_outputs_for_selected_models": sorted(cases.keys() - outputs.keys()),
        "prepared_cases": len(cases),
        "outputs": len(rows),
        "method": {
            "coverage": "Intersect the original hole with mask[::stride, ::stride] repeated on the reference grid",
            "stride": "8 for diffusion mask sampling at 512px, 4 at 1024px after 2x nearest mask enlargement",
            "controls": "LaMa and MAT are scored on the same stride-8 reference partition as 512px diffusion outputs. "
                        "This partition does not describe their internal mask processing",
            "qualification": "Proxy for explicit mask sampling, not a causal decomposition of model error",
            "brightness": "Rec.709 coefficients on gamma-encoded sRGB R', G', B', each divided by 255",
            "black_luma_inclusive_threshold": BLACK_LUMA,
            "mae": "Mean absolute RGB-channel difference in [0, 1]",
            "empty_subset": "Zero pixels and null metrics. Equal-output means omit empty subsets",
            "aggregate_unit": "Saved outputs by model and condition. Repeated seeds can share a mask",
        },
        "groups": summarize(rows),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New JSON outside the input run")
    parser.add_argument("--models", help="Comma-separated names. Defaults to all saved models")
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    output = args.output.resolve()
    if output.is_relative_to(run_dir) or output.exists():
        parser.error("--output must name a new file outside --run-dir")
    models = tuple(name.strip() for name in args.models.split(",")) if args.models is not None else None
    if models is not None and any(model not in GRID_STRIDES for model in models):
        parser.error(f"--models only accepts {', '.join(GRID_STRIDES)}")

    report = analyze(run_dir, models)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = NamedTemporaryFile(dir=output.parent, delete=False, mode="w", encoding="utf-8")
    staged = Path(temporary.name)
    try:
        with temporary:
            json.dump(report, temporary, indent=2, ensure_ascii=False, allow_nan=False)
            temporary.write("\n")
        os.link(staged, output)
    finally:
        staged.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
