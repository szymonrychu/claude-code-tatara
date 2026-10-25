---
title: Legacy transcript matcher
status: todo
repo: workbench
value: "Old epics' implementer and reviewer transcripts count toward their tasks' actuals even without the run marker"
files: [plugins/workbench/scripts/lib/agent_usage.py, plugins/workbench/scripts/tests/test_agent_usage.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint"
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 34
expected_tokens: 2250000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Legacy transcript matcher

## Requirement

User request (verbatim, 2026-10-25): "Skill to add: migrate epics/tasks from old scheme to new one. Can be started after current work gets delivered."

User decision (verbatim): "Q5 Actuals for old tasks: actual_minutes from legacy numeric `actual`, else from matched transcripts; actual_tokens and roles only from matched transcripts (first prompt names the task file or the task worktree; role from meta.json agentType); otherwise absent, never invented."

User decision (verbatim): "Q11 (my call): the legacy transcript matcher skips transcripts that name no task (planner, merger, auditor, record-writer); only implementer and reviewer agent types count, mapped to impl and review."

Design D5: Legacy transcript matcher (Q11; interrogate item 2) (verbatim):

`agent_usage.legacy_task(path, names)` returns `(epic, task)` for an unmarked transcript whose first user
prompt names one task, matching tokens of `names` (a dict from name to `(epic, task or None)`) bounded by
non-name characters. Precedence: exactly one task file path (`<epic>/tasks/<task>.md`) named wins; else
exactly one tree or branch name of a task; else, or when ambiguous (two tasks at the same level, or only
an epic name), no match and no record. The caller (migrate) builds `names` only from
`<epic>/tasks/<task>.md` for every task, every `ticket.ticket_names` entry, and each old task's legacy
`worktree` basename and `branch` (read before D2 drops them) when that value contains both the epic slug
and the task slug; never `HEAD` (4 old tasks carry `branch: HEAD`), an empty string or free text.
`agent_usage.backfill(..., names=None)` writes a record for such a transcript only when `names` is given
and its `agent-<id>.meta.json` agentType is `workbench:implementer` (role impl), `workbench:reviewer`
(review) or `workbench:verifier` (review: the old verifier did the review's verification); every other
agent type (planner, merger, auditor, record-writer, general-purpose) is skipped. A marker still wins over
the names. backfill's rglob already reaches the workflow transcripts under
`<session>/subagents/workflows/wf_*/` (887 of the 1042 on disk, each with a meta.json). Alternatives:
importing ticket.py in agent_usage (rejected: stdlib-only lib), a fixed regex for the layout (rejected:
names already exist in ticket.py).

Constraint (verbatim): "Python 3.9 safe in hooks and scripts/lib; stdlib only in scripts/lib (agent_usage cannot import ticket.py, so the legacy matcher takes a names map from its caller)."

Reuse brief fix-as-ac (verbatim): "unmarked skipped - AU:257; pinned by test_agent_usage.py:293 - update test, keep no-task transcripts skipped"

Interrogate verdict item 2 (verbatim): "Only task file paths, ticket_names entries and worktree or branch names that contain both the epic and the task slug enter the map; never HEAD, empty strings or free text. Precedence: exactly one task file path wins, else exactly one tree name, else skipped; an ambiguous prompt never gets a record."

Interrogate verdict item 3 (verbatim, part): "workbench:verifier transcripts count as role review, implementer as impl, reviewer as review, every other agent type skipped."

## Acceptance conditions

- AC1: `agent_usage.legacy_task(path, names)` matches tokens of `names` bounded by non-name characters with this precedence: exactly one task file path (`<epic>/tasks/<task>.md` under any phase dir) wins, even when a tree name of another task is also named; else exactly one task tree or branch name (`<epic>--<task>`, `<epic>-<task>`); a prompt naming only an epic name, no name, or two different tasks at the deciding level returns None [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_legacy_task_matches_one_task]
- AC2: `backfill(transcripts, logs, names=names)` writes a record for an unmarked transcript that `legacy_task` matches and whose `agent-<id>.meta.json` agentType is `workbench:implementer` (role impl), `workbench:reviewer` (review) or `workbench:verifier` (review), with epic and task from the match and the same summariser and record shape as a marked one; with `epic=` set, other epics' matches are skipped [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_backfill_matches_legacy_transcripts]
- AC3: unmarked transcripts that name no task or an ambiguous set, and matched ones of any other agent type (worktree-merger, general-purpose, planner, scope-auditor, record-writer) or with no meta.json, are skipped [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_backfill_skips_unmatched_and_other_types]
- AC4: a matched transcript under `<session>/subagents/workflows/wf_<id>/agent-<id>.jsonl` with its meta.json beside it is reached and recorded like one directly under `subagents/` [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_backfill_reaches_workflow_transcripts]
- AC5: test_backfill_writes_marked_only is updated, not weakened: its fixture gains an unmarked implementer transcript naming a task file, and without `names` only the marked record is written, as before [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_backfill_writes_marked_only]
- AC6: a marked transcript keeps its marker's epic, task and role even when its prompt also names another task of `names` [evidence: test:plugins/workbench/scripts/tests/test_agent_usage.py::test_backfill_marker_wins_over_names]
- AC7: agent_usage imports no ticket module (stdlib plus workbench only) [evidence: command:! grep -nE '^\s*(import|from)\s+ticket' plugins/workbench/scripts/lib/agent_usage.py]
- AC8: the scripts suite and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint]

## Files

- `plugins/workbench/scripts/lib/agent_usage.py`
- `plugins/workbench/scripts/tests/test_agent_usage.py`

## Interfaces

- `agent_usage.legacy_task(path: str | os.PathLike, names: dict[str, tuple[str, str | None]]) -> tuple[str, str] | None` (plugins/workbench/scripts/lib/agent_usage.py).
- `agent_usage.backfill(transcripts_dir, logs_dir, refresh=False, epic=None, names=None) -> list[dict]`: new keyword `names`; `None` keeps today's marked-only behaviour.
- Record shape unchanged: agentId, agentType, transcript, updatedAt, start, end, model, epic, task, role, tokens.

## Expected outcome

Given a names map, backfill writes `.logs/agents` records for the old epics' implementer and reviewer transcripts that name one task (lean-development-flow's name their task files); without one, nothing changes.

## Steps

1. Read agent_usage.py and test_agent_usage.py in one pass. Write the four new tests and the fixture change; run `cd plugins/workbench && pytest scripts/tests/test_agent_usage.py -q`: the new tests fail (no `legacy_task`, no `names` keyword).
2. Implement `legacy_task` and the `names` path in `backfill`; run the verify once: `bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint`.
3. `git add`, commit, rerun the verify and quote the `[lint:*]` and suite summary lines from that run.

## Notes

- Estimate: 3 points: one lib function plus a keyword on backfill, four tests in one file.
- Reuse (reuse brief): parse_marker, _first_text, transcript_lines, _agent_type, role_for, summarize, write_record (agent_usage.py:107,96,45,231,121,69,128); AGENT_ROLES maps the two agent types to impl and review; fixtures usage, assistant, user, write, backfill_fixture (test_agent_usage.py:12,22,32,43,269).
- Do not build (reuse brief): a summariser or record writer (summarize, write_record); a worktree-name splitter (ticket.ticket_names lives in ticket.py; the caller, migrate, builds `names` with it).
- Real prompt shapes (on-disk sample of ~/.claude/projects/-Users-szymonri-Documents-workbench): lean-development-flow implementers and reviewers name `.../docs/plans/in-progress/lean-development-flow/tasks/<task>.md` plus the epic tree `.claude/worktrees/lean-development-flow` (epic only, which matches nothing alone); the epic-integration-worktrees transcripts naming `worktrees/epic-integration-worktrees--<task>` are all worktree-merger, so skipped.
- The phase dir varies (in-progress at run time, done now), so `names` holds `<epic>/tasks/<task>.md` without the phase.
- Stdlib only and Python 3.9 safe (hooks import agent_usage).
- Retro lesson (housekeeping-rules-estimates): quote the lint and suite lines of a run made after `git add` and commit, never a tail read.

- 2026-10-25 amended: interrogate items 1-3: match precedence (task file path, then one tree name), workbench:verifier counts as review, workflow transcripts under <session>/subagents/workflows/wf_*/ (887 of 1042) covered by new AC4; Steps now mean five new tests; points stay 3
