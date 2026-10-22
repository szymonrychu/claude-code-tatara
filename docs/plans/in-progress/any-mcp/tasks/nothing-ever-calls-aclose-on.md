---
title: "Nothing ever calls aclose() on the per-plugin httpx.AsyncClient that load_plugins creates for each PluginContext.http."
status: todo
repo: any-mcp
value: "Each plugin's HTTP client and its connection pool leak at shutdown. The registry does not close them because whoever called load_plugins owns them, and closing them in stop() would break a registry restart or a lifespan that runs more than once."
files: []
verify: ""
depends_on: []
owns: []
uses: []
model: ""
estimate: ""
estimate_by: ""
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Nothing ever calls aclose() on the per-plugin httpx.AsyncClient that load_plugins creates for each PluginContext.http.

## Requirement

Nothing ever calls aclose() on the per-plugin httpx.AsyncClient that load_plugins creates for each PluginContext.http.

Where: src/any_mcp/discovery.py:load_plugins (creator); whoever owns the loaded plugins: cli-stdio main, testing-harness PluginHarness, fastmcp-adapter lifespan

Why: Each plugin's HTTP client and its connection pool leak at shutdown. The registry does not close them because whoever called load_plugins owns them, and closing them in stop() would break a registry restart or a lifespan that runs more than once.

## Acceptance conditions

- AC1: Nothing ever calls aclose() on the per-plugin httpx.AsyncClient that load_plugins creates for each PluginContext.http. at src/any_mcp/discovery.py:load_plugins (creator); whoever owns the loaded plugins: cli-stdio main, testing-harness PluginHarness, fastmcp-adapter lifespan is resolved [evidence: judgement]

## Files



## Interfaces

Keep the interfaces around src/any_mcp/discovery.py:load_plugins (creator); whoever owns the loaded plugins: cli-stdio main, testing-harness PluginHarness, fastmcp-adapter lifespan unchanged unless resolving it requires otherwise: Nothing ever calls aclose() on the per-plugin httpx.AsyncClient that load_plugins creates for each PluginContext.http..

## Expected outcome

Nothing ever calls aclose() on the per-plugin httpx.AsyncClient that load_plugins creates for each PluginContext.http. at src/any_mcp/discovery.py:load_plugins (creator); whoever owns the loaded plugins: cli-stdio main, testing-harness PluginHarness, fastmcp-adapter lifespan is resolved, and Each plugin's HTTP client and its connection pool leak at shutdown. The registry does not close them because whoever called load_plugins owns them, and closing them in stop() would break a registry restart or a lifespan that runs more than once. no longer applies.

## Steps

1. Write a failing test that shows: Nothing ever calls aclose() on the per-plugin httpx.AsyncClient that load_plugins creates for each PluginContext.http..
2. Fix it at src/any_mcp/discovery.py:load_plugins (creator); whoever owns the loaded plugins: cli-stdio main, testing-harness PluginHarness, fastmcp-adapter lifespan.
3. Run the task verify command and confirm it passes.

## Notes

Discovered in task `registry` during run `any-mcp`.

