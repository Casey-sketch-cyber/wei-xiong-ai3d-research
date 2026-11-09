"""Synthetic tests for alignment_core. Run: python -I -m pytest -q tests  (or python tests/test_alignment_core.py)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import alignment_core as ac  # noqa: E402


def sample_box(rng, center, size, count):
    """Uniform samples on the surface of an axis-aligned box."""
    center = np.asarray(center, float)
    size = np.asarray(size, float)
    areas = np.array([size[1] * size[2], size[0] * size[2], size[0] * size[1]] * 2)
    face = rng.choice(6, size=count, p=areas / areas.sum())
    uv = rng.random((count, 3)) - 0.5
    points = uv * size
    axis = face % 3
    sign = np.where(face < 3, 0.5, -0.5)
    points[np.arange(count), axis] = sign * size[axis]
    return points + center


def asymmetric_shape(rng, count=6000):
    """An L-shaped object with a small tab: no rotational symmetry."""
    parts = [
        sample_box(rng, [0.0, 0.0, 0.0], [0.8, 0.3, 0.4], count // 2),
        sample_box(rng, [0.3, 0.35, 0.0], [0.2, 0.5, 0.4], count // 3),
        sample_box(rng, [-0.3, -0.05, 0.3], [0.15, 0.15, 0.25], count - count // 2 - count // 3),
    ]
    points = np.concatenate(parts)
    return points - points.mean(axis=0)


def rotation_error_deg(estimated, truth):
    return ac.rotation_angle_deg(estimated @ truth.T)


def test_umeyama_exact():
    rng = np.random.default_rng(0)
    src = rng.normal(size=(500, 3))
    rotation = Rotation.random(random_state=1).as_matrix()
    dst = 1.3 * src @ rotation.T + np.array([0.1, -0.2, 0.3])
    r, s, t = ac.umeyama(src, dst, with_scale=True)
    assert np.allclose(r, rotation, atol=1e-8)
    assert abs(s - 1.3) < 1e-8
    assert np.allclose(t, [0.1, -0.2, 0.3], atol=1e-8)


def test_similarity_recovers_pose_and_scale():
    rng = np.random.default_rng(2)
    gt = asymmetric_shape(rng)
    failures = []
    for trial in range(6):
        truth = Rotation.random(random_state=100 + trial).as_matrix()
        scale = float(rng.uniform(0.6, 1.6))
        shift = rng.uniform(-0.1, 0.1, size=3)
        # pred = inverse transform of an independently sampled copy of the shape
        pred_shape = asymmetric_shape(np.random.default_rng(50 + trial))
        pred = ((pred_shape - shift) @ truth) / scale
        pred += rng.normal(scale=0.003, size=pred.shape)
        result = ac.align(pred, gt, mode="similarity")
        err = rotation_error_deg(result.rotation, truth)
        # residual floor comes from two independent surface samplings, not misalignment
        if not (err < 3.0 and abs(result.scale - scale) / scale < 0.03 and result.chamfer_l2_aligned < 5e-4):
            failures.append((trial, err, result.scale, scale, result.chamfer_l2_aligned))
    assert not failures, failures


def test_rigid_keeps_scale_and_reports_scale_error():
    rng = np.random.default_rng(3)
    gt = asymmetric_shape(rng)
    truth = Rotation.from_euler("yx", [35, 31], degrees=True).as_matrix()
    pred = (asymmetric_shape(np.random.default_rng(9)) @ truth) * 1.0
    result = ac.align(pred, gt, mode="rigid")
    assert result.scale == 1.0
    assert rotation_error_deg(result.rotation, truth) < 3.0
    # with a 20% scale error, rigid alignment should leave a clearly larger residual
    scaled = ac.align(pred * 1.2, gt, mode="rigid")
    assert scaled.chamfer_l2_aligned > 3 * result.chamfer_l2_aligned


def test_tilted_view_case_improves_over_identity():
    """Mimics M03: target in a tilted view frame, prediction upright."""
    rng = np.random.default_rng(4)
    upright = asymmetric_shape(rng)
    view = np.array([[0.8192, 0.0, 0.5736], [0.2962, 0.8563, -0.4234], [-0.4912, 0.5165, 0.7010]])
    gt = upright @ view.T
    pred = asymmetric_shape(np.random.default_rng(11))
    result = ac.align(pred, gt, mode="similarity")
    assert result.chamfer_l2_aligned < 0.1 * result.chamfer_l2_initial
    assert abs(result.rotation_angle_deg - ac.rotation_angle_deg(view)) < 3.0


def test_partial_prediction_still_aligns():
    rng = np.random.default_rng(5)
    gt = asymmetric_shape(rng)
    truth = Rotation.random(random_state=7).as_matrix()
    pred_full = asymmetric_shape(np.random.default_rng(12))
    keep = pred_full[:, 0] < 0.3  # remove part of the geometry
    pred = pred_full[keep] @ truth
    result = ac.align(pred, gt, mode="similarity")
    assert rotation_error_deg(result.rotation, truth) < 8.0


def test_candidates_are_rotations():
    for matrix in ac.rotation_candidates():
        assert np.allclose(matrix @ matrix.T, np.eye(3), atol=1e-8)
        assert abs(np.linalg.det(matrix) - 1.0) < 1e-8
    assert len(ac.cube_rotations()) == 24


if __name__ == "__main__":
    for name, function in list(globals().items()):
        if name.startswith("test_") and callable(function):
            function()
            print("PASS", name)
