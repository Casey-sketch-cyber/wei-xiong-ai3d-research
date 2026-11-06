from __future__ import annotations

import json
from pathlib import Path

import nvdiffrast.torch as dr
import numpy as np
import pandas as pd
from PIL import Image

import make_representative_cases as cases
import render_diagnostics as render


ROOT = Path("/root/autodl-tmp/m03_q2_confirmatory_20260715")
OUTPUT = ROOT / "fig1_framework_assets"
OBJECT_ID = "c120_017"
MODELS = ("triposr", "instantmesh", "hunyuan21", "trellis")


def save_mesh_render(context, mesh, path: Path) -> None:
    image = cases.mesh_image(context, mesh, resolution=512, grid_extent=1.5)
    Image.fromarray(image).save(path)


def main() -> int:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    variants = ROOT / "inputs" / "main" / OBJECT_ID / "variants"
    for source in sorted(variants.glob("*.png")):
        Image.open(source).convert("RGBA").save(OUTPUT / f"input_{source.name}")

    context = dr.RasterizeCudaContext()
    evaluations = cases.evaluation_rows(ROOT / "evaluation")
    object_rows = evaluations[
        (evaluations["object_id"] == OBJECT_ID)
        & (evaluations["split"] == "main")
    ].copy()
    gt_path = Path(object_rows.iloc[0]["gt_view_path"])
    gt_mesh = render.centered(render.load_mesh(gt_path))
    save_mesh_render(context, gt_mesh, OUTPUT / "gt_reference.png")

    manifest = []
    for model in MODELS:
        seed = -1 if model == "triposr" else 20260715
        calibration = json.loads(
            (ROOT / "evaluation" / model / "calibration.json").read_text(encoding="utf-8")
        )
        for style in ("photo", "sketch"):
            row = object_rows[
                (object_rows["model"] == model)
                & (object_rows["seed"] == seed)
                & (object_rows["style"] == style)
            ].iloc[0]
            mesh = render.transform_mesh(
                render.load_mesh(Path(row["mesh_path"])),
                float(calibration["scale"]),
                np.asarray(calibration["matrix"], dtype=np.float64),
            )
            output_name = f"{model}_{style}.png"
            save_mesh_render(context, mesh, OUTPUT / output_name)
            manifest.append(
                {
                    "model": model,
                    "style": style,
                    "seed": int(seed),
                    "mesh_sha256": row["mesh_sha256"],
                    "output": output_name,
                }
            )

    pd.DataFrame(manifest).to_csv(OUTPUT / "asset_manifest.csv", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
