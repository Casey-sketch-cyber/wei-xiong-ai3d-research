from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd


STYLES = ("edge", "flat", "low_detail", "sketch", "watercolor")
MODELS = ("triposr", "instantmesh", "hunyuan21")
BOOTSTRAP_REPLICATES = 5000


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--bootstrap", type=int, default=BOOTSTRAP_REPLICATES)
    return parser.parse_args()


def stable_seed(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)


def atomic_json(path: Path, data: object) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def bootstrap_means(frame: pd.DataFrame, columns: list[str], key: str, count: int) -> dict:
    values = frame[columns].to_numpy(dtype=float)
    rng = np.random.default_rng(stable_seed(key))
    indices = rng.integers(0, len(values), size=(count, len(values)))
    boot = values[indices].mean(axis=1)
    result = {}
    for index, column in enumerate(columns):
        result[column] = {
            "mean": float(values[:, index].mean()),
            "ci_low": float(np.quantile(boot[:, index], 0.025)),
            "ci_high": float(np.quantile(boot[:, index], 0.975)),
        }
    return result


def prepare_pairs(data: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    metrics = [
        "fscore_0.05",
        "chamfer_l2",
        "voxel_iou",
        "absolute_solid_volume_error",
        "solid_volume_ratio",
        "depth_extent_error",
        "normal_consistency",
    ]
    averaged = (
        data.groupby(["model", "object_id", "object_name", "style"], as_index=False)[metrics]
        .mean()
    )
    photo = averaged[averaged["style"] == "photo"].drop(columns="style")
    styled = averaged[averaged["style"] != "photo"]
    paired = styled.merge(
        photo,
        on=["model", "object_id", "object_name"],
        suffixes=("", "_photo"),
        validate="many_to_one",
    )
    paired["delta_fscore"] = paired["fscore_0.05"] - paired["fscore_0.05_photo"]
    paired["delta_voxel_iou"] = paired["voxel_iou"] - paired["voxel_iou_photo"]
    paired["delta_abs_volume_error"] = (
        paired["absolute_solid_volume_error"]
        - paired["absolute_solid_volume_error_photo"]
    )
    paired["delta_chamfer_improvement"] = (
        paired["chamfer_l2_photo"] - paired["chamfer_l2"]
    )
    paired["metric_family_contrast"] = (
        paired["delta_fscore"] - paired["delta_voxel_iou"]
    )
    return averaged, paired


def reversal_analysis(paired: pd.DataFrame, bootstrap: int) -> list[dict]:
    rows = []
    columns = [
        "delta_fscore",
        "delta_voxel_iou",
        "delta_abs_volume_error",
        "delta_chamfer_improvement",
    ]
    for (model, style), frame in paired.groupby(["model", "style"]):
        estimates = bootstrap_means(frame, columns, f"reversal:{model}:{style}", bootstrap)
        primary = (
            estimates["delta_fscore"]["ci_low"] > 0
            and estimates["delta_voxel_iou"]["ci_high"] < 0
        )
        volume_corroboration = (
            estimates["delta_fscore"]["ci_low"] > 0
            and estimates["delta_abs_volume_error"]["ci_low"] > 0
        )
        chamfer_corroboration = (
            estimates["delta_chamfer_improvement"]["ci_low"] > 0
            and estimates["delta_voxel_iou"]["ci_high"] < 0
        )
        rows.append(
            {
                "model": model,
                "style": style,
                "objects": int(frame["object_id"].nunique()),
                **{
                    f"{metric}_{part}": value
                    for metric, estimate in estimates.items()
                    for part, value in estimate.items()
                },
                "primary_reversal": bool(primary),
                "volume_corroboration": bool(volume_corroboration),
                "chamfer_corroboration": bool(chamfer_corroboration),
            }
        )
    return rows


def rank_reversal_analysis(averaged: pd.DataFrame, bootstrap: int) -> list[dict]:
    rows = []
    for style in STYLES:
        subset = averaged[averaged["style"] == style]
        for model_a, model_b in itertools.combinations(sorted(subset["model"].unique()), 2):
            a = subset[subset["model"] == model_a][["object_id", "fscore_0.05", "voxel_iou"]]
            b = subset[subset["model"] == model_b][["object_id", "fscore_0.05", "voxel_iou"]]
            merged = a.merge(b, on="object_id", suffixes=("_a", "_b"), validate="one_to_one")
            merged["fscore_difference"] = merged["fscore_0.05_a"] - merged["fscore_0.05_b"]
            merged["voxel_iou_difference"] = merged["voxel_iou_a"] - merged["voxel_iou_b"]
            estimates = bootstrap_means(
                merged,
                ["fscore_difference", "voxel_iou_difference"],
                f"rank:{style}:{model_a}:{model_b}",
                bootstrap,
            )
            fscore = estimates["fscore_difference"]
            voxel = estimates["voxel_iou_difference"]
            fscore_significant = fscore["ci_low"] > 0 or fscore["ci_high"] < 0
            voxel_significant = voxel["ci_low"] > 0 or voxel["ci_high"] < 0
            opposite = np.sign(fscore["mean"]) == -np.sign(voxel["mean"])
            rows.append(
                {
                    "style": style,
                    "model_a": model_a,
                    "model_b": model_b,
                    "objects": int(len(merged)),
                    **{
                        f"{metric}_{part}": value
                        for metric, estimate in estimates.items()
                        for part, value in estimate.items()
                    },
                    "stable_rank_reversal": bool(
                        fscore_significant and voxel_significant and opposite
                    ),
                }
            )
    return rows


def interaction_analysis(paired: pd.DataFrame) -> list[dict]:
    rows = []
    for (model, style), frame in paired.groupby(["model", "style"]):
        contrast = frame["metric_family_contrast"].to_numpy(dtype=float)
        standard_deviation = float(np.std(contrast, ddof=1))
        effect = float(np.mean(contrast) / standard_deviation) if standard_deviation > 0 else 0.0
        photo_surface = float(np.median(frame["fscore_0.05_photo"]))
        photo_solid = float(np.median(frame["voxel_iou_photo"]))
        baseline_adequate = photo_surface >= 0.15 and photo_solid >= 0.05
        rows.append(
            {
                "model": model,
                "style": style,
                "objects": int(len(frame)),
                "metric_family_contrast_mean": float(np.mean(contrast)),
                "cohen_dz": effect,
                "photo_fscore_median": photo_surface,
                "photo_voxel_iou_median": photo_solid,
                "photo_baseline_adequate": bool(baseline_adequate),
                "medium_effect": bool(effect >= 0.5 and baseline_adequate),
            }
        )
    return rows


def seed_consistency(data: pd.DataFrame) -> list[dict]:
    stochastic = data[data["seed"] >= 0].copy()
    rows = []
    for model in sorted(stochastic["model"].unique()):
        model_data = stochastic[stochastic["model"] == model]
        seeds = sorted(model_data["seed"].unique())
        if len(seeds) < 2:
            continue
        for style in STYLES:
            directions = []
            for seed in seeds:
                subset = model_data[model_data["seed"] == seed]
                photo = subset[subset["style"] == "photo"][["object_id", "fscore_0.05", "voxel_iou"]]
                target = subset[subset["style"] == style][["object_id", "fscore_0.05", "voxel_iou"]]
                merged = target.merge(photo, on="object_id", suffixes=("", "_photo"))
                delta_f = float((merged["fscore_0.05"] - merged["fscore_0.05_photo"]).mean())
                delta_iou = float((merged["voxel_iou"] - merged["voxel_iou_photo"]).mean())
                directions.append(
                    {
                        "seed": int(seed),
                        "delta_fscore": delta_f,
                        "delta_voxel_iou": delta_iou,
                        "direction": [int(np.sign(delta_f)), int(np.sign(delta_iou))],
                    }
                )
            consistent = all(item["direction"] == directions[0]["direction"] for item in directions[1:])
            rows.append(
                {
                    "model": model,
                    "style": style,
                    "consistent": bool(consistent),
                    "seed_results": json.dumps(directions, ensure_ascii=False),
                }
            )
    return rows


def main() -> int:
    args = parse_args()
    data = pd.read_csv(args.work / "evaluation_results.csv")
    data = data[data["evaluation_status"] == "success"].copy()
    available_models = sorted(data["model"].unique())
    if set(MODELS) - set(available_models):
        raise ValueError(f"Missing models: {sorted(set(MODELS) - set(available_models))}")
    averaged, paired = prepare_pairs(data)

    reversals = reversal_analysis(paired, args.bootstrap)
    ranks = rank_reversal_analysis(averaged, args.bootstrap)
    interactions = interaction_analysis(paired)
    seeds = seed_consistency(data)

    reversal_models = sorted({row["model"] for row in reversals if row["primary_reversal"]})
    gate_1 = len(reversal_models) >= 2
    stable_ranks = [row for row in ranks if row["stable_rank_reversal"]]
    gate_2 = bool(stable_ranks)
    medium_by_style = {
        style: sorted({row["model"] for row in interactions if row["style"] == style and row["medium_effect"]})
        for style in STYLES
    }
    gate_3_styles = {style: models for style, models in medium_by_style.items() if len(models) >= 2}
    gate_3 = bool(gate_3_styles)
    seed_frame = pd.DataFrame(seeds)
    model_seed_rates = (
        seed_frame.groupby("model")["consistent"].mean().to_dict() if len(seed_frame) else {}
    )
    gate_4 = bool(model_seed_rates) and all(rate >= 0.8 for rate in model_seed_rates.values())

    gates = {
        "gate_1_cross_model_primary_sign_reversal": {
            "passed": gate_1,
            "models": reversal_models,
            "criterion": "At least two models have a style whose cluster-bootstrap CI shows delta F-score > 0 and delta voxel IoU < 0.",
        },
        "gate_2_stable_model_rank_reversal": {
            "passed": gate_2,
            "cases": stable_ranks,
            "criterion": "A model pair has significant opposite orderings under F-score and voxel IoU for at least one style.",
        },
        "gate_3_medium_metric_family_by_style_effect": {
            "passed": gate_3,
            "styles": gate_3_styles,
            "criterion": "The same style has Cohen dz >= 0.5 for delta F-score minus delta voxel IoU in at least two models, with adequate photo baselines.",
        },
        "gate_4_seed_direction_consistency": {
            "passed": gate_4,
            "model_rates": {key: float(value) for key, value in model_seed_rates.items()},
            "criterion": "Each stochastic model preserves the sign pair of mean delta F-score and delta voxel IoU in at least 80% of styles.",
        },
    }
    passed_count = sum(item["passed"] for item in gates.values())
    decision = {
        "pilot_objects": int(data["object_id"].nunique()),
        "models": available_models,
        "evaluated_reconstructions": int(len(data)),
        "bootstrap_replicates": args.bootstrap,
        "gates": gates,
        "passed_gate_count": passed_count,
        "expand_to_100": passed_count >= 2,
        "decision_rule": "Expand only when at least two of the four frozen gates pass.",
    }
    atomic_json(args.work / "pilot_gate.json", decision)
    pd.DataFrame(reversals).to_csv(args.work / "reversal_bootstrap.csv", index=False)
    pd.DataFrame(ranks).to_csv(args.work / "rank_reversal_bootstrap.csv", index=False)
    pd.DataFrame(interactions).to_csv(args.work / "interaction_effects.csv", index=False)
    pd.DataFrame(seeds).to_csv(args.work / "seed_consistency.csv", index=False)
    paired.to_csv(args.work / "paired_style_changes.csv", index=False)

    lines = [
        "# M03 metric-validity pilot gate report",
        "",
        f"- Objects: {decision['pilot_objects']}",
        f"- Reconstructions: {decision['evaluated_reconstructions']}",
        f"- Bootstrap replicates: {args.bootstrap}",
        f"- Passed gates: {passed_count}/4",
        f"- Decision: {'EXPAND TO 100' if decision['expand_to_100'] else 'STOP AT 30'}",
        "",
        "## Frozen gates",
        "",
    ]
    for name, item in gates.items():
        lines.append(f"- {'PASS' if item['passed'] else 'FAIL'}: {name}")
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "The decision is mechanical. A TripoSR-only effect is not treated as a cross-model law, and no threshold is changed after inspecting the pilot.",
        ]
    )
    (args.work / "pilot_gate_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
