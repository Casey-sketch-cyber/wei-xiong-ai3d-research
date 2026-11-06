from __future__ import annotations

import copy
import math
import random
import time
from dataclasses import asdict, dataclass
from typing import Iterable

import numpy as np


TAU_ON = 0.60
TAU_OFF = 0.12
ROOM_MARGIN = 0.08
PATH_CLEARANCE = 0.48


@dataclass
class Box:
    object_id: str
    kind: str
    center: list[float]
    size: list[float]
    yaw: float = 0.0
    movable: bool = True
    target_id: str | None = None

    def clone(self) -> "Box":
        return copy.deepcopy(self)


@dataclass(frozen=True)
class Action:
    object_id: str
    dx: float = 0.0
    dy: float = 0.0
    dyaw: float = 0.0


@dataclass
class Scene:
    scene_id: str
    room: list[float]
    route: list[list[float]]
    objects: list[Box]
    exhibit_order: list[str]
    protected_order: list[str]
    surface_grid: int = 3
    path_check_step: float = 0.18

    def clone(self) -> "Scene":
        return copy.deepcopy(self)

    def object_map(self) -> dict[str, Box]:
        return {obj.object_id: obj for obj in self.objects}


@dataclass
class Evaluation:
    schedule_loss: float
    missed_loss: float
    leakage_loss: float
    satisfaction: float
    missed_violations: int
    leakage_violations: int
    reveal_order_inversions: int
    hard_valid: bool
    collision_count: int
    path_clearance_violations: int
    bounds_violations: int
    relation_violations: int
    visibility: dict[str, list[float]]
    first_blockers: dict[str, dict[int, dict[str, int]]]


@dataclass
class SolverResult:
    method: str
    scene: Scene
    evaluation: Evaluation
    actions: list[Action]
    edit_count: int
    translation_cost: float
    yaw_cost: float
    edit_cost: float
    evaluations: int
    runtime_seconds: float


def rotation(yaw: float) -> np.ndarray:
    c, s = math.cos(yaw), math.sin(yaw)
    return np.array([[c, -s], [s, c]], dtype=float)


def wrap_angle(value: float) -> float:
    return (value + math.pi) % (2.0 * math.pi) - math.pi


def rectangle_corners(box: Box) -> np.ndarray:
    hx, hy = box.size[0] / 2.0, box.size[1] / 2.0
    local = np.array([[-hx, -hy], [hx, -hy], [hx, hy], [-hx, hy]])
    return local @ rotation(box.yaw).T + np.asarray(box.center[:2], dtype=float)


def polygons_overlap(a: np.ndarray, b: np.ndarray, tolerance: float = 1e-6) -> bool:
    for polygon in (a, b):
        for index in range(len(polygon)):
            edge = polygon[(index + 1) % len(polygon)] - polygon[index]
            axis = np.array([-edge[1], edge[0]], dtype=float)
            norm = np.linalg.norm(axis)
            if norm < 1e-12:
                continue
            axis /= norm
            proj_a = a @ axis
            proj_b = b @ axis
            if proj_a.max() <= proj_b.min() + tolerance:
                return False
            if proj_b.max() <= proj_a.min() + tolerance:
                return False
    return True


def point_to_box_distance(point: np.ndarray, box: Box) -> float:
    local = rotation(box.yaw).T @ (point[:2] - np.asarray(box.center[:2]))
    half = np.asarray(box.size[:2]) / 2.0
    delta = np.maximum(np.abs(local) - half, 0.0)
    return float(np.linalg.norm(delta))


def ray_box_distance(origin: np.ndarray, endpoint: np.ndarray, box: Box) -> float | None:
    direction = endpoint - origin
    distance = float(np.linalg.norm(direction))
    if distance < 1e-9:
        return None
    direction /= distance

    rot = rotation(box.yaw)
    local_origin_xy = rot.T @ (origin[:2] - np.asarray(box.center[:2]))
    local_direction_xy = rot.T @ direction[:2]
    local_origin = np.array(
        [local_origin_xy[0], local_origin_xy[1], origin[2] - box.center[2]],
        dtype=float,
    )
    local_direction = np.array(
        [local_direction_xy[0], local_direction_xy[1], direction[2]], dtype=float
    )
    half = np.asarray(box.size, dtype=float) / 2.0

    t_min, t_max = 0.0, distance
    for axis in range(3):
        if abs(local_direction[axis]) < 1e-10:
            if abs(local_origin[axis]) > half[axis]:
                return None
            continue
        t1 = (-half[axis] - local_origin[axis]) / local_direction[axis]
        t2 = (half[axis] - local_origin[axis]) / local_direction[axis]
        near, far = min(t1, t2), max(t1, t2)
        t_min = max(t_min, near)
        t_max = min(t_max, far)
        if t_min > t_max:
            return None
    if t_max < 0.0 or t_min >= distance - 1e-4:
        return None
    return max(0.0, t_min)


def front_samples(box: Box, grid: int = 3) -> tuple[np.ndarray, np.ndarray]:
    width, depth, height = box.size
    if grid < 2:
        raise ValueError("surface grid must be at least 2")
    xs = np.linspace(-0.42 * width, 0.42 * width, grid)
    zs = np.linspace(-0.32 * height, 0.32 * height, grid)
    local_xy = np.array([[x, -depth / 2.0 - 1e-4] for z in zs for x in xs])
    world_xy = local_xy @ rotation(box.yaw).T + np.asarray(box.center[:2])
    world_z = np.array([box.center[2] + z for z in zs for _ in xs])
    points = np.column_stack((world_xy, world_z))
    normal_xy = rotation(box.yaw) @ np.array([0.0, -1.0])
    return points, np.array([normal_xy[0], normal_xy[1], 0.0])


def visibility_at(scene: Scene, target: Box, camera: np.ndarray) -> tuple[float, dict[str, int]]:
    points, front_normal = front_samples(target, scene.surface_grid)
    toward_camera = camera - np.asarray(target.center, dtype=float)
    toward_camera[2] = 0.0
    norm = np.linalg.norm(toward_camera)
    if norm < 1e-9 or float(np.dot(front_normal[:2], toward_camera[:2] / norm)) < 0.08:
        return 0.0, {"BACK_FACING": len(points)}

    visible = 0
    blockers: dict[str, int] = {}
    for point in points:
        segment_length = float(np.linalg.norm(point - camera))
        first_id: str | None = None
        first_distance = segment_length
        for obj in scene.objects:
            if obj.object_id == target.object_id:
                continue
            hit = ray_box_distance(camera, point, obj)
            if hit is not None and hit < first_distance - 1e-3:
                first_id = obj.object_id
                first_distance = hit
        if first_id is None:
            visible += 1
        else:
            blockers[first_id] = blockers.get(first_id, 0) + 1
    return visible / len(points), blockers


def compute_visibility(scene: Scene) -> tuple[dict[str, list[float]], dict[str, dict[int, dict[str, int]]]]:
    objects = scene.object_map()
    profiles: dict[str, list[float]] = {}
    blockers: dict[str, dict[int, dict[str, int]]] = {}
    for target_id in scene.exhibit_order:
        target = objects[target_id]
        profile: list[float] = []
        target_blockers: dict[int, dict[str, int]] = {}
        for index, route_point in enumerate(scene.route):
            camera = np.array([route_point[0], route_point[1], route_point[2]], dtype=float)
            value, first_hits = visibility_at(scene, target, camera)
            profile.append(value)
            if first_hits:
                target_blockers[index] = first_hits
        profiles[target_id] = profile
        blockers[target_id] = target_blockers
    return profiles, blockers


def dense_route_points(scene: Scene) -> list[np.ndarray]:
    route = [np.asarray(point, dtype=float) for point in scene.route]
    if len(route) < 2:
        return route
    samples: list[np.ndarray] = [route[0]]
    for start, end in zip(route, route[1:]):
        distance = float(np.linalg.norm(end[:2] - start[:2]))
        segments = max(
            1,
            int(math.ceil(distance / max(scene.path_check_step, 1e-3))),
        )
        for index in range(1, segments + 1):
            samples.append(start + (end - start) * (index / segments))
    return samples


def hard_constraints(scene: Scene) -> tuple[bool, int, int, int, int]:
    xmin, xmax, ymin, ymax = scene.room
    bounds = 0
    for obj in scene.objects:
        corners = rectangle_corners(obj)
        if (
            corners[:, 0].min() < xmin + ROOM_MARGIN
            or corners[:, 0].max() > xmax - ROOM_MARGIN
            or corners[:, 1].min() < ymin + ROOM_MARGIN
            or corners[:, 1].max() > ymax - ROOM_MARGIN
        ):
            bounds += 1

    collisions = 0
    for i, first in enumerate(scene.objects):
        a = rectangle_corners(first)
        for second in scene.objects[i + 1 :]:
            vertical_overlap = abs(first.center[2] - second.center[2]) < (
                first.size[2] + second.size[2]
            ) / 2.0
            if vertical_overlap and polygons_overlap(a, rectangle_corners(second)):
                collisions += 1

    path_violations = 0
    for p in dense_route_points(scene):
        if any(point_to_box_distance(p, obj) < PATH_CLEARANCE for obj in scene.objects):
            path_violations += 1

    relations = 0
    objects = scene.object_map()
    order_x = [objects[object_id].center[0] for object_id in scene.protected_order]
    relations += sum(order_x[i] >= order_x[i + 1] - 0.1 for i in range(len(order_x) - 1))
    route_y = float(np.median(np.asarray(scene.route)[:, 1]))
    relations += sum(objects[target_id].center[1] <= route_y + 2.0 for target_id in scene.exhibit_order)
    for target_id in scene.exhibit_order:
        screen = objects.get(f"screen_{target_id}")
        target = objects[target_id]
        if screen is None:
            relations += 1
            continue
        if screen.center[0] >= target.center[0] + 0.2:
            relations += 1
        if np.linalg.norm(np.asarray(screen.center[:2]) - np.asarray(target.center[:2])) > 5.2:
            relations += 1

    valid = collisions == 0 and path_violations == 0 and bounds == 0 and relations == 0
    return valid, collisions, path_violations, bounds, relations


def reveal_order_inversions(
    labels: dict[str, list[int]], profiles: dict[str, list[float]], exhibit_order: list[str]
) -> int:
    expected: dict[str, int] = {}
    actual: dict[str, int] = {}
    fallback = max(len(values) for values in profiles.values()) + 1
    for object_id in exhibit_order:
        show_indices = [i for i, value in enumerate(labels[object_id]) if value == 1]
        expected[object_id] = min(show_indices) if show_indices else fallback
        visible_indices = [i for i, value in enumerate(profiles[object_id]) if value >= TAU_ON]
        actual[object_id] = min(visible_indices) if visible_indices else fallback
    inversions = 0
    for i, first in enumerate(exhibit_order):
        for second in exhibit_order[i + 1 :]:
            expected_sign = expected[first] - expected[second]
            actual_sign = actual[first] - actual[second]
            if expected_sign * actual_sign < 0:
                inversions += 1
    return inversions


def evaluate(scene: Scene, labels: dict[str, list[int]]) -> Evaluation:
    profiles, blockers = compute_visibility(scene)
    missed_terms: list[float] = []
    leakage_terms: list[float] = []
    satisfied: list[float] = []
    missed_count = 0
    leakage_count = 0
    for object_id, target_labels in labels.items():
        for label, value in zip(target_labels, profiles[object_id], strict=True):
            if label == 1:
                violation = max(TAU_ON - value, 0.0) / TAU_ON
                missed_terms.append(violation * violation)
                satisfied.append(float(value >= TAU_ON))
                missed_count += int(value < TAU_ON)
            elif label == -1:
                violation = max(value - TAU_OFF, 0.0) / (1.0 - TAU_OFF)
                leakage_terms.append(violation * violation)
                satisfied.append(float(value <= TAU_OFF))
                leakage_count += int(value > TAU_OFF)
    missed = float(np.mean(missed_terms)) if missed_terms else 0.0
    leakage = float(np.mean(leakage_terms)) if leakage_terms else 0.0
    hard_valid, collisions, path, bounds, relations = hard_constraints(scene)
    return Evaluation(
        schedule_loss=0.5 * (missed + leakage),
        missed_loss=missed,
        leakage_loss=leakage,
        satisfaction=float(np.mean(satisfied)) if satisfied else 1.0,
        missed_violations=missed_count,
        leakage_violations=leakage_count,
        reveal_order_inversions=reveal_order_inversions(labels, profiles, scene.exhibit_order),
        hard_valid=hard_valid,
        collision_count=collisions,
        path_clearance_violations=path,
        bounds_violations=bounds,
        relation_violations=relations,
        visibility=profiles,
        first_blockers=blockers,
    )


def derive_schedule(scene: Scene, minimum_hidden: int = 4, show_window: int = 5) -> dict[str, list[int]] | None:
    profiles, _ = compute_visibility(scene)
    labels: dict[str, list[int]] = {}
    for object_id in scene.exhibit_order:
        profile = profiles[object_id]
        start: int | None = None
        for index in range(minimum_hidden, len(profile) - show_window + 1):
            if all(value >= TAU_ON for value in profile[index : index + show_window]):
                start = index
                break
        if start is None:
            return None
        target_labels = [0] * len(profile)
        hidden_indices = [i for i in range(start) if profile[i] <= TAU_OFF]
        if len(hidden_indices) < minimum_hidden:
            return None
        for index in hidden_indices:
            target_labels[index] = -1
        for index in range(start, start + show_window):
            target_labels[index] = 1
        labels[object_id] = target_labels
    return labels


def make_base_scene(seed: int, exhibit_count: int = 3, route_samples: int = 34) -> tuple[Scene, dict[str, list[int]]]:
    rng = np.random.default_rng(seed)
    room = [0.0, 16.0, 0.0, 10.0]
    xs = np.linspace(0.8, 15.2, route_samples)
    phase = rng.uniform(0.0, 2.0 * math.pi)
    ys = 2.0 + 0.12 * np.sin(xs * 0.65 + phase)
    route = [[float(x), float(y), 1.62] for x, y in zip(xs, ys, strict=True)]

    objects: list[Box] = []
    exhibit_order: list[str] = []
    base_x = np.linspace(5.0, 12.8, exhibit_count)
    for index, nominal_x in enumerate(base_x):
        target_id = f"exhibit_{index}"
        exhibit_order.append(target_id)
        x = float(nominal_x + rng.uniform(-0.18, 0.18))
        y = float(7.55 + rng.uniform(-0.12, 0.12))
        objects.append(
            Box(
                object_id=target_id,
                kind="exhibit",
                center=[x, y, 1.35],
                size=[1.05, 0.42, 2.15],
                yaw=float(rng.uniform(-0.035, 0.035)),
                movable=True,
            )
        )
        objects.append(
            Box(
                object_id=f"screen_{target_id}",
                kind="partition",
                center=[x - 1.35, 5.55 + float(rng.uniform(-0.08, 0.08)), 1.35],
                size=[0.20, 2.50, 2.70],
                yaw=0.0,
                movable=True,
                target_id=target_id,
            )
        )

    scene = Scene(
        scene_id=f"base_{seed}",
        room=room,
        route=route,
        objects=objects,
        exhibit_order=exhibit_order,
        protected_order=list(exhibit_order),
    )
    labels = derive_schedule(scene)
    if labels is None:
        raise RuntimeError(f"unable to derive valid schedule for seed {seed}")
    valid, *_ = hard_constraints(scene)
    if not valid:
        raise RuntimeError(f"generated base scene is not hard-valid for seed {seed}")
    return scene, labels


def apply_action(scene: Scene, action: Action) -> Scene:
    result = scene.clone()
    obj = result.object_map()[action.object_id]
    obj.center[0] += action.dx
    obj.center[1] += action.dy
    obj.yaw = wrap_angle(obj.yaw + action.dyaw)
    return result


def apply_actions(scene: Scene, actions: Iterable[Action]) -> Scene:
    result = scene
    for action in actions:
        result = apply_action(result, action)
    return result


def corrupt_scene(
    base: Scene, labels: dict[str, list[int]], corruption: str, severity: int, seed: int
) -> tuple[Scene, list[Action]]:
    rng = random.Random(seed)
    target_id = rng.choice(base.exhibit_order)
    inverse: list[Action] = []
    corrupted = base.clone()
    magnitude = 2.0 + 0.4 * severity
    if corruption == "premature_reveal":
        object_id = f"screen_{target_id}"
        action = Action(object_id, dy=magnitude)
        corrupted = apply_action(corrupted, action)
        inverse = [Action(object_id, dy=-magnitude)]
    elif corruption == "missed_reveal":
        object_id = f"screen_{target_id}"
        amount = 0.65 + 0.25 * severity
        action = Action(object_id, dx=amount)
        corrupted = apply_action(corrupted, action)
        inverse = [Action(object_id, dx=-amount)]
    elif corruption == "back_facing":
        action = Action(target_id, dyaw=math.pi)
        corrupted = apply_action(corrupted, action)
        inverse = [Action(target_id, dyaw=math.pi)]
    elif corruption == "target_displacement":
        amount = 0.65 + 0.25 * severity
        action = Action(target_id, dx=amount)
        corrupted = apply_action(corrupted, action)
        inverse = [Action(target_id, dx=-amount)]
    elif corruption == "compound":
        other_targets = [item for item in base.exhibit_order if item != target_id]
        second_id = rng.choice(other_targets)
        screen_id = f"screen_{target_id}"
        first = Action(screen_id, dy=magnitude)
        second = Action(second_id, dyaw=math.pi)
        corrupted = apply_actions(corrupted, [first, second])
        inverse = [Action(screen_id, dy=-magnitude), Action(second_id, dyaw=math.pi)]
    else:
        raise ValueError(f"unknown corruption: {corruption}")

    corrupted.scene_id = f"{base.scene_id}_{corruption}_s{severity}_{seed}"
    valid, *_ = hard_constraints(corrupted)
    if not valid:
        raise RuntimeError(f"corruption broke protected constraints: {corrupted.scene_id}")
    base_eval = evaluate(base, labels)
    corrupt_eval = evaluate(corrupted, labels)
    if corrupt_eval.schedule_loss <= base_eval.schedule_loss + 1e-6:
        raise RuntimeError(f"corruption did not worsen schedule: {corrupted.scene_id}")
    return corrupted, inverse


def standard_actions(
    scene: Scene,
    object_ids: Iterable[str],
    translation_steps: Iterable[float] | None = None,
    rotation_degrees: Iterable[float] | None = None,
) -> list[Action]:
    objects = scene.object_map()
    actions: list[Action] = []
    translations = list(
        translation_steps or [0.5, 0.65, 0.9, 1.15, 2.0, 2.4, 2.8]
    )
    rotations = [
        math.radians(value)
        for value in (rotation_degrees or [15, 30, 60, 90, 180])
    ]
    for object_id in sorted(set(object_ids)):
        obj = objects.get(object_id)
        if obj is None or not obj.movable:
            continue
        for amount in translations:
            actions.extend(
                [
                    Action(object_id, dx=amount),
                    Action(object_id, dx=-amount),
                    Action(object_id, dy=amount),
                    Action(object_id, dy=-amount),
                ]
            )
        for amount in rotations:
            actions.extend(
                [Action(object_id, dyaw=amount), Action(object_id, dyaw=-amount)]
            )
    return actions


def implicated_objects(scene: Scene, labels: dict[str, list[int]], evaluation: Evaluation) -> list[str]:
    scores: dict[str, float] = {}
    objects = scene.object_map()
    for target_id, target_labels in labels.items():
        profile = evaluation.visibility[target_id]
        for index, (label, value) in enumerate(zip(target_labels, profile, strict=True)):
            if label == 1 and value < TAU_ON:
                target = objects[target_id]
                camera = np.asarray(scene.route[index], dtype=float)
                _, normal = front_samples(target, scene.surface_grid)
                direction = camera - np.asarray(target.center, dtype=float)
                direction[2] = 0.0
                direction /= max(np.linalg.norm(direction), 1e-9)
                if float(np.dot(normal[:2], direction[:2])) < 0.08:
                    scores[target_id] = scores.get(target_id, 0.0) + 3.0
                for blocker_id, count in evaluation.first_blockers[target_id].get(index, {}).items():
                    if blocker_id != "BACK_FACING":
                        scores[blocker_id] = scores.get(blocker_id, 0.0) + count
            elif label == -1 and value > TAU_OFF:
                scores[target_id] = scores.get(target_id, 0.0) + value
                screen_id = f"screen_{target_id}"
                if screen_id in objects:
                    scores[screen_id] = scores.get(screen_id, 0.0) + 4.0 * value
    ranked = sorted(scores, key=lambda object_id: scores[object_id], reverse=True)
    return ranked[:5]


def edit_metrics(initial: Scene, repaired: Scene) -> tuple[int, float, float, float]:
    initial_objects = initial.object_map()
    repaired_objects = repaired.object_map()
    translation = 0.0
    yaw = 0.0
    count = 0
    diagonal = math.hypot(initial.room[1] - initial.room[0], initial.room[3] - initial.room[2])
    for object_id, before in initial_objects.items():
        after = repaired_objects[object_id]
        delta_translation = float(
            np.linalg.norm(np.asarray(after.center[:2]) - np.asarray(before.center[:2]))
        )
        delta_yaw = abs(wrap_angle(after.yaw - before.yaw))
        if delta_translation > 1e-7 or delta_yaw > 1e-7:
            count += 1
            translation += delta_translation / diagonal
            yaw += delta_yaw / math.pi
    cost = count + translation + 0.35 * yaw
    return count, translation, yaw, cost


def state_key(scene: Scene) -> tuple[tuple[str, float, float, float], ...]:
    return tuple(
        sorted(
            (
                obj.object_id,
                round(obj.center[0], 3),
                round(obj.center[1], 3),
                round(wrap_angle(obj.yaw), 4),
            )
            for obj in scene.objects
        )
    )


def objective_key(
    evaluation: Evaluation,
    initial: Scene,
    candidate: Scene,
    objective: str,
    enforce_hard: bool = True,
    use_sparsity: bool = True,
) -> tuple[float, float, float]:
    _, _, _, cost = edit_metrics(initial, candidate)
    hard = 0.0 if evaluation.hard_valid or not enforce_hard else 1.0
    loss = evaluation.missed_loss if objective == "visibility_only" else evaluation.schedule_loss
    return hard, loss, cost if use_sparsity else 0.0


def package_result(
    method: str,
    initial: Scene,
    scene: Scene,
    evaluation: Evaluation,
    actions: list[Action],
    evaluations: int,
    started: float,
) -> SolverResult:
    count, translation, yaw, cost = edit_metrics(initial, scene)
    net_actions: list[Action] = []
    before_map = initial.object_map()
    after_map = scene.object_map()
    for object_id in sorted(before_map):
        before = before_map[object_id]
        after = after_map[object_id]
        dx = after.center[0] - before.center[0]
        dy = after.center[1] - before.center[1]
        dyaw = wrap_angle(after.yaw - before.yaw)
        if abs(dx) > 1e-7 or abs(dy) > 1e-7 or abs(dyaw) > 1e-7:
            net_actions.append(Action(object_id, dx=dx, dy=dy, dyaw=dyaw))
    return SolverResult(
        method=method,
        scene=scene,
        evaluation=evaluation,
        actions=net_actions,
        edit_count=count,
        translation_cost=translation,
        yaw_cost=yaw,
        edit_cost=cost,
        evaluations=evaluations,
        runtime_seconds=time.perf_counter() - started,
    )


def solve_beam(
    method: str,
    initial: Scene,
    labels: dict[str, list[int]],
    attributed: bool,
    objective: str = "signed",
    max_depth: int = 2,
    beam_width: int = 10,
    max_evaluations: int = 900,
    translation_steps: Iterable[float] | None = None,
    rotation_degrees: Iterable[float] | None = None,
    enforce_hard: bool = True,
    use_sparsity: bool = True,
    object_scope: str | None = None,
) -> SolverResult:
    started = time.perf_counter()
    initial_eval = evaluate(initial, labels)
    evaluations = 1
    frontier: list[tuple[Scene, list[Action], Evaluation]] = [(initial, [], initial_eval)]
    best_scene, best_actions, best_eval = initial, [], initial_eval
    seen = {state_key(initial)}
    for _ in range(max_depth):
        expanded: list[tuple[Scene, list[Action], Evaluation]] = []
        for scene, history, current_eval in frontier:
            implicated = implicated_objects(scene, labels, current_eval)
            if object_scope == "targets":
                object_ids = [
                    object_id
                    for object_id in implicated
                    if scene.object_map()[object_id].kind == "exhibit"
                ]
            elif object_scope == "partitions":
                object_ids = [
                    object_id
                    for object_id in implicated
                    if scene.object_map()[object_id].kind == "partition"
                ]
            elif attributed:
                object_ids = implicated
            else:
                object_ids = [obj.object_id for obj in scene.objects if obj.movable]
            for action in standard_actions(
                scene, object_ids, translation_steps, rotation_degrees
            ):
                if evaluations >= max_evaluations:
                    break
                candidate = apply_action(scene, action)
                key = state_key(candidate)
                if key in seen:
                    continue
                seen.add(key)
                candidate_eval = evaluate(candidate, labels)
                evaluations += 1
                if enforce_hard and not candidate_eval.hard_valid:
                    continue
                candidate_history = history + [action]
                expanded.append((candidate, candidate_history, candidate_eval))
                if objective_key(
                    candidate_eval,
                    initial,
                    candidate,
                    objective,
                    enforce_hard,
                    use_sparsity,
                ) < objective_key(
                    best_eval,
                    initial,
                    best_scene,
                    objective,
                    enforce_hard,
                    use_sparsity,
                ):
                    best_scene, best_actions, best_eval = candidate, candidate_history, candidate_eval
            if evaluations >= max_evaluations:
                break
        if not expanded:
            break
        expanded.sort(
            key=lambda item: objective_key(
                item[2],
                initial,
                item[0],
                objective,
                enforce_hard,
                use_sparsity,
            )
        )
        frontier = expanded[:beam_width]
        active_loss = best_eval.missed_loss if objective == "visibility_only" else best_eval.schedule_loss
        if active_loss <= 1e-12:
            break
    return package_result(
        method, initial, best_scene, best_eval, best_actions, evaluations, started
    )


def solve_random(
    initial: Scene,
    labels: dict[str, list[int]],
    seed: int,
    max_evaluations: int = 900,
    translation_steps: Iterable[float] | None = None,
    rotation_degrees: Iterable[float] | None = None,
) -> SolverResult:
    started = time.perf_counter()
    rng = random.Random(seed)
    all_actions = standard_actions(
        initial,
        [obj.object_id for obj in initial.objects if obj.movable],
        translation_steps,
        rotation_degrees,
    )
    best_scene = initial
    best_eval = evaluate(initial, labels)
    best_actions: list[Action] = []
    evaluations = 1
    while evaluations < max_evaluations:
        depth = 1 if rng.random() < 0.55 else 2
        history = [rng.choice(all_actions) for _ in range(depth)]
        candidate = apply_actions(initial, history)
        candidate_eval = evaluate(candidate, labels)
        evaluations += 1
        if not candidate_eval.hard_valid:
            continue
        if objective_key(candidate_eval, initial, candidate, "signed") < objective_key(
            best_eval, initial, best_scene, "signed"
        ):
            best_scene, best_actions, best_eval = candidate, history, candidate_eval
            if best_eval.schedule_loss <= 1e-12:
                break
    return package_result(
        "random_feasible", initial, best_scene, best_eval, best_actions, evaluations, started
    )


def solve_annealing(
    initial: Scene,
    labels: dict[str, list[int]],
    seed: int,
    max_evaluations: int = 900,
    translation_steps: Iterable[float] | None = None,
    rotation_degrees: Iterable[float] | None = None,
) -> SolverResult:
    started = time.perf_counter()
    rng = random.Random(seed)
    object_ids = [obj.object_id for obj in initial.objects if obj.movable]
    actions = standard_actions(
        initial, object_ids, translation_steps, rotation_degrees
    )
    current_scene = initial
    current_eval = evaluate(initial, labels)
    best_scene, best_eval = current_scene, current_eval
    current_history: list[Action] = []
    best_history: list[Action] = []
    evaluations = 1

    def energy(scene: Scene, result: Evaluation) -> float:
        _, _, _, cost = edit_metrics(initial, scene)
        hard_penalty = 10.0 if not result.hard_valid else 0.0
        return hard_penalty + result.schedule_loss + 0.003 * cost

    for step in range(1, max_evaluations):
        temperature = 0.18 * (0.01 / 0.18) ** (step / max_evaluations)
        action = rng.choice(actions)
        candidate = apply_action(current_scene, action)
        candidate_eval = evaluate(candidate, labels)
        evaluations += 1
        delta = energy(candidate, candidate_eval) - energy(current_scene, current_eval)
        if delta <= 0.0 or rng.random() < math.exp(-delta / max(temperature, 1e-8)):
            current_scene = candidate
            current_eval = candidate_eval
            current_history = current_history + [action]
        if candidate_eval.hard_valid and objective_key(
            candidate_eval, initial, candidate, "signed"
        ) < objective_key(best_eval, initial, best_scene, "signed"):
            best_scene, best_eval = candidate, candidate_eval
            best_history = current_history if current_scene is candidate else current_history + [action]
            if best_eval.schedule_loss <= 1e-12:
                break
    return package_result(
        "simulated_annealing",
        initial,
        best_scene,
        best_eval,
        best_history,
        evaluations,
        started,
    )


def no_repair(initial: Scene, labels: dict[str, list[int]]) -> SolverResult:
    started = time.perf_counter()
    result = evaluate(initial, labels)
    return package_result("no_repair", initial, initial, result, [], 1, started)


def scene_to_dict(scene: Scene) -> dict[str, object]:
    return {
        "scene_id": scene.scene_id,
        "room": scene.room,
        "route": scene.route,
        "objects": [asdict(obj) for obj in scene.objects],
        "exhibit_order": scene.exhibit_order,
        "protected_order": scene.protected_order,
        "surface_grid": scene.surface_grid,
        "path_check_step": scene.path_check_step,
    }


def result_to_row(
    case_id: str,
    corruption: str,
    severity: int,
    seed: int,
    result: SolverResult,
) -> dict[str, object]:
    evaluation = result.evaluation
    return {
        "case_id": case_id,
        "corruption": corruption,
        "severity": severity,
        "seed": seed,
        "method": result.method,
        "schedule_loss": evaluation.schedule_loss,
        "missed_loss": evaluation.missed_loss,
        "leakage_loss": evaluation.leakage_loss,
        "satisfaction": evaluation.satisfaction,
        "missed_violations": evaluation.missed_violations,
        "leakage_violations": evaluation.leakage_violations,
        "reveal_order_inversions": evaluation.reveal_order_inversions,
        "hard_valid": int(evaluation.hard_valid),
        "collision_count": evaluation.collision_count,
        "path_clearance_violations": evaluation.path_clearance_violations,
        "bounds_violations": evaluation.bounds_violations,
        "relation_violations": evaluation.relation_violations,
        "edit_count": result.edit_count,
        "translation_cost": result.translation_cost,
        "yaw_cost": result.yaw_cost,
        "edit_cost": result.edit_cost,
        "evaluations": result.evaluations,
        "runtime_seconds": result.runtime_seconds,
        "actions": [asdict(action) for action in result.actions],
    }
