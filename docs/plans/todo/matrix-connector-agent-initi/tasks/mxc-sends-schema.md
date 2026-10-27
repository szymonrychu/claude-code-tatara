---
title: mxc sends schema
status: todo
repo: agents-matrix-connector
value: "agent sends get a queue, a room flag, a database-enforced 1:1 room-session binding and the reference queries every later task needs"
files: [src/agents_matrix_connector/migrations/0002_agent_sends.sql, src/agents_matrix_connector/db/sends.py, src/agents_matrix_connector/db/bindings.py, tests/test_schema.py, tests/test_sends_repo.py, tests/test_bindings_repo.py]
verify: "uv run pytest tests/test_schema.py tests/test_sends_repo.py tests/test_bindings_repo.py && mise run lint"
depends_on: []
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

# mxc sends schema

## Requirement

README Goals, verbatim:
- "An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn."
- "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."
- "A chat room and a session are bound one to one: a room has at most one bound session and a session at most one bound room, and the user's chat messages in a bound room, including the answer to an agent-initiated or follow-up message, always reach its bound session."

User decision (final gate, 2026-10-27), verbatim: "1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go".

Design D7, verbatim (the schema part): "`sends` (new queue, COMMENT `queue: inserted by api, transitions by bot worker`): `id bigserial`, `session_id uuid NOT NULL`, `slug text NULL`, `kind` CHECK `message|reaction`, `room_id text NOT NULL`, `text text NULL`, `key text NULL`, `reply_to text NULL` (the `m<n>`/`s<n>` the agent gave), `ref_event_id text NULL`, `event_id text NULL`, `status` CHECK `queued|sending|sent|failed|refused`, `reason text NULL`, `created_at`, `claimed_at`, `sent_at`; indexes for queued rows, per session and time (rate), and per room and status. `outbound` keeps the bot worker as its only writer and gains `send_id bigint NULL`, `event_type text NOT NULL DEFAULT 'm.room.message'`, `relates_to jsonb NULL`; its kind CHECK gains `agent` and `reaction`. `runs` gets an index on `(session_id, room_id)` for the "other run of this session in this room" check (D9 PREAMBLE), and `runs.preset_id` drops NOT NULL with a new CHECK `kind <> 'first' OR preset_id IS NOT NULL` (D9). `room_settings` gains `agents_may_initiate`. The same migration creates `room_bindings` with its two partial unique indexes and the backfill (D9)."

Design D9, verbatim (storage): "Storage: the uniqueness lives in the connector's own database. Migration 0002 creates `room_bindings` (COMMENT `writer: bot worker`): `id bigserial`, `room_id text NOT NULL`, `session_id uuid NULL`, `slug text NULL`, `origin` CHECK `inbound|agent`, `run_id bigint NULL` (the first run that bound it), `send_id bigint NULL` (the send that bound it), `created_at`, `released_at timestamptz NULL`, `release_reason text NULL`. A binding is active while `released_at` is NULL. A partial unique index on `room_id WHERE released_at IS NULL` and one on `session_id WHERE released_at IS NULL AND session_id IS NOT NULL` make two active bindings of one room, or of one session, impossible; CHECKs: an `inbound` binding has a `run_id`, an `agent` binding a `session_id` and a `send_id`. The bot worker (its worker and sender steps, one bot process) is the only writer; the api only reads it. A release is a guarded UPDATE (`released_at IS NULL`, plus the expected session); released rows stay as history and are pruned with the daily retention (my call). `runs.latest_session` is removed: the binding replaces it."

Design D9, verbatim (backfill): "Backfill (my call, gate question Q12): 0002 inserts one active `inbound` binding per room from its newest run that has a session (its session id, slug and run id), or a reservation for a room whose newest run is an in-progress first run without a session yet, so existing chats keep their session. A session that is the newest of several rooms (not expected: the worker creates one `mx-` session per room) binds only the room of its newest run. A backfilled binding of a session already deleted is released by the first binding sweep (below)."

Design D9, verbatim (the binding writes this repository serves): "the worker's claim transaction of a `first` run reserves the room (an active `inbound` binding with the run id and no session yet) [...] when the run stores its session id (`_RoomRunStore.set_session`), the same transaction fills the binding's session id and slug (idempotent for a retried dispatch). A first run that finishes without a session [...] releases its reservation in its finish transaction (`run_failed`)." "the bot's sender, in the transaction that claims the send `queued -> sending`, inserts the active `agent` binding (session id and slug of the send, its send id) when the room is still unbound, still flagged `agents_may_initiate` and the session still bound to no room. The unique indexes decide a race: a conflicting insert refuses the send (`room_bound` or `session_bound`), it never makes a second binding."

Design D4, verbatim (binding): "Bound means an active `room_bindings` row pairing R and S (D9); nothing else binds (no `runs` or `sends` row is read as a binding, and the api writes no binding). A room reserved by another session's first run in progress (an active binding without a session yet, D9) counts as bound to another session. `room_settings.agents_may_initiate boolean NOT NULL DEFAULT false` is new; its writer stays the api."

Design D6, verbatim (resolution): "The connector resolves `m<n>` to the inbound row's `event_id` and `s<n>` to the send's delivered `event_id` (first chunk of a message, the reaction event of a reaction)."

Design D5, verbatim (rate count): "at most `MATRIX_AGENT_RATE_PER_MINUTE` (default 20, gate question Q5) sends (messages and reactions together) per session in the last 60 s, counted on `sends` rows of any status".

Design D7, verbatim (retention): "`sends` rows that ended and released `room_bindings` rows are pruned with the existing daily retention."

Design D9, verbatim (preset): "Migration 0002 drops NOT NULL on `runs.preset_id` and adds CHECK `kind <> 'first' OR preset_id IS NOT NULL` (my call: an explicit "no preset" rather than a sentinel uuid; a first run still always has one, and no NOT NULL violation is possible)."

Open question Q12 (pending), verbatim: "Migration 0002 (approved, no down step) also creates room_bindings and backfills one active binding per room from its newest run that has a session, or reserves the room for an in-progress first run without one, so existing chats keep their session; bindings of sessions already deleted are released by the bot's first binding sweep. Approve that backfill as part of migration 0002?" recommended "yes".

Scope (agents-matrix-connector): migration `0002_agent_sends.sql`, the repository module `db/sends.py` (insert, claim, guarded transitions, rate count, reference resolution, prune) and the new repository module `db/bindings.py` (reserve, fill, bind for a send, release, active lookups by room and by session, the active list for the sweep, prune of released rows). The api routes, the bot step and the routing change are later tasks.

`tests/test_schema.py::test_writer_comments` and `tests/test_schema.py::test_check_constraints` are no longer accurate once the new tables and the widened `outbound.kind` CHECK exist (named): they list every table's writer and the accepted kinds; both are extended to the new tables and kinds, nothing they assert today is removed.

## Acceptance conditions

- ac1: migration 0002 creates `sends` with the D7 columns and its COMMENT names the api as inserter and the bot worker as the only mover, and `room_bindings` with the D9 columns and COMMENT `writer: bot worker` (updated) [evidence: test:tests/test_schema.py::test_writer_comments]
- ac2: the `sends.kind` and `sends.status` CHECKs and the `room_bindings.origin` CHECK refuse other values, and `outbound.kind` accepts agent and reaction besides reply and notice (updated) [evidence: test:tests/test_schema.py::test_check_constraints]
- ac3: applying the migrations twice changes nothing [evidence: test:tests/test_schema.py::test_migration_idempotent]
- ac4: `room_settings.agents_may_initiate` is NOT NULL with default false; `outbound` has `send_id`, `event_type` defaulting to m.room.message and `relates_to` jsonb; the runs `(session_id, room_id)` index exists [evidence: test:tests/test_schema.py::test_agent_sends_columns]
- ac5: a queued send is claimed once (queued to sending), and sent, failed and refused are reached only from sending, every move through `agents_common.db.queue.transition`; a second claim or a move from the wrong status changes nothing [evidence: test:tests/test_sends_repo.py::test_guarded_transitions]
- ac6: the database refuses a second active binding of one room and a second active binding of one session, while released bindings of that room or session do not count; an inbound binding without a run id and an agent binding without a session id or a send id are refused [evidence: test:tests/test_bindings_repo.py::test_one_active_binding_per_room_and_session]
- ac7: reserving a room for a first run, filling its session id and slug (twice with the same id is a no-op) and releasing it with a reason work through guarded updates; a reservation of an already bound room, a fill of a released binding and a second release change nothing [evidence: test:tests/test_bindings_repo.py::test_reserve_fill_release]
- ac8: binding a room for a send answers bound for an unbound room and a session bound to no room, already for the session's own room, room_bound for a room bound to or reserved by another session and session_bound for a session bound elsewhere, writing a row only in the first case [evidence: test:tests/test_bindings_repo.py::test_bind_for_send_outcomes]
- ac9: the active binding of a room and of a session, and the list of active bindings with a session, are read back exactly; no runs or sends row counts as a binding [evidence: test:tests/test_bindings_repo.py::test_active_lookups]
- ac10: applying 0002 over a 0001 database binds each room to the session of its newest run that has one, reserves a room whose newest run is an in-progress first run without a session, binds a session newest in two rooms only to the room of its newest run, and binds nothing for a room without runs [evidence: test:tests/test_schema.py::test_binding_backfill]
- ac11: the rate count counts a session's sends of any status and kind created in the last 60 s and no older ones [evidence: test:tests/test_sends_repo.py::test_rate_count_window]
- ac12: `m<n>` resolves to that inbound row's event_id and room; `s<n>` resolves to that send's room, session, kind, status and event_id; an unknown or malformed reference resolves to nothing [evidence: test:tests/test_sends_repo.py::test_resolve_references]
- ac13: prune deletes sent, failed and refused sends older than the cutoff and keeps queued and sending ones [evidence: test:tests/test_sends_repo.py::test_prune_ended_sends]
- ac14: the bindings prune deletes released bindings released before the cutoff and keeps active ones and newer released ones [evidence: test:tests/test_bindings_repo.py::test_prune_released_bindings]
- ac15: `runs.preset_id` accepts NULL for a follow run and the CHECK refuses a first run without a preset [evidence: test:tests/test_schema.py::test_follow_run_preset_nullable]
- ac16: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_schema.py tests/test_sends_repo.py tests/test_bindings_repo.py && mise run lint]

## Files

- `src/agents_matrix_connector/migrations/0002_agent_sends.sql`
- `src/agents_matrix_connector/db/sends.py`
- `src/agents_matrix_connector/db/bindings.py`
- `tests/test_schema.py`
- `tests/test_sends_repo.py`
- `tests/test_bindings_repo.py`

## Interfaces

- `src/agents_matrix_connector/migrations/0002_agent_sends.sql`: table `sends` (D7 columns), `outbound` new columns, widened kind CHECK, `room_settings.agents_may_initiate`, indexes, `runs.preset_id` DROP NOT NULL plus CHECK `kind <> 'first' OR preset_id IS NOT NULL`; table `room_bindings` (D9 columns, origin CHECK, the inbound/agent CHECKs, partial unique indexes `(room_id) WHERE released_at IS NULL` and `(session_id) WHERE released_at IS NULL AND session_id IS NOT NULL`) and its backfill; COMMENTs on `sends` and `room_bindings`.
- `src/agents_matrix_connector/db/sends.py` (new): a frozen `SendRow` dataclass; `insert(conn, *, session_id, slug, kind, room_id, text, key, reply_to, ref_event_id) -> int`; `claim_queued(conn) -> list[SendRow]` (queued to sending, sets `claimed_at`); `mark_sent(conn, id, event_id)`, `mark_failed(conn, id, reason)`, `mark_refused(conn, id, reason)` through `queue.transition`; `count_recent(conn, session_id, seconds) -> int`; `resolve(conn, ref) -> Ref | None` for `m<n>`/`s<n>`; `get(conn, id) -> SendRow | None`; `prune(conn, older_than) -> int`. No binding query here: the binding is `db/bindings.py`.
- `src/agents_matrix_connector/db/bindings.py` (new, writer: bot worker; names left to the builder): a frozen `BindingRow(id, room_id, session_id, slug, origin, run_id, send_id, created_at, released_at, release_reason)`; `reserve_for_run(conn, room_id, run_id) -> bool`; `fill_session(conn, run_id, session_id, slug) -> bool` (idempotent for the same id); `bind_for_send(conn, *, room_id, session_id, slug, send_id) -> Literal["bound", "already", "room_bound", "session_bound"]` (a unique violation maps to the matching refusal inside a savepoint, never an exception for the caller's transaction); `release(conn, binding_id, reason, *, session_id=None) -> bool` (guarded on `released_at IS NULL` and the expected session); `active_for_room(conn, room_id) -> BindingRow | None`; `active_for_session(conn, session_id) -> BindingRow | None`; `active_with_session(conn) -> list[BindingRow]` (the sweep); `prune_released(conn, older_than) -> int`. Writers take a connection and never commit, as in `db/runs.py`; the api uses only the readers.

## Expected outcome

The connector database holds the agent send queue, the room flag and the room-session bindings, and the database itself refuses a second active binding of a room or of a session; two repository modules offer every query the api, the bot step and the routing change need; existing chats keep their session through the backfill.

## Steps

- Red: add `test_agent_sends_columns`, `test_binding_backfill`, extend `test_writer_comments` and `test_check_constraints`, write `tests/test_sends_repo.py` and `tests/test_bindings_repo.py`; run `uv run pytest tests/test_schema.py tests/test_sends_repo.py tests/test_bindings_repo.py`: the new tests fail (no tables, no modules).
- Green: write the migration, `db/sends.py` and `db/bindings.py`; run the task's verify: passes. Quote the summary line with counts.

## Notes

- DB tests use testcontainers (Docker); agent pods have none, so they run in GitHub CI (retro proposal: CI is the DB gate). Keep the reference parser (`m<n>`/`s<n>` to kind and id) and the mapping of a unique-index name to `room_bound`/`session_bound` pure functions with their own non-DB tests so the local run has signal.
- Reuse `agents_common.db.queue.transition` exactly as `db/runs.py` does; no raw UPDATE of `sends.status`. `room_bindings` is not a queue; its release is still one guarded UPDATE (`released_at IS NULL`).
- Writers: the api only inserts `sends`; the bot only moves them (D7); `room_bindings` is written only by the bot worker (D9), the api only reads it. Record the writers in the COMMENTs.
- `test_binding_backfill` applies `0001_init.sql`, seeds runs, then applies `0002_agent_sends.sql` on a fresh database; the tiebreak "a session newest in two rooms binds only its newest run's room" is a ruling and this test is its pin (retro proposal).
- The backfill is part of the approved migration 0002 (no down step); gate question Q12 (recommended yes) settles it. The task builds it as recommended; Q12 must be answered before the live apply (chat-live-smoke), and a "no" removes ac10 and the backfill by amend before then.
- Follow `db/runs.py` and `db/inbound.py` style (dict_row, frozen dataclasses, connection-taking writers).

- 2026-10-27 amended: interrogate.md Act 1: runs.preset_id nullable for follow runs with a CHECK that first runs keep one

- 2026-10-27 amended: final gate 2026-10-27: hard 1:1 room-session binding replaces last-speaker routing (D9): room_bindings table, unique indexes, backfill, db/bindings.py
