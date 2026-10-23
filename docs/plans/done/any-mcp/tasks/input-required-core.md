---
title: Input-required core
status: done
repo: any-mcp
value: "A plugin can ask the client for more input mid-call with one optional hook, and plugins that ignore it are unchanged"
files: [src/any_mcp/types.py, src/any_mcp/plugin.py, src/any_mcp/pipeline.py, src/any_mcp/__init__.py, tests/test_input_required.py]
verify: "uv run --frozen pytest tests/test_input_required.py tests/test_pipeline.py tests/test_plugin.py -q && mise run lint"
depends_on: [call-pipeline]
owns: [input-required-hook]
uses: [tool-types, plugin-abc, call-pipeline]
model: sonnet
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/any-mcp-input-required-core/any-mcp
branch: any-mcp-input-required-core
verified_head: 2782d30fe76cda719a4d2a43b9c46153c54c0a22
run: any-mcp
provides: [input-required-hook]
acs_for_audit: []
process_gaps: []
---

# Input-required core

## Requirement

Add the MRTR `InputRequiredResult` hook to the plugin contract and the call pipeline (design D19). No `fastmcp` or `mcp` imports.

- `types.py`: frozen dataclasses `InputRequest(kind: Literal["elicitation"], message: str, schema: Mapping[str, Any])` and `InputRequired(requests: Mapping[str, InputRequest], state: str | None = None)`; `ToolCall` gains `input_responses: Mapping[str, Any] = {}` and `request_state: str | None = None`; `ToolResult` gains `input_required: InputRequired | None = None` (when set, `is_error` is false and the text is the first request message). `InputRequired` rejects an empty `requests` mapping.
- `Plugin.request_input(call) -> InputRequired | None`: an optional async hook, not abstract, whose default returns `None` (never requests input). A plugin overrides it to return `InputRequired` while `call.input_responses` lacks what it needs, and `None` once it has everything; it reads the client's answers from `call.input_responses` and its own opaque state from `call.request_state`.
- Pipeline order becomes: validate, `before_call`, `request_input`, then `credentials`/`call`/`shape_response` only when `request_input` returned `None`. A non-None result returns `ToolResult(input_required=...)` without calling `call`. `call_tool(..., input_responses=None, request_state=None)` passes the retry values into the `ToolCall`. An exception from `request_input` goes to `on_error` like any hook failure.
- `any_mcp` exports `InputRequired` and `InputRequest`.

## Acceptance conditions

- AC1: the default request_input returns None and an existing plugin's calls are unchanged [evidence: test:tests/test_input_required.py::test_default_never_requests_input]
- AC2: a plugin returning InputRequired gets a result with input_required set, no isError, and call is not run [evidence: test:tests/test_input_required.py::test_input_required_short_circuits_call]
- AC3: on retry the input_responses and request_state reach request_input and, once it returns None, call runs with them on the ToolCall [evidence: test:tests/test_input_required.py::test_retry_carries_responses_and_state]
- AC4: an exception from request_input becomes an isError result through on_error [evidence: test:tests/test_input_required.py::test_request_input_failure_goes_to_on_error]
- AC5: InputRequired rejects an empty requests mapping and the types are exported from any_mcp [evidence: test:tests/test_input_required.py::test_types_and_exports]
- AC6: lint passes [evidence: command:mise run lint]

## Files

- `src/any_mcp/types.py`
- `src/any_mcp/plugin.py`
- `src/any_mcp/pipeline.py`
- `src/any_mcp/__init__.py`
- `tests/test_input_required.py`

## Interfaces

`Plugin.request_input(self, call: ToolCall) -> InputRequired | None` (part `input-required-hook`, consumer input-required-adapter); `pipeline.call_tool(..., input_responses=None, request_state=None)`.

## Expected outcome

A plugin author who never touches `request_input` sees no change; one who overrides it gets a clean ask-then-continue flow in plain Python.

## Steps

- Write `tests/test_input_required.py`; run `uv run --frozen pytest tests/test_input_required.py -q`; expect failures on the missing types and hook.
- Add the types, the hook and the pipeline step; rerun all three test files (pass), then `mise run lint`.

## Notes

Keep the hook's default a real implementation (return `None`), not an abstract method, so G1 (one required hook) still holds. State strings are opaque to any-mcp; a plugin that signs or encrypts them does so itself, and the guide says so.
