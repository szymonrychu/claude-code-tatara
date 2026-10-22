---
title: Input-required adapter
status: todo
repo: any-mcp
value: "InputRequiredResult round trips work through a real stdio client and a real HTTP client, with a runnable example plugin"
files: [src/any_mcp/_fastmcp_adapter.py, examples/confirm_delete.py, tests/test_input_required_transports.py]
verify: "uv run --frozen pytest tests/test_input_required_transports.py tests/test_adapter.py tests/test_import_boundary.py -q && mise run lint"
depends_on: [input-required-core, http-transport, testing-harness]
owns: []
uses: [input-required-hook, fastmcp-adapter, any-mcp-cli, plugin-harness]
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

# Input-required adapter

## Requirement

Wire `InputRequired` through the FastMCP adapter so MCP 2026-07-28 clients get `InputRequiredResult` and can retry with `inputResponses` (design D19).

- Adapter: a `ToolResult` with `input_required` is returned as the era's `InputRequiredResult` (`inputRequests` keyed as the plugin keyed them, `requestState` from `state`); a retried `tools/call` passes `inputResponses` and `requestState` into `pipeline.call_tool`. First probe how FastMCP 4.1 exposes MRTR (a tool-return type, or the lowlevel result) and write the finding into the module docstring; fall back to the `mcp.server.MCPServer` path of D1 for this one result only, still inside the adapter.
- A handshake-era client (<= 2025-11-25) cannot retry: it receives an `isError` result whose text says the tool needs a 2026-07-28 client. The server still declares only the tools capability.
- `examples/confirm_delete.py`: a plugin with a `delete_record` tool that overrides `request_input` to ask for a confirmation (`{"confirm": boolean}`) and deletes in an in-memory dict only after `inputResponses` say yes. It imports only `any_mcp`.
- `tests/test_input_required_transports.py`: the example served by the real `any-mcp --config` over stdio (subprocess, a modern client) and over `--transport http` on a free port: first call returns input-required, the retry with `inputResponses` completes; also a "no" answer completes without deleting; the legacy client gets the isError message.

## Acceptance conditions

- AC1: over stdio a 2026-07-28 client gets InputRequiredResult for the first call and the retry with inputResponses completes the tool [evidence: test:tests/test_input_required_transports.py::test_stdio_round_trip]
- AC2: over streamable HTTP the same round trip completes [evidence: test:tests/test_input_required_transports.py::test_http_round_trip]
- AC3: a no answer completes without performing the delete [evidence: test:tests/test_input_required_transports.py::test_declined_answer]
- AC4: a handshake-era client gets an isError result saying a newer client is needed [evidence: test:tests/test_input_required_transports.py::test_legacy_client_gets_error]
- AC5: the server still declares only the tools capability and only the adapter imports fastmcp or mcp [evidence: test:tests/test_import_boundary.py::test_only_adapter_imports_fastmcp]
- AC6: lint passes [evidence: command:mise run lint]

## Files

- `src/any_mcp/_fastmcp_adapter.py`
- `examples/confirm_delete.py`
- `tests/test_input_required_transports.py`

## Interfaces

Consumes `Plugin.request_input` (`input-required-hook`). `examples/confirm_delete.py` is embedded by the authoring guide.

## Expected outcome

A plugin that needs a confirmation or a missing parameter asks for it and continues, over both transports, without importing any MCP library.

## Steps

- Write the transport test and the example; run `uv run --frozen pytest tests/test_input_required_transports.py -q`; expect failures on the adapter.
- Probe FastMCP MRTR, implement in the adapter, rerun, then `mise run lint`.

## Notes

If the MRTR result type is missing from the pinned FastMCP, the task raises the question (do not fake the result shape): record the probe output in the adapter docstring and stop for a decision.
