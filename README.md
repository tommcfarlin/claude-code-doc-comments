# Doc Comments

Help your codebase help your agent. Doc comments compress a function's contract into a few lines so an agent doesn't have to re-derive it from the implementation every time it reads the file.

> **Safe by default.** This skill writes only inside doc comment blocks — it never modifies code logic, formatting, or whitespace. Comments already current are left alone; only missing or stale ones are touched.

Measured against paired agent sessions — methodology in [EVALUATION.md](EVALUATION.md).

## Why

The traditional argument for documentation is human readability. That's still true. But in agentic workflows there's a second, more immediate argument: a structured doc comment is a compressed, reliable signal that lets an agent understand a function's contract — what it takes, what it returns, what it touches — without reading the implementation.

An agent that has to infer what a function does from 50 lines of code is slower and more error-prone than one that reads a 6-line doc comment stating the contract directly. This skill generates comments with that priority in mind. Human readability is a byproduct, not the goal.

**And stale is worse than missing.** A missing comment forces the agent to read the implementation, which is always correct. A stale comment gives the agent false confidence — it acts on wrong information without knowing it's wrong. That's why this skill isn't a one-shot generator. It re-runs, detects drift per symbol, and refreshes comments that no longer match the code.

## How It Works

Run `/doc-comments` and the skill:

1. **Sweeps the codebase** — all source files, exclusions applied
2. **Identifies target symbols** — functions, methods, classes, structs, enums, interfaces
3. **Classifies each symbol** — missing doc comment, stale (drifted from implementation), or current
4. **Generates or refreshes** — writes agent-useful doc comments in the correct format for each language
5. **Reports results** — summary of what was generated, refreshed, and skipped

## Usage

Full codebase sweep (default):

```
/doc-comments
```

Only files modified since last commit:

```
/doc-comments --changed
```

Filter by language:

```
/doc-comments --only php
/doc-comments --only swift
/doc-comments --only ts
```

Combine flags:

```
/doc-comments --changed --only php
```

## When to Skip This Skill

Mature tools say no. Skip this skill if:

- Your codebase is small enough that an agent reads the whole thing in one pass anyway (~under 2k LOC).
- You don't run agents against this codebase regularly — the payoff is in repeated sessions, not one-off reads.
- Your team has strict house-style doc conventions this skill doesn't match. The output follows standard per-language formats (DocBlock, JSDoc, Swift Documentation Comments), not bespoke style guides.
- The language isn't yet supported. See **Supported Languages** below.

## What Gets Documented

| Symbol Type | Documented |
|---|---|
| Functions and methods | Yes |
| Classes and structs | Yes |
| Enums and interfaces | Yes |
| Public properties with non-obvious meaning | Yes |
| Private single-line utilities (self-explanatory) | Skipped |
| Auto-generated code | Skipped |
| Test stubs with no meaningful contract | Skipped |

## What a Good Doc Comment Contains

Agent-useful doc comments cover:

- **Purpose** — the contract, not the implementation
- **Parameters** — what each value represents, not just its type
- **Return value** — what the result means, not just its type
- **Side effects** — anything touching external state (DB, API, filesystem, cache)
- **Throws/errors** — failure conditions
- **Non-obvious behavior** — edge cases, nullability, ordering constraints

They do not restate the function name in prose or describe implementation steps the agent can read directly.

## Supported Languages

- PHP (DocBlock)
- Swift (Documentation Comments)
- JavaScript / TypeScript (JSDoc)

Additional languages can be added to `references/formats.md`.

## What Gets Excluded

The following are never processed:

- `.git`, `node_modules`, `vendor`, `.build`, `dist`, `build`, `.cache`
- `__pycache__`, `.next`, `.nuxt`, `coverage`, `.nyc_output`
- `.terraform`, `.serverless`, `.tox`, `.venv`
- Images, fonts, compiled assets, archives, lock files, binaries

## Stale Comments

A doc comment that contradicts the current implementation is worse than no comment. An agent that reads a stale comment and acts on it confidently produces incorrect output.

The default sweep classifies and refreshes stale comments automatically. Run `/doc-comments --changed` after significant refactors to keep comments aligned with the code.

## Requirements

- A supported language codebase (PHP, Swift, JS, TS)
- `--changed` flag requires a git repository

> **Status:** Experimental. The skill works, but it's actively being evaluated in real-world workflows — expect rough edges and changes as it matures.

## Installation

Clone the repo directly into your Claude Code skills directory:

```bash
git clone https://github.com/tommcfarlin/claude-code-doc-comments.git ~/.claude/skills/doc-comments
```

After that, `/doc-comments` is available in any Claude Code session.
