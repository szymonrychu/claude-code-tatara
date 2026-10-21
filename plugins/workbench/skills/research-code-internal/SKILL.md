---
name: research-code-internal
description: "Hunt the repos in scope for parts a plan would otherwise rebuild, near-duplicate helpers and optimisation hot spots, before the plan is written. Use when the plan adds any helper, reader, parser, schema field or subsystem, or a repo has more than ~200 source files; always on the full path before phase 3. Read-only; dispatches one reuse-hunter agent."
---

# research-code-internal

Finds what already exists in our own code so the plan reuses it instead of
rebuilding it.

## When to run it

Run when:
- the plan will add any helper, reader, parser, schema field or subsystem;
- a repo in scope has more than ~200 source files;
- always, on the full path, before phase 3.

Skip when:
- lean path with every file named and no new helper.

## Procedure

1. Get the brief path: `bash ${CLAUDE_PLUGIN_ROOT}/skills/start-research/scripts/doc_path.sh research "<topic>-code-internal"`.
2. Dispatch ONE `reuse-hunter` agent. Model: `sonnet`; `opus` when more than
   two repos are in scope. Set the model explicitly. Pass it the task, the repos
   in scope, and the plan items or the design doc path.
3. Write its answer to the brief path and return the path plus the Plan inputs.
4. Its `reuse` list is the shared-parts map (part -> exists-at / needed-by /
   proposed owner) that phase 3 consumes. Pass it on unedited.

## Output: Plan inputs

Return the four `## Plan inputs` lists (`reuse`, `do-not-build`, `fix-as-ac`, `ideas`) exactly as
defined in `${CLAUDE_PLUGIN_ROOT}/skills/start-development/references/plan-inputs.md`; do not restate
them.

## Rules

- Read-only: no edits to the repos in scope.
- Every claim cites file:line or file:symbol that was found, not guessed.
- Model sonnet unless stated above; set the model explicitly on the agent call.
