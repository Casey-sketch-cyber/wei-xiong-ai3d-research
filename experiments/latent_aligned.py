"""Apply the same grid-aligned inference mask to each model in a comparison."""

from collections.abc import Callable

import numpy as np
from PIL import Image


def grid_cover(mask: np.ndarray, stride: int = 8) -> np.ndarray:
    """Fill every top-left-aligned block touched by the two-dimensional mask."""
    if not isinstance(mask, np.ndarray) or mask.ndim != 2 or mask.dtype != np.bool_ or not mask.size:
        raise ValueError("Expected a nonempty two-dimensional boolean mask")
    if not isinstance(stride, (int, np.integer)) or stride <= 0:
        raise ValueError("Expected a positive integer grid stride")

    stride = int(stride)
    height, width = mask.shape
    rows, columns = np.arange(height), np.arange(width)
    block_rows = np.logical_or.reduceat(mask, rows[::stride], axis=0)
    blocks = np.logical_or.reduceat(block_rows, columns[::stride], axis=1)
    return blocks[(rows // stride)[:, None], columns // stride]


def aligned_prediction(
    model: Callable[[np.ndarray, np.ndarray, int], np.ndarray],
    reference: np.ndarray,
    mask: np.ndarray,
    seed: int,
    *,
    inference_size: int = 512,
    align: bool = True,
    stride: int = 8,
) -> np.ndarray:
    """Mask in inference space and retain generated pixels only in the original hole."""
    if not isinstance(reference, np.ndarray) or reference.ndim != 3 or reference.dtype != np.uint8:
        raise ValueError("Expected a square HWC uint8 RGB reference image")
    height, width, channels = reference.shape
    if height != width or not height or channels != 3:
        raise ValueError("Expected a square HWC uint8 RGB reference image")
    if not isinstance(mask, np.ndarray) or mask.shape != (height, width) or mask.dtype != np.bool_:
        raise ValueError("Expected a boolean mask matching the reference dimensions")
    if not isinstance(inference_size, (int, np.integer)):
        raise ValueError("Inference size must be an integer upscale of the reference and divisible by eight")
    inference_size = int(inference_size)
    if inference_size < height or inference_size % height or inference_size % 8:
        raise ValueError("Inference size must be an integer upscale of the reference and divisible by eight")

    scale = inference_size // height
    inference_shape = (inference_size, inference_size)
    inference_mask = mask
    if scale > 1:
        inference_mask = np.array(Image.fromarray(mask).resize(inference_shape, Image.Resampling.NEAREST))
    if align:
        inference_mask = grid_cover(inference_mask, stride)

    # Hide every source pixel that contributes to the inference hole before any bicubic filtering.
    hidden_at_reference = inference_mask.reshape(height, scale, width, scale).any(axis=(1, 3))
    context = reference.copy()
    context[hidden_at_reference] = 0
    if scale > 1:
        context = np.array(Image.fromarray(context).resize(inference_shape, Image.Resampling.BICUBIC))
    damaged = context.copy()
    damaged[inference_mask] = 0
    prediction = model(damaged, inference_mask.copy(), seed)
    if (not isinstance(prediction, np.ndarray) or prediction.dtype != np.uint8
            or prediction.shape != (*inference_shape, 3)):
        raise ValueError("Expected a uint8 RGB prediction matching the inference dimensions")

    if scale > 1:
        # Replace generated pixels outside the inference hole before downsampling can mix them in.
        context[inference_mask] = prediction[inference_mask]
        prediction = np.array(Image.fromarray(context).resize((width, height), Image.Resampling.BICUBIC))

    result = reference.copy()
    result[mask] = prediction[mask]
    return result
