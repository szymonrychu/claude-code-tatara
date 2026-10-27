---
title: mxc room initiate flag
status: todo
repo: agents-matrix-connector
value: "the user can flag a room so agents may start a chat there, off by default"
files: [src/agents_matrix_connector/db/rules.py, src/agents_matrix_connector/api/rooms.py, src/agents_matrix_connector/api/schemas.py, openapi.json, README.md, tests/test_api_rooms.py]
verify: "uv run pytest tests/test_api_rooms.py tests/test_readme_api.py tests/test_rules_repo.py && mise run lint"
depends_on: [mxc-sends-schema]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 941421
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc room initiate flag

## Requirement

README Goal, verbatim: "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."

Design D4, verbatim (the flag): "`room_settings.agents_may_initiate boolean NOT NULL DEFAULT false` is new; its writer stays the api. `PUT /matrix/api/v1/rooms/{room_id}/settings` takes an optional `agents_may_initiate`; omitted keeps the stored value (my call: the flag is an authorisation grant, so a save of the preset or trigger from an older UI never silently grants or revokes it); `RoomView` and `RoomDetail` return it."

Design D9, verbatim (the binding view): "The room's binding is visible to the user (my call: the live smoke and the operator need it): `RoomView` and `RoomDetail` of the UI API gain `binding: {session_id, slug, origin, since} | null` (the active binding; a reservation shows `session_id` null), next to the unchanged `session` (the latest run). Showing it in agents-web: noted, not doing now."

User decision (final gate, 2026-10-27), verbatim: "1. hard 1:1 relationship between chat and session / Wrap other code changes around it, besides that: Go".

Open question Q1 (approved by the user 2026-10-27, "All yes"), verbatim: "Only the owner DM gets agents_may_initiate on, set once after deploy (my call, pending gate)?" answer "yes".

Scope (agents-matrix-connector): `db/rules.py` (`RoomSettings` and `set_room_settings` carry the flag), `db/directory.py` (the room queries read the active `room_bindings` row; read only, the bot stays its writer), `api/schemas.py` (`RoomSettingsIn.agents_may_initiate: bool | None = None`, `RoomView.agents_may_initiate: bool`, `RoomView.binding: BindingView | None`), `api/rooms.py` (PUT stores the flag, views return the flag, false when the room has no settings row, and the binding), the committed `openapi.json`, and README: the `PUT /matrix/api/v1/rooms/{room_id}/settings` section names the field and its omitted-keeps rule, the `GET /matrix/api/v1/rooms` section names `binding`, and the Operations section gets a step "Let agents start chats in a room" (PUT the flag for the owner DM `!iLWrAwaTMYnINJsyNv:szymonrichert.pl` through a port-forward to the api container, or the agents-web toggle once deployed; the flag lets an agent start a chat only while the room is unbound).

## Acceptance conditions

- ac1: a PUT with agents_may_initiate true stores it and GET /rooms/{id} and GET /rooms return it [evidence: test:tests/test_api_rooms.py::test_room_settings_agents_may_initiate]
- ac2: a PUT that omits agents_may_initiate keeps the stored value, and a PUT with false clears it [evidence: test:tests/test_api_rooms.py::test_room_settings_flag_omitted_keeps_value]
- ac3: a room without a settings row reports agents_may_initiate false [evidence: test:tests/test_api_rooms.py::test_agents_may_initiate_default_false]
- ac4: GET /rooms and GET /rooms/{id} return binding {session_id, slug, origin, since} for a room with an active binding, session_id null for a reservation, and null for an unbound room or one with only released bindings, while session (the latest run) is unchanged [evidence: test:tests/test_api_rooms.py::test_room_binding_view]
- ac5: the existing room settings behaviour (preset check, trigger) is unchanged [evidence: test:tests/test_api_rooms.py::test_room_settings]
- ac6: the existing room listing assertions are unchanged [evidence: test:tests/test_api_rooms.py::test_list_rooms]
- ac7: the committed openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_committed_matches]
- ac8: the README PUT settings section documents the field, the rooms listing section the binding, and the Operations section the owner DM step [evidence: command:grep -A15 '^### `PUT /matrix/api/v1/rooms/{room_id}/settings`' README.md | grep -q agents_may_initiate && grep -A12 '^### `GET /matrix/api/v1/rooms`' README.md | grep -q binding && grep -q '^### Let agents start chats in a room' README.md]
- ac9: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_api_rooms.py tests/test_readme_api.py tests/test_rules_repo.py tests/test_directory_repo.py && mise run lint]

## Files

- `src/agents_matrix_connector/db/rules.py`
- `src/agents_matrix_connector/api/rooms.py`
- `src/agents_matrix_connector/api/schemas.py`
- `openapi.json`
- `README.md`
- `tests/test_api_rooms.py`

## Interfaces

- `api/schemas.py:RoomSettingsIn` gains `agents_may_initiate: bool | None = None`; `RoomView` (and so `RoomDetail`) gains `agents_may_initiate: bool`.
- `db/rules.py:RoomSettings` gains `agents_may_initiate: bool`; `set_room_settings(pool, room_id, *, preset_id, trigger, agents_may_initiate: bool | None = None)`: None keeps the stored value (false for a new row).
- `PUT /matrix/api/v1/rooms/{room_id}/settings` body `{preset_id?, trigger?, agents_may_initiate?}`; response `RoomDetail` with the flag.

## Expected outcome

The user can flag a room so agents may start a chat there; nothing changes for rooms left unflagged, and a settings save that does not name the flag leaves it as it was.

## Steps

- Red: add the three new tests in `tests/test_api_rooms.py`; run `uv run pytest tests/test_api_rooms.py`: they fail.
- Green: schemas, repository, route; regenerate `openapi.json` with `uv run python -m agents_matrix_connector.api.openapi > openapi.json`; update README; run the task's verify: passes. Quote the summary line with counts.

## Notes

- The omitted-keeps rule is a merge-semantics ruling: its pin test is `test_room_settings_flag_omitted_keeps_value` (retro proposal).
- The column exists after mxc-sends-schema (migration 0002); do not add another migration.
- `tests/test_api_rooms.py` is DB-backed (Docker); it runs in CI here. `test_readme_api.py` runs locally.
- `set_room_settings` keeps its single upsert statement; the keep-value rule is `COALESCE(EXCLUDED.agents_may_initiate, room_settings.agents_may_initiate)` or equivalent.

- 2026-10-27 amended: final gate 2026-10-27: hard 1:1 room-session binding replaces last-speaker routing (D9): binding shown in the room views
