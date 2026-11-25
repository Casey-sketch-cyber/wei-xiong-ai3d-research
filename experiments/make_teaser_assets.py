"""Bitmaps for the Figure 1 teaser and Figure 2 pipeline (drawn with FigGenie, see docs/paper/FIGURE_SPEC.md).

The mask geometry is rebuilt from the frozen procedural design (patch_design.design_mask) with the main
experiment's seed rule, so the coverage tiles show the real scoring mask and the real 8x8 nearest-neighbour
sampling.  Painting crops and SDXL outputs come from the server archive; when a file is not given, a neutral
placeholder is written so the layout can be reviewed.

    python experiments/make_teaser_assets.py --out docs/paper/figures/src/fig1 \
        --crop <frozen 512 crop of the chosen case> --slot <within-group position of that case> \
        --sdxl-black <png> --sdxl-gray <png> --sdxl-ring <png>
"""

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from patch_design import MASK_AREAS, MASK_FAMILIES, design_mask
from latent_aligned import grid_cover
from latent_mask_diagnostic import digest, read_pixels
from models import _diffusion_input

NATIVE_SEED = 20261119  # run_followup.NATIVE_SEED
STRIDE = 8
SELECTION_SALT = "museum-painting-figures-v1"
PREFILL_SUFFIX = "_loss_05"
FIRST_FIGURES_SHA = "ae3791716c3a9eaf7dbe6734876aa7a9cccf1e9fa155c8cfc529782e6b7d5326"
CMA_SUMMARY_SHA = "babeef02a7057d0abdce298caefacd9c1fab830e2db96924345d8fbb8b57c419"
PREFILL_SUMMARY_SHA = "e18163e5dddc67fb2596dcb2af30577412d1e13cf3b7664fba33fe1b7384521d"
RIGHT = (112, 173, 71)    # covered pixels  #70AD47
WRONG = (192, 0, 0)       # missed pixels   #C00000
CELL = (68, 114, 196)     # latent cell edges #4472C4


def mask_seed(slot: int, family: str, area: float) -> int:
    return NATIVE_SEED + slot * 100 + MASK_FAMILIES.index(family) * 10 + MASK_AREAS.index(area)


def checked_json(path: Path, expected_sha256: str) -> dict:
    if digest(path) != expected_sha256:
        raise ValueError(f"Frozen JSON checksum mismatch: {path}")
    return json.loads(path.read_bytes())


def artwork_files(directory: Path, case: dict) -> tuple[Path, np.ndarray, np.ndarray]:
    crop_path = directory / "originals" / f"{case['case_id']}.png"
    crop = read_pixels(crop_path, case["crop_sha256"])
    mask = read_pixels(directory / "masks" / case["mask_file"], case["mask_sha256"]) > 0
    if case["rights"] != "CC0" or crop.shape != (512, 512, 3) or mask.shape != crop.shape[:2]:
        raise ValueError(f"Unexpected frozen artwork or mask: {case['case_id']}")
    return crop_path, crop, mask


def verify_output(path: Path, digest_value: str, crop: np.ndarray, mask: np.ndarray) -> None:
    output = read_pixels(path, digest_value)
    if output.shape != crop.shape or not np.array_equal(output[~mask], crop[~mask]):
        raise ValueError(f"Output does not preserve the frozen crop outside the scoring mask: {path}")


def archive_inputs(project: Path, args: argparse.Namespace) -> dict:
    """Select and verify the two distinct published examples before rendering."""
    prefill = project / "runs/sdxl-prefill-20261120"
    prefill_summary = checked_json(prefill / "diagnostics/prefill-summary.json", PREFILL_SUMMARY_SHA)
    # Figure 1(b) is shown zoomed on the hole, so the example is drawn from the 5% broad-loss conditions only
    # (rule fixed before rerunning, 2026-11-23); within them the first case by the same salted hash.
    rows = [row for row in prefill_summary["cohorts"]["native"]["rows"] if row["case_id"].endswith(PREFILL_SUFFIX)]
    sample = min(rows, key=lambda row: sha256(f"{SELECTION_SALT}|{row['case_id']}".encode()).hexdigest())
    prefill_id = sample["case_id"]
    arms = {"black": project / "runs/official-inference-20261119/official-native",
            "gray": prefill / "gray-native", "ring": prefill / "ring-native"}
    locks = {name: json.loads((root / "prepared.json").read_bytes()) for name, root in arms.items()}
    cases = {name: next(row for row in lock["cases"] if row["case_id"] == prefill_id)
             for name, lock in locks.items()}
    black_case = cases["black"]
    _, prefill_crop, prefill_mask = artwork_files(arms["black"], black_case)
    for name, root in arms.items():
        case = cases[name]
        if (locks[name]["reference_plan_sha256"] != locks["black"]["reference_plan_sha256"]
                or case["artwork_id"] != sample["artwork_id"]
                or any(case[key] != black_case[key] for key in ("crop_sha256", "mask_sha256"))):
            raise ValueError(f"Mismatched SDXL prefill trial: {name}")
        artwork_files(root, case)
        path = root / "restored" / f"{prefill_id}__sdxl__s2026.png"
        verify_output(path, sample["scores"][name]["restored_sha256"], prefill_crop, prefill_mask)
        setattr(args, f"sdxl_{name}", path)
    enlarged = grid_cover(prefill_mask, STRIDE)
    ring_rgb = _diffusion_input(prefill_crop, enlarged, "ring")[enlarged][0]
    ring_hex = "#" + "".join(f"{value:02X}" for value in ring_rgb)
    (args.out / "ring_mean.json").write_text(json.dumps({"hex": ring_hex}) + "\n", encoding="utf-8")

    cma = project / "runs/native-main-20261120"
    summary = checked_json(cma / "diagnostics/native-main-summary.json", CMA_SUMMARY_SHA)
    inputs = summary["inputs_sha256"]
    prepared = cma / "prepared"
    plan = checked_json(prepared / "prepared.json", inputs["native_plan"])
    by_id = {row["case_id"]: row for row in plan["cases"]}
    # Figure 1(a) and Figure 2 use the artwork already chosen for Figure 1(b), so all three show one painting
    # (rule fixed 2026-11-25 before rerunning; the earlier example, a dark oil on wood, made thin masks hard to see).
    matches = [row for row in plan["cases"]
               if row["artwork_id"] == sample["artwork_id"] and row["case_id"].endswith("_crack_01")]
    if len(matches) != 1:
        raise ValueError(f"Figure 1(b) artwork {sample['artwork_id']} has {len(matches)} 1% crack cases in the main plan")
    example = matches[0]
    case_prefix = example["case_id"].removesuffix("_crack_01")
    args.slot = int(case_prefix.rsplit("_", 1)[1])
    args.crop, crop, _ = artwork_files(prepared, example)
    if example["mask_seed"] != mask_seed(args.slot, "crack", 0.01):
        raise ValueError("The Figure 1(a) mask seed does not follow the frozen seed rule")
    for family in MASK_FAMILIES:
        for area in MASK_AREAS:
            case = by_id[f"{case_prefix}_{family}_{int(area * 100):02d}"]
            _, _, mask = artwork_files(prepared, case)
            seed = mask_seed(args.slot, family, area)
            if (case["artwork_id"] != example["artwork_id"] or case["crop_sha256"] != example["crop_sha256"]
                    or case["mask_seed"] != seed or not np.array_equal(mask, design_mask(family, area, seed))):
                raise ValueError(f"Reconstructed Figure 2 mask does not match the freeze: {case['case_id']}")

    composite_id = f"{case_prefix}_crack_05"
    _, _, score_mask = artwork_files(prepared, by_id[composite_id])
    lama = checked_json(cma / "diagnostics/native-main-shared.json", inputs["arms"]["shared"]["diagnostics"])
    composite = next(row for row in lama["rows"] if row["case_id"] == composite_id and row["model"] == "lama")
    args.composite = cma / "native-main-shared/restored" / f"{composite_id}__lama__s2026.png"
    verify_output(args.composite, composite["restored_sha256"], crop, score_mask)

    return {
        "alignment_case": {key: example[key] for key in
                           ("case_id", "artwork_id", "title", "artist", "source_url", "crop_sha256", "mask_sha256")},
        "composite_case": {"case_id": composite_id, "sha256": composite["restored_sha256"]},
        "prefill_case": {key: black_case[key] for key in
                         ("case_id", "artwork_id", "title", "artist", "source_url", "crop_sha256", "mask_sha256")},
        "prefill_outputs": sample["scores"],
        "ring_mean": ring_hex,
    }


def nearest_cover(mask: np.ndarray) -> np.ndarray:
    """Cells kept by top-left nearest-neighbour downsampling, expanded back to pixels."""
    keep = mask[::STRIDE, ::STRIDE]
    return np.kron(keep, np.ones((STRIDE, STRIDE), dtype=bool))[: mask.shape[0], : mask.shape[1]]


def placeholder(size: int, seed: int) -> Image.Image:
    """Muted painterly placeholder, clearly not a real painting."""
    rng = np.random.default_rng(seed)
    small = rng.normal(0, 1, (6, 6))
    lum = np.asarray(Image.fromarray(np.uint8(np.clip(128 + 30 * small, 0, 255))).resize((size, size), Image.BICUBIC),
                     dtype=float)
    arr = lum[..., None] * np.array([1.0, 0.86, 0.66]) + np.array([30, 28, 22])
    return Image.fromarray(np.uint8(np.clip(arr, 0, 255)))


def best_window(mask: np.ndarray, cover: np.ndarray, cells: int) -> tuple[int, int]:
    """Grid-aligned window with the most hole pixels, preferring a mix of covered and missed ones."""
    w = cells * STRIDE
    best, pos = -1.0, (0, 0)
    for y in range(0, mask.shape[0] - w + 1, STRIDE):
        for x in range(0, mask.shape[1] - w + 1, STRIDE):
            m = mask[y:y + w, x:x + w]
            hit = (m & cover[y:y + w, x:x + w]).sum()
            miss = (m & ~cover[y:y + w, x:x + w]).sum()
            score = m.sum() + 2 * min(hit, miss)
            if score > best:
                best, pos = score, (y, x)
    return pos


def zoom_tile(crop: np.ndarray, mask: np.ndarray, cells_on: np.ndarray, y: int, x: int, cells: int,
              scale: int, aligned: bool) -> Image.Image:
    w = cells * STRIDE
    base = crop[y:y + w, x:x + w].astype(float)
    base = 255 - 0.35 * (255 - base)                      # washed-out context
    m = mask[y:y + w, x:x + w]
    on = cells_on[y:y + w, x:x + w]
    rgb = base.copy()
    rgb[on] = 0.75 * rgb[on] + 0.25 * np.array([222, 235, 247])   # cells the model is asked to fill
    rgb[m & on] = RIGHT
    rgb[m & ~on] = RIGHT if aligned else WRONG
    img = Image.fromarray(np.uint8(rgb)).resize((w * scale, w * scale), Image.NEAREST)
    draw = ImageDraw.Draw(img)
    for k in range(cells + 1):
        p = min(k * STRIDE * scale, w * scale - 1)
        draw.line([(p, 0), (p, w * scale)], fill=(190, 198, 210), width=1)
        draw.line([(0, p), (w * scale, p)], fill=(190, 198, 210), width=1)
    for cy in range(cells):
        for cx in range(cells):
            if on[cy * STRIDE, cx * STRIDE]:
                x0, y0 = cx * STRIDE * scale, cy * STRIDE * scale
                draw.rectangle([x0, y0, x0 + STRIDE * scale - 1, y0 + STRIDE * scale - 1], outline=CELL, width=2)
    return img


def hole_window(images: list, min_side: int = 96, pad: float = 0.35) -> tuple[int, int, int, int]:
    """Square window around the pixels where the outputs differ, i.e. the generated hole.

    The composites keep the original crop outside the hole, so any pixel that differs between the prefill arms is
    inside it. The window is padded so some context remains, and kept inside the image.
    """
    stack = np.stack([img.astype(int) for img in images])
    hole = (np.abs(stack - stack[0]).max(axis=(0, 3)) > 0)
    if not hole.any():
        return 0, 0, images[0].shape[0], images[0].shape[1]
    ys, xs = np.nonzero(hole)
    cy, cx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
    side = int(max(min_side, (1 + 2 * pad) * max(np.ptp(ys) + 1, np.ptp(xs) + 1)))
    side = min(side, *images[0].shape[:2])
    y0 = int(np.clip(round(cy - side / 2), 0, images[0].shape[0] - side))
    x0 = int(np.clip(round(cx - side / 2), 0, images[0].shape[1] - side))
    return y0, x0, y0 + side, x0 + side


def crop_with_mask(crop: np.ndarray, mask: np.ndarray, y: int, x: int, w: int) -> Image.Image:
    rgb = crop.astype(float).copy()
    rgb[mask] = 0 if crop.mean() > 128 else 255          # the hole in black on light paintings, white on dark ones
    img = Image.fromarray(np.uint8(rgb))
    ImageDraw.Draw(img).rectangle([x - 1, y - 1, x + w, y + w], outline=(68, 114, 196), width=4)
    return img


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True, help="Figure 1 folder")
    ap.add_argument("--out-fig2", type=Path, help="Figure 2 folder (default: ../fig2 next to --out)")
    ap.add_argument("--archive", type=Path, help="Project data disk with the frozen experimental archives")
    ap.add_argument("--slot", type=int, default=0)
    ap.add_argument("--crop", type=Path)
    ap.add_argument("--sdxl-black", type=Path)
    ap.add_argument("--sdxl-gray", type=Path)
    ap.add_argument("--sdxl-ring", type=Path)
    ap.add_argument("--composite", type=Path, help="a LaMa composite of the crack-5%% case for Figure 2")
    ap.add_argument("--cells", type=int, default=6)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    provenance = archive_inputs(args.archive, args) if args.archive else {}

    seed = mask_seed(args.slot, "crack", 0.01)
    mask = design_mask("crack", 0.01, seed)
    nearest, aligned = nearest_cover(mask), grid_cover(mask, STRIDE)
    crop = np.asarray(Image.open(args.crop).convert("RGB")) if args.crop else np.asarray(placeholder(512, 1))
    y, x = best_window(mask, nearest, args.cells)
    w = args.cells * STRIDE

    crop_with_mask(crop, mask, y, x, w).resize((256, 256), Image.LANCZOS).save(args.out / "a_crop.png")
    zoom_tile(crop, mask, nearest, y, x, args.cells, 8, False).save(args.out / "a_zoom_default.png")
    zoom_tile(crop, mask, aligned, y, x, args.cells, 8, True).save(args.out / "a_zoom_aligned.png")

    outs = {}
    for name, path, seed_ in (("b_out_black", args.sdxl_black, 2), ("b_out_gray", args.sdxl_gray, 3),
                              ("b_out_ring", args.sdxl_ring, 4)):
        outs[name] = np.asarray(Image.open(path).convert("RGB") if path else placeholder(512, seed_))
    box = hole_window(list(outs.values())) if all((args.sdxl_black, args.sdxl_gray, args.sdxl_ring)) else None
    for name, arr in outs.items():
        tile = Image.fromarray(arr if box is None else arr[box[0]:box[2], box[1]:box[3]])
        tile.resize((256, 256), Image.LANCZOS).save(args.out / f"{name}.png")

    # Figure 2: the same crop, the six masks of this slot, the shared aligned input and a composited output
    fig2 = args.out_fig2 or args.out.parent / "fig2"
    fig2.mkdir(exist_ok=True)
    Image.fromarray(crop).resize((256, 256), Image.LANCZOS).save(fig2 / "f2_crop.png")
    for fam in MASK_FAMILIES:
        for area in MASK_AREAS:
            m = design_mask(fam, area, mask_seed(args.slot, fam, area))
            tile = np.full((512, 512, 3), 247, np.uint8)
            tile[m] = (64, 64, 72)
            Image.fromarray(tile).resize((128, 128), Image.LANCZOS).save(fig2 / f"f2_mask_{fam}_{int(area * 100)}.png")
    m5 = design_mask("crack", 0.05, mask_seed(args.slot, "crack", 0.05))
    shared = grid_cover(m5, STRIDE)
    inp = crop.copy()
    inp[shared] = 0
    Image.fromarray(inp).resize((256, 256), Image.LANCZOS).save(fig2 / "f2_input.png")
    if args.composite:
        out = np.asarray(Image.open(args.composite).convert("RGB")).astype(float).copy()
    else:
        out = crop.astype(float).copy()
        out[m5] = out[m5].mean(axis=0)
    edge = m5 & ~np.roll(m5, 1, 0) | m5 & ~np.roll(m5, 1, 1) | m5 & ~np.roll(m5, -1, 0) | m5 & ~np.roll(m5, -1, 1)
    out[edge] = (68, 114, 196)
    Image.fromarray(np.uint8(out)).resize((256, 256), Image.LANCZOS).save(fig2 / "f2_output.png")

    missed = float((mask & ~nearest).sum() / mask.sum())
    info = {**provenance, "slot": args.slot, "mask_seed": seed, "mask_pixels": int(mask.sum()), "missed_fraction_this_mask": missed,
            "zoom_window_yx": [int(y), int(x)], "zoom_cells": args.cells,
            "prefill_zoom_bbox_yxyx_exclusive": list(box) if box is not None else None,
            "placeholders": [k for k, v in {"crop": args.crop, "sdxl_black": args.sdxl_black,
                                            "sdxl_gray": args.sdxl_gray, "sdxl_ring": args.sdxl_ring,
                                            "composite": args.composite}.items() if not v]}
    (args.out / "assets.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
