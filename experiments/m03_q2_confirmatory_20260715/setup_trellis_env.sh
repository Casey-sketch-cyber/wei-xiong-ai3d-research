#!/usr/bin/env bash
set -euo pipefail

ROOT=/root/autodl-tmp/m03_q2_confirmatory_20260715
SOURCE_ENV=/root/autodl-tmp/m03_metric_validity_pilot_20260714/envs/instantmesh
ENV="$ROOT/envs/trellis"
REPO="$ROOT/repos/TRELLIS"

source /root/miniconda3/etc/profile.d/conda.sh
if [[ ! -x "$ENV/bin/python" ]]; then
  conda create --yes --prefix "$ENV" --clone "$SOURCE_ENV"
fi

PY="$ENV/bin/python"
PIP="$ENV/bin/pip"

"$PIP" install --upgrade \
  easydict \
  "huggingface-hub>=0.24,<1.0" \
  pyvista \
  pymeshfix \
  igraph

"$PIP" install --no-deps \
  --index-url https://download.pytorch.org/whl/cu128 \
  xformers==0.0.32.post2

"$PIP" install spconv-cu120==2.3.6

"$PIP" install packaging psutil ninja
"$PIP" install --no-deps \
  "https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.3/flash_attn-2.8.3%2Bcu12torch2.8cxx11abiTRUE-cp310-cp310-linux_x86_64.whl"

"$PIP" install --no-index --no-deps \
  --find-links https://nvidia-kaolin.s3.us-east-2.amazonaws.com/torch-2.8.0_cu128.html \
  kaolin==0.18.0
"$PIP" install warp-lang==1.15.0

source /etc/network_turbo
"$PIP" install --no-deps --no-build-isolation \
  "git+https://github.com/EasternJournalist/utils3d.git@9a4eb15e4021b67b12c460c7057d642626897ec8"
unset http_proxy
unset https_proxy

cd "$REPO"
ATTN_BACKEND=xformers SPARSE_ATTN_BACKEND=xformers SPCONV_ALGO=native \
  "$PY" - <<'PY'
import torch
import torchvision
import xformers
import flash_attn
import spconv
import spconv.pytorch
import kaolin
import utils3d

print("torch", torch.__version__, "cuda", torch.version.cuda)
print("torchvision", torchvision.__version__)
print("xformers", xformers.__version__)
print("flash_attn", flash_attn.__version__)
print("spconv", getattr(spconv, "__version__", "unknown"))
print("kaolin", kaolin.__version__)
print("cuda_available", torch.cuda.is_available())
print("device", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none")
PY

"$PY" -m pip freeze > "$ROOT/trellis_environment_freeze.txt"
