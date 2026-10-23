---
title: http auth on non loopback
status: todo
repo: any-mcp
value: an HTTP server reachable beyond loopback is never unauthenticated by accident
files: [src/any_mcp/_fastmcp_adapter.py, src/any_mcp/cli.py, src/any_mcp/config.py, docs/transports.md, tests/test_http_transport.py]
verify: "uv run --frozen pytest tests/test_http_transport.py tests/test_docs_reference.py -q && mise run lint"
depends_on: []
owns: []
uses: []
model: ""
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

# http auth on non loopback

## Requirement

Security finding (medium): _fastmcp_adapter.py:454-460 only warns when HTTP binds a non-loopback host without a bearer token. Refuse to start in that case (exit code 78, clear message) unless an explicit --insecure flag (and config key) is set, which keeps today's warning. docs/transports.md Security section states the rule and that TLS must terminate at a reverse proxy. stdio is unaffected.

## Acceptance conditions

- AC1: non-loopback bind without a token exits 78 [evidence: test:tests/test_http_transport.py::test_non_loopback_without_token_refused]
- AC2: --insecure allows it with the warning [evidence: test:tests/test_http_transport.py::test_insecure_flag_allows_with_warning]
- AC3: transports doc states the rule [evidence: test:tests/test_docs_reference.py]

## Files

- `src/any_mcp/_fastmcp_adapter.py`
- `src/any_mcp/cli.py`
- `src/any_mcp/config.py`
- `docs/transports.md`
- `tests/test_http_transport.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
