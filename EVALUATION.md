# Evaluation Plan

## Question

Does `/doc-comments` reduce the cost of agent work in a documented codebase compared to an undocumented one?

## Hypothesis

Agent sessions working in a codebase with current doc comments will spend fewer tokens and fewer tool calls on symbol-level discovery before reaching productive work, compared to sessions working in the same codebase without doc comments.

## Variables

- **Independent:** with doc comments vs. without doc comments
- **Dependent:** tokens consumed on discovery, tool calls before first meaningful action, accuracy of symbol understanding
- **Controlled:** same codebase, same tasks, same model, same conversation structure

## Method

Run paired agent sessions across a set of real tasks. Each task is performed twice: once in the undocumented codebase, once after running `/doc-comments`. Record metrics for each.

### Task Set

Use a mix of task types to avoid biasing toward scenarios where one approach wins by default:

1. **Symbol lookup** — "What does `<function>` do and what does it return?"
2. **Call site change** — "Update all callers of `<function>` to handle the new return type"
3. **Side effect audit** — "Which functions in this module write to the database?"
4. **Bug fix** — "This function is producing wrong output, find and fix it"
5. **Cross-module change** — "Update the shared client and all callers"

Run each task type against at least two projects of varying size (small: <10 files, medium: 10–50 files, large: 50+ files).

### Metrics

Track the following per session:

| Metric | Description |
|---|---|
| Tokens to first meaningful action | Total tokens consumed before the agent performs a productive action rather than discovery |
| Discovery tool calls | Count of Read, Glob, and Grep calls used to understand symbols before productive work begins |
| Total session tokens | Total tokens for the entire session |
| Correct symbol references | Whether the agent correctly identifies the contract, return value, and side effects without reading the full implementation (yes/no) |
| Stale comment encounters | Number of times the agent encountered a comment that did not match the implementation (doc-comments sessions only) |

### Procedure

1. Select a project and task from the matrix above.
2. **Undocumented run:** Start a fresh agent session on the codebase with no doc comments. Issue the task prompt. Record all metrics.
3. **Documented run:** Run `/doc-comments` on the codebase. Start a fresh agent session. Issue the same task prompt. Record all metrics.
4. Repeat for each task/project combination.
5. Use the same model and no other context-loading mechanisms across both runs.

### Controls

- Do not reuse a session for multiple test runs.
- Strip all doc comments before undocumented runs to ensure a clean baseline.
- Use the same prompt phrasing for both runs of each task.
- Run undocumented and documented sessions in randomized order to avoid learning effects.

## Analysis

Compare paired results across each metric. Key questions:

1. **Discovery cost:** How many fewer tool calls and tokens does the documented run spend before productive work?
2. **Accuracy:** Does the documented run reference correct contracts and side effects more reliably?
3. **Scaling:** Does the benefit increase with project size?
4. **Stale comment impact:** When stale comments are present, does agent accuracy drop below the undocumented baseline?

## Reporting

Record results in a table per task/project pair:

| Project | Task Type | Metric | Undocumented | Documented | Delta |
|---|---|---|---|---|---|
| project-a | symbol lookup | tokens to first action | | | |
| project-a | symbol lookup | discovery tool calls | | | |
| ... | ... | ... | ... | ... | ... |

Summarize findings with aggregate comparisons. Note any task types or project sizes where doc comments showed no measurable benefit. Pay particular attention to whether stale comments produce worse outcomes than no comments — this is the key risk the `--changed` workflow is designed to mitigate.
