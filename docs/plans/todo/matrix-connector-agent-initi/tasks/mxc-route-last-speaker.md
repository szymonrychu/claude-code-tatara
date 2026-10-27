---
title: mxc route last speaker
status: todo
repo: agents-matrix-connector
value: "the user's answer reaches the agent that last spoke in the chat while it runs"
files: [src/agents_matrix_connector/db/runs.py, src/agents_matrix_connector/worker.py, MEMORY.md, README.md, tests/test_worker.py, tests/test_runs_repo.py]
verify: "uv run pytest tests/test_runs_repo.py tests/test_worker.py && mise run lint"
depends_on: [mxc-sends-schema, mxc-bot-sends-delivery]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 9
expected_tokens: 1836811
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc route last speaker

## Requirement

README Goal, verbatim: "The user's next chat message after an agent-initiated or follow-up message reaches the session that last spoke in the room while it runs."

Design D9, verbatim: "The room's target is the newest running session among those that started a run in it or had a send delivered in it (architecture fork 3, pick). `runs.latest_session` becomes a newest-first list of distinct candidate sessions ordered by their latest activity in the room (run `started_at`, send `sent_at`), at most 5 per room (my call: bounds the orchestrator lookups per tick); the worker takes the first one `agents_common.runs.running_session` reports running, else falls back to a new `mx-` session as today. The batch goes in as a normal `follow` run, so the tracker posts its final answer as today. Tiebreak on equal times: the higher row id wins (my call, pinned by a test).

`runs.preset_id` (NOT NULL) of a follow run (settled here): the target session's `preset_id` from the `running_session` lookup the worker already makes; when it is null, the room's effective preset (room setting, else default) the worker resolved first. No migration change, no extra orchestrator call. A room without any preset still ignores its rows `no_preset` before routing (unchanged).

A follow run into a session that has no earlier run in this room renders the prompt with the PREAMBLE (as a first prompt), because that session never saw the untrusted-input framing (my call).

MEMORY amendment (connector MEMORY.md, dated): 2026-10-25 "One agent session per room" becomes "one session per room at a time: the one that last spoke"."

Open question Q2 (pending gate), verbatim: "Your answer after an agent starts a chat goes to that session while it runs, otherwise to the room's chat session (my call, pending gate)?" recommended "yes".

Scope (agents-matrix-connector): `db/runs.py` (the candidate query replacing `latest_session`), `worker.py` (`Worker._room` walks the candidates; follow-run preset and PREAMBLE rules), `MEMORY.md` (the dated amendment, with the why), README (how the room's answer is routed). `tests/test_runs_repo.py::test_create_run_and_latest_session` is no longer accurate (named): it pins `latest_session`, which this task replaces; it is rewritten to pin the candidate query with the same run-creation checks.

## Acceptance conditions

- ac1: the candidates of a room are its distinct sessions newest first by latest activity (run started_at, sent send sent_at), at most 5, with the higher row id winning on equal times (updated) [evidence: test:tests/test_runs_repo.py::test_create_run_and_latest_session]
- ac2: after a non-mx session's send is delivered to a room, the room's next batch is delivered into that session as a follow run while it runs [evidence: test:tests/test_worker.py::test_answer_goes_to_last_speaker]
- ac3: a candidate that is gone or deleting is skipped for the next one, and with none running a first run creates a new mx- session [evidence: test:tests/test_worker.py::test_gone_speaker_skipped]
- ac4: a follow run records the target session's preset_id, and the room's effective preset when the session has none [evidence: test:tests/test_worker.py::test_follow_run_preset_from_session]
- ac5: a follow run into a session with no earlier run in the room renders the PREAMBLE, and a follow run into the room's own running session does not [evidence: test:tests/test_worker.py::test_preamble_for_session_new_to_room]
- ac6: the existing worker behaviour (batching, reuse bypassing the cap, session gone fallback, new-session cap, no preset, restart idempotence, typing, receipts) is unchanged [evidence: command:uv run pytest tests/test_worker.py]
- ac7: connector MEMORY.md records the amendment "one session per room at a time: the one that last spoke", dated, with the why [evidence: command:grep -qF "one session per room at a time: the one that last spoke" MEMORY.md]
- ac8: README describes that the room's next message goes to the session that last spoke while it runs, else a new chat session [evidence: command:grep -qi "last spoke" README.md]
- ac9: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_runs_repo.py tests/test_worker.py && mise run lint]

## Files

- `src/agents_matrix_connector/db/runs.py`
- `src/agents_matrix_connector/worker.py`
- `MEMORY.md`
- `README.md`
- `tests/test_worker.py`
- `tests/test_runs_repo.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
