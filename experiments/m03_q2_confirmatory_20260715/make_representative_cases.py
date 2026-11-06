from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import nvdiffrast.torch as dr
import numpy as np
import pandas as pd
from PIL import Image
import torch

import render_diagnostics as render


MODELS = ("triposr", "instantmesh", "hunyuan21", "trellis")
MODEL_LABELS = {
    "triposr": "TripoSR",
    "instantmesh": "InstantMesh",
    "hunyuan21": "Hunyuan3D 2.1",
    "trellis": "TRELLIS",
}
MODEL_COLORS = {
    "triposr": "#4C78A8",
    "instantmesh": "#D4A72C",
    "hunyuan21": "#5B9E9A",
    "trellis": "#D97967",
}
CASE_LABELS = ("P1", "P2", "L1")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-root", type=Path, required=True)
    parser.add_argument("--evaluation-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--resolution", type=int, default=512)
    parser.add_argument("--grid-extent", type=float, default=1.5)
    return parser.parse_args()


def configure_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
            "font.size": 7,
            "axes.titlesize": 7.5,
            "axes.labelsize": 7,
            "xtick.labelsize": 6.5,
            "ytick.labelsize": 6.5,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "axes.linewidth": 0.7,
            "legend.frameon": False,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
        }
    )


def save_figure(fig: plt.Figure, stem: Path) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".tiff"), dpi=600, bbox_inches="tight")
    fig.savefig(stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def select_cases(paired: pd.DataFrame) -> pd.DataFrame:
    sketch = paired[paired["style"] == "sketch"].copy()
    model_means = sketch.groupby("model")["rg"].mean().sort_values(ascending=False)
    selected = []
    used_objects: set[str] = set()
    requests = (
        (CASE_LABELS[0], model_means.index[0], 0.90, "highest model mean; nearest 90th percentile"),
        (CASE_LABELS[1], model_means.index[1], 0.90, "second-highest model mean; nearest 90th percentile"),
        (CASE_LABELS[2], model_means.index[-1], 0.10, "lowest model mean; nearest 10th percentile"),
    )
    for case_label, model, quantile, rule in requests:
        candidates = sketch[sketch["model"] == model].copy()
        target = float(candidates["rg"].quantile(quantile))
        candidates["distance_to_target"] = np.abs(candidates["rg"] - target)
        candidates = candidates.sort_values(["distance_to_target", "object_id"])
        available = candidates[~candidates["object_id"].isin(used_objects)]
        if available.empty:
            available = candidates
        row = available.iloc[0].to_dict()
        used_objects.add(str(row["object_id"]))
        selected.append(
            {
                **row,
                "case_label": case_label,
                "selection_quantile": quantile,
                "selection_target_rg": target,
                "selection_rule": rule,
                "model_mean_rg": float(model_means[model]),
            }
        )
    return pd.DataFrame(selected)


def evaluation_rows(root: Path) -> pd.DataFrame:
    frames = [pd.read_csv(root / model / "evaluation_results.csv") for model in MODELS]
    return pd.concat(frames, ignore_index=True)


def camera_basis(direction: tuple[float, float, float]) -> np.ndarray:
    forward = np.asarray(direction, dtype=np.float64)
    forward /= np.linalg.norm(forward)
    up_reference = np.asarray((0.0, 1.0, 0.0), dtype=np.float64)
    if abs(float(np.dot(forward, up_reference))) > 0.9:
        up_reference = np.asarray((0.0, 0.0, 1.0), dtype=np.float64)
    right = np.cross(up_reference, forward)
    right /= np.linalg.norm(right)
    up = np.cross(forward, right)
    up /= np.linalg.norm(up)
    return np.stack((right, up, forward), axis=0)


def mesh_image(
    context: dr.RasterizeCudaContext,
    mesh,
    resolution: int,
    grid_extent: float,
) -> np.ndarray:
    vertices = torch.from_numpy(np.asarray(mesh.vertices, dtype=np.float32)).cuda()
    normals = torch.from_numpy(np.asarray(mesh.vertex_normals, dtype=np.float32)).cuda()
    faces = torch.from_numpy(np.asarray(mesh.faces, dtype=np.int32)).cuda()
    basis = torch.from_numpy(camera_basis((1.0, 0.75, 1.0)).astype(np.float32)).cuda()
    camera_vertices = vertices @ basis.T
    camera_normals = torch.nn.functional.normalize(normals @ basis.T, dim=-1)
    ones = torch.ones((len(vertices), 1), dtype=torch.float32, device="cuda")
    clip = torch.cat((camera_vertices / (grid_extent / 2.0), ones), dim=1)[None]
    raster, _ = dr.rasterize(context, clip, faces, resolution=[resolution, resolution])
    mask = raster[0, :, :, 3] > 0
    interpolated, _ = dr.interpolate(camera_normals[None], raster, faces)
    pixel_normals = torch.nn.functional.normalize(interpolated[0], dim=-1)
    light = torch.tensor((0.25, 0.35, 0.90), device="cuda", dtype=torch.float32)
    light = torch.nn.functional.normalize(light, dim=0)
    diffuse = torch.abs(torch.sum(pixel_normals * light, dim=-1))
    intensity = 0.42 + 0.48 * diffuse
    base = torch.tensor((0.78, 0.82, 0.87), device="cuda", dtype=torch.float32)
    image = torch.ones((resolution, resolution, 3), device="cuda", dtype=torch.float32)
    image[mask] = torch.clamp(intensity[mask][:, None] * base, 0.0, 1.0)
    return (image.detach().cpu().numpy() * 255).astype(np.uint8)


def input_image(path: str, resolution: int) -> np.ndarray:
    image = Image.open(path).convert("RGBA")
    background = Image.new("RGBA", image.size, (255, 255, 255, 255))
    background.alpha_composite(image)
    return np.asarray(background.convert("RGB").resize((resolution, resolution), Image.Resampling.LANCZOS))


def case_assets(
    context: dr.RasterizeCudaContext,
    case: dict,
    evaluations: pd.DataFrame,
    evaluation_root: Path,
    resolution: int,
    grid_extent: float,
) -> tuple[list[np.ndarray], dict]:
    model = case["model"]
    seed = -1 if model == "triposr" else 20260715
    subset = evaluations[
        (evaluations["model"] == model)
        & (evaluations["object_id"] == case["object_id"])
        & (evaluations["split"] == "main")
        & (evaluations["seed"] == seed)
        & (evaluations["style"].isin(("photo", "sketch")))
    ].set_index("style")
    if set(subset.index) != {"photo", "sketch"}:
        raise ValueError(f"Missing photo/sketch rows for {model} {case['object_id']} seed {seed}")
    calibration = json.loads(
        (evaluation_root / model / "calibration.json").read_text(encoding="utf-8")
    )
    photo = subset.loc["photo"]
    sketch = subset.loc["sketch"]
    gt_mesh = render.centered(render.load_mesh(Path(photo["gt_view_path"])))
    photo_mesh = render.transform_mesh(
        render.load_mesh(Path(photo["mesh_path"])),
        float(calibration["scale"]),
        np.asarray(calibration["matrix"], dtype=np.float64),
    )
    sketch_mesh = render.transform_mesh(
        render.load_mesh(Path(sketch["mesh_path"])),
        float(calibration["scale"]),
        np.asarray(calibration["matrix"], dtype=np.float64),
    )
    assets = [
        input_image(photo["input_path"], resolution),
        input_image(sketch["input_path"], resolution),
        mesh_image(context, gt_mesh, resolution, grid_extent),
        mesh_image(context, photo_mesh, resolution, grid_extent),
        mesh_image(context, sketch_mesh, resolution, grid_extent),
    ]
    details = {
        "display_seed": seed,
        "display_delta_fscore_0.05": float(sketch["fscore_0.05"] - photo["fscore_0.05"]),
        "display_delta_voxel_iou": float(sketch["voxel_iou"] - photo["voxel_iou"]),
        "photo_mesh_sha256": photo["mesh_sha256"],
        "sketch_mesh_sha256": sketch["mesh_sha256"],
        "photo_input_sha256": photo["input_sha256"],
        "sketch_input_sha256": sketch["input_sha256"],
    }
    return assets, details


def main() -> int:
    args = parse_args()
    configure_style()
    args.output_root.mkdir(parents=True, exist_ok=True)
    paired = pd.read_csv(args.analysis_root / "paired_main_object_averaged.csv")
    selected = select_cases(paired)
    evaluations = evaluation_rows(args.evaluation_root)
    context = dr.RasterizeCudaContext()

    all_assets = []
    details = []
    for case in selected.to_dict("records"):
        assets, detail = case_assets(
            context,
            case,
            evaluations,
            args.evaluation_root,
            args.resolution,
            args.grid_extent,
        )
        all_assets.append(assets)
        details.append(detail)
    selected = pd.concat((selected.reset_index(drop=True), pd.DataFrame(details)), axis=1)
    selected.to_csv(args.output_root / "representative_case_selection.csv", index=False)

    sketch = paired[paired["style"] == "sketch"].copy()
    fig = plt.figure(figsize=(7.2, 6.8))
    grid = fig.add_gridspec(
        4,
        6,
        left=0.05,
        right=0.98,
        bottom=0.04,
        top=0.97,
        hspace=0.50,
        wspace=0.08,
        height_ratios=(2.05, 1.0, 1.0, 1.0),
        width_ratios=(0.88, 1.0, 1.0, 1.0, 1.0, 1.0),
    )
    scatter_axis = fig.add_subplot(grid[0, :])
    for model in MODELS:
        subset = sketch[sketch["model"] == model]
        scatter_axis.scatter(
            subset["surface_degradation"],
            subset["solid_degradation"],
            s=10,
            color=MODEL_COLORS[model],
            alpha=0.42,
            edgecolors="none",
            label=MODEL_LABELS[model],
        )
    values = np.concatenate((sketch["surface_degradation"], sketch["solid_degradation"]))
    lower = float(np.nanmin(values) - 0.02)
    upper = float(np.nanmax(values) + 0.02)
    scatter_axis.plot([lower, upper], [lower, upper], color="#777777", linestyle="--", linewidth=0.8)
    annotation_offsets = {"P1": (4, 4), "P2": (4, -10), "L1": (4, 4)}
    for case in selected.to_dict("records"):
        scatter_axis.scatter(
            case["surface_degradation"],
            case["solid_degradation"],
            s=48,
            facecolor=MODEL_COLORS[case["model"]],
            edgecolor="#111111",
            linewidth=0.8,
            zorder=4,
        )
        scatter_axis.annotate(
            case["case_label"],
            (case["surface_degradation"], case["solid_degradation"]),
            xytext=annotation_offsets[case["case_label"]],
            textcoords="offset points",
            fontweight="bold",
            fontsize=6.5,
        )
    scatter_axis.set_xlim(lower, upper)
    scatter_axis.set_ylim(lower, upper)
    scatter_axis.set_xlabel("Surface F-score degradation")
    scatter_axis.set_ylabel("Solid IoU degradation")
    scatter_axis.set_title("Paired object-level sketch effects (n=120 objects per model)")
    scatter_axis.legend(ncol=4, loc="upper center", fontsize=6)
    scatter_axis.text(-0.055, 1.04, "a", transform=scatter_axis.transAxes, fontsize=8, fontweight="bold")

    column_titles = ("Photo input", "Sketch input", "Ground truth", "Photo output", "Sketch output")
    panel_labels = ("b", "c", "d")
    for row_index, (case, assets) in enumerate(zip(selected.to_dict("records"), all_assets), start=1):
        label_axis = fig.add_subplot(grid[row_index, 0])
        label_axis.axis("off")
        label_axis.text(0.0, 1.0, panel_labels[row_index - 1], fontsize=8, fontweight="bold", va="top")
        label_axis.text(
            0.15,
            0.82,
            f"{case['case_label']}\n{MODEL_LABELS[case['model']]}\n{case['object_id']}",
            fontsize=6.2,
            fontweight="bold",
            va="top",
        )
        label_axis.text(
            0.15,
            0.37,
            f"RG(avg)={case['rg']:.3f}\n"
            f"dF={case['display_delta_fscore_0.05']:.3f}\n"
            f"dIoU={case['display_delta_voxel_iou']:.3f}\n"
            f"seed={int(case['display_seed'])}",
            fontsize=5.5,
            va="top",
        )
        for column_index, asset in enumerate(assets):
            axis = fig.add_subplot(grid[row_index, column_index + 1])
            axis.imshow(asset)
            axis.set_xticks([])
            axis.set_yticks([])
            for spine in axis.spines.values():
                spine.set_color("#D0D0D0")
                spine.set_linewidth(0.5)
            if row_index == 1:
                axis.set_title(column_titles[column_index], fontsize=6.5, pad=3)

    save_figure(fig, args.output_root / "figure3_metric_gap_and_representative_cases")
    print(selected[["case_label", "model", "object_id", "rg", "display_seed"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
