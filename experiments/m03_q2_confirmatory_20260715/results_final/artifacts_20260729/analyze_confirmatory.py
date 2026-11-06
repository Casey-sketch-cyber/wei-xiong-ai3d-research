from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
import statsmodels.formula.api as smf


BOOTSTRAP_SEED = 20260715
BOOTSTRAP_REPLICATES = 50000
ALPHA = 0.01
MODELS = ("triposr", "instantmesh", "hunyuan21", "trellis")
STOCHASTIC_MODELS = ("instantmesh", "hunyuan21", "trellis")
STYLES = ("edge", "flat", "low_detail", "sketch", "watercolor")
VIEW_IDS = ("azimuth_minus_30", "azimuth_plus_30")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluation-root", type=Path, required=True)
    parser.add_argument("--render-diagnostics", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--bootstrap-replicates", type=int, default=BOOTSTRAP_REPLICATES)
    return parser.parse_args()


def atomic_json(path: Path, payload: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def stable_seed(label: str) -> int:
    return BOOTSTRAP_SEED ^ int(hashlib.sha256(label.encode("utf-8")).hexdigest()[:8], 16)


def bootstrap_mean(values: np.ndarray, replicates: int, label: str) -> dict:
    values = np.asarray(values, dtype=np.float64)
    values = values[np.isfinite(values)]
    if len(values) < 2:
        raise ValueError(f"Insufficient values for {label}: {len(values)}")
    rng = np.random.default_rng(stable_seed(label))
    means = np.empty(replicates, dtype=np.float64)
    chunk = 5000
    for start in range(0, replicates, chunk):
        stop = min(start + chunk, replicates)
        indices = rng.integers(0, len(values), size=(stop - start, len(values)))
        means[start:stop] = values[indices].mean(axis=1)
    lower, upper = np.quantile(means, [ALPHA / 2.0, 1.0 - ALPHA / 2.0])
    nonpositive = int(np.sum(means <= 0))
    nonnegative = int(np.sum(means >= 0))
    p_value = min(1.0, 2.0 * min(nonpositive + 1, nonnegative + 1) / (replicates + 1))
    return {
        "n_objects": int(len(values)),
        "mean": float(values.mean()),
        "median": float(np.median(values)),
        "sd": float(values.std(ddof=1)),
        "standardized_mean": float(values.mean() / values.std(ddof=1))
        if values.std(ddof=1) > 0
        else math.nan,
        "positive_fraction": float(np.mean(values > 0)),
        "ci99_low": float(lower),
        "ci99_high": float(upper),
        "p_two_sided": float(p_value),
        "bootstrap_replicates": int(replicates),
    }


def holm_adjust(p_values: list[float]) -> list[float]:
    count = len(p_values)
    order = np.argsort(p_values)
    adjusted = np.empty(count, dtype=np.float64)
    running = 0.0
    for rank, index in enumerate(order):
        candidate = min(1.0, (count - rank) * float(p_values[index]))
        running = max(running, candidate)
        adjusted[index] = running
    return adjusted.tolist()


def read_evaluations(root: Path) -> pd.DataFrame:
    frames = []
    for model in MODELS:
        path = root / model / "evaluation_results.csv"
        if not path.exists():
            raise FileNotFoundError(path)
        frame = pd.read_csv(path)
        if set(frame["model"].unique()) != {model}:
            raise ValueError(f"Unexpected model labels in {path}")
        frames.append(frame)
    data = pd.concat(frames, ignore_index=True)
    data = data[data["evaluation_status"] == "success"].copy()
    data["seed"] = data["seed"].astype(int)
    return data


def pair_with_photo(data: pd.DataFrame, split: str) -> pd.DataFrame:
    subset = data[data["split"] == split].copy()
    keys = ["model", "object_id", "seed", "view_id"]
    metrics = [
        "fscore_0.05",
        "fscore_0.1",
        "voxel_iou",
        "solid_volume_ratio",
        "z_extent_ratio",
        "chamfer_l2",
        "normal_consistency",
        "watertight",
        "components",
        "boundary_edges",
        "nonmanifold_edges",
    ]
    photos = subset[subset["style"] == "photo"][keys + metrics].copy()
    photos = photos.rename(columns={metric: f"photo_{metric}" for metric in metrics})
    stylized = subset[subset["style"] != "photo"].copy()
    paired = stylized.merge(photos, on=keys, how="inner", validate="many_to_one")
    paired["delta_fscore_0.05"] = paired["fscore_0.05"] - paired["photo_fscore_0.05"]
    paired["delta_fscore_0.1"] = paired["fscore_0.1"] - paired["photo_fscore_0.1"]
    paired["delta_voxel_iou"] = paired["voxel_iou"] - paired["photo_voxel_iou"]
    paired["rg"] = paired["delta_fscore_0.05"] - paired["delta_voxel_iou"]
    paired["rg_fscore_0.1"] = paired["delta_fscore_0.1"] - paired["delta_voxel_iou"]
    paired["surface_degradation"] = -paired["delta_fscore_0.05"]
    paired["solid_degradation"] = -paired["delta_voxel_iou"]
    paired["delta_watertight"] = (
        paired["watertight"].astype(float) - paired["photo_watertight"].astype(float)
    )
    paired["delta_components"] = paired["components"] - paired["photo_components"]
    paired["delta_boundary_edges"] = paired["boundary_edges"] - paired["photo_boundary_edges"]
    return paired


def object_average(paired: pd.DataFrame) -> pd.DataFrame:
    numeric = [
        "delta_fscore_0.05",
        "delta_fscore_0.1",
        "delta_voxel_iou",
        "rg",
        "rg_fscore_0.1",
        "surface_degradation",
        "solid_degradation",
        "delta_watertight",
        "delta_components",
        "delta_boundary_edges",
    ]
    return (
        paired.groupby(["model", "object_id", "style"], as_index=False)[numeric]
        .mean()
        .sort_values(["model", "object_id", "style"])
    )


def photo_baseline_tests(data: pd.DataFrame, replicates: int) -> pd.DataFrame:
    metrics = ("fscore_0.05", "fscore_0.1", "voxel_iou", "chamfer_l2", "normal_consistency")
    topology_metrics = ["watertight", "components", "boundary_edges", "nonmanifold_edges"]
    photos = data[(data["split"] == "main") & (data["style"] == "photo")].copy()
    averaged = photos.groupby(["model", "object_id"], as_index=False)[list(metrics)].mean()
    rows = []
    for model in MODELS:
        subset = averaged[averaged["model"] == model]
        for metric in metrics:
            rows.append(
                {
                    "model": model,
                    "metric": metric,
                    **bootstrap_mean(
                        subset[metric].to_numpy(),
                        replicates,
                        f"photo_baseline:{model}:{metric}",
                    ),
                }
            )
    topology = (
        photos.groupby(["model", "object_id"], as_index=False)[topology_metrics]
        .mean()
        .groupby("model", as_index=False)[topology_metrics]
        .mean()
    )
    for row in topology.to_dict("records"):
        for metric in ("watertight", "components", "boundary_edges", "nonmanifold_edges"):
            rows.append(
                {
                    "model": row["model"],
                    "metric": f"photo_{metric}",
                    "n_objects": 120,
                    "mean": float(row[metric]),
                    "median": np.nan,
                    "sd": np.nan,
                    "standardized_mean": np.nan,
                    "positive_fraction": np.nan,
                    "ci99_low": np.nan,
                    "ci99_high": np.nan,
                    "p_two_sided": np.nan,
                    "bootstrap_replicates": 0,
                }
            )
    return pd.DataFrame(rows)


def style_tests(
    averaged: pd.DataFrame, replicates: int, metric: str = "rg"
) -> pd.DataFrame:
    rows = []
    for model in MODELS:
        for style in STYLES:
            values = averaged.loc[
                (averaged["model"] == model) & (averaged["style"] == style), metric
            ].to_numpy()
            result = bootstrap_mean(values, replicates, f"main:{model}:{style}:{metric}")
            rows.append({"model": model, "style": style, "metric": metric, **result})
    return pd.DataFrame(rows)


def primary_tests(style_frame: pd.DataFrame) -> pd.DataFrame:
    primary = style_frame[style_frame["style"] == "sketch"].copy()
    primary = primary.set_index("model").loc[list(MODELS)].reset_index()
    primary["p_holm"] = holm_adjust(primary["p_two_sided"].tolist())
    primary["passes"] = (primary["ci99_low"] > 0) & (primary["p_holm"] < ALPHA)
    return primary


def seed_analysis(main_paired: pd.DataFrame, replicates: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    sketch = main_paired[
        (main_paired["style"] == "sketch")
        & (main_paired["model"].isin(STOCHASTIC_MODELS))
    ].copy()
    estimates = []
    reliability = []
    for model in STOCHASTIC_MODELS:
        model_rows = sketch[sketch["model"] == model]
        for seed in sorted(model_rows["seed"].unique()):
            values = model_rows.loc[model_rows["seed"] == seed, "rg"].to_numpy()
            estimates.append(
                {
                    "model": model,
                    "seed": int(seed),
                    **bootstrap_mean(values, replicates, f"seed:{model}:{seed}:sketch"),
                }
            )
        pivot = model_rows.pivot(index="object_id", columns="seed", values="rg")
        if pivot.shape[1] != 2:
            raise ValueError(f"Expected two seeds for {model}, found {pivot.columns.tolist()}")
        first, second = pivot.columns.tolist()
        x = pivot[first].to_numpy()
        y = pivot[second].to_numpy()
        reliability.append(
            {
                "model": model,
                "seed_a": int(first),
                "seed_b": int(second),
                "n_objects": int(len(pivot)),
                "pearson_r": float(pearsonr(x, y).statistic),
                "spearman_rho": float(spearmanr(x, y).statistic),
                "object_sign_agreement": float(np.mean(np.sign(x) == np.sign(y))),
                "mean_positive_both": bool(x.mean() > 0 and y.mean() > 0),
            }
        )
    return pd.DataFrame(estimates), pd.DataFrame(reliability)


def view_analysis(data: pd.DataFrame, replicates: int) -> pd.DataFrame:
    paired = pair_with_photo(data, "view")
    paired = paired[paired["style"].isin(("edge", "sketch"))]
    rows = []
    for (model, view_id, style), group in paired.groupby(["model", "view_id", "style"]):
        result = bootstrap_mean(
            group["rg"].to_numpy(), replicates, f"view:{model}:{view_id}:{style}"
        )
        rows.append({"model": model, "view_id": view_id, "style": style, **result})
    return pd.DataFrame(rows).sort_values(["model", "view_id", "style"])


def severity_analysis(data: pd.DataFrame, replicates: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    main = data[data["split"] == "main"].copy()
    severity = data[data["split"] == "severity"].copy()
    selected = []
    for model in MODELS:
        seed = -1 if model == "triposr" else 20260715
        selected.append(
            main[
                (main["model"] == model)
                & (main["seed"] == seed)
                & (main["style"].isin(("photo", "edge", "sketch")))
            ]
        )
        selected.append(
            severity[(severity["model"] == model) & (severity["seed"] == seed)]
        )
    combined = pd.concat(selected, ignore_index=True)
    photos = combined[combined["style"] == "photo"][
        ["model", "object_id", "seed", "fscore_0.05", "voxel_iou"]
    ].rename(
        columns={"fscore_0.05": "photo_fscore_0.05", "voxel_iou": "photo_voxel_iou"}
    )
    styles = combined[combined["style"].isin(("edge", "sketch"))].copy()
    styles = styles.merge(
        photos, on=["model", "object_id", "seed"], how="inner", validate="many_to_one"
    )
    styles["rg"] = (
        styles["fscore_0.05"]
        - styles["photo_fscore_0.05"]
        - (styles["voxel_iou"] - styles["photo_voxel_iou"])
    )
    level = {"low": 0, "medium": 1, "high": 2}
    styles["severity_level"] = styles["severity"].map(level)
    pivot = styles.pivot_table(
        index=["model", "object_id", "style"],
        columns="severity",
        values="rg",
        aggfunc="first",
    ).reset_index()
    required = {"low", "medium", "high"}
    if not required.issubset(pivot.columns):
        raise ValueError(f"Missing severity columns: {required - set(pivot.columns)}")
    pivot["slope"] = (pivot["high"] - pivot["low"]) / 2.0
    rows = []
    for (model, style), group in pivot.groupby(["model", "style"]):
        rows.append(
            {
                "model": model,
                "style": style,
                **bootstrap_mean(
                    group["slope"].to_numpy(), replicates, f"severity:{model}:{style}"
                ),
            }
        )
    return styles, pd.DataFrame(rows).sort_values(["model", "style"])


def topology_summary(averaged: pd.DataFrame) -> pd.DataFrame:
    return (
        averaged.groupby(["model", "style"], as_index=False)[
            ["delta_watertight", "delta_components", "delta_boundary_edges"]
        ]
        .agg(["mean", "median"])
    )


def absolute_change_tests(averaged: pd.DataFrame, replicates: int) -> pd.DataFrame:
    metrics = (
        "delta_fscore_0.05",
        "delta_fscore_0.1",
        "delta_voxel_iou",
        "surface_degradation",
        "solid_degradation",
    )
    rows = []
    for model in MODELS:
        for style in STYLES:
            subset = averaged[(averaged["model"] == model) & (averaged["style"] == style)]
            for metric in metrics:
                rows.append(
                    {
                        "model": model,
                        "style": style,
                        "metric": metric,
                        **bootstrap_mean(
                            subset[metric].to_numpy(),
                            replicates,
                            f"absolute:{model}:{style}:{metric}",
                        ),
                    }
                )
    return pd.DataFrame(rows)


def render_diagnostic_analysis(path: Path, replicates: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    data = pd.read_csv(path)
    data = data[data["render_status"] == "success"].copy()
    keys = ["model", "object_id", "seed"]
    metrics = ["silhouette_iou_mean", "normal_render_similarity_mean"]
    photos = data[data["style"] == "photo"][keys + metrics].rename(
        columns={metric: f"photo_{metric}" for metric in metrics}
    )
    stylized = data[data["style"] != "photo"].copy()
    paired = stylized.merge(photos, on=keys, how="inner", validate="many_to_one")
    for metric in metrics:
        paired[f"delta_{metric}"] = paired[metric] - paired[f"photo_{metric}"]
    averaged = (
        paired.groupby(["model", "object_id", "style"], as_index=False)[
            [f"delta_{metric}" for metric in metrics]
        ]
        .mean()
        .sort_values(["model", "object_id", "style"])
    )
    rows = []
    for model in MODELS:
        for style in STYLES:
            subset = averaged[(averaged["model"] == model) & (averaged["style"] == style)]
            for metric in metrics:
                delta = f"delta_{metric}"
                rows.append(
                    {
                        "model": model,
                        "style": style,
                        "diagnostic": metric,
                        **bootstrap_mean(
                            subset[delta].to_numpy(),
                            replicates,
                            f"render:{model}:{style}:{metric}",
                        ),
                    }
                )
    return averaged, pd.DataFrame(rows)


def interaction_test(averaged: pd.DataFrame, metric: str) -> dict:
    frame = averaged.rename(columns={metric: "outcome"}).copy()
    fit = smf.ols("outcome ~ C(model) * C(style)", data=frame).fit(
        cov_type="cluster", cov_kwds={"groups": frame["object_id"]}
    )
    names = fit.model.exog_names
    interaction_indices = [
        index
        for index, name in enumerate(names)
        if "C(model)" in name and "C(style)" in name and ":" in name
    ]
    if not interaction_indices:
        raise ValueError("No model-by-style interaction terms in fitted model")
    restriction = np.zeros((len(interaction_indices), len(names)), dtype=np.float64)
    for row_index, column_index in enumerate(interaction_indices):
        restriction[row_index, column_index] = 1.0
    test = fit.wald_test(restriction, scalar=True)
    return {
        "metric": metric,
        "n_rows": int(len(frame)),
        "n_object_clusters": int(frame["object_id"].nunique()),
        "interaction_df": int(len(interaction_indices)),
        "wald_statistic": float(np.asarray(test.statistic).squeeze()),
        "p_value": float(np.asarray(test.pvalue).squeeze()),
        "covariance": "object-cluster robust",
        "formula": "RG ~ C(model) * C(style)",
    }


def markdown_report(gate: dict, primary: pd.DataFrame, supporting: dict) -> str:
    lines = [
        "# Confirmatory Evidence Report",
        "",
        f"Primary models passing: {gate['primary_models_passing']} / 4.",
        f"Supporting criteria passing: {gate['supporting_criteria_passing']} / 4.",
        f"Q2 publication evidence gate: {'PASS' if gate['q2_gate_passes'] else 'FAIL'}.",
        "",
        "## Primary sketch RG",
        "",
        "| Model | Mean RG | 99% CI | Holm p | Pass |",
        "|---|---:|---:|---:|:---:|",
    ]
    for row in primary.to_dict("records"):
        lines.append(
            f"| {row['model']} | {row['mean']:.4f} | "
            f"[{row['ci99_low']:.4f}, {row['ci99_high']:.4f}] | "
            f"{row['p_holm']:.6g} | {'yes' if row['passes'] else 'no'} |"
        )
    lines.extend(["", "## Supporting criteria", ""])
    for name, result in supporting.items():
        lines.append(f"- {name}: {'pass' if result['passes'] else 'fail'} ({result['detail']})")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    data = read_evaluations(args.evaluation_root)
    main_paired = pair_with_photo(data, "main")
    averaged = object_average(main_paired)
    photo_baselines = photo_baseline_tests(data, args.bootstrap_replicates)

    main_paired.to_csv(args.output_root / "paired_main_seed_specific.csv", index=False)
    averaged.to_csv(args.output_root / "paired_main_object_averaged.csv", index=False)
    photo_baselines.to_csv(args.output_root / "photo_baseline_summary.csv", index=False)

    styles = style_tests(averaged, args.bootstrap_replicates, "rg")
    primary = primary_tests(styles)
    styles_f10 = style_tests(averaged, args.bootstrap_replicates, "rg_fscore_0.1")
    primary_f10 = primary_tests(styles_f10)
    absolute_changes = absolute_change_tests(averaged, args.bootstrap_replicates)
    styles.to_csv(args.output_root / "style_rg_tests.csv", index=False)
    primary.to_csv(args.output_root / "primary_sketch_tests.csv", index=False)
    styles_f10.to_csv(args.output_root / "style_rg_fscore_0.1_tests.csv", index=False)
    primary_f10.to_csv(
        args.output_root / "primary_sketch_fscore_0.1_sensitivity.csv", index=False
    )
    absolute_changes.to_csv(args.output_root / "absolute_metric_changes.csv", index=False)

    seed_estimates, seed_reliability = seed_analysis(main_paired, args.bootstrap_replicates)
    seed_estimates.to_csv(args.output_root / "seed_specific_sketch_tests.csv", index=False)
    seed_reliability.to_csv(args.output_root / "seed_reliability.csv", index=False)

    views = view_analysis(data, args.bootstrap_replicates)
    views.to_csv(args.output_root / "view_generalization.csv", index=False)
    severity_records, severity = severity_analysis(data, args.bootstrap_replicates)
    severity_records.to_csv(args.output_root / "severity_paired_records.csv", index=False)
    severity.to_csv(args.output_root / "severity_trends.csv", index=False)
    topology_summary(averaged).to_csv(args.output_root / "topology_changes.csv", index=False)
    render_paired, render_tests = render_diagnostic_analysis(
        args.render_diagnostics, args.bootstrap_replicates
    )
    render_paired.to_csv(args.output_root / "render_diagnostic_paired_changes.csv", index=False)
    render_tests.to_csv(args.output_root / "render_diagnostic_style_tests.csv", index=False)

    interactions = [
        interaction_test(averaged, "rg"),
        interaction_test(averaged, "rg_fscore_0.1"),
    ]
    adjusted = holm_adjust([row["p_value"] for row in interactions])
    for row, p_holm in zip(interactions, adjusted):
        row["p_holm"] = p_holm
    atomic_json(args.output_root / "interaction_tests.json", interactions)

    primary_count = int(primary["passes"].sum())
    seed_models = int(seed_reliability["mean_positive_both"].sum())
    view_sketch = views[views["style"] == "sketch"]
    view_models = int(
        sum(
            len(group) == 2 and bool((group["mean"] > 0).all())
            for _, group in view_sketch.groupby("model")
        )
    )
    sketch_severity = severity[severity["style"] == "sketch"]
    severity_models = int((sketch_severity["mean"] > 0).sum())
    interaction_pass = bool(interactions[0]["p_holm"] < ALPHA)
    supporting = {
        "both_seed_directions": {
            "passes": seed_models >= 2,
            "detail": f"{seed_models} stochastic models positive in both seeds",
        },
        "both_view_directions": {
            "passes": view_models >= 2,
            "detail": f"{view_models} models positive at both additional views",
        },
        "positive_severity_slope": {
            "passes": severity_models >= 2,
            "detail": f"{severity_models} models with positive sketch slope",
        },
        "model_style_metric_interaction": {
            "passes": interaction_pass,
            "detail": f"primary Holm p={interactions[0]['p_holm']:.6g}",
        },
    }
    supporting_count = sum(int(row["passes"]) for row in supporting.values())
    gate = {
        "primary_models_passing": primary_count,
        "primary_requirement_passes": primary_count >= 2,
        "supporting_criteria": supporting,
        "supporting_criteria_passing": supporting_count,
        "supporting_requirement_passes": supporting_count >= 2,
        "q2_gate_passes": primary_count >= 2 and supporting_count >= 2,
        "alpha": ALPHA,
        "bootstrap_seed": BOOTSTRAP_SEED,
        "bootstrap_replicates": args.bootstrap_replicates,
        "n_main_objects": int(averaged["object_id"].nunique()),
    }
    atomic_json(args.output_root / "publication_evidence_gate.json", gate)
    (args.output_root / "CONFIRMATORY_RESULTS_REPORT.md").write_text(
        markdown_report(gate, primary, supporting), encoding="utf-8"
    )
    print(json.dumps(gate, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
