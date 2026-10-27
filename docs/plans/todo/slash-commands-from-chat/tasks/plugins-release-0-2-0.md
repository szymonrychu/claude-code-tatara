---
title: plugins release 0.2.0
status: todo
repo: any-mcp-tatara-plugins
value: superleaders can install the orchestrator plugin whose session_send says what slash text does
files: [orchestration/orchestrator/pyproject.toml, uv.lock, orchestration/orchestrator/README.md, tests/test_source_install.py]
verify: "uv run pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [plugin-session-send-slash]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 656326
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# plugins release 0.2.0

## Requirement

Goal G2 (README), verbatim: "A superleader can send a slash command to a target session and it runs as a command, not as framed prompt text."

Open question Q1 of design.md, verbatim: "Release any-mcp-tatara-plugins v0.2.0 after plugin-session-send-slash merges and bump the orchestrator's plugins pin (ORCH_ANY_MCP_PLUGINS_REF default, the any-mcp-tatara-orchestrator dev dependency, README, tests) to v0.2.0, as two small tasks added at the gate, so superleaders actually see the new session_send description? Without them the description change stays unreleased." Settled by the builder check (user decision, verbatim): "add two tasks, any-mcp-tatara-plugins release v0.2.0 after plugin-session-send-slash, and an orchestrator plugins pin bump (ORCH_ANY_MCP_PLUGINS_REF, dev dependency, README, tests)".

Design D13, verbatim (the release part): "Release and pin (builder check, my call): any-mcp-tatara-plugins `v0.2.0` after the description change (task plugins-release-0-2-0: version bump; the tag is pushed by the orchestrator session after the merge), then the orchestrator pins it (task orch-plugins-pin-0-2-0: the `ORCH_ANY_MCP_PLUGINS_REF` default, the `any-mcp-tatara-orchestrator` dev dependency, README, tests), so superleaders actually see the description. The helmfile value of `ORCH_ANY_MCP_PLUGINS_REF` stays with the gate's deploy decision."

Repo README `## Releases`, verbatim: "Releases are `vX.Y.Z` tags on `main`; pin `?ref=` to a release tag. Nothing is published beyond the tag."

Scope (any-mcp-tatara-plugins):
- `orchestration/orchestrator/pyproject.toml`: version `0.2.0`; `uv lock` updates `uv.lock`.
- `orchestration/orchestrator/README.md`: the example source pins `?ref=v0.2.0`.
- `tests/test_source_install.py::test_orchestrator_distribution_metadata` is no longer accurate (named): it pins version `0.1.0` in the pyproject and the installed metadata; it asserts `0.2.0`.
- Release step, run by the orchestrator session (never a subagent) once this repo's PR is merged to `main` with green CI: `git tag v0.2.0 <merge sha> && git push origin v0.2.0` (irreversible, listed in design.md). ac3 is checked by the orchestrator after that push, not by the implementer or reviewer.

## Acceptance conditions

- ac1: the plugin's pyproject and installed metadata say 0.2.0 (updated) [evidence: test:tests/test_source_install.py::test_orchestrator_distribution_metadata]
- ac2: the plugin README example pins the new release [evidence: command:grep -q "ref=v0.2.0" orchestration/orchestrator/README.md && ! grep -q "ref=v0.1.0" orchestration/orchestrator/README.md]
- ac3: (checked by the orchestrator session after it pushed the tag) tag v0.2.0 exists on origin at the merge commit [evidence: command:test -n "$(git ls-remote --tags origin v0.2.0)"]
- ac4: targeted tests and lint pass [evidence: command:uv run pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `orchestration/orchestrator/pyproject.toml`
- `uv.lock`
- `orchestration/orchestrator/README.md`
- `tests/test_source_install.py`

## Interfaces

- Distribution `any-mcp-tatara-orchestrator` version `0.2.0`; git tag `v0.2.0` on the `main` merge commit.

## Expected outcome

The orchestrator plugin with the new session_send description is released as tag v0.2.0, so the orchestrator can pin it.

## Steps

- Red: change `test_orchestrator_distribution_metadata` to 0.2.0; run `uv run pytest tests/test_source_install.py::test_orchestrator_distribution_metadata`: fails.
- Green: bump the plugin pyproject, `uv lock`, the plugin README example; run the task's verify: passes. Quote the summary line.
- After the merge (orchestrator session): wait for CI green on the merge commit, `git tag v0.2.0 <merge sha> && git push origin v0.2.0`, then check ac3.

## Notes

- Dependency-bump TDD exception for the version values; the metadata test is the guard.
- The tag push is an orchestrator-session step (retro proposal: plan live steps as orchestrator-run).
- Depends on plugin-session-send-slash.
