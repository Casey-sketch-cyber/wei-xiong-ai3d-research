"""Verify the native-scale main experiment and compare on frozen artwork pairs."""

import argparse
import json
import os
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np

from analyze_aligned import DIFFUSION_NATIVE, PIXEL_NATIVE, combine
from analyze_followup import CONDITIONS, METRICS, PROVENANCE, CaseScores, load_cases, match_native_plan, matched_native
from analyze_prefill import utc_datetime
from latent_mask_diagnostic import read_pixels
from prepare_aic_replication import CATALOG_SHA256, candidate_rank
from run_followup import NATIVE_MAIN_MANIFEST_SHA256, NATIVE_MAIN_PROTOCOL, NATIVE_MODELS, NATIVE_SEED, PAIRED_SEED
from run_latent_aligned import NATIVE_AIC_PROTOCOL, PROTOCOL
from run_pilot import BOOTSTRAP_SEED, N_BOOTSTRAPS, SIZE, STRATA, WORKS_PER_STRATUM, read_json, sha256


ARMS = {
    "diffusion": ("native-main", DIFFUSION_NATIVE, "shared_grid8"),
    "shared": ("native-main-shared", PIXEL_NATIVE, "shared_grid8"),
    "original": ("native-main-original", PIXEL_NATIVE, "original"),
}
POWERPAINT_SAFETY = "The PowerPaint base safety checker withheld the generated image"
MAX_ATTEMPTS = 2


def validate_source(plan, *, cohort="cma"):
    aic = cohort == "aic"
    protocol = NATIVE_AIC_PROTOCOL if aic else NATIVE_MAIN_PROTOCOL
    if (
        plan["protocol"] != protocol or plan["seed"] != PAIRED_SEED
        or (not aic and plan["manifest_sha256"] != NATIVE_MAIN_MANIFEST_SHA256)
    ):
        raise ValueError(f"Unexpected frozen source or paired inference seed for {cohort}")
    if aic and (plan["catalog_sha256"] != CATALOG_SHA256 or plan["source_rendition"] != "aic_iiif_1686_jpeg"):
        raise ValueError("Unexpected AIC catalog or image rendition in the frozen plan")
    index = match_native_plan(plan)
    work_strata = index[1]
    if Counter(work_strata.values()) != dict.fromkeys(STRATA, WORKS_PER_STRATUM):
        raise ValueError("Expected 15 artworks in each frozen stratum")
    rng = np.random.default_rng(NATIVE_SEED)
    artwork_order = {}
    for stratum in STRATA:
        artwork_ids = sorted(artwork for artwork, group in work_strata.items() if group == stratum)
        if aic:
            if any(not uid.startswith("aic-") or not uid[4:].isdigit() for uid in artwork_ids):
                raise ValueError(f"Invalid AIC object ID in {stratum}")
            artwork_order[stratum] = sorted(
                artwork_ids, key=lambda uid: (candidate_rank(stratum, int(uid[4:])), int(uid[4:])),
            )
        else:
            artwork_order[stratum] = [artwork_ids[position] for position in rng.permutation(len(artwork_ids))]
    observed = {stratum: list(dict.fromkeys(case["artwork_id"] for case in plan["cases"] if case["stratum"] == stratum))
                for stratum in STRATA}
    if artwork_order != plan["artwork_order_by_stratum"] or artwork_order != observed:
        raise ValueError("The case order differs from the frozen sampling order")
    return index


def artifact_paths(root, directory, suffix):
    return {path.stem: path for path in (root / directory).glob(f"*{suffix}")}


def score_attempts(payload, path):
    value = payload["attempts"]
    if type(value) is not int or not 1 <= value <= MAX_ATTEMPTS:
        raise ValueError(f"Unexpected inference attempt count: {path}")
    return value


def verify_score(saved, diagnostic, case, model, original, mask, output_file):
    expected = (case["case_id"], case["artwork_id"], case["stratum"], model, PAIRED_SEED)
    keys = ("case_id", "artwork_id", "stratum", "model", "seed")
    if any(tuple(row[key] for key in keys) != expected for row in (saved, diagnostic)):
        raise ValueError(f"Score identity mismatch: {output_file}")
    if saved["mask_pixels"] != int(mask.sum()):
        raise ValueError(f"Score mask pixel count mismatch: {output_file}")
    restored = read_pixels(output_file, diagnostic["restored_sha256"])
    if restored.shape != original.shape or restored.dtype != np.uint8:
        raise ValueError(f"Unexpected restored RGB crop: {output_file}")
    if not np.array_equal(restored[~mask], original[~mask]):
        raise ValueError(f"Restored output changed original context: {output_file}")
    difference = restored[mask].astype(np.int16) - original[mask].astype(np.int16)
    mae = float(np.abs(difference).mean() / 255)
    if mae != saved["masked_mae"] or mae != diagnostic["masked_mae"] or saved["local_lpips"] != diagnostic["local_lpips"]:
        raise ValueError(f"Saved reconstruction metrics disagree: {output_file}")


def verify_run(root, diagnostic_file, arm_key, source_cases, source_sha, *, cohort="cma"):
    arm, models, aperture = ARMS[arm_key]
    aic = cohort == "aic"
    if aic:
        arm = arm.replace("native-main", "aic-replication")
    protocol = NATIVE_AIC_PROTOCOL if aic else NATIVE_MAIN_PROTOCOL
    plan_file = root / "prepared.json"
    plan = read_json(plan_file)
    if (
        plan["protocol"] != PROTOCOL or plan["arm"] != arm or plan["reference_protocol"] != protocol
        or plan["input_aperture"] != aperture or plan["reference_plan_sha256"] != source_sha
        or plan["cases"] != source_cases or plan["model_seeds"] != {model: [PAIRED_SEED] for model in models}
        or plan.get("inference_settings") is not None or plan.get("init_prefill") is not None
    ):
        raise ValueError(f"Arm plan differs from the frozen native-main design: {plan_file}")

    diagnostics = read_json(diagnostic_file)
    plan_sha = sha256(plan_file)
    if (
        diagnostics["protocol"] != "reconstruction-diagnostics-v1" or diagnostics["source_protocol"] != PROTOCOL
        or diagnostics["source_arm"] != arm or diagnostics["reference_plan_sha256"] != source_sha
        or diagnostics["input_aperture"] != aperture
        or diagnostics["prepared_sha256"] != plan_sha or diagnostics.get("inference_settings") != plan.get("inference_settings")
    ):
        raise ValueError(f"Diagnostic provenance does not match the arm plan: {diagnostic_file}")

    cases = load_cases(diagnostics)
    diagnostic_rows = {f"{row['case_id']}__{row['model']}__s{row['seed']}": row for row in diagnostics["rows"]}
    scores = artifact_paths(root, "scores", ".json")
    outputs = artifact_paths(root, "restored", ".png")
    failures = artifact_paths(root, "failures", ".json")
    expected = {f"{case['case_id']}__{model}__s{PAIRED_SEED}" for case in source_cases for model in models}
    if (
        len(diagnostic_rows) != len(diagnostics["rows"]) or scores.keys() != outputs.keys()
        or scores.keys() != diagnostic_rows.keys() or scores.keys() & failures.keys()
        or scores.keys() | failures.keys() != expected
        or diagnostics["cases_without_outputs"] != [case["case_id"] for case in source_cases if case["case_id"] not in cases]
    ):
        raise ValueError(f"Expected an exact partition of planned cases into scored outputs and logged failures: {root}")

    statuses = {model: [] for model in models}
    for case in source_cases:
        case_id = case["case_id"]
        original = read_pixels(root / "originals" / f"{case_id}.png", case["crop_sha256"])
        mask = read_pixels(root / "masks" / case["mask_file"], case["mask_sha256"]) > 0
        if (
            original.shape != (SIZE, SIZE, 3) or original.dtype != np.uint8 or mask.shape != (SIZE, SIZE)
            or not mask.any() or int(mask.sum()) != case["mask_pixels"]
        ):
            raise ValueError(f"Unexpected frozen crop or score mask: {case_id}")
        info = {key: case[key] for key in ("case_id", "artwork_id", "stratum", "family")}
        info["target_area"] = float(case["target_area"])
        for model in models:
            stem = f"{case_id}__{model}__s{PAIRED_SEED}"
            if stem in failures:
                failure_file = failures[stem]
                failure = read_json(failure_file)
                attempts = score_attempts(failure, failure_file)
                if model != "powerpaint" or attempts != MAX_ATTEMPTS or failure["error"] != POWERPAINT_SAFETY:
                    raise ValueError(f"Unexpected unsuccessful inference: {failure_file} ({failure['error']})")
                statuses[model].append({**info, "attempts": attempts, "status": "safety_blocked", "error": failure["error"],
                                        "failure_sha256": sha256(failure_file)})
            else:
                saved = read_json(scores[stem])
                verify_score(saved, diagnostic_rows[stem], case, model, original, mask, outputs[stem])
                statuses[model].append({**info, "attempts": score_attempts(saved, scores[stem]), "status": "completed"})

    runs = {}
    for model, entries in statuses.items():
        run_file = root / f"run_{model}.json"
        run = read_json(run_file)
        completed = sum(entry["status"] == "completed" for entry in entries)
        start, end = (utc_datetime(run[key]) for key in ("started_at_utc", "finished_at_utc"))
        if (run["model"], run["completed"], run["failed"]) != (model, completed, len(entries) - completed) or end < start:
            raise ValueError(f"Inconsistent model counts or timestamps: {run_file}")
        runs[model] = {**run, "summary_sha256": sha256(run_file)}

    return cases, statuses, runs, diagnostics, {"prepared": plan_sha, "diagnostics": sha256(diagnostic_file)}, plan["input_mask_areas"]


def coverage_counts(entries):
    completed = sum(entry["status"] == "completed" for entry in entries)
    blocked = len(entries) - completed
    return {
        "planned_outputs": len(entries),
        "attempted_outputs": len(entries),
        "total_inference_attempts": sum(entry["attempts"] for entry in entries),
        "completed_outputs": completed,
        "failed_outputs": blocked,
        "safety_blocked_outputs": blocked,
        "completion_fraction": completed / len(entries),
        "planned_artworks": len({entry["artwork_id"] for entry in entries}),
        "artworks_with_all_planned_outputs": len({entry["artwork_id"] for entry in entries})
        - len({entry["artwork_id"] for entry in entries if entry["status"] != "completed"}),
    }


def summarize_coverage(entries):
    return {
        "overall": coverage_counts(entries),
        "by_stratum": {stratum: coverage_counts([entry for entry in entries if entry["stratum"] == stratum])
                       for stratum in STRATA},
        "by_condition": [
            {"family": family, "target_area": area, **coverage_counts([
                entry for entry in entries if (entry["family"], entry["target_area"]) == (family, area)
            ])} for family, area in CONDITIONS
        ],
        "failures": [entry for entry in entries if entry["status"] != "completed"],
    }


def stratum_gap_contrasts(cases, pair):
    """Compare paired MAE gaps across artwork strata, in descriptor order."""
    reference, candidate = pair
    mae = METRICS.index("masked_mae")
    by_artwork = defaultdict(list)
    for case in cases.values():
        before, after = (case.values.get((model, PAIRED_SEED)) for model in pair)
        if before is not None and after is not None:
            by_artwork[case.stratum, case.artwork_id].append(float(after[mae] - before[mae]))

    strata = {name: [] for name in STRATA}
    for (stratum, _), gaps in sorted(by_artwork.items()):
        if len(gaps) == len(CONDITIONS):
            strata[stratum].append(float(np.mean(gaps)))
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    draws = {name: np.asarray(values)[rng.integers(len(values), size=(N_BOOTSTRAPS, len(values)))].mean(axis=1)
             for name, values in strata.items() if len(values) >= 2}
    canvas = "oil_canvas"
    contrasts = {}
    for name, values in strata.items():
        if name == canvas or not values or not strata[canvas]:
            continue
        contrasts[name] = {
            "n_artworks": len(values), "n_canvas_artworks": len(strata[canvas]),
            "mean": float(np.mean(values) - np.mean(strata[canvas])),
            "ci95": np.percentile(draws[name] - draws[canvas], [2.5, 97.5]).tolist()
            if name in draws and canvas in draws else None,
        }
    return {"reference_model": reference, "candidate_model": candidate,
            "reference_stratum": canvas, "stratum_minus_canvas": contrasts}


def model_comparisons(cases, index, *, compare_strata=False):
    pairs = {}
    for pair in combinations(NATIVE_MODELS, 2):
        summary = matched_native(cases, *index, pair)
        if compare_strata:
            summary["mae_gap_by_stratum_vs_canvas"] = stratum_gap_contrasts(cases, pair)
        pairs["__".join(pair)] = summary
    return {"all_models": matched_native(cases, *index, NATIVE_MODELS), "pairs": pairs}


def pixel_aperture_comparison(original, shared, index, model):
    key = (model, PAIRED_SEED)
    paired = {
        case_id: CaseScores(case.artwork_id, case.stratum, {
            ("original", PAIRED_SEED): case.values[key],
            ("shared", PAIRED_SEED): shared[case_id].values[key],
        }) for case_id, case in original.items()
    }
    return matched_native(paired, *index, ("original", "shared"))


def analyze(plan_file, run_dirs, diagnostic_files, prereg, *, cohort="cma"):
    source = read_json(plan_file)
    index = validate_source(source, cohort=cohort)
    source_sha = sha256(plan_file)
    cases, coverage, runs, run_hashes = {}, {}, {}, {}
    metric_provenance = None
    mask_areas = None
    for key in ARMS:
        scores, statuses, run, diagnostics, hashes, input_areas = verify_run(
            run_dirs[key], diagnostic_files[key], key, source["cases"], source_sha, cohort=cohort,
        )
        provenance = {field: diagnostics[field] for field in PROVENANCE}
        if metric_provenance is not None and provenance != metric_provenance:
            raise ValueError(f"Metric provenance differs between arms: {diagnostic_files[key]}")
        if mask_areas is not None and input_areas != mask_areas:
            raise ValueError(f"Input mask area metadata differs between arms: {run_dirs[key]}")
        metric_provenance, mask_areas = provenance, input_areas
        cases[key], runs[key], run_hashes[key] = scores, run, hashes
        coverage[key] = {model: summarize_coverage(entries) for model, entries in statuses.items()}
        print(f"Verified {run_dirs[key].name} across {len(source['cases'])} planned cases", flush=True)

    start_key, end_key = "started_at_utc", "finished_at_utc"
    run_entries = [run for models in runs.values() for run in models.values()]
    start = min((run[start_key] for run in run_entries), key=utc_datetime)
    end = max((run[end_key] for run in run_entries), key=utc_datetime)
    if prereg is not None and utc_datetime(start) <= utc_datetime(prereg["committed_at_utc"]):
        raise ValueError("The recorded preregistration must precede all model inference runs")
    cohort_provenance = {}
    if cohort == "aic":
        frozen_prereg = {"commit": source["prereg_commit"], "committed_at_utc": source["prereg_utc"]}
        registered, acquired, prepared, started = (utc_datetime(time) for time in (
            source["prereg_utc"], source["artwork_manifest_completed_utc"], source["prepared_utc"], start,
        ))
        if frozen_prereg != prereg or not registered < acquired <= prepared <= started:
            raise ValueError("AIC inference must follow the frozen sampling, acquisition and preparation")
        cohort_provenance = {key: source[key] for key in (
            "collection", "source_rendition", "catalog_sha256", "candidate_order_sha256", "manifest_sha256",
            "artwork_manifest_completed_utc", "prepared_utc",
        )}

    primary = combine(cases["shared"], cases["diffusion"], PIXEL_NATIVE)
    original = combine(cases["original"], cases["diffusion"], PIXEL_NATIVE)
    return {
        "protocol": "native-main-paired-summary-v1",
        **({"cohort": cohort, "cohort_provenance": cohort_provenance} if cohort_provenance else {}),
        "seed": PAIRED_SEED,
        "planned_artworks": len(index[1]),
        "planned_cases_per_model": len(index[0]),
        "inputs_sha256": {"native_plan": source_sha, "arms": run_hashes},
        "runs": runs,
        "coverage": coverage,
        "metric_provenance": metric_provenance,
        "preregistration": prereg,
        "inference_window": {start_key: start, end_key: end},
        "bootstrap": {"unit": "artwork", "resamples": N_BOOTSTRAPS, "seed": BOOTSTRAP_SEED,
                      "interval": "95% percentile, unadjusted"},
        "difference_direction": "candidate minus the reference named in each comparison",
        "primary": model_comparisons(primary, index, compare_strata=True),
        "original_sensitivity": model_comparisons(original, index),
        "pixel_aperture_paired": {model: pixel_aperture_comparison(cases["original"], cases["shared"], index, model)
                                  for model in PIXEL_NATIVE},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native-plan", type=Path, required=True)
    parser.add_argument("--cohort", choices=("cma", "aic"), default="cma")
    for identifier in ARMS:
        parser.add_argument(f"--{identifier}-run", type=Path, required=True)
        parser.add_argument(f"--{identifier}-diagnostics", type=Path, required=True)
    parser.add_argument("--prereg-commit", help="Commit ID of the frozen native-main protocol")
    parser.add_argument("--prereg-utc", help="UTC committer timestamp from that commit")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("--output must be a new file")
    if (args.prereg_commit is None) != (args.prereg_utc is None):
        parser.error("--prereg-commit and --prereg-utc must be supplied together")
    prereg = None if args.prereg_commit is None else {"commit": args.prereg_commit, "committed_at_utc": args.prereg_utc}
    run_dirs = {key: getattr(args, f"{key}_run") for key in ARMS}
    diagnostics = {key: getattr(args, f"{key}_diagnostics") for key in ARMS}
    report = analyze(args.native_plan, run_dirs, diagnostics, prereg, cohort=args.cohort)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = NamedTemporaryFile(dir=args.output.parent, delete=False, mode="w", encoding="utf-8")
    staged = Path(temporary.name)
    try:
        with temporary:
            json.dump(report, temporary, indent=2, ensure_ascii=False, allow_nan=False)
            temporary.write("\n")
        os.link(staged, args.output)
    finally:
        staged.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
