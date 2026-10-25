---
title: Name lookup parsers
status: done
repo: workbench
value: "No code guesses an epic from a name, so single-hyphen names can never be misattributed"
files: [plugins/workbench/skills/start-development/scripts/ticket.py, plugins/workbench/skills/start-development/tests/test_ticket_names.py, plugins/workbench/skills/start-development/tests/test_ticket_check.py, plugins/workbench/skills/start-development/tests/test_ticket_overlap_ignore.py, plugins/workbench/skills/start-development/tests/test_ticket_move.py]
verify: "cd plugins/workbench && bash scripts/run-tests.sh --only start-development && cd ../.. && mise run lint"
depends_on: [single-hyphen-names]
model: sonnet
review: ""
verified_head: 97192abc1ba9aa7faeec3d43e698b831248f5bba
points: 3
expected_minutes: 45
expected_tokens: 2250000
points_actual: ""
actual_minutes: 12
actual_tokens: 221162
actual_roles: "impl 3, review 9"
actual_role_tokens: "impl 94514, review 126648"
---

# Name lookup parsers

## Requirement

Replace every name parser in ticket.py with one lookup from the tickets (design D3, D10), because `<epic>-<task>` cannot be split.

- New `ticket_names(root) -> dict[str, tuple[str, str | None]]` maps every epic slug in all three phases to `(epic, None)`, and every `<epic>-<task>` built with `worktree_name` from the epic's task files to `(epic, task)`. It is the one way code maps a tree or branch name to a ticket.
- The `run_check` live-worktree warning (ticket.py:571) resolves each live tree name through `ticket_names`, as an integration tree `<epic>` or a task tree `<epic>-<task>`. It warns when that epic is not in-progress.
- Reap-all (`cmd_reap` with no `--epic`, :1520) sweeps a directory under `<configdir>/worktrees/` only when `ticket_names` maps it to an epic that is not in-progress, or when it is a legacy `<x>--<y>` directory whose `<x>` is not an in-progress epic, so old trees stay reapable. Every other directory is left untouched and is not listed as removed.
- The `_counting_overlaps` fallback branch (:473) uses `worktree_name`; its base stays `main` (design D10).
- No f-string producer `}--{` and no `split("--")` remains in ticket.py; the legacy check uses a named constant.
- Updated tests: test_ticket_check.py:312-321 (the warning names single-hyphen trees of a real task), test_ticket_overlap_ignore.py:138, and the reap-all stray-tree tests in test_ticket_move.py; new test_ticket_names.py.

## Acceptance conditions

- AC1: ticket_names maps every epic slug and every epic-task name to its ticket across all phases [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_names.py::test_ticket_names_maps_epics_and_tasks]
- AC2: the check warning resolves live tree names through the lookup [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_check.py::test_live_tree_warning_uses_ticket_lookup]
- AC3: reap-all leaves a directory that maps to no ticket untouched and still reaps a merged legacy double-hyphen tree [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_move.py::test_reap_all_ignores_dirs_with_no_ticket]
- AC4: the overlap fallback branch uses the single-hyphen name [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_overlap_ignore.py::test_merged_fallback_branch_single_hyphen]
- AC5: no double-hyphen producer or splitter remains in ticket.py [evidence: command:! grep -nE '\}--\{|split\("--"' plugins/workbench/skills/start-development/scripts/ticket.py]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_names.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_check.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_overlap_ignore.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_move.py`

## Interfaces

- `ticket.ticket_names(root: Path) -> dict[str, tuple[str, str | None]]` (new; the `ticket-name-lookup` part, consumed by slug-collision-guard and epic-close-sweep).

## Expected outcome

Nothing in ticket.py splits a name: the warning, reap-all and the overlap check all go through the tickets, and unknown directories under the worktrees dir are never touched.

## Steps

- Red: write `plugins/workbench/skills/start-development/tests/test_ticket_names.py` and update the pinned tests; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_names.py skills/start-development/tests/test_ticket_check.py -q`; expect failures.
- Green: add `ticket_names` (built on `scan(root)`), switch the parsers and the fallback.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development`, then `mise run test && mise run lint` from the root.

## Notes

- `scan(root)` already walks every phase and task file; reuse it.
- An integration tree `<epic>` (created by integration-tree-create) maps to `(epic, None)`, so the warning covers it too.
