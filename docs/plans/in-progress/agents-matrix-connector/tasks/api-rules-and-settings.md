---
title: api rules and settings
status: done
repo: agents-matrix-connector
value: allow and deny lists and the default preset are editable over HTTP
files: [src/agents_matrix_connector/api/rules.py, src/agents_matrix_connector/api/app.py, src/agents_matrix_connector/api/schemas.py, tests/test_api_rules.py]
verify: "uv run --frozen pytest tests/test_api_rules.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [api-rooms-and-users]
model: sonnet
review: ""
verified_head: 38223425a5ee0681dce02bcc347e659f10957202
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: 3
actual_minutes: 4
actual_tokens: 1003544
actual_roles: "impl 3, review 2"
actual_role_tokens: "impl 813058, review 190486"
---

# api rules and settings

## Requirement

The rules, settings and global messages routes of the UI API (design D6, D11). Paths are in code/agents-matrix-connector.

- `src/agents_matrix_connector/api/rules.py`, mounted by `create_api_app` under `/matrix/api/v1`:
  - `GET /rules` -> `{allow: [RuleView], deny: [RuleView]}` (`RuleView {id, list, kind, value, note, created_at}`).
  - `POST /rules` body `RuleIn {list, kind, value, note?}` -> 201 `RuleView`; `policy.validate_rule` errors answer 422 `invalid_rule` with the validation message (including the display-name-allow refusal); a duplicate answers 409 `rule_exists`.
  - `DELETE /rules/{id}` -> 204, 404 `not_found`.
  - `GET /settings` -> `{default_preset_id}`; `PUT /settings` body `{default_preset_id: UUID | None}` -> the view; an unknown preset answers 422 `unknown_preset` (checked with `orchestrator.get_preset`).
  - `GET /messages?status=&room_id=&limit=50&before_id=` -> inbound `MessageView`s newest first across rooms.
- `src/agents_matrix_connector/api/schemas.py` gains `RuleIn`, `RuleView`, `RulesView`, `SettingsView`, `SettingsIn`.
- `src/agents_matrix_connector/api/app.py` includes the router.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: rules are created, listed per list and deleted, and a rule changes the access shown by GET /rooms at once [evidence: test:tests/test_api_rules.py::test_rules_crud_changes_access]
- AC2: an invalid rule answers 422 invalid_rule naming the field and a display name allow rule is refused [evidence: test:tests/test_api_rules.py::test_invalid_rules]
- AC3: a duplicate rule answers 409 rule_exists and deleting an unknown rule 404 [evidence: test:tests/test_api_rules.py::test_duplicate_and_unknown]
- AC4: the default preset is read and set, and an unknown preset answers 422 unknown_preset [evidence: test:tests/test_api_rules.py::test_default_preset_setting]
- AC5: GET /messages filters by status and room and pages newest first [evidence: test:tests/test_api_rules.py::test_global_messages]

## Files

- `src/agents_matrix_connector/api/rules.py`
- `src/agents_matrix_connector/api/app.py`
- `src/agents_matrix_connector/api/schemas.py`
- `tests/test_api_rules.py`

## Interfaces

- `src/agents_matrix_connector/api/rules.py`: the routes above (contract `matrix-connector-api`).
- Uses `db.rules` and `policy`.

## Expected outcome

Allowing a room through `POST /rules {"list": "allow", "kind": "room", "value": "!x:szymonrichert.pl"}` flips its access in `GET /rooms` to allowed.

## Steps

- Red: `tests/test_api_rules.py` with the five tests. Fails on the missing routes.
- Green: write the routes and schemas. Run the verify (Docker).

## Notes

- Never echo a rule value into logs beyond its id; values are personal identifiers.

- 2026-10-25 done
