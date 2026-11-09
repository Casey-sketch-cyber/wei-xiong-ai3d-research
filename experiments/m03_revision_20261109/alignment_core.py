"""Per-sample pose (and optional scale) alignment for image-to-3D evaluation.

Only numpy and scipy are required, so this module can be unit-tested without
trimesh or a GPU. It aligns a predicted point cloud to a ground-truth point
cloud with a global rotation search followed by symmetric ICP.

Two modes are supported:

* ``"similarity"``: rotation + translation + one uniform scale. This gives the
  shape-only protocol (pose and scale errors removed).
* ``"rigid"``: rotation + translation, scale fixed at 1. The input prediction
  is expected to be already scaled by the frozen model-level calibration, so
  scale error is kept while pose error is removed.

The returned transform maps prediction coordinates to ground-truth
coordinates: ``x_gt = scale * x_pred @ R.T + t``.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

DEFAULT_RANDOM_ROTATIONS = 72
DEFAULT_ROTATION_SEED = 20261109
SCALE_BOUNDS = (0.25, 4.0)


@dataclass
class AlignmentResult:
    mode: str
    rotation: np.ndarray
    scale: float
    translation: np.ndarray
    chamfer_l2_initial: float
    chamfer_l2_aligned: float
    rotation_angle_deg: float
    best_candidate: int
    candidates_evaluated: int
    history: list = field(default_factory=list)

    def as_record(self, prefix: str) -> dict:
        return {
            f"{prefix}mode": self.mode,
            f"{prefix}rotation": np.asarray(self.rotation).round(8).tolist(),
            f"{prefix}scale": float(self.scale),
            f"{prefix}translation": np.asarray(self.translation).round(8).tolist(),
            f"{prefix}chamfer_l2_initial": float(self.chamfer_l2_initial),
            f"{prefix}chamfer_l2_aligned": float(self.chamfer_l2_aligned),
            f"{prefix}rotation_angle_deg": float(self.rotation_angle_deg),
            f"{prefix}best_candidate": int(self.best_candidate),
            f"{prefix}candidates_evaluated": int(self.candidates_evaluated),
        }


def cube_rotations() -> list[np.ndarray]:
    """The 24 proper rotations that map the coordinate axes onto themselves."""
    result = []
    for permutation in itertools.permutations(range(3)):
        for signs in itertools.product((-1.0, 1.0), repeat=3):
            matrix = np.zeros((3, 3), dtype=np.float64)
            for row, column in enumerate(permutation):
                matrix[row, column] = signs[row]
            if np.linalg.det(matrix) > 0:
                result.append(matrix)
    return result


def rotation_candidates(
    random_count: int = DEFAULT_RANDOM_ROTATIONS, seed: int = DEFAULT_ROTATION_SEED
) -> list[np.ndarray]:
    """Identity first, then the 24 cube rotations, then seeded random rotations."""
    candidates = [np.eye(3)]
    for matrix in cube_rotations():
        if not np.allclose(matrix, np.eye(3)):
            candidates.append(matrix)
    if random_count > 0:
        random_rotations = Rotation.random(random_count, random_state=seed).as_matrix()
        candidates.extend(np.asarray(matrix, dtype=np.float64) for matrix in random_rotations)
    return candidates


def symmetric_chamfer_l2(a: np.ndarray, b: np.ndarray, b_tree: cKDTree | None = None) -> float:
    b_tree = b_tree if b_tree is not None else cKDTree(b)
    a_tree = cKDTree(a)
    d_ab, _ = b_tree.query(a, workers=-1)
    d_ba, _ = a_tree.query(b, workers=-1)
    return float(np.mean(d_ab**2) + np.mean(d_ba**2))


def umeyama(src: np.ndarray, dst: np.ndarray, with_scale: bool) -> tuple[np.ndarray, float, np.ndarray]:
    """Least-squares similarity transform with dst ~= s * src @ R.T + t."""
    if src.shape != dst.shape or src.ndim != 2 or src.shape[1] != 3:
        raise ValueError("umeyama expects matching (n, 3) arrays")
    mu_src = src.mean(axis=0)
    mu_dst = dst.mean(axis=0)
    xs = src - mu_src
    xd = dst - mu_dst
    covariance = xd.T @ xs / len(src)
    u, singular, vt = np.linalg.svd(covariance)
    correction = np.eye(3)
    if np.linalg.det(u) * np.linalg.det(vt) < 0:
        correction[2, 2] = -1.0
    rotation = u @ correction @ vt
    if with_scale:
        variance = float(np.mean(np.sum(xs**2, axis=1)))
        scale = float(np.trace(np.diag(singular) @ correction) / variance) if variance > 0 else 1.0
    else:
        scale = 1.0
    translation = mu_dst - scale * rotation @ mu_src
    return rotation, scale, translation


def apply_transform(points: np.ndarray, rotation: np.ndarray, scale: float, translation: np.ndarray) -> np.ndarray:
    return scale * np.asarray(points) @ np.asarray(rotation).T + np.asarray(translation)


def rms_radius(points: np.ndarray) -> float:
    centered = points - points.mean(axis=0)
    return float(np.sqrt(np.mean(np.sum(centered**2, axis=1))))


def icp(
    src: np.ndarray,
    dst: np.ndarray,
    dst_tree: cKDTree,
    rotation: np.ndarray,
    scale: float,
    translation: np.ndarray,
    with_scale: bool,
    iterations: int,
    tolerance: float = 1e-7,
) -> tuple[np.ndarray, float, np.ndarray, float]:
    """Symmetric point-to-point ICP.

    Correspondences are taken in both directions (pred->gt and gt->pred) so a
    free scale cannot shrink the prediction onto a dense part of the target.
    """
    previous = np.inf
    error = np.inf
    lower, upper = SCALE_BOUNDS
    for _ in range(iterations):
        moved = apply_transform(src, rotation, scale, translation)
        moved_tree = cKDTree(moved)
        d_fwd, idx_fwd = dst_tree.query(moved, workers=-1)
        d_bwd, idx_bwd = moved_tree.query(dst, workers=-1)
        error = float(np.mean(d_fwd**2) + np.mean(d_bwd**2))
        if abs(previous - error) < tolerance:
            break
        previous = error
        source_pairs = np.concatenate([src, src[idx_bwd]], axis=0)
        target_pairs = np.concatenate([dst[idx_fwd], dst], axis=0)
        rotation, scale, translation = umeyama(source_pairs, target_pairs, with_scale)
        scale = float(np.clip(scale, lower, upper))
    moved = apply_transform(src, rotation, scale, translation)
    error = symmetric_chamfer_l2(moved, dst, dst_tree)
    return rotation, scale, translation, error


def _subsample(points: np.ndarray, count: int, seed: int) -> np.ndarray:
    if len(points) <= count:
        return points
    rng = np.random.default_rng(seed)
    return points[rng.choice(len(points), size=count, replace=False)]


def rotation_angle_deg(rotation: np.ndarray) -> float:
    cosine = (np.trace(rotation) - 1.0) / 2.0
    return float(np.degrees(np.arccos(np.clip(cosine, -1.0, 1.0))))


def align(
    pred_points: np.ndarray,
    gt_points: np.ndarray,
    mode: str = "similarity",
    random_rotations: int = DEFAULT_RANDOM_ROTATIONS,
    coarse_points: int = 1500,
    coarse_iterations: int = 8,
    refine_top_k: int = 5,
    fine_points: int = 5000,
    fine_iterations: int = 50,
    seed: int = DEFAULT_ROTATION_SEED,
) -> AlignmentResult:
    """Global rotation search + symmetric ICP refinement.

    ``pred_points`` and ``gt_points`` are surface samples in the frames the
    caller wants to compare (for M03: the prediction after the frozen
    model-level calibration, and the view-frame ground truth).
    """
    if mode not in ("similarity", "rigid"):
        raise ValueError(f"Unknown alignment mode: {mode}")
    with_scale = mode == "similarity"
    pred_points = np.asarray(pred_points, dtype=np.float64)
    gt_points = np.asarray(gt_points, dtype=np.float64)

    gt_full_tree = cKDTree(gt_points)
    initial = symmetric_chamfer_l2(pred_points, gt_points, gt_full_tree)

    coarse_pred = _subsample(pred_points, coarse_points, seed)
    coarse_gt = _subsample(gt_points, coarse_points, seed + 1)
    coarse_tree = cKDTree(coarse_gt)
    pred_center = coarse_pred.mean(axis=0)
    gt_center = coarse_gt.mean(axis=0)
    if with_scale:
        radius = rms_radius(coarse_pred)
        scale0 = rms_radius(coarse_gt) / radius if radius > 0 else 1.0
        scale0 = float(np.clip(scale0, *SCALE_BOUNDS))
    else:
        scale0 = 1.0

    candidates = rotation_candidates(random_rotations, seed)
    coarse = []
    for index, rotation0 in enumerate(candidates):
        translation0 = gt_center - scale0 * rotation0 @ pred_center
        rotation, scale, translation, error = icp(
            coarse_pred, coarse_gt, coarse_tree, rotation0, scale0, translation0,
            with_scale, coarse_iterations,
        )
        coarse.append((error, index, rotation, scale, translation))
    coarse.sort(key=lambda item: item[0])

    fine_pred = _subsample(pred_points, fine_points, seed + 2)
    fine_gt = _subsample(gt_points, fine_points, seed + 3)
    fine_tree = cKDTree(fine_gt)
    best = None
    history = []
    for error0, index, rotation, scale, translation in coarse[:refine_top_k]:
        rotation, scale, translation, _ = icp(
            fine_pred, fine_gt, fine_tree, rotation, scale, translation,
            with_scale, fine_iterations,
        )
        full_error = symmetric_chamfer_l2(
            apply_transform(pred_points, rotation, scale, translation), gt_points, gt_full_tree
        )
        history.append({"candidate": index, "coarse_chamfer": error0, "fine_chamfer": full_error})
        if best is None or full_error < best[0]:
            best = (full_error, index, rotation, scale, translation)

    error, index, rotation, scale, translation = best
    return AlignmentResult(
        mode=mode,
        rotation=rotation,
        scale=float(scale),
        translation=translation,
        chamfer_l2_initial=initial,
        chamfer_l2_aligned=float(error),
        rotation_angle_deg=rotation_angle_deg(rotation),
        best_candidate=index,
        candidates_evaluated=len(candidates),
        history=history,
    )
