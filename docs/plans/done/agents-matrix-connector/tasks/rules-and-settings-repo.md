---
title: rules and settings repo
status: done
repo: agents-matrix-connector
value: "allow and deny rules, room presets and the default preset persist validated"
files: [src/agents_matrix_connector/db/rules.py, tests/test_rules_repo.py]
verify: "uv run --frozen pytest tests/test_rules_repo.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [directory-repository, access-policy-engine]
model: sonnet
review: ""
verified_head: 88b5ca0fc8e637a17e460550569ba3231104b04b
points: 2
expected_minutes: 8
expected_tokens: 542616
points_actual: 2
actual_minutes: 2
actual_tokens: 367266
actual_roles: "impl 1, review 1"
actual_role_tokens: "impl 251893, review 115373"
---

# rules and settings repo

## Requirement

The rules and settings repository, written only by the API (design D6, D10). Paths are in code/agents-matrix-connector.

`src/agents_matrix_connector/db/rules.py`:

- `RuleExists(Exception)`.
- `add_rule(pool, list_, kind, value, note: str | None) -> policy.Rule`: validates through `policy.validate_rule` (its `ValueError` propagates), inserts, maps the unique violation to `RuleExists`.
- `delete_rule(pool, rule_id) -> bool`.
- `list_rules(conn_or_pool) -> list[policy.Rule]` ordered by id, plus `list_rule_rows(pool)` with `note` and `created_at` for the API.
- `get_room_settings(conn_or_pool, room_id) -> RoomSettings | None` (`preset_id`, `trigger`); `set_room_settings(pool, room_id, *, preset_id, trigger) -> RoomSettings` (upsert; both may be None).
- `get_default_preset(conn_or_pool) -> uuid.UUID | None`; `set_default_preset(pool, preset_id: uuid.UUID | None)`.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: add_rule stores the canonical value and list_rules returns rules ordered by id [evidence: test:tests/test_rules_repo.py::test_add_and_list_rules]
- AC2: a duplicate rule raises RuleExists and an invalid rule raises ValueError without writing [evidence: test:tests/test_rules_repo.py::test_duplicate_and_invalid_rules]
- AC3: delete_rule removes a rule and answers False for an unknown id [evidence: test:tests/test_rules_repo.py::test_delete_rule]
- AC4: room settings and the default preset round-trip, including clearing to None [evidence: test:tests/test_rules_repo.py::test_room_settings_and_default_preset]

## Files

- `src/agents_matrix_connector/db/rules.py`
- `tests/test_rules_repo.py`

## Interfaces

- `src/agents_matrix_connector/db/rules.py`: `RuleExists`, `add_rule`, `delete_rule`, `list_rules`, `list_rule_rows`, `RoomSettings`, `get_room_settings`, `set_room_settings`, `get_default_preset`, `set_default_preset`. Writers used only by the API; readers also by matrix-sync-loop and dispatch-worker.

## Expected outcome

Rules and settings persist exactly in the shape `policy.evaluate` and the worker consume.

## Steps

- Red: `tests/test_rules_repo.py` with the four tests on a migrated database. Fails on the missing module.
- Green: write the module. Run the verify (Docker).

## Notes

- Accept either an `AsyncConnection` or an `AsyncConnectionPool` for the readers (a small helper), so the sync loop can read inside its transaction.

- 2026-10-25 done
