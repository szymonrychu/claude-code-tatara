---
title: Core types
status: todo
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
worktree: ""
branch: ""
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
