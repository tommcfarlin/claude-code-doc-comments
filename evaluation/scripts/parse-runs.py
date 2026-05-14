#!/usr/bin/env python3
"""
Parse stream-json output from each measurement run and extract metrics.

For each run, computes:
  - input_tokens_total: sum of input tokens across all assistant turns
  - input_tokens_to_first_edit: sum up to and including the turn with the
    first Edit/Write/NotebookEdit tool call
  - output_tokens_total
  - discovery_calls_before_first_edit: count of Read/Grep/Glob/Bash tool uses
    that occurred before any Edit/Write/NotebookEdit
  - tool_use_counts: per-tool counts
  - first_edit_turn_index: turn number where the first edit occurred
  - made_an_edit: whether any edit happened at all
  - duration_seconds: from meta file
  - exit_code

Writes results/metrics.json with one entry per run.
"""

import json
from pathlib import Path

EDIT_TOOLS = {"Edit", "Write", "NotebookEdit", "MultiEdit"}
DISCOVERY_TOOLS = {"Read", "Grep", "Glob", "Bash"}

RESULTS_DIR = Path("/Users/tommcfarlin/Projects/02-tm/doc-comments-experiment/results")
RAW_DIR = RESULTS_DIR / "raw"


def parse_run(jsonl_path: Path, meta_path: Path) -> dict:
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

            # The Claude Code stream-json format emits events with `type`
            # describing event kind. Assistant messages with content blocks
            # and usage info are the key signal.
            etype = event.get("type")

            if etype == "assistant":
                turn_index += 1
                msg = event.get("message", {})
                usage = msg.get("usage", {}) or {}
                in_t = (usage.get("input_tokens") or 0) + (usage.get("cache_read_input_tokens") or 0) + (usage.get("cache_creation_input_tokens") or 0)
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
        # If the agent never edited, treat the full run as "discovery"
        input_tokens_to_first_edit = input_tokens_total

    return {
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
    for jsonl in sorted(RAW_DIR.glob("arm-*-run-*.jsonl")):
        meta = jsonl.with_suffix(".meta.json").with_name(jsonl.stem + ".meta.json")
        # The above is messy because .jsonl has a single suffix. Fix:
        meta = jsonl.parent / (jsonl.stem + ".meta.json")
        try:
            r = parse_run(jsonl, meta)
        except Exception as e:
            r = {"file": str(jsonl), "parse_error": str(e)}
        results.append(r)

    out = RESULTS_DIR / "metrics.json"
    out.write_text(json.dumps(results, indent=2))
    print(f"Wrote {out} ({len(results)} runs)")

    # Console summary
    print("\nPer-run summary:")
    print(f"{'arm':<4} {'run':<4} {'in_total':>10} {'in_to_edit':>12} {'disc_pre':>9} {'edit?':>6} {'dur':>6}")
    for r in results:
        print(f"{r.get('arm','?'):<4} {str(r.get('run','?')):<4} "
              f"{r.get('input_tokens_total',0):>10} "
              f"{r.get('input_tokens_to_first_edit',0):>12} "
              f"{r.get('discovery_calls_before_first_edit',0):>9} "
              f"{str(r.get('made_an_edit','?')):>6} "
              f"{r.get('duration_seconds','?')!s:>6}")


if __name__ == "__main__":
    main()
