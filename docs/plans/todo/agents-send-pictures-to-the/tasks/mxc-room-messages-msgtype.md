---
title: mxc room messages msgtype
status: todo
repo: agents-matrix-connector
value: the Chats page API tells a picture row from a text row
files: [src/agents_matrix_connector/api/schemas.py, src/agents_matrix_connector/api/rooms.py, openapi.json, README.md, tests/test_api_rooms.py]
verify: "uv run --frozen pytest tests/test_api_rooms.py tests/test_readme_api.py && mise run lint"
depends_on: [mxc-send-images-schema, mxc-bridge-error-notices]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 545296
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc room messages msgtype

## Requirement

README Goal G3, verbatim: "the session web chat shows the sent picture inside the tool-call box from the same-origin session download route; message text still never renders images; the Chats page shows "picture: <name>"."

Design D8, verbatim: "Chats page: MessageView grows `msgtype` (from outbound.content); RoomMessages shows "picture: <name>" for m.image. No bytes served by the connector, no mxc proxy. User Q3."

brief-cartographer fix-as-ac, verbatim: "`_out_view` / `MessageView` (`api/schemas.py:69`) expose only `body`: an image row must not render as an empty or misleading line on the Chats page."

Scope (agents-matrix-connector, UI API):
- `api/schemas.py`: `MessageView.msgtype: str | None`.
- `api/rooms.py`: `_out_view` sets `msgtype` from `outbound.content["msgtype"]` when the row has content, else null; inbound rows null. The image row's `body` is the picture name (stored by mxc-bot-image-upload).
- `openapi.json` regenerated; README documents the field on `GET /matrix/api/v1/rooms/{room_id}/messages`.
- No image bytes and no mxc URL in the view (non-goal).

## Acceptance conditions

- ac1: an outbound image row lists msgtype m.image with the picture name as body and no mxc URL; rows without content and inbound rows list msgtype null [evidence: test:tests/test_api_rooms.py::test_room_messages_msgtype]
- ac2: the committed UI OpenAPI matches the app [evidence: test:tests/test_readme_api.py::test_openapi_committed_matches]
- ac3: the README documents msgtype on the messages route [evidence: command:grep -q 'msgtype' README.md]
- ac4: the targeted tests and lint pass (DB tests in CI) [evidence: command:uv run --frozen pytest tests/test_api_rooms.py tests/test_readme_api.py && mise run lint]

## Files

- `src/agents_matrix_connector/api/schemas.py`
- `src/agents_matrix_connector/api/rooms.py`
- `openapi.json`
- `README.md`
- `tests/test_api_rooms.py`

## Interfaces

- `MessageView.msgtype: str | None` on `GET /matrix/api/v1/rooms/{room_id}/messages` (consumed by agents-web, task web-room-messages-picture).

## Expected outcome

The Chats page API tells a picture row apart from a text row without serving any image data.

## Steps

- Red: `test_room_messages_msgtype` (insert an outbound row with m.image content through `runs.add_outbound`); run `uv run --frozen pytest tests/test_api_rooms.py::test_room_messages_msgtype`: errors locally (no Docker), fails in CI.
- Green: schema field, `_out_view`, regenerate `openapi.json`, README; run the task's verify; quote the local summary line and the CI run.

## Notes

- DB-backed tests (testcontainers Postgres) need Docker; agent pods have none, so they error here (baseline 2026-10-29: 182 Docker errors) and CI on the PR is the gate for them (recurring retro). Run the verify, quote the local summary line and the CI run of the pushed head. Keep each pure helper covered by a non-DB test so the local run has signal.
- `OutboundRow.content` and `list_outbound` returning it come from mxc-send-images-schema.
