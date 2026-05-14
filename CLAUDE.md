# Handoff: claude-code-doc-comments

This file captures all decisions made during planning so Claude Code can pick up without re-litigating anything. Read this fully before taking any action.

---

## What This Is

A Claude Code skill named `doc-comments`. It generates and refreshes structured doc comments across a codebase, prioritizing agent context over human readability.

The core argument: agents burn tokens inferring function contracts from implementations. A well-formed doc comment is a compressed, reliable signal that lets an agent understand what a function takes, returns, touches, and can fail with — without reading the code. Stale or missing doc comments are a token budget problem, not just a developer experience problem.

---

## Decisions Already Made — Do Not Revisit

**Name:** `doc-comments`
Chosen over `docblock` (PHP-specific) and `inline-docs` (too vague). Language-agnostic and unambiguous.

**GitHub repo name:** `claude-code-doc-comments`
Follows the naming pattern of the companion skill: `claude-code-onboard`.

**Priority order:** Agent context first, human readability second. This frames all content decisions — README rationale, quality bar, comment content rules.

**Default behavior:** Full codebase sweep with exclusions applied. No flags needed for the common case.

**Flags:**
- `--changed`: git-modified files only, same exclusions
- `--only <ext>`: filter by extension, combinable with either mode

**Modes:** Generate (missing) and refresh (stale) are not separate flags — the skill auto-detects per symbol and handles both in a single pass.

**Languages supported:** PHP, Swift, JavaScript, TypeScript. Defined in `references/formats.md`. Extensible.

**Exclusions (always applied):**
Directories: `.git`, `node_modules`, `vendor`, `.build`, `dist`, `build`, `.cache`, `__pycache__`, `.next`, `.nuxt`, `coverage`, `.nyc_output`, `.terraform`, `.serverless`, `.tox`, `.venv`
File types: images, fonts, compiled assets, archives, lock files, binaries

**No company-specific references anywhere.** This is a public, open-source skill. No org names, no internal tool references, no team names.

**Zip packaging rule:** Files are at the root of the archive. No wrapper directory. Correct: `zip doc-comments.zip SKILL.md README.md EVALUATION.md references/formats.md references/quality-bar.md`. Incorrect: a zip that extracts to `doc-comments/SKILL.md`.

---

## File Manifest

All files are already written and located at the path where you cloned or placed this repo. Do not regenerate them.

```
SKILL.md                     — executable skill definition, YAML frontmatter + workflow
README.md                    — human-facing docs, agent-first rationale, usage, flags
EVALUATION.md                — testing methodology, paired session metrics
CLAUDE.md                    — this file, handoff context for Claude Code
references/
    formats.md               — per-language doc comment syntax (PHP, Swift, JS, TS)
    quality-bar.md           — standard for agent-useful vs. noise comments
```

---

## Remaining Tasks

### 1. Initialize the GitHub repo

```bash
gh repo create tommcfarlin/claude-code-doc-comments --public --description "A Claude Code skill that generates and refreshes doc comments across a codebase. Agent context first." --clone
```

### 2. Copy files into the cloned repo

Copy all files from this directory into the cloned `claude-code-doc-comments/` directory, preserving the `references/` subdirectory.

### 3. Initial commit and push

```bash
git add .
git commit -m "chore: initial skill scaffold"
git push -u origin main
```

### 4. Verify repo structure on GitHub

Confirm the repo at `https://github.com/tommcfarlin/claude-code-doc-comments` shows:

```
references/
    formats.md
    quality-bar.md
CLAUDE.md
EVALUATION.md
README.md
SKILL.md
```

### 5. Remove CLAUDE.md after setup is complete

This file is a handoff artifact. Once the repo is live and verified, delete `CLAUDE.md` and push a cleanup commit:

```bash
git rm CLAUDE.md
git commit -m "chore: remove handoff file"
git push
```

---

## Reference: Companion Skill

The `onboard` skill at `https://github.com/tommcfarlin/claude-code-onboard` is the structural reference for this skill. Match its patterns for SKILL.md frontmatter, README tone, and EVALUATION.md format. Do not copy its content — the skills are different — but the structure and conventions should be consistent.

---

## Questions Already Answered

**Why not separate generate and refresh flags?**
Auto-detection per symbol is cleaner. The user doesn't need to know or care which symbols are missing vs. stale — the skill handles both in one pass.

**Why agent context before human readability?**
Because that's the current, underserved use case. Every developer already knows doc comments help humans. The agent argument is newer and more actionable — it's why someone would install this skill *now*.

**Why is stale worse than missing?**
A missing comment forces the agent to read the implementation, which is always correct. A stale comment gives the agent false confidence. It acts on wrong information without knowing it's wrong. This is documented in `references/quality-bar.md`.
