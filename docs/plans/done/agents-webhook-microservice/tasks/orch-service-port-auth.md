---
title: orch service port auth
status: done
repo: agent-orchestrator
value: "other in-cluster services can start clusters and send prompts with a token, without opening the main API to pod CIDRs"
files: [src/agent_orchestrator/settings.py, src/agent_orchestrator/api/service_auth.py, src/agent_orchestrator/api/allowlist.py, src/agent_orchestrator/api/app.py, src/agent_orchestrator/cli.py, tests/test_service_port.py]
verify: "uv run pytest tests/test_service_port.py tests/test_agent_port.py tests/test_settings.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: opus
review: panel
verified_head: db35508
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: 2
actual_minutes: 12
actual_tokens: 2753783
actual_roles: "impl 12, review 1"
actual_role_tokens: "impl 2568588, review 185195"
---

# orch service port auth

## Requirement

Service-to-service authentication for agent-orchestrator on a dedicated internal port (design D10, user decision: authz change, panel review). Paths are in code/agent-orchestrator.

- `settings.py`: `service_port: int = 8002`; `service_tokens: CsvList = []` from `ORCH_SERVICE_TOKENS` or `ORCH_SERVICE_TOKENS_FILE` (file content wins), each entry `<name>:<64 lowercase hex sha256>` with `name` matching `^[a-z0-9][a-z0-9-]{0,62}$`; a malformed entry or a duplicate name is a `SettingsError` naming `ORCH_SERVICE_TOKENS` without echoing the value; `service_port` must differ from `http_port` and `agent_port`.
- `api/service_auth.py`: `ServiceGate` ASGI middleware active only for connections accepted on `service_port`:
  - WebSocket scopes are closed with 1008.
  - `/healthz` and `/readyz` pass without a token.
  - Otherwise `Authorization: Bearer <token>` is required; `sha256(token)` is compared with every configured hash by `hmac.compare_digest` (no early exit on the first mismatch); a missing or wrong token gets 401 `unauthorized` with `WWW-Authenticate: Bearer`.
  - With a valid token only these method and path pairs pass, everything else is 403 `forbidden`: `GET /api/v1/meta`, `GET /api/v1/presets`, `GET /api/v1/presets/{id}`, `GET /api/v1/clusters`, `POST /api/v1/clusters`, `GET /api/v1/clusters/{id}`, `GET /api/v1/clusters/{id}/messages`, `POST /api/v1/clusters/{id}/messages`, `GET /api/v1/messages/{id}`. `/agent/v1/*` is never served there.
  - The request log line carries `service=<name>`; the token never appears in logs or errors.
- `api/allowlist.py`: `PortGate` learns the service port (serves the paths above plus health; never `/agent/v1`); `SourceAllowlist` skips the service port as it skips the agent port. The main port and the agent port behave exactly as before.
- `api/app.py`: wire `ServiceGate` with the settings; `cli.py`: `_listen_sockets` binds the service port too (a third socket).
- `tests/test_service_port.py` (with the existing app fixtures, a client whose server port is 8002): health without a token; 401 without or with a wrong token; each allowed route answers with a valid token from a non-allowlisted source address; a not-listed route (for example `DELETE /api/v1/clusters/{id}`, `PUT /api/v1/presets/{id}`, `POST /api/v1/agents/{id}/restart`) is 403; `/agent/v1/me` is 404 there; WebSocket closes 1008; the main port still refuses a non-allowlisted source with 403 and ignores the bearer header; settings validation cases. Existing `tests/test_agent_port.py` and `tests/test_settings.py` stay green.

## Acceptance conditions

- AC1: a valid service token reaches each allowed route from a source outside ORCH_ALLOWED_CIDRS [evidence: test:tests/test_service_port.py::test_allowed_routes_with_token]
- AC2: a missing or wrong token gets 401 and health needs no token [evidence: test:tests/test_service_port.py::test_token_required]
- AC3: routes outside the list get 403, /agent/v1 gets 404 and WebSockets close 1008 on the service port [evidence: test:tests/test_service_port.py::test_route_allowlist]
- AC4: the main port ignores bearer tokens and still enforces the source allowlist [evidence: test:tests/test_service_port.py::test_main_port_unchanged]
- AC5: malformed ORCH_SERVICE_TOKENS entries are a SettingsError that does not echo the value [evidence: test:tests/test_service_port.py::test_service_tokens_validation]
- AC6: existing agent-port and settings tests and lint pass [evidence: command:uv run pytest tests/test_agent_port.py tests/test_settings.py -q && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/settings.py`
- `src/agent_orchestrator/api/service_auth.py`
- `src/agent_orchestrator/api/allowlist.py`
- `src/agent_orchestrator/api/app.py`
- `src/agent_orchestrator/cli.py`
- `tests/test_service_port.py`

## Interfaces

- Owns `orch-service-tokens`: port `ORCH_SERVICE_PORT` (8002); `ORCH_SERVICE_TOKENS` = CSV `<name>:<sha256 hex>`; Bearer auth; the route list above; errors 401 `unauthorized`, 403 `forbidden`. Documented in README by task orch-service-port-docs.

## Expected outcome

`curl -H "Authorization: Bearer $T" http://<api>:8002/api/v1/presets` answers 200 from any pod; without the token 401; the main and agent ports are unchanged.

## Steps

- Red: write `tests/test_service_port.py`; run it: fails.
- Green: settings, middleware, PortGate and SourceAllowlist changes, socket binding; tests pass.
- Run the verify command.

## Notes

- Model on `api/allowlist.py:PortGate` and the agent port's `skip_port` handling in `app.py` L84-86; `api/agent.py:require_agent` L57 for constant-time token checks.
- No route changes shape: `openapi.json` stays byte-identical (`tests/test_readme_api.py`).
- cluster-scaling and configuration-improvements also edit `settings.py`; rebase on whichever lands first.

- 2026-10-25 done
