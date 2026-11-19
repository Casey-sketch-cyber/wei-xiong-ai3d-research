"""Compare the SDXL model-card settings on the frozen pilot cases."""

import argparse
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from analyze_aligned import ALIGNED_PROTOCOL, ORIGINAL_PROTOCOLS, center_comparison, combine
from analyze_followup import (
    PROVENANCE, CaseScores, load_cases, match_native_plan, matched_native, require_single_case_per_artwork,
)
from run_followup import NATIVE_MODELS, PAIRED_SEED, SENSITIVITY_MODELS
from run_latent_aligned import OFFICIAL_SDXL_SETTINGS
from run_pilot import BOOTSTRAP_SEED, N_BOOTSTRAPS, SEEDS, read_json, sha256


OFFICIAL_ARMS = {"baseline": "official-baseline", "sensitivity": "official-1024", "native": "official-native"}
EXPECTED_MODELS = {
    "baseline_reference": ("sdxl",),
    "baseline_official": ("sdxl",),
    "baseline_pixels": ("lama", "sdxl"),
    "baseline_shared": ("lama",),
    "sensitivity_reference": SENSITIVITY_MODELS,
    "sensitivity_official": ("sdxl_1024",),
    "sensitivity_shared": ("lama",),
    "native_reference": ("sdxl", "powerpaint"),
    "native_official": ("sdxl",),
    "native_pixels": NATIVE_MODELS,
    "native_shared": ("lama", "mat"),
}


def validate_cases(name, cases, cohort):
    counts = dict.fromkeys(EXPECTED_MODELS[name], 0)
    for case_id, case in cases.items():
        if cohort.get(case_id) != (case.artwork_id, case.stratum):
            raise ValueError(f"{name} has an unknown or inconsistent case: {case_id}")
        for model, seed in case.values:
            seeds = SEEDS if name in {"baseline_reference", "baseline_pixels"} and model == "sdxl" else (PAIRED_SEED,)
            if model not in counts or seed not in seeds:
                raise ValueError(f"{name} has an unexpected model or seed: {case_id}/{model}/{seed}")
            counts[model] += 1
    return counts


def load_inputs(paths, native_plan):
    reports = {name: read_json(path) for name, path in paths.items()}
    plan = read_json(native_plan)
    plan_index = match_native_plan(plan)
    baseline_report = reports["baseline_pixels"]
    legacy_hashes = {
        "baseline": baseline_report.get("prepared_sha256"),
        "sensitivity": reports["sensitivity_reference"].get("reference_plan_sha256"),
        "native": sha256(native_plan),
    }
    if not all(legacy_hashes.values()) or plan.get("protocol") != ORIGINAL_PROTOCOLS["native"]:
        raise ValueError("Expected the legacy prepared plan hashes and a native-v2 prepared plan")
    for name, report in reports.items():
        stage, status = name.split("_", 1)
        arm = {"reference": stage, "official": OFFICIAL_ARMS[stage], "shared": f"{stage}-shared"}.get(status)
        protocol = ALIGNED_PROTOCOL if arm else ORIGINAL_PROTOCOLS[stage]
        hash_field = "reference_plan_sha256" if arm else "prepared_sha256"
        if report.get("protocol") != "reconstruction-diagnostics-v1" or not report.get("prepared_sha256"):
            raise ValueError(f"{name} is missing diagnostic or prepared-plan provenance")
        if report.get("source_protocol") != protocol or report.get("source_arm") != arm:
            raise ValueError(f"{name} has an unexpected source protocol or arm")
        if report.get(hash_field) != legacy_hashes[stage]:
            raise ValueError(f"{name} comes from a different frozen evaluation plan")
        if status == "official" and report.get("inference_settings") != OFFICIAL_SDXL_SETTINGS:
            raise ValueError(f"{name} has different or missing inference settings")
        for key in PROVENANCE:
            if key not in report or report[key] != baseline_report.get(key):
                raise ValueError(f"{name} has different or missing metric provenance: {key}")

    cases = {name: load_cases(report) for name, report in reports.items()}
    center_ids = {case_id: (case.artwork_id, case.stratum) for case_id, case in cases["baseline_pixels"].items()}
    native_ids = {case_id: entry[:2] for case_id, entry in plan_index[0].items()}
    counts = {}
    for name, rows in cases.items():
        is_native = name.startswith("native_")
        if not is_native:
            require_single_case_per_artwork(rows)
        counts[name] = validate_cases(name, rows, native_ids if is_native else center_ids)
    return cases, counts, plan_index, legacy_hashes, reports


def center_pair(left, left_model, right, right_model, labels):
    return center_comparison(left, ((left_model, PAIRED_SEED),), right, ((right_model, PAIRED_SEED),), labels)


def center_analysis(cases, stage, model):
    reference = cases[f"{stage}_reference"]
    official = cases[f"{stage}_official"]
    pixels = cases["baseline_pixels"]
    shared = cases[f"{stage}_shared"]
    direct = center_pair(reference, model, official, model, ("reference", "official"))
    common = {case_id for case_id, row in official.items()
              if case_id in reference and (model, PAIRED_SEED) in reference[case_id].values
              and (model, PAIRED_SEED) in row.values}
    paired_reference = {case_id: reference[case_id] for case_id in common}
    paired_official = {case_id: official[case_id] for case_id in common}
    return {
        "official_vs_reference": direct,
        "official_outputs_missing": sorted(pixels.keys() - official.keys()),
        "reference_vs_original_pixels": center_pair(pixels, "lama", paired_reference, model, ("lama", model)),
        "official_vs_original_pixels": center_pair(pixels, "lama", paired_official, model, ("lama", model)),
        "reference_vs_shared_pixels": center_pair(shared, "lama", paired_reference, model, ("lama", model)),
        "official_vs_shared_pixels": center_pair(shared, "lama", paired_official, model, ("lama", model)),
    }


def native_model_comparison(pixels, diffusion, plan_index):
    combined = combine(pixels, diffusion, ("lama", "mat"))
    return {
        "comparison": matched_native(combined, *plan_index, NATIVE_MODELS),
        "vs_models": {
            comparator: matched_native(combined, *plan_index, (comparator, "sdxl"))
            for comparator in ("lama", "mat", "powerpaint")
        },
    }


def native_analysis(cases, plan_index):
    reference = cases["native_reference"]
    official = cases["native_official"]
    key = ("sdxl", PAIRED_SEED)
    common = sorted(case_id for case_id, row in official.items()
                    if case_id in reference and key in reference[case_id].values and key in row.values)
    reference = {case_id: reference[case_id] for case_id in common}
    paired = {}
    for case_id in common:
        left, right = reference[case_id], official[case_id]
        paired[case_id] = CaseScores(left.artwork_id, left.stratum, {
            ("reference", PAIRED_SEED): left.values[key], ("official", PAIRED_SEED): right.values[key],
        })
    new_diffusion = combine(reference, {case_id: official[case_id] for case_id in common}, ("powerpaint",))
    pixels, shared = cases["native_pixels"], cases["native_shared"]
    return {
        "official_vs_reference": matched_native(paired, *plan_index, ("reference", "official")),
        "official_outputs_missing": sorted(plan_index[0].keys() - official.keys()),
        "reference_vs_original_pixels": native_model_comparison(pixels, reference, plan_index),
        "official_vs_original_pixels": native_model_comparison(pixels, new_diffusion, plan_index),
        "reference_vs_shared_pixels": native_model_comparison(shared, reference, plan_index),
        "official_vs_shared_pixels": native_model_comparison(shared, new_diffusion, plan_index),
    }


def analyze(paths, native_plan):
    cases, counts, plan_index, legacy_hashes, reports = load_inputs(paths, native_plan)
    return {
        "protocol": "official-sdxl-paired-summary-v1",
        "inputs_sha256": {name: sha256(path) for name, path in {**paths, "native_plan": native_plan}.items()},
        "legacy_prepared_sha256": legacy_hashes,
        "saved_output_counts_by_source_and_model": counts,
        "official_inference_settings": {stage: reports[f"{stage}_official"].get("inference_settings")
                                       for stage in OFFICIAL_ARMS},
        "seed": PAIRED_SEED,
        "bootstrap": {"unit": "artwork", "resamples": N_BOOTSTRAPS, "seed": BOOTSTRAP_SEED,
                      "interval": "95% percentile, unadjusted"},
        "difference_direction": "candidate minus the reference listed in each comparison",
        "baseline": center_analysis(cases, "baseline", "sdxl"),
        "sensitivity": center_analysis(cases, "sensitivity", "sdxl_1024"),
        "native": native_analysis(cases, plan_index),
        "reference_1024_vs_512": center_pair(cases["baseline_reference"], "sdxl", cases["sensitivity_reference"],
                                            "sdxl_1024", ("sdxl_512", "sdxl_1024")),
        "official_1024_vs_512": center_pair(cases["baseline_official"], "sdxl", cases["sensitivity_official"],
                                           "sdxl_1024", ("sdxl_512", "sdxl_1024")),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in EXPECTED_MODELS:
        parser.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    parser.add_argument("--native-plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New analysis JSON")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("--output must be a new file")

    report = analyze({name: getattr(args, name) for name in EXPECTED_MODELS}, args.native_plan)
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
