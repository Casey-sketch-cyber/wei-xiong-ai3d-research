"""Optional MAT and PowerPaint v1 checkpoints for the painting pilot."""

import sys
from contextlib import contextmanager
from hashlib import file_digest
from pathlib import Path

import numpy as np

from models import DIFFUSION_GUIDANCE, DIFFUSION_PROMPT, DIFFUSION_STEPS, Inpaint, _mask_input


MAT_SOURCE_REVISION = "d273d891ecdad2e1df106516423a75bc45b2d800"
MAT_WEIGHTS = "Places_512_FullData_G.pth"
# IOPaint release asset 75486776, matched against the published MD5 before hashing.
MAT_SHA256 = "0512e37ebba3986b0355130b2e2c1f95736d0778ac82e91b1212b4b21c231312"
POWERPAINT_SOURCE_REVISION = "5b4c3d52291709fcec2a1870d987da693fd3549c"
POWERPAINT_CHECKPOINT = ("JunhaoZhuang/PowerPaint-v1", "b4174b7cade590ab185dbdcfa09eee2c0f63410b")
SD15_INPAINT = ("stable-diffusion-v1-5/stable-diffusion-inpainting", "8a4288a76071f7280aedbdb3253bdb9e9d5d84bb")
SD15_TOKENIZER = ("stable-diffusion-v1-5/stable-diffusion-v1-5", "451f4fe16113bff5a5d2269ed5ad43b0592e9a14")
POWERPAINT_WEIGHTS = {
    "unet/unet.safetensors": "f7e5f7955115d63c4f42541bcacb7e534cc476755de883aa9bb8a8415c4fc589",
    "text_encoder/text_encoder.safetensors": "16410ea003cd5b3494c7e64b91b6669a40bad2b413e8255510dff8c3db5adfd7",
}


@contextmanager
def _source_checkout(model_dir: Path, name: str, revision: str, entry: str):
    checkout = (model_dir / "sources" / name).resolve()
    if not (checkout / entry).is_file():
        raise FileNotFoundError(f"Check out {name} at {revision} under {checkout}")
    previous_path = sys.path.copy()
    sys.path.insert(0, str(checkout))
    try:
        yield
    finally:
        sys.path[:] = previous_path


def _verify_digest(path: Path, expected: str) -> None:
    with path.open("rb") as stream:
        if file_digest(stream, "sha256").hexdigest() != expected:
            raise ValueError(f"Checkpoint SHA-256 mismatch: {path}")


def _load_mat(device: str, model_dir: Path) -> Inpaint:
    import torch

    checkpoint = model_dir / MAT_WEIGHTS
    _verify_digest(checkpoint, MAT_SHA256)
    with _source_checkout(model_dir, "MAT", MAT_SOURCE_REVISION, "networks/mat.py"):
        from networks.mat import Generator
        from torch_utils.ops import bias_act, upfirdn2d

    # Use upstream PyTorch reference ops to avoid compiling StyleGAN CUDA extensions.
    bias_act._init = lambda: False
    upfirdn2d._init = lambda: False
    target = torch.device(device)
    model = Generator(
        z_dim=512, c_dim=0, w_dim=512, img_resolution=512, img_channels=3,
        synthesis_kwargs={"use_noise": False},
    )
    model.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True), strict=True)
    model = model.to(target).eval()
    label = torch.zeros((1, 0), device=target)

    def run(image: np.ndarray, mask: np.ndarray, seed: int) -> np.ndarray:
        damaged = _mask_input(image, mask)
        if mask.shape != (512, 512):
            raise ValueError("The Places MAT checkpoint requires a 512 by 512 image")
        rgb = torch.from_numpy(damaged).permute(2, 0, 1).unsqueeze(0)
        rgb = rgb.to(device=target, dtype=torch.float32) / 127.5 - 1
        known = torch.from_numpy(~mask)[None, None].to(device=target, dtype=torch.float32)
        generator = torch.Generator(device=target).manual_seed(seed)
        latent = torch.randn((1, model.z_dim), device=target, generator=generator)
        # MAT uses stochastic dropout in its synthesis path even in evaluation mode.
        devices = [target] if target.type == "cuda" else []
        with torch.random.fork_rng(devices=devices), torch.inference_mode():
            torch.random.default_generator.manual_seed(seed)
            if devices:
                with torch.cuda.device(target):
                    torch.cuda.manual_seed(seed)
            output = model(rgb, known, latent, label, truncation_psi=1.0, noise_mode="none")
            if not torch.isfinite(output).all():
                raise RuntimeError("MAT generated non-finite pixels")
            output = (output[0].permute(1, 2, 0) * 127.5 + 127.5).round()
            return output.clamp(0, 255).to(torch.uint8).cpu().numpy()

    return run


def _load_powerpaint(device: str, model_dir: Path, *, safety_checker_enabled: bool = True) -> Inpaint:
    import torch
    from diffusers import UNet2DConditionModel
    from huggingface_hub import snapshot_download
    from PIL import Image
    from safetensors.torch import load_model
    from transformers import CLIPTextConfig, CLIPTextModel

    with _source_checkout(model_dir, "PowerPaint", POWERPAINT_SOURCE_REVISION, "powerpaint/pipelines/pipeline_PowerPaint.py"):
        from powerpaint.pipelines.pipeline_PowerPaint import StableDiffusionInpaintPipeline
        from powerpaint.utils.utils import TokenizerWrapper, add_tokens

    def local_snapshot(checkpoint: tuple[str, str]) -> Path:
        repo_id, revision = checkpoint
        return Path(snapshot_download(repo_id, revision=revision, cache_dir=model_dir / "huggingface", local_files_only=True))

    weights = local_snapshot(POWERPAINT_CHECKPOINT)
    for relative_path, digest in POWERPAINT_WEIGHTS.items():
        _verify_digest(weights / relative_path, digest)
    target = torch.device(device)
    dtype = torch.float16 if target.type == "cuda" else torch.float32
    base = local_snapshot(SD15_INPAINT)
    unet = UNet2DConditionModel.from_config(str(base / "unet")).to(dtype=dtype)
    text_config = CLIPTextConfig.from_pretrained(str(base / "text_encoder"), local_files_only=True)
    text_encoder = CLIPTextModel(text_config).to(dtype=dtype)
    tokenizer = TokenizerWrapper(
        from_pretrained=str(local_snapshot(SD15_TOKENIZER)), subfolder="tokenizer", local_files_only=True,
    )
    add_tokens(
        tokenizer=tokenizer, text_encoder=text_encoder,
        placeholder_tokens=["P_ctxt", "P_shape", "P_obj"], initialize_tokens=["a", "a", "a"],
        num_vectors_per_token=10,
    )
    load_model(unet, str(weights / "unet/unet.safetensors"))
    missing, unexpected = load_model(
        text_encoder, str(weights / "text_encoder/text_encoder.safetensors"), strict=False,
    )
    # The older training version serialized these fixed position IDs. Newer CLIP recreates them.
    unexpected = set(unexpected) - {"text_model.embeddings.position_ids"}
    if missing or unexpected:
        raise ValueError(f"PowerPaint text encoder checkpoint differs: {missing=}, {unexpected=}")
    # The author checkpoints replace both components in full. Load the base's remaining components only.
    pipeline = StableDiffusionInpaintPipeline.from_pretrained(
        str(base), torch_dtype=dtype, variant="fp16", use_safetensors=True, local_files_only=True,
        unet=unet.eval(), text_encoder=text_encoder.eval(),
    )
    if not safety_checker_enabled:
        pipeline.safety_checker = None
    pipeline.tokenizer = tokenizer
    pipeline.to(target)
    pipeline.set_progress_bar_config(disable=True)

    def run(image: np.ndarray, mask: np.ndarray, seed: int) -> np.ndarray:
        damaged = _mask_input(image, mask)
        height, width = mask.shape
        prompt = DIFFUSION_PROMPT + " P_ctxt"
        output = pipeline(
            promptA=prompt, promptB=prompt, negative_promptA="P_obj", negative_promptB="P_obj",
            image=Image.fromarray(damaged), mask=Image.fromarray(mask.astype(np.uint8) * 255),
            height=height, width=width, strength=1.0, num_inference_steps=DIFFUSION_STEPS,
            guidance_scale=DIFFUSION_GUIDANCE, generator=torch.Generator(device=target).manual_seed(seed),
        )
        if any(output.nsfw_content_detected or []):
            raise RuntimeError("The PowerPaint base safety checker withheld the generated image")
        return np.array(output.images[0].convert("RGB"), dtype=np.uint8)

    return run


def load_additional_model(model_name: str, device: str, model_dir: Path) -> Inpaint:
    """Load one optional model and return a callable producing an RGB result."""
    if model_name == "mat":
        return _load_mat(device, model_dir)
    if model_name == "powerpaint":
        return _load_powerpaint(device, model_dir)
    raise ValueError(f"Unknown additional inpainting model: {model_name}")
