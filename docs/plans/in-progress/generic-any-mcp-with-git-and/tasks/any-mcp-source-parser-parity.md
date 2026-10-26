---
title: any-mcp source parser parity with the web grammar
status: todo
repo: any-mcp
value: any-mcp and the web form accept exactly the same remote sources
files: [src/any_mcp/sources.py, tests/test_sources.py]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest -q -o addopts=\"\" tests/test_sources.py && mise run lint"
depends_on: [anymcp-source-installer]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 658840
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# any-mcp source parser parity with the web grammar

## Requirement

Review finding (2026-10-27, web-plugin-source-parser review, parity check against src/any_mcp/sources.py): any-mcp's parser accepts git sources the design's grammar (D8: `git::https://<host>/<path>`) does not: `git::https://github.com` and `git::https://github.com/` (no repo path), `git::https://host//sub` and `git::https:///x` (empty host or empty repo path before the `//` subdir separator), and locations containing whitespace or control characters such as a newline. Tighten `_parse_git` so a git location must be an http(s) or other allowed scheme URL with a non-empty host and a non-empty repo path, and no whitespace or control characters anywhere in the source; each refusal uses the existing `plugin source '<text>': <problem>` message form. The agents-web parser (src/presets/pluginSource.ts in the web tree) already refuses these; after this task both parsers decide identically on the remote https subset.

## Acceptance conditions

- ac1: git sources with no repo path (`git::https://github.com`, `git::https://github.com/`, `git::https://host//sub`) and with an empty host (`git::https:///x`) are refused with a message naming the problem [evidence: test:tests/test_sources.py::test_git_location_needs_host_and_path]
- ac2: sources containing whitespace or control characters (space, tab, newline) are refused [evidence: test:tests/test_sources.py::test_whitespace_and_control_refused]
- ac3: the parser tests, nomenclature and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q -o addopts="" tests/test_sources.py tests/test_nomenclature.py && mise run lint]

## Files

- `src/any_mcp/sources.py`
- `tests/test_sources.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
