---
title: orch ingester reattach
status: done
repo: agents-orchestrator
value: an agent comes back from dead after a pod restart and its queued messages are delivered
files: [src/agents_orchestrator/db/migrations/0009_wrapper_resume.sql, src/agents_orchestrator/db/agents.py, src/agents_orchestrator/reconciler/wrapper_sessions.py, src/agents_orchestrator/ingester/loop.py, tests/test_ingester.py, tests/test_wrapper_session_bootstrap.py, MEMORY.md]
verify: "uv run pytest -q tests/test_ingester.py tests/test_wrapper_session_bootstrap.py tests/test_migrations.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: opus
review: ""
verified_head: 4ca88eacea5f0c226b8b917c505e1991269c8f62
points: 5
expected_minutes: 8
expected_tokens: 1828146
points_actual: 5
actual_minutes: 67
actual_tokens: 7999692
actual_roles: "impl 31, review 35"
actual_role_tokens: "impl 7206272, review 793420"
---

# orch ingester reattach

## Requirement

Design D3, user decision verbatim: "Ingester root cause: the bootstrapper's successful resume becomes a re-attach trigger (e.g. a resume generation/timestamp on the agent row included in AgentRef or equivalent); a stored session_closed is honoured only if no resume happened after it; re-attach replays from the last stored seq (wrapper keeps seq across resume; carto-orchestrator.md item 1). Amend tests/test_ingester.py:723 with the reason. Also mark the agent idle/ready again on re-attach so the dispatcher delivers."

Design D3 (my call), verbatim: ""After it" is decided by database order (the events row id or the database clock), never by comparing the wrapper's event `ts` with the database clock (clock-skew debt recorded by leader-auto-handover)." and "The marker is a new column on `agents` written only by the reconciler (the agents row's writer), in a new migration numbered after the highest one on main when the task runs (0008 today; 0009 if slash-commands-from-chat's `0008_slash_messages.sql` lands first)."

Goal G1, verbatim: "After an agent pod restart and a successful wrapper resume, the ingester re-attaches from the last stored event, the agent leaves `dead`, and queued messages are delivered (the 20:07-20:29 hang cannot recur)."

Scope (agents-orchestrator):
- Migration `src/agents_orchestrator/db/migrations/0009_wrapper_resume.sql` (renumber to the next free number on main): the resume marker column on `agents`.
- `db/agents.py`: write the marker on a successful resume (database clock or a counter); `Agent` carries it.
- `reconciler/wrapper_sessions.py`: both resume paths (the stored session and `_pick`) record the marker; adopt and create do not.
- `ingester/loop.py`: `AgentRef` includes the marker, so `refresh` restarts the stream after a resume; `_stored_closed` honours a stored `session_closed` only when no resume was recorded after it; the re-attach streams from `events.last_seq` (the wrapper continues seq across resume, SSE replay stops at a replayed close, so `after_seq >= close seq` streams live); the attach projects the snapshot state (a resumed `ready` becomes `idle`, `notify_agent_free` fires) so the dispatcher delivers. Module docstring updated (it says `session_closed` ends the task "until the reconciler records a new session").
- Test no longer accurate, to amend: `tests/test_ingester.py::test_session_closed_marks_dead_and_stops` (line 723) still asserts dead and no reconnect when no resume followed the close; its docstring states why the old "until a new session" rule changed (D3).

Interfaces: `AgentRef(agent_id, session_id, wrapper_session_id, url, <marker>)`; `agents_repo.set_wrapper_session(..., resumed=...)` or a separate `mark_resumed`; the migration is additive.

Steps: tests first in `tests/test_ingester.py` and `tests/test_wrapper_session_bootstrap.py`, seen failing (the agent stays dead after a resume); then the migration and code; run the verify.

Notes: DB tests need Docker; PR CI is the evidence. Replayed events below `last_seq` are never re-projected (existing `_store` rule). MEMORY.md: dated entry on the root cause and the marker.

## Acceptance conditions

- AC1: after a resume of the same wrapper session the ingester re-attaches from the last stored seq and stores the later events [evidence: test:tests/test_ingester.py::test_resume_reattaches_from_last_stored_seq]
- AC2: a stored session_closed followed by a recorded resume is not honoured: the agent leaves dead and its stream runs [evidence: test:tests/test_ingester.py::test_closed_before_resume_not_honoured]
- AC3: the re-attach marks a ready agent idle and notifies agent_free so the dispatcher delivers [evidence: test:tests/test_ingester.py::test_reattach_marks_idle_and_notifies]
- AC4: a session_closed with no later resume still marks the agent dead and stops the stream, the test states the reason for the amendment [evidence: test:tests/test_ingester.py::test_session_closed_marks_dead_and_stops]
- AC5: events replayed on a re-attach are not projected again [evidence: test:tests/test_ingester.py::test_reattach_does_not_reproject_replayed_events]
- AC6: both resume paths record the resume marker; adopt and create do not [evidence: test:tests/test_wrapper_session_bootstrap.py::test_successful_resume_records_resume_marker]
- AC7: the migration applies on a fresh and an existing database [evidence: test:tests/test_migrations.py::test_rerun_is_noop]
- AC8: MEMORY.md records the root cause and the fix [evidence: command:grep -q "re-attach" MEMORY.md]
- AC9: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/db/migrations/0009_wrapper_resume.sql`
- `src/agents_orchestrator/db/agents.py`
- `src/agents_orchestrator/reconciler/wrapper_sessions.py`
- `src/agents_orchestrator/ingester/loop.py`
- `tests/test_ingester.py`
- `tests/test_wrapper_session_bootstrap.py`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

- Red: write the tests the requirement and acceptance conditions name (or, for a release/deploy/CI step, the check the evidence names); run `"uv run pytest -q tests/test_ingester.py tests/test_wrapper_session_bootstrap.py tests/test_migrations.py && uv run ruff check . && uv run ruff format --check ."` and see them fail for the expected reason.
- Green: implement the requirement exactly as written; run `"uv run pytest -q tests/test_ingester.py tests/test_wrapper_session_bootstrap.py tests/test_migrations.py && uv run ruff check . && uv run ruff format --check ."` and expect every check to pass, quoting the summary line.
- Refactor with the verify still green; update MEMORY.md with a dated entry for any non-obvious decision.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

- 2026-10-28 done
