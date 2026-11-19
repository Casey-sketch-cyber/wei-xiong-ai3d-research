"""Load the pinned inference checkpoints for the painting pilot."""

from collections.abc import Callable
from hashlib import file_digest
from pathlib import Path

import numpy as np


LAMA_URL = "https://github.com/Sanster/models/releases/download/add_big_lama/big-lama.pt"
# GitHub release asset 49462813, matched against IOPaint's MD5 before hashing.
LAMA_SHA256 = "344c77bbcb158f17dd143070d1e789f38a66c04202311ae3a258ef66667a9ea9"
DIFFUSION_CHECKPOINTS = {
    "sdxl": (
        "diffusers/stable-diffusion-xl-1.0-inpainting-0.1",
        "115134f363124c53c7d878647567d04daf26e41e",
    ),
    "sd15": (
        "stable-diffusion-v1-5/stable-diffusion-inpainting",
        "8a4288a76071f7280aedbdb3253bdb9e9d5d84bb",
    ),
}
DIFFUSION_PROMPT = "Restore the missing area of the painting to match the surrounding colors, texture, and brushwork."
DIFFUSION_STEPS = 25
DIFFUSION_GUIDANCE = 7.5

Inpaint = Callable[[np.ndarray, np.ndarray, int], np.ndarray]


def _mask_input(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
    if image.ndim != 3 or image.shape[2] != 3 or image.dtype != np.uint8:
        raise ValueError("Expected an HWC uint8 RGB image")
    if mask.shape != image.shape[:2] or mask.dtype != np.bool_:
        raise ValueError("Expected a boolean mask with the image's height and width")
    if min(mask.shape) < 8 or any(length % 8 for length in mask.shape):
        raise ValueError("Image dimensions must be positive multiples of eight")

    damaged = image.copy()
    damaged[mask] = 0
    return damaged


def _load_lama(device: str, model_dir: Path) -> Inpaint:
    import torch

    checkpoint = model_dir / "big-lama.pt"
    if not checkpoint.is_file():
        raise FileNotFoundError(f"Download {LAMA_URL} to {checkpoint}")
    # This TorchScript archive can execute code on load. Accept only the IOPaint release bytes.
    with checkpoint.open("rb") as stream:
        digest = file_digest(stream, "sha256").hexdigest()
    if digest != LAMA_SHA256:
        raise ValueError(f"IOPaint big-lama.pt checksum mismatch: {checkpoint}")

    target = torch.device(device)
    model = torch.jit.load(str(checkpoint), map_location="cpu").to(target).eval()

    def run(image: np.ndarray, mask: np.ndarray, seed: int) -> np.ndarray:
        damaged = _mask_input(image, mask)
        rgb = torch.from_numpy(damaged).permute(2, 0, 1).unsqueeze(0)
        rgb = rgb.to(device=target, dtype=torch.float32) / 255
        hole = torch.from_numpy(mask.copy())[None, None].to(device=target, dtype=torch.float32)
        # LaMa is deterministic and does not use the seed.
        with torch.inference_mode():
            output = model(rgb, hole)[0].permute(1, 2, 0)
            if not torch.isfinite(output).all():
                raise RuntimeError("LaMa generated non-finite pixels")
            return (255 * output).clamp(0, 255).to(torch.uint8).cpu().numpy()

    return run


def _load_diffusion(
    model_name: str, device: str, model_dir: Path, prompt: str,
    *, strength: float, num_inference_steps: int, guidance_scale: float,
) -> Inpaint:
    import torch
    from diffusers import StableDiffusionInpaintPipeline, StableDiffusionXLInpaintPipeline
    from huggingface_hub import snapshot_download
    from PIL import Image

    repo_id, revision = DIFFUSION_CHECKPOINTS[model_name]
    snapshot = snapshot_download(
        repo_id=repo_id,
        revision=revision,
        cache_dir=model_dir / "huggingface",
        local_files_only=True,
    )
    target = torch.device(device)
    dtype = torch.float16 if target.type == "cuda" else torch.float32
    options = {
        "torch_dtype": dtype,
        "variant": "fp16",
        "use_safetensors": True,
        "local_files_only": True,
    }
    if model_name == "sdxl":
        pipeline = StableDiffusionXLInpaintPipeline.from_pretrained(
            snapshot, add_watermarker=False, **options
        )
    else:
        pipeline = StableDiffusionInpaintPipeline.from_pretrained(snapshot, **options)
    pipeline.to(target)
    pipeline.set_progress_bar_config(disable=True)

    def run(image: np.ndarray, mask: np.ndarray, seed: int) -> np.ndarray:
        damaged = _mask_input(image, mask)
        height, width = mask.shape
        generator = torch.Generator(device=target).manual_seed(seed)
        with torch.inference_mode():
            output = pipeline(
                prompt=prompt,
                image=Image.fromarray(damaged),
                mask_image=Image.fromarray(mask.astype(np.uint8) * 255),
                height=height,
                width=width,
                strength=strength,
                num_inference_steps=num_inference_steps,
                guidance_scale=guidance_scale,
                generator=generator,
                output_type="np",
            )
        if any(getattr(output, "nsfw_content_detected", None) or []):
            raise RuntimeError("The SD 1.5 safety checker withheld the generated image")
        pixels = np.asarray(output.images[0])
        if not np.isfinite(pixels).all():
            raise RuntimeError(f"{model_name} generated non-finite pixels")
        return np.rint(255 * pixels).clip(0, 255).astype(np.uint8)

    return run


def load_model(
    model_name: str, device: str, model_dir: Path, *, prompt: str = DIFFUSION_PROMPT,
    strength: float = 1.0, num_inference_steps: int = DIFFUSION_STEPS, guidance_scale: float = DIFFUSION_GUIDANCE,
) -> Inpaint:
    """Load one model and return a callable producing an uncomposited RGB result."""
    if model_name == "lama":
        return _load_lama(device, model_dir)
    if model_name in DIFFUSION_CHECKPOINTS:
        return _load_diffusion(
            model_name, device, model_dir, prompt,
            strength=strength, num_inference_steps=num_inference_steps, guidance_scale=guidance_scale,
        )
    raise ValueError(f"Unknown inpainting model: {model_name}")
