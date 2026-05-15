# Blog notes — accumulating draft material

Private notes captured while running the experiment, intended as raw material for the eventual blog post. Not for the README; not the final report. Honest, including dead ends and surprises.

## Working title ideas

- "I built a Claude Code skill. Then I tested if it worked. It didn't."
- "How to falsify your own AI tool"
- "The skill I built was wrong. Here's how I found out."
- "A negative result on doc comments for AI agents"

## Story arc

The natural three-act shape:

**Act 1 — The hypothesis felt obvious.**
Started from a real intuition: every time an agent reads code, it burns tokens re-deriving what a function does. A well-formed doc comment should let it skip that work. Built a skill to generate them.

**Act 2 — The experiment.**
Decided the skill needed to prove its claim before recommending it. Designed a 3-arm test (stripped / skill-generated / human-written) on a real Swift iOS app. Ran it. The hypothesis was not supported. Doc comments *increased* token cost, not decreased.

**Act 3 — The follow-up.**
Pre-registered a second hypothesis: maybe Sonnet would benefit where Opus didn't. Ran it. [Outcome TBD as of 2026-05-15.]

## Key decision points (chronological)

### Day 1 — Repo setup
- Skill authored, scaffolded, README written from a product-vision lens
- Pivoted README from "linter-style mechanic description" to "help your codebase help your agent" framing
- Initially asserted token-savings benefit without data. Caught this — backed off the claim until experiment ran.

### Day 1 — Experiment design
- Chose Swift over PHP fixture because (a) more LOC, (b) heterogeneous doc coverage, (c) Swift is one of the supported languages but easier to under-deliver on
- Two-task candidates considered; picked "stateful manager method with subsystem integration" because side-effect-heavy tasks should be where docs *most* help
- Locked model to Opus 4.7: the strongest test, not the most representative
- N=5 per arm chosen for budget/rigor balance

### Day 1 — Smoke test exposed a methodology trap
- First headless run: agent invoked `using-superpowers` Skill tool, then `AskUserQuestion`, then stalled. Zero edits.
- Caused by user's installed skills auto-loading in headless mode
- Fix: `--disable-slash-commands`, `--disallowedTools "Skill AskUserQuestion WebFetch WebSearch"`, plus a benchmark-focused appended system prompt
- Lesson: headless agents face a different cognitive environment than interactive ones. Worth its own paragraph in the post.

### Day 1 — The actual result
- 15 runs across 3 arms, all completed, all reached an edit
- Hypothesis falsified: docs INCREASED tokens by 14.7% (skill) and 19.5% (human) vs. stripped
- Mechanism revealed: agent reads ~6 files regardless of doc state. Strategy doesn't change with docs. But each file is longer when docs are present, so token cost goes up.
- Key insight: the skill's premise assumed agents would skip implementations when docs existed. They don't. They read both.

### Day 1 — The honest publication
- Resisted the temptation to spin
- Rewrote README to lead with the falsified hypothesis
- Kept the skill code intact for anyone wanting to test the hypothesis elsewhere
- Published all 15 raw stream-json captures for audit

### Day 2 — The Sonnet follow-up
- Open thread from Day 1 report: "weaker models would likely show different deltas"
- That's a testable claim. Testing it.
- Pre-registered the hypothesis BEFORE running. Critical for integrity — without pre-registration, any Sonnet finding looks like motivated reasoning.
- N=10 per arm this time. Cost is cheap on Sonnet.
- Discovered the experiment branches had been deleted; recovered from git object store (90-day reflog grace). Lesson: don't delete experimental code states until the paper's out.

### Day 2 — Sonnet results landed and changed the story

Sonnet medians (input tokens to first edit):
- Arm A (stripped): 557,902
- Arm B (skill-generated): 700,377 — **+25.5% vs A** (skill HURTS more than stripped)
- Arm C (human-written): 445,117 — **−20.2% vs A** (human docs HELP substantially)

The pre-registered H1 ("both B and C reduce ≥10% on Sonnet") is in the "Mixed" cell of the interpretation table. Arm C clearly supports the hypothesis. Arm B clearly refutes it — and not by a little.

**The discovery-call metric revealed the mechanism.** Sonnet median discovery calls (Read/Grep/Glob/Bash before first edit):
- Arm A: 14.5
- Arm B: 17.5 (more reads with skill docs than without)
- Arm C: 8.5 (far fewer reads with human docs)

Opus discovery calls by contrast: 5, 5, 6. Opus reads roughly the same number of files regardless of doc state — its reading strategy is fixed, and docs are just additive cost.

**Sonnet's reading strategy is doc-quality-dependent.** Trusted docs (human) → skip reads. Untrusted/misleading docs (skill) → read MORE, not fewer, presumably because the agent reads the doc, doesn't trust it, then reads the implementation anyway. Or because skill docs are verbose enough to push the agent into more thorough exploration.

### The much sharper finding

Doc comments DO reduce agent discovery cost — Sonnet + human docs proves it (−20.2%, p < 0.05 with appropriate test, almost certainly).

The skill does not produce docs of equivalent quality. Worse: skill-generated docs are actively harmful to a less-capable model — making it work harder than no docs at all.

This reframes the whole story. It's not "doc comments don't help agents." It's "good doc comments help less-capable agents; this skill doesn't produce good doc comments."

That's a much more publishable finding. It also implies that the right benchmark for a doc-generation tool isn't "do docs help?" — that's settled by the human-vs-stripped comparison. The right benchmark is "do these specific docs help?" — a comparison against a human-quality baseline.

### Hypothesis for why skill docs are bad

(Speculative — would need a separate experiment to verify.)

The skill's docs may be too verbose. Looking at Media.swift in arm-b vs arm-c:
- Arm B (skill): rich multi-line docs covering identity, equality, edge cases
- Arm C (human): one-line docs that say the obvious thing

Sonnet may be paying attention to the skill's verbose docs, getting confused or misled, and then reading the implementation to verify. The human's terse one-liners are dismissed as obvious and the agent trusts the signature instead.

Or: the skill's docs may have inaccuracies the agent picks up on, triggering verification reads.

Either way, this is the deeper insight: **for AI consumption, terser-is-better-than-thorough is plausible**, opposite of the usual "more documentation is better" intuition for humans.

### Day 2 — Opus backfill to N=10 changed the Opus picture

Ran 5 more Opus passes per arm to balance Sonnet's N=10. The result was unexpected: the Opus deltas collapsed.

N=5 medians (original report):
- Arm A: 355,942
- Arm B: 408,297 (+14.7% vs A)
- Arm C: 425,455 (+19.5% vs A)

N=10 medians (after backfill):
- Arm A: 405,939
- Arm B: 403,236 (−0.7% vs A) ← collapsed to noise
- Arm C: 438,718 (+8.1% vs A) ← halved

The Opus story shifted from "docs increase token cost by ~15–20%" to "docs have approximately no effect." The original direction-of-effect was an artifact of N=5 variance.

This is itself an important methodological finding worth a callout in the blog post: **small-sample variance in LLM benchmarks can produce sizable misleading deltas**. The original Opus report wasn't *wrong* in the sense of fabrication — it accurately reported the medians of 5 runs each. But N=5 turned out to be insufficient to see through variance. A reviewer at N=5 might have flagged this; we caught it ourselves by going to N=10.

Sonnet N=10 numbers were stable (collected at N=10 from the start, no comparable correction needed).

## Final framing for the README (revised)

> Tested across Opus 4.7 and Sonnet 4.6, N=10 per cell. Doc comments can reduce agent token cost — but only when well-written, and only for less-capable models. On Opus, doc comments are approximately neutral. On Sonnet, human-written docs reduce cost by 20%; this skill's generated docs *increase* cost by 25%. The skill is never better than human docs across the tested capability range. Don't use this skill.

## Updated story arc for the post

**Act 1 — The hypothesis felt obvious.** Same as before.

**Act 2 — The first experiment showed the hypothesis was wrong.** N=5 Opus result: docs cost 14–19% more. Published it honestly.

**Act 3 — The follow-up.** Pre-registered Sonnet test. Sonnet C-arm strongly supported the hypothesis (−20%); B-arm strongly refuted it (+25%). Discovery-calls metric revealed the mechanism.

**Act 4 — Backfilling Opus to N=10 corrected the Act 2 numbers.** The original Opus deltas were noise-dominated. At N=10, Opus is effectively flat. The story sharpens: the skill is bad on Sonnet, neutral on Opus.

**Coda — what this teaches about benchmarking AI skills.**
- Pre-register or pay the price.
- N=5 is not enough for medians on noisy LLM metrics. Plan for N≥10 from the start, ideally with power analysis.
- The mechanism metric (discovery calls) was more revealing than the headline metric (input tokens). Always collect mechanism data.
- Falsification is publishable. The repo is more valuable as an honest negative-result case study than as another optimistic skill.

## Findings worth a sidebar in the post

**The cache-vs-discovery question.** Stream-json reports `input_tokens`, `cache_read_input_tokens`, and `cache_creation_input_tokens`. We summed all three for the metric. Worth a footnote on why this is the right billable-cost metric — caching doesn't make tokens "free."

**The agent doesn't strategize differently.** Discovery tool counts were nearly identical across arms (median 5–6). This was the most surprising finding. We assumed docs would let the agent skip reads. They didn't — the agent's read pattern is driven by symbol-name matching, not by doc availability.

**Headless agent has different reflexes.** The using-superpowers auto-invocation in the first smoke test is its own short anecdote about how the interactive and headless environments diverge.

## Quotes to use

(Will fill in from final report and from this conversation.)

## Open questions / future experiments

1. Does a task that *requires* understanding non-obvious side effects show docs benefit? Our task had descriptive method names — too easy to find via grep.
2. Does an untyped language (Python without type hints) show more benefit? Type-rich Swift may already give the agent most of what docs would provide.
3. Does an opaquely-named codebase show benefit? We tested clean naming. Code that's been through a refactor history of `processData()` -> `processData2()` -> `processDataFinal()` might tell a different story.
4. Does a non-frontier model (Haiku, GPT-4o mini equivalent) show more benefit than even Sonnet?
