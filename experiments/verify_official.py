"""Verify saved official SDXL reruns and compare paired in-mask brightness."""

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from analyze_followup import match_native_plan
from latent_mask_diagnostic import LUMA_WEIGHTS, read_pixels
from run_latent_aligned import OFFICIAL_SDXL_SETTINGS, PROTOCOL
from run_pilot import BOOTSTRAP_SEED, N_BOOTSTRAPS, SEEDS, read_json, sha256

ARMS = (
    ("official-baseline", "baseline", "sdxl", 60),
    ("official-1024", "sensitivity", "sdxl_1024", 60),
    ("official-native", "native", "sdxl", 96),
)


def check_arm(run_dir, reference_dir, diagnostics, model, planned):
    plan_file = run_dir / "prepared.json"
    previous_plan_file = reference_dir / "prepared.json"
    previous_diagnostics = reference_dir.parent / "diagnostics" / f"{reference_dir.name}.json"
    plan = read_json(plan_file)
    previous = read_json(previous_plan_file)
    if (
        len(plan["cases"]) != planned or plan["cases"] != previous["cases"]
        or plan["reference_plan_sha256"] != previous["reference_plan_sha256"]
        or plan["input_mask_areas"] != previous["input_mask_areas"]
        or plan["inference_settings"] != OFFICIAL_SDXL_SETTINGS
        or plan["model_seeds"] != {model: [SEEDS[0]]}
    ):
        raise ValueError(f"Unexpected case or parameter freeze: {run_dir}")
    if reference_dir.name == "native":
        match_native_plan(plan)
        n_artworks = 16
    else:
        n_artworks = planned
    if len({case["artwork_id"] for case in plan["cases"]}) != n_artworks:
        raise ValueError(f"Unexpected artwork count: {run_dir}")
    report = read_json(run_dir / f"run_{model}.json")
    if report["completed"] != planned or report["failed"] or any((run_dir / "failures").glob("*.json")):
        raise ValueError(f"Expected all {planned} inference outputs: {run_dir}")
    metrics = read_json(diagnostics)
    by_case = {row["case_id"]: row for row in metrics["rows"]}
    if (
        metrics["prepared_sha256"] != sha256(plan_file)
        or metrics["source_protocol"] != PROTOCOL or metrics["source_arm"] != run_dir.name
        or metrics["reference_plan_sha256"] != plan["reference_plan_sha256"]
        or metrics["cases_without_outputs"]
        or metrics["inference_settings"] != OFFICIAL_SDXL_SETTINGS
        or len(metrics["rows"]) != planned or len(by_case) != planned
    ):
        raise ValueError(f"Diagnostic plan or row count mismatch: {diagnostics}")
    previous_metrics = read_json(previous_diagnostics)
    if previous_metrics["prepared_sha256"] != sha256(previous_plan_file):
        raise ValueError(f"Historical diagnostic plan differs: {previous_diagnostics}")
    previous_cases = [row for row in previous_metrics["rows"] if (row["model"], row["seed"]) == (model, SEEDS[0])]
    previous_by_case = {row["case_id"]: row for row in previous_cases}
    if len(previous_cases) != planned or previous_by_case.keys() != by_case.keys():
        raise ValueError(f"Historical diagnostic case coverage differs: {previous_diagnostics}")
    expected = {f"{case['case_id']}__{model}__s{SEEDS[0]}" for case in plan["cases"]}
    for directory, suffix in (("restored", "png"), ("scores", "json")):
        if {p.stem for p in (run_dir / directory).glob(f"*.{suffix}")} != expected:
            raise ValueError(f"Missing or extra saved artifacts: {run_dir / directory}")

    rows = []
    for case in plan["cases"]:
        case_id = case["case_id"]
        stem = f"{case_id}__{model}__s{SEEDS[0]}"
        original = read_pixels(run_dir / "originals" / f"{case_id}.png", case["crop_sha256"])
        mask = read_pixels(run_dir / "masks" / case["mask_file"], case["mask_sha256"]) > 0
        saved = read_json(run_dir / "scores" / f"{stem}.json")
        diagnostic = by_case[case_id]
        new = read_pixels(run_dir / "restored" / f"{stem}.png", diagnostic["restored_sha256"])
        previous_score = previous_by_case[case_id]
        old = read_pixels(reference_dir / "restored" / f"{stem}.png", previous_score["restored_sha256"])
        if not np.array_equal(original[~mask], new[~mask]) or not np.array_equal(original[~mask], old[~mask]):
            raise ValueError(f"Saved image changed original context: {stem}")
        new_delta = new[mask].astype(np.int16) - original[mask].astype(np.int16)
        old_delta = old[mask].astype(np.int16) - original[mask].astype(np.int16)
        for identity in (saved, diagnostic, previous_score):
            if (identity["case_id"], identity["artwork_id"], identity["stratum"], identity["model"], identity["seed"]) != (
                case_id, case["artwork_id"], case["stratum"], model, SEEDS[0],
            ):
                raise ValueError(f"Score identity mismatch: {stem}")
        if (
            not np.isclose(np.abs(new_delta).mean() / 255, saved["masked_mae"], atol=1e-12, rtol=0)
            or saved["masked_mae"] != diagnostic["masked_mae"]
            or saved["local_lpips"] != diagnostic["local_lpips"]
            or saved["mask_pixels"] != int(mask.sum())
        ):
            raise ValueError(f"Saved MAE mismatch: {stem}")
        rows.append({
            **{name: case.get(name) for name in ("case_id", "artwork_id", "stratum", "family", "target_area")},
            "prior_signed_luma_error": float(old_delta.mean(axis=0) @ LUMA_WEIGHTS / 255),
            "official_signed_luma_error": float(new_delta.mean(axis=0) @ LUMA_WEIGHTS / 255),
        })
    return rows, {
        "prior_plan_sha256": sha256(previous_plan_file),
        "official_plan_sha256": sha256(plan_file),
        "prior_diagnostics_sha256": sha256(previous_diagnostics),
        "official_diagnostics_sha256": sha256(diagnostics),
    }


def summarize(rows):
    by_artwork = defaultdict(list)
    for row in rows:
        by_artwork[row["artwork_id"]].append((row["prior_signed_luma_error"], row["official_signed_luma_error"]))
    values = np.stack([np.mean(pairs, axis=0) for _, pairs in sorted(by_artwork.items())])
    n = len(values)
    change = values[:, 1] - values[:, 0]
    sample = np.random.default_rng(BOOTSTRAP_SEED).integers(n, size=(N_BOOTSTRAPS, n))
    return {
        "n_artworks": n, "n_conditions": len(rows),
        "prior_signed_luma_error": float(values[:, 0].mean()),
        "official_signed_luma_error": float(values[:, 1].mean()),
        "official_minus_prior": float(change.mean()),
        "change_ci95": np.percentile(change[sample].mean(axis=1), [2.5, 97.5]).tolist(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--new-root", required=True, type=Path)
    parser.add_argument("--aligned-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("--output must be a new file")
    arms = {}
    for arm, prior, model, planned in ARMS:
        diagnostic = args.new_root / "diagnostics" / f"{arm}.json"
        rows, provenance = check_arm(args.new_root / arm, args.aligned_root / prior, diagnostic, model, planned)
        by_stratum, by_condition = defaultdict(list), defaultdict(list)
        for row in rows:
            by_stratum[row["stratum"]].append(row)
            if row["family"] is not None:
                by_condition[row["family"], row["target_area"]].append(row)
        arms[arm] = {
            "overall": summarize(rows),
            "provenance": provenance,
            "by_stratum": {name: summarize(group) for name, group in sorted(by_stratum.items())},
            "by_condition": [
                {"family": family, "target_area": area, **summarize(group)}
                for (family, area), group in sorted(by_condition.items())
            ],
            "rows": rows,
        }
        print(f"Verified {arm}: {len(rows)} output, score, diagnostic and frozen-input pairs", flush=True)
    with args.output.open("x", encoding="utf-8") as output:
        json.dump({
            "metric": "signed in-mask Rec.709 luma difference",
            "bootstrap": {"seed": BOOTSTRAP_SEED, "resamples": N_BOOTSTRAPS, "unit": "artwork"},
            "arms": arms,
        }, output, indent=2, allow_nan=False)
        output.write("\n")


if __name__ == "__main__":
    main()
