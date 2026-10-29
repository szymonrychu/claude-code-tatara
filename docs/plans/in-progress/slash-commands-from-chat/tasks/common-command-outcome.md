---
title: common command outcome
status: done
repo: agents-common
value: "webhook and schedule runs whose prompt is a slash command finish handled or failed by the command's outcome instead of timing out"
files: [src/agents_common/orchestrator.py, src/agents_common/runs.py, src/agents_common/fake_orchestrator.py, tests/test_runs.py, tests/test_orchestrator_client.py, README.md]
verify: "uv run pytest tests/test_runs.py tests/test_orchestrator_client.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [orch-command-outcome]
model: opus
review: ""
verified_head: 4d495171ff9cd299a132f7082909896995bb232c
points: 3
expected_minutes: 8
expected_tokens: 996161
points_actual: 3
actual_minutes: 3
actual_tokens: 740467
actual_roles: "impl 3, review 1"
actual_role_tokens: "impl 635662, review 104805"
---

# common command outcome

## Requirement

User decision F2 (2026-10-29), verbatim: "F2: read-side command outcome on MessageView (orchestrator, migration 0012 partial index; check the next free migration number on the rebased orchestrator branch at /workdir/workdir/.claude/worktrees/slash-commands-from-chat/agents-orchestrator, which contains main's 0011), agents-common run tracker handles kind=command outcomes per the architect's mapping, agents-common release v0.4.0 (tag pending mx-34 confirmation; write the task so the orchestrator session pushes the tag after confirmation), then pin bumps in agents-webhook and agents-schedule."

Architect brief, verbatim: "6. `common-command-outcome` (agents-common)
   - Files: `orchestrator.py` (new `Message.command`), `runs.py` (`track`), `fake_orchestrator.py` (new `complete_command` and `fail_command`).
   - Mapping in `track`:

     | Command outcome | Run result |
     |---|---|
     | completed: ok, dismissed, skipped_cache | handled |
     | failed (e.g. unknown_command, dialog_stuck, timeout) | failed, reason `command_<error>` |
     | cancelled | failed, reason `command_cancelled` |
     | completed with result `turn` | decided by the existing turn checks |

   - Tests in `tests/test_runs.py`: `test_track_command_completed_is_handled`, `test_track_command_failed_reason_is_error_code`, `test_track_command_cancelled_is_failed`, `test_track_promoted_command_waits_for_turn`, `test_track_command_pending_times_out`."

Design D20, verbatim: "A command with no outcome yet keeps waiting and ends `timeout` as today; a failed outcome with no error code reads `command_failed` (my call). `fake_orchestrator` gains `complete_command` and `fail_command`."

The wire shape is the orchestrator's `MessageView.command` (task orch-command-outcome, design D19): null, or `{state, result, error, turn_id, at}` with `state` one of `completed`, `failed`, `cancelled`.

Scope (agents-common, branch from origin `main`): `src/agents_common/orchestrator.py` (new `CommandOutcome` model, `Message.command: CommandOutcome | None = None`), `src/agents_common/runs.py` (`track` per the mapping), `src/agents_common/fake_orchestrator.py` (`complete_command(message_id, result="ok", turn_id=None)` marks the message `sent` with a completed outcome; `fail_command(message_id, error, state="failed")` with `state` `failed` or `cancelled` marks it `sent` with that outcome), `tests/test_runs.py`, `tests/test_orchestrator_client.py` (the client parses `command`), README.md (`## runs`: `track` judges a command message by its outcome, with the reasons).

## Acceptance conditions

- ac1: a command message completed with result ok, dismissed or skipped_cache finishes the run handled with no reason (new) [evidence: test:tests/test_runs.py::test_track_command_completed_is_handled]
- ac2: a failed command with error unknown_command, dialog_stuck or timeout finishes the run failed with reason command_unknown_command, command_dialog_stuck or command_timeout; a failed outcome with no error reads command_failed (new) [evidence: test:tests/test_runs.py::test_track_command_failed_reason_is_error_code]
- ac3: a cancelled command finishes the run failed with reason command_cancelled (new) [evidence: test:tests/test_runs.py::test_track_command_cancelled_is_failed]
- ac4: a command completed with result turn is decided by the turn: running returns None, a completed turn is handled, a failed turn is turn_failed (new) [evidence: test:tests/test_runs.py::test_track_promoted_command_waits_for_turn]
- ac5: a sent command message with no outcome returns None until the timeout, then finishes failed timeout (new) [evidence: test:tests/test_runs.py::test_track_command_pending_times_out]
- ac6: the existing turn mapping is unchanged [evidence: test:tests/test_runs.py::test_track_completed_is_handled]
- ac7: the client parses Message.command from the fake's message view, and it is None for a turn message (new) [evidence: test:tests/test_orchestrator_client.py::test_message_command_outcome_roundtrip]
- ac8: README names the command reasons [evidence: command:grep -q "command_cancelled" README.md]
- ac9: the named tests and lint pass [evidence: command:uv run pytest tests/test_runs.py tests/test_orchestrator_client.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_common/orchestrator.py`
- `src/agents_common/runs.py`
- `src/agents_common/fake_orchestrator.py`
- `tests/test_runs.py`
- `tests/test_orchestrator_client.py`
- `README.md`

## Interfaces

- `agents_common.orchestrator.CommandOutcome(_Model)`: `state: str`, `result: str | None = None`, `error: str | None = None`, `turn_id: str | None = None`, `at: datetime | None = None`; `Message.command: CommandOutcome | None = None`.
- `agents_common.runs.track(...)`: same signature and return; order of checks: completed turn -> handled; message failed/cancelled -> `message_<status>`; failed turn -> `turn_failed`; command outcome (when `turn` is None and the outcome is not completed with result `turn`) -> handled / `command_<error>` / `command_failed` / `command_cancelled`; timeout.
- `FakeOrchestrator.complete_command(message_id: int, result: str = "ok", turn_id: str | None = None) -> None`; `FakeOrchestrator.fail_command(message_id: int, error: str | None, state: str = "failed") -> None` (`state` `failed` or `cancelled`).

## Expected outcome

A run whose prompt the orchestrator stored as a command finishes by the command's outcome instead of waiting for a turn until `timeout`.

## Steps

- Red: write the five `test_track_command_*`/`test_track_promoted_command_waits_for_turn` tests and `test_message_command_outcome_roundtrip`; run `uv run pytest tests/test_runs.py tests/test_orchestrator_client.py`: they fail (no `complete_command`).
- Green: model, fake methods, `track` mapping, README; run the task's verify. Quote the summary line.

## Notes

- `track_delivery` (reuse path) already finishes on `sent`; unchanged.
- A promoted command (result `turn`) gets its `turn` from the orchestrator's turn link (orch-command-turn-link), so the existing turn checks decide it.
- Wire shape from orch-command-outcome (design D19). The todo epic immediate-message-delivery-w also edits `orchestrator.py` and `fake_orchestrator.py` (`Message.turn_id`) and plans agents-common 0.4.0; it rebases on this and renumbers its release when claimed.
- `model` is opus by the file-count rule (6 files).

- 2026-10-29 done
