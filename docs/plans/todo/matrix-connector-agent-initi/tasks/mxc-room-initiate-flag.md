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

Open question Q1 (pending gate), verbatim: "Only the owner DM gets agents_may_initiate on, set once after deploy (my call, pending gate)?" recommended "yes".

Scope (agents-matrix-connector): `db/rules.py` (`RoomSettings` and `set_room_settings` carry the flag), `api/schemas.py` (`RoomSettingsIn.agents_may_initiate: bool | None = None`, `RoomView.agents_may_initiate: bool`), `api/rooms.py` (PUT stores it, views return it, false when the room has no settings row), the committed `openapi.json`, and README: the `PUT /matrix/api/v1/rooms/{room_id}/settings` section names the field and its omitted-keeps rule, and the Operations section gets a step "Let agents start chats in a room" (PUT the flag for the owner DM `!iLWrAwaTMYnINJsyNv:szymonrichert.pl` through a port-forward to the api container, or the agents-web toggle once deployed).

## Acceptance conditions

- ac1: a PUT with agents_may_initiate true stores it and GET /rooms/{id} and GET /rooms return it [evidence: test:tests/test_api_rooms.py::test_room_settings_agents_may_initiate]
- ac2: a PUT that omits agents_may_initiate keeps the stored value, and a PUT with false clears it [evidence: test:tests/test_api_rooms.py::test_room_settings_flag_omitted_keeps_value]
- ac3: a room without a settings row reports agents_may_initiate false [evidence: test:tests/test_api_rooms.py::test_agents_may_initiate_default_false]
- ac4: the existing room settings behaviour (preset check, trigger) is unchanged [evidence: test:tests/test_api_rooms.py::test_room_settings]
- ac5: the committed openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_committed_matches]
- ac6: the README PUT settings section documents the field and the Operations section the owner DM step [evidence: command:grep -A15 '^### `PUT /matrix/api/v1/rooms/{room_id}/settings`' README.md | grep -q agents_may_initiate && grep -q '^### Let agents start chats in a room' README.md]
- ac7: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_api_rooms.py tests/test_readme_api.py tests/test_rules_repo.py && mise run lint]

## Files

- `src/agents_matrix_connector/db/rules.py`
- `src/agents_matrix_connector/api/rooms.py`
- `src/agents_matrix_connector/api/schemas.py`
- `openapi.json`
- `README.md`
- `tests/test_api_rooms.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
