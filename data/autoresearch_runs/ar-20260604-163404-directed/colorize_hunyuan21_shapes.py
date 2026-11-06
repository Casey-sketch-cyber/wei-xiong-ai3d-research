#!/usr/bin/env python
"""Colorize Hunyuan3D shape-only meshes by projecting input image colors.

This is a lightweight post-process for visual assessment. It does not claim to
be Hunyuan3D's official PBR texture/paint stage.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path


def add_local_deps() -> None:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / ".codex_tmp" / "hunyuan_colorize_deps"
        if candidate.exists():
            sys.path.insert(0, str(candidate))
            return


add_local_deps()

import numpy as np
from PIL import Image, ImageDraw
import trimesh


ROOT = Path(__file__).resolve().parent
RERUN = ROOT / "m02_hunyuan21_rerun"
REMOTE_OUT = RERUN / "remote_hunyuan21_shape_smoke_results" / "outputs" / "hunyuan21_shape_smoke"
MANIFEST = RERUN / "hunyuan21_smoke_manifest.csv"
OUT = RERUN / "colorized_projection_results"
PREV = OUT / "previews"


def load_mesh(path: Path) -> trimesh.Trimesh:
    obj = trimesh.load(path, force="scene")
    if isinstance(obj, trimesh.Scene):
        dumped = obj.dump(concatenate=True)
        if isinstance(dumped, trimesh.Trimesh):
            mesh = dumped
        else:
            geoms = [g for g in obj.geometry.values() if hasattr(g, "vertices") and len(g.vertices)]
            if not geoms:
                raise ValueError(f"empty scene: {path}")
            mesh = trimesh.util.concatenate(geoms)
    else:
        mesh = obj
    mesh.remove_unreferenced_vertices()
    return mesh


def normalize_vertices(vertices: np.ndarray) -> np.ndarray:
    v = np.asarray(vertices, dtype=np.float64)
    v = v - v.mean(axis=0, keepdims=True)
    scale = np.max(np.linalg.norm(v, axis=1)) or 1.0
    return v / scale


def load_color_image(item_dir: Path, fallback: Path) -> np.ndarray:
    rgba_path = item_dir / "input_rgba.png"
    img_path = rgba_path if rgba_path.exists() else fallback
    image = Image.open(img_path).convert("RGBA")
    # Keep the original colors where alpha is low, avoiding white holes after rembg.
    if rgba_path.exists():
        original = Image.open(fallback).convert("RGBA").resize(image.size)
        src = np.asarray(image).copy()
        orig = np.asarray(original)
        alpha = src[:, :, 3]
        src[alpha < 16, :3] = orig[alpha < 16, :3]
        src[:, :, 3] = 255
        return src
    return np.asarray(image)


def sample_projected_vertex_colors(mesh: trimesh.Trimesh, image: np.ndarray) -> np.ndarray:
    v = normalize_vertices(mesh.vertices)
    xy = v[:, :2]
    lo = np.percentile(xy, 2, axis=0)
    hi = np.percentile(xy, 98, axis=0)
    span = np.maximum(hi - lo, 1e-6)
    uv = (xy - lo) / span
    uv = np.clip(uv, 0.0, 1.0)

    h, w = image.shape[:2]
    px = np.clip(np.round(uv[:, 0] * (w - 1)).astype(np.int64), 0, w - 1)
    py = np.clip(np.round((1.0 - uv[:, 1]) * (h - 1)).astype(np.int64), 0, h - 1)
    colors = image[py, px, :4].astype(np.uint8)
    colors[:, 3] = 255
    return colors


def rotation_matrix(rx: float = 0, ry: float = 0, rz: float = 0) -> np.ndarray:
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    rxm = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    rym = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rzm = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rzm @ rym @ rxm


def render_mesh(mesh: trimesh.Trimesh, rotation: np.ndarray, size: int = 320) -> Image.Image:
    v = normalize_vertices(mesh.vertices)
    f = np.asarray(mesh.faces, dtype=np.int64)
    vr = v @ rotation.T
    pts = vr[:, :2] * (size * 0.40) + size / 2
    depths = vr[:, 2]
    face_depth = depths[f].mean(axis=1)
    order = np.argsort(face_depth)

    vertex_colors = np.asarray(mesh.visual.vertex_colors[:, :3], dtype=np.float64)
    face_colors = vertex_colors[f].mean(axis=1)
    normals = np.asarray(mesh.face_normals) @ rotation.T
    light = np.array([0.25, -0.35, 0.9])
    light = light / np.linalg.norm(light)

    img = Image.new("RGB", (size, size), (248, 248, 248))
    draw = ImageDraw.Draw(img)
    for idx in order:
        poly = [tuple(pts[j]) for j in f[idx]]
        shade = max(0.22, float(np.dot(normals[idx], light)) * 0.58 + 0.42)
        color = np.clip(face_colors[idx] * shade, 0, 255).astype(np.uint8)
        draw.polygon(poly, fill=tuple(int(c) for c in color))
    draw.rectangle((0, 0, size - 1, size - 1), outline=(210, 210, 210))
    return img


def thumb(path: Path, size: tuple[int, int] = (220, 220)) -> Image.Image:
    im = Image.open(path).convert("RGB")
    im.thumbnail(size)
    canvas = Image.new("RGB", size, "white")
    canvas.paste(im, ((size[0] - im.width) // 2, (size[1] - im.height) // 2))
    return canvas


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    PREV.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(MANIFEST.open("r", encoding="utf-8-sig", newline="")))
    panels = []
    summary = []
    for row in rows:
        safe_id = row["safe_id"]
        src_item = REMOTE_OUT / safe_id
        out_item = OUT / safe_id
        out_item.mkdir(parents=True, exist_ok=True)
        mesh = load_mesh(src_item / "shape.glb")
        input_png = RERUN / row["input_png"]
        color_image = load_color_image(src_item, input_png)
        colors = sample_projected_vertex_colors(mesh, color_image)
        mesh.visual.vertex_colors = colors
        out_glb = out_item / "colorized_shape.glb"
        mesh.export(out_glb)

        views = [
            ("front", rotation_matrix()),
            ("side", rotation_matrix(0, math.radians(80), 0)),
            ("iso", rotation_matrix(math.radians(25), math.radians(-35), 0)),
        ]
        render_imgs = []
        for name, rot in views:
            image = render_mesh(mesh, rot)
            image.save(out_item / f"color_preview_{name}.png")
            render_imgs.append(image)

        original = thumb(input_png)
        gray_panel = thumb(src_item / "comparison_panel.png", (320, 220))
        panel = Image.new("RGB", (220 + 320 + 320 * 3, 300), (255, 255, 255))
        x = 0
        for im in [original, gray_panel] + render_imgs:
            panel.paste(im, (x, 25))
            x += im.width
        d = ImageDraw.Draw(panel)
        d.text((8, 4), safe_id, fill=(0, 0, 0))
        d.text((8, 250), "original", fill=(0, 0, 0))
        d.text((225, 250), "old gray preview", fill=(0, 0, 0))
        d.text((545, 250), "color front", fill=(0, 0, 0))
        d.text((865, 250), "color side", fill=(0, 0, 0))
        d.text((1185, 250), "color iso", fill=(0, 0, 0))
        panel.save(out_item / "colorized_comparison_panel.png")
        panels.append(panel)
        summary.append(
            {
                "safe_id": safe_id,
                "source_glb": str((src_item / "shape.glb").relative_to(ROOT)),
                "colorized_glb": str(out_glb.relative_to(ROOT)),
                "color_source": str(input_png.relative_to(ROOT)),
                "vertices": int(len(mesh.vertices)),
                "faces": int(len(mesh.faces)),
                "method": "front_view_vertex_color_projection_from_input_image",
            }
        )

    sheet_w = panels[0].width
    sheet_h = panels[0].height * len(panels)
    sheet = Image.new("RGB", (sheet_w, sheet_h), (245, 245, 245))
    for idx, panel in enumerate(panels):
        sheet.paste(panel, (0, idx * panel.height))
    sheet_path = PREV / "hunyuan21_colorized_projection_contact_sheet.png"
    sheet.save(sheet_path)
    summary_obj = {
        "experiment": "m02_hunyuan21_colorized_projection",
        "n": len(summary),
        "success": len(summary),
        "texture_status": "not_official_pbr_front_view_vertex_color_projection",
        "contact_sheet": str(sheet_path.relative_to(ROOT)),
        "items": summary,
    }
    (OUT / "colorized_projection_summary.json").write_text(
        json.dumps(summary_obj, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"success": len(summary), "contact_sheet": str(sheet_path)}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
