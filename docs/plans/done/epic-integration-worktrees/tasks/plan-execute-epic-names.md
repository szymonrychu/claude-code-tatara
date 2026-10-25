---
title: Plan execute epic names
status: done
repo: workbench
value: "The run accepts the new <epic>-<task> trees and rejects the old form"
files: [plugins/workbench/workflows/plan-execute.js, plugins/workbench/workflows/tests/plan-execute-epic.test.mjs, plugins/workbench/workflows/tests/plan-execute-epic-audit.test.mjs]
verify: "mise run test && mise run lint"
depends_on: []
model: sonnet
review: ""
verified_head: 772697036c84a9d79930eb78a307cb84c37a4add
points: 3
expected_minutes: 40
expected_tokens: 2250000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Plan execute epic names

## Requirement

Make the plan-execute epic-run name check expect `<epic>-<id>`, and still accept the recorded legacy tree of an epic claimed before this change (design D3, D13; interrogate verdict F).

- In `plugins/workbench/workflows/plan-execute.js` (316-326) an epic run requires each task worktree to end in `<epic>-<id>` or `<epic>-<id>/<repo>`; the name cap is 57 characters. It also accepts the legacy `<epic>--<id>` or `<epic>--<id>/<repo>` that `ticket.py worktrees` kept for a live tree of an epic claimed before this change. The legacy separator is a named constant `LEGACY_SEP`, so no `EPIC}--` literal remains, and the legacy cap stays 58. Errors read `plan-execute: task <id> worktree <wt> must be <epic>-<id>` and `... is <n> chars; the cap is 57`.
- The header comment (line 76) says `<epic>-<id>[/<repo>]`.
- Updated tests: `plan-execute-epic.test.mjs:59-91` (the message `must be epic-x-a`, a 58-character name throws, exactly 57 passes) and `plan-execute-epic-audit.test.mjs:57,65,215-216` (branches `epic-x-parser`, `epic-x-writer`).
- Runs without `args.epic` are unchanged.
- Every new or renamed test title in these files is a single kebab token, so the AC refs run with the refRunners `--test-name-pattern {name}` command.

## Acceptance conditions

- AC1: an epic run rejects a worktree that ends in neither the single-hyphen name nor the legacy double-hyphen name [evidence: test:plugins/workbench/workflows/tests/plan-execute-epic.test.mjs::epic-worktree-must-end-in-epic-hyphen-id]
- AC2: a 58-character single-hyphen name throws with the cap 57 [evidence: test:plugins/workbench/workflows/tests/plan-execute-epic.test.mjs::epic-worktree-name-over-57-throws]
- AC3: a 57-character name passes [evidence: test:plugins/workbench/workflows/tests/plan-execute-epic.test.mjs::epic-worktree-name-of-57-passes]
- AC4: the epic-close audit prompt lists single-hyphen branches [evidence: test:plugins/workbench/workflows/tests/plan-execute-epic-audit.test.mjs::epic-audit-lists-single-hyphen-branches]
- AC5: no double-hyphen epic name check remains in plan-execute.js [evidence: command:! grep -n 'EPIC}--' plugins/workbench/workflows/plan-execute.js]
- AC6: an epic run accepts a task whose recorded worktree is a legacy double-hyphen tree [evidence: test:plugins/workbench/workflows/tests/plan-execute-epic.test.mjs::epic-worktree-legacy-double-hyphen-accepted]

## Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/workflows/tests/plan-execute-epic.test.mjs`
- `plugins/workbench/workflows/tests/plan-execute-epic-audit.test.mjs`

## Interfaces

- plan-execute args validation for `args.epic` (existing, changed); no new args.

## Expected outcome

`ticket.py args` output for an epic whose trees are `<epic>-<task>` passes plan-execute's validation; a recorded legacy `<epic>--<task>` tree is still accepted, and any other name is rejected.

## Steps

- Red: rename and update the pinned tests; run `cd plugins/workbench && node --test workflows/tests/plan-execute-epic.test.mjs workflows/tests/plan-execute-epic-audit.test.mjs`; expect failures.
- Green: change `want` and the cap in plan-execute.js.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only workflows`, then `mise run test && mise run lint` from the root.

## Notes

- validate-tasks.mjs runs plan-execute without `args.epic`, so the lint is unaffected.
