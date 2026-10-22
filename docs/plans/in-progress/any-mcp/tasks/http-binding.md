---
title: HTTP binding
status: in-progress
repo: any-mcp
value: Plugins describe an endpoint declaratively and write no HTTP code
files: [src/any_mcp/http.py, tests/test_http_binding.py]
verify: "uv run --frozen pytest tests/test_http_binding.py -q && mise run lint"
depends_on: [core-types]
owns: [http-executor]
uses: [tool-types, tool-errors]
model: sonnet
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/any-mcp-http-binding/any-mcp
branch: any-mcp-http-binding
verified_head: ""
run: ""
provides: []
---

# HTTP binding

## Requirement

Execute a declarative `HttpBinding` with httpx so a plugin can describe an endpoint and write no call code (design D3, D11).

- `make_client(base_url, *, transport=None, timeout=30.0) -> httpx.AsyncClient`: `User-Agent: any-mcp/<version>`, no `Authorization` or `Cookie` header, the given transport when not `None` (tests pass `httpx.MockTransport`).
- `execute_binding(client, call, *, headers={}, timeout=None) -> RawResponse`: fills `{name}` path segments from the arguments (URL-encoded; a missing one raises `ToolInputError`), sends `query` arguments as query parameters (lists repeated, `None` omitted, booleans as `true`/`false`), maps `headers` arguments to request headers, builds the JSON body per the `body` mode, and merges the `headers` parameter (the plugin's `credentials()` output) last so it wins.
- URL: `binding.base_url` when set, else the client's base URL; a relative path with neither raises `ConfigError`.
- Status `>= 400` raises `UpstreamError` carrying the `RawResponse`; any other status returns `RawResponse(status, headers, body, content_type)`.
- Nothing from an inbound MCP request is an input here: only the `ToolCall` arguments and the `headers` parameter reach the request.

## Acceptance conditions

- AC1: path parameters are filled and URL-encoded, and a missing one raises ToolInputError [evidence: test:tests/test_http_binding.py::test_path_parameters]
- AC2: query parameters repeat lists, omit None and lowercase booleans [evidence: test:tests/test_http_binding.py::test_query_parameters]
- AC3: the four body modes (None, "*", one name, a tuple of names) produce the specified JSON bodies [evidence: test:tests/test_http_binding.py::test_body_modes]
- AC4: argument headers are mapped and credential headers are merged last and win [evidence: test:tests/test_http_binding.py::test_headers_and_credentials]
- AC5: binding base_url overrides the client base URL and a relative path with no base URL raises ConfigError [evidence: test:tests/test_http_binding.py::test_base_url_resolution]
- AC6: a status of 400 or above raises UpstreamError with the response, other statuses return a RawResponse [evidence: test:tests/test_http_binding.py::test_status_handling]
- AC7: make_client sets the any-mcp user agent, no Authorization or Cookie header, and uses the given transport [evidence: test:tests/test_http_binding.py::test_make_client_defaults]
- AC8: lint passes [evidence: command:mise run lint]

## Files

- `src/any_mcp/http.py`
- `tests/test_http_binding.py`

## Interfaces

`any_mcp.http.make_client(base_url: str | None, *, transport: httpx.AsyncBaseTransport | None = None, timeout: float = 30.0) -> httpx.AsyncClient` and `any_mcp.http.execute_binding(client: httpx.AsyncClient, call: ToolCall, *, headers: Mapping[str, str] = {}, timeout: float | None = None) -> RawResponse`: the `http-executor` part, used by the default `Plugin.call` and by discovery when it builds `ctx.http`.

## Expected outcome

A `ToolSpec` with an `HttpBinding` turns into exactly one well-formed HTTP request, and errors come back as typed exceptions the pipeline maps.

## Steps

- Write `tests/test_http_binding.py` with an `httpx.MockTransport` that records each request; run `uv run --frozen pytest tests/test_http_binding.py -q`; expect import errors.
- Implement `src/any_mcp/http.py`; rerun (all pass), then `mise run lint`.

## Notes

Use the `httpx` package declared by scaffold, never FastMCP's HTTP client. Read the version with `importlib.metadata`.
