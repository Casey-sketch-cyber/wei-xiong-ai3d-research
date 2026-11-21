"""Prepare, run, and analyze the explicitly synthetic-mask arm of the painting pilot."""
import argparse
import csv
import hashlib
import io
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms, ImageDraw, ImageOps

STRATA = ("oil_canvas", "oil_wood", "watercolor_paper", "ink_paper")
SIZE = 512
AREA_PIXELS = round(0.05 * SIZE**2)
SEEDS = (2026, 2027, 2028, 2029)
BOOTSTRAP_SEED = 20261118
N_BOOTSTRAPS = 10_000
MAE_THRESHOLD = 0.01
LPIPS_THRESHOLD = 0.02
WORKS_PER_STRATUM = 15


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_png(path, array):
    tmp = path.with_suffix(".tmp")
    Image.fromarray(array).save(tmp, format="PNG")
    tmp.replace(path)


def program_mask(index):
    """Fixed-center, connected radial outline with ~5% binary area."""
    random = np.random.default_rng(BOOTSTRAP_SEED + index)
    rotation = random.uniform(0, 2 * math.pi)
    angles = np.linspace(0, 2 * math.pi, 18, endpoint=False) + rotation
    radii = random.uniform(0.58, 1.35, len(angles))
    dx, dy = np.cos(angles) * radii, np.sin(angles) * radii

    lower, upper = 30.0, 120.0
    best = None
    best_error = float("inf")
    for _ in range(20):
        scale = (lower + upper) / 2
        coordinates = np.column_stack((SIZE / 2 + dx * scale, SIZE / 2 + dy * scale))
        points = [tuple(point) for point in np.rint(coordinates).astype(int).tolist()]
        raster = Image.new("1", (SIZE, SIZE))
        ImageDraw.Draw(raster).polygon(points, fill=1)
        mask = np.array(raster)
        error = int(mask.sum()) - AREA_PIXELS
        if abs(error) < best_error:
            best, best_error = mask, abs(error)
        if error < 0:
            lower = scale
        else:
            upper = scale
    if best_error > 0.01 * AREA_PIXELS:
        raise RuntimeError(f"Mask {index} misses its area tolerance")
    return best


def crop_srgb(path):
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source)
        if min(image.size) < SIZE:
            raise ValueError(f"Image is too small: {path}")
        profile = image.info.get("icc_profile")
        if profile:
            image = ImageCms.profileToProfile(
                image, io.BytesIO(profile), ImageCms.createProfile("sRGB"), outputMode="RGB"
            )
        else:
            image = image.convert("RGB")
        return np.array(ImageOps.fit(image, (SIZE, SIZE), Image.Resampling.LANCZOS))


def prepare(manifest, run_dir):
    run_dir.mkdir(parents=True, exist_ok=True)
    lock = run_dir / "prepared.json"
    mask_dir = run_dir / "masks"
    original_dir = run_dir / "originals"
    mask_dir.mkdir(exist_ok=True)
    original_dir.mkdir(exist_ok=True)
    manifest_hash = sha256(manifest)

    if lock.exists():
        saved = read_json(lock)
        if saved["manifest_sha256"] != manifest_hash:
            raise ValueError("Run already prepared with a different artwork manifest")
        for case in saved["cases"]:
            if sha256(original_dir / f"{case['case_id']}.png") != case["crop_sha256"]:
                raise ValueError(f"Prepared crop changed: {case['case_id']}")
            if sha256(mask_dir / case["mask_file"]) != case["mask_sha256"]:
                raise ValueError(f"Prepared mask changed: {case['mask_file']}")
        return saved["cases"]

    with manifest.open(encoding="utf-8-sig", newline="") as stream:
        artworks = list(csv.DictReader(stream))
    ids = [row["artwork_id"] for row in artworks]
    if len(ids) != len(set(ids)) or any(row["stratum"] not in STRATA for row in artworks):
        raise ValueError("Artwork IDs must be unique, with defined strata")
    if any(row["rights"] != "CC0" for row in artworks):
        raise ValueError("The pilot requires an object-level CC0 entry for each artwork")

    for index in range(WORKS_PER_STRATUM):
        save_png(mask_dir / f"mask_{index:02}.png", program_mask(index).astype(np.uint8) * 255)

    cases = []
    for stratum in STRATA:
        group = sorted(
            (row for row in artworks if row["stratum"] == stratum), key=lambda row: row["artwork_id"]
        )
        if len(group) != WORKS_PER_STRATUM:
            raise ValueError(f"{stratum} must have {WORKS_PER_STRATUM} eligible artworks, found {len(group)}")
        for index, artwork in enumerate(group):
            case_id = f"{stratum}_{index:02}"
            source = (manifest.parent / artwork["image_path"]).resolve()
            if not source.is_relative_to(manifest.parent.resolve()):
                raise ValueError(f"Image is outside manifest directory: {source}")
            mask_file = f"mask_{index:02}.png"
            original = original_dir / f"{case_id}.png"
            save_png(original, crop_srgb(source))
            cases.append({
                **artwork,
                "case_id": case_id,
                "mask_file": mask_file,
                "source_image_sha256": sha256(source),
                "crop_sha256": sha256(original),
                "mask_sha256": sha256(mask_dir / mask_file),
            })
    write_json(lock, {
        "manifest_sha256": manifest_hash,
        "protocol": "procedural-v1",
        "mask_type": "procedural",
        "resolution": SIZE,
        "target_area_pixels": AREA_PIXELS,
        "diffusion_seeds": list(SEEDS),
        "cases": cases,
    })
    return cases


def reset_memory(device):
    import torch

    if torch.device(device).type == "cuda":
        torch.cuda.synchronize(device)
        torch.cuda.reset_peak_memory_stats(device)


def device_info(device):
    import torch

    if torch.device(device).type != "cuda":
        return {"device": device}
    torch.cuda.synchronize(device)
    return {
        "device": torch.cuda.get_device_name(device),
        "peak_allocated_mib": round(torch.cuda.max_memory_allocated(device) / 2**20, 1),
        "peak_reserved_mib": round(torch.cuda.max_memory_reserved(device) / 2**20, 1),
    }


def model_output(model, pixels, mask, seed):
    # Give model adapters only the masked input, so they cannot accidentally see a reference pixel in the hole.
    damaged = pixels.copy()
    damaged[mask] = 0
    output = model(damaged, mask, seed)
    if output.shape != pixels.shape or output.dtype != np.uint8:
        raise ValueError(f"Unexpected output shape or dtype: {output.shape}, {output.dtype}")
    restored = pixels.copy()
    restored[mask] = output[mask]
    return restored


def smoke(args, *, model_loader=None, predictor=model_output):
    from models import load_model

    args.run_dir.mkdir(parents=True, exist_ok=True)
    yy, xx = np.mgrid[:SIZE, :SIZE]
    pixels = np.stack((xx % 256, yy % 256, (xx + yy) % 256), axis=-1).astype(np.uint8)
    mask = program_mask(0)
    reset_memory(args.device)
    start = time.perf_counter()
    if model_loader is None:
        model_loader = load_model
    model = model_loader(args.model, args.device, args.models_dir)
    load_seconds = time.perf_counter() - start
    start = time.perf_counter()
    restored = predictor(model, pixels, mask, SEEDS[0])
    memory = device_info(args.device)
    seconds = time.perf_counter() - start
    if np.array_equal(restored[mask], np.zeros_like(restored[mask])):
        raise RuntimeError("Smoke test received an empty patch")
    if not np.array_equal(restored[~mask], pixels[~mask]):
        raise RuntimeError("An out-of-mask pixel changed")
    report = {
        "model": args.model, "resolution": SIZE, "mask_type": "procedural",
        "load_seconds": round(load_seconds, 2), "inference_seconds": round(seconds, 2),
        **memory,
    }
    write_json(args.run_dir / f"smoke_{args.model}.json", report)
    print(json.dumps(report), flush=True)


def masked_metrics(pixels, restored, mask, lpips_metric, device):
    import torch

    mae = np.abs(restored[mask].astype(np.int16) - pixels[mask].astype(np.int16)).mean() / 255
    rows, columns = np.nonzero(mask)
    top, bottom = max(0, int(rows.min()) - 8), min(SIZE, int(rows.max()) + 9)
    left, right = max(0, int(columns.min()) - 8), min(SIZE, int(columns.max()) + 9)

    def tensor(array):
        crop = array[top:bottom, left:right]
        return torch.from_numpy(crop.copy()).permute(2, 0, 1).unsqueeze(0).to(
            device=device, dtype=torch.float32
        ) / 127.5 - 1

    with torch.inference_mode():
        distance = lpips_metric(tensor(pixels), tensor(restored)).item()
    if not (math.isfinite(mae) and math.isfinite(distance)):
        raise ValueError("Non-finite scoring result")
    return float(mae), float(distance)


def run(args, *, cases=None, model_loader=None, seeds=None, predictor=model_output, max_attempts=2):
    import lpips

    from models import load_model

    if cases is None:
        cases = prepare(args.manifest, args.run_dir)
    score_dir = args.run_dir / "scores"
    output_dir = args.run_dir / "restored"
    failure_dir = args.run_dir / "failures"
    for directory in (score_dir, output_dir, failure_dir):
        directory.mkdir(exist_ok=True)
    if seeds is None:
        seeds = (SEEDS[0],) if args.model == "lama" else SEEDS

    reset_memory(args.device)
    if model_loader is None:
        model_loader = load_model
    model = model_loader(args.model, args.device, args.models_dir)
    metric = lpips.LPIPS(net="alex", version="0.1", verbose=False).to(args.device).eval()
    report_path = args.run_dir / f"run_{args.model}.json"
    previous = read_json(report_path) if report_path.exists() else {}
    started_at = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    complete, failures = 0, 0
    attempted = False
    for case in cases:
        case_id = case["case_id"]
        with Image.open(args.run_dir / "originals" / f"{case_id}.png") as image:
            pixels = np.array(image)
        with Image.open(args.run_dir / "masks" / case["mask_file"]) as image:
            mask = np.array(image) > 0
        for seed in seeds:
            stem = f"{case_id}__{args.model}__s{seed}"
            score_path = score_dir / f"{stem}.json"
            output_path = output_dir / f"{stem}.png"
            failure_path = failure_dir / f"{stem}.json"
            if score_path.exists() and output_path.exists():
                complete += 1
                continue
            attempts = read_json(failure_path)["attempts"] if failure_path.exists() else 0
            for attempt in range(attempts + 1, max_attempts + 1):
                attempted = True
                start = time.perf_counter()
                try:
                    restored = predictor(model, pixels, mask, seed)
                    mae, distance = masked_metrics(pixels, restored, mask, metric, args.device)
                    save_png(output_path, restored)
                    write_json(score_path, {
                        "case_id": case_id, "artwork_id": case["artwork_id"], "stratum": case["stratum"],
                        "model": args.model, "seed": seed, "mask_type": "procedural",
                        "masked_mae": mae, "local_lpips": distance,
                        "mask_pixels": int(mask.sum()), "attempts": attempt,
                        "seconds": round(time.perf_counter() - start, 3),
                    })
                    failure_path.unlink(missing_ok=True)
                    complete += 1
                    if complete % 15 == 0 or complete == len(cases) * len(seeds):
                        print(f"{args.model}: {complete}/{len(cases) * len(seeds)}", flush=True)
                    break
                except (RuntimeError, ValueError, OSError) as error:
                    write_json(failure_path, {"attempts": attempt, "error": str(error)})
                    print(f"{stem}: attempt {attempt}: {error}", flush=True)
            if not score_path.exists() or not output_path.exists():
                failures += 1
    report = {"model": args.model, "completed": complete, "failed": failures, **device_info(args.device)}
    if attempted:
        report["started_at_utc"] = previous.get("started_at_utc", started_at)
        report["finished_at_utc"] = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
    elif "started_at_utc" in previous and "finished_at_utc" in previous:
        report.update(started_at_utc=previous["started_at_utc"], finished_at_utc=previous["finished_at_utc"])
    write_json(report_path, report)
    print(json.dumps(report), flush=True)
    return report


def interval(samples):
    return [float(value) for value in np.percentile(samples, [2.5, 97.5])]


def support_opposite(left, right, threshold):
    return (left[0] > threshold and right[1] < -threshold) or (
        right[0] > threshold and left[1] < -threshold
    )


def analyze(args):
    cases = read_json(args.run_dir / "prepared.json")["cases"]
    metrics = ("masked_mae", "local_lpips")
    differences = {stratum: {metric: [] for metric in metrics} for stratum in STRATA}
    model_scores = {stratum: {model: {metric: [] for metric in metrics}
                            for model in ("lama", args.model)} for stratum in STRATA}
    complete_rows = []
    excluded = []

    for case in cases:
        case_id = case["case_id"]
        group = case["stratum"]
        score_dir = args.run_dir / "scores"
        lama_path = score_dir / f"{case_id}__lama__s{SEEDS[0]}.json"
        diffusion_paths = [score_dir / f"{case_id}__{args.model}__s{seed}.json" for seed in SEEDS]
        paths = [lama_path, *diffusion_paths]
        if not all(path.exists() for path in paths):
            excluded.append(case_id)
            continue
        row = {"case_id": case_id, "artwork_id": case["artwork_id"], "stratum": group}
        for metric in metrics:
            baseline = read_json(lama_path)[metric]
            diffusion = float(np.mean([read_json(path)[metric] for path in diffusion_paths]))
            model_scores[group]["lama"][metric].append(baseline)
            model_scores[group][args.model][metric].append(diffusion)
            differences[group][metric].append(diffusion - baseline)
            row.update({f"lama_{metric}": baseline, f"{args.model}_{metric}": diffusion,
                        f"difference_{metric}": diffusion - baseline})
        complete_rows.append(row)

    random = np.random.default_rng(BOOTSTRAP_SEED)
    cohorts = {}
    drawn = {}
    for group in STRATA:
        n = len(differences[group]["masked_mae"])
        cohorts[group] = {"complete_artworks": n, "metrics": {}}
        if not n:
            continue
        sample = random.integers(n, size=(N_BOOTSTRAPS, n))
        drawn[group] = {}
        for metric in metrics:
            values = np.asarray(differences[group][metric])
            replicates = values[sample].mean(axis=1)
            drawn[group][metric] = replicates
            cohorts[group]["metrics"][metric] = {
                "lama_mean": float(np.mean(model_scores[group]["lama"][metric])),
                "diffusion_mean": float(np.mean(model_scores[group][args.model][metric])),
                "diffusion_minus_lama_mean": float(values.mean()),
                "paired_sd": float(values.std(ddof=1)) if n > 1 else None,
                "ci95": interval(replicates) if n == WORKS_PER_STRATUM else None,
            }

    contrasts = {}
    control = STRATA[0]
    for group in STRATA[1:]:
        if any(cohorts[stratum]["complete_artworks"] < WORKS_PER_STRATUM for stratum in (control, group)):
            continue
        results = {}
        for metric, threshold in (("masked_mae", MAE_THRESHOLD), ("local_lpips", LPIPS_THRESHOLD)):
            left = cohorts[control]["metrics"][metric]
            right = cohorts[group]["metrics"][metric]
            ci = interval(drawn[group][metric] - drawn[control][metric])
            results[metric] = {
                "group_minus_oil_canvas_model_gap": right["diffusion_minus_lama_mean"] - left["diffusion_minus_lama_mean"],
                "ci95": ci,
                "threshold": threshold,
                "effect_beyond_threshold": ci[0] > threshold or ci[1] < -threshold,
                "opposite_ranking": support_opposite(left["ci95"], right["ci95"], 0) and (ci[0] > 0 or ci[1] < 0),
                "practical_ranking_reversal": support_opposite(left["ci95"], right["ci95"], threshold)
                and (ci[0] > 0 or ci[1] < 0),
            }
            if metric == "masked_mae":
                variance_sum = left["paired_sd"] ** 2 + right["paired_sd"] ** 2
                results[metric]["planning_n_per_group_for_0_01_gap_difference"] = max(
                    2, math.ceil((1.959964 + 0.841621) ** 2 * variance_sum / MAE_THRESHOLD**2)
                )
        contrasts[group] = results
    summary = {
        "protocol": "procedural-v1", "diffusion_model": args.model, "excluded_cases": excluded,
        "mask_type": "procedural", "bootstrap_resamples": N_BOOTSTRAPS,
        "cohorts": cohorts, "contrasts_by_reference_oil_canvas": contrasts,
        "sample_size_assumptions": "Equal group sizes, two-sided alpha 0.05, 80% power, target MAE gap difference 0.01. Normal approximation using the pilot paired SDs; not power for a ranking reversal.",
    }
    write_json(args.run_dir / "summary.json", summary)
    if complete_rows:
        with (args.run_dir / "artwork_scores.csv").open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=complete_rows[0])
            writer.writeheader()
            writer.writerows(complete_rows)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("prepare", "smoke", "run", "analyze"))
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--models-dir", type=Path)
    parser.add_argument("--model", choices=("lama", "sdxl", "sd15"))
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    if args.stage in ("prepare", "run") and args.manifest is None:
        parser.error("--manifest is required for prepare/run")
    if args.stage in ("smoke", "run") and (args.models_dir is None or args.model is None):
        parser.error("--models-dir and --model are required for smoke/run")
    if args.stage == "analyze" and args.model not in ("sdxl", "sd15"):
        parser.error("analyze requires --model sdxl or --model sd15")
    if args.stage == "prepare":
        print(f"Prepared {len(prepare(args.manifest, args.run_dir))} artworks", flush=True)
    else:
        {"smoke": smoke, "run": run, "analyze": analyze}[args.stage](args)


if __name__ == "__main__":
    main()
