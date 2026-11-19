"""Summarize paired artwork-level diagnostics for the pilot and its follow-ups."""

import argparse
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np

from diagnostic_metrics import METRICS as DIAGNOSTIC_METRICS
from patch_design import MASK_AREAS, MASK_FAMILIES
from run_followup import NATIVE_MODELS, PAIRED_SEED, SENSITIVITY_MODELS
from run_pilot import BOOTSTRAP_SEED, N_BOOTSTRAPS, SEEDS, STRATA, WORKS_PER_STRATUM, read_json, sha256

METRICS = ("masked_mae", "local_lpips", *DIAGNOSTIC_METRICS)
CONDITIONS = tuple((family, area) for family in MASK_FAMILIES for area in MASK_AREAS)
PROVENANCE = (
    "dists_package", "dists_source_sha256", "dists_weights_sha256", "vgg_checkpoint_sha256",
    "dists_roi_context_px", "scikit_image_version", "color_space",
)


@dataclass
class CaseScores:
    artwork_id: str
    stratum: str
    values: dict[tuple[str, int], np.ndarray] = field(default_factory=dict)


def load_cases(report: dict) -> dict[str, CaseScores]:
    cases = {}
    for row in report["rows"]:
        case_id, artwork, stratum = (row[key] for key in ("case_id", "artwork_id", "stratum"))
        if not case_id or not artwork or stratum not in STRATA:
            raise ValueError(f"Invalid artwork identity in diagnostic case {case_id}")
        case = cases.setdefault(case_id, CaseScores(artwork, stratum))
        key = row["model"], row["seed"]
        if (case.artwork_id, case.stratum) != (artwork, stratum) or key in case.values:
            raise ValueError(f"Duplicate or inconsistent diagnostic row {case_id}/{key}")
        values = np.asarray([row[metric] for metric in METRICS], dtype=np.float64)
        if not np.isfinite(values).all():
            raise ValueError(f"Nonfinite diagnostic row {case_id}/{key}")
        case.values[key] = values
    return cases


def summarize(observations, models, reference):
    n = len(observations)
    summary = {"n_artworks": n, "reference_model": reference, "metrics": {}}
    if not n:
        return summary

    values = np.stack([scores for _, scores in observations])
    means = values.mean(axis=0)
    ref_index = models.index(reference)
    differences = values - values[:, ref_index : ref_index + 1, :]
    differences_mean = differences.mean(axis=0)
    intervals = None
    if n >= 2:
        rng = np.random.default_rng(BOOTSTRAP_SEED)
        sample = rng.integers(n, size=(N_BOOTSTRAPS, n))
        intervals = np.percentile(differences[sample].mean(axis=1), [2.5, 97.5], axis=0)

    for metric_index, metric in enumerate(METRICS):
        summary["metrics"][metric] = {
            "model_means": {model: float(means[i, metric_index]) for i, model in enumerate(models)},
            "difference_from_reference": {
                model: {
                    "mean": float(differences_mean[i, metric_index]),
                    "ci95": intervals[:, i, metric_index].tolist() if intervals is not None else None,
                }
                for i, model in enumerate(models) if model != reference
            },
        }
    return summary


def summarize_by_stratum(observations, models, reference):
    return {
        "overall": summarize(observations, models, reference),
        "by_stratum": {
            stratum: summarize([item for item in observations if item[0] == stratum], models, reference)
            for stratum in STRATA
        },
    }


def require_single_case_per_artwork(cases):
    if len({case.artwork_id for case in cases.values()}) != len(cases):
        raise ValueError("Expected one frozen center-mask case per artwork.")


def baseline_summary(baseline):
    require_single_case_per_artwork(baseline)
    expected = (("lama", PAIRED_SEED), *(("sdxl", seed) for seed in SEEDS))
    observations = []
    seed_observations = []
    incomplete_cases = []
    for case_id, case in sorted(baseline.items()):
        if set(case.values) - set(expected):
            raise ValueError(f"Unexpected baseline model or seed in {case_id}")
        lama, sdxl = case.values.get(expected[0]), case.values.get(("sdxl", PAIRED_SEED))
        if lama is not None and sdxl is not None:
            seed_observations.append((case.stratum, np.stack((lama, sdxl))))
        if not all(key in case.values for key in expected):
            incomplete_cases.append(case_id)
            continue
        diffusion_mean = np.mean([case.values[key] for key in expected[1:]], axis=0)
        observations.append((case.stratum, np.stack((lama, diffusion_mean))))
    report = summarize_by_stratum(observations, ("lama", "sdxl"), "lama")
    report.update(expected_artworks=len(STRATA) * WORKS_PER_STRATUM,
                  diffusion_seeds=list(SEEDS), incomplete_observed_cases=incomplete_cases)
    return report, summarize_by_stratum(seed_observations, ("lama", "sdxl"), "lama")


def sensitivity_summary(baseline, followup):
    require_single_case_per_artwork(followup)
    alternatives = {model: ([], []) for model in SENSITIVITY_MODELS}
    missing_baseline = {model: [] for model in SENSITIVITY_MODELS}
    for case_id, case in sorted(followup.items()):
        original = baseline.get(case_id)
        if original is None or (original.artwork_id, original.stratum) != (case.artwork_id, case.stratum):
            raise ValueError(f"Sensitivity case does not match the frozen baseline: {case_id}")
        for (model, seed), candidate in case.values.items():
            if model not in alternatives or seed != PAIRED_SEED:
                raise ValueError(f"Unexpected sensitivity model or seed in {case_id}: {model}/{seed}")
            sdxl = original.values.get(("sdxl", PAIRED_SEED))
            lama = original.values.get(("lama", PAIRED_SEED))
            vs_sdxl, vs_lama = alternatives[model]
            if sdxl is None:
                missing_baseline[model].append(case_id)
            else:
                vs_sdxl.append((case.stratum, np.stack((sdxl, candidate))))
            if lama is not None:
                vs_lama.append((case.stratum, np.stack((lama, candidate))))

    return {
        model: {
            "seed": PAIRED_SEED,
            "expected_artworks": len(STRATA) * WORKS_PER_STRATUM,
            "missing_same_seed_sdxl_baseline": missing_baseline[model],
            "vs_baseline": summarize_by_stratum(vs_sdxl, ("sdxl", model), "sdxl"),
            "vs_lama": summarize_by_stratum(vs_lama, ("lama", model), "lama"),
        }
        for model, (vs_sdxl, vs_lama) in alternatives.items()
    }


def match_native_plan(plan):
    planned_cases = {}
    conditions_by_artwork = {}
    strata_by_artwork = {}
    for case in plan["cases"]:
        case_id, artwork, stratum = (case[key] for key in ("case_id", "artwork_id", "stratum"))
        condition = case["family"], float(case["target_area"])
        if case_id in planned_cases or condition not in CONDITIONS or stratum not in STRATA:
            raise ValueError(f"Invalid or duplicate native case {case_id}")
        planned_cases[case_id] = artwork, stratum, condition
        strata_by_artwork.setdefault(artwork, stratum)
        conditions = conditions_by_artwork.setdefault(artwork, set())
        if strata_by_artwork[artwork] != stratum or condition in conditions:
            raise ValueError(f"Invalid or repeated native condition for {artwork}: {condition}")
        conditions.add(condition)
    if not conditions_by_artwork or any(conditions != set(CONDITIONS) for conditions in conditions_by_artwork.values()):
        raise ValueError("Every native artwork must be planned under all six conditions.")
    return planned_cases, strata_by_artwork


def matched_native(cases, planned_cases, strata_by_artwork, models):
    reference = "lama" if "lama" in models else models[0] if models else None
    scores_by_artwork = {}
    scores_by_condition = {condition: [] for condition in CONDITIONS}
    for case_id, case in sorted(cases.items()):
        keys = [(model, PAIRED_SEED) for model in models]
        if not keys or not all(key in case.values for key in keys):
            continue
        artwork, stratum, condition = planned_cases[case_id]
        scores = np.stack([case.values[key] for key in keys])
        scores_by_artwork.setdefault(artwork, {})[condition] = scores
        scores_by_condition[condition].append((stratum, scores))
    complete = [artwork for artwork, scores in scores_by_artwork.items() if len(scores) == len(CONDITIONS)]
    observations = [
        (strata_by_artwork[artwork], np.mean([scores_by_artwork[artwork][condition] for condition in CONDITIONS], axis=0))
        for artwork in sorted(complete)
    ]
    return {
        "models": list(models),
        "matched_cases": sum(len(scores) for scores in scores_by_condition.values()),
        "matched_cases_in_overall": len(complete) * len(CONDITIONS),
        "artworks_without_all_matched_conditions": sorted(set(strata_by_artwork) - set(complete)),
        **summarize_by_stratum(observations, models, reference),
        "by_condition": [
            {
                "family": family, "target_area": area,
                **summarize_by_stratum(scores, models, reference),
            }
            for (family, area), scores in scores_by_condition.items()
        ],
    }


def native_summary(cases, plan):
    planned_cases, strata_by_artwork = match_native_plan(plan)
    counts = dict.fromkeys(NATIVE_MODELS, 0)
    for case_id, case in cases.items():
        if case_id not in planned_cases or planned_cases[case_id][:2] != (case.artwork_id, case.stratum):
            raise ValueError(f"Unexpected native diagnostic case {case_id}")
        for model, seed in case.values:
            if model not in NATIVE_MODELS or seed != PAIRED_SEED:
                raise ValueError(f"Unexpected native model or seed in {case_id}: {model}/{seed}")
            counts[model] += 1
    available = tuple(model for model in NATIVE_MODELS if counts[model])
    matched = matched_native(cases, planned_cases, strata_by_artwork, available)
    report = {
        "seed": PAIRED_SEED,
        "planned_cases": len(planned_cases),
        "planned_artworks": len(strata_by_artwork),
        "counts_by_model": counts,
        "common_matched_cases": matched["matched_cases"],
        "all_planned_models_matched_cases": matched["matched_cases"] if available == NATIVE_MODELS else 0,
        "comparison": matched,
    }
    if available != ("lama", "sdxl") and {"lama", "sdxl"}.issubset(available):
        report["lama_sdxl"] = matched_native(cases, planned_cases, strata_by_artwork, ("lama", "sdxl"))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--sensitivity", type=Path, required=True)
    parser.add_argument("--native", type=Path)
    parser.add_argument("--native-plan", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="New summary JSON")
    args = parser.parse_args()
    if args.native is not None and args.native_plan is None:
        parser.error("--native requires --native-plan")
    if args.output.exists():
        parser.error("--output must be a new file")

    paths = {"baseline": args.baseline, "sensitivity": args.sensitivity}
    if args.native is not None:
        paths["native"] = args.native
    inputs = {name: read_json(path) for name, path in paths.items()}
    for name, other in inputs.items():
        for key in PROVENANCE:
            reference = inputs["baseline"].get(key)
            if reference is not None and key in other and other[key] != reference:
                raise ValueError(f"Metric provenance mismatch for {name}: {key}")

    baseline_cases = load_cases(inputs["baseline"])
    baseline, seed_comparison = baseline_summary(baseline_cases)
    sensitivity = sensitivity_summary(baseline_cases, load_cases(inputs["sensitivity"]))
    sensitivity["baseline_seed_vs_lama"] = seed_comparison
    native = None
    inputs_sha256 = {name: sha256(path) for name, path in paths.items()}
    if args.native is not None:
        digest = sha256(args.native_plan)
        if inputs["native"].get("prepared_sha256", digest) != digest:
            raise ValueError("Native diagnostic artifact does not match --native-plan")
        inputs_sha256["native_plan"] = digest
        native = native_summary(load_cases(inputs["native"]), read_json(args.native_plan))

    report = {
        "protocol": "followup-paired-summary-v1",
        "inputs_sha256": inputs_sha256,
        "bootstrap": {"unit": "artwork", "resamples": N_BOOTSTRAPS, "seed": BOOTSTRAP_SEED,
                      "interval": "95% percentile, unadjusted"},
        "difference_direction": "candidate minus the reference listed for each comparison",
        "baseline": baseline,
        "sensitivity": sensitivity,
        "native": native,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = NamedTemporaryFile(dir=args.output.parent, delete=False, mode="w", encoding="utf-8")
    staged = Path(temporary.name)
    try:
        with temporary:
            json.dump(report, temporary, ensure_ascii=False, indent=2, allow_nan=False)
            temporary.write("\n")
        os.link(staged, args.output)
    finally:
        staged.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
