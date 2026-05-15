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
