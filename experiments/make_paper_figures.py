"""Render five publication figures from the verified painting experiment archives."""

import argparse
import json
from hashlib import sha256 as hash_bytes
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
from matplotlib.font_manager import findfont
from matplotlib.patches import FancyBboxPatch, Patch
from matplotlib.ticker import MultipleLocator, PercentFormatter
from PIL import Image, ImageDraw, ImageFont, ImageOps

from analyze_followup import CONDITIONS
from audit_native_outputs import artwork_metadata, read_arm
from latent_aligned import grid_cover
from latent_mask_diagnostic import GRID_STRIDES, read_pixels, split_mask
from patch_design import MASK_FAMILIES
from run_followup import PAIRED_SEED
from run_pilot import SIZE, STRATA, read_json, sha256


ARCHIVED_SUMMARIES = {
    "cma": ("native-main-summary.json", "babeef02a7057d0abdce298caefacd9c1fab830e2db96924345d8fbb8b57c419"),
    "aic": ("aic-summary.json", "e0f6189a59731a47227aa4b96da8aec32cfd2c47bd92fd365e70e48f203394d0"),
}
COHORTS = {"cma": "Cleveland", "aic": "Chicago"}
MODELS = (
    ("shared", "lama", "LaMa", "#0072B2", "o", "-"),
    ("shared", "mat", "MAT", "#009E73", "s", "--"),
    ("diffusion", "powerpaint", "PowerPaint", "#D55E00", "^", "-."),
    ("diffusion", "sdxl", "SDXL", "#704A91", "D", ":"),
)
STYLES = {
    "font.family": "DejaVu Sans",
    "font.size": 8.5,
    "axes.titlesize": 9.5,
    "axes.labelsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#586572",
    "axes.labelcolor": "#162533",
    "xtick.color": "#162533",
    "ytick.color": "#162533",
    "text.color": "#162533",
    "figure.facecolor": "white",
    "pdf.fonttype": 42,
}
FAMILIES = {"crack": "Crack", "flake": "Flake", "loss": "Broad loss"}
MATERIALS = {
    "oil_canvas": "Oil on canvas", "oil_wood": "Oil on wood",
    "watercolor_paper": "Watercolor on paper", "ink_paper": "Ink on paper",
}
COHORT_COLORS = ("#22558A", "#D07920")
MASK_COLORS = ("#F1F3F4", "#B53D36", "#007681", "#BCE4E4")
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


def plotted_counts(summary):
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
        if (not 0 < count <= planned_works or count != pp_conditions[family, area]
                or set(values) != {model for _, model, *_ in MODELS}
                or not all(np.isfinite(value) and 0 <= value <= 1 for value in values.values())):
            raise ValueError(f"Invalid common-model denominator or MAE: {family}/{area}")
        per_condition.append({"family": family, "target_area": area, "matched_artworks": count, "masked_mae": values})
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


def workflow_figure():
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    fig.subplots_adjust(0.01, 0.02, 0.99, 0.99)
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis("off")

    def box(x, y, title, detail, face="#EEF3F8"):
        width, height = 0.385, 0.127
        ax.add_patch(FancyBboxPatch((x - width / 2, y - height / 2), width, height,
                                    boxstyle="round,pad=0.004,rounding_size=0.012",
                                    edgecolor="#648096", facecolor=face, linewidth=0.7))
        ax.text(x, y + 0.022, title, ha="center", va="center", weight="bold", fontsize=9.3)
        ax.text(x, y - 0.022, detail, ha="center", va="center", fontsize=8.05)

    def arrow(start, end):
        ax.annotate("", xy=end, xytext=start, arrowprops={
            "arrowstyle": "->", "linewidth": 0.85, "color": "#48677C", "shrinkA": 0, "shrinkB": 0,
        })

    box(0.255, 0.904, "Cleveland Museum of Art", "60 CC0 works • published full-size files")
    box(0.745, 0.904, "Art Institute of Chicago", "60 CC0 works • 1686 px-wide IIIF JPEG")
    box(0.5, 0.704, "Freeze reference crops and masks", "512 × 512 pixels • six damage conditions")
    box(0.255, 0.504, "Expand shared model input", "Hide every 8 × 8 cell touching the mask", "#E5F1F3")
    box(0.745, 0.504, "Hold original crop and mask", "Original scoring region and visible pixels")
    box(0.255, 0.304, "Run fixed configurations", "LaMa • MAT • PowerPaint • SDXL", "#E5F1F3")
    box(0.745, 0.304, "Composite and score", "Use predictions only inside the original mask")
    box(0.255, 0.104, "Record output coverage", "Available outputs / all planned conditions", "#F8EEE2")
    box(0.745, 0.104, "Compare paired works", "Full-reference errors by collection", "#F8EEE2")
    for x in (0.255, 0.745):
        arrow((x, 0.837), (0.5 + (x - 0.5) * 0.45, 0.771))
        arrow((0.5 + (x - 0.5) * 0.45, 0.637), (x, 0.571))
        arrow((x, 0.437), (x, 0.371))
        arrow((x, 0.237), (x, 0.171))
    arrow((0.452, 0.304), (0.548, 0.304))
    return fig


def examples_figure(examples):
    fig, axes = plt.subplots(3, 6, figsize=(7.2, 4.03))
    fig.subplots_adjust(left=0.025, right=0.985, bottom=0.05, top=0.831, wspace=0.035, hspace=0.28)
    headings = ("Reference", "Scoring mask", *(label for _, _, label, *_ in MODELS))
    for ax, title in zip(axes[0], headings, strict=True):
        ax.text(0.5, 1.235, title, transform=ax.transAxes, ha="center", va="bottom", weight="bold")
    for row, (metadata, panels) in enumerate(examples):
        for col, (ax, pixels) in enumerate(zip(axes[row], panels, strict=True)):
            ax.imshow(pixels, cmap="gray" if col == 1 else None, vmin=0 if col == 1 else None,
                      vmax=1 if col == 1 else None, interpolation="none")
            ax.axis("off")
        axes[row, 0].text(0, 1.036,
                          f"{FAMILIES[metadata['family']]} · {metadata['target_area']:.0%} · {metadata['artwork_id']}",
                          transform=axes[row, 0].transAxes, fontsize=8.1, va="bottom")
    return fig


def coverage_figure(examples):
    fig, axes = plt.subplots(3, 3, figsize=(5.85, 5.32))
    fig.subplots_adjust(left=0.047, right=0.982, bottom=0.136, top=0.90, wspace=0.08, hspace=0.25)
    titles = ("Original scoring mask", "Legacy nearest-neighbor grid", "Aligned 8 × 8 grid")
    for ax, title in zip(axes[0], titles, strict=True):
        ax.text(0.5, 1.20, title, transform=ax.transAxes, ha="center", va="bottom", weight="bold")
    for row, (metadata, panels) in enumerate(examples):
        for col, (ax, pixels) in enumerate(zip(axes[row], panels, strict=True)):
            cmap = ListedColormap((MASK_COLORS[0], "#182D3B") if col == 0 else MASK_COLORS)
            ax.imshow(pixels, cmap=cmap, vmin=0, vmax=1 if col == 0 else 3, interpolation="none")
            ax.set(xticks=[], yticks=[], xlim=(-0.5, pixels.shape[1] - 0.5), ylim=(pixels.shape[0] - 0.5, -0.5))
            for spine in ax.spines.values():
                spine.set_visible(False)
        axes[row, 0].text(0.5, 1.026, f"{FAMILIES[metadata['family']]} · {metadata['target_area']:.0%}",
                          transform=axes[row, 0].transAxes, ha="center", va="bottom", fontsize=8.1)
        missed = metadata["legacy_missed_mask_pixels"] / metadata["mask_pixels"]
        axes[row, 1].text(0.5, 1.026, f"{missed:.1%} of scoring mask missed",
                          transform=axes[row, 1].transAxes, ha="center", va="bottom", fontsize=8.1)
        axes[row, 2].text(0.5, 1.026, "Full mask coverage",
                          transform=axes[row, 2].transAxes, ha="center", va="bottom", fontsize=8.1)
    legend = [
        Patch(facecolor=MASK_COLORS[2], label="Scored and reached"),
        Patch(facecolor=MASK_COLORS[1], label="Scored and missed"),
        Patch(facecolor=MASK_COLORS[3], edgecolor="#78A7AB", linewidth=0.4, label="Reached outside scoring mask"),
    ]
    fig.legend(handles=legend, loc="lower center", bbox_to_anchor=(0.5, 0.043), ncols=3, frameon=False, fontsize=8)
    fig.text(0.5, 0.025, "The legacy grid samples the top-left pixel of each 8 × 8 cell.",
             ha="center", va="center", fontsize=8)
    return fig


def condition_figure(by_cohort):
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.38), sharey=True)
    fig.subplots_adjust(left=0.092, right=0.989, bottom=0.248, top=0.882, wspace=0.104)
    maximum = max(value for rows in by_cohort.values() for row in rows for value in row["masked_mae"].values())
    for ax, (cohort, rows) in zip(axes, by_cohort.items(), strict=True):
        xs = np.arange(len(rows))
        for _, model, label, color, marker, line in MODELS:
            ax.plot(xs, [row["masked_mae"][model] for row in rows],
                    label=label, color=color, marker=marker, linestyle=line, linewidth=1.45, markersize=4.6)
        ax.set_xticks(xs, [
            f"{'Loss' if row['family'] == 'loss' else FAMILIES[row['family']]}\n"
            f"{row['target_area']:.0%}\nn={row['matched_artworks']}" for row in rows
        ], fontsize=7.8)
        ax.tick_params(axis="x", length=0, pad=7)
        ax.set(xlim=(-0.30, len(rows) - 0.70), ylim=(0, max(0.1, maximum * 1.12)))
        ax.set_title(COHORTS[cohort], loc="left", fontweight="bold", pad=8)
        ax.yaxis.set_major_locator(MultipleLocator(0.1))
        ax.set_axisbelow(True)
        ax.grid(axis="y", color="#DCE3E8", linewidth=0.6)
    axes[0].set_ylabel("Mean masked MAE")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.018), ncols=4, frameon=False)
    return fig


def powerpaint_figure(by_cohort):
    fig, ax = plt.subplots(figsize=(6.5, 3.18))
    fig.subplots_adjust(left=0.255, right=0.989, bottom=0.31, top=0.968)
    ys = np.arange(len(STRATA))
    for cohort, rows, color, offset in zip(by_cohort, by_cohort.values(), COHORT_COLORS, (-0.18, 0.18), strict=True):
        shares = [row["completed"] / row["planned"] for row in rows]
        ax.barh(ys + offset, shares, height=0.33, color=color, label=COHORTS[cohort], zorder=3)
        for y, share, row in zip(ys, shares, rows, strict=True):
            ax.text(share + 0.012, y + offset, f"{row['completed']}/{row['planned']}", va="center", fontsize=8.3)
    ax.set_yticks(ys, [MATERIALS[stratum] for stratum in STRATA])
    ax.set(xlim=(0, 1.15), xlabel="Available proportion of planned conditions", ylim=(len(ys) - 0.47, -0.53))
    ax.set_xticks(np.arange(5) / 4)
    ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.tick_params(axis="y", length=0, pad=6)
    ax.grid(axis="x", color="#DCE3E8", linewidth=0.6)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_bounds(0, 1)
    handles, labels = ax.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.012), ncols=2, frameon=False)
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


def save_preview(directory, outputs):
    width, height, pad = 800, 478, 22
    canvas = Image.new("RGB", (2 * (width + pad) + pad, 3 * (height + pad) + pad), "#EAF0F3")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype(findfont("DejaVu Sans"), 19)
    names = ("Workflow", "Restoration examples", "Latent mask coverage", "MAE by condition", "PowerPaint availability")
    for index, (name, files) in enumerate(zip(names, outputs.values(), strict=True)):
        x = pad + (index % 2) * (width + pad)
        y = pad + (index // 2) * (height + pad)
        draw.rectangle((x, y, x + width - 1, y + height - 1), fill="white")
        draw.text((x + 14, y + 11), f"Figure {index + 1} · {name}", fill="#162533", font=font)
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
    args = parser.parse_args()
    roots = {"cma": args.cma_root.resolve(), "aic": args.aic_root.resolve()}
    output = args.output_dir.resolve()
    if output.exists() or any(output.is_relative_to(root) for root in roots.values()):
        parser.error("Figure directory must be new and outside the frozen runs")

    summaries = {cohort: load_summary(root, cohort) for cohort, root in roots.items()}
    cma = roots["cma"]
    prepared = cma / "prepared"
    source = read_json(prepared / "prepared.json")
    source_hash = summaries["cma"]["inputs_sha256"]["native_plan"]
    arms = {arm: read_arm(cma, arm, source, source_hash) for arm in ("shared", "diffusion")}
    for arm, (root, _, diagnostic_hash) in arms.items():
        hashes = summaries["cma"]["inputs_sha256"]["arms"][arm]
        if diagnostic_hash != hashes["diagnostics"] or sha256(root / "prepared.json") != hashes["prepared"]:
            raise ValueError(f"Cleveland diagnostics or plan differ from the published summary: {arm}")
    examples = [load_example(prepared, arms, case) for case in choose_examples(source["cases"], arms, 0.05)]
    masks = [load_coverage_mask(prepared, case) for case in choose_examples(source["cases"], arms, 0.01)]
    by_damage, by_material = {}, {}
    for cohort, summary in summaries.items():
        by_damage[cohort], by_material[cohort] = plotted_counts(summary)

    output.mkdir(parents=True)
    files = {}
    with plt.rc_context(STYLES):
        for stem, draw in (
            ("figure-1-workflow", workflow_figure),
            ("figure-2-examples", lambda: examples_figure(examples)),
            ("figure-3-latent-coverage", lambda: coverage_figure(masks)),
            ("figure-4-condition-mae", lambda: condition_figure(by_damage)),
            ("figure-5-powerpaint-coverage", lambda: powerpaint_figure(by_material)),
        ):
            files[stem] = save_figure(draw(), stem, output)
    preview = save_preview(output, files)
    manifest = {
        "protocol": "museum-painting-publication-figures-v1",
        "script_sha256": sha256(Path(__file__)), "matplotlib_version": matplotlib.__version__,
        "inference_seed": PAIRED_SEED,
        "summary_inputs": {cohort: {"file": filename, "sha256": digest}
                           for cohort, (filename, digest) in ARCHIVED_SUMMARIES.items()},
        "cma_plan_sha256": source_hash,
        "cma_diagnostic_sha256": {name: info[2] for name, info in arms.items()},
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
        "damage_condition_mae": by_damage,
        "powerpaint_coverage": by_material, "figures": files, "preview": preview,
    }
    (output / "figure-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8",
    )
    print(f"Verified archived inputs and wrote five figures plus a preview to {output}", flush=True)


if __name__ == "__main__":
    main()
