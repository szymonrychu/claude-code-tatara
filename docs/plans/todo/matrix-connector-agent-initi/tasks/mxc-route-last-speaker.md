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
points: 8
expected_minutes: 14
expected_tokens: 3155191
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc route last speaker

## Requirement

README Goal, verbatim: "The user's next chat message after an agent-initiated or follow-up message reaches the session that last spoke in the room while it runs."

Design D9, verbatim:

> The room's target is the running session that last spoke in it (architecture fork 3, pick). `runs.latest_session` becomes a newest-first list of distinct candidate sessions: those with a run in the room or a `sent` send in it, at most 5 per room (my call: bounds the orchestrator lookups per tick). Each session is ordered by when it last spoke in the room (interrogate Act 8): a run counts at the `sent_at` of its last sent `reply` outbound row (its final answer's delivery), or at its `started_at` when no reply row of it was sent yet (my call: notices are the bot's, not the session's, and do not count); a send counts at its `sent_at`; a session's time is the latest of its runs and sends. Tiebreak on equal times: the higher row id wins (my call, pinned by a test). Example pinned by a test: a chat run of session A starts, session B's send is delivered, A's final answer posts, the user replies: the reply goes to A.

> "While it runs" means `agents_common.runs.running_session` reports the session running: it exists and its desired state is active, not that it is mid-turn. The worker walks the candidates first, before any preset check (interrogate Act 1, B5, Q9), and the first running one gets the batch as a normal `follow` run, so the tracker posts its final answer as today. A busy session (for example a hive leader in a long turn) gets the batch as a follow message queued behind its current turn; the tracker follows that message for at most `MATRIX_RUN_TIMEOUT_SECONDS` (default 1800 s, 30 min), and meanwhile the room's later messages stay `new`, because a room with a run in progress is not ready (`inbound.rooms_ready`), as for every run today (Q2). Only when no candidate runs does the preset matter: the room's effective preset (room setting, else default) starts a new `mx-` session under the new-session cap as today, and with no preset the rows are ignored `no_preset` as today.

> `runs.preset_id` of a follow run (interrogate Act 1): the target session's `preset_id` from the `running_session` lookup (`GET /api/v1/sessions/{id}`) the worker already makes; when it is null, the room's effective preset; when that is null too, NULL. Migration 0002 drops NOT NULL on `runs.preset_id` and adds CHECK `kind <> 'first' OR preset_id IS NOT NULL` (my call: an explicit "no preset" rather than a sentinel uuid; a first run still always has one, and no NOT NULL violation is possible). No extra orchestrator call; agents-common is unchanged (a follow run's `RunRef.preset_id` is never read by `deliver`).

> A follow run into a session that has no other run in this room (the run itself excluded) renders the prompt with the PREAMBLE (as a first prompt), because that session never saw the untrusted-input framing (my call). This holds on the first delivery and on every retry through `Worker._resume`, which today renders `first=False` for every follow run (interrogate Act 7).

Design D9, verbatim (MEMORY): "MEMORY amendment (connector MEMORY.md, dated): 2026-10-25 "One agent session per room" becomes "one session per room at a time: the one that last spoke"."

Open question Q2 (approved 2026-10-27, reworded the same day), verbatim: "Your next chat message after an agent starts a chat or sends a follow-up goes to the session that last spoke in the room while it runs ('while it runs' means the session exists with desired state active, not that it is mid-turn), including a hive leader or a webhook or schedule session, as a follow message with its final answer posted to the chat; if that session is busy (for example a hive leader in a long turn), your message waits behind its current turn and the connector tracks the reply for up to 30 min (the run timeout), holding your later messages in that room meanwhile; otherwise it goes to the room's chat session?"

Open question Q9 (pending gate), verbatim: "When the last speaker in a flagged room is a running session, your answer routes there even if the room has no preset; a preset is only needed to start a new chat session (my call, pending gate)?" recommended "yes".

Open question Q10 (pending gate), verbatim: "A session stays bound to a room it posted in; turning agents_may_initiate off does not unbind it; revocation is a deny rule on the room or deleting the session?" recommended "yes".

Interrogate verdict, verbatim: "1. Preset contradiction (B,C high): D9/mxc-route-last-speaker keep `no_preset` before routing while B5/Q9 promise routing to a running last speaker without a preset. Build B5: routing to a running last speaker happens before the preset check; a preset is needed only to start a new mx- session; follow runs need a non-null runs.preset_id: use the target session's preset (GET /api/v1/sessions/{id}); if that is null too, define the value explicitly (no NOT NULL violation possible). ACs pin both paths." "7. Preamble lost on resume (B medium): Worker._resume renders first=False; a follow run into a session new to the room must keep the PREAMBLE on the retry path too, excluding the run itself from "no earlier run in this room". Add Worker._resume to the task and an AC." "8. Last-speaker ordering (B medium): order by when each speaker last spoke in the room: a run counts at its final answer's delivery (outbound sent_at) or its start when no answer was posted yet; a send at its sent_at. AC for: chat run starts, session B sends, chat answer posts, user replies -> chat session."

Scope (agents-matrix-connector): `db/runs.py` (the candidate query replacing `latest_session`, ordered by when each session last spoke; `RunRow.preset_id` and `create_run` accept no preset for a follow run; a query for "this session has another run in this room"), `worker.py` (`Worker._room` walks the candidates before the preset check; follow-run preset rule; PREAMBLE rule in `Worker._deliver`, so `Worker._resume` keeps it), `MEMORY.md` (the dated amendment, with the why), README (how the room's answer is routed, the busy-session hold and that a binding stays until a deny rule or the session is deleted). The `runs.preset_id` nullability itself is migration 0002 (mxc-sends-schema). `tests/test_runs_repo.py::test_create_run_and_latest_session` is no longer accurate (named): it pins `latest_session`, which this task replaces; it is rewritten to pin the candidate query with the same run-creation checks.

## Acceptance conditions

- ac1: the candidates of a room are its distinct sessions with a run or a sent send there, newest first by when each last spoke (a run at its last sent reply row's sent_at, else its started_at; a send at its sent_at; notices not counted), at most 5, with the higher row id winning on equal times (updated) [evidence: test:tests/test_runs_repo.py::test_create_run_and_latest_session]
- ac2: a chat run of session A starts, session B's send is delivered, A's final answer posts, then the user replies: the reply goes to A as a follow run [evidence: test:tests/test_worker.py::test_answer_goes_to_session_that_last_spoke]
- ac3: after a non-mx session's send is delivered to a room, the room's next batch is delivered into that session as a follow run while it runs [evidence: test:tests/test_worker.py::test_answer_goes_to_last_speaker]
- ac4: a candidate that is gone or deleting is skipped for the next one, and with none running a first run creates a new mx- session [evidence: test:tests/test_worker.py::test_gone_speaker_skipped]
- ac5: in a room with no room preset and no default preset, a batch goes to the running last speaker as a follow run, and with no candidate running the rows are ignored no_preset [evidence: test:tests/test_worker.py::test_running_speaker_routes_without_preset]
- ac6: a follow run records the target session's preset_id, the room's effective preset when the session has none, and no preset (NULL) when neither has one, without an error [evidence: test:tests/test_worker.py::test_follow_run_preset_from_session]
- ac7: a follow run into a session with no other run in the room renders the PREAMBLE, and a follow run into the room's own running session does not [evidence: test:tests/test_worker.py::test_preamble_for_session_new_to_room]
- ac8: a follow run into a session new to the room whose first delivery failed (orchestrator unavailable) is retried by Worker._resume with the PREAMBLE, the run itself not counting as an earlier run; a resumed follow run into a session with an earlier run in the room renders no PREAMBLE [evidence: test:tests/test_worker.py::test_resume_keeps_preamble_for_session_new_to_room]
- ac9: the existing worker behaviour (batching, reuse bypassing the cap, session gone fallback, new-session cap, no preset, restart idempotence, typing, receipts) is unchanged [evidence: command:uv run pytest tests/test_worker.py]
- ac10: connector MEMORY.md records the amendment "one session per room at a time: the one that last spoke", dated, with the why [evidence: command:grep -qF "one session per room at a time: the one that last spoke" MEMORY.md]
- ac11: README describes that the room's next message goes to the session that last spoke while it runs, else a new chat session, that a busy session holds the room's later messages until its reply or the run timeout, and that a binding stays until a deny rule or the session is deleted [evidence: command:grep -qi "last spoke" README.md && grep -qi "run timeout" README.md]
- ac12: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_runs_repo.py tests/test_worker.py && mise run lint]

## Files

- `src/agents_matrix_connector/db/runs.py`
- `src/agents_matrix_connector/worker.py`
- `MEMORY.md`
- `README.md`
- `tests/test_worker.py`
- `tests/test_runs_repo.py`

## Interfaces

- `db/runs.py:room_speakers(conn, room_id, limit=5) -> list[uuid.UUID]` (name left to the builder), replacing `latest_session`: sessions ordered by when each last spoke (a run at its last sent `reply` outbound row's `sent_at`, else its `started_at`; a send at its `sent_at`), ties by the higher row id.
- `db/runs.py:RunRow.preset_id: uuid.UUID | None`; `create_run(conn, *, room_id, preset_id: str | None, kind)`; `has_other_run(conn, session_id, room_id, exclude_run_id) -> bool` (name left to the builder).
- `worker.py:Worker._room`: walks the candidates first (`agent_runs.running_session` each); the first running one gets a `follow` run with `preset_id` from that `Session.preset_id`, else the room's effective preset, else None; only with none running does `_preset` decide between a first run and `no_preset`.
- `worker.py:Worker._deliver` decides `first=True` rendering when the session has no other run in the room, so `Worker._resume` (which calls `_deliver` for follow runs) keeps the PREAMBLE; `RunRef.preset_id` of a follow run without a preset is `""` (never read by `deliver`).

## Expected outcome

When an agent started or continued a chat, the user's answer reaches that agent while it runs; otherwise the room behaves as today.

## Steps

- Red: rewrite `test_create_run_and_latest_session`, add the seven worker tests (ac2 to ac8); run `uv run pytest tests/test_runs_repo.py tests/test_worker.py`: the new tests fail.
- Green: query, worker, README, MEMORY; run the task's verify: passes. Quote the summary line with counts.

## Notes

- The equal-time tiebreak is pinned by `test_create_run_and_latest_session` (retro proposal: every tiebreak ruling names a pin test).
- `running_session` already returns `agents_common.orchestrator.Session`, which carries `preset_id` (nullable); no new orchestrator call.
- An `OrchestratorUnavailable` during the candidate walk keeps today's behaviour (log once a minute, retry next tick); an `OrchestratorError` for one candidate skips it.
- The no_preset ignore and the new-session cap now apply only when no candidate runs (interrogate Act 1); their behaviour for a room with no running speaker is unchanged.
- `runs.preset_id` is nullable from migration 0002 (mxc-sends-schema), with a CHECK that first runs keep one.
- The ordering scenario (A starts, B sends, A answers, user replies -> A) is the pin test of the last-spoke rule (`test_answer_goes_to_session_that_last_spoke`).
- MEMORY.md entry format: `- One session per room at a time: the one that last spoke (2026-10-27, epic matrix-connector-agent-initi): ...` amending the 2026-10-25 line, newest first.
- DB-backed tests (CI).

- 2026-10-27 amended: interrogate.md Acts 1, 7, 8 and Q2/Q9/Q10: routing before the preset check, explicit follow preset, PREAMBLE on resume, last-spoke ordering
