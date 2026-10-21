---
title: Plan execute epic names
status: todo
repo: workbench
value: "The run accepts the new <epic>-<task> trees and rejects the old form"
files: [plugins/workbench/workflows/plan-execute.js, plugins/workbench/workflows/tests/plan-execute-epic.test.mjs, plugins/workbench/workflows/tests/plan-execute-epic-audit.test.mjs]
verify: "mise run test && mise run lint"
depends_on: []
owns: []
uses: []
model: sonnet
estimate: 30
actual: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Plan execute epic names

## Requirement

Make the plan-execute epic-run name check expect `<epic>-<id>` (design D3).

- In `plugins/workbench/workflows/plan-execute.js` (316-326) an epic run requires each task worktree to end in `<epic>-<id>` or `<epic>-<id>/<repo>`; the name cap is 57 characters. Errors read `plan-execute: task <id> worktree <wt> must be <epic>-<id>` and `... is <n> chars; the cap is 57`.
- The header comment (line 76) says `<epic>-<id>[/<repo>]`.
- Updated tests: `plan-execute-epic.test.mjs:59-91` (the message `must be epic-x-a`, a 58-character name throws, exactly 57 passes) and `plan-execute-epic-audit.test.mjs:57,65,215-216` (branches `epic-x-parser`, `epic-x-writer`).
- Runs without `args.epic` are unchanged.
- Every new or renamed test title in these files is a single kebab token, so the AC refs run with the refRunners `--test-name-pattern {name}` command.

## Acceptance conditions

- AC1: an epic run rejects a worktree that does not end in the single-hyphen name [evidence: test:plugins/workbench/workflows/tests/plan-execute-epic.test.mjs::epic-worktree-must-end-in-epic-hyphen-id]
- AC2: a 58-character name throws with the cap 57 [evidence: test:plugins/workbench/workflows/tests/plan-execute-epic.test.mjs::epic-worktree-name-over-57-throws]
- AC3: a 57-character name passes [evidence: test:plugins/workbench/workflows/tests/plan-execute-epic.test.mjs::epic-worktree-name-of-57-passes]
- AC4: the epic-close audit prompt lists single-hyphen branches [evidence: test:plugins/workbench/workflows/tests/plan-execute-epic-audit.test.mjs::epic-audit-lists-single-hyphen-branches]
- AC5: no double-hyphen epic name check remains in plan-execute.js [evidence: command:! grep -n 'EPIC}--' plugins/workbench/workflows/plan-execute.js]

## Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-epic.test.mjs`
- `plugins/workbench/workflows/tests/plan-execute-epic-audit.test.mjs`

## Interfaces

- plan-execute args validation for `args.epic` (existing, changed); no new args.

## Expected outcome

`ticket.py args` output for an epic whose trees are `<epic>-<task>` passes plan-execute's validation; `<epic>--<task>` trees are rejected.

## Steps

- Red: rename and update the pinned tests; run `cd plugins/workbench && node --test workflows/tests/plan-execute-epic.test.mjs workflows/tests/plan-execute-epic-audit.test.mjs`; expect failures.
- Green: change `want` and the cap in plan-execute.js.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`, then `mise run test && mise run lint` from the root.

## Notes

- validate-tasks.mjs runs plan-execute without `args.epic`, so the lint is unaffected.
