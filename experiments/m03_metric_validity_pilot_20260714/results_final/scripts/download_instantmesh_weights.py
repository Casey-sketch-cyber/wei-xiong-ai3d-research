from __future__ import annotations

import os
import time

import huggingface_hub.file_download as file_download
from huggingface_hub import hf_hub_download, snapshot_download


original_http_get = file_download.http_get


def patient_http_get(*args, **kwargs):
    kwargs["timeout"] = 120.0
    kwargs["max_retries"] = 8
    return original_http_get(*args, **kwargs)


file_download.http_get = patient_http_get


def retry(label: str, callback, attempts: int = 8):
    for attempt in range(1, attempts + 1):
        try:
            result = callback()
            print("READY", label, result, flush=True)
            return result
        except Exception as error:
            print("RETRY", label, attempt, repr(error), flush=True)
            if attempt == attempts:
                raise
            time.sleep(min(60, attempt * 10))


def main() -> None:
    endpoint = os.environ.get("HF_ENDPOINT", "https://hf-mirror.com")
    cache_dir = os.environ.get("HUGGINGFACE_HUB_CACHE")
    retry(
        "zero123plus-v1.2",
        lambda: snapshot_download(
            "sudo-ai/zero123plus-v1.2",
            endpoint=endpoint,
            cache_dir=cache_dir,
            resume_download=True,
            etag_timeout=120,
            max_workers=1,
        ),
    )
    retry(
        "dino-vitb16",
        lambda: snapshot_download(
            "facebook/dino-vitb16",
            endpoint=endpoint,
            cache_dir=cache_dir,
            resume_download=True,
            etag_timeout=120,
            max_workers=1,
        ),
    )
    for filename in ("diffusion_pytorch_model.bin", "instant_mesh_large.ckpt"):
        retry(
            filename,
            lambda filename=filename: hf_hub_download(
                repo_id="TencentARC/InstantMesh",
                filename=filename,
                repo_type="model",
                endpoint=endpoint,
                cache_dir=cache_dir,
                resume_download=True,
                etag_timeout=120,
            ),
        )


if __name__ == "__main__":
    main()
