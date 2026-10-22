---
title: Examples small medium
status: in-progress
repo: any-mcp
value: "Runnable, tested small and medium plugins users can copy"
files: [examples/hello/hello.py, examples/hello/any-mcp.yaml, examples/single_endpoint/zippopotam.py, examples/single_endpoint/any-mcp.yaml, examples/github_issues/github_issues.py, examples/github_issues/any-mcp.yaml, tests/test_examples_small.py]
verify: "uv run --frozen pytest tests/test_examples_small.py tests/test_import_boundary.py -q && mise run lint"
depends_on: [testing-harness, cli-stdio]
owns: []
uses: [plugin-abc, plugin-harness, any-mcp-cli]
model: sonnet
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/any-mcp-examples-small-medium/any-mcp
branch: any-mcp-examples-small-medium
verified_head: ""
run: any-mcp
provides: []
acs_for_audit: []
process_gaps: []
---

# Examples small medium

## Requirement

Write the small and medium example plugins, runnable and tested offline (design D13, D14).

- `examples/hello/hello.py`: the hello-world plugin, one class `Hello` with `name = "hello"` and one `@tool` method `greet(name: str) -> str` returning `Hello, <name>!`; at most 15 lines. `examples/hello/any-mcp.yaml` runs it (`python_path: ["."]`, `plugin: hello:Hello`).
- `examples/single_endpoint/zippopotam.py`: a plugin whose `load_tools()` returns one `ToolSpec` with an `HttpBinding` (`GET /{country}/{postal_code}` on `https://api.zippopotam.us`, an input schema with both properties required) and no `call` code. `examples/single_endpoint/any-mcp.yaml` runs it.
- `examples/github_issues/github_issues.py`: a decorator-based multi-tool plugin with `Config(token: str, base_url: str = "https://api.github.com", read_only: bool = True)`; tools `list_issues(repo, state="open", limit=10)`, `get_issue(repo, number)`, `add_comment(repo, number, body)` using `self.ctx.http`; `credentials()` returns `Authorization: Bearer <token>` and the GitHub `Accept` and API-version headers; `before_call` raises `Deny` for `add_comment` while `read_only`; `shape_response` projects issues to `number`, `title`, `state`, `url`. `examples/github_issues/any-mcp.yaml` sets `token: ${GITHUB_TOKEN}`.
- `tests/test_examples_small.py` runs each example through `PluginHarness` with an `httpx.MockTransport`, and the hello example through the CLI (`python -m any_mcp --config examples/hello/any-mcp.yaml --list-tools`).

## Acceptance conditions

- AC1: the hello plugin is at most 15 lines and its greet tool returns Hello, Ada! through the harness [evidence: test:tests/test_examples_small.py::test_hello_example]
- AC2: the hello config runs through the CLI and lists hello_greet [evidence: test:tests/test_examples_small.py::test_hello_cli_list_tools]
- AC3: the single-endpoint plugin has no call code and sends GET /us/90210 through the harness [evidence: test:tests/test_examples_small.py::test_single_endpoint_example]
- AC4: the github_issues plugin lists, gets and comments with the bearer token, denies add_comment while read_only and projects issue fields [evidence: test:tests/test_examples_small.py::test_github_issues_example]
- AC5: every example config loads with load_config given the variables it names [evidence: test:tests/test_examples_small.py::test_example_configs_load]
- AC6: the import boundary holds for the examples and lint passes [evidence: command:uv run --frozen pytest tests/test_import_boundary.py -q && mise run lint]

## Files

- `examples/hello/hello.py`
- `examples/hello/any-mcp.yaml`
- `examples/single_endpoint/zippopotam.py`
- `examples/single_endpoint/any-mcp.yaml`
- `examples/github_issues/github_issues.py`
- `examples/github_issues/any-mcp.yaml`
- `tests/test_examples_small.py`

## Interfaces

Example files only; they use the public `any_mcp` API (`Plugin`, `tool`, `ToolSpec`, `HttpBinding`, `Deny`) and `any_mcp.testing.PluginHarness`. The docs-authoring task embeds `examples/hello/hello.py` and `examples/single_endpoint/zippopotam.py` verbatim.

## Expected outcome

`any-mcp --config examples/hello/any-mcp.yaml` works from a checkout, and with `GITHUB_TOKEN` set so does the github_issues example against the real API.

## Steps

- Write `tests/test_examples_small.py` (add each `examples/<name>` directory to the harness via `python_path` or `from_config`); run `uv run --frozen pytest tests/test_examples_small.py -q`; expect failures.
- Write the examples; rerun (all pass), then `uv run --frozen pytest tests/test_import_boundary.py -q` and `mise run lint`.

## Notes

Examples are documentation: keep each one short, commented where a reader needs it, and free of FastMCP imports (the boundary test scans `examples/`). Ruff lints `examples/` too.

- 2026-10-23 run any-mcp: dependency-failed on cli-stdio
