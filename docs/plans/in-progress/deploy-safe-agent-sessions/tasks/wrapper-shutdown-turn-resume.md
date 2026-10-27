---
title: wrapper shutdown turn resume
status: in-progress
repo: claude-code-wrapper
value: a turn cut off by a pod restart continues instead of being lost
files: [src/claude_code_wrapper/manager.py, src/claude_code_wrapper/session.py, src/claude_code_wrapper/turns.py, src/claude_code_wrapper/router.py, tests/test_shutdown_turn_resume.py, README.md]
verify: "uv run pytest -q tests/test_shutdown_turn_resume.py tests/test_e2e_resume.py tests/test_turn_continuity.py tests/test_session_turns.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 8
expected_tokens: 1828146
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper shutdown turn resume

## Requirement

Design D5, user decision verbatim: "Wrapper: a turn interrupted by service shutdown is recorded distinguishably from a user stop/delete; on resume (API resume and load_persisted) such a turn is continued with restart_continue_prompt when configured; the orchestrator renders a default restart_continue_prompt (render.py:130). Wrapper gets a release tag (next patch, 0.3.2) and pyproject version fixed to match."

Design D5 (my call), verbatim: "Mechanism: on service shutdown the running turn stays `running` in turns.jsonl with a marker (`interrupted: "shutdown"`), no `turn_failed` is emitted; a user stop or delete keeps ending it `failed` with `session_stopped`. On resume with `restart_continue_prompt` set, the fresh Session adopts that record and continues the same `turn_id` (a `turn_resumed` event, cause `resume`), so the orchestrator's turn row and message complete normally; without the prompt it ends `failed` with error `service_shutdown`. A turn left `running` by a killed process is treated the same way. Alternative rejected: end the turn `failed` at shutdown and start a new turn on resume (the orchestrator would record a failure and the message would not complete)."

Goal G4, verbatim: "A wrapper session resumed after a shutdown that interrupted a turn continues that turn with the continue prompt, and the orchestrator renders a default continue prompt."

Scope (claude-code-wrapper):
- `manager.py`: `shutdown` stops sessions with cause shutdown; `resume` and `load_persisted` hand an interrupted `running` record (TurnStore.current) to the fresh Session.
- `session.py`: `stop(grace, cause=...)` keeps the turn running with the marker on shutdown and ends it `session_stopped` otherwise; a resumed Session holds the record and, once ready, continues it with `continue_turn` (reuse `_continue_held`), or fails it `service_shutdown` when no prompt is configured.
- `turns.py`: the marker persisted in turns.jsonl (a `TurnRecord` field or equivalent) and readable after a restart.
- `router.py`: `turn_resumed` with cause `resume` (the in-process relaunch keeps cause `restart`).
- README: the turn states, the marker, `service_shutdown` and the resume continuation.
- `tests/test_shutdown_turn_resume.py` (new), fake claude only.

Steps: tests first, seen failing; then the code; run the verify.

Notes: the event seq continues across resume (`events.py:157-158`); the orchestrator's re-attach (task orch-ingester-reattach) relies on it, pin it here. In-progress epic slash-commands-from-chat also edits `session.py`, `manager.py` and `router.py`: rebase on its merge first. Only the fake-claude task edits `tests/conftest.py` (repo convention).

## Acceptance conditions

- AC1: a graceful service shutdown during a turn leaves the turn running with the shutdown marker and emits no turn_failed [evidence: test:tests/test_shutdown_turn_resume.py::test_shutdown_marks_running_turn_interrupted]
- AC2: a user stop or delete of a busy session still ends the turn failed session_stopped and it is never continued [evidence: test:tests/test_shutdown_turn_resume.py::test_user_stop_turn_not_continued]
- AC3: an API resume with restart_continue_prompt continues the same turn_id with the prompt, emits turn_resumed cause resume, and the turn completes [evidence: test:tests/test_shutdown_turn_resume.py::test_api_resume_continues_interrupted_turn]
- AC4: load_persisted with resume_on_start continues a turn a killed process left running [evidence: test:tests/test_shutdown_turn_resume.py::test_load_persisted_continues_interrupted_turn]
- AC5: a resume without restart_continue_prompt ends the interrupted turn failed with service_shutdown [evidence: test:tests/test_shutdown_turn_resume.py::test_resume_without_prompt_fails_interrupted_turn]
- AC6: the event seq continues across shutdown and resume [evidence: test:tests/test_shutdown_turn_resume.py::test_event_seq_continues_across_resume]
- AC7: README documents the marker and service_shutdown [evidence: command:grep -q "service_shutdown" README.md]
- AC8: the resume, continuity and turn suites pass [evidence: command:uv run pytest -q tests/test_e2e_resume.py tests/test_turn_continuity.py tests/test_session_turns.py tests/test_manager.py tests/test_command_turn_resume.py]
- AC9: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/manager.py`
- `src/claude_code_wrapper/session.py`
- `src/claude_code_wrapper/turns.py`
- `src/claude_code_wrapper/router.py`
- `tests/test_shutdown_turn_resume.py`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
