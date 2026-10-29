---
title: orch priority column
status: todo
repo: agents-orchestrator
value: every message records whether it should reach the agent at once or wait until idle
files: [src/agents_orchestrator/db/migrations/0012_message_priority.sql, src/agents_orchestrator/db/queue.py, src/agents_orchestrator/db/views.py, src/agents_orchestrator/api/schemas.py, src/agents_orchestrator/api/messages.py, openapi.json, tests/test_api_messages.py, tests/test_migrations.py]
verify: "uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint"
depends_on: []
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 996161
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch priority column

## Requirement

User scope addition (21:04Z via mx-34 #266), verbatim: "A: maybe worth adding priority meta to messages (by default reaching instantly, option to wait until idle)".

Goal G2 (README), verbatim: "each message carries a priority, immediate (the default) or idle (wait until the leader is idle, today's behaviour), settable from the web composer, the orchestrator messages API, the superleader's session_send tool and the ccw peer send_message tool."

Design D1 (orchestrator part), verbatim: "Every message route takes an optional `priority`: `"immediate"` (the default) or `"idle"`. Routes: orchestrator `POST /api/sessions/{id}/messages` (`schemas.PostMessage`), the agent route `POST /agent/v1/sessions/{slug}/messages` (`api/agent.py:SessionMessageIn`), `MessageView.priority`, [...]"

Design D12, verbatim: "Migration `0012_message_priority.sql` (the next free number after hive-decoupling's 0011): `ALTER TABLE messages ADD COLUMN IF NOT EXISTS priority text NOT NULL DEFAULT 'idle' CHECK (priority IN ('immediate', 'idle'))`, then `ALTER TABLE messages ALTER COLUMN priority SET DEFAULT 'immediate'`. Existing rows take `idle`, new rows default to `immediate` (my call, Q11). The api writes it once at insert (`enqueue_message(priority=)`); `MessageView` and `views._MESSAGE_SELECT` expose it."

Design D8, verbatim: "`kind = 'command'` messages keep the slash epic's path (D9 run at the Stop, D10 dispatch); their `priority` is stored as sent and ignored (Q4)."

Scope (agents-orchestrator): `src/agents_orchestrator/db/migrations/0012_message_priority.sql` (new), `db/queue.py` (`enqueue_message(..., priority="immediate")`), `db/views.py` (`_MESSAGE_SELECT` reads `m.priority`), `api/schemas.py` (`MessagePriority`, `PostMessage.priority`, `MessageView.priority`), `api/messages.py` (passes it through), `openapi.json` (regenerated), `tests/test_api_messages.py`, `tests/test_migrations.py`. Test no longer accurate (named): `tests/test_migrations.py::test_fresh_database_gets_all_tables` and `test_presets_migration_on_existing_sessions` list every applied migration and gain `0012`.

## Acceptance conditions

- ac1: (CI or a Docker host) migration 0012 adds messages.priority: rows that existed before it read idle, a new row without priority reads immediate, any other value violates the CHECK, and a rerun is a no-op (new) [evidence: test:tests/test_migrations.py::test_message_priority_column]
- ac2: (CI or a Docker host) the migration lists of the fresh and existing-database tests include 0012 (updated, named) [evidence: test:tests/test_migrations.py::test_fresh_database_gets_all_tables]
- ac3: (CI or a Docker host) POST /api/v1/sessions/{id}/messages stores priority (immediate by default, idle when sent), GET of the message and the session list return it, and an unknown value answers 422 (new) [evidence: test:tests/test_api_messages.py::test_post_message_priority]
- ac4: PostMessage defaults to immediate, accepts idle, refuses other values, and MessageView carries priority [evidence: command:uv run --frozen python -c "import pydantic; from agents_orchestrator.api.schemas import PostMessage, MessageView; assert PostMessage(text='x').priority == 'immediate'; assert PostMessage(text='x', priority='idle').priority == 'idle'; assert 'priority' in MessageView.model_fields; exec('try:\n PostMessage(text=\'x\', priority=\'soon\')\n raise SystemExit(1)\nexcept pydantic.ValidationError:\n pass')"]
- ac5: openapi.json is regenerated from the app and carries the field [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- ac6: Docker-free suites and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint]

## Files

- `src/agents_orchestrator/db/migrations/0012_message_priority.sql`
- `src/agents_orchestrator/db/queue.py`
- `src/agents_orchestrator/db/views.py`
- `src/agents_orchestrator/api/schemas.py`
- `src/agents_orchestrator/api/messages.py`
- `openapi.json`
- `tests/test_api_messages.py`
- `tests/test_migrations.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
