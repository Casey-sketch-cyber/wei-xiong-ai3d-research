#!/usr/bin/env bash

set -u

ROOT=/root/autodl-tmp/m03_q2_confirmatory_20260715
LOG_DIR="$ROOT/logs"
STATUS_FILE="$ROOT/inference_stage_status.tsv"

mkdir -p "$LOG_DIR" "$ROOT/inference"

export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/hf
export HUGGINGFACE_HUB_CACHE=/root/autodl-tmp/hf/hub
export HF_HUB_DISABLE_XET=1
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY

if [[ ! -f "$STATUS_FILE" ]]; then
  printf 'stage\tstarted_at\tfinished_at\texit_code\tlog\n' > "$STATUS_FILE"
fi

run_stage() {
  local stage="$1"
  shift
  local started finished exit_code log_file
  started="$(date --iso-8601=seconds)"
  log_file="$LOG_DIR/${stage}.log"
  printf '[%s] START %s\n' "$started" "$stage" | tee -a "$LOG_DIR/orchestrator.log"
  nvidia-smi --query-gpu=name,memory.total,memory.used --format=csv,noheader \
    >> "$log_file" 2>&1 || true
  "$@" >> "$log_file" 2>&1
  exit_code=$?
  finished="$(date --iso-8601=seconds)"
  printf '%s\t%s\t%s\t%s\t%s\n' \
    "$stage" "$started" "$finished" "$exit_code" "$log_file" >> "$STATUS_FILE"
  printf '[%s] END %s exit=%s\n' "$finished" "$stage" "$exit_code" \
    | tee -a "$LOG_DIR/orchestrator.log"
  return 0
}

run_stage triposr \
  env PYTHONPATH=/root/autodl-tmp/m03/repos/TripoSR \
  /root/autodl-tmp/m03/envs/triposr/bin/python \
  "$ROOT/run_triposr_confirmatory.py" \
  --repo /root/autodl-tmp/m03/repos/TripoSR \
  --manifest "$ROOT/inference_schedule_deterministic.csv" \
  --work "$ROOT/inference/triposr" \
  --mc-resolution 128 --chunk-size 4096

run_stage instantmesh \
  env PYTHONPATH=/root/autodl-tmp/m03_metric_validity_pilot_20260714/repos/InstantMesh \
  /root/autodl-tmp/m03_metric_validity_pilot_20260714/envs/instantmesh/bin/python \
  "$ROOT/run_instantmesh_confirmatory.py" \
  --repo /root/autodl-tmp/m03_metric_validity_pilot_20260714/repos/InstantMesh \
  --manifest "$ROOT/inference_schedule_stochastic.csv" \
  --work "$ROOT/inference/instantmesh" \
  --stage all --steps 75

run_stage hunyuan21 \
  /root/autodl-tmp/m02_hunyuan21_smoke/conda_env/bin/python \
  "$ROOT/run_hunyuan_confirmatory.py" \
  --repo /root/autodl-tmp/m03_hunyuan21_pilot_20260714/repo/Hunyuan3D-2.1-official \
  --manifest "$ROOT/inference_schedule_stochastic.csv" \
  --work "$ROOT/inference/hunyuan21" \
  --steps 25 --resolution 384

# TRELLIS loads the official DINOv2 image encoder through torch.hub. Keep the
# academic proxy active for this stage so a cold cache remains reproducible.
source /etc/network_turbo
run_stage trellis \
  env PYTHONPATH=/root/autodl-tmp/m03_q2_confirmatory_20260715/repos/TRELLIS \
      ATTN_BACKEND=flash_attn SPARSE_ATTN_BACKEND=flash_attn SPCONV_ALGO=native \
  /root/autodl-tmp/m03_q2_confirmatory_20260715/envs/trellis/bin/python \
  "$ROOT/run_trellis_confirmatory.py" \
  --repo /root/autodl-tmp/m03_q2_confirmatory_20260715/repos/TRELLIS \
  --manifest "$ROOT/inference_schedule_stochastic.csv" \
  --work "$ROOT/inference/trellis"
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY

date --iso-8601=seconds > "$ROOT/INFERENCE_QUEUE_FINISHED"
