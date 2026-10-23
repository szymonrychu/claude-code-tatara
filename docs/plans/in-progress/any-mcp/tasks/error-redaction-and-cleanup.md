---
title: error redaction and cleanup
status: in-progress
repo: any-mcp
value: tool errors never echo credentials and HTTP clients always close
files: [src/any_mcp/errors.py, src/any_mcp/discovery.py, src/any_mcp/cli.py, src/any_mcp/openapi.py, docs/configuration.md, tests/test_pipeline.py, tests/test_cli.py, tests/test_discovery.py]
verify: "uv run --frozen pytest tests/test_pipeline.py tests/test_cli.py tests/test_discovery.py tests/test_docs_reference.py -q && mise run lint"
depends_on: [bounded-upstream-bodies, call-pipeline, cli-stdio, core-types, docs-reference, http-auth-on-non-loopback, http-transport, nothing-ever-calls-aclose-on, openapi-credential-hosts, openapi-plugin, plugin-discovery]
owns: []
uses: []
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/any-mcp-error-redaction-and-cleanup/any-mcp
branch: any-mcp-error-redaction-and-cleanup
verified_head: ""
run: ""
provides: []
---

# error redaction and cleanup

## Requirement

Security finding (low): errors.py:68-69 returns up to 500 chars of the upstream body in tool errors; redact every configured credential value (bearer token, header values) from it, and strip query strings from URLs in ConfigError messages for spec fetches (openapi.py:96). Review findings (medium): cli._list_tools awaits registry.start() before its try, so a failing plugin setup skips loaded.aclose(); move it inside so clients always close. LoadedPlugins.aclose (discovery.py:42-46) closes clients in a loop without isolation; close every client even if one raises, then re-raise the first error. docs/configuration.md states that plugin references (module:Class, python_path, entry points) import operator-supplied code, so a config file is trusted like code.

## Acceptance conditions

- AC1: a credential reflected in an upstream error body is redacted [evidence: test:tests/test_pipeline.py::test_error_body_redacts_credentials]
- AC2: list-tools closes clients when plugin setup fails [evidence: test:tests/test_cli.py::test_list_tools_closes_clients_on_setup_failure]
- AC3: aclose closes every client when one raises [evidence: test:tests/test_discovery.py::test_aclose_isolates_client_errors]
- AC4: configuration doc states the plugin trust model [evidence: test:tests/test_docs_reference.py]

## Files

- `src/any_mcp/errors.py`
- `src/any_mcp/discovery.py`
- `src/any_mcp/cli.py`
- `src/any_mcp/openapi.py`
- `docs/configuration.md`
- `tests/test_pipeline.py`
- `tests/test_cli.py`
- `tests/test_discovery.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The requirement holds, pinned by the acceptance tests.

What is true and observable when the task is done.

## Steps

- Write the failing acceptance tests; run red.
- Implement; run green with the verify command.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
