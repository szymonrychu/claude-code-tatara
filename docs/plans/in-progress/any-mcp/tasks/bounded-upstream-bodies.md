---
title: bounded upstream bodies
status: todo
repo: any-mcp
value: a large or hostile upstream cannot exhaust memory
files: [src/any_mcp/http.py, src/any_mcp/openapi.py, src/any_mcp/config.py, tests/test_http_binding.py, tests/test_openapi.py]
verify: "uv run --frozen pytest tests/test_http_binding.py tests/test_openapi.py -q && mise run lint"
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

# bounded upstream bodies

## Requirement

Security finding (medium): http.py:139-145 buffers the full upstream body (client.send then response.content) before the response budget truncates it, and openapi._read_spec (openapi.py:93) does the same for spec downloads. Stream both with a max-bytes cap (the existing response budget for tool calls; a configurable spec cap, default 10 MiB, for specs): stop reading at the cap, return the truncated/limit result exactly as the budget does today for tool calls, and a ConfigError for an oversize spec.

## Acceptance conditions

- AC1: a tool call against an upstream larger than the cap reads at most the cap and returns the budget result [evidence: test:tests/test_http_binding.py::test_upstream_body_streamed_with_cap]
- AC2: an oversize spec download fails with ConfigError without reading past the cap [evidence: test:tests/test_openapi.py::test_spec_download_capped]

## Files

- `src/any_mcp/http.py`
- `src/any_mcp/openapi.py`
- `src/any_mcp/config.py`
- `tests/test_http_binding.py`
- `tests/test_openapi.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
