"""Verify paired SDXL prefill runs and summarize metrics by artwork."""

import argparse
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np

from analyze_followup import CONDITIONS, match_native_plan
from latent_mask_diagnostic import LUMA_WEIGHTS, read_pixels
from run_latent_aligned import OFFICIAL_SDXL_SETTINGS, PROTOCOL
from run_pilot import BOOTSTRAP_SEED, N_BOOTSTRAPS, SEEDS, SIZE, STRATA, WORKS_PER_STRATUM, read_json, sha256


MODEL = "sdxl"
SEED = SEEDS[0]
ARMS = ("black", "gray", "ring")
METRICS = ("masked_mae", "local_lpips", "signed_luma_error")
CONTRASTS = (("gray", "black"), ("ring", "black"), ("ring", "gray"))


def validate_cohort(plan, cohort):
    cases = plan["cases"]
    if cohort == "native":
        _, stratum_by_artwork = match_native_plan(plan)
        works_per_stratum = 4
    else:
        stratum_by_artwork = {case["artwork_id"]: case["stratum"] for case in cases}
        if len(stratum_by_artwork) != len(cases):
            raise ValueError("Expected one center-mask case per artwork")
        works_per_stratum = WORKS_PER_STRATUM
    if Counter(stratum_by_artwork.values()) != dict.fromkeys(STRATA, works_per_stratum):
        raise ValueError(f"Unexpected artwork strata for {cohort}")
    if len({case["case_id"] for case in cases}) != len(cases):
        raise ValueError(f"Duplicate case IDs for {cohort}")


def historical_rows(path, plan, plan_digest):
    audit = read_json(path)
    rows = {row["case_id"]: row for row in audit["rows"]}
    if (
        audit["protocol"] != "reconstruction-diagnostics-v1" or audit["prepared_sha256"] != plan_digest
        or audit["source_protocol"] != PROTOCOL or audit["source_arm"] != plan["arm"]
        or audit["reference_plan_sha256"] != plan["reference_plan_sha256"] or audit["cases_without_outputs"]
        or audit["inference_settings"] != OFFICIAL_SDXL_SETTINGS
        or len(rows) != len(audit["rows"]) or rows.keys() != {case["case_id"] for case in plan["cases"]}
    ):
        raise ValueError(f"Historical diagnostic provenance or coverage mismatch: {path}")
    return rows


def utc_datetime(value):
    parsed = datetime.fromisoformat(value)
    if parsed.utcoffset() != timedelta(0):
        raise ValueError(f"Expected a UTC timestamp, got {value}")
    return parsed


def run_metadata(run_dir, expected_count, *, historical):
    path = run_dir / f"run_{MODEL}.json"
    run = read_json(path)
    if (run["model"] != MODEL or run["completed"] != expected_count or run["failed"]
            or any((run_dir / "failures").glob("*.json"))):
        raise ValueError(f"Expected {expected_count} completed {MODEL} outputs: {run_dir}")
    if not historical:
        start, end = (utc_datetime(run[key]) for key in ("started_at_utc", "finished_at_utc"))
        if end < start:
            raise ValueError(f"Run ends before it starts: {run_dir}")
    return {"arm": run_dir.name, "completed": run["completed"], "failed": run["failed"],
            "started_at_utc": run.get("started_at_utc"), "finished_at_utc": run.get("finished_at_utc"),
            "run_sha256": sha256(path)}


def stem(case):
    return f"{case['case_id']}__{MODEL}__s{SEED}"


def verify_identity(score, case, path):
    identity = (case["case_id"], case["artwork_id"], case["stratum"], MODEL, SEED)
    actual = tuple(score[key] for key in ("case_id", "artwork_id", "stratum", "model", "seed"))
    if actual != identity:
        raise ValueError(f"Saved score identity mismatch: {path}")


def read_arm_scores(run_dir, cases, audit_rows=None):
    expected = {stem(case) for case in cases}
    for directory, suffix in (("scores", ".json"), ("restored", ".png")):
        if {path.stem for path in (run_dir / directory).glob(f"*{suffix}")} != expected:
            raise ValueError(f"Missing or additional outputs: {run_dir / directory}")

    result = {}
    for case in cases:
        case_id = case["case_id"]
        score_path = run_dir / "scores" / f"{stem(case)}.json"
        restored_path = run_dir / "restored" / f"{stem(case)}.png"
        score = read_json(score_path)
        verify_identity(score, case, score_path)
        expected_hash = None
        if audit_rows is not None:
            audit_score = audit_rows[case_id]
            verify_identity(audit_score, case, restored_path)
            if any(score[metric] != audit_score[metric] for metric in METRICS[:2]):
                raise ValueError(f"Historical diagnostic metrics disagree: {score_path}")
            expected_hash = audit_score["restored_sha256"]

        original = read_pixels(run_dir / "originals" / f"{case_id}.png", case["crop_sha256"])
        mask = read_pixels(run_dir / "masks" / case["mask_file"], case["mask_sha256"]) > 0
        restored = read_pixels(restored_path, expected_hash)
        if (
            mask.shape != (SIZE, SIZE) or original.shape != (SIZE, SIZE, 3)
            or original.dtype != np.uint8 or restored.shape != original.shape or restored.dtype != np.uint8
            or not mask.any() or score["mask_pixels"] != int(mask.sum())
        ):
            raise ValueError(f"Unexpected image shape, encoding or score mask: {restored_path}")
        if not np.array_equal(original[~mask], restored[~mask]):
            raise ValueError(f"Restoration changed out-of-mask pixels: {restored_path}")
        error = restored[mask].astype(np.int16) - original[mask].astype(np.int16)
        mae = float(np.abs(error).mean() / 255)
        lpips = score["local_lpips"]
        if mae != score["masked_mae"] or not np.isfinite(lpips):
            raise ValueError(f"Wrong MAE or nonfinite LPIPS: {score_path}")
        result[case_id] = {
            "masked_mae": mae,
            "local_lpips": lpips,
            "signed_luma_error": float(error.mean(axis=0) @ LUMA_WEIGHTS / 255),
            "restored_sha256": expected_hash if expected_hash is not None else sha256(restored_path),
        }
    return result


def summarize(rows):
    by_artwork = defaultdict(list)
    for row in rows:
        by_artwork[row["artwork_id"]].append([[row["scores"][arm][metric] for metric in METRICS] for arm in ARMS])
    values = np.stack([np.mean(by_artwork[key], axis=0) for key in sorted(by_artwork)])
    means = values.mean(axis=0)
    n = len(values)
    sample = np.random.default_rng(BOOTSTRAP_SEED).integers(n, size=(N_BOOTSTRAPS, n))
    metrics = {metric: {"means": dict(zip(ARMS, means[:, index].tolist(), strict=True)), "contrasts": {}}
               for index, metric in enumerate(METRICS)}
    for later, earlier in CONTRASTS:
        differences = values[:, ARMS.index(later)] - values[:, ARMS.index(earlier)]
        means = differences.mean(axis=0)
        limits = np.percentile(differences[sample].mean(axis=1), [2.5, 97.5], axis=0) if n >= 2 else None
        for index, metric in enumerate(METRICS):
            metrics[metric]["contrasts"][f"{later}_minus_{earlier}"] = {
                "mean": float(means[index]), "ci95": limits[:, index].tolist() if limits is not None else None,
            }
    return {"n_artworks": n, "n_conditions": len(rows), "metrics": metrics}


def summarize_strata(rows):
    return {
        "overall": summarize(rows),
        "by_stratum": {name: summarize([row for row in rows if row["stratum"] == name]) for name in STRATA},
    }


def analyze_cohort(new_root, official_root, cohort):
    dirs = {"black": official_root / f"official-{cohort}",
            **{arm: new_root / f"{arm}-{cohort}" for arm in ARMS[1:]}}
    plan_paths = {arm: path / "prepared.json" for arm, path in dirs.items()}
    plan_hashes = {arm: sha256(path) for arm, path in plan_paths.items()}
    black = read_json(plan_paths["black"])
    validate_cohort(black, cohort)
    cases = black["cases"]
    audit = official_root / "diagnostics" / f"official-{cohort}.json"
    audit_rows = historical_rows(audit, black, plan_hashes["black"])
    runs, scores = {}, {}
    for arm, path in dirs.items():
        plan = black if arm == "black" else read_json(plan_paths[arm])
        prefill = None if arm == "black" else arm
        if (plan["protocol"] != PROTOCOL or plan["arm"] != path.name or plan.get("init_prefill") != prefill
                or plan["model_seeds"] != {MODEL: [SEED]}
                or plan["inference_settings"] != OFFICIAL_SDXL_SETTINGS or plan["cases"] != cases
                or plan["reference_plan_sha256"] != black["reference_plan_sha256"]
                or plan["reference_protocol"] != black["reference_protocol"]
                or plan["input_mask_areas"] != black["input_mask_areas"]):
            raise ValueError(f"Frozen plan differs from the prefill comparison: {path}")
        runs[arm] = {**run_metadata(path, len(cases), historical=arm == "black"),
                     "prepared_sha256": plan_hashes[arm]}
        scores[arm] = read_arm_scores(path, cases, audit_rows if arm == "black" else None)
        print(f"Verified {path.name}: {len(cases)} same-seed outputs", flush=True)

    rows = [{**{key: case.get(key) for key in ("case_id", "artwork_id", "stratum", "family")},
             "target_area": float(case["target_area"]) if cohort == "native" else None,
             "scores": {arm: scores[arm][case["case_id"]] for arm in ARMS}} for case in cases]
    return {
        **summarize_strata(rows),
        "by_condition": [
            {"family": family, "target_area": area, **summarize_strata([
                row for row in rows if (row["family"], row["target_area"]) == (family, area)
            ])} for family, area in CONDITIONS
        ] if cohort == "native" else [],
        "runs": runs,
        "black_diagnostics_sha256": sha256(audit),
        "rows": rows,
    }


def analyze(new_root, official_root, prereg=None):
    cohorts = {name: analyze_cohort(new_root, official_root, name) for name in ("baseline", "native")}
    new_runs = [cohort["runs"][arm] for cohort in cohorts.values() for arm in ARMS[1:]]
    window = {field: choose((run[field] for run in new_runs), key=utc_datetime)
              for field, choose in (("started_at_utc", min), ("finished_at_utc", max))}
    if prereg is not None and utc_datetime(window["started_at_utc"]) <= utc_datetime(prereg["committed_at_utc"]):
        raise ValueError("The recorded preregistration must precede all new inference runs")
    return {
        "protocol": "sdxl-prefill-paired-summary-v1",
        "seed": SEED,
        "bootstrap": {"unit": "artwork", "resamples": N_BOOTSTRAPS, "seed": BOOTSTRAP_SEED,
                      "interval": "95% percentile, unadjusted"},
        "signed_luma_error": "mean restored minus reference Rec.709 luma of normalized sRGB inside the scoring mask",
        "preregistration": prereg,
        "inference_window": window,
        "cohorts": cohorts,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--new-root", type=Path, required=True)
    parser.add_argument("--official-root", type=Path, required=True)
    parser.add_argument("--prereg-commit", help="Commit ID from the frozen prefill protocol")
    parser.add_argument("--prereg-utc", help="UTC committer timestamp from that commit")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("--output must be a new file")
    if (args.prereg_commit is None) != (args.prereg_utc is None):
        parser.error("--prereg-commit and --prereg-utc must be supplied together")
    prereg = None if args.prereg_commit is None else {"commit": args.prereg_commit, "committed_at_utc": args.prereg_utc}
    report = analyze(args.new_root, args.official_root, prereg)
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
