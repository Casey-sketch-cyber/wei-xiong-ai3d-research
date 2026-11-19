"""Native-pixel crops and controlled procedural shapes for the painting pilot."""

import io
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms, ImageOps


SIZE = 512
MASK_FAMILIES = ("crack", "flake", "loss")
MASK_AREAS = (0.01, 0.05)
MASK_MARGIN = 16


def native_crop(path: Path, seed: int) -> tuple[np.ndarray, tuple[int, int]]:
    """Sample a 512×512 RGB crop and its origin in the EXIF-oriented source."""
    rng = np.random.default_rng(seed)
    with Image.open(path) as source:
        image = ImageOps.exif_transpose(source)
        width, height = image.size
        if min(width, height) < SIZE:
            raise ValueError(f"Image is too small for a native {SIZE}-pixel crop: {path}")
        left = int(rng.integers(width - SIZE + 1))
        top = int(rng.integers(height - SIZE + 1))
        crop = image.crop((left, top, left + SIZE, top + SIZE))
        profile = image.info.get("icc_profile")
        if profile:
            crop = ImageCms.profileToProfile(
                crop, io.BytesIO(profile), ImageCms.createProfile("sRGB"), outputMode="RGB"
            )
        else:
            crop = crop.convert("RGB")
        return np.array(crop, dtype=np.uint8), (left, top)


def _crack_score(x: np.ndarray, y: np.ndarray, rng: np.random.Generator, area: float) -> np.ndarray:
    """Distance to a connected, irregular centerline with tapered ends."""
    along = np.linspace(-1, 1, 65)
    span = rng.uniform(130, 155)
    # The larger area uses a longer, more sinuous path to limit its thickness.
    amplitude = rng.uniform(22, 33) if area == 0.01 else rng.uniform(55, 69)
    frequency = math.pi * rng.uniform(2.8, 3.8)
    phase = rng.uniform(0, math.tau)
    jitter = np.interp(along, np.linspace(-1, 1, 13), rng.uniform(-5, 5, 13))
    u = span * along
    wave = frequency * along
    v = amplitude * (np.sin(wave + phase) + 0.19 * np.sin(2 * wave + phase)) + jitter
    angle = rng.uniform(0, math.tau)
    cosine, sine = math.cos(angle), math.sin(angle)
    points = np.column_stack((u * cosine - v * sine, u * sine + v * cosine))
    profile = 1 - 0.45 * along**6

    score = np.full((y.shape[0], x.shape[1]), np.inf)
    for i, ((x0, y0), (x1, y1)) in enumerate(zip(points[:-1], points[1:])):
        dx, dy = x1 - x0, y1 - y0
        px, py = x - x0, y - y0
        t = np.clip((px * dx + py * dy) / (dx**2 + dy**2), 0, 1)
        radius = profile[i] + t * (profile[i + 1] - profile[i])
        distance = ((px - t * dx)**2 + (py - t * dy)**2) / radius**2
        np.minimum(score, distance, out=score)
    return score


def _flake_score(x: np.ndarray, y: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Distance to twenty small irregular patches arranged in five clusters."""
    score = np.full((y.shape[0], x.shape[1]), np.inf)
    angles = rng.uniform(0, math.tau) + np.arange(5) * math.tau / 5
    for angle in angles + rng.uniform(-0.12, 0.12, len(angles)):
        radius = rng.uniform(115, 131)
        cx, cy = radius * math.cos(angle), radius * math.sin(angle)
        offsets = rng.uniform(0, math.tau) + np.arange(4) * math.tau / 4
        for offset in offsets + rng.uniform(-0.16, 0.16, len(offsets)):
            distance = rng.uniform(32, 43)
            dx = x - (cx + distance * math.cos(offset))
            dy = y - (cy + distance * math.sin(offset))
            rotation = rng.uniform(0, math.tau)
            cosine, sine = math.cos(rotation), math.sin(rotation)
            u = (dx * cosine + dy * sine) / rng.uniform(0.82, 1.22)
            v = (dy * cosine - dx * sine) / rng.uniform(0.58, 0.96)
            edge = 1 + 0.16 * np.cos(3 * np.arctan2(v, u) + rng.uniform(0, math.tau))
            np.minimum(score, (u**2 + v**2) / edge**2, out=score)
    return score


def _loss_score(x: np.ndarray, y: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Radial distance to a single broad region with an irregular outline."""
    angle = rng.uniform(0, math.tau)
    u = x * math.cos(angle) + y * math.sin(angle)
    v = (y * math.cos(angle) - x * math.sin(angle)) / rng.uniform(0.77, 1.02)
    vertices = np.linspace(0, math.tau, 18, endpoint=False)
    outline = rng.uniform(0.70, 1.30, len(vertices))
    edge = np.interp(np.arctan2(v, u), vertices, outline, period=math.tau)
    return (u**2 + v**2) / edge**2


def design_mask(family: str, area: float, seed: int) -> np.ndarray:
    """Rasterize a seeded procedural shape with exactly the requested rounded pixel count."""
    if family not in MASK_FAMILIES or area not in MASK_AREAS:
        raise ValueError(f"Unsupported mask family or area: {family}, {area}")

    rng = np.random.default_rng(seed)
    half = SIZE // 2 - MASK_MARGIN
    y, x = np.ogrid[-half:half, -half:half]
    if family == "crack":
        score = _crack_score(x, y, rng, area)
    elif family == "flake":
        score = _flake_score(x, y, rng)
    else:
        score = _loss_score(x, y, rng)

    # Stable ordering resolves discrete ties before translating the raster.
    count = round(area * SIZE**2)
    selected = np.argsort(score, axis=None, kind="stable")[:count]
    rows, columns = np.unravel_index(selected, score.shape)
    width = int(columns.max() - columns.min() + 1)
    height = int(rows.max() - rows.min() + 1)
    left = int(rng.integers(MASK_MARGIN, SIZE - MASK_MARGIN - width + 1))
    top = int(rng.integers(MASK_MARGIN, SIZE - MASK_MARGIN - height + 1))

    mask = np.zeros((SIZE, SIZE), dtype=bool)
    mask[rows - rows.min() + top, columns - columns.min() + left] = True
    return mask
