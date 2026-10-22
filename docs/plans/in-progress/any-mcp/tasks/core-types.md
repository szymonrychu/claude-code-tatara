---
title: Core types
status: in-progress
repo: any-mcp
value: "One shared vocabulary of tool, call, response and error types for core and plugins"
files: [src/any_mcp/types.py, src/any_mcp/errors.py, tests/test_types.py]
verify: "uv run --frozen pytest tests/test_types.py -q && mise run lint"
depends_on: [scaffold]
owns: [tool-types, tool-errors]
uses: []
model: sonnet
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/any-mcp-core-types/any-mcp
branch: any-mcp-core-types
verified_head: ""
run: ""
provides: []
---

# Core types

## Requirement

Define the plain data types and error types every other module shares (design D2, D3, D7). No `fastmcp` or `mcp` imports.

- `src/any_mcp/types.py`: frozen dataclasses `HttpBinding`, `ToolSpec`, `ToolCall`, `RawResponse`, `ToolResult` with the fields in Interfaces.
- `ToolSpec` validation in `__post_init__`: non-empty `name` and `description`; at most one of `input_schema` and `input_model`; at most one of `http` and `handler`. `ToolSpec.json_schema()` returns a dict: the `input_schema`, the pydantic `input_model.model_json_schema()`, or `{"type": "object", "additionalProperties": false}` for a no-argument tool.
- `RawResponse.json()` parses the body (or returns `value` when the response wraps a handler value), `RawResponse.text()` decodes with the content-type charset (default utf-8, replacement on errors), `RawResponse.from_value(value)` wraps a handler return: `str` gives `text/plain`, `bytes` gives `application/octet-stream`, any JSON-serialisable value gives `application/json`, status 200.
- `src/any_mcp/errors.py`: `AnyMcpError`, `Deny`, `ToolInputError(errors: list[tuple[str, str]])` (JSON path, message), `UpstreamError(response: RawResponse)`, `ConfigError`, `UnknownTool`, and `error_result(exc, *, plugin, expose_details=False) -> ToolResult`.
- `error_result` returns `is_error=True`, a one-line text, and `structured={"error": {"kind": ..., "message": ..., "status": ...}}` (`status` only for upstream). Kinds: `Deny` gives `denied` with its message; `ToolInputError` gives `invalid_arguments` listing every path and message; `UpstreamError` gives `upstream` with the status and at most 500 characters of body text; `TimeoutError` and `asyncio.TimeoutError` give `timeout`; anything else gives `internal` with `<plugin> failed: <ExceptionType>`, plus the message only when `expose_details` is true. No header value ever appears in the text.

## Acceptance conditions

- AC1: ToolSpec rejects an empty name or description, both schema forms at once, and both http and handler at once [evidence: test:tests/test_types.py::test_toolspec_validation]
- AC2: ToolSpec.json_schema returns the explicit schema, the model schema, or the closed empty object schema [evidence: test:tests/test_types.py::test_toolspec_json_schema]
- AC3: RawResponse.json, RawResponse.text and RawResponse.from_value behave as specified for str, bytes, dict, list and scalar values [evidence: test:tests/test_types.py::test_raw_response_helpers]
- AC4: error_result maps Deny, ToolInputError, UpstreamError, TimeoutError and other exceptions to the five kinds with the specified text and structured error [evidence: test:tests/test_types.py::test_error_result_kinds]
- AC5: upstream error text is capped at 500 body characters and no error text contains a request or response header value [evidence: test:tests/test_types.py::test_error_text_has_no_headers]
- AC6: lint passes [evidence: command:mise run lint]

## Files

- `src/any_mcp/types.py`
- `src/any_mcp/errors.py`
- `tests/test_types.py`

## Interfaces

- `HttpBinding(method: str, path: str, query: tuple[str, ...] = (), headers: Mapping[str, str] = {}, body: str | tuple[str, ...] | None = None, base_url: str | None = None)`. `headers` maps argument name to header name. `body`: `None` no body; `"*"` every argument not used by path, query or headers, as a JSON object; one argument name: that argument's value is the JSON body; a tuple of names: those arguments as a JSON object.
- `ToolSpec(name: str, description: str, input_schema: Mapping[str, Any] | None = None, input_model: type[BaseModel] | None = None, output_schema: Mapping[str, Any] | None = None, title: str | None = None, tags: frozenset[str] = frozenset(), annotations: Mapping[str, Any] | None = None, http: HttpBinding | None = None, handler: Callable[[ToolCall], Awaitable[Any]] | None = None)`, `.json_schema() -> dict`.
- `ToolCall(plugin: str, tool: str, exposed_name: str, arguments: Mapping[str, Any], spec: ToolSpec, request_id: str)`, `.with_arguments(arguments) -> ToolCall`.
- `RawResponse(status: int, headers: Mapping[str, str], body: bytes, content_type: str, value: Any = NO_VALUE)`; `NO_VALUE` sentinel exported.
- `ToolResult(text: str, structured: Any = None, is_error: bool = False)`.
- `errors.error_result(exc: BaseException, *, plugin: str, expose_details: bool = False) -> ToolResult`.

These are the `tool-types` and `tool-errors` parts; every later task imports them from `any_mcp.types` and `any_mcp.errors`.

## Expected outcome

`any_mcp.types` and `any_mcp.errors` import with no side effects and carry the full shared vocabulary.

## Steps

- Write `tests/test_types.py`; run `uv run --frozen pytest tests/test_types.py -q`; expect import errors.
- Implement both modules; rerun (all pass), then `mise run lint`.

## Notes

Mappings in frozen dataclasses: store them as `types.MappingProxyType` or tuples so instances stay hashable where the registry diffs them; the registry compares `ToolSpec`s by name, description, schemas, tags and annotations.
