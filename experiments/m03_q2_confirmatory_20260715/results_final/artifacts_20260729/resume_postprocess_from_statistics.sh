#!/usr/bin/env bash

set -u

ROOT=/root/autodl-tmp/m03_q2_confirmatory_20260715
PYTHON=/root/autodl-tmp/m03/envs/triposr/bin/python
LOG_DIR="$ROOT/logs"
STATUS_FILE="$ROOT/postprocess_stage_status.tsv"

mkdir -p "$LOG_DIR" "$ROOT/analysis" "$ROOT/figures"

export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/root/autodl-tmp/hf
export HUGGINGFACE_HUB_CACHE=/root/autodl-tmp/hf/hub
export HF_HUB_DISABLE_XET=1
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY

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

rm -f "$ROOT/POSTPROCESS_FAILED" "$ROOT/POSTPROCESS_FINISHED"

run_stage confirmatory_statistics_retry "$PYTHON" "$ROOT/analyze_confirmatory.py" \
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
  env PYTHONPATH="$ROOT/repos/TRELLIS:$ROOT" \
  "$ROOT/envs/trellis/bin/python" \
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
