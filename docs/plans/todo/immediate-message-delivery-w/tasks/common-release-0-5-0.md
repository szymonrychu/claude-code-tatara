---
title: common release 0.5.0
status: todo
repo: agents-common
value: "the Matrix connector can pin an agents-common release that exposes the message's turn"
files: [pyproject.toml, uv.lock, tests/test_release.py, README.md]
verify: "uv run pytest tests/test_release.py tests/test_package.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [common-message-turn-id]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 627200
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# common release 0.5.0

## Requirement

Design D19, verbatim: "claude-code-wrapper 0.5.0, any-mcp-tatara-plugins 0.7.0 and agents-common 0.5.0 are version bumps whose tags the orchestrator session pushes after merge (checked by it, not by the implementer). [...] the connector pins agents-common v0.5.0."

Scope (agents-common): `pyproject.toml` (0.4.0 to 0.5.0), `uv.lock`, `tests/test_release.py` (the version and install pins), `README.md` (install line).

## Acceptance conditions

- ac1: pyproject, installed metadata and __version__ agree on 0.5.0 (updated, named) [evidence: test:tests/test_release.py::test_versions_agree]
- ac2: the README install line and the release test pin v0.5.0 and no older tag [evidence: command:grep -q 'agents-common@v0.5.0' README.md && ! grep -q 'agents-common@v0.4.0' README.md && grep -q 'agents-common@v0.5.0' tests/test_release.py]
- ac3: (checked by the orchestrator session after it pushed the tag) tag v0.5.0 exists on origin at the merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.5.0)"]
- ac4: release and package tests and lint pass [evidence: command:uv run pytest tests/test_release.py tests/test_package.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `tests/test_release.py`
- `README.md`

## Interfaces

- `[project].version = "0.5.0"`; `tests/test_release.py` `INSTALL` and the asserted version move to 0.5.0.

## Expected outcome

A tagged agents-common release with `Message.turn_id` exists for the Matrix connector to pin.

## Steps

- Read `pyproject.toml`, `README.md`, `tests/test_release.py` and `tests/test_package.py` in one pass.
- Bump the version, run `uv lock`, update the two pins in `tests/test_release.py` (no longer accurate after the bump) and the README install line; version bump with no behaviour change (TDD exception), so no red step.
- Run the task's verify; expect all passed. Quote the summary line.

## Notes

- The tag is pushed by the orchestrator session after the PR merges green; ac3 is checked by it.
- If the README has no install line with the tag, add one next to the existing usage section rather than inventing a new section.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
- Renumbered 0.4.0 to 0.5.0 (2026-10-29): the slash-commands-from-chat fix round takes agents-common v0.4.0 (run tracker command outcomes; user and mx-34 confirmed, #446). Build on v0.4.0; propose the exact tag through mx-34 before tagging (rule #396).

- 2026-10-29 amended: D19 quote follows the design: plugins 0.7.0 (mx-34 #469/#470)
