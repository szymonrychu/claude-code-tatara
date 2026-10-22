---
title: HTTP transport
status: todo
repo: any-mcp
value: "any-mcp also serves streamable HTTP, safe by default and never relaying credentials"
files: [src/any_mcp/cli.py, src/any_mcp/_fastmcp_adapter.py, tests/test_http_transport.py]
verify: "uv run --frozen pytest tests/test_http_transport.py tests/test_cli.py -q && mise run lint"
depends_on: [cli-stdio]
owns: []
uses: [any-mcp-cli, fastmcp-adapter, any-mcp-config]
model: sonnet
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# HTTP transport

## Requirement

Add the streamable HTTP transport (design D10, D11).

- `--transport http` (and `server.transport: http`) serves streamable HTTP through FastMCP at `server.http.path` on `server.http.host:port` (defaults `127.0.0.1:8000`, `/mcp`), stateless, both protocol eras. New flags `--host`, `--port`, `--path` override the config. `--transport sse` stays a usage error.
- `run_http(server, settings)` in the adapter.
- Origin check: a request with an `Origin` header that is neither a loopback origin nor in `allowed_origins` gets 403.
- When `bearer_token` is set, a request without `Authorization: Bearer <token>` (constant-time compare) gets 401. Binding a non-loopback host with no token logs one stderr warning.
- The inbound request's `Authorization`, `Cookie` and any other header never reach a plugin or an outbound request: proved end to end with a plugin whose `HttpBinding` targets a recording `httpx.MockTransport` while the MCP client sends `Authorization: Bearer <secret>` and a cookie.

## Acceptance conditions

- AC1: --transport http serves on 127.0.0.1 at /mcp by default and a 2026-07-28 client lists and calls tools [evidence: test:tests/test_http_transport.py::test_http_modern_client]
- AC2: a handshake-era client initializes, lists and calls tools over HTTP [evidence: test:tests/test_http_transport.py::test_http_legacy_client]
- AC3: a foreign Origin gets 403 and an allowed or loopback Origin is served [evidence: test:tests/test_http_transport.py::test_origin_validation]
- AC4: with bearer_token set a missing or wrong token gets 401 and the right one is served [evidence: test:tests/test_http_transport.py::test_bearer_token]
- AC5: a non-loopback bind without a token logs one warning [evidence: test:tests/test_http_transport.py::test_warns_on_open_bind]
- AC6: inbound Authorization and Cookie values never reach the upstream request [evidence: test:tests/test_http_transport.py::test_inbound_credentials_never_forwarded]
- AC7: --transport sse is rejected as a usage error [evidence: test:tests/test_http_transport.py::test_no_sse_transport]
- AC8: config server.transport http is honoured and --host, --port and --path override the config [evidence: test:tests/test_http_transport.py::test_flags_override_config]
- AC9: the stdio CLI tests still pass and lint passes [evidence: command:uv run --frozen pytest tests/test_cli.py -q && mise run lint]

## Files

- `src/any_mcp/cli.py`
- `src/any_mcp/_fastmcp_adapter.py`
- `tests/test_http_transport.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
