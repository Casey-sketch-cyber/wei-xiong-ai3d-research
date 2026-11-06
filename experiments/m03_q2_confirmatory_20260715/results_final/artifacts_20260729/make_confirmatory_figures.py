from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
import numpy as np
import pandas as pd


MODELS = ("triposr", "instantmesh", "hunyuan21", "trellis")
MODEL_LABELS = {
    "triposr": "TripoSR",
    "instantmesh": "InstantMesh",
    "hunyuan21": "Hunyuan3D 2.1",
    "trellis": "TRELLIS",
}
MODEL_COLORS = {
    "triposr": "#4C78A8",
    "instantmesh": "#D4A72C",
    "hunyuan21": "#5B9E9A",
    "trellis": "#D97967",
}
STYLES = ("edge", "flat", "low_detail", "sketch", "watercolor")
STYLE_LABELS = {
    "edge": "Edge",
    "flat": "Flat colour",
    "low_detail": "Low detail",
    "sketch": "Sketch",
    "watercolor": "Watercolour",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    return parser.parse_args()


def configure_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "font.size": 7,
            "axes.titlesize": 7.5,
            "axes.labelsize": 7,
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "axes.linewidth": 0.7,
            "xtick.major.width": 0.7,
            "ytick.major.width": 0.7,
            "legend.frameon": False,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
        }
    )


def panel_label(axis: plt.Axes, label: str) -> None:
    axis.text(
        -0.14,
        1.05,
        label,
        transform=axis.transAxes,
        fontsize=8,
        fontweight="bold",
        va="bottom",
        ha="left",
    )


def save_figure(fig: plt.Figure, stem: Path) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".tiff"), dpi=600, bbox_inches="tight")
    fig.savefig(stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def plot_interval(
    axis: plt.Axes,
    x: float,
    mean: float,
    low: float,
    high: float,
    color: str,
    marker: str = "o",
    size: float = 28,
) -> None:
    axis.plot([low, high], [x, x], color=color, linewidth=1.4, solid_capstyle="round")
    axis.scatter(mean, x, s=size, color=color, marker=marker, edgecolor="white", linewidth=0.5, zorder=3)


def figure2(analysis: Path, output: Path) -> None:
    styles = pd.read_csv(analysis / "style_rg_tests.csv")
    primary = pd.read_csv(analysis / "primary_sketch_tests.csv")
    changes = pd.read_csv(analysis / "absolute_metric_changes.csv")

    fig = plt.figure(figsize=(7.2, 4.7), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, width_ratios=(1.35, 1.0), height_ratios=(1.0, 1.0))
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[:, 1])
    ax_c = fig.add_subplot(grid[1, 0])

    matrix = np.empty((len(MODELS), len(STYLES)), dtype=float)
    for row_index, model in enumerate(MODELS):
        for column_index, style in enumerate(STYLES):
            row = styles[(styles["model"] == model) & (styles["style"] == style)].iloc[0]
            matrix[row_index, column_index] = row["mean"]
    bound = max(0.01, float(np.nanmax(np.abs(matrix))))
    cmap = LinearSegmentedColormap.from_list(
        "muted_diverging", ("#4C78A8", "#F7F7F7", "#D97967")
    )
    image = ax_a.imshow(
        matrix,
        cmap=cmap,
        norm=TwoSlopeNorm(vmin=-bound, vcenter=0.0, vmax=bound),
        aspect="auto",
    )
    ax_a.set_xticks(range(len(STYLES)), [STYLE_LABELS[style] for style in STYLES], rotation=28, ha="right")
    ax_a.set_yticks(range(len(MODELS)), [MODEL_LABELS[model] for model in MODELS])
    ax_a.set_title("Mean surface-solid robustness gap")
    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            value = matrix[row, column]
            color = "white" if abs(value) > 0.65 * bound else "#222222"
            ax_a.text(column, row, f"{value:.3f}", ha="center", va="center", fontsize=5.8, color=color)
    colorbar = fig.colorbar(image, ax=ax_a, fraction=0.045, pad=0.02)
    colorbar.set_label("RG")
    panel_label(ax_a, "a")

    primary = primary.set_index("model").loc[list(MODELS)].reset_index()
    y_positions = np.arange(len(MODELS))[::-1]
    for y, row in zip(y_positions, primary.to_dict("records")):
        plot_interval(
            ax_b,
            y,
            row["mean"],
            row["ci99_low"],
            row["ci99_high"],
            MODEL_COLORS[row["model"]],
            marker="o" if row["passes"] else "s",
            size=38,
        )
        ax_b.text(
            max(row["ci99_high"], 0) + 0.004,
            y,
            f"p$_{{Holm}}$={row['p_holm']:.3g}",
            va="center",
            fontsize=6,
        )
    ax_b.axvline(0, color="#777777", linestyle="--", linewidth=0.8)
    ax_b.set_yticks(y_positions, [MODEL_LABELS[model] for model in MODELS])
    ax_b.set_xlabel("Sketch RG (mean and 99% cluster-bootstrap CI)")
    ax_b.set_title("Pre-specified primary test (n=120 objects)")
    ax_b.margins(x=0.25, y=0.25)
    panel_label(ax_b, "b")

    sketch = changes[changes["style"] == "sketch"].copy()
    metric_style = {
        "surface_degradation": ("Surface F-score degradation", "#6F7C8E", "o", -0.11),
        "solid_degradation": ("Solid IoU degradation", "#D97967", "s", 0.11),
    }
    for metric, (label, color, marker, offset) in metric_style.items():
        subset = sketch[sketch["metric"] == metric].set_index("model").loc[list(MODELS)]
        for x, (_, row) in enumerate(subset.iterrows()):
            ax_c.plot(
                [x + offset, x + offset],
                [row["ci99_low"], row["ci99_high"]],
                color=color,
                linewidth=1.2,
            )
            ax_c.scatter(
                x + offset,
                row["mean"],
                s=27,
                color=color,
                marker=marker,
                edgecolor="white",
                linewidth=0.4,
                label=label if x == 0 else None,
                zorder=3,
            )
    ax_c.axhline(0, color="#999999", linewidth=0.7)
    ax_c.set_xticks(range(len(MODELS)), [MODEL_LABELS[model] for model in MODELS], rotation=18, ha="right")
    ax_c.set_ylabel("Photo-to-sketch degradation")
    ax_c.set_title("Auditable components of sketch RG")
    ax_c.legend(loc="upper left", fontsize=6)
    panel_label(ax_c, "c")

    save_figure(fig, output / "figure2_main_quantitative_results")


def figure3_scatter(analysis: Path, output: Path) -> None:
    paired = pd.read_csv(analysis / "paired_main_object_averaged.csv")
    paired = paired[paired["style"] == "sketch"].copy()
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 6.2), constrained_layout=True)
    all_values = np.concatenate(
        [paired["surface_degradation"].to_numpy(), paired["solid_degradation"].to_numpy()]
    )
    lower = min(-0.03, float(np.nanmin(all_values)) - 0.01)
    upper = max(0.08, float(np.nanmax(all_values)) + 0.01)
    for label, model, axis in zip(("a", "b", "c", "d"), MODELS, axes.flat):
        subset = paired[paired["model"] == model].copy()
        colors = np.where(subset["rg"] > 0, MODEL_COLORS[model], "#B9BDC4")
        axis.scatter(
            subset["surface_degradation"],
            subset["solid_degradation"],
            s=15,
            c=colors,
            alpha=0.72,
            edgecolors="none",
        )
        axis.plot([lower, upper], [lower, upper], color="#777777", linestyle="--", linewidth=0.8)
        top = subset.nlargest(2, "rg")
        for _, row in top.iterrows():
            axis.annotate(
                row["object_id"],
                (row["surface_degradation"], row["solid_degradation"]),
                xytext=(3, 3),
                textcoords="offset points",
                fontsize=5.4,
            )
        axis.set_xlim(lower, upper)
        axis.set_ylim(lower, upper)
        axis.set_aspect("equal", adjustable="box")
        axis.set_title(MODEL_LABELS[model])
        axis.set_xlabel("Surface F-score degradation")
        axis.set_ylabel("Solid IoU degradation")
        panel_label(axis, label)
    save_figure(fig, output / "figure3_object_level_metric_gap_scatter")


def figure4(analysis: Path, output: Path) -> None:
    views = pd.read_csv(analysis / "view_generalization.csv")
    severity = pd.read_csv(analysis / "severity_trends.csv")
    seeds = pd.read_csv(analysis / "seed_reliability.csv")
    renders = pd.read_csv(analysis / "render_diagnostic_style_tests.csv")

    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.7), constrained_layout=True)
    ax_a, ax_b, ax_c, ax_d = axes.flat

    view_sketch = views[views["style"] == "sketch"].copy()
    view_ids = sorted(view_sketch["view_id"].unique())
    offsets = (-0.10, 0.10)
    markers = ("o", "s")
    for view_id, offset, marker in zip(view_ids, offsets, markers):
        subset = view_sketch[view_sketch["view_id"] == view_id].set_index("model").loc[list(MODELS)]
        for x, (model, row) in enumerate(subset.iterrows()):
            ax_a.plot(
                [x + offset, x + offset],
                [row["ci99_low"], row["ci99_high"]],
                color=MODEL_COLORS[model],
                linewidth=1.1,
            )
            ax_a.scatter(
                x + offset,
                row["mean"],
                marker=marker,
                s=25,
                color=MODEL_COLORS[model],
                edgecolor="white",
                linewidth=0.4,
                label=view_id.replace("yaw_", "yaw ").replace("m30", "-30 deg").replace("p30", "+30 deg")
                if x == 0
                else None,
            )
    ax_a.axhline(0, color="#888888", linestyle="--", linewidth=0.7)
    ax_a.set_xticks(range(len(MODELS)), [MODEL_LABELS[model] for model in MODELS], rotation=18, ha="right")
    ax_a.set_ylabel("Sketch RG")
    ax_a.set_title("Fixed-view generalization (n=30 objects)")
    ax_a.legend(fontsize=6, loc="best")
    panel_label(ax_a, "a")

    sketch_severity = severity[severity["style"] == "sketch"].set_index("model").loc[list(MODELS)]
    for x, (model, row) in enumerate(sketch_severity.iterrows()):
        ax_b.plot([x, x], [row["ci99_low"], row["ci99_high"]], color=MODEL_COLORS[model], linewidth=1.2)
        ax_b.scatter(x, row["mean"], s=31, color=MODEL_COLORS[model], edgecolor="white", linewidth=0.4)
    ax_b.axhline(0, color="#888888", linestyle="--", linewidth=0.7)
    ax_b.set_xticks(range(len(MODELS)), [MODEL_LABELS[model] for model in MODELS], rotation=18, ha="right")
    ax_b.set_ylabel("Sketch RG slope per severity level")
    ax_b.set_title("Ordered severity response (n=30 objects)")
    panel_label(ax_b, "b")

    seeds = seeds.set_index("model").loc[list(("instantmesh", "hunyuan21", "trellis"))]
    x = np.arange(len(seeds))
    ax_c.scatter(x - 0.08, seeds["pearson_r"], s=32, marker="o", color="#4C78A8", label="Pearson r")
    ax_c.scatter(
        x + 0.08,
        seeds["object_sign_agreement"],
        s=32,
        marker="s",
        color="#D4A72C",
        label="Sign agreement",
    )
    ax_c.set_xticks(x, [MODEL_LABELS[model] for model in seeds.index], rotation=18, ha="right")
    ax_c.set_ylim(-0.05, 1.05)
    ax_c.set_ylabel("Reliability")
    ax_c.set_title("Two-seed object-level agreement (n=120)")
    ax_c.legend(fontsize=6, loc="lower right")
    panel_label(ax_c, "c")

    sketch_render = renders[renders["style"] == "sketch"].copy()
    diagnostics = (
        ("silhouette_iou_mean", "Six-view silhouette IoU", "o", -0.10, "#6F7C8E"),
        ("normal_render_similarity_mean", "Normal-render similarity", "s", 0.10, "#D97967"),
    )
    for diagnostic, label, marker, offset, color in diagnostics:
        subset = sketch_render[sketch_render["diagnostic"] == diagnostic].set_index("model").loc[list(MODELS)]
        for x_value, (_, row) in enumerate(subset.iterrows()):
            ax_d.plot(
                [x_value + offset, x_value + offset],
                [row["ci99_low"], row["ci99_high"]],
                color=color,
                linewidth=1.1,
            )
            ax_d.scatter(
                x_value + offset,
                row["mean"],
                s=27,
                marker=marker,
                color=color,
                edgecolor="white",
                linewidth=0.4,
                label=label if x_value == 0 else None,
            )
    ax_d.axhline(0, color="#888888", linestyle="--", linewidth=0.7)
    ax_d.set_xticks(range(len(MODELS)), [MODEL_LABELS[model] for model in MODELS], rotation=18, ha="right")
    ax_d.set_ylabel("Photo-to-sketch change")
    ax_d.set_title("Independent render-space diagnostics")
    ax_d.legend(fontsize=6, loc="best")
    panel_label(ax_d, "d")

    save_figure(fig, output / "figure4_robustness_and_render_diagnostics")


def main() -> int:
    args = parse_args()
    configure_style()
    figure2(args.analysis_root, args.output_root)
    figure3_scatter(args.analysis_root, args.output_root)
    figure4(args.analysis_root, args.output_root)
    print(f"Figures written to {args.output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
