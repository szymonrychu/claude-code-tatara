---
title: Call pipeline
status: todo
repo: any-mcp
value: Every tool call is validated and every failure is an error result the model can read
files: [src/any_mcp/pipeline.py, tests/test_pipeline.py]
verify: "uv run --frozen pytest tests/test_pipeline.py -q && mise run lint"
depends_on: [registry]
owns: [call-pipeline]
uses: [tool-registry, arg-validator, tool-errors, plugin-abc, tool-types]
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

# Call pipeline

## Requirement

Run one tool call through validation and the plugin hooks, turning every failure into an `isError` result (design D7).

- `call_tool(registry, name, arguments, *, request_id=None) -> ToolResult`. An unknown name raises `UnknownTool` (the adapter maps it to JSON-RPC `-32602`).
- Order: `validate_arguments(tool.input_schema, arguments)`, build the `ToolCall` (request id generated with `uuid4().hex[:12]` when not given), `before_call`, then `call` (the default `call` asks `credentials`) under `asyncio.timeout(loaded.timeout)`, then `shape_response`. The arguments returned by `before_call` are the ones `call` sees.
- Any exception (validation, `Deny`, timeout, upstream, any other) goes to the plugin's `on_error`; when `on_error` itself raises, the result is `error_result(exc, plugin=...)` for the original exception. Only `asyncio.CancelledError` propagates.
- One stderr log line per call with request id, exposed tool name, duration in ms and outcome (`ok` or the error kind). Arguments, header values and credentials never appear in logs or result text.

## Acceptance conditions

- AC1: an unknown tool name raises UnknownTool [evidence: test:tests/test_pipeline.py::test_unknown_tool]
- AC2: invalid arguments give an invalid_arguments error result with paths and the plugin's hooks never run [evidence: test:tests/test_pipeline.py::test_invalid_arguments_never_reach_plugin]
- AC3: hooks run in the order validate, before_call, credentials, call, shape_response, and before_call's rewritten arguments reach call [evidence: test:tests/test_pipeline.py::test_hook_order]
- AC4: Deny from before_call gives a denied error result with its message [evidence: test:tests/test_pipeline.py::test_deny]
- AC5: exceptions from call or shape_response go to on_error, an on_error failure falls back to error_result, and nothing but CancelledError escapes [evidence: test:tests/test_pipeline.py::test_exceptions_become_error_results]
- AC6: a call exceeding the plugin timeout gives a timeout error result naming the seconds [evidence: test:tests/test_pipeline.py::test_timeout]
- AC7: each call logs one line with request id, tool, duration and outcome, and no argument or credential value appears in logs [evidence: test:tests/test_pipeline.py::test_call_logging_has_no_secrets]
- AC8: lint passes [evidence: command:mise run lint]

## Files

- `src/any_mcp/pipeline.py`
- `tests/test_pipeline.py`

## Interfaces

`any_mcp.pipeline.call_tool(registry: ToolRegistry, name: str, arguments: Mapping[str, Any] | None, *, request_id: str | None = None) -> ToolResult` (the `call-pipeline` part). Raises only `UnknownTool` and `asyncio.CancelledError`.

## Expected outcome

A model calling any any-mcp tool always gets either a result or an `isError` result it can read, never a `-32603`.

## Steps

- Write `tests/test_pipeline.py` with in-test plugins that record hook calls and raise on demand, behind a started `ToolRegistry`; run `uv run --frozen pytest tests/test_pipeline.py -q`; expect import errors.
- Implement `src/any_mcp/pipeline.py`; rerun (all pass), then `mise run lint`.

## Notes

The low-level MCP SDK never validates arguments and turns exceptions into `-32603` (prior-art S3, traps 2 and 3); this module is why any-mcp does not have that problem. Use `caplog` to assert on log lines, with a secret marker value in arguments and credentials.
