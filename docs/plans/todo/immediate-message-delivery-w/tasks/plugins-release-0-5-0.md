---
title: plugins release 0.7.0
status: todo
repo: any-mcp-tatara-plugins
value: the orchestrator can pin a plugins release whose session_send offers a priority
files: [orchestration/orchestrator/pyproject.toml, uv.lock, orchestration/orchestrator/README.md, tests/test_source_install.py]
verify: "uv run --frozen pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint"
depends_on: [plugin-session-send-priority]
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

# plugins release 0.7.0

## Requirement

Design D15, verbatim: "Released as plugins 0.7.0 on top of session-orchestration-mcp's 0.7.0; the orchestrator pins it."

Design D19, verbatim: "claude-code-wrapper 0.5.0, any-mcp-tatara-plugins 0.7.0 and agents-common 0.5.0 are version bumps whose tags the orchestrator session pushes after merge (checked by it, not by the implementer)."

Scope (any-mcp-tatara-plugins): `orchestration/orchestrator/pyproject.toml` (0.7.0 to 0.7.0), `uv.lock`, `orchestration/orchestrator/README.md` (example ref), `tests/test_source_install.py` (the version pin, no longer accurate after the bump).

## Acceptance conditions

- ac1: the plugin's pyproject and installed metadata say 0.7.0 (updated, named) [evidence: test:tests/test_source_install.py::test_orchestrator_distribution_metadata]
- ac2: the plugin README example pins the new release and no older one [evidence: command:test "$(grep -oE "ref=v[0-9.]+" orchestration/orchestrator/README.md | sort -u)" = "ref=v0.7.0"]
- ac3: (checked by the orchestrator session after it pushed the tag) tag v0.7.0 exists on origin at the merge commit, on top of v0.7.0 [evidence: command:test -n "$(git ls-remote --tags origin v0.7.0)" && git merge-base --is-ancestor v0.7.0 v0.7.0]
- ac4: the release is built on v0.7.0, the live baseline [evidence: command:git merge-base --is-ancestor v0.7.0 HEAD]
- ac5: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint]

## Files

- `orchestration/orchestrator/pyproject.toml`
- `uv.lock`
- `orchestration/orchestrator/README.md`
- `tests/test_source_install.py`

## Interfaces

- `orchestration/orchestrator/pyproject.toml` `[project].version = "0.7.0"`; README example `ref=v0.7.0`.

## Expected outcome

A tagged plugins release with the priority parameter exists for the orchestrator to pin.

## Steps

- Read `orchestration/orchestrator/pyproject.toml`, `orchestration/orchestrator/README.md`, `tests/test_source_install.py` and hive-decoupling's plugins-release-0-4-0 task in one pass.
- Version bump with no behaviour change (TDD exception): bump, `uv lock`, update the metadata pin and the README ref.
- Run the task's verify; expect all passed. Quote the summary line.

## Notes

- Id kept from an earlier numbering; it releases v0.7.0.
- The tag is pushed by the orchestrator session after the PR merges green; ac3 is checked by it.
- If 0.7.0 is taken at build time, take the next free minor and report it so the orchestrator amends this task and orch-plugins-pin-0-5-0.
- Before the tag, the orchestrator session proposes the exact version through mx-34 (epic, live version, what it replaces) and tags only after tatara confirms (standing user rule, mx-34 #396, 2026-10-29). Renumbered 0.5.0 to 0.7.0 because slash took plugins 0.5.0 (user approval, mx-34 #406), then 0.7.0 to 0.7.0 because session-orchestration-mcp takes plugins v0.7.0 (the live baseline; latest tag v0.5.1; mx-34 #469/#470, 2026-10-29).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: agents-common renumbered 0.4.0 -> 0.5.0: the slash fix round takes v0.4.0 (mx-34 #446, #453)

- 2026-10-29 amended: plugins release renumbered v0.6.0 -> v0.7.0 (mx-34 #469/#470): built on session-orchestration-mcp's v0.6.0
