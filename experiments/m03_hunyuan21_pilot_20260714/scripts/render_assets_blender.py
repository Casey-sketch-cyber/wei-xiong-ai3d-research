#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import bpy
from mathutils import Vector
from PIL import Image, ImageDraw, ImageFont


STYLES = ("photo", "edge", "flat", "low_detail", "sketch", "watercolor")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--mode", choices=("shape", "pbr"), required=True)
    parser.add_argument("--seed", type=int, default=20260714)
    parser.add_argument("--size", type=int, default=512)
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


def load_manifest(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def imported_bounds() -> tuple[Vector, Vector]:
    points = []
    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue
        points.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    if not points:
        raise ValueError("Imported asset has no mesh objects")
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return low, high


def add_area_light(name: str, location: Vector, energy: float, size: float, target: Vector) -> None:
    data = bpy.data.lights.new(name=name, type="AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (target - location).to_track_quat("-Z", "Y").to_euler()


def set_neutral_material() -> None:
    material = bpy.data.materials.new("NeutralShapeMaterial")
    material.diffuse_color = (0.24, 0.32, 0.43, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.24, 0.32, 0.43, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.72
    bsdf.inputs["Metallic"].default_value = 0.05
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.data.materials.clear()
            obj.data.materials.append(material)


def render_asset(asset_path: Path, output_path: Path, size: int, neutral: bool) -> None:
    reset_scene()
    bpy.ops.import_scene.gltf(filepath=str(asset_path))
    if neutral:
        set_neutral_material()

    low, high = imported_bounds()
    center = (low + high) * 0.5
    span = max(high.x - low.x, high.y - low.y, high.z - low.z)
    if span <= 1e-6:
        span = 1.0

    camera_data = bpy.data.cameras.new("Camera")
    camera = bpy.data.objects.new("Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = center + Vector((1.75, -2.35, 1.45)) * span
    camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 58
    camera.data.clip_start = max(span * 0.001, 0.001)
    camera.data.clip_end = span * 20
    bpy.context.scene.camera = camera

    add_area_light("Key", center + Vector((2.5, -3.0, 4.0)) * span, 320.0, span * 2.0, center)
    add_area_light("Fill", center + Vector((-3.0, -1.5, 2.0)) * span, 150.0, span * 2.5, center)
    add_area_light("Rim", center + Vector((1.0, 3.0, 2.5)) * span, 220.0, span * 1.8, center)

    scene = bpy.context.scene
    if neutral:
        scene.render.engine = "BLENDER_WORKBENCH"
        scene.display.shading.light = "STUDIO"
        scene.display.shading.color_type = "MATERIAL"
        scene.display.shading.show_shadows = True
        scene.display.shading.show_cavity = True
        scene.display.shading.cavity_type = "WORLD"
        scene.display.shading.background_type = "VIEWPORT"
        scene.display.shading.background_color = (0.96, 0.96, 0.96)
    else:
        try:
            scene.render.engine = "BLENDER_EEVEE_NEXT"
        except TypeError:
            scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = size
    scene.render.resolution_y = size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    if scene.world is None:
        scene.world = bpy.data.worlds.new("NeutralWorld")
    scene.world.color = (0.94, 0.94, 0.94)
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    output_path.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(output_path)
    bpy.ops.render.render(write_still=True)


def fit_thumb(path: Path, size: tuple[int, int]) -> Image.Image:
    image = Image.open(path).convert("RGB")
    image.thumbnail(size, Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", size, "white")
    canvas.paste(image, ((size[0] - image.width) // 2, (size[1] - image.height) // 2))
    return canvas


def compose_object_panel(
    obj: dict[str, str], dataset: Path, preview_root: Path, panel_root: Path
) -> Path:
    cell_w, input_h, render_h, label_h = 260, 180, 260, 30
    header_h = 42
    panel = Image.new("RGB", (cell_w * len(STYLES), header_h + input_h + render_h + label_h), "white")
    draw = ImageDraw.Draw(panel)
    draw.text((8, 10), f"{obj['name']} | {obj['stratum']} | {obj['uid']}", fill=(20, 20, 20))
    for column, style in enumerate(STYLES):
        x = column * cell_w
        input_path = dataset / obj["uid"] / "variants" / f"{style}.png"
        preview_path = preview_root / obj["uid"] / f"{style}.png"
        panel.paste(fit_thumb(input_path, (cell_w, input_h)), (x, header_h))
        panel.paste(fit_thumb(preview_path, (cell_w, render_h)), (x, header_h + input_h))
        draw.rectangle((x, header_h, x + cell_w - 1, header_h + input_h + render_h - 1), outline=(205, 205, 205))
        draw.text((x + 8, header_h + input_h + render_h + 7), style, fill=(20, 20, 20))
    panel_root.mkdir(parents=True, exist_ok=True)
    output = panel_root / f"{obj['uid']}.png"
    panel.save(output)
    return output


def main() -> int:
    args = parse_args()
    objects = load_manifest(args.manifest)
    if args.mode == "pbr":
        objects = [obj for obj in objects if obj["pbr_selected"].lower() == "true"]
    if args.limit > 0:
        objects = objects[: args.limit]
    preview_root = args.work / "previews" / args.mode
    panel_root = args.work / "previews" / f"{args.mode}_panels"

    rendered = 0
    for obj in objects:
        for style in STYLES:
            if args.mode == "shape":
                asset = (
                    args.work
                    / "outputs"
                    / "shape"
                    / obj["uid"]
                    / style
                    / f"seed_{args.seed}"
                    / "shape.glb"
                )
            else:
                asset = args.work / "outputs" / "pbr" / obj["uid"] / style / "textured.glb"
            output = preview_root / obj["uid"] / f"{style}.png"
            if not output.exists():
                render_asset(asset, output, args.size, neutral=args.mode == "shape")
            rendered += 1
            print("RENDERED", rendered, len(objects) * len(STYLES), obj["uid"], style, flush=True)

    panels = [compose_object_panel(obj, args.dataset, preview_root, panel_root) for obj in objects]
    panel_images = [Image.open(path).convert("RGB") for path in panels]
    sheet = Image.new(
        "RGB",
        (max(image.width for image in panel_images), sum(image.height for image in panel_images)),
        (245, 245, 245),
    )
    y = 0
    for image in panel_images:
        sheet.paste(image, (0, y))
        y += image.height
    contact_sheet = args.work / "previews" / f"{args.mode}_contact_sheet.png"
    contact_sheet.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(contact_sheet)
    print("CONTACT_SHEET", contact_sheet, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
