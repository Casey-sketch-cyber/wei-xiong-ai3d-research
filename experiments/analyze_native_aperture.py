"""Compare original and grid-expanded diffusion input on the frozen Cleveland cohort."""

import argparse
import json
import os
import re
from hashlib import sha256 as hash_bytes
from pathlib import Path
from tempfile import NamedTemporaryFile

from analyze_aligned import DIFFUSION_NATIVE
from analyze_followup import CONDITIONS, PROVENANCE, CaseScores, matched_native
from analyze_native_main import summarize_coverage, validate_source, verify_run
from analyze_prefill import utc_datetime
from latent_aligned import grid_cover
from latent_mask_diagnostic import read_pixels, split_mask
from run_followup import PAIRED_SEED
from run_latent_aligned import UNEXPANDED_DIFFUSION
from run_pilot import BOOTSTRAP_SEED, N_BOOTSTRAPS, STRATA, read_json, sha256


SOURCE_SHA256 = "c2bc7621d3ae660f2336f2b9edba206a2e73838035c5dcd092878e9a8a3128d0"
MAIN_SUMMARY_SHA256 = "babeef02a7057d0abdce298caefacd9c1fab830e2db96924345d8fbb8b57c419"
CLEAN_DIFF_SHA256 = hash_bytes(b"0\0" * 2).hexdigest()
ORIGINAL = "original"
SHARED = "shared_grid8"
PAIR_STATUSES = {
    (True, True): "both_completed",
    (True, False): "original_only_completed",
    (False, True): "shared_grid8_only_completed",
    (False, False): "both_safety_blocked",
}


def validate_new_invocations(run_dir, model, entries, run, prereg_time, code_commit):
    """Check the actual clean checkout recorded by every invocation and score."""
    sidecars = {}
    provenance_files = run_dir / "provenance" / model
    started = utc_datetime(run["started_at_utc"])
    finished = utc_datetime(run["finished_at_utc"])
    for path in sorted(provenance_files.glob("*.json")):
        invocation = read_json(path)
        identity = invocation["execution_id"]
        code = invocation["code_provenance"]
        recorded = utc_datetime(invocation["recorded_at_utc"])
        if (
            not re.fullmatch(r"[0-9a-f]{32}", identity) or identity != path.stem
            or recorded <= prereg_time or code["git_state"] != "checkout" or code["git_head"] != code_commit
            or code["git_dirty"] is not False or code["git_diff_sha256"] != CLEAN_DIFF_SHA256
            or not re.fullmatch(r"[0-9a-f]{64}", code["source_python_sha256"])
            or type(code["source_python_count"]) is not int or code["source_python_count"] < 1
        ):
            raise ValueError(f"Unexpected runtime provenance: {path}")
        sidecars[identity] = invocation, recorded, sha256(path)

    report_identity = run["execution_id"]
    report_fields = ("execution_id", "recorded_at_utc", "code_provenance")
    if (
        not sidecars or report_identity not in sidecars
        or sidecars[report_identity][0] != {key: run[key] for key in report_fields}
        or min(recorded for _, recorded, _ in sidecars.values()) > started or started <= prereg_time
    ):
        raise ValueError(f"Run summary is inconsistent with its recorded invocations: {model}")
    snapshot = run["code_provenance"]
    if any(invocation["code_provenance"] != snapshot for invocation, _, _ in sidecars.values()):
        raise ValueError(f"The same model ran with different Python sources: {model}")
    for entry in entries:
        if entry["status"] != "completed":
            continue
        score_file = run_dir / "scores" / f"{entry['case_id']}__{model}__s{PAIRED_SEED}.json"
        execution_id = read_json(score_file).get("execution_id")
        if execution_id not in sidecars or sidecars[execution_id][1] > finished:
            raise ValueError(f"Score is missing provenance for a contributing invocation: {score_file}")
    return {identity: checksum for identity, (_, _, checksum) in sidecars.items()}


def geometry_summary(rows):
    mask_pixels = sum(row["mask_pixels"] for row in rows)
    original_covered = sum(row["original_covered_pixels"] for row in rows)
    missed = mask_pixels - original_covered
    expanded = sum(row["shared_input_pixels"] for row in rows)
    fractions = [row["original_missed_fraction"] for row in rows]
    return {
        "planned_cases": len(rows),
        "distinct_mask_files": len({row["mask_file"] for row in rows}),
        "mask_pixels": mask_pixels,
        "original_covered_pixels": original_covered,
        "original_missed_pixels": missed,
        "original_missed_fraction": missed / mask_pixels,
        "mean_case_original_missed_fraction": sum(fractions) / len(fractions),
        "max_case_original_missed_fraction": max(fractions),
        "shared_covered_pixels": mask_pixels,
        "shared_missed_pixels": 0,
        "shared_input_pixels": expanded,
        "additional_hidden_pixels": expanded - mask_pixels,
    }


def mask_geometry(run_dir, cases, expected_input_areas):
    """Audit the explicit latent-mask flag on every planned case, including exclusions."""
    measured = {}
    coverage_pixels = {}
    rows = []
    for case in cases:
        mask_name = case["mask_file"]
        if mask_name not in measured:
            mask = read_pixels(run_dir / "masks" / mask_name, case["mask_sha256"]) > 0
            covered, missed = split_mask(mask, 8)
            expanded = grid_cover(mask, 8)
            _, expanded_missed = split_mask(expanded, 8)
            if expanded_missed.any() or (mask & ~expanded).any():
                raise ValueError(f"Expanded mask omitted a marked grid pixel: {mask_name}")
            pixels = int(mask.sum())
            if pixels != int(covered.sum()) + int(missed.sum()):
                raise ValueError(f"Original coverage does not partition the scoring mask: {mask_name}")
            measured[mask_name] = {
                "score_pixels": pixels,
                "reference_stride8_pixels": int(expanded.sum()),
                "reference_stride4_pixels": int(grid_cover(mask, 4).sum()),
            }
            coverage_pixels[mask_name] = int(covered.sum()), int(missed.sum())

        pixels = measured[mask_name]["score_pixels"]
        covered, missed = coverage_pixels[mask_name]
        rows.append({
            **{key: case[key] for key in ("case_id", "artwork_id", "stratum", "family", "target_area", "mask_file")},
            "mask_pixels": pixels,
            "original_covered_pixels": covered,
            "original_missed_pixels": missed,
            "original_missed_fraction": missed / pixels,
            "shared_input_pixels": measured[mask_name]["reference_stride8_pixels"],
        })
    if measured != expected_input_areas:
        raise ValueError("Measured input areas disagree with the frozen arm plans")
    return {
        "grid_stride_px": 8,
        "method": "Top-left-aligned nearest-neighbor mask sampling, intersected with the original scoring hole.",
        "interpretation": "Mask geometry on planned cases. It is a proxy for the explicit mask channel.",
        "overall": geometry_summary(rows),
        "by_condition": [
            {"family": family, "target_area": area, **geometry_summary([
                row for row in rows if (row["family"], float(row["target_area"])) == (family, area)
            ])}
            for family, area in CONDITIONS
        ],
        "rows": rows,
    }


def availability_counts(entries):
    return {
        "planned_cases": len(entries),
        **{name: sum(row["pair_status"] == name for row in entries) for name in PAIR_STATUSES.values()},
    }


def availability_pairs(original, shared):
    status = {entry["case_id"]: entry["status"] for entry in shared}
    entries = [
        {
            **{key: entry[key] for key in ("case_id", "artwork_id", "stratum", "family", "target_area")},
            "pair_status": PAIR_STATUSES[(entry["status"] == "completed", status[entry["case_id"]] == "completed")],
        }
        for entry in original
    ]
    unavailable_work = {row["artwork_id"] for row in entries if row["pair_status"] != "both_completed"}
    return {
        "overall": {
            **availability_counts(entries),
            "artworks_complete_in_both": len({row["artwork_id"] for row in entries} - unavailable_work),
        },
        "by_stratum": {
            stratum: availability_counts([row for row in entries if row["stratum"] == stratum]) for stratum in STRATA
        },
        "by_condition": [
            {"family": family, "target_area": area, **availability_counts([
                row for row in entries if (row["family"], row["target_area"]) == (family, area)
            ])}
            for family, area in CONDITIONS
        ],
        "case_ids_by_status": {
            name: [row["case_id"] for row in entries if row["pair_status"] == name] for name in PAIR_STATUSES.values()
        },
    }


def compare_apertures(original, shared, index, model):
    key = model, PAIRED_SEED
    paired = {}
    for case_id in original.keys() & shared.keys():
        before, after = original[case_id], shared[case_id]
        if key in before.values and key in after.values:
            paired[case_id] = CaseScores(before.artwork_id, before.stratum, {
                (ORIGINAL, PAIRED_SEED): before.values[key],
                (SHARED, PAIRED_SEED): after.values[key],
            })
    return matched_native(paired, *index, (ORIGINAL, SHARED))


def analyze(args):
    source_sha = sha256(args.native_plan)
    summary_sha = sha256(args.main_summary)
    if source_sha != SOURCE_SHA256 or summary_sha != MAIN_SUMMARY_SHA256:
        raise ValueError("Expected the archived Cleveland cohort and main-summary bytes")
    source = read_json(args.native_plan)
    index = validate_source(source)
    archive = read_json(args.main_summary)
    prereg_time = utc_datetime(args.prereg_utc)

    shared, old_status, old_runs, old_diag, old_hashes, old_areas = verify_run(
        args.shared_run, args.shared_diagnostics, "diffusion", source["cases"], source_sha,
    )
    old_coverage = {model: summarize_coverage(entries) for model, entries in old_status.items()}
    if (
        archive["inputs_sha256"]["native_plan"] != source_sha
        or archive["inputs_sha256"]["arms"]["diffusion"] != old_hashes
        or archive["runs"]["diffusion"] != old_runs or archive["coverage"]["diffusion"] != old_coverage
        or any(old_diag[key] != archive["metric_provenance"][key] for key in PROVENANCE)
    ):
        raise ValueError("The shared-grid artifacts disagree with the archived main summary")
    print("Verified the archived shared-grid arm", flush=True)

    original, new_status, new_runs, new_diag, new_hashes, new_areas = verify_run(
        args.original_run, args.original_diagnostics, "diffusion", source["cases"], source_sha,
        arm_spec=(UNEXPANDED_DIFFUSION, DIFFUSION_NATIVE, ORIGINAL),
    )
    new_plan = read_json(args.original_run / "prepared.json")
    if (
        new_plan.get("safety_checker") != "enabled" or new_diag.get("safety_checker") != "enabled"
        or new_diag.get("init_prefill") is not None or new_areas != old_areas
        or any(new_diag[key] != old_diag[key] for key in PROVENANCE)
    ):
        raise ValueError("The original-aperture arm differs in safety, scoring provenance or frozen geometry")
    invocation_hashes = {
        model: validate_new_invocations(args.original_run, model, entries, new_runs[model], prereg_time, args.code_commit)
        for model, entries in new_status.items()
    }
    if new_runs["sdxl"]["code_provenance"] != new_runs["powerpaint"]["code_provenance"]:
        raise ValueError("The original-aperture models ran against different source snapshots")
    print("Verified original-mask outputs and their pre-inference Git provenance", flush=True)

    return {
        "protocol": "native-diffusion-aperture-summary-v1",
        "cohort": "cma",
        "seed": PAIRED_SEED,
        "planned_artworks": len(index[1]),
        "planned_cases_per_model": len(index[0]),
        "preregistration": {"commit": args.prereg_commit, "committed_at_utc": args.prereg_utc},
        "code_commit": args.code_commit,
        "difference_direction": "shared_grid8 minus original",
        "inference_window": {
            "started_at_utc": min((run["started_at_utc"] for run in new_runs.values()), key=utc_datetime),
            "finished_at_utc": max((run["finished_at_utc"] for run in new_runs.values()), key=utc_datetime),
        },
        "bootstrap": {"unit": "artwork", "resamples": N_BOOTSTRAPS, "seed": BOOTSTRAP_SEED,
                      "interval": "95% percentile, unadjusted"},
        "metric_provenance": archive["metric_provenance"],
        "inputs_sha256": {
            "native_plan": source_sha, "main_summary": summary_sha,
            "arms": {ORIGINAL: new_hashes, SHARED: old_hashes}, "original_invocations": invocation_hashes,
        },
        "runs": {ORIGINAL: new_runs, SHARED: old_runs},
        "coverage": {
            ORIGINAL: {model: summarize_coverage(entries) for model, entries in new_status.items()},
            SHARED: old_coverage,
        },
        "availability_pairs": {
            model: availability_pairs(new_status[model], old_status[model]) for model in DIFFUSION_NATIVE
        },
        "mask_geometry": mask_geometry(args.original_run, source["cases"], new_areas),
        "paired": {model: compare_apertures(original, shared, index, model) for model in DIFFUSION_NATIVE},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("native-plan", "main-summary", "shared-run", "shared-diagnostics", "original-run",
                   "original-diagnostics", "output"):
        parser.add_argument(f"--{option}", type=Path, required=True)
    parser.add_argument("--prereg-commit", required=True)
    parser.add_argument("--prereg-utc", required=True)
    parser.add_argument("--code-commit", required=True)
    args = parser.parse_args()
    for commit in (args.prereg_commit, args.code_commit):
        if not re.fullmatch(r"[0-9a-f]{40}", commit):
            parser.error("Use full Git commit IDs for --prereg-commit and --code-commit")
    if (
        args.output.exists()
        or any(args.output.resolve().is_relative_to(root.resolve()) for root in (args.shared_run, args.original_run))
    ):
        parser.error("--output must name a new file outside both run directories")
    report = analyze(args)
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
