from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import bpy
import cv2
import numpy as np
import trimesh
from mathutils import Matrix, Vector
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


STYLES = ("photo", "edge", "flat", "low_detail", "sketch", "watercolor")
VIEW_ROTATION = np.array(
    [
        [0.8192, 0.0, 0.5736],
        [0.2962, 0.8563, -0.4234],
        [-0.4912, 0.5165, 0.7010],
    ],
    dtype=np.float64,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", type=int, default=512)
    parser.add_argument("--seed", type=int, default=20260714)
    return parser.parse_args()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def imported_bounds() -> tuple[Vector, Vector]:
    points = []
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not points:
        raise ValueError("Imported asset contains no mesh objects")
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return low, high


def add_area_light(name: str, location: tuple[float, float, float], energy: float, size: float) -> None:
    data = bpy.data.lights.new(name=name, type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (-Vector(location)).to_track_quat("-Z", "Y").to_euler()


def transform_scene_to_view() -> float:
    low, high = imported_bounds()
    center = (low + high) * 0.5
    span = max(high.x - low.x, high.y - low.y, high.z - low.z)
    if span <= 1e-9:
        raise ValueError("Degenerate imported asset")
    rotation = Matrix(
        (
            (float(VIEW_ROTATION[0, 0]), float(VIEW_ROTATION[0, 1]), float(VIEW_ROTATION[0, 2]), 0.0),
            (float(VIEW_ROTATION[1, 0]), float(VIEW_ROTATION[1, 1]), float(VIEW_ROTATION[1, 2]), 0.0),
            (float(VIEW_ROTATION[2, 0]), float(VIEW_ROTATION[2, 1]), float(VIEW_ROTATION[2, 2]), 0.0),
            (0.0, 0.0, 0.0, 1.0),
        )
    )
    normalize = Matrix.Scale(1.0 / float(span), 4) @ Matrix.Translation(-center)
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.matrix_world = rotation @ normalize @ obj.matrix_world
    view_low, view_high = imported_bounds()
    return max(float(view_high.x - view_low.x), float(view_high.y - view_low.y))


def configure_scene(output_path: Path, size: int, view_span: float) -> None:
    camera_data = bpy.data.cameras.new("Camera")
    camera = bpy.data.objects.new("Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (0.0, 0.0, 2.05)
    camera.rotation_euler = (0.0, 0.0, 0.0)
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = view_span / 0.82
    camera.data.clip_start = 0.01
    camera.data.clip_end = 20.0
    bpy.context.scene.camera = camera

    add_area_light("Key", (2.8, -3.2, 4.5), 420.0, 3.0)
    add_area_light("Fill", (-3.0, -1.0, 2.2), 180.0, 3.5)
    add_area_light("Rim", (1.0, 3.2, 2.5), 240.0, 2.8)

    scene = bpy.context.scene
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = True
    scene.render.filepath = str(output_path)
    if scene.world is None:
        scene.world = bpy.data.worlds.new("WhiteWorld")
    scene.world.color = (1.0, 1.0, 1.0)
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass


def render_photo(mesh_path: Path, output_path: Path, size: int) -> None:
    reset_scene()
    bpy.ops.import_scene.gltf(filepath=str(mesh_path))
    view_span = transform_scene_to_view()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    configure_scene(output_path, size, view_span)
    bpy.ops.render.render(write_still=True)


def rgba_on_white(image: Image.Image) -> tuple[Image.Image, Image.Image]:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    white = Image.new("RGB", rgba.size, "white")
    white.paste(rgba.convert("RGB"), mask=alpha)
    return white, alpha


def attach_alpha(rgb: Image.Image, alpha: Image.Image) -> Image.Image:
    result = rgb.convert("RGBA")
    result.putalpha(alpha)
    pixels = np.asarray(result).copy()
    pixels[np.asarray(alpha) == 0, :3] = 255
    return Image.fromarray(pixels, mode="RGBA")


def edge_style(rgb: Image.Image, alpha: Image.Image) -> Image.Image:
    gray = np.asarray(ImageOps.grayscale(rgb))
    edges = cv2.Canny(gray, 70, 160)
    edges = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1)
    drawing = np.full((*edges.shape, 3), 255, dtype=np.uint8)
    drawing[edges > 0] = 20
    return attach_alpha(Image.fromarray(drawing), alpha)


def flat_style(rgb: Image.Image, alpha: Image.Image, seed: int) -> Image.Image:
    arr = np.asarray(rgb).copy()
    mask = np.asarray(alpha) > 0
    pixels = arr[mask].astype(np.float32)
    if len(pixels) >= 8:
        cv2.setRNGSeed(seed)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
        _, labels, centers = cv2.kmeans(pixels, 8, None, criteria, 3, cv2.KMEANS_PP_CENTERS)
        arr[mask] = np.uint8(centers)[labels.ravel()]
    result = cv2.edgePreservingFilter(cv2.cvtColor(arr, cv2.COLOR_RGB2BGR), flags=1, sigma_s=45, sigma_r=0.35)
    return attach_alpha(Image.fromarray(cv2.cvtColor(result, cv2.COLOR_BGR2RGB)), alpha)


def low_detail_style(rgb: Image.Image, alpha: Image.Image) -> Image.Image:
    small = rgb.resize((64, 64), Image.Resampling.BILINEAR)
    result = small.resize(rgb.size, Image.Resampling.BILINEAR).filter(ImageFilter.SMOOTH_MORE)
    return attach_alpha(ImageEnhance.Contrast(result).enhance(1.1), alpha)


def sketch_style(rgb: Image.Image, alpha: Image.Image) -> Image.Image:
    gray = ImageOps.grayscale(rgb)
    inverted = ImageOps.invert(gray)
    blurred = inverted.filter(ImageFilter.GaussianBlur(radius=9))
    g = np.asarray(gray, dtype=np.float32)
    b = np.asarray(blurred, dtype=np.float32)
    dodge = np.minimum(255.0, g * 255.0 / (255.0 - b + 1.0)).astype(np.uint8)
    return attach_alpha(Image.fromarray(dodge).convert("RGB"), alpha)


def watercolor_style(rgb: Image.Image, alpha: Image.Image) -> Image.Image:
    bgr = cv2.cvtColor(np.asarray(rgb), cv2.COLOR_RGB2BGR)
    try:
        styled = cv2.stylization(bgr, sigma_s=70, sigma_r=0.45)
    except Exception:
        styled = cv2.edgePreservingFilter(bgr, flags=1, sigma_s=70, sigma_r=0.45)
    result = Image.fromarray(cv2.cvtColor(styled, cv2.COLOR_BGR2RGB)).filter(ImageFilter.SMOOTH_MORE)
    return attach_alpha(ImageEnhance.Color(result).enhance(1.12), alpha)


def make_styles(photo_path: Path, output_dir: Path, seed: int) -> dict[str, Path]:
    photo = Image.open(photo_path).convert("RGBA")
    rgb, alpha = rgba_on_white(photo)
    variants = {
        "photo": attach_alpha(rgb, alpha),
        "edge": edge_style(rgb, alpha),
        "flat": flat_style(rgb, alpha, seed),
        "low_detail": low_detail_style(rgb, alpha),
        "sketch": sketch_style(rgb, alpha),
        "watercolor": watercolor_style(rgb, alpha),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for style, image in variants.items():
        path = output_dir / f"{style}.png"
        image.save(path)
        paths[style] = path
    return paths


def make_view_gt(source_path: Path, output_path: Path) -> None:
    mesh = trimesh.load_mesh(source_path, process=False)
    mesh.vertices = np.asarray(mesh.vertices, dtype=np.float64) @ VIEW_ROTATION.T
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mesh.export(output_path)


def main() -> int:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    records = []
    for index, row in enumerate(load_rows(args.manifest), start=1):
        object_id = row["object_id"]
        object_dir = args.output / "inputs" / object_id
        raw_photo = object_dir / "photo_render.png"
        render_photo(Path(row["input_mesh_path"]), raw_photo, args.size)
        paths = make_styles(raw_photo, object_dir / "variants", args.seed + index)
        gt_view = args.output / "gt_view" / object_id / "solid_gt_view.ply"
        make_view_gt(Path(row["gt_path"]), gt_view)
        alpha = np.asarray(Image.open(paths["photo"]).getchannel("A"))
        ys, xs = np.nonzero(alpha > 0)
        if len(xs) == 0:
            raise ValueError(f"Empty alpha mask for {object_id}")
        bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
        for style, path in paths.items():
            records.append(
                {
                    "object_id": object_id,
                    "object_name": row["object_name"],
                    "style": style,
                    "input_path": str(path),
                    "input_sha256": file_sha256(path),
                    "gt_view_path": str(gt_view),
                    "gt_view_sha256": file_sha256(gt_view),
                    "alpha_bbox": json.dumps(bbox),
                    "foreground_fraction": float(np.mean(alpha > 0)),
                }
            )
        print("INPUT", index, 30, object_id, row["object_name"], bbox, flush=True)

    fields = list(records[0].keys())
    with (args.output / "inputs_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    summary = {
        "objects": len({row["object_id"] for row in records}),
        "styles": list(STYLES),
        "images": len(records),
        "size": args.size,
        "seed": args.seed,
        "view_rotation": VIEW_ROTATION.tolist(),
        "camera": {
            "type": "orthographic",
            "location": [0.0, 0.0, 2.05],
            "foreground_fit_fraction": 0.82,
        },
        "background": "transparent alpha with white RGB outside foreground",
        "all_hashes_recorded": True,
    }
    (args.output / "inputs_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("SUMMARY", json.dumps(summary, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
