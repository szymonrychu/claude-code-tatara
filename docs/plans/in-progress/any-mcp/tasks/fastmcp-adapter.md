---
title: FastMCP adapter
status: in-progress
repo: any-mcp
value: MCP clients of both protocol eras see the tools while plugins stay free of FastMCP
files: [src/any_mcp/_fastmcp_adapter.py, tests/test_adapter.py, tests/test_import_boundary.py]
verify: "uv run --frozen pytest tests/test_adapter.py tests/test_import_boundary.py -q && mise run lint"
depends_on: [call-pipeline]
owns: [fastmcp-adapter]
uses: [tool-registry, call-pipeline]
model: opus
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

# FastMCP adapter

## Requirement

Serve the registry over MCP with FastMCP 4.x from the one module allowed to import `fastmcp` or `mcp` (design D1, D6, D8, D15).

- `build_server(registry, config) -> Server`: an any-mcp `Server` wrapping a FastMCP instance named `config.server.name` with `config.server.instructions`, `cache_ttl` from `tools.list_ttl_ms` and `cache_scope` from `tools.cache_scope`, and one provider that lists `registry.tools()` (sorted) as FastMCP `Tool` subclasses with raw `parameters` = `listed_schema`, `output_schema`, `title`, `annotations` and description, whose `run(arguments)` calls `pipeline.call_tool` and converts the `ToolResult` to text content plus `structured_content` and `is_error`.
- FastMCP's own input validation must not pre-empt the pipeline: invalid arguments reach `call_tool` and come back as `isError` results.
- An unknown tool name is a JSON-RPC `-32602` error.
- The server declares only the tools capability: no resources, prompts, sampling, elicitation or roots.
- The FastMCP lifespan runs `registry.start()`, `registry.run_periodic()` as a task, and `registry.stop()` on exit.
- A registry listener sends the tool-list-changed notification FastMCP supports for the connected era(s), once per real change; the next `tools/list` is current whether or not the client acts on it.
- `run_stdio(server)` serves stdio. `in_memory_client(server)` is an async context manager yielding an `InMemoryClient` with `list_tools() -> list[dict]` (MCP tool dicts), `call_tool(name, arguments) -> dict` (`{"text", "structured", "is_error"}`) and `list_tools_result() -> dict` (the raw result including `ttlMs` and `cacheScope` where the era carries them), using plain Python types only.
- `tests/test_import_boundary.py` parses every `.py` under `src/any_mcp` and `examples` with `ast` and fails when any module other than `src/any_mcp/_fastmcp_adapter.py` imports `fastmcp` or `mcp`.
- Write the probe results (Tool subclass API used, how validation was bypassed, which notification call reaches which protocol era) into the module docstring.

## Acceptance conditions

- AC1: tools/list over the in-memory client returns the registry tools sorted, with listed schemas, descriptions, output schemas and annotations [evidence: test:tests/test_adapter.py::test_list_tools_matches_registry]
- AC2: the tools/list result carries ttlMs equal to list_ttl_ms and the configured cacheScope on the 2026-07-28 protocol [evidence: test:tests/test_adapter.py::test_list_result_cacheable]
- AC3: call results carry text and structured content, and invalid arguments and plugin failures come back as isError results, not protocol errors [evidence: test:tests/test_adapter.py::test_call_results_and_errors]
- AC4: an unknown tool gives JSON-RPC error -32602 [evidence: test:tests/test_adapter.py::test_unknown_tool_is_protocol_error]
- AC5: after a reload that changes the tools, the next tools/list on the same client is current without reconnecting [evidence: test:tests/test_adapter.py::test_reload_visible_on_next_list]
- AC6: the adapter's notification is sent once per changed reload and never for an unchanged reload [evidence: test:tests/test_adapter.py::test_notify_only_on_change]
- AC7: the server declares the tools capability only [evidence: test:tests/test_adapter.py::test_only_tools_capability]
- AC8: the lifespan starts the registry, runs periodic reloads and tears plugins down on exit [evidence: test:tests/test_adapter.py::test_lifespan_runs_plugin_lifecycle]
- AC9: no module but the adapter, and no example, imports fastmcp or mcp [evidence: test:tests/test_import_boundary.py::test_only_adapter_imports_fastmcp]
- AC10: lint passes [evidence: command:mise run lint]

## Files

- `src/any_mcp/_fastmcp_adapter.py`
- `tests/test_adapter.py`
- `tests/test_import_boundary.py`

## Interfaces

`any_mcp._fastmcp_adapter` (the `fastmcp-adapter` part): `class Server` (opaque; `.registry`, `.config`), `build_server(registry: ToolRegistry, config: AnyMcpConfig) -> Server`, `async run_stdio(server: Server) -> None`, `in_memory_client(server: Server) -> AsyncContextManager[InMemoryClient]`, `InMemoryClient.list_tools() -> list[dict]`, `.call_tool(name: str, arguments: Mapping[str, Any] | None = None) -> dict`, `.list_tools_result() -> dict`. Nothing in its public signatures is a FastMCP type.

## Expected outcome

Any MCP client of either protocol era sees the registry's tools with correct schemas, caching hints and error semantics, and plugins remain unaware of FastMCP.

## Steps

- Probe first: in a test, subclass `fastmcp.tools.base.Tool` with a raw `parameters` dict and serve it through `fastmcp.Client` in memory; record what works.
- Write `tests/test_adapter.py` and `tests/test_import_boundary.py`; run `uv run --frozen pytest tests/test_adapter.py tests/test_import_boundary.py -q`; expect failures.
- Implement `src/any_mcp/_fastmcp_adapter.py`; rerun (all pass), then `mise run lint`.

## Notes

Docs brief 3.2-3.8: `FastMCP(name, instructions, *, providers, cache_ttl, cache_scope, strict_input_validation, mask_error_details, lifespan, ...)`; custom providers override `_list_tools`/`_get_tool`; FastMCP auto-notifies only inside a request context, and modern-era out-of-request delivery is undocumented, so pin the observed behaviour in AC6's test and keep AC5 independent of it. Fallback if a FastMCP 4.1 surface blocks an AC: `mcp.server.MCPServer` plus `InMemorySubscriptionBus` (prior-art S4), still inside this one module. Tests may import `fastmcp` (the boundary test scans `src` and `examples` only).
