from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import binomtest, wilcoxon


PRIMARY_METHODS = [
    "no_repair",
    "visibility_max_only",
    "random_feasible",
    "generic_greedy",
    "simulated_annealing",
    "revealrepair_attributed",
]
OURS = "revealrepair_attributed"
SUCCESS_TOLERANCE = 0.005


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bootstrap", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=20260904)
    return parser.parse_args()


def read_rows(path: Path) -> list[dict[str, Any]]:
    numeric_int = {
        "severity",
        "seed",
        "hard_valid",
        "collision_count",
        "path_clearance_violations",
        "bounds_violations",
        "relation_violations",
        "edit_count",
        "evaluations",
        "base_seed",
        "route_samples",
        "surface_grid",
        "exhibit_count",
        "generation_attempt",
        "missed_violations",
        "leakage_violations",
        "reveal_order_inversions",
    }
    numeric_float = {
        "schedule_loss",
        "missed_loss",
        "leakage_loss",
        "satisfaction",
        "translation_cost",
        "yaw_cost",
        "edit_cost",
        "runtime_seconds",
    }
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        for key in numeric_int:
            if key in row and row[key] != "":
                row[key] = int(float(row[key]))
        for key in numeric_float:
            if key in row and row[key] != "":
                row[key] = float(row[key])
    return rows


def percentile_interval(values: np.ndarray, alpha: float = 0.05) -> list[float]:
    return [
        float(np.quantile(values, alpha / 2.0)),
        float(np.quantile(values, 1.0 - alpha / 2.0)),
    ]


def bootstrap_statistic(
    values: Iterable[float],
    statistic: str,
    repetitions: int,
    rng: np.random.Generator,
) -> tuple[float, list[float]]:
    array = np.asarray(list(values), dtype=float)
    if len(array) == 0:
        return float("nan"), [float("nan"), float("nan")]
    estimator = np.mean if statistic == "mean" else np.median
    estimates = np.empty(repetitions, dtype=float)
    for index in range(repetitions):
        sample = array[rng.integers(0, len(array), size=len(array))]
        estimates[index] = estimator(sample)
    return float(estimator(array)), percentile_interval(estimates)


def cluster_bootstrap_statistic(
    values: Iterable[float],
    clusters: Iterable[str],
    statistic: str,
    repetitions: int,
    rng: np.random.Generator,
) -> tuple[float, list[float], int]:
    array = np.asarray(list(values), dtype=float)
    cluster_array = np.asarray(list(clusters), dtype=object)
    if len(array) == 0:
        return float("nan"), [float("nan"), float("nan")], 0
    if len(array) != len(cluster_array):
        raise ValueError("values and clusters must have equal length")
    unique_clusters = np.unique(cluster_array)
    indices = {
        cluster: np.flatnonzero(cluster_array == cluster)
        for cluster in unique_clusters
    }
    estimator = np.mean if statistic == "mean" else np.median
    estimates = np.empty(repetitions, dtype=float)
    for index in range(repetitions):
        sampled_clusters = rng.choice(
            unique_clusters,
            size=len(unique_clusters),
            replace=True,
        )
        sample = np.concatenate([array[indices[cluster]] for cluster in sampled_clusters])
        estimates[index] = estimator(sample)
    return (
        float(estimator(array)),
        percentile_interval(estimates),
        int(len(unique_clusters)),
    )


def method_summary(
    subset: list[dict[str, Any]],
    repetitions: int,
    rng: np.random.Generator,
) -> dict[str, Any]:
    losses = [float(row["schedule_loss"]) for row in subset]
    mean_loss, mean_loss_ci = bootstrap_statistic(losses, "mean", repetitions, rng)
    success = [float(value <= SUCCESS_TOLERANCE) for value in losses]
    success_rate, success_ci = bootstrap_statistic(success, "mean", repetitions, rng)
    clusters = [str(row["layout_id"]) for row in subset]
    _, mean_loss_cluster_ci, layout_count = cluster_bootstrap_statistic(
        losses, clusters, "mean", repetitions, rng
    )
    _, success_cluster_ci, _ = cluster_bootstrap_statistic(
        success, clusters, "mean", repetitions, rng
    )
    missed_losses = [float(row["missed_loss"]) for row in subset]
    leakage_losses = [float(row["leakage_loss"]) for row in subset]
    mean_missed, missed_cluster_ci, _ = cluster_bootstrap_statistic(
        missed_losses, clusters, "mean", repetitions, rng
    )
    mean_leakage, leakage_cluster_ci, _ = cluster_bootstrap_statistic(
        leakage_losses, clusters, "mean", repetitions, rng
    )
    return {
        "n": len(subset),
        "layout_count": layout_count,
        "mean_schedule_loss": mean_loss,
        "mean_schedule_loss_ci95": mean_loss_ci,
        "mean_schedule_loss_layout_cluster_ci95": mean_loss_cluster_ci,
        "median_schedule_loss": float(np.median(losses)),
        "success_rate_at_0.005": success_rate,
        "success_rate_ci95": success_ci,
        "success_rate_layout_cluster_ci95": success_cluster_ci,
        "exact_solution_rate": float(np.mean([value <= 1e-12 for value in losses])),
        "mean_satisfaction": float(np.mean([row["satisfaction"] for row in subset])),
        "mean_missed_loss": mean_missed,
        "mean_missed_loss_layout_cluster_ci95": missed_cluster_ci,
        "mean_leakage_loss": mean_leakage,
        "mean_leakage_loss_layout_cluster_ci95": leakage_cluster_ci,
        "hard_valid_rate": float(np.mean([row["hard_valid"] for row in subset])),
        "median_edit_count": float(np.median([row["edit_count"] for row in subset])),
        "median_edit_cost": float(np.median([row["edit_cost"] for row in subset])),
        "median_evaluations": float(np.median([row["evaluations"] for row in subset])),
        "mean_runtime_seconds": float(np.mean([row["runtime_seconds"] for row in subset])),
    }


def paired_comparison(
    ours: dict[str, dict[str, Any]],
    other: dict[str, dict[str, Any]],
    repetitions: int,
    rng: np.random.Generator,
) -> dict[str, Any]:
    case_ids = sorted(ours.keys() & other.keys())
    ours_loss = np.asarray([ours[case_id]["schedule_loss"] for case_id in case_ids], dtype=float)
    other_loss = np.asarray([other[case_id]["schedule_loss"] for case_id in case_ids], dtype=float)
    difference = ours_loss - other_loss
    mean_difference, mean_ci = bootstrap_statistic(
        difference, "mean", repetitions, rng
    )
    median_difference, median_ci = bootstrap_statistic(
        difference, "median", repetitions, rng
    )
    layout_ids = np.asarray(
        [str(ours[case_id]["layout_id"]) for case_id in case_ids], dtype=object
    )
    _, mean_cluster_ci, layout_count = cluster_bootstrap_statistic(
        difference, layout_ids, "mean", repetitions, rng
    )
    _, median_cluster_ci, _ = cluster_bootstrap_statistic(
        difference, layout_ids, "median", repetitions, rng
    )
    nonzero = difference[np.abs(difference) > 1e-12]
    if len(nonzero) == 0:
        wilcoxon_p = 1.0
    else:
        wilcoxon_p = float(wilcoxon(nonzero, alternative="two-sided").pvalue)
    layout_mean_differences = np.asarray(
        [
            float(np.mean(difference[layout_ids == layout_id]))
            for layout_id in np.unique(layout_ids)
        ],
        dtype=float,
    )
    nonzero_layout = layout_mean_differences[
        np.abs(layout_mean_differences) > 1e-12
    ]
    layout_wilcoxon_p = (
        float(wilcoxon(nonzero_layout, alternative="two-sided").pvalue)
        if len(nonzero_layout)
        else 1.0
    )
    ours_success = ours_loss <= SUCCESS_TOLERANCE
    other_success = other_loss <= SUCCESS_TOLERANCE
    ours_only = int(np.sum(ours_success & ~other_success))
    other_only = int(np.sum(~ours_success & other_success))
    discordant = ours_only + other_only
    mcnemar_p = (
        float(binomtest(ours_only, discordant, 0.5, alternative="two-sided").pvalue)
        if discordant
        else 1.0
    )
    both_success = ours_success & other_success
    evaluation_difference = np.asarray(
        [
            ours[case_id]["evaluations"] - other[case_id]["evaluations"]
            for case_id, keep in zip(case_ids, both_success, strict=True)
            if keep
        ],
        dtype=float,
    )
    edit_difference = np.asarray(
        [
            ours[case_id]["edit_cost"] - other[case_id]["edit_cost"]
            for case_id, keep in zip(case_ids, both_success, strict=True)
            if keep
        ],
        dtype=float,
    )
    both_success_layouts = [
        str(ours[case_id]["layout_id"])
        for case_id, keep in zip(case_ids, both_success, strict=True)
        if keep
    ]
    if len(evaluation_difference):
        _, evaluation_case_ci = bootstrap_statistic(
            evaluation_difference, "median", repetitions, rng
        )
        _, evaluation_cluster_ci, _ = cluster_bootstrap_statistic(
            evaluation_difference,
            both_success_layouts,
            "median",
            repetitions,
            rng,
        )
        _, edit_case_ci = bootstrap_statistic(
            edit_difference, "median", repetitions, rng
        )
        _, edit_cluster_ci, _ = cluster_bootstrap_statistic(
            edit_difference,
            both_success_layouts,
            "median",
            repetitions,
            rng,
        )
    else:
        evaluation_case_ci = None
        evaluation_cluster_ci = None
        edit_case_ci = None
        edit_cluster_ci = None
    return {
        "n_paired": len(case_ids),
        "n_layout_clusters": layout_count,
        "mean_loss_difference_ours_minus_other": mean_difference,
        "mean_loss_difference_ci95": mean_ci,
        "mean_loss_difference_layout_cluster_ci95": mean_cluster_ci,
        "median_loss_difference_ours_minus_other": median_difference,
        "median_loss_difference_ci95": median_ci,
        "median_loss_difference_layout_cluster_ci95": median_cluster_ci,
        "wins_ties_losses": {
            "wins": int(np.sum(difference < -1e-12)),
            "ties": int(np.sum(np.abs(difference) <= 1e-12)),
            "losses": int(np.sum(difference > 1e-12)),
        },
        "wilcoxon_p": wilcoxon_p,
        "layout_mean_wilcoxon_p": layout_wilcoxon_p,
        "success_discordance": {
            "ours_only": ours_only,
            "other_only": other_only,
            "exact_mcnemar_p": mcnemar_p,
        },
        "both_success_n": int(np.sum(both_success)),
        "median_evaluation_difference_when_both_succeed": (
            float(np.median(evaluation_difference)) if len(evaluation_difference) else None
        ),
        "median_evaluation_difference_case_ci95": evaluation_case_ci,
        "median_evaluation_difference_layout_cluster_ci95": evaluation_cluster_ci,
        "median_edit_cost_difference_when_both_succeed": (
            float(np.median(edit_difference)) if len(edit_difference) else None
        ),
        "median_edit_cost_difference_case_ci95": edit_case_ci,
        "median_edit_cost_difference_layout_cluster_ci95": edit_cluster_ci,
    }


def paired_metric_difference(
    ours: dict[str, dict[str, Any]],
    other: dict[str, dict[str, Any]],
    metric: str,
    repetitions: int,
    rng: np.random.Generator,
) -> dict[str, Any]:
    case_ids = sorted(ours.keys() & other.keys())
    difference = np.asarray(
        [
            float(ours[case_id][metric]) - float(other[case_id][metric])
            for case_id in case_ids
        ],
        dtype=float,
    )
    layout_ids = [str(ours[case_id]["layout_id"]) for case_id in case_ids]
    mean_difference, case_ci = bootstrap_statistic(
        difference, "mean", repetitions, rng
    )
    _, cluster_ci, layout_count = cluster_bootstrap_statistic(
        difference, layout_ids, "mean", repetitions, rng
    )
    return {
        "metric": metric,
        "n_paired": len(case_ids),
        "n_layout_clusters": layout_count,
        "mean_difference_ours_minus_other": mean_difference,
        "mean_difference_case_ci95": case_ci,
        "mean_difference_layout_cluster_ci95": cluster_ci,
        "wins_ties_losses": {
            "wins": int(np.sum(difference < -1e-12)),
            "ties": int(np.sum(np.abs(difference) <= 1e-12)),
            "losses": int(np.sum(difference > 1e-12)),
        },
    }


def stratified_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ours = [row for row in rows if row["method"] == OURS]
    no_repair = {
        str(row["case_id"]): row for row in rows if row["method"] == "no_repair"
    }
    grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
    for row in ours:
        key = (
            row["source"],
            row["corruption"],
            row["severity"],
            row["route_family"],
            row["exhibit_count"],
        )
        grouped.setdefault(key, []).append(row)
    records: list[dict[str, Any]] = []
    for key, subset in sorted(grouped.items(), key=lambda item: tuple(map(str, item[0]))):
        reductions = []
        for row in subset:
            baseline = no_repair[str(row["case_id"])]
            denominator = max(float(baseline["schedule_loss"]), 1e-12)
            reductions.append(
                (float(baseline["schedule_loss"]) - float(row["schedule_loss"]))
                / denominator
            )
        records.append(
            {
                "source": key[0],
                "corruption": key[1],
                "severity": key[2],
                "route_family": key[3],
                "exhibit_count": key[4],
                "n": len(subset),
                "mean_schedule_loss": float(
                    np.mean([row["schedule_loss"] for row in subset])
                ),
                "success_rate_at_0.005": float(
                    np.mean([row["schedule_loss"] <= SUCCESS_TOLERANCE for row in subset])
                ),
                "median_relative_loss_reduction": float(np.median(reductions)),
                "hard_valid_rate": float(np.mean([row["hard_valid"] for row in subset])),
                "median_edit_count": float(np.median([row["edit_count"] for row in subset])),
            }
        )
    return records


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def holm_adjust(pvalues: dict[str, float]) -> dict[str, float]:
    ordered = sorted(pvalues.items(), key=lambda item: item[1])
    adjusted: dict[str, float] = {}
    running = 0.0
    total = len(ordered)
    for index, (name, value) in enumerate(ordered):
        running = max(running, min(1.0, (total - index) * value))
        adjusted[name] = running
    return adjusted


def plot_main(methods: dict[str, dict[str, Any]], output: Path) -> None:
    names = [method for method in PRIMARY_METHODS if method in methods]
    labels = [
        "No repair",
        "Visibility only",
        "Random",
        "Generic beam",
        "Annealing",
        "RevealRepair3D",
    ][: len(names)]
    colors = ["#9CA3AF", "#D9A441", "#70A6A1", "#718096", "#A07070", "#216E9B"]
    figure, axes = plt.subplots(1, 2, figsize=(10.8, 4.0))
    means = [methods[name]["mean_schedule_loss"] for name in names]
    lower = [
        means[index] - methods[name]["mean_schedule_loss_layout_cluster_ci95"][0]
        for index, name in enumerate(names)
    ]
    upper = [
        methods[name]["mean_schedule_loss_layout_cluster_ci95"][1] - means[index]
        for index, name in enumerate(names)
    ]
    axes[0].bar(range(len(names)), means, color=colors[: len(names)], width=0.72)
    axes[0].errorbar(
        range(len(names)), means, yerr=[lower, upper], fmt="none", ecolor="#222222", capsize=3
    )
    axes[0].set_ylabel("Mean signed schedule loss")
    axes[0].set_xticks(range(len(names)), labels, rotation=28, ha="right")
    axes[0].grid(axis="y", color="#D9DEE7", linewidth=0.7)
    axes[0].set_axisbelow(True)

    success = [methods[name]["success_rate_at_0.005"] for name in names]
    axes[1].bar(range(len(names)), success, color=colors[: len(names)], width=0.72)
    success_lower = [
        success[index] - methods[name]["success_rate_layout_cluster_ci95"][0]
        for index, name in enumerate(names)
    ]
    success_upper = [
        methods[name]["success_rate_layout_cluster_ci95"][1] - success[index]
        for index, name in enumerate(names)
    ]
    axes[1].errorbar(
        range(len(names)),
        success,
        yerr=[success_lower, success_upper],
        fmt="none",
        ecolor="#222222",
        capsize=3,
    )
    axes[1].set_ylim(0.0, 1.04)
    axes[1].set_ylabel("Tolerance satisfaction rate (loss <= 0.005)")
    axes[1].set_xticks(range(len(names)), labels, rotation=28, ha="right")
    axes[1].grid(axis="y", color="#D9DEE7", linewidth=0.7)
    axes[1].set_axisbelow(True)
    figure.tight_layout()
    figure.savefig(output / "figure_main_results.png", dpi=300, bbox_inches="tight")
    figure.savefig(output / "figure_main_results.pdf", bbox_inches="tight")
    plt.close(figure)


def plot_stratified(records: list[dict[str, Any]], output: Path) -> None:
    procedural = [row for row in records if row["source"] == "procedural"]
    corruptions = sorted({str(row["corruption"]) for row in procedural})
    severities = sorted({int(row["severity"]) for row in procedural})
    matrix = np.full((len(corruptions), len(severities)), np.nan)
    for i, corruption in enumerate(corruptions):
        for j, severity in enumerate(severities):
            values = [
                (row["success_rate_at_0.005"], row["n"])
                for row in procedural
                if row["corruption"] == corruption and row["severity"] == severity
            ]
            if values:
                matrix[i, j] = float(
                    sum(value * count for value, count in values)
                    / sum(count for _, count in values)
                )
    figure, axis = plt.subplots(figsize=(6.2, 4.1))
    image = axis.imshow(matrix, vmin=0.0, vmax=1.0, cmap="Blues", aspect="auto")
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            axis.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", color="#111111")
    axis.set_xticks(range(len(severities)), [f"Severity {value}" for value in severities])
    axis.set_yticks(range(len(corruptions)), [value.replace("_", " ") for value in corruptions])
    axis.set_title("RevealRepair3D tolerance satisfaction by corruption and severity")
    figure.colorbar(image, ax=axis, label="Tolerance satisfaction rate")
    figure.tight_layout()
    figure.savefig(output / "figure_stratified_success.png", dpi=300, bbox_inches="tight")
    figure.savefig(output / "figure_stratified_success.pdf", bbox_inches="tight")
    plt.close(figure)


def plot_efficiency(methods: dict[str, dict[str, Any]], output: Path) -> None:
    names = [method for method in PRIMARY_METHODS[1:] if method in methods]
    labels = {
        "visibility_max_only": "Visibility only",
        "random_feasible": "Random",
        "generic_greedy": "Generic beam",
        "simulated_annealing": "Annealing",
        OURS: "RevealRepair3D",
    }
    colors = {
        "visibility_max_only": "#D9A441",
        "random_feasible": "#70A6A1",
        "generic_greedy": "#718096",
        "simulated_annealing": "#A07070",
        OURS: "#216E9B",
    }
    figure, axis = plt.subplots(figsize=(6.2, 4.4))
    for name in names:
        row = methods[name]
        size = 80.0 + 55.0 * row["median_edit_count"]
        axis.scatter(
            row["median_evaluations"],
            row["success_rate_at_0.005"],
            s=size,
            color=colors[name],
            edgecolor="white",
            linewidth=0.8,
            label=labels[name],
        )
    axis.set_xlabel("Median objective evaluations")
    axis.set_ylabel("Tolerance satisfaction rate")
    axis.set_ylim(0.0, 1.04)
    axis.grid(color="#D9DEE7", linewidth=0.7)
    axis.set_axisbelow(True)
    axis.legend(frameon=False, loc="lower left")
    figure.tight_layout()
    figure.savefig(output / "figure_efficiency.png", dpi=300, bbox_inches="tight")
    figure.savefig(output / "figure_efficiency.pdf", bbox_inches="tight")
    plt.close(figure)


def matched_ablation_reference(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ablation_names = sorted(
        {str(row["method"]) for row in rows if str(row["method"]).startswith("ablation_")}
    )
    if not ablation_names:
        return {}
    case_sets = [
        {str(row["case_id"]) for row in rows if row["method"] == method}
        for method in ablation_names
    ]
    reference_ids = case_sets[0]
    if any(case_ids != reference_ids for case_ids in case_sets[1:]):
        raise RuntimeError("ablation methods do not share one matched case subset")
    reference_rows = [
        row
        for row in rows
        if row["method"] == OURS and str(row["case_id"]) in reference_ids
    ]
    if len(reference_rows) != len(reference_ids):
        raise RuntimeError("full method is missing cases from the ablation subset")
    return {
        "n": len(reference_rows),
        "case_ids_sha256": hashlib.sha256(
            "\n".join(sorted(reference_ids)).encode("utf-8")
        ).hexdigest(),
        "success_rate_at_0.005": float(
            np.mean(
                [float(row["schedule_loss"] <= SUCCESS_TOLERANCE) for row in reference_rows]
            )
        ),
        "hard_valid_rate": float(np.mean([row["hard_valid"] for row in reference_rows])),
    }


def plot_ablations(
    methods: dict[str, dict[str, Any]],
    full_reference: dict[str, Any],
    output: Path,
) -> None:
    names = [OURS] + sorted(name for name in methods if name.startswith("ablation_"))
    if len(names) == 1:
        return
    labels = {
        OURS: "Full (matched)",
        "ablation_visibility_only": "No hide term",
        "ablation_no_sparsity": "No sparsity",
        "ablation_no_hard_filter": "No hard filter",
        "ablation_targets_only": "Targets only",
        "ablation_partitions_only": "Partitions only",
    }
    colors = ["#216E9B"] + ["#AAB1BA"] * (len(names) - 1)
    figure, axes = plt.subplots(1, 2, figsize=(9.4, 3.8))
    x = np.arange(len(names))
    success_rates = [full_reference["success_rate_at_0.005"]] + [
        methods[name]["success_rate_at_0.005"] for name in names[1:]
    ]
    hard_valid_rates = [full_reference["hard_valid_rate"]] + [
        methods[name]["hard_valid_rate"] for name in names[1:]
    ]
    axes[0].bar(x, success_rates, color=colors)
    axes[0].set_ylim(0.0, 1.04)
    axes[0].set_ylabel("Tolerance satisfaction rate")
    axes[1].bar(x, hard_valid_rates, color=colors)
    axes[1].set_ylim(0.0, 1.04)
    axes[1].set_ylabel("Hard-valid output rate")
    for axis in axes:
        axis.set_xticks(x, [labels.get(name, name) for name in names], rotation=28, ha="right")
        axis.grid(axis="y", color="#D9DEE7", linewidth=0.7)
        axis.set_axisbelow(True)
    figure.tight_layout()
    figure.savefig(output / "figure_ablations.png", dpi=300, bbox_inches="tight")
    figure.savefig(output / "figure_ablations.pdf", bbox_inches="tight")
    plt.close(figure)


def plot_loss_components(methods: dict[str, dict[str, Any]], output: Path) -> None:
    names = [method for method in PRIMARY_METHODS if method in methods]
    labels = {
        "no_repair": "No repair",
        "visibility_max_only": "Visibility only",
        "random_feasible": "Random",
        "generic_greedy": "Generic beam",
        "simulated_annealing": "Annealing",
        OURS: "RevealRepair3D",
    }
    x = np.arange(len(names))
    width = 0.36
    missed = [methods[name]["mean_missed_loss"] for name in names]
    leakage = [methods[name]["mean_leakage_loss"] for name in names]

    def errors(metric: str, values: list[float]) -> list[list[float]]:
        lower = []
        upper = []
        for name, value in zip(names, values, strict=True):
            interval = methods[name][f"{metric}_layout_cluster_ci95"]
            lower.append(value - interval[0])
            upper.append(interval[1] - value)
        return [lower, upper]

    figure, axis = plt.subplots(figsize=(8.6, 4.2))
    axis.bar(
        x - width / 2.0,
        missed,
        width,
        yerr=errors("mean_missed_loss", missed),
        color="#D9A441",
        edgecolor="white",
        capsize=3,
        label="Missed-reveal loss",
    )
    axis.bar(
        x + width / 2.0,
        leakage,
        width,
        yerr=errors("mean_leakage_loss", leakage),
        color="#216E9B",
        edgecolor="white",
        capsize=3,
        label="Premature-reveal leakage",
    )
    axis.set_ylabel("Mean normalized loss component")
    axis.set_xticks(x, [labels[name] for name in names], rotation=25, ha="right")
    axis.grid(axis="y", color="#D9DEE7", linewidth=0.7)
    axis.set_axisbelow(True)
    axis.legend(frameon=False)
    figure.tight_layout()
    figure.savefig(output / "figure_loss_components.png", dpi=300, bbox_inches="tight")
    figure.savefig(output / "figure_loss_components.pdf", bbox_inches="tight")
    plt.close(figure)


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result_path = args.input / "full_results.csv" if args.input.is_dir() else args.input
    rows = read_rows(result_path)
    if not rows:
        raise RuntimeError("no experiment rows found")
    rng = np.random.default_rng(args.seed)
    methods: dict[str, dict[str, Any]] = {}
    for method in sorted({str(row["method"]) for row in rows}):
        subset = [row for row in rows if row["method"] == method]
        methods[method] = method_summary(subset, args.bootstrap, rng)

    by_method_case = {
        method: {
            str(row["case_id"]): row for row in rows if row["method"] == method
        }
        for method in methods
    }
    comparisons = {
        method: paired_comparison(
            by_method_case[OURS], by_method_case[method], args.bootstrap, rng
        )
        for method in PRIMARY_METHODS
        if method not in {OURS, "no_repair"} and method in by_method_case
    }
    wilcoxon_adjusted = holm_adjust(
        {method: values["wilcoxon_p"] for method, values in comparisons.items()}
    )
    layout_wilcoxon_adjusted = holm_adjust(
        {
            method: values["layout_mean_wilcoxon_p"]
            for method, values in comparisons.items()
        }
    )
    mcnemar_adjusted = holm_adjust(
        {
            method: values["success_discordance"]["exact_mcnemar_p"]
            for method, values in comparisons.items()
        }
    )
    for method in comparisons:
        comparisons[method]["wilcoxon_p_holm"] = wilcoxon_adjusted[method]
        comparisons[method]["layout_mean_wilcoxon_p_holm"] = (
            layout_wilcoxon_adjusted[method]
        )
        comparisons[method]["success_discordance"]["exact_mcnemar_p_holm"] = (
            mcnemar_adjusted[method]
        )
    ablation_comparisons = {
        method: paired_comparison(
            by_method_case[OURS], by_method_case[method], args.bootstrap, rng
        )
        for method in sorted(by_method_case)
        if method.startswith("ablation_")
    }
    ablation_reference = matched_ablation_reference(rows)
    no_repair = by_method_case["no_repair"]
    ours_rows = list(by_method_case[OURS].values())
    reductions = []
    for row in ours_rows:
        baseline = no_repair[str(row["case_id"])]
        denominator = max(float(baseline["schedule_loss"]), 1e-12)
        reductions.append(
            (float(baseline["schedule_loss"]) - float(row["schedule_loss"]))
            / denominator
        )
    median_reduction, median_reduction_ci = bootstrap_statistic(
        reductions, "median", args.bootstrap, rng
    )
    _, median_reduction_cluster_ci, reduction_layout_count = (
        cluster_bootstrap_statistic(
            reductions,
            [str(row["layout_id"]) for row in ours_rows],
            "median",
            args.bootstrap,
            rng,
        )
    )
    source_summaries = {
        source: method_summary(
            [row for row in ours_rows if row["source"] == source],
            args.bootstrap,
            rng,
        )
        for source in sorted({str(row["source"]) for row in ours_rows})
    }
    generic = comparisons.get("generic_greedy", {})
    annealing = comparisons.get("simulated_annealing", {})
    visibility_leakage = (
        paired_metric_difference(
            by_method_case[OURS],
            by_method_case["visibility_max_only"],
            "leakage_loss",
            args.bootstrap,
            rng,
        )
        if "visibility_max_only" in by_method_case
        else {}
    )
    procedural_count = sum(row["source"] == "procedural" for row in ours_rows)
    gate = {
        "procedural_case_count_at_least_300": procedural_count >= 300,
        "success_rate_at_least_0.80": methods[OURS]["success_rate_at_0.005"] >= 0.80,
        "median_relative_loss_reduction_at_least_0.80": median_reduction >= 0.80,
        "all_hard_constraints_preserved": methods[OURS]["hard_valid_rate"] == 1.0,
        "median_edited_entities_at_most_2": methods[OURS]["median_edit_count"] <= 2.0,
        "noninferior_to_generic_layout_cluster_upper_ci_nonpositive": bool(generic)
        and generic["mean_loss_difference_layout_cluster_ci95"][1] <= 0.0,
        "noninferior_to_annealing_layout_cluster_upper_ci_nonpositive": bool(annealing)
        and annealing["mean_loss_difference_layout_cluster_ci95"][1] <= 0.0,
        "signed_loss_reduces_visibility_only_leakage_cluster_ci_negative": bool(
            visibility_leakage
        )
        and visibility_leakage["mean_difference_layout_cluster_ci95"][1] < 0.0,
    }
    if "procedural" in source_summaries:
        gate["procedural_success_at_least_0.80"] = (
            source_summaries["procedural"]["success_rate_at_0.005"] >= 0.80
        )
    if "llm" in source_summaries:
        gate["llm_transfer_success_at_least_0.75"] = (
            source_summaries["llm"]["success_rate_at_0.005"] >= 0.75
        )
    gate["overall_pass"] = all(gate.values())
    strata = stratified_summary(rows)
    summary = {
        "input_sha256": hashlib.sha256(result_path.read_bytes()).hexdigest(),
        "row_count": len(rows),
        "primary_case_count": len(ours_rows),
        "success_tolerance": SUCCESS_TOLERANCE,
        "bootstrap_repetitions": args.bootstrap,
        "bootstrap_seed": args.seed,
        "methods": methods,
        "revealrepair_by_source": source_summaries,
        "paired_comparisons": comparisons,
        "ablation_comparisons": ablation_comparisons,
        "ablation_full_matched_reference": ablation_reference,
        "visibility_only_leakage_comparison": visibility_leakage,
        "median_relative_loss_reduction": median_reduction,
        "median_relative_loss_reduction_ci95": median_reduction_ci,
        "median_relative_loss_reduction_layout_cluster_ci95": (
            median_reduction_cluster_ci
        ),
        "layout_cluster_count": reduction_layout_count,
        "gate": gate,
    }
    with (args.output / "full_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
    method_table = [{"method": method} | values for method, values in methods.items()]
    write_csv(args.output / "table_method_summary.csv", method_table)
    write_csv(args.output / "table_stratified.csv", strata)
    plot_main(methods, args.output)
    plot_stratified(strata, args.output)
    plot_efficiency(methods, args.output)
    plot_ablations(methods, ablation_reference, args.output)
    plot_loss_components(methods, args.output)
    print(json.dumps(summary["gate"], indent=2), flush=True)


if __name__ == "__main__":
    main()
