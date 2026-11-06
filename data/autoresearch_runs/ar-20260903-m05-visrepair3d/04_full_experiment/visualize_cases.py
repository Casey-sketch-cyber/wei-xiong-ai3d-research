from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon, Rectangle
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


PILOT_DIR = Path(__file__).resolve().parents[1] / "03_pilot"
if str(PILOT_DIR) not in sys.path:
    sys.path.insert(0, str(PILOT_DIR))

from revealrepair_core import (  # noqa: E402
    TAU_OFF,
    TAU_ON,
    Action,
    Box,
    Scene,
    apply_actions,
    evaluate,
    rectangle_corners,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def scene_from_dict(value: dict[str, Any]) -> Scene:
    return Scene(
        scene_id=str(value["scene_id"]),
        room=[float(item) for item in value["room"]],
        route=[[float(item) for item in point] for point in value["route"]],
        objects=[Box(**item) for item in value["objects"]],
        exhibit_order=[str(item) for item in value["exhibit_order"]],
        protected_order=[str(item) for item in value["protected_order"]],
        surface_grid=int(value.get("surface_grid", 3)),
        path_check_step=float(value.get("path_check_step", 0.18)),
    )


def plot_scene(
    axis: plt.Axes,
    scene: Scene,
    edited: set[str],
    title: str,
) -> None:
    xmin, xmax, ymin, ymax = scene.room
    axis.add_patch(
        Rectangle((xmin, ymin), xmax - xmin, ymax - ymin, fill=False, ec="#222222", lw=1.2)
    )
    route = np.asarray(scene.route)
    axis.plot(route[:, 0], route[:, 1], color="#333333", lw=1.5, zorder=1)
    axis.scatter(
        route[:, 0],
        route[:, 1],
        c=np.linspace(0.0, 1.0, len(route)),
        cmap="viridis",
        s=7,
        zorder=2,
    )
    for object_index, obj in enumerate(scene.objects):
        corners = rectangle_corners(obj)
        face = "#70A6A1" if obj.kind == "exhibit" else "#B6BBC4"
        edge = "#C63D3D" if obj.object_id in edited else "#3F4650"
        width = 2.0 if obj.object_id in edited else 0.8
        axis.add_patch(Polygon(corners, closed=True, fc=face, ec=edge, lw=width, alpha=0.88))
        if obj.kind == "exhibit":
            axis.text(
                obj.center[0],
                obj.center[1] + 0.35,
                f"E{object_index // 2 + 1}",
                ha="center",
                va="bottom",
                fontsize=8,
            )
    axis.set_xlim(xmin - 0.35, xmax + 0.35)
    axis.set_ylim(ymin - 0.35, ymax + 0.35)
    axis.set_aspect("equal")
    axis.set_title(title, loc="left", fontsize=10, fontweight="bold")
    axis.set_xticks([])
    axis.set_yticks([])
    for spine in axis.spines.values():
        spine.set_visible(False)


def cuboid_faces(box: Box) -> list[list[list[float]]]:
    footprint = rectangle_corners(box)
    bottom = box.center[2] - box.size[2] / 2.0
    top = box.center[2] + box.size[2] / 2.0
    lower = [[float(x), float(y), float(bottom)] for x, y in footprint]
    upper = [[float(x), float(y), float(top)] for x, y in footprint]
    return [
        lower,
        upper,
        [lower[0], lower[1], upper[1], upper[0]],
        [lower[1], lower[2], upper[2], upper[1]],
        [lower[2], lower[3], upper[3], upper[2]],
        [lower[3], lower[0], upper[0], upper[3]],
    ]


def plot_scene_3d(
    axis: plt.Axes,
    scene: Scene,
    edited: set[str],
    title: str,
) -> None:
    xmin, xmax, ymin, ymax = scene.room
    floor = Poly3DCollection(
        [[(xmin, ymin, 0.0), (xmax, ymin, 0.0), (xmax, ymax, 0.0), (xmin, ymax, 0.0)]],
        facecolors="#F5F6F7",
        edgecolors="#A9AFB8",
        linewidths=0.8,
        alpha=0.65,
    )
    axis.add_collection3d(floor)
    for object_index, obj in enumerate(scene.objects):
        face = "#70A6A1" if obj.kind == "exhibit" else "#B6BBC4"
        edge = "#C63D3D" if obj.object_id in edited else "#3F4650"
        width = 1.8 if obj.object_id in edited else 0.7
        collection = Poly3DCollection(
            cuboid_faces(obj),
            facecolors=face,
            edgecolors=edge,
            linewidths=width,
            alpha=0.86,
        )
        axis.add_collection3d(collection)
        if obj.kind == "exhibit":
            axis.text(
                obj.center[0],
                obj.center[1],
                obj.center[2] + obj.size[2] / 2.0 + 0.22,
                f"E{object_index // 2 + 1}",
                ha="center",
                va="bottom",
                fontsize=8,
            )
    route = np.asarray(scene.route, dtype=float)
    axis.plot(route[:, 0], route[:, 1], route[:, 2], color="#30343B", lw=1.6)
    axis.scatter(
        route[:, 0],
        route[:, 1],
        route[:, 2],
        c=np.linspace(0.0, 1.0, len(route)),
        cmap="viridis",
        s=11,
        depthshade=False,
    )
    axis.set_xlim(xmin, xmax)
    axis.set_ylim(ymin, ymax)
    axis.set_zlim(0.0, max(3.4, max(obj.center[2] + obj.size[2] / 2.0 for obj in scene.objects)))
    axis.set_box_aspect((xmax - xmin, ymax - ymin, 5.0), zoom=1.12)
    axis.view_init(elev=24, azim=-66)
    axis.set_xlabel("x (m)", labelpad=5)
    axis.set_ylabel("y (m)", labelpad=5)
    axis.set_zlabel("z (m)", labelpad=3)
    axis.set_title(title, loc="left", fontsize=11, fontweight="bold", pad=0, y=0.89)
    axis.grid(color="#DDE1E6", linewidth=0.5)


def target_violation(
    target_id: str,
    labels: dict[str, list[int]],
    visibility: dict[str, list[float]],
) -> float:
    total = 0.0
    for label, value in zip(labels[target_id], visibility[target_id], strict=True):
        if label == 1:
            total += max(TAU_ON - value, 0.0)
        elif label == -1:
            total += max(value - TAU_OFF, 0.0)
    return total


def plot_profile(
    axis: plt.Axes,
    before: Scene,
    after: Scene,
    labels: dict[str, list[int]],
    panel_label: str,
    edit_count: int,
) -> str:
    before_eval = evaluate(before, labels)
    after_eval = evaluate(after, labels)
    target_id = max(
        before.exhibit_order,
        key=lambda object_id: target_violation(object_id, labels, before_eval.visibility),
    )
    target_labels = labels[target_id]
    x = np.arange(len(target_labels))
    show = np.asarray(target_labels) == 1
    hide = np.asarray(target_labels) == -1
    axis.fill_between(x, 0.0, 1.0, where=hide, step="mid", color="#F2C9C9", alpha=0.45)
    axis.fill_between(x, 0.0, 1.0, where=show, step="mid", color="#C9E4D3", alpha=0.55)
    axis.plot(x, before_eval.visibility[target_id], color="#C63D3D", lw=1.8, label="Corrupted")
    axis.plot(x, after_eval.visibility[target_id], color="#216E9B", lw=1.8, label="Repaired")
    axis.axhline(TAU_ON, color="#356A46", lw=0.9, ls="--")
    axis.axhline(TAU_OFF, color="#8A4141", lw=0.9, ls="--")
    axis.set_ylim(-0.03, 1.03)
    axis.set_xlim(0, len(x) - 1)
    axis.set_xlabel("Route sample")
    axis.set_ylabel("Visible front-surface fraction")
    axis.set_title(
        f"{panel_label}  Visibility schedule for {target_id.replace('_', ' ')}",
        loc="left",
        fontsize=10,
        fontweight="bold",
        pad=20,
    )
    axis.text(
        0.0,
        1.015,
        f"Loss {before_eval.schedule_loss:.3f} -> {after_eval.schedule_loss:.3f}; "
        f"edited entities = {edit_count}",
        transform=axis.transAxes,
        fontsize=8,
        ha="left",
        va="bottom",
    )
    axis.grid(color="#D9DEE7", lw=0.6)
    axis.set_axisbelow(True)
    axis.legend(frameon=False, fontsize=8, loc="upper right")
    return target_id


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.experiment / "full_cases.json").open("r", encoding="utf-8") as handle:
        cases = json.load(handle)
    case_map = {case["case_id"]: case for case in cases}
    with (args.experiment / "full_results.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    ours = {
        row["case_id"]: row
        for row in rows
        if row["method"] == "revealrepair_attributed" and float(row["schedule_loss"]) <= 0.005
    }
    no_repair = {
        row["case_id"]: row for row in rows if row["method"] == "no_repair"
    }
    chosen = []
    for corruption in ("premature_reveal", "back_facing", "compound"):
        candidates = [
            case_id
            for case_id in ours
            if case_map[case_id]["corruption"] == corruption
        ]
        if not candidates:
            continue
        chosen.append(
            max(candidates, key=lambda case_id: float(no_repair[case_id]["schedule_loss"]))
        )
    if len(chosen) != 3:
        raise RuntimeError("could not select three representative successful cases")

    figure, axes = plt.subplots(3, 3, figsize=(12.0, 10.2))
    records = []
    for row_index, case_id in enumerate(chosen):
        case = case_map[case_id]
        corrupted = scene_from_dict(case["corrupted"])
        actions = [Action(**value) for value in json.loads(ours[case_id]["actions"])]
        repaired = apply_actions(corrupted, actions)
        labels = {key: [int(value) for value in values] for key, values in case["labels"].items()}
        edited = {action.object_id for action in actions}
        plot_scene(axes[row_index, 0], corrupted, edited, f"{chr(65 + row_index * 3)}  Corrupted layout")
        plot_scene(axes[row_index, 1], repaired, edited, f"{chr(66 + row_index * 3)}  Sparse repair")
        target_id = plot_profile(
            axes[row_index, 2],
            corrupted,
            repaired,
            labels,
            chr(67 + row_index * 3),
            len(edited),
        )
        before_eval = evaluate(corrupted, labels)
        after_eval = evaluate(repaired, labels)
        records.append(
            {
                "case_id": case_id,
                "corruption": case["corruption"],
                "severity": case["severity"],
                "profile_target": target_id,
                "before_loss": before_eval.schedule_loss,
                "after_loss": after_eval.schedule_loss,
                "actions": [action.__dict__ for action in actions],
            }
        )
    figure.tight_layout(h_pad=2.0, w_pad=1.4)
    figure.savefig(args.output / "figure_representative_repairs.png", dpi=300, bbox_inches="tight")
    figure.savefig(args.output / "figure_representative_repairs.pdf", bbox_inches="tight")
    plt.close(figure)
    with (args.output / "representative_cases.json").open("w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)

    overview_case_id = chosen[-1]
    overview_case = case_map[overview_case_id]
    overview_corrupted = scene_from_dict(overview_case["corrupted"])
    overview_actions = [
        Action(**value) for value in json.loads(ours[overview_case_id]["actions"])
    ]
    overview_repaired = apply_actions(overview_corrupted, overview_actions)
    overview_edited = {action.object_id for action in overview_actions}
    overview, overview_axes = plt.subplots(
        1,
        2,
        figsize=(12.0, 4.8),
        subplot_kw={"projection": "3d"},
    )
    plot_scene_3d(
        overview_axes[0],
        overview_corrupted,
        overview_edited,
        "A  Corrupted 3D exhibition layout",
    )
    plot_scene_3d(
        overview_axes[1],
        overview_repaired,
        overview_edited,
        "B  Sparse route-conditioned repair",
    )
    overview.tight_layout(w_pad=1.5)
    overview.savefig(args.output / "figure_3d_repair_overview.png", dpi=300, bbox_inches="tight")
    overview.savefig(args.output / "figure_3d_repair_overview.pdf", bbox_inches="tight")
    plt.close(overview)
    print(json.dumps(records, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
