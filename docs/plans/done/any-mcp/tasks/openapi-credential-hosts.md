---
title: openapi credential hosts
status: done
repo: any-mcp
value: credentials never reach a host the operator did not configure
files: [src/any_mcp/openapi.py, src/any_mcp/http.py, tests/test_openapi.py]
verify: "uv run --frozen pytest tests/test_openapi.py tests/test_http_binding.py -q && mise run lint"
depends_on: [http-binding, openapi-plugin]
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/any-mcp-openapi-credential-hosts/any-mcp
branch: "HEAD (worktree any-mcp-openapi-credential-hosts)"
verified_head: 4ece80b7a74121ff60ee4cd0c3183d465793c388
run: any-mcp
provides: []
acs_for_audit: []
process_gaps: []
---

# openapi credential hosts

## Requirement

Security finding (medium): a remote or compromised OpenAPI spec can set servers[0].url (used when base_url is unset, openapi.py:122-136) or an absolute-URL path key, and http._url (http.py:91-93) returns absolute paths as-is, so the plugin's bearer token and headers (openapi.py:82-86) go to an attacker host. Fix: _url rejects absolute-URL paths (scheme://) with a ConfigError at tool build time; a spec fetched by URL requires base_url or a servers URL with the same origin as the spec URL; a local-file spec without base_url uses servers[0] only if it is http(s). Also: OpenAPI tool input schemas set additionalProperties: false so unknown arguments are rejected by validation instead of silently ignored (openapi.py:224).

## Acceptance conditions

- AC1: an absolute-URL path key is rejected at load [evidence: test:tests/test_openapi.py::test_absolute_url_path_rejected]
- AC2: a URL spec whose servers origin differs from the spec origin without base_url is refused [evidence: test:tests/test_openapi.py::test_cross_origin_servers_refused_without_base_url]
- AC3: unknown arguments to an OpenAPI tool fail validation [evidence: test:tests/test_openapi.py::test_unknown_arguments_rejected]

## Files

- `src/any_mcp/openapi.py`
- `src/any_mcp/http.py`
- `tests/test_openapi.py`

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
