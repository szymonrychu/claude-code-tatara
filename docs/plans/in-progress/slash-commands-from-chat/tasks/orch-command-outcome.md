---
title: orch command outcome
status: todo
repo: agents-orchestrator
value: "a caller reading a command message sees whether the command completed, failed or was cancelled, so no client waits for a turn that never comes"
files: [src/agents_orchestrator/db/migrations/0012_command_outcome_index.sql, src/agents_orchestrator/db/views.py, src/agents_orchestrator/api/schemas.py, src/agents_orchestrator/api/messages.py, openapi.json, README.md, tests/test_api_messages.py, tests/test_migrations.py]
verify: "uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint"
depends_on: [orch-slash-js-whitespace, orch-command-turn-link]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1975864
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch command outcome

## Requirement

User decision F2 (2026-10-29), verbatim: "F2: read-side command outcome on MessageView (orchestrator, migration 0012 partial index; check the next free migration number on the rebased orchestrator branch at /workdir/workdir/.claude/worktrees/slash-commands-from-chat/agents-orchestrator, which contains main's 0011), agents-common run tracker handles kind=command outcomes per the architect's mapping, agents-common release v0.4.0 (tag pending mx-34 confirmation; write the task so the orchestrator session pushes the tag after confirmation), then pin bumps in agents-webhook and agents-schedule."

Next free migration number, checked 2026-10-29: the rebased epic branch ends at `0011_drop_feed_cursor.sql` (main's), so this is `0012`.

Architect brief, verbatim: "F2: a command message stays `sent` and never gets a turn, so `runs.track` waits until it gives up with `timeout`." and "**Read-side outcome (chosen):** the message query looks up the latest `command_completed` or `command_failed` event for the message's `wrapper_command_id`, as `mark_sent_command` already does.
  - For: no new writer, and no race between the event and the dispatcher's 202.
  - Against: a JSON lookup on every message read.
  - Mitigation: migration `0012` adds a partial index on the command record id. The build briefly blocks event inserts."
"5. `orch-command-outcome` (orchestrator)
   - Files: `0012_command_outcome_index.sql`, `db/views.py`, `api/schemas.py` (new `CommandOutcomeView {state, result, error, turn_id, at}` as `MessageView.command`), `api/messages.py`, `openapi.json`.
   - Tests (new, in `tests/test_api_messages.py`, CI only): `test_message_command_outcome_completed`, `..._failed_unknown_command`, `..._cancelled`, `test_message_command_none_for_turns_and_pending`."

Design D19, verbatim: "`MessageView.command` (new `CommandOutcomeView {state, result, error, turn_id, at}`, null for turn messages and for a command with no outcome yet) is looked up at query time: the latest `command_completed` or `command_failed` event of the message's agent whose `data.record.id` equals the message's `wrapper_command_id` (as `mark_sent_command` already does); `state`, `result`, `error` and `turn_id` come from the event's record, `at` is the event's `ts`; a cancelled command is a `command_failed` event whose record state is `cancelled`. Migration `0012_command_outcome_index.sql` adds a partial index on the command record id over those two event types (my call: keyed by `agent_id` and the record id, the lookup's two equality predicates); its build briefly blocks event inserts. No new writer, no new message status."

Scope (agents-orchestrator): `src/agents_orchestrator/db/migrations/0012_command_outcome_index.sql` (new; `CREATE INDEX IF NOT EXISTS ... ON events (agent_id, (data -> 'record' ->> 'id')) WHERE type IN ('command_completed', 'command_failed')`), `src/agents_orchestrator/db/views.py` (`_MESSAGE_SELECT` gains a `LEFT JOIN LATERAL` on that lookup, so `get_message` and `list_messages` both carry it), `src/agents_orchestrator/api/schemas.py`, `src/agents_orchestrator/api/messages.py` (`_message_view`), `openapi.json` (regenerated), README.md (the message view field list documents `command` (null, or the command's outcome once it finished: `state`, `result`, `error`, `turn_id`, `at`)), `tests/test_api_messages.py`, `tests/test_migrations.py`. Test no longer accurate (named): `tests/test_migrations.py::test_fresh_database_gets_all_tables` and `test_presets_migration_on_existing_sessions` list every migration by number; they gain 0012.

## Acceptance conditions

- ac1: (Docker: CI or a Docker host) a sent command message whose agent stored command_completed for its wrapper_command_id (record state completed, result ok) returns command {state: completed, result: ok, error: null, turn_id: null, at: the event ts} from GET /api/v1/messages/{id} and from the session's message list (new) [evidence: test:tests/test_api_messages.py::test_message_command_outcome_completed]
- ac2: (Docker) a command_failed record with error unknown_command returns command {state: failed, error: unknown_command}; a later event for the same command id wins over an earlier one; an event of another agent with the same record id is ignored (new) [evidence: test:tests/test_api_messages.py::test_message_command_outcome_failed_unknown_command]
- ac3: (Docker) a command_failed record with state cancelled returns command {state: cancelled} (new) [evidence: test:tests/test_api_messages.py::test_message_command_outcome_cancelled]
- ac4: (Docker) command is null for a turn message, for a queued command message and for a sent command with no outcome event yet (new) [evidence: test:tests/test_api_messages.py::test_message_command_none_for_turns_and_pending]
- ac5: (Docker) migration 0012 applies on a fresh database after 0001-0011 and on rerun (updated, named) [evidence: test:tests/test_migrations.py::test_fresh_database_gets_all_tables]
- ac6: (Docker) an existing database migrates through 0012 (updated, named) [evidence: test:tests/test_migrations.py::test_presets_migration_on_existing_sessions]
- ac7: the migration is tracked as 0012 next to main's 0011 and creates a partial index on the command record id [evidence: command:test -n "$(git ls-files src/agents_orchestrator/db/migrations/0011_drop_feed_cursor.sql)" && test -n "$(git ls-files src/agents_orchestrator/db/migrations/0012_command_outcome_index.sql)" && grep -q "command_completed" src/agents_orchestrator/db/migrations/0012_command_outcome_index.sql && grep -qi "IF NOT EXISTS" src/agents_orchestrator/db/migrations/0012_command_outcome_index.sql]
- ac8: openapi.json matches the app and carries CommandOutcomeView [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- ac9: README documents the command field of the message view [evidence: command:grep -qF '`command` (null' README.md]
- ac10: the Docker-free checks and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint]

## Files

- `src/agents_orchestrator/db/migrations/0012_command_outcome_index.sql`
- `src/agents_orchestrator/db/views.py`
- `src/agents_orchestrator/api/schemas.py`
- `src/agents_orchestrator/api/messages.py`
- `openapi.json`
- `README.md`
- `tests/test_api_messages.py`
- `tests/test_migrations.py`

## Interfaces

- `api/schemas.py`: `CommandOutcomeView(BaseModel)`: `state: Literal["completed", "failed", "cancelled"]`, `result: str | None`, `error: str | None`, `turn_id: str | None`, `at: datetime`; `MessageView.command: CommandOutcomeView | None`.
- `db/views.py` `_MESSAGE_SELECT`: `LEFT JOIN LATERAL (SELECT e.ts, e.data -> 'record' AS record FROM events e WHERE e.agent_id = m.agent_id AND e.type IN ('command_completed', 'command_failed') AND e.data -> 'record' ->> 'id' = m.wrapper_command_id ORDER BY e.id DESC LIMIT 1) co ON m.kind = 'command'` (shape; the builder may name columns).
- Migration `0012_command_outcome_index.sql`: `CREATE INDEX IF NOT EXISTS events_command_record_id ON events (agent_id, (data -> 'record' ->> 'id')) WHERE type IN ('command_completed', 'command_failed')`.
- The wire shape agents-common's `Message.command` reads (task common-command-outcome).

## Expected outcome

`GET /api/v1/messages/{id}` and the session's message list show, for a command message, the command's outcome once it finished, with no new writer and no new message status.

## Steps

- Red: write the four tests in `tests/test_api_messages.py` (insert the `command_*` events rows directly, as the ingester would store them) and add 0012 to the migration lists in `tests/test_migrations.py`; in CI or on a Docker host they fail.
- Green: migration, view, schema, `_message_view`, regenerate `openapi.json`, README; run the task's verify (Docker-free part) and quote the summary line; the Docker tests run in CI.

## Notes

- Read-side only (design D19): the ingester stays the only writer of `events`; no UPDATE of `messages`.
- `mark_sent_command` (`db/queue.py`) already looks up a command's event by `data -> 'record' ->> 'id'` and agent: reuse that predicate.
- A cancelled command arrives as `command_failed` with record `state = 'cancelled'`.
- Migration 0012 is the next free number on the rebased epic branch (main's 0011_drop_feed_cursor). The todo epic immediate-message-delivery-w planned `0012_message_priority.sql`; it renumbers when claimed.
- Builds on orch-slash-js-whitespace (README touched by both).
