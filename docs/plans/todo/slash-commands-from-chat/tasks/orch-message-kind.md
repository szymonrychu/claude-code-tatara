---
title: orch message kind
status: todo
repo: agents-orchestrator
value: a slash message from the chat is stored as a command message instead of a turn
files: [src/agents_orchestrator/db/migrations/0008_slash_messages.sql, src/agents_orchestrator/db/queue.py, src/agents_orchestrator/db/views.py, src/agents_orchestrator/api/schemas.py, src/agents_orchestrator/api/messages.py, openapi.json, tests/test_api_messages.py, tests/test_migrations.py]
verify: "uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint"
depends_on: [orch-slash-parser]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 963314
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch message kind

## Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."

Design D1, verbatim: "`POST /api/v1/sessions/{id}/messages` (`api/messages.py:post_message`, the chat) and `POST /agent/v1/sessions/{slug}/messages` (`api/agent.py:session_send`, the superleader) both call one new `agents_orchestrator.slash.parse(text) -> tuple[str, str] | None` and store the message with `kind = 'command'` when it matches, else `kind = 'turn'`. Migration `0008_slash_messages.sql` adds `messages.kind text NOT NULL DEFAULT 'turn' CHECK (kind IN ('turn', 'command'))` and `messages.wrapper_command_id text`. The stored text stays raw; `MessageView` gains `kind`. The `commands` table and its CHECK are untouched."

Scope (agents-orchestrator), the chat route (the superleader route is task orch-session-send-command):
- `src/agents_orchestrator/db/migrations/0008_slash_messages.sql`: the two columns, idempotent (`ADD COLUMN IF NOT EXISTS`, like 0006 and 0007).
- `db/queue.py`: `enqueue_message(..., kind: str = "turn")` writes `kind`.
- `db/views.py`: `_MESSAGE_SELECT` returns `m.kind` and `m.wrapper_command_id`.
- `api/schemas.py`: `MessageView.kind: Literal["turn", "command"]`, `MessageView.wrapper_command_id: str | None`.
- `api/messages.py:post_message`: `kind = "command" if slash.parse(body.text) else "turn"`.
- `openapi.json` regenerated (`uv run python -m agents_orchestrator.api.openapi > openapi.json`).

Test no longer accurate (named): `tests/test_migrations.py::test_fresh_database_gets_all_tables` pins the applied versions to 0001-0007; it gains `0008`.

## Acceptance conditions

- ac1: (Docker: CI or a Docker host) POST /api/v1/sessions/{id}/messages {text: "/reload-plugins"} answers 202 and stores kind command with the raw text (new) [evidence: test:tests/test_api_messages.py::test_slash_text_enqueues_command_kind]
- ac2: (Docker) prose stores kind turn and GET /api/v1/messages/{id} returns kind and wrapper_command_id (new) [evidence: test:tests/test_api_messages.py::test_message_view_has_kind]
- ac3: (Docker) migration 0008 applies on a fresh database and on rerun (updated) [evidence: test:tests/test_migrations.py::test_fresh_database_gets_all_tables]
- ac4: openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- ac5: Docker-free checks and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint]

## Files

- `src/agents_orchestrator/db/migrations/0008_slash_messages.sql`
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
