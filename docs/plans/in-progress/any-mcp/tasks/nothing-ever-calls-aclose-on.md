---
title: "Nothing ever calls aclose() on the per-plugin httpx.AsyncClient that load_plugins creates for each PluginContext.http."
status: in-progress
repo: any-mcp
value: "Each plugin's HTTP client and its connection pool leak at shutdown. The registry does not close them because whoever called load_plugins owns them, and closing them in stop() would break a registry restart or a lifespan that runs more than once."
files: [src/any_mcp/discovery.py, src/any_mcp/cli.py, src/any_mcp/_fastmcp_adapter.py, src/any_mcp/testing.py, tests/test_discovery.py]
verify: "uv run --frozen pytest tests/test_discovery.py tests/test_cli.py tests/test_adapter.py -q && mise run lint"
depends_on: [cli-stdio, fastmcp-adapter, http-transport, input-required-adapter, plugin-discovery, registry, testing-harness]
owns: []
uses: []
model: ""
estimate: ""
estimate_by: ""
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/any-mcp-nothing-ever-calls-aclose-on/any-mcp
branch: any-mcp-nothing-ever-calls-aclose-on
verified_head: ""
run: ""
provides: []
---

# Nothing ever calls aclose() on the per-plugin httpx.AsyncClient that load_plugins creates for each PluginContext.http.

## Requirement

The per-plugin httpx.AsyncClient created by load_plugins (discovery.py) for each PluginContext.http is closed exactly once when its owner shuts down: load_plugins returns (or exposes) an async aclose() that closes every client it created, and every owner calls it on shutdown - the stdio/HTTP CLI main, the FastMCP adapter lifespan (only on final shutdown, never on a registry restart or a lifespan that runs more than once), and the testing harness PluginHarness. Closing twice is a no-op.

## Acceptance conditions

- AC1: aclose() closes every client load_plugins created and a second call is a no-op [evidence: test:tests/test_discovery.py::test_loaded_plugins_aclose_closes_http_clients]
- AC2: the CLI, the adapter lifespan and the harness each close the clients on shutdown [evidence: test:tests/test_discovery.py::test_owners_close_http_clients_on_shutdown]

## Files

- `src/any_mcp/discovery.py`
- `src/any_mcp/cli.py`
- `src/any_mcp/_fastmcp_adapter.py`
- `src/any_mcp/testing.py`
- `tests/test_discovery.py`

## Expected outcome

No per-plugin HTTP client or connection pool outlives its owner.

## Steps

- Write the failing tests; run red.
- Implement aclose() and call it from each owner; run green.
