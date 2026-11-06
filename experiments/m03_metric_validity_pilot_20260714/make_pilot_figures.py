from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D


MODEL_ORDER = ("triposr", "instantmesh", "hunyuan21")
STYLE_ORDER = ("edge", "flat", "low_detail", "sketch", "watercolor")
MODEL_LABELS = {
    "triposr": "TripoSR",
    "instantmesh": "InstantMesh",
    "hunyuan21": "Hunyuan3D 2.1",
}
STYLE_LABELS = {
    "edge": "Edge",
    "flat": "Flat colour",
    "low_detail": "Low detail",
    "sketch": "Sketch",
    "watercolor": "Watercolour",
}
STYLE_COLORS = {
    "edge": "#3B6FB6",
    "flat": "#35A17B",
    "low_detail": "#E0A02B",
    "sketch": "#D85B55",
    "watercolor": "#7D62A8",
}
MODEL_COLORS = {
    "triposr": "#2D5B9A",
    "instantmesh": "#2D936C",
    "hunyuan21": "#C75850",
}
STYLE_MARKERS = {
    "edge": "o",
    "flat": "s",
    "low_detail": "^",
    "sketch": "D",
    "watercolor": "P",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    return parser.parse_args()


def style_axes(axis) -> None:
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.tick_params(direction="out", length=3, width=0.8)


def save(fig, root: Path, name: str) -> None:
    fig.savefig(root / f"{name}.png", dpi=400, bbox_inches="tight", facecolor="white")
    fig.savefig(root / f"{name}.pdf", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def paradox_scatter(paired: pd.DataFrame, root: Path) -> None:
    x_limit = max(abs(paired["delta_fscore"]).quantile(0.995), 0.02) * 1.12
    y_limit = max(abs(paired["delta_voxel_iou"]).quantile(0.995), 0.02) * 1.12
    fig, axes = plt.subplots(1, 3, figsize=(10.6, 3.45), sharex=True, sharey=True)
    for panel, (axis, model) in enumerate(zip(axes, MODEL_ORDER)):
        frame = paired[paired["model"] == model]
        axis.axvspan(0, x_limit, ymin=0, ymax=0.5, color="#F7D9D5", alpha=0.55, zorder=0)
        axis.axhline(0, color="#555555", linewidth=0.8, linestyle=(0, (3, 2)), zorder=1)
        axis.axvline(0, color="#555555", linewidth=0.8, linestyle=(0, (3, 2)), zorder=1)
        for style in STYLE_ORDER:
            subset = frame[frame["style"] == style]
            color = STYLE_COLORS[style]
            axis.scatter(
                subset["delta_fscore"],
                subset["delta_voxel_iou"],
                s=18,
                color=color,
                alpha=0.36,
                linewidths=0,
            )
            axis.scatter(
                [subset["delta_fscore"].mean()],
                [subset["delta_voxel_iou"].mean()],
                s=60,
                color=color,
                edgecolor="white",
                linewidth=1.0,
                label=STYLE_LABELS[style],
                zorder=4,
            )
        axis.set_title(MODEL_LABELS[model], fontsize=10, fontweight="bold")
        axis.text(0.02, 0.98, chr(ord("A") + panel), transform=axis.transAxes, va="top", fontweight="bold")
        axis.set_xlim(-x_limit, x_limit)
        axis.set_ylim(-y_limit, y_limit)
        axis.set_xlabel(r"$\Delta$ F-score@0.05", fontsize=9)
        style_axes(axis)
    axes[0].set_ylabel(r"$\Delta$ voxel IoU", fontsize=9)
    handles, labels = axes[-1].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=5, frameon=False, fontsize=8)
    fig.subplots_adjust(bottom=0.25, wspace=0.14)
    save(fig, root, "figure_metric_paradox_scatter")


def delta_summary(reversal: pd.DataFrame, root: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 3.55), sharex=True)
    specifications = (
        ("delta_fscore", r"Mean $\Delta$ F-score@0.05", "A"),
        ("delta_voxel_iou", r"Mean $\Delta$ voxel IoU", "B"),
    )
    offsets = {"triposr": -0.22, "instantmesh": 0.0, "hunyuan21": 0.22}
    for axis, (metric, ylabel, panel) in zip(axes, specifications):
        axis.axhline(0, color="#555555", linewidth=0.8, linestyle=(0, (3, 2)))
        for model in MODEL_ORDER:
            subset = reversal[reversal["model"] == model].set_index("style").loc[list(STYLE_ORDER)]
            x = np.arange(len(STYLE_ORDER)) + offsets[model]
            means = subset[f"{metric}_mean"].to_numpy()
            low = subset[f"{metric}_ci_low"].to_numpy()
            high = subset[f"{metric}_ci_high"].to_numpy()
            axis.errorbar(
                x,
                means,
                yerr=np.vstack((means - low, high - means)),
                fmt="o",
                markersize=5,
                capsize=2.5,
                linewidth=1.1,
                color=MODEL_COLORS[model],
                label=MODEL_LABELS[model],
            )
        axis.set_xticks(np.arange(len(STYLE_ORDER)), [STYLE_LABELS[item] for item in STYLE_ORDER], rotation=18, ha="right")
        axis.set_ylabel(ylabel, fontsize=9)
        axis.text(0.01, 0.98, panel, transform=axis.transAxes, va="top", fontweight="bold")
        style_axes(axis)
    axes[1].legend(frameon=False, fontsize=8, loc="best")
    fig.tight_layout()
    save(fig, root, "figure_bootstrap_style_effects")


def seed_agreement(data: pd.DataFrame, root: Path) -> None:
    stochastic = data[(data["seed"] >= 0) & (data["model"].isin(("instantmesh", "hunyuan21")))]
    metrics = ("fscore_0.05", "voxel_iou")
    rows = []
    for model in ("instantmesh", "hunyuan21"):
        frame = stochastic[stochastic["model"] == model]
        seeds = sorted(frame["seed"].unique())
        if len(seeds) != 2:
            continue
        for seed in seeds:
            seed_frame = frame[frame["seed"] == seed]
            photo = seed_frame[seed_frame["style"] == "photo"][["object_id", *metrics]]
            for style in STYLE_ORDER:
                target = seed_frame[seed_frame["style"] == style][["object_id", *metrics]]
                merged = target.merge(photo, on="object_id", suffixes=("", "_photo"))
                rows.append(
                    {
                        "model": model,
                        "style": style,
                        "seed": int(seed),
                        "delta_fscore": float((merged["fscore_0.05"] - merged["fscore_0.05_photo"]).mean()),
                        "delta_voxel_iou": float((merged["voxel_iou"] - merged["voxel_iou_photo"]).mean()),
                    }
                )
    frame = pd.DataFrame(rows)
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.75))
    for panel, (axis, metric, label) in enumerate(
        zip(axes, ("delta_fscore", "delta_voxel_iou"), (r"Mean $\Delta$ F-score", r"Mean $\Delta$ voxel IoU"))
    ):
        values = []
        for model in ("instantmesh", "hunyuan21"):
            subset = frame[frame["model"] == model]
            pivot = subset.pivot(index="style", columns="seed", values=metric).loc[list(STYLE_ORDER)]
            x = pivot.iloc[:, 0]
            y = pivot.iloc[:, 1]
            values.extend(x.tolist() + y.tolist())
            for style, xv, yv in zip(STYLE_ORDER, x, y):
                axis.scatter(
                    xv,
                    yv,
                    s=48,
                    color=MODEL_COLORS[model],
                    marker=STYLE_MARKERS[style],
                    alpha=0.9,
                )
        low, high = min(values), max(values)
        margin = max((high - low) * 0.08, 0.005)
        axis.plot([low - margin, high + margin], [low - margin, high + margin], color="#666666", linewidth=0.8, linestyle=(0, (3, 2)))
        axis.set_xlim(low - margin, high + margin)
        axis.set_ylim(low - margin, high + margin)
        axis.set_xlabel("Seed 3407", fontsize=9)
        axis.set_ylabel("Seed 20260714", fontsize=9)
        axis.set_title(label, fontsize=9)
        axis.text(0.01, 0.98, chr(ord("A") + panel), transform=axis.transAxes, va="top", fontweight="bold")
        style_axes(axis)
    model_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            linestyle="none",
            markerfacecolor=MODEL_COLORS[model],
            markeredgecolor="none",
            markersize=6,
            label=MODEL_LABELS[model],
        )
        for model in ("instantmesh", "hunyuan21")
    ]
    style_handles = [
        Line2D(
            [0],
            [0],
            marker=STYLE_MARKERS[style],
            linestyle="none",
            markerfacecolor="#666666",
            markeredgecolor="none",
            markersize=5.5,
            label=STYLE_LABELS[style],
        )
        for style in STYLE_ORDER
    ]
    axes[1].legend(handles=model_handles, frameon=False, fontsize=7.5, loc="lower right")
    fig.legend(
        handles=style_handles,
        frameon=False,
        fontsize=7.2,
        ncol=5,
        loc="lower center",
        bbox_to_anchor=(0.5, 0.0),
    )
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    save(fig, root, "figure_seed_agreement")


def main() -> None:
    args = parse_args()
    root = args.work / "figures"
    root.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8,
            "axes.linewidth": 0.8,
            "xtick.major.width": 0.8,
            "ytick.major.width": 0.8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    paired = pd.read_csv(args.work / "paired_style_changes.csv")
    reversal = pd.read_csv(args.work / "reversal_bootstrap.csv")
    evaluation = pd.read_csv(args.work / "evaluation_results.csv")
    paradox_scatter(paired, root)
    delta_summary(reversal, root)
    seed_agreement(evaluation, root)
    print(root)


if __name__ == "__main__":
    main()
