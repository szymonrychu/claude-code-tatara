---
title: Retro records once
status: todo
repo: workbench
value: "Retro reads each epic's agent records in one pass and orders undated old epics by when their work was verified"
files: [plugins/workbench/scripts/lib/agent_usage.py, plugins/workbench/skills/start-development/scripts/ticket_cmds/retro.py, plugins/workbench/skills/start-development/tests/test_ticket_retro.py, plugins/workbench/skills/start-development/references/tickets.md]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint"
depends_on: [legacy-transcript-matcher]
model: sonnet
review: ""
verified_head: ""
points: 5
expected_minutes: 57
expected_tokens: 3750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Retro records once

## Requirement

User request (verbatim, 2026-10-25): "Skill to add: migrate epics/tasks from old scheme to new one. Can be started after current work gets delivered."

User decision (verbatim): "Q7 Delivery order for epics without `task <slug> done` commits: by the commit date of each task's verified_head (retro fallback), then dependency order for the rest."

Design D6: One transcript pass per epic (verbatim):

`agent_usage.records_by_task(epic, logs_dir, transcripts_dir, backfill=True, names=None)` reads the
epic's records once, backfills at most once when a task wanted is missing, reads again once, and returns
`{task: [records]}`. `retro._fill_from_records` uses it instead of `records_for` per task (each empty task
walked every transcript: 23 x 149 for epic-integration-worktrees), and migrate uses it with `names`.
`records_for` stays for the single task of `ticket.py task --status done`.

Design D7: Delivery order fallback (Q7) (verbatim):

`retro._delivery_order`: tasks with a `task <slug> done` commit first, oldest first; then the rest by the
committer date of their `verified_head`, oldest first; then the remainder in dependency order. A
`verified_head` that is empty, not a commit, or not a sha at all (`"$(see below)"` in
init-leaves-a-green-tree/license-every-plugin) puts the task in the remainder, never an error.

Reuse brief fix-as-ac (verbatim): "hot spot: retro._fill_from_records calls records_for per task (C/retro.py:139-142); each empty task triggers a full rglob+parse of every transcript (AU:254,302): O(tasks x transcripts), 23x149 for epic-integration-worktrees. Index once per epic."

Reuse brief fix-as-ac (verbatim): "verified_head \"$(see...\" non-sha - done/init-leaves-a-green-tree/tasks/license-every-plugin.md - fallback tolerates it"

housekeeping-rules-estimates RETRO.md, Tech debt (verbatim): "retro backfills per empty task (up to N transcript walks): lives in retro command; remove by a single transcript pass shared across tasks. Accepted at review."

## Acceptance conditions

- AC1: `agent_usage.records_by_task(epic, logs_dir, transcripts_dir, backfill=True, names=None)` returns `{task: [records]}` for the epic, reading the logs once, backfilling at most once (only when a wanted task has no record) and reading again once; `backfill=False` or no transcripts dir only reads; `names` passes through to `backfill` [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_records_by_task_one_pass]
- AC2: `ticket.py retro` over an epic whose three tasks have no records parses each transcript's marker at most once (one backfill per epic, not one per task) and fills the same minutes and tokens as before [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_retro_walks_transcripts_once]
- AC3: tasks with no `task <slug> done` commit follow the delivered ones by the committer date of their verified_head, oldest first, before the remaining tasks in dependency order [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_delivery_order_falls_back_to_verified_head]
- AC4: a verified_head that is empty, an unknown sha, or not a sha at all (`"$(see below)"`) puts its task with the dependency-ordered rest, and retro exits 0 [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_delivery_order_tolerates_non_sha_verified_head]
- AC5: the existing delivery order test still passes unchanged: done commits win over verified_head dates [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_tasks_in_delivery_order]
- AC6: the existing records and Notes fallback test still passes unchanged [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_retro.py::test_falls_back_to_records_and_notes]
- AC7: references/tickets.md's `retro` entry names the verified_head fallback and the one transcript pass per epic [evidence: command:awk '/^- `retro`:/,/^- `deltas`:/' plugins/workbench/skills/start-development/references/tickets.md | grep -q 'verified_head']
- AC8: the start-development and scripts suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development && bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint]

## Files

- `plugins/workbench/scripts/lib/agent_usage.py`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/retro.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_retro.py`
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
