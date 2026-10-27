---
title: mxc agent listener
status: todo
repo: agents-matrix-connector
value: the orchestrator gets a token-protected way into the connector without opening the SSO-protected UI api
files: [src/agents_matrix_connector/settings.py, src/agents_matrix_connector/cli.py, src/agents_matrix_connector/api/agent.py, README.md, tests/test_settings.py, tests/test_cli.py, tests/test_agent_gate.py]
verify: "uv run pytest tests/test_settings.py tests/test_agent_gate.py tests/test_cli.py && mise run lint"
depends_on: []
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 9
expected_tokens: 1836811
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc agent listener

## Requirement

README Goal, verbatim: "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."

Design D3, verbatim: "`agents-matrix-connector api` binds a second listener, `MATRIX_AGENT_PORT` (default 8001), serving only `/chat/v1/*`, `/healthz` and `/readyz`, behind a bearer gate: the sha256 hex of the presented token must equal `MATRIX_AGENT_TOKEN_SHA256` (constant-time compare, mirroring the orchestrator's `api/service_auth.py:ServiceGate`). With `MATRIX_AGENT_TOKEN_SHA256` empty the listener is not bound (my call). The token never reaches a log line or an error body."

Design D3, verbatim (probe): "The agent listener therefore skips the source allowlist and authenticates by token alone, exactly like the orchestrator's agent and service ports (`api/allowlist.py:SourceAllowlist`, "the agent and service ports authenticate on their own and are skipped"). The UI app and its allowlist are unchanged."

Design D5, verbatim (rate setting): "Rate: at most `MATRIX_AGENT_RATE_PER_MINUTE` (default 20, gate question Q5) sends (messages and reactions together) per session in the last 60 s".

Open question Q5 (pending gate), verbatim: "Per-session limit of 20 messages a minute (my call, pending gate)?" recommended "yes".

Scope (agents-matrix-connector): settings `MATRIX_AGENT_PORT` (int, default 8001, must differ from `MATRIX_HTTP_PORT`), `MATRIX_AGENT_TOKEN_SHA256` (empty, or 64 lowercase hex characters; never in repr), `MATRIX_AGENT_RATE_PER_MINUTE` (int >= 1, default 20); new module `api/agent.py` with the bearer gate and `create_agent_app(pool, settings)` serving `/healthz`, `/readyz` and a `/chat/v1` router (empty here; the routes are task mxc-agent-routes); `cli.py` runs the agent app on its own listener next to the UI app when the hash is set; README Configuration rows for the three variables. The routes, the chart and the helmfile are later tasks.

## Acceptance conditions

- ac1: the three settings parse with their defaults and bounds, a malformed hash or an agent port equal to the http port is a settings error naming the variable, and the hash never appears in repr [evidence: test:tests/test_settings.py::test_agent_listener_settings]
- ac2: the README Configuration section lists every MATRIX_ variable, the three new ones included [evidence: test:tests/test_settings.py::test_readme_lists_every_variable]
- ac3: the gate answers 401 unauthorized with WWW-Authenticate Bearer for a missing, malformed or wrong bearer and passes the token whose sha256 matches; the token and hash never appear in a log line or response body [evidence: test:tests/test_agent_gate.py::test_gate_accepts_only_the_hashed_token]
- ac4: the agent app serves only /chat/v1/*, /healthz and /readyz (anything else 404 not_found) and admits a non-loopback peer that presents the token, so no source allowlist applies to it [evidence: test:tests/test_agent_gate.py::test_agent_app_paths_and_no_source_allowlist]
- ac5: the UI app still refuses a non-loopback peer with 403 forbidden and serves no /chat/v1 path [evidence: test:tests/test_agent_gate.py::test_ui_app_keeps_source_allowlist]
- ac6: `agents-matrix-connector api` serves the agent app on MATRIX_AGENT_PORT only when MATRIX_AGENT_TOKEN_SHA256 is set, and only the UI app otherwise [evidence: test:tests/test_cli.py::test_api_binds_agent_listener_only_with_hash]
- ac7: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_settings.py tests/test_agent_gate.py tests/test_cli.py && mise run lint]

## Files

- `src/agents_matrix_connector/settings.py`
- `src/agents_matrix_connector/cli.py`
- `src/agents_matrix_connector/api/agent.py`
- `README.md`
- `tests/test_settings.py`
- `tests/test_cli.py`
- `tests/test_agent_gate.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
