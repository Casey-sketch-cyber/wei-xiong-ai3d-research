#!/usr/bin/env bash

set -u

ROOT=/root/autodl-tmp/m03_q2_confirmatory_20260715
PYTHON=/root/autodl-tmp/m03/envs/triposr/bin/python
LOG_DIR="$ROOT/logs"
STATUS_FILE="$ROOT/postprocess_stage_status.tsv"

mkdir -p "$LOG_DIR" "$ROOT/evaluation" "$ROOT/analysis" "$ROOT/calibration/trellis"

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
  log_file="$LOG_DIR/post_${stage}.log"
  printf '[%s] START %s\n' "$started" "$stage" | tee -a "$LOG_DIR/postprocess.log"
  "$@" >> "$log_file" 2>&1
  exit_code=$?
  finished="$(date --iso-8601=seconds)"
  printf '%s\t%s\t%s\t%s\t%s\n' \
    "$stage" "$started" "$finished" "$exit_code" "$log_file" >> "$STATUS_FILE"
  printf '[%s] END %s exit=%s\n' "$finished" "$stage" "$exit_code" \
    | tee -a "$LOG_DIR/postprocess.log"
  if [[ "$exit_code" -ne 0 ]]; then
    printf '%s\t%s\n' "$stage" "$exit_code" > "$ROOT/POSTPROCESS_FAILED"
    exit "$exit_code"
  fi
}

while [[ ! -f "$ROOT/INFERENCE_QUEUE_FINISHED" ]]; do
  if [[ -f "$ROOT/inference_queue.pid" ]] \
    && ! kill -0 "$(cat "$ROOT/inference_queue.pid")" 2>/dev/null; then
    echo "Inference queue exited without completion marker" > "$ROOT/POSTPROCESS_FAILED"
    exit 20
  fi
  sleep 60
done

run_stage validate_inference "$PYTHON" "$ROOT/validate_confirmatory_inference.py" \
  --root "$ROOT"

run_stage inference_compute_summary "$PYTHON" "$ROOT/summarize_inference.py" \
  --root "$ROOT" \
  --output "$ROOT/analysis/inference_compute_summary.csv"

run_stage trellis_calibration \
  env PYTHONPATH=/root/autodl-tmp/m03_q2_confirmatory_20260715/repos/TRELLIS \
      ATTN_BACKEND=flash_attn SPARSE_ATTN_BACKEND=flash_attn SPCONV_ALGO=native \
  /root/autodl-tmp/m03_q2_confirmatory_20260715/envs/trellis/bin/python \
  "$ROOT/run_trellis_confirmatory.py" \
  --repo /root/autodl-tmp/m03_q2_confirmatory_20260715/repos/TRELLIS \
  --manifest "$ROOT/calibration_d30_schedule.csv" \
  --work "$ROOT/calibration/trellis"

evaluate_model() {
  local model="$1"
  run_stage "evaluation_${model}" "$PYTHON" "$ROOT/evaluate_confirmatory_model.py" \
    --model "$model" \
    --inference-root "$ROOT/inference" \
    --deterministic-schedule "$ROOT/inference_schedule_deterministic.csv" \
    --stochastic-schedule "$ROOT/inference_schedule_stochastic.csv" \
    --d30-schedule "$ROOT/calibration_d30_schedule.csv" \
    --d30-results-root /root/autodl-tmp/m03_metric_validity_pilot_20260714 \
    --trellis-calibration-root "$ROOT/calibration/trellis" \
    --output-root "$ROOT/evaluation"
}

evaluate_model instantmesh
evaluate_model hunyuan21
evaluate_model trellis

run_stage render_diagnostics \
  env PYTHONPATH=/root/autodl-tmp/m03_q2_confirmatory_20260715/repos/TRELLIS \
      ATTN_BACKEND=flash_attn SPARSE_ATTN_BACKEND=flash_attn SPCONV_ALGO=native \
  /root/autodl-tmp/m03_q2_confirmatory_20260715/envs/trellis/bin/python \
  "$ROOT/render_diagnostics.py" \
  --evaluation-root "$ROOT/evaluation" \
  --output-root "$ROOT/render_diagnostics" \
  --resolution 256 --grid-extent 1.5

run_stage confirmatory_statistics "$PYTHON" "$ROOT/analyze_confirmatory.py" \
  --evaluation-root "$ROOT/evaluation" \
  --render-diagnostics "$ROOT/render_diagnostics/render_diagnostics.csv" \
  --output-root "$ROOT/analysis" \
  --bootstrap-replicates 50000

run_stage exploratory_morphology "$PYTHON" "$ROOT/analyze_morphology.py" \
  --schedule "$ROOT/inference_schedule_deterministic.csv" \
  --analysis-root "$ROOT/analysis"

run_stage confirmatory_figures "$PYTHON" "$ROOT/make_confirmatory_figures.py" \
  --analysis-root "$ROOT/analysis" \
  --output-root "$ROOT/figures"

run_stage representative_cases \
  env PYTHONPATH=/root/autodl-tmp/m03_q2_confirmatory_20260715/repos/TRELLIS:/root/autodl-tmp/m03_q2_confirmatory_20260715 \
  /root/autodl-tmp/m03_q2_confirmatory_20260715/envs/trellis/bin/python \
  "$ROOT/make_representative_cases.py" \
  --analysis-root "$ROOT/analysis" \
  --evaluation-root "$ROOT/evaluation" \
  --output-root "$ROOT/figures" \
  --resolution 512 --grid-extent 1.5

run_stage final_validation "$PYTHON" "$ROOT/validate_confirmatory_results.py" \
  --root "$ROOT"

run_stage artifact_package "$PYTHON" "$ROOT/package_confirmatory_artifacts.py" \
  --root "$ROOT" \
  --output "$ROOT/m03_q2_confirmatory_artifacts.zip"

date --iso-8601=seconds > "$ROOT/POSTPROCESS_FINISHED"
