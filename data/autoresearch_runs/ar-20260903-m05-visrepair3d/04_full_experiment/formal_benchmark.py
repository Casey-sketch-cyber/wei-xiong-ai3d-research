from __future__ import annotations

import math
import random
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np


PILOT_DIR = Path(__file__).resolve().parents[1] / "03_pilot"
if str(PILOT_DIR) not in sys.path:
    sys.path.insert(0, str(PILOT_DIR))

from revealrepair_core import (  # noqa: E402
    Action,
    Box,
    Scene,
    apply_action,
    apply_actions,
    derive_schedule,
    evaluate,
    hard_constraints,
    no_repair,
    result_to_row,
    scene_to_dict,
    solve_annealing,
    solve_beam,
    solve_random,
)


FORMAL_TRANSLATION_STEPS = [0.35, 0.60, 0.85, 1.10, 1.40, 1.80, 2.20, 2.75, 3.30]
FORMAL_ROTATION_DEGREES = [15, 30, 45, 75, 105, 150, 180]
CORRUPTIONS = [
    "premature_reveal",
    "missed_reveal",
    "back_facing",
    "target_displacement",
    "compound",
]


@dataclass(frozen=True)
class LayoutSpec:
    layout_id: str
    source: str
    theme: str
    room_width: float
    room_depth: float
    route_family: str
    route_amplitude: float
    exhibit_count: int
    exhibit_scale: float
    screen_depth: float
    screen_offset_x: float
    screen_offset_y: float


class CaseGenerationError(RuntimeError):
    pass


def _bounded(value: Any, low: float, high: float, fallback: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = fallback
    return min(max(numeric, low), high)


def make_layout_spec(
    seed: int,
    source: str = "procedural",
    overrides: dict[str, Any] | None = None,
) -> LayoutSpec:
    rng = random.Random(seed)
    values = dict(overrides or {})
    source_name = str(values.get("source", source))
    route_family = str(
        values.get("route_family", rng.choice(["straight", "arc", "serpentine"]))
    ).lower()
    if route_family not in {"straight", "arc", "serpentine"}:
        route_family = "straight"
    exhibit_count = int(round(_bounded(values.get("exhibit_count"), 3, 5, 3 + seed % 3)))
    room_width = _bounded(
        values.get("room_width"),
        15.5,
        20.5,
        15.8 + rng.random() * 4.4,
    )
    if exhibit_count == 5:
        room_width = max(room_width, 17.0)
    return LayoutSpec(
        layout_id=str(values.get("layout_id", f"{source_name}_{seed}")),
        source=source_name,
        theme=str(values.get("theme", "neutral contemporary exhibition"))[:120],
        room_width=room_width,
        room_depth=_bounded(
            values.get("room_depth"),
            9.5,
            12.5,
            9.7 + rng.random() * 2.5,
        ),
        route_family=route_family,
        route_amplitude=_bounded(
            values.get("route_amplitude"),
            0.08,
            0.55,
            0.12 + rng.random() * 0.34,
        ),
        exhibit_count=exhibit_count,
        exhibit_scale=_bounded(
            values.get("exhibit_scale"),
            0.82,
            1.18,
            0.88 + rng.random() * 0.24,
        ),
        screen_depth=_bounded(
            values.get("screen_depth"),
            2.20,
            2.85,
            2.30 + rng.random() * 0.45,
        ),
        screen_offset_x=_bounded(
            values.get("screen_offset_x"),
            1.15,
            1.55,
            1.20 + rng.random() * 0.28,
        ),
        screen_offset_y=_bounded(
            values.get("screen_offset_y"),
            2.00,
            2.60,
            2.10 + rng.random() * 0.35,
        ),
    )


def _make_route(spec: LayoutSpec, route_samples: int, rng: np.random.Generator) -> list[list[float]]:
    xs = np.linspace(0.055 * spec.room_width, 0.945 * spec.room_width, route_samples)
    u = np.linspace(0.0, 1.0, route_samples)
    phase = rng.uniform(0.0, 2.0 * math.pi)
    base_y = 0.19 * spec.room_depth
    if spec.route_family == "arc":
        ys = base_y + spec.route_amplitude * (1.0 - (2.0 * u - 1.0) ** 2)
    elif spec.route_family == "serpentine":
        ys = base_y + spec.route_amplitude * np.sin(2.0 * math.pi * 1.25 * u + phase)
    else:
        ys = base_y + 0.08 * np.sin(2.0 * math.pi * u + phase)
    ys = np.clip(ys, 0.95, 0.31 * spec.room_depth)
    return [[float(x), float(y), 1.62] for x, y in zip(xs, ys, strict=True)]


def make_formal_base_scene(
    seed: int,
    source: str = "procedural",
    overrides: dict[str, Any] | None = None,
    route_samples: int = 36,
    surface_grid: int = 3,
) -> tuple[Scene, dict[str, list[int]], dict[str, Any]]:
    spec = make_layout_spec(seed, source, overrides)
    for attempt in range(12):
        rng = np.random.default_rng(seed * 97 + attempt * 7919)
        room = [0.0, spec.room_width, 0.0, spec.room_depth]
        route = _make_route(spec, route_samples, rng)
        objects: list[Box] = []
        exhibit_order: list[str] = []
        x_positions = np.linspace(
            0.31 * spec.room_width,
            0.82 * spec.room_width,
            spec.exhibit_count,
        )
        exhibit_y = 0.79 * spec.room_depth
        for index, nominal_x in enumerate(x_positions):
            target_id = f"exhibit_{index}"
            exhibit_order.append(target_id)
            x = float(nominal_x + rng.uniform(-0.12, 0.12))
            y = float(exhibit_y + rng.uniform(-0.08, 0.08))
            scale = spec.exhibit_scale * float(rng.uniform(0.92, 1.08))
            objects.append(
                Box(
                    object_id=target_id,
                    kind="exhibit",
                    center=[x, y, 1.30],
                    size=[1.00 * scale, 0.40 * scale, 2.05 * scale],
                    yaw=float(rng.uniform(-0.05, 0.05)),
                    movable=True,
                )
            )
            screen_y = y - spec.screen_offset_y + float(rng.uniform(-0.07, 0.07))
            objects.append(
                Box(
                    object_id=f"screen_{target_id}",
                    kind="partition",
                    center=[
                        x - spec.screen_offset_x + float(rng.uniform(-0.06, 0.06)),
                        screen_y,
                        1.35,
                    ],
                    size=[0.20, spec.screen_depth, 2.70],
                    yaw=float(rng.uniform(-0.025, 0.025)),
                    movable=True,
                    target_id=target_id,
                )
            )
        scene = Scene(
            scene_id=spec.layout_id,
            room=room,
            route=route,
            objects=objects,
            exhibit_order=exhibit_order,
            protected_order=list(exhibit_order),
            surface_grid=surface_grid,
            path_check_step=0.18,
        )
        labels = derive_schedule(scene, minimum_hidden=4, show_window=5)
        valid, *_ = hard_constraints(scene)
        if labels is not None and valid:
            metadata = asdict(spec) | {
                "seed": seed,
                "generation_attempt": attempt,
                "route_samples": route_samples,
                "surface_grid": surface_grid,
            }
            return scene, labels, metadata
    raise CaseGenerationError(f"unable to build a valid base scene for seed {seed}")


def _severity_values(severity: int) -> tuple[float, float, float]:
    if severity not in {1, 2, 3}:
        raise ValueError("severity must be 1, 2, or 3")
    screen_shift = {1: 2.05, 2: 2.50, 3: 3.00}[severity]
    local_shift = {1: 0.73, 2: 1.03, 3: 1.33}[severity]
    yaw_degrees = {1: 145.0, 2: 163.0, 3: 177.0}[severity]
    return screen_shift, local_shift, math.radians(yaw_degrees)


def _premature_actions(screen_id: str, screen_shift: float, severity: int) -> list[Action]:
    yaw_shift = math.radians({1: 37.0, 2: 53.0, 3: 67.0}[severity])
    translations = [screen_shift, 0.72 * screen_shift, 0.55 * screen_shift]
    actions: list[Action] = []
    for amount in translations:
        for direction in (-1.0, 1.0):
            actions.append(Action(screen_id, dx=direction * amount))
            actions.append(Action(screen_id, dy=direction * amount))
    actions.extend(
        Action(screen_id, dyaw=direction * yaw_shift) for direction in (-1.0, 1.0)
    )
    return actions


def _best_single_action(
    base: Scene,
    labels: dict[str, list[int]],
    actions: list[Action],
    component: str,
) -> tuple[Scene, Action]:
    base_eval = evaluate(base, labels)
    candidates: list[tuple[tuple[float, float], Scene, Action]] = []
    for action in actions:
        candidate = apply_action(base, action)
        result = evaluate(candidate, labels)
        if not result.hard_valid:
            continue
        if component == "leakage":
            component_gain = result.leakage_loss - base_eval.leakage_loss
        elif component == "missed":
            component_gain = result.missed_loss - base_eval.missed_loss
        else:
            component_gain = result.schedule_loss - base_eval.schedule_loss
        total_gain = result.schedule_loss - base_eval.schedule_loss
        if component_gain > 1e-6 and total_gain > 1e-6:
            candidates.append(((component_gain, total_gain), candidate, action))
    if not candidates:
        raise CaseGenerationError(f"no hard-valid action created a {component} violation")
    candidates.sort(key=lambda item: item[0], reverse=True)
    _, candidate, action = candidates[0]
    return candidate, action


def formal_corrupt_scene(
    base: Scene,
    labels: dict[str, list[int]],
    corruption: str,
    severity: int,
    seed: int,
) -> tuple[Scene, list[Action], dict[str, Any]]:
    rng = random.Random(seed)
    screen_shift, local_shift, yaw_shift = _severity_values(severity)
    target_id = rng.choice(base.exhibit_order)
    screen_id = f"screen_{target_id}"
    if corruption == "premature_reveal":
        actions = _premature_actions(screen_id, screen_shift, severity)
        corrupted, applied = _best_single_action(base, labels, actions, "leakage")
        applied_actions = [applied]
    elif corruption == "missed_reveal":
        actions = [
            Action(screen_id, dx=direction * local_shift)
            for direction in (-1.0, 1.0)
        ] + [
            Action(screen_id, dy=direction * local_shift)
            for direction in (-1.0, 1.0)
        ]
        corrupted, applied = _best_single_action(base, labels, actions, "missed")
        applied_actions = [applied]
    elif corruption == "back_facing":
        actions = [
            Action(target_id, dyaw=direction * yaw_shift)
            for direction in (-1.0, 1.0)
        ]
        corrupted, applied = _best_single_action(base, labels, actions, "missed")
        applied_actions = [applied]
    elif corruption == "target_displacement":
        actions = [
            Action(target_id, dx=direction * local_shift)
            for direction in (-1.0, 1.0)
        ] + [
            Action(target_id, dy=direction * local_shift)
            for direction in (-1.0, 1.0)
        ]
        corrupted, applied = _best_single_action(base, labels, actions, "total")
        applied_actions = [applied]
    elif corruption == "compound":
        pairs: list[tuple[tuple[float, float, float], Scene, list[Action]]] = []
        base_eval = evaluate(base, labels)
        for first_target in base.exhibit_order:
            first_screen = f"screen_{first_target}"
            screen_actions = _premature_actions(first_screen, screen_shift, severity)
            for second_target in base.exhibit_order:
                if second_target == first_target:
                    continue
                for first in screen_actions:
                    for direction in (-1.0, 1.0):
                        second = Action(second_target, dyaw=direction * yaw_shift)
                        candidate = apply_actions(base, [first, second])
                        result = evaluate(candidate, labels)
                        leakage_gain = result.leakage_loss - base_eval.leakage_loss
                        missed_gain = result.missed_loss - base_eval.missed_loss
                        if result.hard_valid and leakage_gain > 1e-6 and missed_gain > 1e-6:
                            pairs.append(
                                (
                                    (result.schedule_loss, leakage_gain, missed_gain),
                                    candidate,
                                    [first, second],
                                )
                            )
        if not pairs:
            raise CaseGenerationError("no hard-valid compound corruption found")
        pairs.sort(key=lambda item: item[0], reverse=True)
        _, corrupted, applied_actions = pairs[0]
    else:
        raise ValueError(f"unknown corruption: {corruption}")

    corrupted.scene_id = f"{base.scene_id}_{corruption}_s{severity}_{seed}"
    result = evaluate(corrupted, labels)
    if not result.hard_valid or result.schedule_loss <= 1e-6:
        raise CaseGenerationError(f"invalid formal corruption: {corrupted.scene_id}")
    inverse = [
        Action(action.object_id, -action.dx, -action.dy, -action.dyaw)
        for action in reversed(applied_actions)
    ]
    metadata = {
        "target_id": target_id,
        "applied_corruption": [asdict(action) for action in applied_actions],
        "known_inverse": [asdict(action) for action in inverse],
        "off_grid": all(
            (
                not any(
                    abs(abs(value) - step) < 1e-9
                    for step in FORMAL_TRANSLATION_STEPS
                )
                if axis != "dyaw"
                else not any(
                    abs(abs(math.degrees(value)) - step) < 1e-9
                    for step in FORMAL_ROTATION_DEGREES
                )
            )
            for action in applied_actions
            for axis, value in (
                ("dx", action.dx),
                ("dy", action.dy),
                ("dyaw", action.dyaw),
            )
            if abs(value) > 1e-9
        ),
    }
    return corrupted, inverse, metadata


def run_case(task: dict[str, Any]) -> dict[str, Any]:
    base_seed = int(task["base_seed"])
    severity = int(task["severity"])
    corruption = str(task["corruption"])
    case_seed = int(task["case_seed"])
    budget = int(task["budget"])
    beam_width = int(task["beam_width"])
    max_depth = int(task["max_depth"])
    source = str(task.get("source", "procedural"))
    overrides = task.get("overrides")
    base, labels, layout_metadata = make_formal_base_scene(
        base_seed,
        source=source,
        overrides=overrides,
        route_samples=int(task.get("route_samples", 36)),
        surface_grid=int(task.get("surface_grid", 3)),
    )
    corrupted, inverse, corruption_metadata = formal_corrupt_scene(
        base, labels, corruption, severity, case_seed
    )
    common = {
        "max_depth": max_depth,
        "beam_width": beam_width,
        "max_evaluations": budget,
        "translation_steps": FORMAL_TRANSLATION_STEPS,
        "rotation_degrees": FORMAL_ROTATION_DEGREES,
    }
    results = [
        no_repair(corrupted, labels),
        solve_beam(
            "visibility_max_only",
            corrupted,
            labels,
            attributed=False,
            objective="visibility_only",
            **common,
        ),
        solve_random(
            corrupted,
            labels,
            case_seed + 11,
            budget,
            FORMAL_TRANSLATION_STEPS,
            FORMAL_ROTATION_DEGREES,
        ),
        solve_beam(
            "generic_greedy",
            corrupted,
            labels,
            attributed=False,
            **common,
        ),
        solve_annealing(
            corrupted,
            labels,
            case_seed + 29,
            budget,
            FORMAL_TRANSLATION_STEPS,
            FORMAL_ROTATION_DEGREES,
        ),
        solve_beam(
            "revealrepair_attributed",
            corrupted,
            labels,
            attributed=True,
            **common,
        ),
    ]
    if bool(task.get("run_ablations", False)):
        results.extend(
            [
                solve_beam(
                    "ablation_visibility_only",
                    corrupted,
                    labels,
                    attributed=True,
                    objective="visibility_only",
                    **common,
                ),
                solve_beam(
                    "ablation_no_sparsity",
                    corrupted,
                    labels,
                    attributed=True,
                    use_sparsity=False,
                    **common,
                ),
                solve_beam(
                    "ablation_no_hard_filter",
                    corrupted,
                    labels,
                    attributed=True,
                    enforce_hard=False,
                    **common,
                ),
                solve_beam(
                    "ablation_targets_only",
                    corrupted,
                    labels,
                    attributed=True,
                    object_scope="targets",
                    **common,
                ),
                solve_beam(
                    "ablation_partitions_only",
                    corrupted,
                    labels,
                    attributed=True,
                    object_scope="partitions",
                    **common,
                ),
            ]
        )

    rows: list[dict[str, Any]] = []
    for result in results:
        row = result_to_row(corrupted.scene_id, corruption, severity, case_seed, result)
        row.update(
            {
                "source": layout_metadata["source"],
                "layout_id": layout_metadata["layout_id"],
                "base_seed": base_seed,
                "route_family": layout_metadata["route_family"],
                "route_samples": layout_metadata["route_samples"],
                "surface_grid": layout_metadata["surface_grid"],
                "exhibit_count": layout_metadata["exhibit_count"],
                "generation_attempt": layout_metadata["generation_attempt"],
            }
        )
        rows.append(row)
    return {
        "task_id": str(task["task_id"]),
        "case": {
            "case_id": corrupted.scene_id,
            "layout_metadata": layout_metadata,
            "corruption": corruption,
            "severity": severity,
            "case_seed": case_seed,
            "base": scene_to_dict(base),
            "corrupted": scene_to_dict(corrupted),
            "labels": labels,
            "known_inverse": [asdict(action) for action in inverse],
            "corruption_metadata": corruption_metadata,
        },
        "rows": rows,
    }
