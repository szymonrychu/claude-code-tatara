---
title: orch message kind
status: done
repo: agents-orchestrator
value: a slash message from the chat is stored as a command message instead of a turn
files: [src/agents_orchestrator/db/migrations/0008_slash_messages.sql, src/agents_orchestrator/db/queue.py, src/agents_orchestrator/db/views.py, src/agents_orchestrator/api/schemas.py, src/agents_orchestrator/api/messages.py, openapi.json, tests/test_api_messages.py, tests/test_migrations.py]
verify: "uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint"
depends_on: [orch-slash-parser]
model: opus
review: ""
verified_head: f4c16fbdf6f84edb0659d79123a6df4abae58a14
points: 3
expected_minutes: 6
expected_tokens: 963314
points_actual: 3
actual_minutes: 21
actual_tokens: 1617345
actual_roles: "impl 21, review 1"
actual_role_tokens: "impl 1538540, review 78805"
---

# orch message kind

## Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."

Design D1, verbatim (as amended 2026-10-29: the migration number only): "`POST /api/v1/sessions/{id}/messages` (`api/messages.py:post_message`, the chat) and `POST /agent/v1/sessions/{slug}/messages` (`api/agent.py:session_send`, the superleader) both call one new `agents_orchestrator.slash.parse(text) -> tuple[str, str] | None` and store the message with `kind = 'command'` when it matches, else `kind = 'turn'`. Migration `0010_slash_messages.sql` adds `messages.kind text NOT NULL DEFAULT 'turn' CHECK (kind IN ('turn', 'command'))` and `messages.wrapper_command_id text`. The stored text stays raw; `MessageView` gains `kind`. The `commands` table and its CHECK are untouched."

Amendment (2026-10-29, user-approved release order agreed between hives 2026-10-28): agents-orchestrator `main` now carries migrations `0008_wrapper_resume.sql` and `0009_created_by_service.sql` (the latter from the epic matrix-connector-agent-initi, merge a9f936f), so this epic's migration is `0010_slash_messages.sql`, not `0008_slash_messages.sql`. The epic's orchestrator branch `slash-commands-from-chat` (base with migrations up to 0007) is rebased onto orchestrator `main` before this task's commit. Where the frontmatter `files`, the Files section and the Steps below still name `0008_slash_messages.sql` or "migration 0008" (written before this amendment), they mean `0010_slash_messages.sql` and migration 0010.

Scope (agents-orchestrator), the chat route (the superleader route is task orch-session-send-command):
- `src/agents_orchestrator/db/migrations/0010_slash_messages.sql`: the two columns, idempotent (`ADD COLUMN IF NOT EXISTS`, like 0006 to 0009).
- `db/queue.py`: `enqueue_message(..., kind: str = "turn")` writes `kind`.
- `db/views.py`: `_MESSAGE_SELECT` returns `m.kind` and `m.wrapper_command_id`.
- `api/schemas.py`: `MessageView.kind: Literal["turn", "command"]`, `MessageView.wrapper_command_id: str | None`.
- `api/messages.py:post_message`: `kind = "command" if slash.parse(body.text) else "turn"`.
- `openapi.json` regenerated (`uv run python -m agents_orchestrator.api.openapi > openapi.json`) on the rebased branch, so it carries main's API changes too.

Tests no longer accurate (named): on orchestrator `main`, `tests/test_migrations.py::test_fresh_database_gets_all_tables` pins the applied versions to 0001-0009, `::test_presets_migration_on_existing_sessions` to 0002-0009 and `::test_0005_renames_clusters_to_sessions` to 0005-0009; each gains `0010`.

## Acceptance conditions

- ac1: (Docker: CI or a Docker host) POST /api/v1/sessions/{id}/messages {text: "/reload-plugins"} answers 202 and stores kind command with the raw text (new) [evidence: test:tests/test_api_messages.py::test_slash_text_enqueues_command_kind]
- ac2: (Docker) prose stores kind turn and GET /api/v1/messages/{id} returns kind and wrapper_command_id (new) [evidence: test:tests/test_api_messages.py::test_message_view_has_kind]
- ac3: (Docker) migration 0010 applies on a fresh database after 0001-0009 and on rerun (updated) [evidence: test:tests/test_migrations.py::test_fresh_database_gets_all_tables]
- ac4: (Docker) an existing database migrates through 0010 (updated) [evidence: test:tests/test_migrations.py::test_presets_migration_on_existing_sessions]
- ac5: (Docker) the 0005 upgrade path runs on through 0010 (updated) [evidence: test:tests/test_migrations.py::test_0005_renames_clusters_to_sessions]
- ac6: the migration is numbered 0010 after main's 0009, and no 0008_slash_messages.sql is tracked [evidence: command:test -n "$(git ls-files src/agents_orchestrator/db/migrations/0009_created_by_service.sql)" && test -n "$(git ls-files src/agents_orchestrator/db/migrations/0010_slash_messages.sql)" && test -z "$(git ls-files src/agents_orchestrator/db/migrations/0008_slash_messages.sql)"]
- ac7: openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- ac8: Docker-free checks and lint pass [evidence: command:uv run --frozen pytest tests/test_readme_api.py tests/test_slash.py && mise run lint]

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

- `messages.kind text NOT NULL DEFAULT 'turn' CHECK (kind IN ('turn','command'))`, `messages.wrapper_command_id text`.
- `queue.enqueue_message(conn, session_id, text, target_agent_id=None, *, kind="turn", sender_session_id=None, sender_slug=None, hop=0) -> int`.
- `MessageView.kind`, `MessageView.wrapper_command_id`.

## Expected outcome

A chat message starting with a slash command is stored as a command message; the queue view and the API expose its kind.

## Steps

- Red: add ac1 and ac2, update the migrations version list; on a Docker host run `uv run --frozen pytest tests/test_api_messages.py tests/test_migrations.py`: they fail. In this container only ac4 and ac5 run.
- Green: migration, queue, views, schemas, route, openapi.json; run the task's verify: passes. Quote the summary line; the Docker legs run in CI.

## Notes

- The api module may import `agents_orchestrator.slash` (no wrapper import: the layering pin `tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper` must stay green).
- Text is stored raw; never rewrite it (agents-orchestrator.md do-not-build).
- Depends on orch-slash-parser.

- 2026-10-29 amended: orchestrator main now has migrations 0008_wrapper_resume and 0009_created_by_service (matrix-connector-agent-initi merged first, user-approved order): migration renumbered 0010_slash_messages.sql, three migration version-list tests named, branch rebases onto main

- 2026-10-29 done
