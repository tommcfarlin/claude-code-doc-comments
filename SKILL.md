---
name: doc-comments
description: "Generate and refresh structured doc comments across a codebase. Agent-context first — produces comments that reduce LLM discovery cost, with human readability as a byproduct."
allowed-tools: "Bash Read Write Glob Grep"
argument-hint: "[--changed] [--only <ext>]"
---

# Doc Comments

Generate and maintain structured doc comments across a codebase. Prioritizes agent-useful signal — what a function contracts, what it returns, what side effects it has — over prose description.

## When to Use

- The user says "doc-comments", "generate doc comments", "refresh doc comments", or runs `/doc-comments`
- The user wants to prepare a codebase for agentic workflows
- The user wants to audit or update existing doc comments after code changes

## Flags

- **No flags (default):** Full codebase sweep, exclusions applied. Generates missing doc comments and refreshes existing ones that have drifted from the implementation.
- **`--changed`:** Scoped to git-modified files only. Same exclusions applied. Use after commits or during active development.
- **`--only <ext>`:** Filter by file extension (e.g. `--only php`, `--only swift`, `--only ts`). Combinable with either mode.

## File Exclusions

Always applied regardless of flags. Skip these directories:

- `.git`, `node_modules`, `vendor`, `.build`, `dist`, `build`, `.cache`
- `__pycache__`, `.next`, `.nuxt`, `coverage`, `.nyc_output`
- `.terraform`, `.serverless`, `.tox`, `.venv`

Skip these file types:

- Images: `png`, `jpg`, `gif`, `svg`, `ico`, `webp`
- Fonts: `woff`, `woff2`, `ttf`, `eot`, `otf`
- Compiled: `*.min.js`, `*.min.css`, `*.map`
- Archives: `zip`, `tar`, `gz`
- Lock files: `package-lock.json`, `composer.lock`, `yarn.lock`, `Gemfile.lock`
- Binaries and non-text files

## Workflow

### Step 1 — Determine Scope

**If `--changed` flag is present:**

```bash
git diff --name-only HEAD
```

Filter the result through the exclusion list and, if `--only <ext>` is set, by extension. This is the working file set.

If not in a git repository, tell the user:
> "`--changed` requires a git repository. Either run from within a git repo or remove the flag to sweep the full codebase."

Stop here.

**If no flags (default):**

Glob all files recursively from the project root. Apply exclusions. If `--only <ext>` is set, filter by extension. This is the working file set.

### Step 2 — Identify Target Symbols

For each file in the working set:

1. Detect the language from the file extension. Refer to `references/formats.md` for supported languages. Skip files with unsupported extensions silently.
2. Scan for documentable symbols: functions, methods, classes, structs, enums, interfaces, and public properties.
3. For each symbol, determine its state:
   - **Missing:** no doc comment present
   - **Stale:** doc comment exists but does not match the current signature, parameters, return type, or behavior
   - **Current:** doc comment exists and accurately reflects the implementation

Skip symbols that are:
- Private/internal single-line utility functions where the name and signature are fully self-explanatory
- Auto-generated code blocks
- Test helper stubs with no meaningful contract

### Step 3 — Generate or Refresh

For each symbol in **Missing** or **Stale** state:

**Refer to `references/formats.md`** for the correct doc comment syntax for that language.

**Refer to `references/quality-bar.md`** for what constitutes agent-useful content vs. noise.

Write doc comments that cover:

1. **Purpose** — what the symbol does, stated as a contract not a description of implementation
2. **Parameters** — name, type (if not in signature), and what the value represents
3. **Return value** — what it returns and what that value means, not just its type
4. **Side effects** — any external state touched: database, API, filesystem, cache, globals
5. **Throws/errors** — conditions under which it fails and what is thrown
6. **Non-obvious behavior** — edge cases, nullability, ordering constraints, performance characteristics

Do not:
- Restate the function name in prose ("This function gets the user")
- Describe implementation steps the agent can read directly
- Add boilerplate that contributes tokens without contributing signal

### Step 4 — Write Changes

Write updated doc comments in place. Do not modify any code outside of doc comment blocks.

If a symbol had a **Stale** comment, replace it entirely rather than patching inline.

### Step 5 — Summary

After processing the working file set, print a summary:

> **Doc comments complete.**
>
> **Files processed:** N
> **Symbols documented:** N (N generated, N refreshed, N already current)
> **Skipped:** N (unsupported extension or self-explanatory)
>
> Run `/doc-comments --changed` after future commits to keep comments current.

If no symbols required changes:

> **All doc comments are current.** No changes made.

## Important

- Always use the format for the detected language. Never apply PHP DocBlock syntax to Swift files, etc.
- Agent-useful signal is the standard. If a comment would not help an LLM understand the contract without reading the implementation, rewrite it.
- Do not modify code logic, formatting, or whitespace outside of doc comment blocks.
- Stale is worse than missing. A doc comment that contradicts the implementation is actively harmful to agent accuracy. When in doubt, refresh.
