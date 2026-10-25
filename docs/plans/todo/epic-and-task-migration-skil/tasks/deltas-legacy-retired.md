---
title: Deltas legacy retired
status: todo
repo: workbench
value: "deltas reads one scheme; pre-points tasks go through migrate instead of a legacy reader"
files: [plugins/workbench/skills/start-development/scripts/ticket_cmds/deltas.py, plugins/workbench/skills/start-development/tests/test_ticket_deltas.py, plugins/workbench/skills/start-development/references/tickets.md]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: [migrate-command]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 23
expected_tokens: 1500000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Deltas legacy retired

## Requirement

User request (verbatim, 2026-10-25): "Skill to add: migrate epics/tasks from old scheme to new one. Can be started after current work gets delivered."

User decision (verbatim): "Q10 (my call): deltas._legacy (minutes-only legacy rows) is removed once migrate exists, pinned by a retirement test; migrate is the one path for pre-points tasks (no backward compatibility rule)."

Design D11: deltas legacy rows retired (Q10) (verbatim):

`deltas._legacy` (minutes-only rows from `estimate` and `actual`) and the row's `legacy` flag and
`(legacy)` marker are removed, pinned by a retirement test; migrate is the one path for pre-points tasks.
`test_all_includes_legacy_minutes` is no longer accurate and is replaced by the pin.

Reuse brief fix-as-ac (verbatim): "deltas._legacy dead after migrate - C/deltas.py:81, test_ticket_deltas.py:119 - remove (no back-compat) or keep, decide"

Constraint (verbatim, part): "deltas._legacy removal with a retirement pin"

## Acceptance conditions

- AC1: a done task without points that carries numeric legacy `estimate` and `actual` reads `not recorded` for points, minutes and tokens in `deltas --all --json`, rows carry no `legacy` key, the text output has no `(legacy)` marker, and the task file is unchanged; this replaces test_all_includes_legacy_minutes, which is no longer accurate because migrate is the one path for pre-points tasks (Q10), and drops the `legacy` assertion of test_epic_deltas [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_deltas.py::test_pre_points_tasks_are_not_read]
- AC2: retirement pin: the deltas module has no `_legacy` attribute and its source contains neither `get("estimate"` nor `get("actual"` [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_deltas.py::test_legacy_rows_retired]
- AC3: references/tickets.md's `deltas` entry has no legacy-row text and names `ticket.py migrate` as the path for pre-points tasks, and deltas.py no longer says legacy [evidence: command:! grep -qi 'legacy' plugins/workbench/skills/start-development/scripts/ticket_cmds/deltas.py && awk '/^- `deltas`:/,/^## Naming/' plugins/workbench/skills/start-development/references/tickets.md | grep -q 'ticket.py migrate' && ! (awk '/^- `deltas`:/,/^## Naming/' plugins/workbench/skills/start-development/references/tickets.md | grep -qi 'legacy')]
- AC4: the start-development suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket_cmds/deltas.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_deltas.py`
- `plugins/workbench/skills/start-development/references/tickets.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
