# Doc Comments

> **Status: hypothesis falsified, but not for the reason originally reported.** This skill was built on the premise that structured doc comments reduce the input-token cost an agent pays when working in a codebase. A controlled experiment across two models (60 runs total, N=10 per cell) found a more specific picture: doc comments *can* reduce agent cost — but only when they're well-written, and only for less-capable models. **This skill's generated comments don't qualify.**

## Headline (N=10 per cell)

Median input tokens to first edit, lower = better for the hypothesis:

| Model | Arm A (stripped) | Arm B (skill) | Arm C (human) | Δ B vs A | Δ C vs A |
|---|---|---|---|---|---|
| **Opus 4.7** | 405,939 | 403,236 | 438,718 | **−0.7%** | **+8.1%** |
| **Sonnet 4.6** | 557,902 | 700,377 | 445,117 | **+25.5%** | **−20.2%** |

Full report: [`evaluation/report.html`](evaluation/report.html). Pre-registered Sonnet hypothesis (committed before Sonnet runs): [`evaluation/preregistration-sonnet.md`](evaluation/preregistration-sonnet.md).

## What the data says

**On Opus**, doc comments have approximately no effect on agent token cost. The skill is statistically indistinguishable from stripped code; human docs sit slightly higher but within variance.

**On Sonnet**, doc comment *quality* matters a lot. Human-written docs reduce token cost by 20% — a real, substantial effect. Skill-generated docs *increase* token cost by 25% — making the agent do more work, not less.

**The skill is never better than human docs across the tested capability range.** It's roughly neutral on Opus and actively harmful on Sonnet. The premise that this skill produces agent-useful doc comments is not supported.

## A correction worth being explicit about

An earlier version of this README reported Opus deltas of **+14.7%** (skill) and **+19.5%** (human) — both meaningfully positive, suggesting docs increased Opus's token cost. Those numbers came from N=5 per arm. The N=10 numbers above (−0.7%, +8.1%) are the canonical result; the N=5 numbers were noise-dominated. The Opus conclusion *changed* between N=5 and N=10. This is itself a finding worth flagging: small-sample variance in LLM benchmarks can produce sizeable misleading deltas.

The Sonnet numbers were collected at N=10 from the start and are stable.

## The mechanism (it's about how the agent reads)

Median discovery tool calls (Read / Grep / Glob / Bash) before the agent's first edit:

| Model | Arm A | Arm B | Arm C |
|---|---|---|---|
| **Opus** | 5 | 5 | 6 |
| **Sonnet** | 14.5 | 17.5 | 8.5 |

Opus reads roughly the same number of files regardless of doc state — its reading strategy is fixed. Sonnet's reading strategy is doc-quality-dependent: trusted docs reduce reading dramatically; untrusted or misleading docs push the agent toward *more* verification, not less.

That's the mechanism. Doc comments work for agents when they're good enough to trust. The skill doesn't produce docs the agent trusts.

## What this does not prove

That doc comments are useless. Sonnet + human docs is a clean refutation of that. Good docs help less-capable agents — substantially.

That this skill could never work. Different prompting, different formats, or different quality bars might produce docs that pass the trust threshold. We didn't test that. We tested the skill as written.

That a more capable future model will behave the same way. Capability-dependent effects suggest the picture will keep shifting.

## What this does show

On the tested fixture, task, and model pair, **this skill's output is worse than no docs at all on the smaller model, and indistinguishable from no docs on the larger one**. There is no condition we tested where running this skill made things better. If you were going to install it to make agentic workflows cheaper, the data says: don't.

## If you want to use the skill anyway

It still does what it says — generates structured doc comments for PHP, Swift, JavaScript, and TypeScript. If you value the comments for human readers, or want to test whether the result holds in *your* codebase, install it:

```bash
git clone https://github.com/tommcfarlin/claude-code-doc-comments.git ~/.claude/skills/doc-comments
```

Then `/doc-comments` is available in any Claude Code session. See [`SKILL.md`](SKILL.md) for behavior and flags.

## Reproducing

Everything needed to reproduce is in [`evaluation/`](evaluation/):

- 60 raw stream-json captures (`evaluation/raw-opus/`, `evaluation/raw-sonnet/`)
- The strip script, harness, parser, and report builder (`evaluation/scripts/`)
- The locked task prompt (`evaluation/task-prompt.txt`, SHA-256 verifiable)
- The pre-registration document committed before any Sonnet data existed

See [`evaluation/README.md`](evaluation/README.md) for step-by-step reproduction.

If you re-run on a different codebase, task, or language, share the result. The methodology generalizes; the numbers don't.
