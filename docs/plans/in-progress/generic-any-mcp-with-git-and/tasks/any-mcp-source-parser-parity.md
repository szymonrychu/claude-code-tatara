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

Review finding (2026-10-27, web-plugin-source-parser review, parity check against src/any_mcp/sources.py): any-mcp's parser accepts git sources the design's grammar (D8: `git::https://<host>/<path>`) does not: `git::https://github.com` and `git::https://github.com/` (no repo path), `git::https://host//sub` and `git::https:///x` (empty host or empty repo path before the `//` subdir separator), and locations containing control characters such as a newline. Tighten `_parse_git` so a git location must be an http(s) or other allowed scheme URL with a non-empty host and a non-empty repo path, no whitespace in a remote (git:: or github.com) source, and no control characters in any source - a local path may contain spaces (user requirement: local plugin directories keep working); each refusal uses the existing `plugin source '<text>': <problem>` message form. The agents-web parser (src/presets/pluginSource.ts in the web tree) already refuses these; after this task both parsers decide identically on the remote https subset.

## Acceptance conditions

- ac1: git sources with no repo path (`git::https://github.com`, `git::https://github.com/`, `git::https://host//sub`) and with an empty host (`git::https:///x`) are refused with a message naming the problem [evidence: test:tests/test_sources.py::test_git_location_needs_host_and_path]
- ac2: remote sources containing whitespace (space, tab) and any source containing a control character (newline, tab in a local path) are refused, while a local path containing a space is accepted [evidence: test:tests/test_sources.py::test_whitespace_and_control_refused]
- ac3: the parser tests, nomenclature and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q -o addopts="" tests/test_sources.py tests/test_nomenclature.py && mise run lint]

## Files

- `src/any_mcp/sources.py`
- `tests/test_sources.py`

## Interfaces

- `src/any_mcp/sources.py:_parse_git` and the top-level parse entry: stricter location checks; public API unchanged.

## Expected outcome

any-mcp refuses every remote source the web form refuses, with the same message form.

## Steps

- Red: add the two tests; run the task's verify; expect failures.
- Green: tighten the parser; run the task's verify and ac3 on the committed HEAD.

## Notes

- Depends on anymcp-source-installer only to serialize work in the any-mcp tree (same file area); no functional dependency.
- Reference: agents-web tree /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/generic-any-mcp-with-git-and/agents-web/src/presets/pluginSource.ts (HOST_AND_PATH) and its tests.
- The orchestrator-side check (task orch-any-mcp-sources-spec) must follow the same rules.

- 2026-10-27 amended: orchestrator over-specified: local paths with spaces must keep working; whitespace refusal limited to remote sources
