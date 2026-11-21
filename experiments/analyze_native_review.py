"""Validate and summarize the Cleveland native-scale review sensitivities."""

import argparse
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np

from analyze_aligned import DIFFUSION_NATIVE, PIXEL_NATIVE, combine
from analyze_followup import PROVENANCE, CaseScores, load_cases, matched_native, summarize_by_stratum
from analyze_native_main import POWERPAINT_SAFETY, artifact_paths, model_comparisons, score_attempts, validate_source, verify_score
from analyze_prefill import utc_datetime
from latent_mask_diagnostic import read_pixels
from run_followup import NATIVE_MAIN_PROTOCOL, NATIVE_MODELS, PAIRED_SEED
from run_latent_aligned import OFFICIAL_SDXL_SETTINGS, PROTOCOL
from run_pilot import BOOTSTRAP_SEED, N_BOOTSTRAPS, SIZE, STRATA, read_json, sha256


SDXL_ARM = "native-review-sdxl"
PP_ARM = "native-review-pp-replay"
SDXL_PRIMARY = "sdxl_1_0"
SDXL_RING = "sdxl_0_99_ring"
POWERPAINT_REPLAY = "powerpaint_replay"
REPLAY_COUNT = 79
APERTURE = "shared_grid8"
REPLAY_SAFETY = "disabled_replay_only"


def validate_diagnostics(report, arm, source_sha, plan_sha, metric_provenance):
    if (
        report["protocol"] != "reconstruction-diagnostics-v1" or report["source_protocol"] != PROTOCOL
        or report["source_arm"] != arm or report["reference_plan_sha256"] != source_sha
        or report["prepared_sha256"] != plan_sha or report["input_aperture"] != APERTURE
        or {key: report[key] for key in PROVENANCE} != metric_provenance
    ):
        raise ValueError(f"Diagnostic metadata disagrees with the verified plan or scoring configuration: {arm}")


def validate_rows(rows, source_cases, model_to_cases):
    planned = {case["case_id"]: (case["artwork_id"], case["stratum"]) for case in source_cases}
    observed = defaultdict(set)
    for case_id, case in rows.items():
        if planned.get(case_id) != (case.artwork_id, case.stratum):
            raise ValueError(f"Scored case identity differs from the source: {case_id}")
        for model, seed in case.values:
            if seed != PAIRED_SEED or model not in model_to_cases:
                raise ValueError(f"Unexpected model or seed for {case_id}: {model}/{seed}")
            observed[model].add(case_id)
    if dict(observed) != model_to_cases:
        raise ValueError("Scored case coverage differs from the planned or verified coverage")


def main_inputs(summary_file, diffusion_file, shared_file, source_file, source_cases):
    summary = read_json(summary_file)
    source_sha = sha256(source_file)
    hashes = summary["inputs_sha256"]
    if (
        summary["protocol"] != "native-main-paired-summary-v1" or summary["seed"] != PAIRED_SEED
        or hashes["native_plan"] != source_sha or summary["planned_cases_per_model"] != len(source_cases)
    ):
        raise ValueError("The main summary does not match the frozen source")
    powerpaint = summary["coverage"]["diffusion"]["powerpaint"]
    blocked_rows = powerpaint["failures"]
    by_id = {case["case_id"]: case for case in source_cases}
    blocked = {row["case_id"] for row in blocked_rows}
    if (
        len(blocked) != REPLAY_COUNT or len(blocked_rows) != len(blocked)
        or powerpaint["overall"]["safety_blocked_outputs"] != REPLAY_COUNT
        or powerpaint["overall"]["completed_outputs"] != len(by_id) - REPLAY_COUNT
    ):
        raise ValueError("Expected exactly the 79 documented PowerPaint safety exclusions")
    for row in blocked_rows:
        case = by_id[row["case_id"]]
        keys = ("artwork_id", "stratum", "family")
        if (
            any(row[key] != case[key] for key in keys) or float(row["target_area"]) != float(case["target_area"])
            or row["status"] != "safety_blocked" or row["attempts"] != 2 or row["error"] != POWERPAINT_SAFETY
        ):
            raise ValueError(f"Replay ID is not a verified safety exclusion: {row['case_id']}")

    all_cases = set(by_id)
    paired = {}
    for label, arm, path, models in (
        ("diffusion", "native-main", diffusion_file, {"sdxl": all_cases, "powerpaint": all_cases - blocked}),
        ("shared", "native-main-shared", shared_file, {model: all_cases for model in PIXEL_NATIVE}),
    ):
        expected_hashes = hashes["arms"][label]
        if sha256(path) != expected_hashes["diagnostics"]:
            raise ValueError(f"Existing diagnostic bytes differ from the main verified summary: {path}")
        report = read_json(path)
        validate_diagnostics(report, arm, source_sha, expected_hashes["prepared"], summary["metric_provenance"])
        paired[label] = load_cases(report)
        validate_rows(paired[label], source_cases, models)
    return summary, paired, {row["case_id"]: row["failure_sha256"] for row in blocked_rows}


def verify_review_run(root, diagnostic_path, arm, model, source_cases, source_sha, metric_provenance, *,
                      blocked_parent_sha=None, blocked_hashes=None):
    plan_path = root / "prepared.json"
    plan = read_json(plan_path)
    if (
        plan["protocol"] != PROTOCOL or plan["arm"] != arm or plan["reference_protocol"] != NATIVE_MAIN_PROTOCOL
        or plan["reference_plan_sha256"] != source_sha or plan["model_seeds"] != {model: [PAIRED_SEED]}
        or plan["input_aperture"] != APERTURE or plan["cases"] != source_cases
    ):
        raise ValueError(f"Unexpected frozen sensitivity plan: {plan_path}")
    settings = OFFICIAL_SDXL_SETTINGS if model == "sdxl" else None
    prefill = "ring" if model == "sdxl" else None
    safety = REPLAY_SAFETY if model == "powerpaint" else None
    if (
        plan.get("inference_settings") != settings or plan.get("init_prefill") != prefill
        or plan.get("safety_checker") != safety
        or plan.get("blocked_reference_plan_sha256") != blocked_parent_sha
        or plan.get("blocked_failure_sha256") != blocked_hashes
    ):
        raise ValueError(f"Unexpected inference settings or replay provenance: {plan_path}")

    diagnostics = read_json(diagnostic_path)
    plan_sha = sha256(plan_path)
    validate_diagnostics(diagnostics, arm, source_sha, plan_sha, metric_provenance)
    if (
        diagnostics.get("inference_settings") != settings or diagnostics.get("init_prefill") != prefill
        or diagnostics.get("safety_checker") != safety or diagnostics["cases_without_outputs"]
    ):
        raise ValueError(f"Diagnostic settings or coverage differ from the sensitivity plan: {diagnostic_path}")
    cases = load_cases(diagnostics)
    validate_rows(cases, source_cases, {model: {case["case_id"] for case in source_cases}})
    diag_rows = {row["case_id"]: row for row in diagnostics["rows"]}
    scores = artifact_paths(root, "scores", ".json")
    restored = artifact_paths(root, "restored", ".png")
    expected = {f"{case['case_id']}__{model}__s{PAIRED_SEED}" for case in source_cases}
    if scores.keys() != expected or restored.keys() != expected or artifact_paths(root, "failures", ".json"):
        raise ValueError(f"Expected only complete scored sensitivity outputs without failure records: {root}")

    total_attempts = 0
    for case in source_cases:
        case_id = case["case_id"]
        stem = f"{case_id}__{model}__s{PAIRED_SEED}"
        original = read_pixels(root / "originals" / f"{case_id}.png", case["crop_sha256"])
        mask = read_pixels(root / "masks" / case["mask_file"], case["mask_sha256"]) > 0
        if (
            original.shape != (SIZE, SIZE, 3) or original.dtype != np.uint8 or mask.shape != (SIZE, SIZE)
            or not mask.any() or int(mask.sum()) != case["mask_pixels"]
        ):
            raise ValueError(f"Invalid frozen crop or scoring mask: {case_id}")
        score = read_json(scores[stem])
        verify_score(score, diag_rows[case_id], case, model, original, mask, restored[stem])
        attempts = score_attempts(score, scores[stem])
        if model == "powerpaint" and attempts != 1:
            raise ValueError(f"Expected a single attempt per replayed PowerPaint condition: {scores[stem]}")
        total_attempts += attempts

    run_path = root / f"run_{model}.json"
    run = read_json(run_path)
    start, end = (utc_datetime(run[field]) for field in ("started_at_utc", "finished_at_utc"))
    if (run["model"], run["completed"], run["failed"]) != (model, len(source_cases), 0) or end < start:
        raise ValueError(f"Run summary differs from the verified artifact set: {run_path}")
    return cases, {
        **run, "arm": arm, "planned_outputs": len(source_cases), "total_inference_attempts": total_attempts,
        "inference_settings": settings, "init_prefill": prefill, "safety_checker": safety,
        "prepared_sha256": plan_sha, "diagnostics_sha256": sha256(diagnostic_path), "run_sha256": sha256(run_path),
    }


def compare_sdxl(main, sensitivity, index):
    seed = PAIRED_SEED
    key = "sdxl", seed
    cohorts = {
        case_id: CaseScores(case.artwork_id, case.stratum, {
            (SDXL_PRIMARY, seed): main["diffusion"][case_id].values[key],
            (SDXL_RING, seed): case.values[key],
        }) for case_id, case in sensitivity.items()
    }
    with_pixels = combine(main["shared"], cohorts, PIXEL_NATIVE)
    return {
        "paired_settings": matched_native(cohorts, *index, (SDXL_PRIMARY, SDXL_RING)),
        "vs_pixels": {model: matched_native(with_pixels, *index, (model, SDXL_RING)) for model in PIXEL_NATIVE},
    }


def compare_replay_only(main, replay, index):
    seed = PAIRED_SEED
    models = (*PIXEL_NATIVE, SDXL_PRIMARY, POWERPAINT_REPLAY)
    blocked_only = {}
    by_work = defaultdict(list)
    for case_id, case in sorted(replay.items()):
        values = {
            **{(model, seed): main["shared"][case_id].values[(model, seed)] for model in PIXEL_NATIVE},
            (SDXL_PRIMARY, seed): main["diffusion"][case_id].values[("sdxl", seed)],
            (POWERPAINT_REPLAY, seed): case.values[("powerpaint", seed)],
        }
        blocked_only[case_id] = CaseScores(case.artwork_id, case.stratum, values)
        by_work[case.stratum, case.artwork_id].append(np.stack([values[model, seed] for model in models]))
    observations = [(group, np.mean(values, axis=0)) for (group, _), values in sorted(by_work.items())]
    return {
        "scope": "Previously blocked cases only. Overall equal-weights affected works after averaging their replayed conditions.",
        "matched_cases": len(replay),
        **summarize_by_stratum(observations, models, "lama"),
        "by_condition": matched_native(blocked_only, *index, models)["by_condition"],
    }


def affected_work_metadata(source_cases, blocked):
    by_work = defaultdict(list)
    for case in source_cases:
        if case["case_id"] in blocked:
            by_work[case["stratum"], case["artwork_id"]].append(case)
    return [{
        "stratum": stratum, "artwork_id": artwork, "title": cases[0].get("title"),
        "artist": cases[0].get("artist"), "subject": cases[0].get("subject"),
        "blocked_count": len(cases), "planned_conditions": 6,
        "blocked_conditions": [{"case_id": case["case_id"], "family": case["family"],
                                "target_area": float(case["target_area"])} for case in cases],
    } for (stratum, artwork), cases in sorted(by_work.items())]


def analyze(args, prereg):
    source = read_json(args.native_plan)
    index = validate_source(source)
    source_sha = sha256(args.native_plan)
    cases = source["cases"]
    verified_main, main, blocked_hashes = main_inputs(
        args.main_summary, args.main_diffusion_diagnostics, args.main_shared_diagnostics, args.native_plan, cases,
    )
    blocked = set(blocked_hashes)
    provenance = verified_main["metric_provenance"]
    sensitivity, sdxl_run = verify_review_run(
        args.sdxl_run, args.sdxl_diagnostics, SDXL_ARM, "sdxl", cases, source_sha, provenance,
    )
    print(f"Verified {len(sensitivity)} matched SDXL sensitivity cases", flush=True)
    replay_cases = [case for case in cases if case["case_id"] in blocked]
    replay, pp_run = verify_review_run(
        args.pp_run, args.pp_diagnostics, PP_ARM, "powerpaint", replay_cases, source_sha, provenance,
        blocked_parent_sha=verified_main["inputs_sha256"]["arms"]["diffusion"]["prepared"],
        blocked_hashes=blocked_hashes,
    )
    print(f"Verified {len(replay)} PowerPaint replays of the original safety exclusions", flush=True)

    main_all = combine(main["shared"], main["diffusion"], PIXEL_NATIVE)
    mixed = combine(main_all, replay, NATIVE_MODELS)
    start_key, end_key = "started_at_utc", "finished_at_utc"
    start = min((sdxl_run[start_key], pp_run[start_key]), key=utc_datetime)
    end = max((sdxl_run[end_key], pp_run[end_key]), key=utc_datetime)
    if prereg is not None and utc_datetime(start) <= utc_datetime(prereg["committed_at_utc"]):
        raise ValueError("The recorded preregistration must precede the new model inference runs")

    source_counts = Counter(case["stratum"] for case in cases)
    replay_counts = Counter(case["stratum"] for case in replay_cases)
    return {
        "protocol": "native-review-paired-summary-v1",
        "seed": PAIRED_SEED,
        "cma_native_plan_sha256": source_sha,
        "verified_main_summary_sha256": sha256(args.main_summary),
        "metric_provenance": provenance,
        "preregistration": prereg,
        "runs": {"sdxl": sdxl_run, "powerpaint_replay": pp_run},
        "inference_window": {start_key: start, end_key: end},
        "bootstrap": {"unit": "artwork", "resamples": N_BOOTSTRAPS, "seed": BOOTSTRAP_SEED,
                      "interval": "95% percentile, unadjusted"},
        "difference_direction": "candidate minus the reference named in each comparison",
        "sdxl": compare_sdxl(main, sensitivity, index),
        "powerpaint": {
            "primary_safety_on": {
                "coverage": verified_main["coverage"]["diffusion"]["powerpaint"],
                "all_models": verified_main["primary"]["all_models"],
                "vs_lama": verified_main["primary"]["pairs"]["lama__powerpaint"],
            },
            "mixed_coverage_by_stratum": {
                group: {"planned": source_counts[group], "accepted_with_safety_on": source_counts[group] - replay_counts[group],
                        "replayed_with_safety_off": replay_counts[group]} for group in STRATA
            },
            "affected_works": affected_work_metadata(cases, blocked),
            "replay_only": compare_replay_only(main, replay, index),
            "mixed_scope": ("Exploratory mixture of accepted safety-on outputs and replays of previously blocked cases. "
                            "Accepted cases were not replayed, so these scores do not estimate a checker effect on them."),
            "mixed_all": model_comparisons(mixed, index),
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ("native-plan", "main-summary", "main-diffusion-diagnostics", "main-shared-diagnostics",
                 "sdxl-run", "sdxl-diagnostics", "pp-run", "pp-diagnostics", "output"):
        parser.add_argument(f"--{flag}", required=True, type=Path)
    parser.add_argument("--prereg-commit")
    parser.add_argument("--prereg-utc")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("--output must be a new file")
    if (args.prereg_commit is None) != (args.prereg_utc is None):
        parser.error("--prereg-commit and --prereg-utc must be supplied together")
    prereg = None if args.prereg_commit is None else {"commit": args.prereg_commit, "committed_at_utc": args.prereg_utc}
    report = analyze(args, prereg)
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
