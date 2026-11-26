"""Figure S1: forest plot of the protocol and sensitivity effects in Table S2 (masked MAE).

Reads only docs/paper/peerj-cs/figdata/protocol_effects.csv (metric == "mae"); no number is typed here.
Each panel has its own x-axis because the effects differ by two orders of magnitude (Gemini, writing
discussion, item 3). Grey band = the pre-specified +/-0.01 MAE practical margin; dashed line = no change.
Filled blue markers: the whole 95% CI lies outside the margin. Open grey markers: the CI touches it.

    python3 make_figS1.py [--fonts FIGGENIE/assets/fonts]   # writes fig.pdf, fig.png (3000 px wide), preview.png
"""
import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
CSV = ROOT / "docs/paper/peerj-cs/figdata/protocol_effects.csv"

MARGIN = 0.01
BLUE, GREY, BAND, INK, MUTED = "#4472C4", "#8C8C8C", "#E7E6E6", "#262626", "#595959"
SIZE_TITLE, SIZE_LABEL, SIZE_TICK = 7.5, 7.0, 6.5

PANELS = [
    ("A", "Original input masks", "vs. shared expanded mask"),
    ("B", "Edge-case exclusions", "vs. LaMa"),
    ("C", "Center-masked alignment pilot", "expanded vs. original mask"),
    ("D", "Prefill color at fixed SDXL settings", "model-card settings"),
    ("E", "Cleveland full-cohort ring-prefill configuration", "SDXL model-card setup + ring"),
    ("F", "Center-masked SDXL resolution, prompt and settings", ""),
]

# Row labels only; every value comes from the CSV.
LABELS = {
    "cma_lama_original_mask": "LaMa, original mask · CMA",
    "cma_mat_original_mask": "MAT, original mask · CMA",
    "aic_lama_original_mask": "LaMa, original mask · AIC",
    "aic_mat_original_mask": "MAT, original mask · AIC",
    "cma_sdxl_main_exclusion": "SDXL main · CMA without The Trinity",
    "cma_sdxl_ring_prefill_exclusion": "SDXL ring prefill · CMA without The Trinity",
    "aic_mat_main_exclusion": "MAT · AIC without card-mounted work",
    "aic_powerpaint_main_exclusion": "PowerPaint v1 · AIC without card-mounted work",
    "aic_sdxl_main_exclusion": "SDXL · AIC without card-mounted work",
    "center-mask-alignment-sdxl": "SDXL",
    "center-mask-alignment-lama": "LaMa",
    "prefill-native-ring-black": "Ring mean − black · native-scale pilot",
    "prefill-native-gray-ring": "Mid-gray − ring mean · native-scale pilot",
    "prefill-native-loss5-ring-black": "Ring mean − black · 5% contiguous loss",
    "prefill-center-gray-black": "Mid-gray − black · center-masked",
    "prefill-center-ring-black": "Ring mean − black · center-masked",
    "prefill-cma-ring-main": "vs. SDXL main setup",
    "prefill-cma-ring-lama": "vs. LaMa",
    "prefill-cma-ring-mat": "vs. MAT",
    "prefill-cma-ring-lama-oil-canvas": "vs. LaMa · oil on canvas",
    "prefill-cma-ring-lama-oil-wood": "vs. LaMa · oil on wood",
    "prefill-cma-ring-lama-watercolor-paper": "vs. LaMa · watercolor on paper",
    "prefill-cma-ring-lama-ink-paper": "vs. LaMa · ink on paper",
    "sdxl-center-main-1024-512": "SDXL 1024 − 512, main settings",
    "sdxl-center-empty-default": "Empty − restoration prompt",
    "sdxl-center-1024-lama": "SDXL 1024 − LaMa",
    "sdxl-center-empty-lama": "SDXL empty prompt − LaMa",
    "sdxl-center-1024-model-card-main": "Model-card − main settings, 1024",
    "sdxl-center-model-card-1024-512": "Model-card settings, 1024 − 512",
}


def setup_fonts(font_dir):
    family = "DejaVu Sans"
    if font_dir:
        for f in Path(font_dir).glob("Arimo-*.ttf"):
            font_manager.fontManager.addfont(str(f))
        if any(Path(font_dir).glob("Arimo-Regular.ttf")):
            family = "Arimo"  # metric-compatible with Arial, as in Figures 1-2
    plt.rcParams.update({
        "font.family": family, "pdf.fonttype": 42, "font.size": SIZE_TICK,
        "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.size": 0,
        "xtick.major.size": 2.5, "xtick.labelsize": SIZE_TICK, "axes.edgecolor": MUTED,
        "xtick.color": MUTED,
    })


def load_rows():
    rows = [r for r in csv.DictReader(CSV.open(encoding="utf-8")) if r["metric"] == "mae"]
    missing = [r["comparison_id"] for r in rows if r["comparison_id"] not in LABELS]
    if missing:
        raise SystemExit(f"no label for: {missing}")
    for r in rows:
        r["est"], r["lo"], r["hi"] = float(r["estimate"]), float(r["ci_low"]), float(r["ci_high"])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts", help="folder with Arimo-*.ttf (FigGenie assets/fonts)")
    args = ap.parse_args()
    setup_fonts(args.fonts)
    rows = load_rows()
    groups = [(p, [r for r in rows if r["table_panel"] == p[0]]) for p in PANELS]
    assert sum(len(g) for _, g in groups) == len(rows), "a CSV row is outside panels A-F"

    heights = [len(g) + 1.3 for _, g in groups]
    gap = 0.30  # inches between panels, room for each panel's tick labels
    H = 0.2 * sum(heights) + gap * (len(groups) - 1) + 0.95
    fig = plt.figure(figsize=(6.5, H))
    gs = fig.add_gridspec(len(groups), 1, height_ratios=heights,
                          hspace=gap / (0.2 * sum(heights) / len(groups)),
                          left=0.43, right=0.90, top=1 - 0.40 / H, bottom=0.55 / H)

    for i, ((key, title, sub), g) in enumerate(groups):
        ax = fig.add_subplot(gs[i])
        n = len(g)
        ys = list(range(n, 0, -1))
        lo = min([-MARGIN] + [r["lo"] for r in g])
        hi = max([MARGIN] + [r["hi"] for r in g])
        pad = 0.08 * (hi - lo)
        ax.set_xlim(lo - pad, hi + pad)
        ax.set_ylim(0.3, n + 1.25)
        ax.patch.set_alpha(0)
        ax.fill_betweenx([0.3, n + 0.5], -MARGIN, MARGIN, color=BAND, lw=0, zorder=0)
        ax.plot([0, 0], [0.3, n + 0.5], color=MUTED, lw=0.6, ls=(0, (3, 2)), zorder=1)
        for y, r in zip(ys, g):
            beyond = r["lo"] > MARGIN or r["hi"] < -MARGIN
            c = BLUE if beyond else GREY
            ax.plot([r["lo"], r["hi"]], [y, y], color=c, lw=1.2, solid_capstyle="round", zorder=2)
            ax.plot(r["est"], y, "o", ms=4.2, mew=1.0, mec=c, mfc=c if beyond else "white", zorder=3)
            ax.text(-0.012, y, LABELS[r["comparison_id"]], transform=ax.get_yaxis_transform(),
                    ha="right", va="center", fontsize=SIZE_LABEL, color=INK)
            ax.text(1.015, y, f"n = {r['n_works']}", transform=ax.get_yaxis_transform(),
                    ha="left", va="center", fontsize=SIZE_TICK, color=MUTED)
        head = f"{key}   {title}" + (f"  ({sub})" if sub else "")
        ax.text(-0.69, n + 0.75, head, transform=ax.get_yaxis_transform(), ha="left", va="center",
                fontsize=SIZE_TITLE, fontweight="bold", color=INK)
        ax.set_yticks([])
        for s in ("left", "right", "top"):
            ax.spines[s].set_visible(False)
        ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(5, symmetric=False))
        ax.tick_params(axis="x", pad=1.5)

    fig.text(0.665, 0.12 / H, "Paired difference in masked MAE (comparison − reference)",
             ha="center", va="bottom", fontsize=SIZE_LABEL, color=INK)
    legend = [
        Patch(facecolor=BAND, edgecolor="none", label="±0.01 practical margin"),
        Line2D([], [], color=BLUE, lw=1.2, marker="o", ms=4.2, mfc=BLUE, label="95% CI outside the margin"),
        Line2D([], [], color=GREY, lw=1.2, marker="o", ms=4.2, mfc="white", label="95% CI touches the margin"),
    ]
    fig.legend(handles=legend, loc="upper center", ncol=3, frameon=False, fontsize=SIZE_TICK,
               bbox_to_anchor=(0.5, 1 - 0.03 / H), handlelength=1.8, columnspacing=1.6)

    width_px = 3000
    fig.savefig(HERE / "fig.pdf")
    fig.savefig(HERE / "fig.png", dpi=width_px / 6.5)
    fig.savefig(HERE / "preview.png", dpi=170)
    print("wrote", HERE / "fig.pdf", HERE / "fig.png", HERE / "preview.png")


if __name__ == "__main__":
    main()
