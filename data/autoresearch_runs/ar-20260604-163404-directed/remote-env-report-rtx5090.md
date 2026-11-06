# Remote RTX 5090 Environment Report

日期：2026-06-04  
Host：`connect.bjb2.seetacloud.com:13288`  
Workspace：`/root/autodl-tmp/m03`

## Confirmed

- GPU：NVIDIA GeForce RTX 5090
- Driver：580.76.05
- Driver-reported CUDA：13.0
- PyTorch：2.8.0+cu128
- PyTorch CUDA：12.8
- Compute capability：12.0
- VRAM：32607 MiB
- Python：`/root/miniconda3/bin/python`, Python 3.12.3
- Data workspace：`/root/autodl-tmp/m03`
- Data disk：`/root/autodl-tmp`, xfs, 750GB available
- CUDA smoke test：passed, matrix multiplication on GPU completed

## Important Path Notes

Non-interactive SSH shell does not expose `python` or `pip` on PATH. Use:

```bash
/root/miniconda3/bin/python
```

Do not write models or datasets to `/`, because the root overlay is only 30GB. Use:

```bash
/root/autodl-tmp/m03
```

## Created Remote Files

```text
/root/autodl-tmp/m03/README.md
/root/autodl-tmp/m03/scripts/bootstrap_m03.sh
/root/autodl-tmp/m03/scripts/env_probe.py
/root/autodl-tmp/m03/logs/env_probe.json
/root/autodl-tmp/m03/logs/env_probe.txt
```

## Current Caveats

- `nvcc` was not found in PATH. Pure PyTorch inference is fine; custom CUDA extensions may need extra toolchain handling.
- `blender` was not found. Rendering can start with Python/Open3D/trimesh, but Blender-based rendering needs installation later.
- `nvidia-smi` reported 100% GPU util with no process listed, while PyTorch smoke test succeeded. Treat this as a monitoring quirk unless it blocks runtime.
