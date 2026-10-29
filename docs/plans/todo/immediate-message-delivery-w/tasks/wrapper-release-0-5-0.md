---
title: wrapper release 0.5.0
status: todo
repo: claude-code-wrapper
value: the orchestrator can pin a wrapper release that delivers messages mid-turn
files: [pyproject.toml, uv.lock, src/claude_code_wrapper/__init__.py, tests/test_packaging.py]
verify: "uv run pytest tests/test_packaging.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-peer-priority, wrapper-paste-hygiene]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 632059
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper release 0.5.0

## Requirement

Design D19, verbatim: "claude-code-wrapper 0.5.0, any-mcp-tatara-plugins 0.7.0 and agents-common 0.5.0 are version bumps whose tags the orchestrator session pushes after merge (checked by it, not by the implementer). [...] The wrapper is pinned by its release tag, cut before the orchestrator task (retro file-editor-with-tabs-and-hi: Harbor prunes sha7 tags)."

Design Constraints, verbatim: "This epic therefore takes migration 0014, wrapper 0.5.0, plugins 0.7.0 (negotiated 2026-10-29, mx-34 #469/#470); when a number is taken at build time the task takes the next free one and the orchestrator amends its `files`."

Scope (claude-code-wrapper): `pyproject.toml` and `src/claude_code_wrapper/__init__.py` (0.4.1 from the slash epic's fix round to 0.5.0), `uv.lock`, `tests/test_packaging.py` (the version pin, if it names the version).

## Acceptance conditions

- ac1: the version is 0.5.0 in pyproject and the package, and the branch contains the v0.4.1 tag commit [evidence: command:grep -q '^version = "0.5.0"' pyproject.toml && grep -q '__version__ = "0.5.0"' src/claude_code_wrapper/__init__.py && git merge-base --is-ancestor v0.4.1 HEAD]
- ac2: the built wheel installs and reports its version [evidence: test:tests/test_packaging.py::test_wheel_installs_and_ccw_version]
- ac3: (checked by the orchestrator session after it pushed the tag) tag v0.5.0 exists on origin at the merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.5.0)"]
- ac4: packaging tests and lint pass [evidence: command:uv run pytest tests/test_packaging.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `src/claude_code_wrapper/__init__.py`
- `tests/test_packaging.py`

## Interfaces

- Version string `0.5.0` in `pyproject.toml` `[project].version` and `claude_code_wrapper.__version__`; `uv.lock` regenerated with `uv lock`.

## Expected outcome

A wrapper release carrying the mid-turn merge, the bounded Stop defer, the paste hygiene and the peer priority exists for the orchestrator to pin by tag.

## Steps

- Read `pyproject.toml`, `src/claude_code_wrapper/__init__.py`, `tests/test_packaging.py` and the slash epic's wrapper-release-0-4-1 task in one pass.
- Bump the version, run `uv lock`; this is a version bump with no behaviour change (TDD exception: dependency or version bump), so there is no red step; if `tests/test_packaging.py` names the version, update that pin (no longer accurate after the bump).
- Run the task's verify; expect all passed. Quote the summary line.

## Notes

- The tag is pushed by the orchestrator session after the PR merges green; ac3 is checked by it, not by the implementer or reviewer.
- If 0.5.0 is taken at build time, take the next free minor and report it so the orchestrator amends this task and orch-wrapper-pin-0-5-0.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: agents-common renumbered 0.4.0 -> 0.5.0: the slash fix round takes v0.4.0 (mx-34 #446, #453)

- 2026-10-29 amended: slash baseline is wrapper 0.4.1 (fix round); immediate delivery still releases 0.5.0

- 2026-10-29 amended: design quotes follow the design: migration 0014, plugins 0.7.0 (mx-34 #469/#470)
