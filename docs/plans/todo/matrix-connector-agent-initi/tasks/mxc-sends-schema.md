---
title: mxc sends schema
status: todo
repo: agents-matrix-connector
value: "agent sends get a queue, a room flag and the binding and reference queries every later task needs"
files: [src/agents_matrix_connector/migrations/0002_agent_sends.sql, src/agents_matrix_connector/db/sends.py, tests/test_schema.py, tests/test_sends_repo.py]
verify: "uv run pytest tests/test_schema.py tests/test_sends_repo.py && mise run lint"
depends_on: []
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

# mxc sends schema

## Requirement

README Goals, verbatim:
- "An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn."
- "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."

Design D7, verbatim (the schema part): "`sends` (new queue, COMMENT `queue: inserted by api, transitions by bot worker`): `id bigserial`, `session_id uuid NOT NULL`, `slug text NULL`, `kind` CHECK `message|reaction`, `room_id text NOT NULL`, `text text NULL`, `key text NULL`, `reply_to text NULL` (the `m<n>`/`s<n>` the agent gave), `ref_event_id text NULL`, `event_id text NULL`, `status` CHECK `queued|sending|sent|failed|refused`, `reason text NULL`, `created_at`, `claimed_at`, `sent_at`; indexes for queued rows, per session and time (rate), and per room and status (binding, last speaker). `outbound` keeps the bot worker as its only writer and gains `send_id bigint NULL`, `event_type text NOT NULL DEFAULT 'm.room.message'`, `relates_to jsonb NULL`; its kind CHECK gains `agent` and `reaction`. `runs` gets an index on `(session_id, room_id)` for the binding check. `room_settings` gains `agents_may_initiate`."

Design D4, verbatim (binding): "Bound means a `runs` row of R with `session_id` S, or a `sends` row of R with `session_id` S and status `sent` (my call: a refused, failed or still queued send binds nothing). `room_settings.agents_may_initiate boolean NOT NULL DEFAULT false` is new; its writer stays the api."

Design D6, verbatim (resolution): "The connector resolves `m<n>` to the inbound row's `event_id` and `s<n>` to the send's delivered `event_id` (first chunk of a message, the reaction event of a reaction)."

Design D5, verbatim (rate count): "at most `MATRIX_AGENT_RATE_PER_MINUTE` (default 20, gate question Q5) sends (messages and reactions together) per session in the last 60 s, counted on `sends` rows of any status".

Design D7, verbatim (retention): "`sends` rows that ended are pruned with the existing daily retention."

Scope (agents-matrix-connector): migration `0002_agent_sends.sql` and the repository module `db/sends.py` (insert, claim, guarded transitions, binding check, rate count, reference resolution, prune). The api routes, the bot step and the routing change are later tasks.

`tests/test_schema.py::test_writer_comments` and `tests/test_schema.py::test_check_constraints` are no longer accurate once the new table and the widened `outbound.kind` CHECK exist (named): they list every table's writer and the accepted kinds; both are extended to the new table and kinds, nothing they assert today is removed.

## Acceptance conditions

- ac1: migration 0002 creates `sends` with the D7 columns and its COMMENT names the api as inserter and the bot worker as the only mover (updated) [evidence: test:tests/test_schema.py::test_writer_comments]
- ac2: the `sends.kind` and `sends.status` CHECKs refuse other values and `outbound.kind` accepts agent and reaction besides reply and notice (updated) [evidence: test:tests/test_schema.py::test_check_constraints]
- ac3: applying the migrations twice changes nothing [evidence: test:tests/test_schema.py::test_migration_idempotent]
- ac4: `room_settings.agents_may_initiate` is NOT NULL with default false; `outbound` has `send_id`, `event_type` defaulting to m.room.message and `relates_to` jsonb; the runs `(session_id, room_id)` index exists [evidence: test:tests/test_schema.py::test_agent_sends_columns]
- ac5: a queued send is claimed once (queued to sending), and sent, failed and refused are reached only from sending, every move through `agents_common.db.queue.transition`; a second claim or a move from the wrong status changes nothing [evidence: test:tests/test_sends_repo.py::test_guarded_transitions]
- ac6: a room is bound to a session exactly when a runs row with that session_id or a sent send of that session exists for it; queued, failed and refused sends bind nothing [evidence: test:tests/test_sends_repo.py::test_binding_counts_runs_and_sent_sends]
- ac7: the rate count counts a session's sends of any status and kind created in the last 60 s and no older ones [evidence: test:tests/test_sends_repo.py::test_rate_count_window]
- ac8: `m<n>` resolves to that inbound row's event_id and room; `s<n>` resolves to that send's room, session, kind, status and event_id; an unknown or malformed reference resolves to nothing [evidence: test:tests/test_sends_repo.py::test_resolve_references]
- ac9: prune deletes sent, failed and refused sends older than the cutoff and keeps queued and sending ones [evidence: test:tests/test_sends_repo.py::test_prune_ended_sends]
- ac10: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_schema.py tests/test_sends_repo.py && mise run lint]

## Files

- `src/agents_matrix_connector/migrations/0002_agent_sends.sql`
- `src/agents_matrix_connector/db/sends.py`
- `tests/test_schema.py`
- `tests/test_sends_repo.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
