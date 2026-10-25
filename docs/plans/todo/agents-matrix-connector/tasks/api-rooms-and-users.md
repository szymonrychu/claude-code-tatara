---
title: api rooms and users
status: todo
repo: agents-matrix-connector
value: "the UI can list discovered rooms and users with their access state and set a room's preset"
files: [src/agents_matrix_connector/api/__init__.py, src/agents_matrix_connector/api/app.py, src/agents_matrix_connector/api/schemas.py, src/agents_matrix_connector/api/rooms.py, tests/test_api_rooms.py]
verify: "uv run --frozen pytest tests/test_api_rooms.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [mxc-settings-model, rules-and-settings-repo, inbound-queue-repository, runs-and-outbound-repo]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# api rooms and users

## Requirement

The UI API app and its rooms and users routes (design D11). Paths are in code/agents-matrix-connector.

- `src/agents_matrix_connector/api/__init__.py` (package marker).
- `src/agents_matrix_connector/api/app.py`: `create_api_app(pool, orchestrator: OrchestratorClient, settings: ApiSettings) -> FastAPI`: routes under `/matrix/api/v1`; `/healthz` and `/readyz` (ready when the pool answers); a source-address allowlist middleware from `MATRIX_API_ALLOWED_CIDRS` answering 403 `{error: {code: "forbidden", message}}` (as agents-webhook's api); error handlers so every error is `{error: {code, message}}` (422 `invalid_request` for validation errors).
- `src/agents_matrix_connector/api/schemas.py`: pydantic models `AccessView {state: "allowed" | "denied" | "default", reason, rule_id}`, `SessionView {id, slug, status}`, `RoomView {room_id, name, alias, kind, encrypted, message_request, membership, member_count, access, preset_id, trigger, effective_trigger, session, last_event_at, queued}`, `MemberView {user_id, display_name, facebook_id, membership, access}`, `RoomDetail(RoomView) {members}`, `RoomSettingsIn {preset_id: UUID | None, trigger: "all" | "mention" | None}`, `MessageView {direction: "in" | "out", id, at, sender, sender_name, body, status, reason, run_id}`, `UserView {user_id, display_name, facebook_id, rooms, access}`, `MetaView {user_id, homeserver_url, default_policy, group_trigger, rule_kinds: {allow: [...], deny: [...]}, sync: {last_sync_at, healthy}}`.
- `src/agents_matrix_connector/api/rooms.py`: `GET /meta` (`healthy` when `last_sync_at` is within three times `MATRIX_SYNC_TIMEOUT_SECONDS`); `GET /rooms?kind=&access=`; `GET /rooms/{room_id}` (404 `not_found`); `PUT /rooms/{room_id}/settings` (404 for an unknown room; a `preset_id` is checked with `orchestrator.get_preset`, a NotFound answers 422 `unknown_preset`); `GET /rooms/{room_id}/messages?limit=50&before_id=` (inbound and outbound merged newest first); `GET /users?q=&limit=100`. Access views come from `policy.evaluate` with the current rules and `MATRIX_DEFAULT_POLICY` (room level: room rules and default; member and user level: with the sender).

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: GET /meta reports the user id, the default policy, the rule kinds per list and sync health from the last sync time [evidence: test:tests/test_api_rooms.py::test_meta]
- AC2: GET /rooms lists rooms with access, effective trigger, session and queued count, filtered by kind and access [evidence: test:tests/test_api_rooms.py::test_list_rooms]
- AC3: GET /rooms/{id} returns members with their decisions and 404 for an unknown room [evidence: test:tests/test_api_rooms.py::test_room_detail]
- AC4: PUT /rooms/{id}/settings stores preset and trigger and answers 422 unknown_preset for a preset the orchestrator does not know [evidence: test:tests/test_api_rooms.py::test_room_settings]
- AC5: GET /rooms/{id}/messages merges inbound and outbound newest first with paging [evidence: test:tests/test_api_rooms.py::test_room_messages]
- AC6: GET /users filters and shows each user's decision [evidence: test:tests/test_api_rooms.py::test_users]
- AC7: a source outside the allowed CIDRs gets 403 and errors use the error body [evidence: test:tests/test_api_rooms.py::test_cidr_and_error_body]

## Files

- `src/agents_matrix_connector/api/__init__.py`
- `src/agents_matrix_connector/api/app.py`
- `src/agents_matrix_connector/api/schemas.py`
- `src/agents_matrix_connector/api/rooms.py`
- `tests/test_api_rooms.py`

## Interfaces

- `src/agents_matrix_connector/api/app.py`: `create_api_app` (extended by api-rules-and-settings, served by mxc-service-entrypoints).
- `src/agents_matrix_connector/api/schemas.py` and `rooms.py`: the views above (contract `matrix-connector-api`, documented by mxc-openapi-and-readme, consumed by agents-web).

## Expected outcome

The UI can list discovered rooms with their access state, open one with members and recent messages, and set its preset and trigger.

## Steps

- Red: `tests/test_api_rooms.py` with the seven tests: `httpx.AsyncClient(transport=ASGITransport(app))`, a migrated database with seeded rows, `FakeOrchestrator` for presets. Fails on the missing package.
- Green: write the app, schemas and routes. Run the verify (Docker).

## Notes

- Follow `code/agents-webhook/src/agents_webhook/api/app.py` for the CIDR middleware and error handlers.
- Room ids in paths contain `!` and `:`; FastAPI path params accept them URL-encoded.
