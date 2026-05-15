#!/usr/bin/env python3
"""
Parse stream-json output from each measurement run and extract metrics.

Scans evaluation/raw-opus/ and evaluation/raw-sonnet/ (whichever exist),
tags each run with its model, writes combined metrics to evaluation/metrics.json.
"""

import json
from pathlib import Path

EDIT_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
DISCOVERY_TOOLS = {"Read", "Grep", "Glob", "Bash"}

SCRIPT_DIR = Path(__file__).resolve().parent
EVAL_DIR = SCRIPT_DIR.parent  # evaluation/
METRICS_FILE = EVAL_DIR / "metrics.json"

MODEL_DIRS = {
    "opus": EVAL_DIR / "raw-opus",
    "sonnet": EVAL_DIR / "raw-sonnet",
}


def parse_run(jsonl_path: Path, meta_path: Path, model: str) -> dict:
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}

    input_tokens_total = 0
    output_tokens_total = 0
    input_tokens_to_first_edit = 0
    discovery_before_edit = 0
    first_edit_turn = None
    tool_counts: dict[str, int] = {}
    turn_index = 0
    edit_seen = False

    with jsonl_path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            etype = event.get("type")
            if etype == "assistant":
                turn_index += 1
                msg = event.get("message", {})
                usage = msg.get("usage", {}) or {}
                in_t = (usage.get("input_tokens") or 0) \
                     + (usage.get("cache_read_input_tokens") or 0) \
                     + (usage.get("cache_creation_input_tokens") or 0)
                out_t = usage.get("output_tokens") or 0
                input_tokens_total += in_t
                output_tokens_total += out_t

                turn_had_edit = False
                for block in msg.get("content", []) or []:
                    if block.get("type") == "tool_use":
                        name = block.get("name", "unknown")
                        tool_counts[name] = tool_counts.get(name, 0) + 1
                        if name in EDIT_TOOLS:
                            turn_had_edit = True
                        elif name in DISCOVERY_TOOLS and not edit_seen:
                            discovery_before_edit += 1

                if turn_had_edit and not edit_seen:
                    edit_seen = True
                    first_edit_turn = turn_index
                    input_tokens_to_first_edit = input_tokens_total

    if not edit_seen:
        input_tokens_to_first_edit = input_tokens_total

    return {
        "model": model,
        **meta,
        "input_tokens_total": input_tokens_total,
        "input_tokens_to_first_edit": input_tokens_to_first_edit,
        "output_tokens_total": output_tokens_total,
        "discovery_calls_before_first_edit": discovery_before_edit,
        "first_edit_turn_index": first_edit_turn,
        "made_an_edit": edit_seen,
        "tool_use_counts": tool_counts,
        "turns_total": turn_index,
    }


def main():
    results = []
    for model, raw_dir in MODEL_DIRS.items():
        if not raw_dir.exists():
            continue
        for jsonl in sorted(raw_dir.glob("arm-*-run-*.jsonl")):
            meta = jsonl.parent / (jsonl.stem + ".meta.json")
            try:
                r = parse_run(jsonl, meta, model)
            except Exception as e:
                r = {"model": model, "file": str(jsonl), "parse_error": str(e)}
            results.append(r)

    METRICS_FILE.write_text(json.dumps(results, indent=2))
    models_seen = sorted({r.get("model") for r in results})
    print(f"Wrote {METRICS_FILE} ({len(results)} runs, models: {models_seen})")

    print(f"\n{'model':<8} {'arm':<4} {'run':<4} {'in_total':>11} {'in_to_edit':>13} {'disc':>5} {'edit?':>6} {'dur':>6}")
    for r in sorted(results, key=lambda x: (x.get("model", ""), x.get("arm", ""), x.get("run", 0))):
        print(f"{r.get('model','?'):<8} {r.get('arm','?'):<4} {str(r.get('run','?')):<4} "
              f"{r.get('input_tokens_total',0):>11,} "
              f"{r.get('input_tokens_to_first_edit',0):>13,} "
              f"{r.get('discovery_calls_before_first_edit',0):>5} "
              f"{str(r.get('made_an_edit','?')):>6} "
              f"{str(r.get('duration_seconds','?')):>5}s")


if __name__ == "__main__":
    main()
