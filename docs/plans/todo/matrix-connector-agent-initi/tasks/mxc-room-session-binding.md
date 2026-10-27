---
title: mxc room session binding
status: todo
repo: agents-matrix-connector
value: "each chat room talks to exactly one session: the user's messages always reach the room's bound session, and deleting the session frees the room"
files: [src/agents_matrix_connector/worker.py, src/agents_matrix_connector/db/runs.py, src/agents_matrix_connector/db/bindings.py, MEMORY.md, README.md, tests/test_worker.py, tests/test_runs_repo.py]
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

# mxc room session binding

## Requirement

README Goal, verbatim: "A chat room and a session are bound one to one: a room has at most one bound session and a session at most one bound room, and the user's chat messages in a bound room, including the answer to an agent-initiated or follow-up message, always reach its bound session."

User decision (final gate, 2026-10-27, relayed by the mx-5 leader), verbatim: "1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go". It replaces Q2's last-speaker routing (rejected); this task replaces the retired task mxc-route-last-speaker.

Design D9, verbatim:

> User decision (final gate, 2026-10-27, relayed by the mx-5 leader), verbatim: "1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go". It replaces the last-speaker routing (the architecture's fork 3 pick, rejected with Q2): each chat room is bound to at most one session at a time and that session to exactly that one room; a user message in a bound room always goes to its bound session. There is no last-speaker routing and no room shared by several sessions.

> How a room gets bound: - Inbound chat in an unbound room: the worker's claim transaction of a `first` run reserves the   room (an active `inbound` binding with the run id and no session yet), so no agent can initiate   there while the session is being created; when the run stores its session id   (`_RoomRunStore.set_session`), the same transaction fills the binding's session id and slug   (idempotent for a retried dispatch). A first run that finishes without a session (for example   `preset_not_found` or a refused dispatch) releases its reservation in its finish transaction   (`run_failed`). - Agent initiation in an unbound flagged room: the api accepts the send (D4 (b), advisory); the   bot's sender, in the transaction that claims the send `queued -> sending`, inserts the active   `agent` binding (session id and slug of the send, its send id) when the room is still unbound,   still flagged `agents_may_initiate` and the session still bound to no room. The unique indexes   decide a race: a conflicting insert refuses the send (`room_bound` or `session_bound`), it never   makes a second binding. If that send then ends with none of its outbound rows sent (`failed`, or   `refused` at send time, D7), the settle transaction releases the binding it created   (`send_failed`, my call: a binding message that never reached the user binds nothing). - A send of a session into the room it is bound to binds nothing new.

> Routing a user message (`Worker._room`): the room's active binding decides, before any preset check (interrogate Act 1, B5, Q9): - bound to a session that `agents_common.runs.running_session` reports running (it exists and its   desired state is active, not that it is mid-turn): the batch becomes a `follow` run into it,   whatever its slug (an `mx-` chat session, a hive leader, a webhook or schedule session), and the   tracker posts its final answer as today. A busy session (for example a hive leader in a long   turn) gets the batch queued behind its current turn; the tracker follows that message for at   most `MATRIX_RUN_TIMEOUT_SECONDS` (default 1800 s, 30 min), and meanwhile the room's later   messages stay `new`, because a room with a run in progress is not ready (`inbound.rooms_ready`),   as for every run today. - bound to a session reported gone or deleting (`running_session` returns None): the binding is   released (`session_gone`) and the room is handled as unbound in the same tick. - a refused session check (an `OrchestratorError` other than not found) keeps the binding and   leaves the rows `new`, logged at most once a minute (my call: a hard binding never moves on an   ambiguous answer); an unavailable orchestrator retries next tick as today. - reserved by a first run in progress: nothing to do (the room is not ready anyway). - unbound: only now does the preset matter: the room's effective preset (room setting, else   default) starts a new `mx-` session under the new-session cap as today, which binds the room;   with no preset the rows are ignored `no_preset` as today and the room stays unbound. A delivery that finds the bound session gone (`Worker._session_gone`) releases the binding in the transaction that fails the run `session_gone`, so the next tick starts a new session as today.

> On session delete: the connector learns it from the orchestrator (`running_session` returns None: not found, or desired state `deleting`) and releases the binding (`session_gone`): at once when it routes the room's next batch, and otherwise within about a minute through a binding sweep in `Worker.tick` (at most once per 60 s, my call: one `GET /api/v1/sessions/{id}` per active binding with a session; an unavailable orchestrator ends that sweep, a refused check keeps the binding). After the release the room is unbound: the next user message starts a new `mx-` session (preset needed), and an agent may initiate there if the room is flagged. Nothing else releases a binding: turning `agents_may_initiate` off or adding a deny rule does not unbind (a deny rule still stops every agent send through D4 (a) and every inbound message) (Q10).

> `runs.preset_id` of a follow run (interrogate Act 1): the bound session's `preset_id` from the `running_session` lookup (`GET /api/v1/sessions/{id}`) the worker already makes; when it is null, the room's effective preset; when that is null too, NULL. Migration 0002 drops NOT NULL on `runs.preset_id` and adds CHECK `kind <> 'first' OR preset_id IS NOT NULL` (my call: an explicit "no preset" rather than a sentinel uuid; a first run still always has one, and no NOT NULL violation is possible). No extra orchestrator call; agents-common is unchanged (a follow run's `RunRef.preset_id` is never read by `deliver`).

> A follow run into a session that has no other run in this room (the run itself excluded), for example the first user answer into a session bound by its agent send, renders the prompt with the PREAMBLE (as a first prompt), because that session never saw the untrusted-input framing (my call). This holds on the first delivery and on every retry through `Worker._resume`, which today renders `first=False` for every follow run (interrogate Act 7).

> MEMORY amendment (connector MEMORY.md, dated): 2026-10-25 "One agent session per room" becomes "one session per room and one room per session (hard 1:1 binding in room_bindings), released only when the session is deleted".

Open question Q9 (approved by the user 2026-10-27, adapted to the 1:1 rule), verbatim: "When a room is bound to a running session (for example one that started the chat there through agents_may_initiate), your answer routes to it even if the room has no preset; a preset is only needed to start a new chat session in an unbound room" answer "yes".

Open question Q10 (approved by the user 2026-10-27, adapted to the 1:1 rule), verbatim: "A room stays bound to its one session until that session is deleted (the connector releases the binding at the room's next message or within about a minute); turning agents_may_initiate off or adding a deny rule does not unbind it, though a deny rule still stops every agent send and inbound message" answer "yes".

Interrogate verdict, verbatim: "1. Preset contradiction (B,C high): D9/mxc-route-last-speaker keep `no_preset` before routing while B5/Q9 promise routing to a running last speaker without a preset. Build B5: routing to a running last speaker happens before the preset check; a preset is needed only to start a new mx- session; follow runs need a non-null runs.preset_id: use the target session's preset (GET /api/v1/sessions/{id}); if that is null too, define the value explicitly (no NOT NULL violation possible). ACs pin both paths." (adapted: the bound session takes the place of the last speaker) "7. Preamble lost on resume (B medium): Worker._resume renders first=False; a follow run into a session new to the room must keep the PREAMBLE on the retry path too, excluding the run itself from "no earlier run in this room". Add Worker._resume to the task and an AC."

Scope (agents-matrix-connector): `worker.py` (`Worker._room` routes by the room's active binding before the preset check; the first-run claim reserves the room; `_RoomRunStore.set_session` fills the binding and `_RoomRunStore.finish` releases a reservation without a session; `Worker._session_gone` releases the binding; the 60 s binding sweep in `Worker.tick`; the follow-run preset rule; the PREAMBLE rule in `Worker._deliver`, so `Worker._resume` keeps it), `db/runs.py` (`latest_session` removed; `RunRow.preset_id` and `create_run` accept no preset for a follow run; a query for "this session has another run in this room"), `db/bindings.py` (any query the worker needs beyond mxc-sends-schema's), `MEMORY.md` (the dated amendment, with the why), README (how a room is bound, that the user's messages always go to the bound session, the busy-session hold, and that only deleting the session releases the binding). The `room_bindings` table and `runs.preset_id` nullability are migration 0002 (mxc-sends-schema); the agent-initiated binding is the sender's (mxc-bot-sends-delivery). `tests/test_runs_repo.py::test_create_run_and_latest_session` is no longer accurate (named): it pins `latest_session`, which the binding replaces and this task removes; it becomes `test_create_run`, keeping every run-creation check and dropping only the `latest_session` assertions.

## Acceptance conditions

- ac1: a first run in an unbound room reserves the room's binding in its claim transaction (origin inbound, the run id, no session), and storing the run's session id fills the binding's session id and slug, a retried dispatch with the same id changing nothing [evidence: test:tests/test_worker.py::test_first_run_binds_room]
- ac2: a first run that ends without a session (preset_not_found, a refused dispatch) releases its reservation with reason run_failed, and the room's next batch starts a new first run [evidence: test:tests/test_worker.py::test_failed_first_run_releases_reservation]
- ac3: a room bound to a running session that is not an mx- session (bound by an agent send) gets the next batch as a follow run into that session, before any preset check: also with no room preset and no default preset [evidence: test:tests/test_worker.py::test_bound_session_gets_batch_without_preset]
- ac4: a user message in a bound room never goes to any other session: with another session holding runs in that room and with a newer run of another session elsewhere, the batch goes to the bound session [evidence: test:tests/test_worker.py::test_batch_goes_only_to_bound_session]
- ac5: a bound session reported gone or deleting releases the binding with reason session_gone, and in the same tick the room starts a new mx- session (which binds it) when it has a preset, or ignores the rows no_preset and stays unbound when it has none [evidence: test:tests/test_worker.py::test_gone_bound_session_released]
- ac6: a delivery that finds the bound session gone fails the run session_gone and releases the binding in that transaction, and the next tick starts a new session [evidence: test:tests/test_worker.py::test_session_gone_releases_binding]
- ac7: a refused session check (an OrchestratorError other than not found) keeps the binding and leaves the rows new, and an unavailable orchestrator retries next tick, both without a new session [evidence: test:tests/test_worker.py::test_refused_check_keeps_binding]
- ac8: the binding sweep runs at most once per 60 s, releases with reason session_gone every active binding whose session is gone or deleting, keeps running ones and reservations, and ends early without releasing anything when the orchestrator is unavailable [evidence: test:tests/test_worker.py::test_binding_sweep_releases_deleted_sessions]
- ac9: a follow run records the bound session's preset_id, the room's effective preset when the session has none, and no preset (NULL) when neither has one, without an error [evidence: test:tests/test_worker.py::test_follow_run_preset_from_session]
- ac10: a follow run into a session with no other run in the room renders the PREAMBLE, and a follow run into a session with an earlier run in the room does not [evidence: test:tests/test_worker.py::test_preamble_for_session_new_to_room]
- ac11: a follow run into a session new to the room whose first delivery failed (orchestrator unavailable) is retried by Worker._resume with the PREAMBLE, the run itself not counting as an earlier run; a resumed follow run into a session with an earlier run in the room renders no PREAMBLE [evidence: test:tests/test_worker.py::test_resume_keeps_preamble_for_session_new_to_room]
- ac12: run creation keeps its checks (slug mx-<id>, no session or message, integer id, other kinds refused) and latest_session no longer exists (updated) [evidence: test:tests/test_runs_repo.py::test_create_run]
- ac13: the existing worker behaviour (batching, reuse bypassing the cap, session gone fallback, new-session cap, no preset, restart idempotence, typing, receipts) is unchanged [evidence: command:uv run pytest tests/test_worker.py]
- ac14: connector MEMORY.md records the amendment "one session per room and one room per session", dated, with the why [evidence: command:grep -qF "one session per room and one room per session" MEMORY.md]
- ac15: README describes the 1:1 binding: how a room is bound (an inbound chat starting a session, an agent initiating in an unbound flagged room), that the user's messages always go to the bound session, that a busy session holds the room's later messages until its reply or the run timeout, and that only deleting the session releases the binding [evidence: command:grep -qi "one room per session" README.md && grep -qi "run timeout" README.md && grep -qi "session is deleted" README.md]
- ac16: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_runs_repo.py tests/test_worker.py && mise run lint]

## Files

- `src/agents_matrix_connector/worker.py`
- `src/agents_matrix_connector/db/runs.py`
- `src/agents_matrix_connector/db/bindings.py`
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
