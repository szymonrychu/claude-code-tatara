---
title: mxc openapi and readme
status: done
repo: agents-matrix-connector
value: every connector capability is documented and usable without the UI
files: [openapi.json, README.md, src/agents_matrix_connector/api/openapi.py, tests/test_readme_api.py]
verify: "uv run --frozen pytest tests/test_readme_api.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [api-rules-and-settings, matrix-sync-loop, dispatch-worker, reply-tracker]
model: sonnet
review: ""
verified_head: 3af4f6e6dcb5b990caf06e8a3fc9a1b2a7f62547
points: 2
expected_minutes: 8
expected_tokens: 542616
points_actual: 2
actual_minutes: 4
actual_tokens: 1311502
actual_roles: "impl 4, review 3"
actual_role_tokens: "impl 1048585, review 262917"
---

# mxc openapi and readme

## Requirement

Headless documentation of the UI API (design D11, D14; contract `matrix-connector-api`). Paths are in code/agents-matrix-connector.

- `src/agents_matrix_connector/api/openapi.py`: `export() -> dict` builds the OpenAPI document of `create_api_app` without a database or orchestrator, and `python -m agents_matrix_connector.api.openapi > openapi.json` writes it (sorted keys, two-space indent, trailing newline).
- `openapi.json` committed at the repo root.
- `README.md` `## API`: base path `/matrix/api/v1`, auth (SSO at the ingress, source CIDR allowlist), every route with method, query and body fields, status codes and error codes (`invalid_request`, `invalid_rule`, `rule_exists`, `unknown_preset`, `not_found`, `forbidden`), the access states and reasons (`room_infrastructure`, `room_encrypted`, `denied: <kind>`, `not_allowed`, `not_mentioned`, `queue_full`, `unsupported_content`, `no_preset`, `preset_not_found`, `session_gone`, `turn_failed`, `message_failed`, `message_cancelled`, `timeout`, `empty_reply`, `forbidden`), and the additive-only rule.
- `tests/test_readme_api.py`: the committed `openapi.json` equals `export()`; every path of the app appears in README `## API`; every reason constant of `policy`, `sync`, `worker` and `tracker` appears in README.

User request 2026-10-25, verbatim: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Acceptance conditions

- AC1: the committed openapi.json equals the exported document [evidence: test:tests/test_readme_api.py::test_openapi_committed_matches]
- AC2: README API section names every route of the app [evidence: test:tests/test_readme_api.py::test_readme_lists_every_route]
- AC3: README names every status reason the service records [evidence: test:tests/test_readme_api.py::test_readme_lists_every_reason]

## Files

- `openapi.json`
- `README.md`
- `src/agents_matrix_connector/api/openapi.py`
- `tests/test_readme_api.py`

## Interfaces

- `openapi.json` (vendored by agents-web task web-matrix-api-client as `openapi/matrix.json`), README `## API` (contract `matrix-connector-api`).

## Expected outcome

`python -m agents_matrix_connector.api.openapi` reproduces the committed `openapi.json` byte for byte; README documents every route and reason.

## Steps

- Red: `tests/test_readme_api.py` with the three tests. Fails: no export module, no README section.
- Green: write `openapi.py`, generate `openapi.json`, write README `## API`. Run the verify.

## Notes

- Follow `code/agents-webhook/src/agents_webhook/api/openapi.py` and `tests/test_readme_api.py`.
- Reason constants: import them from their modules in the test rather than listing strings twice.

- 2026-10-25 done
