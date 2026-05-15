#!/usr/bin/env bash
#
# Doc-comments skill evaluation harness.
#
# Drives 9 fresh `claude -p` invocations (3 arms x 3 runs each) against the
# same locked task prompt. Each run starts from a clean checkout of its arm
# branch. Raw stream-json output is written to results/raw/ for later parsing.
#
# Usage:
#   ./run-experiment.sh              # full 9-run sweep
#   ./run-experiment.sh --smoke      # single run on arm-a only (validation)

set -o pipefail

EXPERIMENT_DIR="/Users/tommcfarlin/Projects/02-tm/doc-comments-experiment"
RESULTS_DIR="$EXPERIMENT_DIR/results"
PROMPT_FILE="$EXPERIMENT_DIR/task-prompt.txt"

MODEL="${MODEL:-opus}"
RAW_SUBDIR="${RAW_SUBDIR:-raw}"
TIMEOUT_MIN=20

arm_dir() {
  case "$1" in
    a) echo "$EXPERIMENT_DIR/arm-a-stripped" ;;
    b) echo "$EXPERIMENT_DIR/arm-b-skill" ;;
    c) echo "$EXPERIMENT_DIR/arm-c-original" ;;
    *) echo "UNKNOWN_ARM_$1" ;;
  esac
}

mkdir -p "$RESULTS_DIR/$RAW_SUBDIR"

PROMPT=$(cat "$PROMPT_FILE")
PROMPT_HASH=$(shasum -a 256 "$PROMPT_FILE" | cut -d' ' -f1)
echo "Locked prompt hash: $PROMPT_HASH"
echo "Model: $MODEL"
echo "Timeout per run: ${TIMEOUT_MIN}m"
echo ""

reset_arm() {
  local dir="$1"
  ( cd "$dir" && git restore . 2>/dev/null; git clean -fd >/dev/null 2>&1 ) || true
}

run_one() {
  local arm="$1"
  local run="$2"
  local dir
  dir=$(arm_dir "$arm")
  local out="$RESULTS_DIR/$RAW_SUBDIR/arm-${arm}-run-${run}.jsonl"
  local meta="$RESULTS_DIR/$RAW_SUBDIR/arm-${arm}-run-${run}.meta.json"

  echo "=== arm=$arm run=$run ==="
  echo "  dir: $dir"
  echo "  out: $out"

  reset_arm "$dir"

  local start_ts end_ts duration exit_code
  start_ts=$(date +%s)

  local timeout_sec=$((TIMEOUT_MIN * 60))
  local bench_sys="This is a measured benchmark run. Your goal is to complete the task by reading code and producing the required edit. Do NOT invoke skills. Do NOT ask clarifying questions. Make reasonable engineering assumptions when conventions are not perfectly clear, and proceed directly to the edit. Match the existing code style. Produce a working implementation."

  ( cd "$dir" && perl -e 'alarm shift @ARGV; exec @ARGV or die "exec: $!"' \
      "$timeout_sec" claude -p "$PROMPT" \
      --model "$MODEL" \
      --output-format stream-json \
      --verbose \
      --disable-slash-commands \
      --permission-mode bypassPermissions \
      --disallowedTools "Skill AskUserQuestion WebFetch WebSearch" \
      --append-system-prompt "$bench_sys" \
      > "$out" 2> "${out%.jsonl}.stderr" )
  exit_code=$?

  end_ts=$(date +%s)
  duration=$((end_ts - start_ts))

  python3 -c "
import json, sys
print(json.dumps({
  'arm': '$arm',
  'run': $run,
  'dir': '$dir',
  'duration_seconds': $duration,
  'exit_code': $exit_code,
  'prompt_hash': '$PROMPT_HASH',
  'model': '$MODEL',
  'started_at': $start_ts,
  'ended_at': $end_ts
}, indent=2))
" > "$meta"

  echo "  duration: ${duration}s exit: $exit_code"
  reset_arm "$dir"
  echo ""
}

if [[ "${1:-}" == "--smoke" ]]; then
  echo "SMOKE TEST: single run on arm-a only"
  run_one a 0
  echo "Smoke test complete. Inspect results/raw/arm-a-run-0.jsonl"
  exit 0
fi

RUNS="${RUNS:-1 2}"
echo "Running runs: $RUNS"
echo ""

for arm in a b c; do
  for run in $RUNS; do
    run_one "$arm" "$run"
  done
done

echo "Pass complete (runs: $RUNS)."
echo "Next: python3 parse-runs.py"
