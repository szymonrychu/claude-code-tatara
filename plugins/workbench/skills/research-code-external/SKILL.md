---
name: research-code-external
description: "Survey similar open-source projects for implementation shapes, known dead ends and maturity before a design is fixed. Use when the change implements something with known analogues (a protocol, parser, scheduler, cache, auth flow, rules engine) or the design has an open fork. Runs start-research, which dispatches the workbench:research-prior-art-scout agent."
---

# research-code-external

Surveys prior art outside our code so the design borrows proven shapes and avoids known dead ends.

## When to run it

Run when:
- the change implements something with known analogues (a protocol, parser,
  scheduler, cache, auth flow, rules engine);
- the design has an open fork.

Skip when:
- pure in-house glue, config edits, version bumps.

## Procedure

1. Get the brief path: `bash ${CLAUDE_PLUGIN_ROOT}/skills/start-research/scripts/doc_path.sh research "<topic>-code-external"`.
2. Invoke `start-research` with lenses [prior-art-scout] (it dispatches the
   `workbench:research-prior-art-scout` agent) and the topic, writing
   the brief to that path. Model: `sonnet`.
3. Distil the brief into the Plan inputs below: shapes worth adopting, dead ends
   to reject, parts an existing project already provides (`do-not-build`).

## Output: Plan inputs

Return the four `## Plan inputs` lists (`reuse`, `do-not-build`, `fix-as-ac`, `ideas`) exactly as
defined in phase 1 of `${CLAUDE_PLUGIN_ROOT}/skills/start-development/SKILL.md`; do not restate
them.

## Rules

- Read-only: research only, no edits to the repos in scope.
- Every claim cited with a source URL, file:line, or DOI / arXiv id.
- Model sonnet unless stated; set the model explicitly on every agent call.
