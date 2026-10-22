---
title: Examples small medium
status: todo
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
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
