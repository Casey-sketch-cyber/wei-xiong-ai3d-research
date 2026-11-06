from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpecFromSubplotSpec


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "02_figures_tables" / "publication_figures"
LATEX_FIGS = ROOT / "01_manuscript" / "latex" / "figures"
ASSETS = ROOT / "02_figures_tables" / "real_sample_assets"
LOCAL_METRICS = ASSETS / "000074a334c541878360457c672b6c2e" / "eval_gt_metrics_all.csv"
PACKAGED_METRICS = ROOT / "experiment_outputs" / "eval_gt_metrics.csv"
RUN_METRICS = (
    ROOT.parents[1]
    / "data"
    / "autoresearch_runs"
    / "ar-20260604-163404-directed"
    / "m03_main100_metrics"
    / "eval_gt_metrics.csv"
)

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
    "grid": "#D8DEE9",
    "soft": "#F5F7FA",
}
CASE_UIDS = [
    "840d2861eb4441239d14fc7013c57e79",
    "02f2bd71a28a421c87288b35524df8d0",
]


def setup() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    LATEX_FIGS.mkdir(parents=True, exist_ok=True)
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
            "font.size": 7.2,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "axes.linewidth": 0.75,
            "legend.frameon": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
        }
    )


def metric_table() -> pd.DataFrame:
    if LOCAL_METRICS.exists():
        metrics_path = LOCAL_METRICS
    elif PACKAGED_METRICS.exists():
        metrics_path = PACKAGED_METRICS
    else:
        metrics_path = RUN_METRICS
    df = pd.read_csv(metrics_path)
    photo = (
        df[df["style"] == "photo"][
            ["uid", "pred_volume", "pred_extent_z", "fscore_0.05", "chamfer_l2"]
        ]
        .rename(
            columns={
                "pred_volume": "photo_volume",
                "pred_extent_z": "photo_extent_z",
                "fscore_0.05": "photo_fscore_0.05",
                "chamfer_l2": "photo_chamfer_l2",
            }
        )
    )
    rel = df[df["style"].isin(STYLE_ORDER)].merge(photo, on="uid", how="inner")
    rel["volume_ratio"] = rel["pred_volume"] / rel["photo_volume"].replace(0, np.nan)
    rel["z_extent_ratio"] = rel["pred_extent_z"] / rel["photo_extent_z"].replace(0, np.nan)
    rel["fscore_delta"] = rel["fscore_0.05"] - rel["photo_fscore_0.05"]
    rel["chamfer_delta"] = rel["chamfer_l2"] - rel["photo_chamfer_l2"]
    return rel.replace([np.inf, -np.inf], np.nan).dropna(subset=["volume_ratio", "fscore_delta"])


def add_panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(-0.075, 1.05, label, transform=ax.transAxes, fontsize=10, fontweight="bold", va="bottom")


def draw_tile(ax: plt.Axes, path: Path, title: str) -> None:
    ax.imshow(mpimg.imread(path))
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("#C8C8C8")
        spine.set_linewidth(0.65)
    ax.set_title(title, fontsize=6.7, pad=2.5)


def case_paths(uid: str) -> list[tuple[str, Path]]:
    base = ASSETS / uid
    return [
        ("Photo input", base / "inputs" / "input_photo.png"),
        ("Sketch input", base / "inputs" / "input_sketch.png"),
        ("from Photo", base / "triposr_renders" / "triposr_photo.png"),
        ("from Sketch", base / "triposr_renders" / "triposr_sketch.png"),
    ]


def draw_case_row(fig: plt.Figure, spec, rel: pd.DataFrame, uid: str, row_label: str, panel: str) -> None:
    sub = GridSpecFromSubplotSpec(1, 6, subplot_spec=spec, width_ratios=[1.02, 1, 1, 1, 1, 0.9], wspace=0.08)
    case = rel[(rel["uid"] == uid) & (rel["style"] == "sketch")].iloc[0]

    ax_text = fig.add_subplot(sub[0, 0])
    ax_text.axis("off")
    ax_text.text(0, 0.82, row_label, fontsize=8.3, fontweight="bold", ha="left", va="top")
    ax_text.text(0, 0.55, f"volume ratio\n{case['volume_ratio']:.3f}", fontsize=7.2, ha="left", va="top")
    ax_text.text(0, 0.25, f"F-score change\n+{case['fscore_delta']:.3f}", fontsize=7.2, ha="left", va="top")

    for j, (title, path) in enumerate(case_paths(uid), start=1):
        ax_img = fig.add_subplot(sub[0, j])
        draw_tile(ax_img, path, title)

    ax_note = fig.add_subplot(sub[0, 5])
    ax_note.axis("off")
    ax_note.text(
        0.0,
        0.5,
        "Surface score\nimproves,\nbut relative\nvolume\ncontracts.",
        fontsize=6.9,
        ha="left",
        va="center",
    )


def build() -> None:
    setup()
    rel = metric_table()

    fig = plt.figure(figsize=(7.4, 6.70))
    gs = fig.add_gridspec(3, 1, height_ratios=[1.52, 1.0, 1.0], hspace=0.45)

    ax = fig.add_subplot(gs[0, 0])
    for style in STYLE_ORDER:
        part = rel[rel["style"] == style]
        ax.scatter(
            part["fscore_delta"],
            part["volume_ratio"],
            s=14,
            color=COLORS[style],
            alpha=0.20,
            edgecolors="none",
            label=STYLE_LABELS[style],
        )

    means = rel.groupby("style", as_index=False)[["fscore_delta", "volume_ratio"]].mean()
    label_positions = {
        "edge": (0.030, 0.390),
        "flat": (0.060, 0.565),
        "low_detail": (0.033, 0.220),
        "sketch": (0.110, 0.205),
        "watercolor": (0.096, 0.405),
    }
    for _, row in means.iterrows():
        style = row["style"]
        ax.scatter(
            row["fscore_delta"],
            row["volume_ratio"],
            s=95,
            color=COLORS[style],
            edgecolor="white",
            linewidth=0.8,
            zorder=5,
        )
        ax.annotate(
            STYLE_LABELS[style],
            xy=(row["fscore_delta"], row["volume_ratio"]),
            xytext=label_positions[style],
            textcoords="data",
            fontsize=6.3,
            ha="center",
            va="center",
            zorder=6,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.62, "pad": 0.25},
            arrowprops={
                "arrowstyle": "-",
                "color": "#555555",
                "linewidth": 0.45,
                "shrinkA": 1,
                "shrinkB": 3,
            },
        )

    for uid in CASE_UIDS:
        case = rel[(rel["uid"] == uid) & (rel["style"] == "sketch")].iloc[0]
        ax.scatter(
            case["fscore_delta"],
            case["volume_ratio"],
            s=115,
            facecolor="none",
            edgecolor="#111111",
            linewidth=1.2,
            zorder=7,
        )

    ax.axhline(1.0, color="#444444", linestyle="--", linewidth=0.8)
    ax.axvline(0.0, color="#444444", linestyle="--", linewidth=0.8)
    ax.fill_between([0, 0.55], 0, 0.25, color="#F6E3E3", alpha=0.55, zorder=0)
    ax.text(
        0.205,
        0.105,
        "F-score improves;\nrelative volume contracts",
        fontsize=6.8,
        color="#7A1F1F",
        ha="left",
        va="center",
        bbox={"facecolor": "#F6E3E3", "edgecolor": "none", "alpha": 0.72, "pad": 0.6},
    )
    ax.set_xlim(-0.22, 0.55)
    ax.set_ylim(0, 1.25)
    ax.set_xlabel("F-score@0.05 change relative to photo")
    ax.set_ylabel("Volume ratio relative to photo")
    ax.grid(color=COLORS["grid"], linewidth=0.6, alpha=0.75)
    ax.set_title("Per-object surface--volume disagreement across 500 stylised reconstructions", loc="left", fontsize=8.9, fontweight="bold")
    fig.text(0.035, 0.942, "A", fontsize=10, fontweight="bold", ha="left", va="bottom")
    fig.text(0.035, 0.598, "B", fontsize=10, fontweight="bold", ha="left", va="bottom")
    fig.text(0.035, 0.333, "C", fontsize=10, fontweight="bold", ha="left", va="bottom")

    draw_case_row(fig, gs[1, 0], rel, CASE_UIDS[0], "Case 1\nsketch", "B")
    draw_case_row(fig, gs[2, 0], rel, CASE_UIDS[1], "Case 2\nsketch", "C")
    fig.subplots_adjust(left=0.085, right=0.985, top=0.940, bottom=0.085)

    for ext in ["svg", "pdf", "png", "tiff"]:
        kwargs = {"bbox_inches": "tight", "pad_inches": 0.10}
        if ext in {"png", "tiff"}:
            kwargs["dpi"] = 600
        fig.savefig(OUT / f"fig3_metric_paradox_cases.{ext}", **kwargs)
    fig.savefig(LATEX_FIGS / "fig3_metric_paradox_cases.pdf", bbox_inches="tight", pad_inches=0.10)
    fig.savefig(LATEX_FIGS / "fig3_metric_paradox_cases.png", dpi=300, bbox_inches="tight", pad_inches=0.10)
    plt.close(fig)


if __name__ == "__main__":
    build()
