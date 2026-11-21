"""Render publication figures 3–6 from the verified painting experiment archives."""

import argparse
import json
from hashlib import sha256 as hash_bytes
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.font_manager import FontProperties, findfont, fontManager
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.path import Path as MarkerPath
from matplotlib.ticker import FuncFormatter, LogLocator, NullLocator, PercentFormatter
from PIL import Image, ImageDraw, ImageFont, ImageOps

from analyze_followup import CONDITIONS
from analyze_native_main import ARMS
from audit_native_outputs import artwork_metadata
from latent_aligned import grid_cover
from latent_mask_diagnostic import GRID_STRIDES, read_pixels, split_mask
from patch_design import MASK_FAMILIES
from run_followup import PAIRED_SEED
from run_pilot import BOOTSTRAP_SEED, N_BOOTSTRAPS, SIZE, STRATA, read_json, sha256


ARCHIVED_SUMMARIES = {
    "cma": ("native-main-summary.json", "babeef02a7057d0abdce298caefacd9c1fab830e2db96924345d8fbb8b57c419"),
    "aic": ("aic-summary.json", "e0f6189a59731a47227aa4b96da8aec32cfd2c47bd92fd365e70e48f203394d0"),
}
COHORTS = {"cma": "Cleveland", "aic": "Chicago"}
MODELS = (
    ("shared", "lama", "LaMa", "o"),
    ("shared", "mat", "MAT", "s"),
    ("diffusion", "powerpaint", "PowerPaint v1", "^"),
    ("diffusion", "sdxl", "SDXL", "D"),
)
PAPER_WIDTH = 495 / 72
PAPER_STYLE = Path(__file__).with_name("paper_style.mplstyle")
INK = "#383848"
OUTLINE = "#8898B8"
MASK_COLORS = ("#F5F6F8", "#C00000", "#70AD47", "#DEEBF7")
FAMILIES = {"crack": "Crack", "flake": "Flake", "loss": "Broad loss"}
MATERIALS = {
    "oil_canvas": "Oil on canvas", "oil_wood": "Oil on wood",
    "watercolor_paper": "Watercolor on paper", "ink_paper": "Ink on paper",
}
SELECTION_SALT = "museum-painting-figures-v1"


def load_summary(root, cohort):
    name, expected_hash = ARCHIVED_SUMMARIES[cohort]
    path = root / "diagnostics" / name
    if sha256(path) != expected_hash:
        raise ValueError(f"Published summary SHA-256 differs: {path}")
    summary = read_json(path)
    plan = root / "prepared" / "prepared.json"
    if (summary["protocol"] != "native-main-paired-summary-v1" or summary.get("cohort", "cma") != cohort
            or summary["seed"] != PAIRED_SEED or sha256(plan) != summary["inputs_sha256"]["native_plan"]):
        raise ValueError(f"Unexpected cohort or source plan: {path}")
    return summary


def load_main_arms(root, summary, cohort):
    arms = {}
    for key in ("shared", "diffusion"):
        name, models, _ = ARMS[key]
        if cohort == "aic":
            name = name.replace("native-main", "aic-replication")
        arm = root / name
        diagnostic = root / "diagnostics" / f"{name}.json"
        hashes = summary["inputs_sha256"]["arms"][key]
        diagnostic_hash = sha256(diagnostic)
        if diagnostic_hash != hashes["diagnostics"] or sha256(arm / "prepared.json") != hashes["prepared"]:
            raise ValueError(f"Diagnostics or plan differ from the published summary: {cohort}/{key}")
        diagnostic_rows = read_json(diagnostic)["rows"]
        rows = {(row["case_id"], row["model"], row["seed"]): row for row in diagnostic_rows}
        if len(rows) != len(diagnostic_rows) or any(model not in models or seed != PAIRED_SEED
                                                    for _, model, seed in rows):
            raise ValueError(f"Unexpected or duplicate scores in {diagnostic}")
        arms[key] = arm, rows, diagnostic_hash
    return arms


def choose_examples(cases, arms, area):
    selected = []
    artworks = set()
    for family in MASK_FAMILIES:
        eligible = [
            case for case in cases
            if case["family"] == family and case["target_area"] == area and case["rights"] == "CC0"
            and case["artwork_id"] not in artworks
            and all((case["case_id"], model, PAIRED_SEED) in arms[arm][1] for arm, model, *_ in MODELS)
        ]
        if not eligible:
            raise ValueError(f"No eligible CC0 case for {family} {area:g}")
        chosen = min(eligible, key=lambda case: (
            hash_bytes(f"{SELECTION_SALT}|{case['case_id']}".encode("utf-8")).digest(), case["case_id"],
        ))
        selected.append(chosen)
        artworks.add(chosen["artwork_id"])
    return selected


def read_mask(prepared, case):
    mask = read_pixels(prepared / "masks" / case["mask_file"], case["mask_sha256"])
    if mask.shape != (SIZE, SIZE) or mask.dtype != np.uint8:
        raise ValueError(f"Invalid scoring-mask dimensions or type: {case['case_id']}")
    if not np.isin(mask, (0, 255)).all() or np.count_nonzero(mask) != case["mask_pixels"] or not mask.any():
        raise ValueError(f"Invalid scoring-mask values: {case['case_id']}")
    return mask > 0


def square_detail(mask, margin):
    ys, xs = np.where(mask)
    height, width = mask.shape
    left, right = int(xs.min()), int(xs.max()) + 1
    top, bottom = int(ys.min()), int(ys.max()) + 1
    side = min(max(right - left, bottom - top) + 2 * margin, height, width)
    x0 = min(max((left + right - side) // 2, 0), width - side)
    y0 = min(max((top + bottom - side) // 2, 0), height - side)
    return slice(y0, y0 + side), slice(x0, x0 + side)


def detail_bounds(detail):
    ys, xs = detail
    return [xs.start, ys.start, xs.stop, ys.stop]


def load_example(prepared, arms, case):
    case_id = case["case_id"]
    original = read_pixels(prepared / "originals" / f"{case_id}.png", case["crop_sha256"])
    if original.shape != (SIZE, SIZE, 3) or original.dtype != np.uint8:
        raise ValueError(f"Invalid saved RGB crop: {case_id}")
    mask = read_mask(prepared, case)
    detail = square_detail(mask, 20)
    example = {
        "case_id": case_id, **artwork_metadata(case),
        "family": case["family"], "target_area": case["target_area"],
        "crop_sha256": case["crop_sha256"], "mask_sha256": case["mask_sha256"],
        "detail_bbox_xyxy_exclusive": detail_bounds(detail), "outputs": {},
    }
    panels = [original[detail], mask[detail]]
    for arm, model, *_ in MODELS:
        root, rows, _ = arms[arm]
        row = rows[case_id, model, PAIRED_SEED]
        path = root / "restored" / f"{case_id}__{model}__s{PAIRED_SEED}.png"
        output = read_pixels(path, row["restored_sha256"])
        if (row["artwork_id"], row["stratum"]) != (case["artwork_id"], case["stratum"]):
            raise ValueError(f"Diagnostic identity mismatch: {path}")
        if output.shape != original.shape or output.dtype != original.dtype:
            raise ValueError(f"Invalid restoration dimensions or pixel type: {path}")
        if not np.array_equal(output[~mask], original[~mask]):
            raise ValueError(f"Restoration changed original pixels outside its scoring mask: {path}")
        mae = float(np.abs(output[mask].astype(np.int16) - original[mask].astype(np.int16)).mean() / 255)
        if mae != row["masked_mae"]:
            raise ValueError(f"Scored MAE differs from the saved masked pixels: {path}")
        example["outputs"][model] = {"sha256": row["restored_sha256"], "masked_mae": mae}
        panels.append(output[detail])
    return example, panels


def load_coverage_mask(prepared, case):
    mask = read_mask(prepared, case)
    stride = GRID_STRIDES["sdxl"]
    covered, missed = split_mask(mask, stride)
    sampled = np.zeros_like(mask)
    sampled[::stride, ::stride] = mask[::stride, ::stride]
    legacy, aligned = grid_cover(sampled, stride), grid_cover(mask, stride)
    if not np.array_equal(legacy & mask, covered) or np.any(mask & ~aligned):
        raise ValueError(f"Unexpected grid coverage: {case['case_id']}")
    detail = square_detail(mask, 2 * stride)
    counts = {
        "case_id": case["case_id"], "mask_sha256": case["mask_sha256"],
        "family": case["family"], "target_area": case["target_area"],
        "mask_pixels": int(mask.sum()), "legacy_covered_mask_pixels": int(covered.sum()),
        "legacy_missed_mask_pixels": int(missed.sum()), "aligned_covered_mask_pixels": int((mask & aligned).sum()),
        "detail_bbox_xyxy_exclusive": detail_bounds(detail),
    }
    legacy_codes = 3 * (legacy & ~mask) + 2 * covered + missed
    aligned_codes = 3 * (aligned & ~mask) + 2 * mask
    return counts, (mask[detail], legacy_codes[detail], aligned_codes[detail])


def common_mae_by_condition(cases, arms):
    by_condition = {condition: {} for condition in CONDITIONS}
    case_ids = {case["case_id"] for case in cases}
    if len(case_ids) != len(cases) or any(case_id not in case_ids for _, rows, _ in arms.values()
                                        for case_id, _, _ in rows):
        raise ValueError("Diagnostic case IDs do not match the frozen source plan")
    for case in sorted(cases, key=lambda row: row["case_id"]):
        case_id, artwork_id, stratum = (case[key] for key in ("case_id", "artwork_id", "stratum"))
        rows = [arms[arm][1].get((case_id, model, PAIRED_SEED)) for arm, model, *_ in MODELS]
        if any(row is None for row in rows):
            continue
        if any((row["artwork_id"], row["stratum"]) != (artwork_id, stratum) for row in rows):
            raise ValueError(f"Diagnostic case identity mismatch: {case_id}")
        condition = (case["family"], case["target_area"])
        if artwork_id in by_condition[condition]:
            raise ValueError(f"Multiple scores per artwork in the same condition: {artwork_id}/{condition}")
        values = [row["masked_mae"] for row in rows]
        if not all(np.isfinite(value) and 0 <= value <= 1 for value in values):
            raise ValueError(f"Invalid MAE scores: {case_id}")
        by_condition[condition][artwork_id] = values
    return by_condition


def plotted_counts(summary, cases, arms):
    common = common_mae_by_condition(cases, arms)
    models = [model for _, model, *_ in MODELS]
    planned_works = summary["planned_artworks"]
    matched = summary["primary"]["all_models"]
    powerpaint = summary["coverage"]["diffusion"]["powerpaint"]
    coverage = []
    per_condition = []
    if [(row["family"], row["target_area"]) for row in matched["by_condition"]] != list(CONDITIONS):
        raise ValueError("Model summary damage conditions differ from the frozen protocol")
    pp_conditions = {
        (row["family"], row["target_area"]): row["completed_outputs"] for row in powerpaint["by_condition"]
    }
    for row in matched["by_condition"]:
        family, area = row["family"], row["target_area"]
        count = row["overall"]["n_artworks"]
        values = row["overall"]["metrics"]["masked_mae"]["model_means"]
        work_scores = common[family, area]
        if (not 2 <= count <= planned_works or count != pp_conditions[family, area]
                or count != len(work_scores) or set(values) != set(models)):
            raise ValueError(f"Invalid common-model denominator or MAE: {family}/{area}")
        matrix = np.asarray(list(work_scores.values()))
        means = matrix.mean(axis=0)
        if not np.allclose(means, [values[model] for model in models], rtol=0, atol=1e-12):
            raise ValueError(f"Recomputed common-model MAE does not match the archived summary: {family}/{area}")
        # Sample the same artworks for all four columns within each condition.
        rng = np.random.default_rng(BOOTSTRAP_SEED)
        sample = rng.integers(count, size=(N_BOOTSTRAPS, count))
        intervals = np.percentile(matrix[sample].mean(axis=1), [2.5, 97.5], axis=0).T
        per_condition.append({
            "family": family, "target_area": area, "matched_artworks": count,
            "masked_mae": values, "masked_mae_ci95": dict(zip(models, intervals.tolist(), strict=True)),
        })
    for stratum in STRATA:
        row = powerpaint["by_stratum"][stratum]
        usable, planned = row["completed_outputs"], row["planned_outputs"]
        if (not 0 <= usable <= planned or planned != row["planned_artworks"] * len(CONDITIONS)
                or usable + row["safety_blocked_outputs"] != planned):
            raise ValueError(f"Unexpected PowerPaint availability denominator: {stratum}")
        coverage.append({"stratum": stratum, "completed": usable, "planned": planned})
    if (sum(row["completed"] for row in coverage) != sum(row["matched_artworks"] for row in per_condition)
            or sum(row["planned"] for row in coverage) != summary["planned_cases_per_model"]):
        raise ValueError("PowerPaint totals differ from common-model totals or the frozen plan")
    return per_condition, coverage


def examples_figure(examples):
    fig, axes = plt.subplots(3, 6, figsize=(PAPER_WIDTH, 3.85))
    fig.subplots_adjust(left=0.015, right=0.985, bottom=0.023, top=0.854, wspace=0.035, hspace=0.21)
    headings = ("Reference", "Scoring mask", *(label for _, _, label, *_ in MODELS))
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    for col, (ax, title) in enumerate(zip(axes[0], headings, strict=True)):
        if col >= 2:
            ax.add_patch(Rectangle((0.06, 1.161), 0.88, 0.019, transform=ax.transAxes,
                                   facecolor=colors[col - 2], edgecolor="none", clip_on=False))
        ax.text(0.5, 1.211, title, transform=ax.transAxes, ha="center", va="bottom", weight="bold",
                fontsize=7.5)
    for row, (metadata, panels) in enumerate(examples):
        for col, (ax, pixels) in enumerate(zip(axes[row], panels, strict=True)):
            ax.imshow(pixels, cmap="gray" if col == 1 else None, vmin=0 if col == 1 else None,
                      vmax=1 if col == 1 else None, interpolation="none")
            ax.add_patch(Rectangle((0, 0), 1, 1, transform=ax.transAxes,
                                   facecolor="none", edgecolor="white", linewidth=0.75, zorder=3))
            ax.axis("off")
            if col >= 2:
                key = MODELS[col - 2][1]
                value = metadata["outputs"][key]["masked_mae"]
                ax.text(0.958, 0.052, f"MAE {value:.4f}", transform=ax.transAxes,
                        ha="right", va="bottom", fontsize=6, zorder=4,
                        bbox={"boxstyle": "square,pad=0.20", "facecolor": "white", "edgecolor": "none", "alpha": 0.94})
        axes[row, 0].text(0, 1.036,
                          f"{FAMILIES[metadata['family']]} · {metadata['target_area']:.0%} · {metadata['artwork_id']}",
                          transform=axes[row, 0].transAxes, fontsize=6.5, va="bottom")
    return fig


def coverage_figure(examples):
    fig, axes = plt.subplots(3, 3, figsize=(PAPER_WIDTH, 4.96))
    fig.subplots_adjust(left=0.061, right=0.96, bottom=0.126, top=0.90, wspace=0.072, hspace=0.24)
    titles = ("Original scoring mask", "Legacy nearest-neighbor grid", "Aligned 8 × 8 grid")
    for ax, title in zip(axes[0], titles, strict=True):
        ax.text(0.5, 1.16, title, transform=ax.transAxes, ha="center", va="bottom", weight="bold", fontsize=7.5)
    for row, (metadata, panels) in enumerate(examples):
        for col, (ax, pixels) in enumerate(zip(axes[row], panels, strict=True)):
            cmap = ListedColormap((MASK_COLORS[0], INK) if col == 0 else MASK_COLORS)
            ax.imshow(pixels, cmap=cmap, vmin=0, vmax=1 if col == 0 else 3, interpolation="none")
            ax.set(xticks=[], yticks=[], xlim=(-0.5, pixels.shape[1] - 0.5), ylim=(pixels.shape[0] - 0.5, -0.5))
            for spine in ax.spines.values():
                spine.set_visible(False)
        axes[row, 0].text(0.5, 1.026, f"{FAMILIES[metadata['family']]} · {metadata['target_area']:.0%}",
                          transform=axes[row, 0].transAxes, ha="center", va="bottom")
        missed = metadata["legacy_missed_mask_pixels"] / metadata["mask_pixels"]
        axes[row, 1].text(0.5, 1.026, f"{missed:.1%} of scoring mask missed",
                          transform=axes[row, 1].transAxes, ha="center", va="bottom")
        axes[row, 2].text(0.5, 1.026, "Full mask coverage",
                          transform=axes[row, 2].transAxes, ha="center", va="bottom")
    check = MarkerPath([(-0.55, -0.05), (-0.18, -0.41), (0.57, 0.45)])
    legend = [
        Line2D([], [], marker=check, markerfacecolor="none", markeredgecolor=MASK_COLORS[2], markeredgewidth=1.1,
               linestyle="none", markersize=6, label="Covered scoring pixels"),
        Line2D([], [], marker="x", color=MASK_COLORS[1], linestyle="none", markersize=5.5, label="Missed scoring pixels"),
        Patch(facecolor=MASK_COLORS[3], edgecolor=OUTLINE, linewidth=0.75, label="Covered outside scoring mask"),
    ]
    fig.legend(handles=legend, loc="lower center", bbox_to_anchor=(0.5, 0.046), ncols=3, frameon=False)
    fig.text(0.5, 0.025, "The legacy grid samples the top-left pixel of each 8 × 8 cell.",
             ha="center", va="center")
    return fig


def condition_figure(by_cohort):
    fig, axes = plt.subplots(1, 2, figsize=(PAPER_WIDTH, 3.10), sharey=True)
    fig.subplots_adjust(left=0.096, right=0.991, bottom=0.244, top=0.899, wspace=0.102)
    intervals = [interval for rows in by_cohort.values() for row in rows
                 for interval in row["masked_mae_ci95"].values()]
    limits = (min(low for low, _ in intervals) * 0.82, max(high for _, high in intervals) * 1.17)
    if limits[0] <= 0:
        raise ValueError("Log-scale MAE chart requires positive interval endpoints")
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
    for ax, (cohort, rows) in zip(axes, by_cohort.items(), strict=True):
        xs = np.arange(len(rows))
        for (_, model, label, marker), color, offset in zip(MODELS, colors, (-0.24, -0.08, 0.08, 0.24), strict=True):
            means = np.asarray([row["masked_mae"][model] for row in rows])
            lows, highs = np.asarray([row["masked_mae_ci95"][model] for row in rows]).T
            pos = xs + offset
            ax.vlines(pos, lows, highs, color=color, linewidth=0.85, zorder=2)
            ax.hlines(lows, pos - 0.038, pos + 0.038, color=color, linewidth=0.75, zorder=2)
            ax.hlines(highs, pos - 0.038, pos + 0.038, color=color, linewidth=0.75, zorder=2)
            ax.plot(pos, means, label=label, color=color, marker=marker, linestyle="none",
                    markersize=4.2, markeredgecolor=INK, markeredgewidth=0.38, zorder=3)
        ax.set_xticks(xs, [
            f"{'Loss' if row['family'] == 'loss' else FAMILIES[row['family']]}\n"
            f"{row['target_area']:.0%}\nn={row['matched_artworks']}" for row in rows
        ])
        ax.tick_params(axis="x", length=0, pad=5)
        ax.set(xlim=(-0.48, len(rows) - 0.52), yscale="log", ylim=limits)
        ax.set_title(COHORTS[cohort], loc="left", fontweight="bold", pad=6)
        ax.yaxis.set_major_locator(LogLocator(base=10, subs=(1, 2, 5)))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:g}"))
        ax.yaxis.set_minor_locator(NullLocator())
        ax.set_axisbelow(True)
        ax.grid(axis="y", color="#DCE3E8", linewidth=0.75)
    axes[0].set_ylabel("Masked MAE (log scale)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.018), ncols=4, frameon=False)
    return fig


def powerpaint_figure(by_cohort):
    fig, axes = plt.subplots(1, 2, figsize=(PAPER_WIDTH, 2.52), sharey=True)
    fig.subplots_adjust(left=0.186, right=0.982, bottom=0.329, top=0.875, wspace=0.154)
    ys = np.arange(len(STRATA))
    for ax, (cohort, rows) in zip(axes, by_cohort.items(), strict=True):
        shares = np.asarray([row["completed"] / row["planned"] for row in rows])
        ax.barh(ys, shares, height=0.61, color=MASK_COLORS[3], edgecolor=OUTLINE, linewidth=0.75, zorder=3)
        ax.barh(ys, 1 - shares, left=shares, height=0.61, color=MASK_COLORS[1], edgecolor="white",
                linewidth=0.5, hatch="///", zorder=4)
        for y, share, row in zip(ys, shares, rows, strict=True):
            center = share / 2 if share >= 0.18 else (1 + share) / 2
            ax.text(center, y, f"{row['completed']}/{row['planned']}", ha="center", va="center",
                    color=INK if share >= 0.18 else "white", zorder=5)
        ax.set(xlim=(0, 1), ylim=(len(ys) - 0.48, -0.52))
        ax.set_xticks(np.arange(5) / 4)
        ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
        ax.tick_params(axis="y", length=0, pad=5)
        ax.grid(axis="x", color="#DCE3E8", linewidth=0.75)
        ax.spines["left"].set_visible(False)
        ax.set_title(COHORTS[cohort], loc="left", fontweight="bold", pad=6)
    axes[0].set_yticks(ys, [MATERIALS[stratum] for stratum in STRATA])
    fig.supxlabel("Proportion of planned PowerPaint conditions", y=0.147, fontsize=6.5)
    legend = [
        Patch(facecolor=MASK_COLORS[3], edgecolor=OUTLINE, linewidth=0.75, label="Scored"),
        Patch(facecolor=MASK_COLORS[1], edgecolor="white", hatch="///", label="Withheld"),
    ]
    fig.legend(handles=legend, loc="lower center", bbox_to_anchor=(0.5, 0.025), ncols=2, frameon=False)
    return fig


def save_figure(fig, stem, directory):
    paths = {}
    for extension in ("pdf", "png"):
        path = directory / f"{stem}.{extension}"
        metadata = {"CreationDate": None, "ModDate": None} if extension == "pdf" else None
        fig.savefig(path, dpi=300, facecolor="white", metadata=metadata)
        paths[extension] = {"file": path.name, "sha256": sha256(path)}
    plt.close(fig)
    return paths


def save_preview(directory, outputs, font_path):
    width, height, pad = 800, 478, 22
    canvas = Image.new("RGB", (2 * (width + pad) + pad, 2 * (height + pad) + pad), "#EAF0F3")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(font_path, 19)
    names = ("Restoration examples", "Latent mask coverage", "MAE by condition", "PowerPaint availability")
    for index, (name, files) in enumerate(zip(names, outputs.values(), strict=True)):
        x = pad + (index % 2) * (width + pad)
        y = pad + (index // 2) * (height + pad)
        draw.rectangle((x, y, x + width - 1, y + height - 1), fill="white")
        draw.text((x + 14, y + 11), f"Figure {index + 3} · {name}", fill=INK, font=font)
        with Image.open(directory / files["png"]["file"]) as image:
            fit = ImageOps.contain(image.convert("RGB"), (width - 16, height - 55))
            canvas.paste(fit, (x + (width - fit.width) // 2, y + 46))
    path = directory / "preview-contact-sheet.png"
    canvas.save(path)
    return {"file": path.name, "sha256": sha256(path)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cma-root", type=Path, required=True, help="Frozen Cleveland native-main run directory")
    parser.add_argument("--aic-root", type=Path, required=True, help="Frozen Chicago replication run directory")
    parser.add_argument("--output-dir", type=Path, required=True, help="New figure directory on the data disk")
    parser.add_argument("--font-dir", type=Path, help="Arimo font directory from the pinned FigGenie checkout")
    args = parser.parse_args()
    roots = {"cma": args.cma_root.resolve(), "aic": args.aic_root.resolve()}
    output = args.output_dir.resolve()
    if output.exists() or any(output.is_relative_to(root) for root in roots.values()):
        parser.error("Figure directory must be new and outside the frozen runs")
    if args.font_dir:
        for style in ("Regular", "Bold"):
            fontManager.addfont(args.font_dir / f"Arimo-{style}.ttf")

    summaries = {cohort: load_summary(root, cohort) for cohort, root in roots.items()}
    plans = {cohort: read_json(root / "prepared" / "prepared.json") for cohort, root in roots.items()}
    arms = {cohort: load_main_arms(root, summaries[cohort], cohort) for cohort, root in roots.items()}
    prepared = roots["cma"] / "prepared"
    cma_cases = plans["cma"]["cases"]
    examples = [load_example(prepared, arms["cma"], case) for case in choose_examples(cma_cases, arms["cma"], 0.05)]
    masks = [load_coverage_mask(prepared, case) for case in choose_examples(cma_cases, arms["cma"], 0.01)]
    by_damage, by_material = {}, {}
    for cohort, summary in summaries.items():
        by_damage[cohort], by_material[cohort] = plotted_counts(summary, plans[cohort]["cases"], arms[cohort])

    output.mkdir(parents=True)
    files = {}
    with plt.style.context(PAPER_STYLE):
        font_path = findfont(FontProperties(family=plt.rcParams["font.sans-serif"]))
        for stem, draw in (
            ("figure-3-examples", lambda: examples_figure(examples)),
            ("figure-4-latent-coverage", lambda: coverage_figure(masks)),
            ("figure-5-condition-mae", lambda: condition_figure(by_damage)),
            ("figure-6-powerpaint-coverage", lambda: powerpaint_figure(by_material)),
        ):
            files[stem] = save_figure(draw(), stem, output)
    preview = save_preview(output, files, font_path)
    manifest = {
        "protocol": "museum-painting-publication-figures-v2",
        "script_sha256": sha256(Path(__file__)), "matplotlib_version": matplotlib.__version__,
        "style": {"file": PAPER_STYLE.name, "sha256": sha256(PAPER_STYLE),
                  "resolved_font_family": FontProperties(fname=font_path).get_name(), "width_pt": 495},
        "inference_seed": PAIRED_SEED,
        "summary_inputs": {
            cohort: {
                "file": filename, "sha256": digest, "plan_sha256": summaries[cohort]["inputs_sha256"]["native_plan"],
                "diagnostic_sha256": {arm: info[2] for arm, info in arms[cohort].items()},
            }
            for cohort, (filename, digest) in ARCHIVED_SUMMARIES.items()
        },
        "illustrative_selection": {
            "rule": "In crack, flake, loss order, minimize SHA256(salt|case_id) among CC0 cases of the fixed area "
                    "with all four main outputs; use distinct artworks within each figure.",
            "salt": SELECTION_SALT, "example_area": 0.05, "coverage_area": 0.01,
            "details": "Show identical square detail within each row; bounding boxes use half-open "
                       "xyxy coordinates in the 512-pixel crop.",
            "legacy_mask_coverage": "Sample at (x,y)=(0,0),(8,0),… on a top-left-origin 8-pixel grid "
                                    "and expand each sampled mask value to its block.",
        },
        "examples": [case for case, _ in examples], "latent_coverage_examples": [case for case, _ in masks],
        "condition_mae_bootstrap": {
            "method": "Unadjusted 95% percentile intervals for individual model means",
            "resampling_unit": "Artwork with scores for all four models within the museum and mask condition",
            "resamples": N_BOOTSTRAPS, "seed": BOOTSTRAP_SEED,
            "shared_draws": "Identical resampled artwork indices for all four models within each condition",
        },
        "damage_condition_mae": by_damage,
        "powerpaint_coverage": by_material, "figures": files, "preview": preview,
    }
    (output / "figure-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8",
    )
    print(f"Verified archived inputs and wrote figures 3–6 plus a preview to {output}", flush=True)


if __name__ == "__main__":
    main()
