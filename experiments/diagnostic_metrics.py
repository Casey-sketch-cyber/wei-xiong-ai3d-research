"""Full-reference color and texture diagnostics for saved painting repairs."""

import argparse
import hashlib
import json
import os
from importlib.metadata import distribution, version
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np
from PIL import Image

DISTS_VERSION = "0.1"
DISTS_SOURCE_SHA256 = "da9162307ae51bc58ffe259e7e778973e8586286652d36c3e9885e94bc269da8"
DISTS_WEIGHTS_SHA256 = "f5e65c96230b7f6ca995691647d482237e4cab8a50c5c4a5784f219ef0748218"
VGG_CHECKPOINT = "vgg16-397923af.pth"
VGG_URL = f"https://download.pytorch.org/models/{VGG_CHECKPOINT}"
VGG_SHA256 = "397923af8e79cdbb6a7127f12361acd7a2f83e06b05044ddf496e83de57a5bf0"
ROI_CONTEXT_PX = 8
METRICS = ("masked_ciede2000", "masked_mean_lab_ciede2000", "local_dists")


def require_hash(path: Path, expected: str) -> None:
    with path.open("rb") as stream:
        actual = hashlib.file_digest(stream, "sha256").hexdigest()
    if actual != expected:
        raise ValueError(f"Unexpected SHA-256 for {path}: {actual}")


def prepare_vgg(torch) -> None:
    if not (os.environ.get("TORCH_HOME") or os.environ.get("XDG_CACHE_HOME")):
        raise RuntimeError("Set TORCH_HOME or XDG_CACHE_HOME to a data-disk cache for DISTS.")
    checkpoint = Path(torch.hub.get_dir()) / "checkpoints" / VGG_CHECKPOINT
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    if not checkpoint.is_file():
        torch.hub.download_url_to_file(VGG_URL, str(checkpoint), hash_prefix=VGG_SHA256)
    require_hash(checkpoint, VGG_SHA256)


class DiagnosticMetrics:
    """Mean masked color error, mean-Lab color shift, and ROI DISTS.

    DISTS compares the unmodified matching rectangles including the mask, any
    pixels inside its bounding box, and up to eight pixels of context. It is a
    local structure/texture distance to the reference, not a hallucination test.
    Comparing the mean Lab values measures net color displacement. Local shifts
    in different directions may cancel before that comparison.
    """

    def __init__(self, device: str):
        import torch
        from skimage.color import deltaE_ciede2000, rgb2lab

        package = distribution("DISTS-pytorch")
        if package.version != DISTS_VERSION:
            raise ValueError(f"Use DISTS-pytorch=={DISTS_VERSION}, got {package.version}")
        package_dir = Path(package.locate_file("DISTS_pytorch"))
        weights_file = package_dir / "weights.pt"
        require_hash(package_dir / "DISTS_pt.py", DISTS_SOURCE_SHA256)
        require_hash(weights_file, DISTS_WEIGHTS_SHA256)
        prepare_vgg(torch)

        from DISTS_pytorch import DISTS

        # The upstream class reads a sys.prefix-relative file by default.
        # Use the equivalent verified weights bundled with the pinned wheel.
        metric = DISTS(load_weights=False)
        weights = torch.load(weights_file, map_location="cpu", weights_only=True)
        with torch.no_grad():
            metric.alpha.copy_(weights["alpha"])
            metric.beta.copy_(weights["beta"])
        self._dists = metric.to(device).eval()
        self._device = device
        self._torch = torch
        self._to_lab = rgb2lab
        self._delta_e = deltaE_ciede2000

    def score(self, reference: np.ndarray, restored: np.ndarray, mask: np.ndarray) -> dict[str, float]:
        if reference.dtype != np.uint8 or restored.dtype != np.uint8:
            raise ValueError("Reference and restoration must both be uint8 sRGB images.")
        if reference.ndim != 3 or reference.shape[-1] != 3 or restored.shape != reference.shape:
            raise ValueError("Reference and restoration must have matching H×W×3 shape.")
        if mask.dtype != np.bool_ or mask.shape != reference.shape[:2] or not mask.any():
            raise ValueError("Expected a nonempty boolean mask matching the image height and width.")

        ref_lab = self._to_lab(reference[mask], illuminant="D65", observer="2")
        out_lab = self._to_lab(restored[mask], illuminant="D65", observer="2")
        pixel_error = self._delta_e(ref_lab, out_lab).mean()
        color_shift = self._delta_e(ref_lab.mean(0, keepdims=True), out_lab.mean(0, keepdims=True))[0]

        y, x = mask.nonzero()
        top = max(int(y.min()) - ROI_CONTEXT_PX, 0)
        bottom = min(int(y.max()) + 1 + ROI_CONTEXT_PX, mask.shape[0])
        left = max(int(x.min()) - ROI_CONTEXT_PX, 0)
        right = min(int(x.max()) + 1 + ROI_CONTEXT_PX, mask.shape[1])

        def image_tensor(image):
            crop = np.ascontiguousarray(image[top:bottom, left:right])
            return self._torch.from_numpy(crop).permute(2, 0, 1).unsqueeze(0).to(
                device=self._device, dtype=self._torch.float32
            ).contiguous() / 255.0

        with self._torch.inference_mode():
            distance = self._dists(image_tensor(reference), image_tensor(restored)).item()
        values = (float(pixel_error), float(color_shift), float(distance))
        if not np.isfinite(values).all():
            raise ValueError("Non-finite diagnostic metric.")
        return dict(zip(METRICS, values, strict=True))


def score_saved_run(run_dir: Path, device: str) -> dict:
    from run_pilot import read_json, sha256

    prepared = run_dir / "prepared.json"
    plan = read_json(prepared)
    cases = plan["cases"]
    by_case = {case["case_id"]: [] for case in cases}
    if len(by_case) != len(cases):
        raise ValueError("The prepared plan contains duplicate case IDs.")
    score_files = sorted((run_dir / "scores").glob("*.json"))
    png_files = {path.stem: path for path in (run_dir / "restored").glob("*.png")}
    if not score_files or {path.stem for path in score_files} != png_files.keys():
        raise ValueError("Saved scores and restored PNGs must form a nonempty matched set.")
    for score_file in score_files:
        saved = read_json(score_file)
        case_id, model, seed = (saved[key] for key in ("case_id", "model", "seed"))
        if case_id not in by_case or score_file.stem != f"{case_id}__{model}__s{seed}":
            raise ValueError(f"Saved score identity mismatch for {score_file.name}")
        by_case[case_id].append((saved, png_files[score_file.stem]))

    metrics = DiagnosticMetrics(device)
    rows = []
    for index, case in enumerate(cases, start=1):
        case_id = case["case_id"]
        if not by_case[case_id]:
            continue
        original = run_dir / "originals" / f"{case_id}.png"
        mask_file = run_dir / "masks" / case["mask_file"]
        if "crop_sha256" in case:
            require_hash(original, case["crop_sha256"])
        if "mask_sha256" in case:
            require_hash(mask_file, case["mask_sha256"])
        with Image.open(original) as image:
            reference = np.array(image)
        with Image.open(mask_file) as image:
            mask = np.array(image) > 0
        identity = {key: case[key] for key in ("case_id", "artwork_id", "stratum")}
        for saved, restored in by_case[case_id]:
            if any(saved.get(key, value) != value for key, value in identity.items()):
                raise ValueError(f"Prepared and saved identities differ for {restored.name}")
            with Image.open(restored) as image:
                scores = metrics.score(reference, np.array(image), mask)
            rows.append({
                **identity,
                **{key: saved[key] for key in ("model", "seed", "mask_type", "masked_mae", "local_lpips") if key in saved},
                "restored_sha256": sha256(restored),
                **scores,
            })
        if index % 15 == 0 or index == len(cases):
            print(f"Diagnostic scoring: {index}/{len(cases)} prepared cases", flush=True)

    return {
        "protocol": "reconstruction-diagnostics-v1",
        "source_protocol": plan.get("protocol"),
        "source_arm": plan.get("arm"),
        "reference_plan_sha256": plan.get("reference_plan_sha256"),
        "inference_settings": plan.get("inference_settings"),
        "input_aperture": plan.get("input_aperture"),
        "init_prefill": plan.get("init_prefill"),
        "safety_checker": plan.get("safety_checker"),
        "prepared_sha256": sha256(prepared),
        "cases_without_outputs": [case_id for case_id, outputs in by_case.items() if not outputs],
        "dists_package": f"DISTS-pytorch=={DISTS_VERSION}",
        "dists_source_sha256": DISTS_SOURCE_SHA256,
        "dists_weights_sha256": DISTS_WEIGHTS_SHA256,
        "vgg_checkpoint_sha256": VGG_SHA256,
        "dists_roi_context_px": ROI_CONTEXT_PX,
        "scikit_image_version": version("scikit-image"),
        "color_space": "sRGB to CIE Lab, D65, CIE 1931 2-degree observer",
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path, help="Existing prepared run with saved repairs and scores")
    parser.add_argument("--output", required=True, type=Path, help="New JSON outside the input run")
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    output = args.output.resolve()
    if output == run_dir or output.is_relative_to(run_dir) or output.exists():
        parser.error("--output must name a new file outside --run-dir")

    report = score_saved_run(run_dir, args.device)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = NamedTemporaryFile(dir=output.parent, delete=False, mode="w", encoding="utf-8")
    staged = Path(temporary.name)
    try:
        with temporary:
            json.dump(report, temporary, indent=2, ensure_ascii=False, allow_nan=False)
            temporary.write("\n")
        # Publish complete bytes without overwriting an existing artifact.
        os.link(staged, output)
    finally:
        staged.unlink(missing_ok=True)
    print(f"Wrote {len(report['rows'])} scored outputs to {output}", flush=True)


if __name__ == "__main__":
    main()
