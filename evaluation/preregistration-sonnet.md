# Pre-registration — Sonnet 4.6 follow-up

**Filed:** 2026-05-15, before any Sonnet measurement run.
**Author:** Tom McFarlin
**Status:** Pre-data. This document is committed before Sonnet data exists, so no observed result can shape what was hypothesized.

## Background

The published Opus 4.7 evaluation in this repo found that doc comments **increased** input-token cost by 14.7% (skill-generated) and 19.5% (human-written) compared to a stripped baseline. The hypothesis that doc comments reduce agent discovery cost was not supported on the tested fixture, task, and model combination.

The Opus result leaves an open question: was the absence of benefit specific to a high-capability model that can infer contracts directly from signatures, or does it hold across capability tiers?

## Hypothesis under test (Sonnet 4.6)

**H1:** On the same fixture and locked task prompt, Sonnet 4.6 will show a *reduction* in median input tokens to first edit in Arms B (skill-generated docs) and C (human-written docs) compared to Arm A (stripped). The expected mechanism: a less-capable model is less able to infer a function's contract from signatures alone, so the explicit contract information in doc comments has more discovery value.

**Quantitative threshold for "supported":** Arm B median *and* Arm C median are at least 10% below Arm A median, measured in input tokens to first edit.

## Pre-stated interpretations

| Outcome on Sonnet | Interpretation |
|---|---|
| Both B and C show ≥10% reduction vs. A | H1 supported. Skill has narrow utility for less-capable models. The cross-tier comparison reveals capability-dependent skill value. |
| Neither B nor C shows ≥10% reduction | H1 not supported. Falsification extends across capability tiers. The skill's premise is wrong across the tested capability range. |
| Mixed: one shows reduction, the other does not | Partial support. Investigate whether the difference between skill-generated and human docs explains the divergence. |
| Sonnet shows the same direction as Opus (docs increase token cost) | Stronger falsification than either single-model result. |

**Critically:** we will not retroactively reframe the skill's purpose to fit whichever result we observe. The published Opus headline remains the published Opus headline. The Sonnet result is reported alongside, with the comparison framing chosen *from this document*, not from inspection of the Sonnet data.

## Experimental conditions (locked)

- **Fixture:** `tommcfarlin/where-can-i-watch-ios` at commit `8cd0d54` (same as Opus run).
- **Arm states:** identical to Opus run. Verified by SHA on the experiment branches:
  - Arm A: `1d5920d` — stripped baseline
  - Arm B: `75f7f81` — skill-generated docs (bit-identical to Opus Arm B)
  - Arm C: `8cd0d54` — pristine, human-written docs
- **Task prompt:** identical, SHA-256 `a8208e04692fbadd2b25150394e64382ac2754cb78144a7798dd548d69ce7d75`.
- **Harness:** same `run-experiment.sh`, only `MODEL` value changes from `opus` to `sonnet`.
- **CLI flags:** `--disable-slash-commands`, `--disallowedTools "Skill AskUserQuestion WebFetch WebSearch"`, `--permission-mode bypassPermissions`, plus a benchmark-focused appended system prompt — all identical to Opus run.
- **Working tree reset** between runs (`git restore .; git clean -fd`).

## N

- Sonnet: **N = 10 per arm** (30 runs total).
- Opus: existing N = 5 per arm. We will attempt to backfill Opus to N = 10 for balance if budget permits; if not, the comparison is reported as N=5 vs. N=10 with the asymmetry noted.

## Confounds we acknowledge up front

1. **Temporal separation.** Opus runs occurred on 2026-05-14; Sonnet runs occur on 2026-05-15. Anthropic infrastructure load and cache state may differ between days. This is unavoidable without re-running Opus.
2. **Cross-model comparison is observational, not randomized.** We are not interleaving Opus and Sonnet runs within the same session.
3. **N=10 is still small.** Effect sizes will be reported but should be treated as directional.

## Metrics (locked, same as Opus)

Primary metric: **input tokens to first edit** (median per arm). Includes `input_tokens` + `cache_read_input_tokens` + `cache_creation_input_tokens` summed across all assistant turns up to and including the turn containing the first Edit / Write / MultiEdit / NotebookEdit tool call.

Secondary: discovery tool calls (Read/Grep/Glob/Bash) before first edit, wall-clock duration, output tokens, total turns, whether the agent reached an edit at all.

## Commit discipline

This document is committed and pushed to the public repo before the first Sonnet run executes. Any change to the hypothesis, threshold, or interpretation table after Sonnet data exists must be made as a *new commit* clearly marked as a post-hoc revision, not as an edit to this file.
