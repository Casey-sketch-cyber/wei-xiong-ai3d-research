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
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from patch_design import MASK_AREAS, MASK_FAMILIES, design_mask
from latent_aligned import grid_cover

NATIVE_SEED = 20261119  # run_followup.NATIVE_SEED
STRIDE = 8
RIGHT = (112, 173, 71)    # covered pixels  #70AD47
WRONG = (192, 0, 0)       # missed pixels   #C00000
CELL = (68, 114, 196)     # latent cell edges #4472C4


def mask_seed(slot: int, family: str, area: float) -> int:
    return NATIVE_SEED + slot * 100 + MASK_FAMILIES.index(family) * 10 + MASK_AREAS.index(area)


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


def crop_with_mask(crop: np.ndarray, mask: np.ndarray, y: int, x: int, w: int) -> Image.Image:
    rgb = crop.astype(float).copy()
    rgb[mask] = 255
    img = Image.fromarray(np.uint8(rgb))
    ImageDraw.Draw(img).rectangle([x - 1, y - 1, x + w, y + w], outline=(68, 114, 196), width=4)
    return img


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, required=True, help="Figure 1 folder")
    ap.add_argument("--out-fig2", type=Path, help="Figure 2 folder (default: ../fig2 next to --out)")
    ap.add_argument("--slot", type=int, default=0)
    ap.add_argument("--crop", type=Path)
    ap.add_argument("--sdxl-black", type=Path)
    ap.add_argument("--sdxl-gray", type=Path)
    ap.add_argument("--sdxl-ring", type=Path)
    ap.add_argument("--composite", type=Path, help="a LaMa composite of the crack-5%% case for Figure 2")
    ap.add_argument("--cells", type=int, default=6)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    seed = mask_seed(args.slot, "crack", 0.01)
    mask = design_mask("crack", 0.01, seed)
    nearest, aligned = nearest_cover(mask), grid_cover(mask, STRIDE)
    crop = np.asarray(Image.open(args.crop).convert("RGB")) if args.crop else np.asarray(placeholder(512, 1))
    y, x = best_window(mask, nearest, args.cells)
    w = args.cells * STRIDE

    crop_with_mask(crop, mask, y, x, w).resize((256, 256), Image.LANCZOS).save(args.out / "a_crop.png")
    zoom_tile(crop, mask, nearest, y, x, args.cells, 8, False).save(args.out / "a_zoom_default.png")
    zoom_tile(crop, mask, aligned, y, x, args.cells, 8, True).save(args.out / "a_zoom_aligned.png")

    for name, path, seed_ in (("b_out_black", args.sdxl_black, 2), ("b_out_gray", args.sdxl_gray, 3),
                              ("b_out_ring", args.sdxl_ring, 4)):
        img = Image.open(path).convert("RGB") if path else placeholder(256, seed_)
        img.resize((256, 256), Image.LANCZOS).save(args.out / f"{name}.png")

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
    info = {"slot": args.slot, "mask_seed": seed, "mask_pixels": int(mask.sum()), "missed_fraction_this_mask": missed,
            "zoom_window_yx": [int(y), int(x)], "zoom_cells": args.cells,
            "placeholders": [k for k, v in {"crop": args.crop, "sdxl_black": args.sdxl_black,
                                            "sdxl_gray": args.sdxl_gray, "sdxl_ring": args.sdxl_ring,
                                            "composite": args.composite}.items() if not v]}
    (args.out / "assets.json").write_text(json.dumps(info, indent=1))
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
