---
title: Testing harness
status: todo
repo: any-mcp
value: "Plugin authors test a plugin in memory, offline, through the real server"
files: [src/any_mcp/testing.py, tests/test_testing_harness.py]
verify: "uv run --frozen pytest tests/test_testing_harness.py tests/test_import_boundary.py -q && mise run lint"
depends_on: [fastmcp-adapter]
owns: [plugin-harness]
uses: [fastmcp-adapter, plugin-loader, plugin-abc]
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

# Testing harness

## Requirement

Give plugin authors an in-memory harness that drives a plugin through the real server (design D13).

- `PluginHarness(plugin, *, config=None, name=None, namespace=None, transport=None, tools=None)`: `plugin` is a `Plugin` subclass or a reference string; builds a one-entry `AnyMcpConfig`, loads it with `load_plugins(..., http_transport=transport)`, builds the registry and server, and serves it with `in_memory_client`. Async context manager: entering starts the plugins, exiting tears them down.
- `PluginHarness.from_config(path, *, transport=None)` does the same for a whole config file (relative `python_path` resolved against the file).
- `list_tools() -> list[dict]` returns tools as a client sees them; `call(tool, arguments=None) -> HarnessResult` accepts a plugin-local name (for a one-plugin harness) or an exposed name; `HarnessResult(text, structured, is_error)`; `reload() -> bool`.
- A `ConfigError` (bad plugin config, failing setup) is raised on entering, unchanged.
- `testing.py` reaches FastMCP only through `_fastmcp_adapter`.

## Acceptance conditions

- AC1: the harness lists a plugin's tools as an MCP client sees them [evidence: test:tests/test_testing_harness.py::test_harness_lists_tools]
- AC2: call accepts the local or the exposed name and returns text, structured and is_error [evidence: test:tests/test_testing_harness.py::test_harness_call]
- AC3: a MockTransport routes every ctx.http request so no network is used [evidence: test:tests/test_testing_harness.py::test_harness_mock_transport]
- AC4: from_config serves a multi-plugin config with python_path relative to the file [evidence: test:tests/test_testing_harness.py::test_harness_from_config]
- AC5: reload returns the changed flag and the next list_tools is current [evidence: test:tests/test_testing_harness.py::test_harness_reload]
- AC6: a plugin config error raises ConfigError on entering [evidence: test:tests/test_testing_harness.py::test_harness_config_error]
- AC7: leaving the harness tears the plugins down [evidence: test:tests/test_testing_harness.py::test_harness_teardown]
- AC8: the import boundary still holds and lint passes [evidence: command:uv run --frozen pytest tests/test_import_boundary.py -q && mise run lint]

## Files

- `src/any_mcp/testing.py`
- `tests/test_testing_harness.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
