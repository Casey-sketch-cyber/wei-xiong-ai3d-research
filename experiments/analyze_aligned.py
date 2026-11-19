"""Summarize the original, aligned-diffusion, and shared-input pilot comparisons."""

import argparse
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np

from analyze_followup import (
    PROVENANCE,
    METRICS,
    CaseScores,
    baseline_summary,
    load_cases,
    match_native_plan,
    matched_native,
    native_summary,
    require_single_case_per_artwork,
    sensitivity_summary,
    summarize_by_stratum,
)
from run_followup import NATIVE_MODELS, PAIRED_SEED, SENSITIVITY_MODELS
from run_pilot import BOOTSTRAP_SEED, N_BOOTSTRAPS, SEEDS, STRATA, read_json, sha256

DIFFUSION_NATIVE = ("sdxl", "powerpaint")
PIXEL_NATIVE = ("lama", "mat")
EXPECTED_MODELS = {
    "baseline_original": ("lama", "sdxl"),
    "baseline_corrected": ("sdxl",),
    "baseline_shared": ("lama",),
    "sensitivity_original": SENSITIVITY_MODELS,
    "sensitivity_corrected": SENSITIVITY_MODELS,
    "sensitivity_shared": ("lama",),
    "native_original": NATIVE_MODELS,
    "native_corrected": DIFFUSION_NATIVE,
    "native_shared": PIXEL_NATIVE,
}
ORIGINAL_PROTOCOLS = {"baseline": "procedural-v1", "sensitivity": "sensitivity-v1", "native": "native-v2"}
ALIGNED_PROTOCOL = "latent-alignment-v1"


def validate_cases(name, cases, cohort):
    counts = dict.fromkeys(EXPECTED_MODELS[name], 0)
    for case_id, case in cases.items():
        if cohort.get(case_id) != (case.artwork_id, case.stratum):
            raise ValueError(f"{name} has an unknown or inconsistent case: {case_id}")
        for model, seed in case.values:
            seeds = SEEDS if name.startswith("baseline_") and model == "sdxl" else (PAIRED_SEED,)
            if model not in counts or seed not in seeds:
                raise ValueError(f"{name} has an unexpected model or seed: {case_id}/{model}/{seed}")
            counts[model] += 1
    return counts


def combine(pixel_cases, diffusion_cases, pixel_models):
    assembled = {}
    for source, selected in ((pixel_cases, pixel_models), (diffusion_cases, None)):
        for case_id, case in source.items():
            scores = {key: value for key, value in case.values.items() if selected is None or key[0] in selected}
            if not scores:
                continue
            output = assembled.setdefault(case_id, CaseScores(case.artwork_id, case.stratum))
            if output.values.keys() & scores.keys():
                raise ValueError(f"Attempted to combine overlapping model results: {case_id}")
            output.values.update(scores)
    return assembled


def center_comparison(left, left_keys, right, right_keys, labels):
    rows = []
    for case_id in sorted(left.keys() & right.keys()):
        before, after = left[case_id], right[case_id]
        if not (all(key in before.values for key in left_keys) and all(key in after.values for key in right_keys)):
            continue
        left_mean = np.mean([before.values[key] for key in left_keys], axis=0)
        right_mean = np.mean([after.values[key] for key in right_keys], axis=0)
        rows.append((before.stratum, np.stack((left_mean, right_mean))))
    return summarize_by_stratum(rows, labels, labels[0])


def paired_correction(original, corrected, model, seeds, native_plan=None):
    before = {(case_id, seed) for case_id, case in original.items() for seed in seeds if (model, seed) in case.values}
    after = {(case_id, seed) for case_id, case in corrected.items() for seed in seeds if (model, seed) in case.values}
    counts = {
        "seeds": list(seeds),
        "original_outputs": len(before),
        "corrected_outputs": len(after),
        "paired_outputs": len(before & after),
        "original_only": [{"case_id": case_id, "seed": seed} for case_id, seed in sorted(before - after)],
        "corrected_only": [{"case_id": case_id, "seed": seed} for case_id, seed in sorted(after - before)],
    }
    labels = ("original", "corrected")
    if native_plan is None:
        keys = tuple((model, seed) for seed in seeds)
        comparison = center_comparison(original, keys, corrected, keys, labels)
    else:
        relabeled = {}
        for case_id, seed in sorted(before & after):
            left, right = original[case_id], corrected[case_id]
            relabeled[case_id] = CaseScores(left.artwork_id, left.stratum, {
                (labels[0], seed): left.values[(model, seed)],
                (labels[1], seed): right.values[(model, seed)],
            })
        comparison = matched_native(relabeled, *native_plan, labels)
    return {**counts, "comparison": comparison}


def stratum_model_gaps(cases):
    """Compare each stratum's four-seed SDXL–LaMa gap with the canvas gap."""
    by_stratum = {stratum: [] for stratum in STRATA}
    for _, case in sorted(cases.items()):
        lama = case.values.get(("lama", PAIRED_SEED))
        keys = [("sdxl", seed) for seed in SEEDS]
        if lama is not None and all(key in case.values for key in keys):
            by_stratum[case.stratum].append(np.mean([case.values[key] for key in keys], axis=0) - lama)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    means, bootstraps = {}, {}
    for stratum, rows in by_stratum.items():
        if not rows:
            continue
        values = np.stack(rows)
        means[stratum] = values.mean(axis=0)
        if len(rows) >= 2:
            draws = rng.integers(len(rows), size=(N_BOOTSTRAPS, len(rows)))
            bootstraps[stratum] = values[draws].mean(axis=1)

    control = "oil_canvas"
    contrasts = {}
    for stratum in STRATA:
        if stratum == control or control not in means or stratum not in means:
            continue
        difference = means[stratum] - means[control]
        ci = None
        if stratum in bootstraps and control in bootstraps:
            ci = np.percentile(bootstraps[stratum] - bootstraps[control], [2.5, 97.5], axis=0)
        contrasts[stratum] = {
            "n_artworks": len(by_stratum[stratum]),
            "n_reference_artworks": len(by_stratum[control]),
            "metrics": {
                metric: {"mean": float(difference[i]), "ci95": ci[:, i].tolist() if ci is not None else None}
                for i, metric in enumerate(METRICS)
            },
        }
    return contrasts


def baseline_analysis(cases):
    original = cases["baseline_original"]
    corrected = cases["baseline_corrected"]
    adjusted = combine(original, corrected, ("lama",))
    corrected_report, seed_report = baseline_summary(adjusted)
    report = {
        "original": baseline_summary(original)[0],
        "corrected": corrected_report,
        "corrected_same_seed": seed_report,
        "sdxl_original_vs_corrected": paired_correction(original, corrected, "sdxl", SEEDS),
    }
    report["original"]["model_gap_contrasts_vs_oil_canvas"] = stratum_model_gaps(original)
    corrected_report["model_gap_contrasts_vs_oil_canvas"] = stratum_model_gaps(adjusted)
    if "baseline_shared" in cases:
        shared = cases["baseline_shared"]
        shared_comparison = combine(shared, corrected, ("lama",))
        report["shared_stride8"] = baseline_summary(shared_comparison)[0]
        report["shared_stride8"]["model_gap_contrasts_vs_oil_canvas"] = stratum_model_gaps(shared_comparison)
        report["lama_original_vs_shared_stride8"] = paired_correction(original, shared, "lama", (PAIRED_SEED,))
    return report, adjusted


def sensitivity_analysis(cases, adjusted_baseline):
    original = cases["sensitivity_original"]
    corrected = cases["sensitivity_corrected"]
    report = {
        "original": sensitivity_summary(cases["baseline_original"], original),
        "corrected": sensitivity_summary(adjusted_baseline, corrected),
        "original_vs_corrected": {
            model: paired_correction(original, corrected, model, (PAIRED_SEED,))
            for model in SENSITIVITY_MODELS
        },
    }
    shared_controls = (("sdxl_1024", "sensitivity_shared", 4), ("sdxl_empty", "baseline_shared", 8))
    report["shared_input"] = {
        model: {
            "effective_stride_at_scoring_resolution": stride,
            **center_comparison(
                cases[source], (("lama", PAIRED_SEED),), corrected, ((model, PAIRED_SEED),), ("lama", model)
            ),
        }
        for model, source, stride in shared_controls if source in cases
    }
    return report


def native_analysis(cases, plan, plan_index):
    original = cases["native_original"]
    corrected = cases["native_corrected"]
    adjusted = combine(original, corrected, PIXEL_NATIVE)
    report = {
        "original": native_summary(original, plan),
        "corrected": native_summary(adjusted, plan),
        "original_vs_corrected": {
            model: paired_correction(original, corrected, model, (PAIRED_SEED,), plan_index)
            for model in DIFFUSION_NATIVE
        },
    }
    if "native_shared" in cases:
        shared = cases["native_shared"]
        report["shared_stride8"] = native_summary(combine(shared, corrected, PIXEL_NATIVE), plan)
        report["pixels_original_vs_shared_stride8"] = {
            model: paired_correction(original, shared, model, (PAIRED_SEED,), plan_index)
            for model in PIXEL_NATIVE
        }
    return report


def load_inputs(paths, native_plan):
    reports = {name: read_json(path) for name, path in paths.items()}
    metric_reference = reports["baseline_original"]
    for name, report in reports.items():
        for key in PROVENANCE:
            if key in metric_reference and key in report and report[key] != metric_reference[key]:
                raise ValueError(f"Metric provenance mismatch for {name}: {key}")
        stage, status = name.split("_", maxsplit=1)
        protocol = ORIGINAL_PROTOCOLS[stage] if status == "original" else ALIGNED_PROTOCOL
        if report.get("source_protocol", protocol) != protocol:
            raise ValueError(f"Unexpected source protocol for {name}: {report['source_protocol']}")
        if status != "original":
            expected_arm = stage if status == "corrected" else f"{stage}-shared"
            arm = report.get("source_arm", report.get("arm"))
            if arm is not None and arm != expected_arm:
                raise ValueError(f"Unexpected aligned arm for {name}: {arm}")
            reference_hash = reports[f"{stage}_original"].get("prepared_sha256")
            linked_hash = report.get("reference_plan_sha256")
            if linked_hash is not None and reference_hash is not None and linked_hash != reference_hash:
                raise ValueError(f"Different frozen evaluation plan for {name}")

    all_cases = {name: load_cases(report) for name, report in reports.items()}
    baseline_identity = {
        case_id: (case.artwork_id, case.stratum) for case_id, case in all_cases["baseline_original"].items()
    }
    native_plan_data, native_index = None, None
    native_identity = {}
    if native_plan is not None and "native_original" in reports:
        plan_hash = sha256(native_plan)
        declared = reports["native_original"].get("prepared_sha256")
        if declared is not None and declared != plan_hash:
            raise ValueError("Native original diagnostics do not match the supplied plan.")
        native_plan_data = read_json(native_plan)
        native_index = match_native_plan(native_plan_data)
        native_identity = {case_id: value[:2] for case_id, value in native_index[0].items()}

    counts = {}
    for name, cases in all_cases.items():
        native = name.startswith("native_")
        if not native:
            require_single_case_per_artwork(cases)
        counts[name] = validate_cases(name, cases, native_identity if native else baseline_identity)
    return all_cases, counts, native_plan_data, native_index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in EXPECTED_MODELS:
        parser.add_argument("--" + name.replace("_", "-"), type=Path, required=name in {
            "baseline_original", "baseline_corrected",
        })
    parser.add_argument("--native-plan", type=Path, help="Frozen native prepared.json")
    parser.add_argument("--output", type=Path, required=True, help="New analysis JSON")
    args = parser.parse_args()
    paths = {name: getattr(args, name) for name in EXPECTED_MODELS if getattr(args, name) is not None}
    for stage in ("sensitivity", "native"):
        if any(name.startswith(stage + "_") for name in paths) and not {
            stage + "_original", stage + "_corrected",
        }.issubset(paths):
            parser.error(f"Provide both --{stage}-original and --{stage}-corrected.")
    if "native_original" in paths and args.native_plan is None:
        parser.error("Native diagnostics require --native-plan.")
    if args.output.exists():
        parser.error("--output must be a new file.")

    cases, counts, plan, plan_index = load_inputs(paths, args.native_plan)
    baseline, adjusted = baseline_analysis(cases)
    source_paths = {**paths, **({"native_plan": args.native_plan} if plan is not None else {})}
    report = {
        "protocol": "aligned-paired-summary-v1",
        "inputs_sha256": {name: sha256(path) for name, path in source_paths.items()},
        "saved_output_counts_by_source_and_model": counts,
        "bootstrap": {"unit": "artwork", "resamples": N_BOOTSTRAPS, "seed": BOOTSTRAP_SEED,
                      "interval": "95% percentile, unadjusted"},
        "difference_direction": "candidate minus reference shown in each comparison",
        "policies": {
            "corrected": "aligned diffusion input; original saved pixel-model input; original scoring mask",
            "shared_input": "aligned inputs for both sides; stride 8 at 512 except stride 4 for the 1024 comparison",
        },
        "baseline": baseline,
        "sensitivity": sensitivity_analysis(cases, adjusted) if "sensitivity_original" in cases else None,
        "native": native_analysis(cases, plan, plan_index) if plan is not None else None,
    }
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
