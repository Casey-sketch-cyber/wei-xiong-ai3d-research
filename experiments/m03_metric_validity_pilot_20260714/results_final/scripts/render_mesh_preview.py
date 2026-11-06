from __future__ import annotations

import argparse
from pathlib import Path

import bpy
from mathutils import Vector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--size", type=int, default=512)
    return parser.parse_args()


def look_at(obj, target: Vector) -> None:
    obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()


def main() -> None:
    args = parse_args()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    suffix = args.input.suffix.lower()
    if suffix == ".obj":
        bpy.ops.wm.obj_import(filepath=str(args.input))
    elif suffix == ".ply":
        bpy.ops.wm.ply_import(filepath=str(args.input))
    else:
        raise ValueError(f"Unsupported mesh format: {suffix}")

    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    center = (low + high) * 0.5
    span = max(high.x - low.x, high.y - low.y, high.z - low.z)
    for obj in meshes:
        obj.location -= center
        obj.scale *= 1.0 / span

    material = bpy.data.materials.new("Clay")
    material.diffuse_color = (0.68, 0.72, 0.78, 1.0)
    material.roughness = 0.7
    for obj in meshes:
        obj.data.materials.clear()
        obj.data.materials.append(material)

    camera_data = bpy.data.cameras.new("Camera")
    camera = bpy.data.objects.new("Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = (1.7, -1.9, 1.35)
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.45
    look_at(camera, Vector((0.0, 0.0, 0.0)))
    bpy.context.scene.camera = camera

    for name, location, energy, size in (
        ("Key", (2.5, -3.0, 4.0), 650.0, 3.0),
        ("Fill", (-3.0, -1.0, 2.0), 280.0, 3.5),
        ("Rim", (1.0, 3.0, 3.0), 380.0, 2.5),
    ):
        light_data = bpy.data.lights.new(name, type="AREA")
        light_data.energy = energy
        light_data.shape = "DISK"
        light_data.size = size
        light = bpy.data.objects.new(name, light_data)
        bpy.context.collection.objects.link(light)
        light.location = location
        look_at(light, Vector((0.0, 0.0, 0.0)))

    scene = bpy.context.scene
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = args.size
    scene.render.resolution_y = args.size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    if scene.world is None:
        scene.world = bpy.data.worlds.new("World")
    scene.world.color = (0.96, 0.96, 0.96)
    scene.view_settings.look = "AgX - Medium High Contrast"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(args.output)
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
