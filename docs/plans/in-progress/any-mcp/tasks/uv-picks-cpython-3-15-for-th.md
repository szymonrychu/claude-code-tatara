---
title: "uv picks CPython 3.15 for the .venv even though mise.toml pins python 3.12. There is no .python-version file and requires-python is >=3.12, so tests run on 3.15 rather than the 3.12 the agent image ships."
status: done
repo: any-mcp
value: A test environment that differs from the target image can hide 3.12-only failures.
files: [.python-version, tests/test_package.py]
verify: "uv run --frozen pytest tests/test_package.py -q && mise run lint"
depends_on: [scaffold]
owns: []
uses: []
model: ""
estimate: ""
estimate_by: ""
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/any-mcp-uv-picks-cpython-3-15-for-th/any-mcp
branch: any-mcp-uv-picks-cpython-3-15-for-th
verified_head: 45351e763ad72b742e073174e40a2ee88571e445
run: any-mcp
provides: []
acs_for_audit: []
process_gaps: []
---

# uv picks CPython 3.15 for the .venv even though mise.toml pins python 3.12. There is no .python-version file and requires-python is >=3.12, so tests run on 3.15 rather than the 3.12 the agent image ships.

## Requirement

uv must build the .venv on Python 3.12, the version mise.toml pins and the agent image ships: add a .python-version file pinning 3.12 (keep requires-python >=3.12), and a test that .python-version and mise.toml agree on 3.12 and that the running interpreter in the test venv is 3.12.

## Acceptance conditions

- AC1: .python-version pins 3.12 and matches mise.toml [evidence: test:tests/test_package.py::test_python_version_pinned_to_312]
- AC2: the test interpreter is 3.12 [evidence: test:tests/test_package.py::test_interpreter_is_312]

## Files

- `.python-version`
- `tests/test_package.py`

## Expected outcome

Tests run on the same Python as the agent image.

## Steps

- Write the failing tests; run red.
- Add .python-version, recreate the venv; run green.
