from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSETS = (
    ROOT
    / "02_figures_tables"
    / "confirmatory_4model_20260729"
    / "fig1_framework_assets"
)
OUT = ROOT / "03_submission_materials"

MODEL_LABELS = ["TripoSR", "InstantMesh", "Hunyuan3D 2.1", "TRELLIS"]
MODEL_FILES = [
    "triposr_sketch.png",
    "instantmesh_sketch.png",
    "hunyuan21_sketch.png",
    "trellis_sketch.png",
]
DELTA_F05 = np.array([-0.006964, -0.207949, -0.006444, -0.003047])
DELTA_IOU = np.array([-0.015821, -0.230103, -0.002381, 0.006031])


def load_rgb(name: str) -> Image.Image:
    return Image.open(ASSETS / name).convert("RGB")


def image_tile(ax, image: Image.Image, label: str, border: str = "#c8ced8") -> None:
    ax.imshow(image)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_edgecolor(border)
        spine.set_linewidth(0.8)
    ax.set_xlabel(label, fontsize=7.4, labelpad=2.5)


def add_panel_background(
    fig: plt.Figure,
    x: float,
    y: float,
    w: float,
    h: float,
    colour: str,
) -> None:
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.004,rounding_size=0.012",
        linewidth=0,
        facecolor=colour,
        transform=fig.transFigure,
        zorder=-10,
    )
    fig.patches.append(patch)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {
            "font.family": "Arial",
            "font.size": 8,
            "axes.titlesize": 9.3,
            "axes.titleweight": "bold",
            "axes.labelsize": 8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )

    # 10 x 4 inches at 300 dpi gives 3000 x 1200 pixels (exact 5:2 ratio).
    fig = plt.figure(figsize=(10, 4), dpi=300, facecolor="white")
    add_panel_background(fig, 0.018, 0.08, 0.285, 0.84, "#f4f7fb")
    add_panel_background(fig, 0.318, 0.08, 0.338, 0.84, "#f7f7f5")
    add_panel_background(fig, 0.671, 0.08, 0.311, 0.84, "#fff7f5")

    fig.text(
        0.042,
        0.865,
        "Matched input shift",
        fontsize=10.2,
        fontweight="bold",
        color="#20242b",
    )
    fig.text(
        0.342,
        0.865,
        "Same object, four systems",
        fontsize=10.2,
        fontweight="bold",
        color="#20242b",
    )
    fig.text(
        0.695,
        0.865,
        "Sketch response is model-specific",
        fontsize=10.2,
        fontweight="bold",
        color="#20242b",
    )

    left_grid = fig.add_gridspec(
        1,
        2,
        left=0.042,
        right=0.279,
        bottom=0.30,
        top=0.79,
        wspace=0.12,
    )
    image_tile(fig.add_subplot(left_grid[0, 0]), load_rgb("input_photo.png"), "Photo")
    image_tile(fig.add_subplot(left_grid[0, 1]), load_rgb("input_sketch.png"), "Sketch")
    fig.text(
        0.1605,
        0.175,
        "Same 3D object  |  same camera  |  same foreground",
        ha="center",
        va="center",
        fontsize=7.5,
        color="#344054",
    )

    centre_grid = fig.add_gridspec(
        2,
        2,
        left=0.342,
        right=0.632,
        bottom=0.235,
        top=0.79,
        hspace=0.25,
        wspace=0.10,
    )
    for axis, filename, label in zip(
        [fig.add_subplot(centre_grid[i, j]) for i in range(2) for j in range(2)],
        MODEL_FILES,
        MODEL_LABELS,
    ):
        image_tile(axis, load_rgb(filename), label)
    fig.text(
        0.487,
        0.137,
        "6,240 completed reconstructions against watertight ground truth",
        ha="center",
        fontsize=7.7,
        color="#344054",
    )

    ax = fig.add_axes([0.704, 0.285, 0.245, 0.48])
    y = np.arange(len(MODEL_LABELS))
    bar_h = 0.28
    colour_f = "#2f78b7"
    colour_iou = "#dc6b52"
    ax.barh(y - bar_h / 2, DELTA_F05, height=bar_h, color=colour_f, label=r"$\Delta F_{0.05}$")
    ax.barh(y + bar_h / 2, DELTA_IOU, height=bar_h, color=colour_iou, label=r"$\Delta$ voxel IoU")
    ax.axvline(0, color="#4b5563", linewidth=0.8)
    ax.set_xlim(-0.255, 0.035)
    ax.set_yticks(y)
    ax.set_yticklabels(MODEL_LABELS, fontsize=7.2)
    ax.invert_yaxis()
    ax.set_xlabel("Mean change from paired photo", fontsize=7.2, labelpad=3)
    ax.tick_params(axis="x", labelsize=6.8)
    ax.grid(axis="x", color="#d7dce3", linewidth=0.55, alpha=0.9)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.legend(
        loc="lower left",
        bbox_to_anchor=(0.0, 1.01),
        ncol=2,
        frameon=False,
        fontsize=7.0,
        handlelength=1.2,
        columnspacing=1.0,
    )

    fig.text(
        0.826,
        0.155,
        "Universal sketch-gap gate: 0/4 models",
        ha="center",
        va="center",
        fontsize=8.2,
        fontweight="bold",
        color="#9b2c2c",
    )
    fig.text(
        0.826,
        0.105,
        "Use surface, solid, topology, and multi-view diagnostics together",
        ha="center",
        va="center",
        fontsize=6.9,
        color="#344054",
    )

    png = OUT / "Graphical_abstract.png"
    pdf = OUT / "Graphical_abstract.pdf"
    tiff = OUT / "Graphical_abstract.tiff"
    fig.savefig(png, dpi=300, facecolor="white")
    fig.savefig(pdf, dpi=300, facecolor="white")
    fig.savefig(tiff, dpi=300, facecolor="white", pil_kwargs={"compression": "tiff_lzw"})
    plt.close(fig)
    print(png)
    print(pdf)
    print(tiff)


if __name__ == "__main__":
    main()
