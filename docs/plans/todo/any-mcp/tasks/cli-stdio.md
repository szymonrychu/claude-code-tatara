---
title: CLI stdio
status: todo
repo: any-mcp
value: "any-mcp runs as a well-behaved local stdio MCP server, the default transport"
files: [src/any_mcp/cli.py, src/any_mcp/__main__.py, src/any_mcp/log.py, tests/test_cli.py, tests/fixtures/stdio_plugin.py]
verify: "uv run --frozen pytest tests/test_cli.py -q && mise run lint"
depends_on: [fastmcp-adapter]
owns: [any-mcp-cli]
uses: [fastmcp-adapter, plugin-loader, any-mcp-config]
model: sonnet
estimate: 6
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

# CLI stdio

## Requirement

Ship the `any-mcp` command with the stdio transport (design D4, D5, D10). This is the `any-mcp-cli` contract the agent-orchestrator image calls as `any-mcp --config /etc/any-mcp/any-mcp.yaml`.

- `build_parser()` flags: `--config PATH` (default from `ANY_MCP_CONFIG`), `--plugin REF` (repeatable; with `--config` the entries are appended), `--transport {stdio}` (default from config, else `stdio`), `--log-level {debug,info,warning,error}`, `--list-tools`, `--version` (prints `any-mcp <version>`).
- `main(argv=None) -> int`: neither a config nor a plugin gives exit 78 and one stderr line `any-mcp: no config: pass --config, --plugin or set ANY_MCP_CONFIG`. A `ConfigError` from loading, discovery or registry start gives exit 78 and one stderr line naming the key or plugin; nothing is written to stdout.
- `--list-tools`: start the plugins, print the exposed tools (name, description, input schema) as a JSON array on stdout, tear down, exit 0.
- stdio: `src/any_mcp/log.py` `configure(level)` sends every log record to stderr; stdout carries only MCP messages; the process exits 0 on stdin EOF and on SIGTERM, after plugin teardown.
- `src/any_mcp/__main__.py` makes `python -m any_mcp` equal to the console script.
- Both protocol eras work over stdio: a handshake-era `initialize` (`2025-11-25`) and a 2026-07-28 `server/discover`, each followed by `tools/list` and `tools/call`.

## Acceptance conditions

- AC1: any-mcp --help exits 0 listing every flag and --version prints the package version [evidence: test:tests/test_cli.py::test_help_and_version]
- AC2: with no config, no plugin and no ANY_MCP_CONFIG the command exits 78 with the one-line message [evidence: test:tests/test_cli.py::test_no_config_exits_78]
- AC3: an invalid config or unloadable plugin exits 78 with one stderr line naming it and empty stdout [evidence: test:tests/test_cli.py::test_config_errors_exit_78]
- AC4: --list-tools prints the exposed tools as JSON and exits 0 [evidence: test:tests/test_cli.py::test_list_tools_flag]
- AC5: over stdio a handshake-era client initializes, lists and calls a tool [evidence: test:tests/test_cli.py::test_stdio_legacy_handshake]
- AC6: over stdio a 2026-07-28 client discovers, lists (with ttlMs) and calls a tool [evidence: test:tests/test_cli.py::test_stdio_modern_discover]
- AC7: every stdout line is a JSON-RPC message while the plugin logs and a call fails [evidence: test:tests/test_cli.py::test_stdout_only_mcp_messages]
- AC8: closing stdin exits 0 within 5 seconds after plugin teardown [evidence: test:tests/test_cli.py::test_exit_on_stdin_eof]
- AC9: SIGTERM tears plugins down and the process exits [evidence: test:tests/test_cli.py::test_sigterm_teardown]
- AC10: ANY_MCP_CONFIG is used when --config is absent [evidence: test:tests/test_cli.py::test_config_from_env]
- AC11: lint passes [evidence: command:mise run lint]

## Files

- `src/any_mcp/cli.py`
- `src/any_mcp/__main__.py`
- `src/any_mcp/log.py`
- `tests/test_cli.py`
- `tests/fixtures/stdio_plugin.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
