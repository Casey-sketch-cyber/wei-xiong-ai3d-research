from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
PROJECT_DATA = ROOT / "02_figures_tables" / "m03_experiment_outputs"
PACKAGED_DATA = ROOT / "experiment_outputs"
DATA = PACKAGED_DATA if (PACKAGED_DATA / "m03_main100.csv").exists() else PROJECT_DATA
OUT = ROOT / "02_figures_tables" / "publication_figures"
LATEX_FIGS = ROOT / "01_manuscript" / "latex" / "figures"


STYLE_ORDER = ["edge", "flat", "low_detail", "sketch", "watercolor"]
STYLE_LABELS = {
    "edge": "Edge",
    "flat": "Flat colour",
    "low_detail": "Low detail",
    "sketch": "Sketch",
    "watercolor": "Watercolour",
}

COLORS = {
    "edge": "#4C78A8",
    "flat": "#72B7B2",
    "low_detail": "#F2CF5B",
    "sketch": "#E45756",
    "watercolor": "#B279A2",
    "photo": "#9A9A9A",
    "ink": "#252525",
    "soft": "#F5F7FA",
    "grid": "#D8DEE9",
}


def setup() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    LATEX_FIGS.mkdir(parents=True, exist_ok=True)
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "font.size": 8,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "axes.linewidth": 0.75,
            "axes.edgecolor": COLORS["ink"],
            "xtick.color": COLORS["ink"],
            "ytick.color": COLORS["ink"],
            "text.color": COLORS["ink"],
            "axes.labelcolor": COLORS["ink"],
            "legend.frameon": False,
        }
    )


def save(fig: plt.Figure, name: str) -> None:
    for ext in ["svg", "pdf", "png", "tiff"]:
        kwargs = {"bbox_inches": "tight"}
        if ext in {"png", "tiff"}:
            kwargs["dpi"] = 600
        fig.savefig(OUT / f"{name}.{ext}", **kwargs)
    fig.savefig(LATEX_FIGS / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(LATEX_FIGS / f"{name}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def add_panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(-0.08, 1.05, label, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom")


def rounded_box(ax: plt.Axes, xy, width, height, text, fc="#FFFFFF", ec="#333333", fontsize=8):
    box = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.025,rounding_size=0.025",
        linewidth=0.9,
        edgecolor=ec,
        facecolor=fc,
    )
    ax.add_patch(box)
    ax.text(xy[0] + width / 2, xy[1] + height / 2, text, ha="center", va="center", fontsize=fontsize)
    return box


def arrow(ax: plt.Axes, start, end) -> None:
    arr = FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=11, linewidth=0.9, color="#555555")
    ax.add_patch(arr)


def figure_framework(main: pd.DataFrame) -> None:
    df = main.set_index("style").loc[STYLE_ORDER].reset_index()
    fig = plt.figure(figsize=(7.4, 4.8))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.42, 1.0], height_ratios=[1.0, 1.0], hspace=0.44, wspace=0.34)
    ax = fig.add_subplot(gs[:, 0])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    rounded_box(ax, (0.04, 0.72), 0.23, 0.14, "Curated\nObjaverse-100\n3D objects", fc="#EEF3FA", ec=COLORS["edge"], fontsize=7.4)
    rounded_box(ax, (0.37, 0.72), 0.25, 0.14, "Matched inputs\nphoto + 5 styles\nsame view", fc="#F7F4E8", ec="#C9A227", fontsize=7.4)
    rounded_box(ax, (0.72, 0.72), 0.22, 0.14, "Same TripoSR\npipeline\n600 meshes", fc="#F1F5EF", ec="#6B9B6A", fontsize=7.4)
    arrow(ax, (0.27, 0.79), (0.37, 0.79))
    arrow(ax, (0.62, 0.79), (0.72, 0.79))

    style_x = [0.25, 0.48, 0.71, 0.25, 0.48, 0.71]
    style_y = [0.635, 0.635, 0.635, 0.575, 0.575, 0.575]
    style_names = ["Photo", "Edge", "Flat colour", "Low detail", "Sketch", "Watercolour"]
    style_cols = [COLORS["photo"], COLORS["edge"], COLORS["flat"], COLORS["low_detail"], COLORS["sketch"], COLORS["watercolor"]]
    for x, y, name, col in zip(style_x, style_y, style_names, style_cols):
        ax.add_patch(plt.Circle((x, y), 0.0145, facecolor=col, edgecolor="white", linewidth=0.6))
        ax.text(x + 0.025, y, name, ha="left", va="center", fontsize=5.6)

    rounded_box(ax, (0.07, 0.38), 0.25, 0.13, "Paired comparison\nstyle output vs.\nphoto output", fc="#FFFFFF", ec="#666666", fontsize=7.2)
    rounded_box(ax, (0.40, 0.38), 0.22, 0.13, "Point metrics\nChamfer\nF-score", fc="#FFFFFF", ec="#666666", fontsize=7.2)
    rounded_box(ax, (0.72, 0.38), 0.22, 0.13, "Asset diagnostics\nvolume\nz-extent", fc="#FFFFFF", ec="#666666", fontsize=7.2)
    arrow(ax, (0.32, 0.445), (0.40, 0.445))
    arrow(ax, (0.62, 0.445), (0.72, 0.445))

    rounded_box(
        ax,
        (0.10, 0.10),
        0.76,
        0.14,
        "Diagnostic question:\ncan point metrics improve\nwhile usable 3D volume collapses?",
        fc="#FAFAFA",
        ec="#999999",
        fontsize=7.2,
    )
    add_panel_label(ax, "A")
    ax.text(0.04, 0.96, "Benchmark design", ha="left", va="top", fontsize=9, fontweight="bold")

    axv = fig.add_subplot(gs[0, 1])
    x = np.arange(len(df))
    axv.bar(x, df["pred_volume_ratio_mean"], color=[COLORS[s] for s in df["style"]], width=0.72)
    axv.axhline(1, color="#444444", linestyle="--", linewidth=0.8)
    axv.set_xticks(x)
    axv.set_xticklabels([STYLE_LABELS[s] for s in df["style"]], rotation=24, ha="right", fontsize=6.2)
    axv.set_ylabel("Volume ratio")
    axv.set_ylim(0, 1.05)
    axv.grid(axis="y", color=COLORS["grid"], linewidth=0.6, alpha=0.8)
    for i, row in df.iterrows():
        axv.text(i, row["pred_volume_ratio_mean"] + 0.035, f'{row["pred_volume_ratio_mean"]:.2f}', ha="center", fontsize=6.2)
    add_panel_label(axv, "B")
    axv.set_title("Observed volume loss", loc="left", fontsize=9, fontweight="bold")

    axp = fig.add_subplot(gs[1, 1])
    axp.axhline(1, color="#444444", linestyle="--", linewidth=0.8)
    axp.axvline(0, color="#444444", linestyle="--", linewidth=0.8)
    for _, row in df.iterrows():
        s = row["style"]
        axp.scatter(row["fscore_0.05_delta_mean"], row["pred_volume_ratio_mean"], s=58, color=COLORS[s], edgecolor="white", linewidth=0.6)
    axp.set_xlabel("F-score@0.05 change")
    axp.set_ylabel("Volume ratio")
    axp.set_xlim(-0.005, 0.105)
    axp.set_ylim(0.18, 0.58)
    axp.grid(color=COLORS["grid"], linewidth=0.6, alpha=0.8)
    add_panel_label(axp, "C")
    axp.set_title("Point metric vs. asset diagnostic", loc="left", fontsize=9, fontweight="bold")
    save(fig, "fig1_framework")


def graphical_abstract(main: pd.DataFrame) -> None:
    df = main.set_index("style").loc[STYLE_ORDER].reset_index()
    fig = plt.figure(figsize=(10, 4))
    gs = fig.add_gridspec(1, 3, width_ratios=[0.9, 1.2, 1.25], wspace=0.34)

    ax0 = fig.add_subplot(gs[0, 0])
    ax0.set_xlim(0, 1)
    ax0.set_ylim(0, 1)
    ax0.axis("off")
    rounded_box(ax0, (0.08, 0.65), 0.34, 0.18, "photo\ninput", fc="#F5F5F5", ec=COLORS["photo"], fontsize=9)
    rounded_box(ax0, (0.58, 0.65), 0.34, 0.18, "artistic\ninput", fc="#FFF7EA", ec=COLORS["low_detail"], fontsize=9)
    arrow(ax0, (0.42, 0.74), (0.58, 0.74))
    rounded_box(ax0, (0.12, 0.38), 0.76, 0.17, "same object\nsame view\nsame TripoSR pipeline", fc="#FFFFFF", ec="#777777", fontsize=8.5)
    rounded_box(ax0, (0.12, 0.12), 0.76, 0.16, "paired geometry\ncomparison", fc="#FFFFFF", ec="#777777", fontsize=8.5)

    ax1 = fig.add_subplot(gs[0, 1])
    x = np.arange(len(df))
    ax1.bar(x, df["pred_volume_ratio_mean"], color=[COLORS[s] for s in df["style"]], width=0.72)
    ax1.axhline(1, color="#444444", linestyle="--", linewidth=0.8)
    ax1.set_xticks(x)
    ax1.set_xticklabels([STYLE_LABELS[s] for s in df["style"]], rotation=28, ha="right", fontsize=7)
    ax1.set_ylabel("Volume ratio vs. photo")
    ax1.set_ylim(0, 1.05)
    ax1.grid(axis="y", color=COLORS["grid"], linewidth=0.6, alpha=0.8)
    ax1.set_title("All stylised inputs reduce output volume", fontsize=10, fontweight="bold", loc="left")
    for i, row in df.iterrows():
        ax1.text(i, row["pred_volume_ratio_mean"] + 0.035, f'{row["pred_volume_ratio_mean"]:.2f}', ha="center", fontsize=7)

    ax2 = fig.add_subplot(gs[0, 2])
    ax2.axhline(1, color="#444444", linestyle="--", linewidth=0.8)
    ax2.axvline(0, color="#444444", linestyle="--", linewidth=0.8)
    for _, row in df.iterrows():
        s = row["style"]
        ax2.scatter(row["fscore_0.05_delta_mean"], row["pred_volume_ratio_mean"], s=80, color=COLORS[s], edgecolor="white", linewidth=0.6)
        ax2.text(row["fscore_0.05_delta_mean"] + 0.002, row["pred_volume_ratio_mean"] + 0.012, STYLE_LABELS[s], fontsize=7)
    ax2.set_xlabel("F-score@0.05 change vs. photo")
    ax2.set_ylabel("Volume ratio vs. photo")
    ax2.set_xlim(-0.005, 0.105)
    ax2.set_ylim(0.18, 0.58)
    ax2.grid(color=COLORS["grid"], linewidth=0.6, alpha=0.8)
    ax2.set_title("Aggregate surface gains can accompany contraction", fontsize=10, fontweight="bold", loc="left")

    for ext in ["svg", "pdf", "png", "tiff"]:
        kwargs = {"bbox_inches": "tight"}
        if ext in {"png", "tiff"}:
            kwargs["dpi"] = 600
        fig.savefig(OUT / f"graphical_abstract.{ext}", **kwargs)
    plt.close(fig)


def figure_main_results(main: pd.DataFrame) -> None:
    df = main.set_index("style").loc[STYLE_ORDER].reset_index()
    x = np.arange(len(df))
    labels = [STYLE_LABELS[s] for s in df["style"]]
    fig = plt.figure(figsize=(7.2, 5.0))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.22, 1.0], height_ratios=[1.0, 1.0], hspace=0.42, wspace=0.35)

    ax1 = fig.add_subplot(gs[:, 0])
    width = 0.36
    ax1.bar(x - width / 2, df["pred_volume_ratio_mean"], width, color=[COLORS[s] for s in df["style"]], alpha=0.92, label="Volume")
    ax1.bar(x + width / 2, df["pred_extent_z_ratio_mean"], width, color=[COLORS[s] for s in df["style"]], alpha=0.42, hatch="//", label="z-extent")
    ax1.axhline(1.0, color="#444444", linewidth=0.9, linestyle="--")
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, rotation=25, ha="right")
    ax1.set_ylabel("Ratio relative to paired photo")
    ax1.set_ylim(0, 1.08)
    ax1.grid(axis="y", color=COLORS["grid"], linewidth=0.6, alpha=0.8)
    ax1.legend(loc="upper left", ncols=2)
    add_panel_label(ax1, "A")
    ax1.set_title("Stylised inputs shrink reconstructed geometry", loc="left", fontsize=9, fontweight="bold")
    for i, row in df.iterrows():
        ax1.text(i - width / 2, row["pred_volume_ratio_mean"] + 0.025, f'{row["pred_volume_ratio_mean"]:.2f}', ha="center", va="bottom", fontsize=6.5)

    ax2 = fig.add_subplot(gs[0, 1])
    for _, row in df.iterrows():
        s = row["style"]
        ax2.scatter(row["fscore_0.05_delta_mean"], row["pred_volume_ratio_mean"], s=78, color=COLORS[s], edgecolor="white", linewidth=0.7, zorder=3)
        ax2.text(row["fscore_0.05_delta_mean"] + 0.002, row["pred_volume_ratio_mean"] + 0.012, STYLE_LABELS[s], fontsize=6.7)
    ax2.axhline(1, color="#444444", linestyle="--", linewidth=0.8)
    ax2.axvline(0, color="#444444", linestyle="--", linewidth=0.8)
    ax2.set_xlabel("F-score@0.05 change vs. photo")
    ax2.set_ylabel("Volume ratio")
    ax2.set_xlim(-0.01, 0.105)
    ax2.set_ylim(0.18, 0.57)
    ax2.grid(color=COLORS["grid"], linewidth=0.6, alpha=0.8)
    add_panel_label(ax2, "B")
    ax2.set_title("Aggregate disagreement", loc="left", fontsize=9, fontweight="bold")

    ax3 = fig.add_subplot(gs[1, 1])
    matrix = df[["chamfer_l2_delta_mean", "fscore_0.05_delta_mean", "pred_volume_ratio_mean", "pred_extent_z_ratio_mean"]].to_numpy()
    # Scale each column to show direction without hiding numeric annotations.
    scaled = np.column_stack(
        [
            -matrix[:, 0] / max(abs(matrix[:, 0]).max(), 1e-9),
            matrix[:, 1] / max(abs(matrix[:, 1]).max(), 1e-9),
            1 - matrix[:, 2],
            1 - matrix[:, 3],
        ]
    )
    im = ax3.imshow(scaled, aspect="auto", cmap="RdYlBu_r", vmin=-1, vmax=1)
    ax3.set_yticks(np.arange(len(df)))
    ax3.set_yticklabels(labels)
    ax3.set_xticks(np.arange(4))
    ax3.set_xticklabels(["Chamfer\nimprov.", "F-score\nimprov.", "Volume\nloss", "z-loss"], rotation=0)
    for i in range(scaled.shape[0]):
        vals = [f'{-matrix[i,0]:.3f}', f'{matrix[i,1]:.3f}', f'{1-matrix[i,2]:.2f}', f'{1-matrix[i,3]:.2f}']
        for j, val in enumerate(vals):
            ax3.text(j, i, val, ha="center", va="center", fontsize=6.3)
    ax3.tick_params(length=0)
    add_panel_label(ax3, "C")
    ax3.set_title("Surface gains accompany volume loss", loc="left", fontsize=9, fontweight="bold")
    cbar = fig.colorbar(im, ax=ax3, fraction=0.04, pad=0.05)
    cbar.set_label("Directional strength", fontsize=7)
    save(fig, "fig2_main100_results")


def figure_robustness(main: pd.DataFrame, res: pd.DataFrame) -> None:
    m = main.set_index("style").loc[STYLE_ORDER]
    r = res.set_index("style").loc[STYLE_ORDER]
    labels = [STYLE_LABELS[s] for s in STYLE_ORDER]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2), sharey=True)
    for ax, metric, title in [
        (axes[0], "pred_volume_ratio_mean", "Volume ratio"),
        (axes[1], "pred_extent_z_ratio_mean", "z-extent ratio"),
    ]:
        if metric == "pred_volume_ratio_mean":
            offsets = {
                "edge": -0.006,
                "flat": 0.015,
                "low_detail": -0.020,
                "sketch": -0.016,
                "watercolor": 0.032,
            }
        else:
            offsets = {
                "edge": 0.015,
                "flat": 0.018,
                "low_detail": -0.018,
                "sketch": -0.018,
                "watercolor": 0.0,
            }
        for i, s in enumerate(STYLE_ORDER):
            y0 = float(m.loc[s, metric])
            y1 = float(r.loc[s, metric])
            ax.plot([0, 1], [y0, y1], color=COLORS[s], linewidth=1.8, marker="o", markersize=4.5)
            label_y = y1 + offsets.get(s, 0.0)
            ax.text(1.05, label_y, f"{STYLE_LABELS[s]} {y1:.2f}", ha="left", va="center", fontsize=6.5)
        ax.axhline(1, color="#444444", linestyle="--", linewidth=0.8)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Main100\nmc=64", "Robustness\nmc=128"])
        ax.set_xlim(-0.12, 1.42)
        ax.set_ylim(0.15, 1.08)
        ax.grid(axis="y", color=COLORS["grid"], linewidth=0.6, alpha=0.8)
        ax.set_title(title, loc="left", fontsize=9, fontweight="bold")
    axes[0].set_ylabel("Ratio relative to paired photo")
    add_panel_label(axes[0], "A")
    add_panel_label(axes[1], "B")
    fig.suptitle("Higher mesh-extraction resolution preserves the contraction pattern", y=1.02, fontsize=10, fontweight="bold")
    save(fig, "fig4_res128_robustness")


def main() -> None:
    setup()
    main_df = pd.read_csv(DATA / "m03_main100.csv")
    res_df = pd.read_csv(DATA / "m03_res128.csv")
    figure_framework(main_df)
    figure_main_results(main_df)
    figure_robustness(main_df, res_df)
    graphical_abstract(main_df)


if __name__ == "__main__":
    main()
