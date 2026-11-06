#!/usr/bin/env bash

set -u

ROOT=/root/autodl-tmp/m03_q2_confirmatory_20260715
LOG_DIR="$ROOT/logs"
STATUS_FILE="$ROOT/inference_stage_status.tsv"

mkdir -p "$LOG_DIR" "$ROOT/inference/trellis"

export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/hf
export HUGGINGFACE_HUB_CACHE=/root/autodl-tmp/hf/hub
export HF_HUB_DISABLE_XET=1
source /etc/network_turbo

started="$(date --iso-8601=seconds)"
log_file="$LOG_DIR/trellis_retry.log"
printf '[%s] START trellis_retry\n' "$started" | tee -a "$LOG_DIR/orchestrator.log"

env PYTHONPATH="$ROOT/repos/TRELLIS" \
    ATTN_BACKEND=flash_attn SPARSE_ATTN_BACKEND=flash_attn SPCONV_ALGO=native \
  "$ROOT/envs/trellis/bin/python" \
  "$ROOT/run_trellis_confirmatory.py" \
  --repo "$ROOT/repos/TRELLIS" \
  --manifest "$ROOT/inference_schedule_stochastic.csv" \
  --work "$ROOT/inference/trellis" >> "$log_file" 2>&1
exit_code=$?

finished="$(date --iso-8601=seconds)"
printf '%s\t%s\t%s\t%s\t%s\n' \
  trellis_retry "$started" "$finished" "$exit_code" "$log_file" >> "$STATUS_FILE"
printf '[%s] END trellis_retry exit=%s\n' "$finished" "$exit_code" \
  | tee -a "$LOG_DIR/orchestrator.log"

unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY

if [[ "$exit_code" -ne 0 ]]; then
  printf 'trellis_retry\t%s\n' "$exit_code" > "$ROOT/POSTPROCESS_FAILED"
  exit "$exit_code"
fi

date --iso-8601=seconds > "$ROOT/INFERENCE_QUEUE_FINISHED"
rm -f "$ROOT/POSTPROCESS_FAILED" "$ROOT/POSTPROCESS_FINISHED"
bash "$ROOT/run_post_inference.sh" >> "$LOG_DIR/postprocess_retry_launcher.log" 2>&1
