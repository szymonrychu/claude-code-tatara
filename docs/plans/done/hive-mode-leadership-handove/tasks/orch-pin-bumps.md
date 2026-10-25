---
title: orch pin bumps
status: done
repo: agent-orchestrator
value: the orchestrator renders against the released plugin and wrapper
files: [pyproject.toml, uv.lock, src/agent_orchestrator/settings.py, README.md, e2e/agent-test.Dockerfile, tests/test_images.py]
verify: "uv run pytest tests/test_images.py tests/test_render.py tests/test_settings.py tests/test_fake_wrapper_contract.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [any-mcp-release-v0-2-0, wrapper-release-0-2-0, agent-port-listener]
owns: [orch-hive-pins]
uses: [any-mcp-release-v0-2-0, wrapper-release-0-2-0]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/hive-mode-leadership-handove-orch-pin-bumps/agent-orchestrator
branch: hive-mode-leadership-handove-orch-pin-bumps
verified_head: b05d82f95f1a003e128039eedc2c03149214392b
run: hand-orchestrated-2026-10-25
provides: []
acs_for_audit: []
process_gaps: []
---

# orch pin bumps

## Requirement

Foundation part F3, pins. Pin agent-orchestrator to any-mcp `v0.2.0` and to the claude-code-wrapper `main` merge commit that carries the notes inbox and `claude.main_agent_only_tools` (version 0.2.0):

- `pyproject.toml`: `any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.2.0` and the wrapper dev dependency `claude-code-wrapper @ git+https://github.com/szymonrychu/claude-code-wrapper@<merge sha>`; `uv lock`.
- `settings.py`: `any_mcp_ref = "v0.2.0"`.
- README `## Images`: recommended agent image `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>` and the `ORCH_ANY_MCP_REF` default.
- `e2e/agent-test.Dockerfile`: `BASE_IMAGE` tag and `WRAPPER_SHA` at the same commit.
- `tests/test_images.py` equality tests (pyproject any-mcp ref equals `Settings.any_mcp_ref`; wrapper sha agrees across pyproject, uv.lock, README and the Dockerfile) pass; `tests/test_render.py` still validates the rendered config against the new wrapper schema.

The merge sha is filled in by amendment when the wrapper PR merges (precedent: done epic web-ui-cluster-tabs-with-fil task wrapper-sha-pin). Dependency bump: the TDD exception for a dependency bump applies to the pin values; the equality tests are the guard.

## Acceptance conditions

- AC1: pyproject any-mcp ref and Settings.any_mcp_ref both say v0.2.0 [evidence: command:uv run pytest tests/test_images.py -q]
- AC2: pyproject, uv.lock, README Images and the agent-test Dockerfile name the same wrapper commit [evidence: test:tests/test_images.py::test_agent_test_dockerfile_matches_dev_dependency]
- AC3: the rendered ccw config validates against the pinned wrapper [evidence: command:uv run pytest tests/test_render.py tests/test_settings.py -q]
- AC4: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `pyproject.toml`
- `uv.lock`
- `src/agent_orchestrator/settings.py`
- `README.md`
- `e2e/agent-test.Dockerfile`
- `tests/test_images.py`

## Interfaces

- Owns part `orch-hive-pins`: any-mcp `v0.2.0` and the wrapper 0.2.0 merge commit across pyproject, uv.lock, settings, README, Dockerfile.

## Expected outcome

The orchestrator validates and renders against the released plugin and wrapper.

## Steps

- Change the pins (dependency-bump exception); run `uv run pytest tests/test_images.py -q`: the equality tests fail until every pin agrees, then pass.
- Run the verify command: passes.

## Notes

- `tests/test_images.py:106-112` ties the any-mcp ref to `Settings.any_mcp_ref`.
- The wrapper merge sha comes from the orchestrator's amendment after the wrapper PR merges.
