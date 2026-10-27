---
title: orch any-mcp 0.5.0 pin
status: done
repo: agents-orchestrator
value: the orchestrator pins generic any-mcp v0.5.0 and the plugins repo tag in one place each
files: [src/agents_orchestrator/settings.py, pyproject.toml, uv.lock, tests/test_settings.py, tests/test_images.py, README.md, tests/golden/session_single.yaml, tests/golden/session_two_peers.yaml]
verify: "unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_settings.py tests/test_images.py tests/test_render.py tests/test_on_start.py && mise run lint"
depends_on: [orch-plugins-dev-dependency, anymcp-release-0-5-0]
model: opus
review: ""
verified_head: 745ca1daa1743320f70bd3fd6c6a54d03252a82e
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: 2
actual_minutes: 3
actual_tokens: 603753
actual_roles: "impl 2, review 1"
actual_role_tokens: "impl 504744, review 99009"
---

# orch any-mcp 0.5.0 pin

## Requirement

Goal G4 (epic README), verbatim: "agents-orchestrator renders the orchestrator plugin from the plugins repo at a pinned ref and accepts a list of extra plugin sources per preset and session, installed in agent pods." Design D7, verbatim: "New settings `any_mcp_plugins_repo` (`ORCH_ANY_MCP_PLUGINS_REPO`, default `https://github.com/szymonrychu/any-mcp-tatara-plugins`) and `any_mcp_plugins_ref` (`ORCH_ANY_MCP_PLUGINS_REF`, default `v0.1.0`, release tag only like `ORCH_ANY_MCP_REF`). ... Settings default `any_mcp_ref` `v0.5.0`." Design D9, verbatim: "`tests/test_images.py` pins the dev dependency tag to `any_mcp_plugins_ref`, as it pins any-mcp's."

Needs a merged upstream: any-mcp tag `v0.5.0` (design Rollout R1). Do not start before `git ls-remote https://github.com/szymonrychu/any-mcp refs/tags/v0.5.0` prints a sha.

Scope (agents-orchestrator):
- `src/agents_orchestrator/settings.py`: `any_mcp_ref = "v0.5.0"`; new `any_mcp_plugins_repo`, `any_mcp_plugins_ref` with the `_TAG_RE` validator of `any_mcp_ref`.
- `pyproject.toml`: `any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.5.0`; `uv.lock` refreshed.
- `README.md`: Configuration rows `ORCH_ANY_MCP_PLUGINS_REPO` and `ORCH_ANY_MCP_PLUGINS_REF`; the `ORCH_ANY_MCP_REF` default and the `## Images` any-mcp sentence name `v0.5.0`, and that sentence names the plugins dev dependency pin too.
- `tests/test_settings.py::test_defaults` asserts any-mcp `v0.4.0`: no longer accurate because the pin moves to v0.5.0 (design D7); it asserts `v0.5.0` and the two plugins defaults. New `test_any_mcp_plugins_ref_must_be_release_tag`.
- `tests/test_images.py`: new `test_plugins_dev_pin_matches_settings_ref`.
- `tests/golden/session_single.yaml`, `tests/golden/session_two_peers.yaml`: regenerated with the golden helper of `tests/test_render.py` (`UPDATE_GOLDEN=1`; the onStart script names the ref).

## Acceptance conditions

- ac1: the pyproject any-mcp pin, uv.lock and the settings default agree on v0.5.0 [evidence: test:tests/test_images.py::test_pyproject_any_mcp_pin_matches_settings_ref]
- ac2: the plugins dev dependency tag and uv.lock agree with the any_mcp_plugins_ref default [evidence: test:tests/test_images.py::test_plugins_dev_pin_matches_settings_ref]
- ac3: the defaults are any_mcp_ref v0.5.0, any_mcp_plugins_repo https://github.com/szymonrychu/any-mcp-tatara-plugins and any_mcp_plugins_ref v0.1.0 [evidence: test:tests/test_settings.py::test_defaults]
- ac4: ORCH_ANY_MCP_PLUGINS_REF accepts only a vX.Y.Z tag [evidence: test:tests/test_settings.py::test_any_mcp_plugins_ref_must_be_release_tag]
- ac5: README documents both new settings and the v0.5.0 default [evidence: command:grep -qF '`ORCH_ANY_MCP_REF` | `v0.5.0`' README.md && grep -qF '`ORCH_ANY_MCP_PLUGINS_REF` | `v0.1.0`' README.md && grep -qF '`ORCH_ANY_MCP_PLUGINS_REPO`' README.md]
- ac6: the settings, images, render, onStart, README and spec validation tests pass with the regenerated goldens [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_settings.py tests/test_images.py tests/test_render.py tests/test_on_start.py tests/test_readme_api.py tests/test_sessions_repo.py]
- ac7: lint passes [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/settings.py`
- `pyproject.toml`
- `uv.lock`
- `tests/test_settings.py`
- `tests/test_images.py`
- `README.md`
- `tests/golden/session_single.yaml`
- `tests/golden/session_two_peers.yaml`

## Interfaces

- `settings.py:Settings.any_mcp_ref = "v0.5.0"`, `any_mcp_plugins_repo: str = "https://github.com/szymonrychu/any-mcp-tatara-plugins"`, `any_mcp_plugins_ref: str = "v0.1.0"` (env `ORCH_ANY_MCP_PLUGINS_REPO`, `ORCH_ANY_MCP_PLUGINS_REF`), the ref validated by `_TAG_RE`.
- Consumed by task orch-render-plugin-sources (`k8s/on_start.py`).

## Expected outcome

The orchestrator runs on any-mcp v0.5.0 (its spec validation understands `source` entries) and knows the plugins repo and tag to render.

## Steps

- Red: update `test_defaults`, add `test_any_mcp_plugins_ref_must_be_release_tag` and `test_plugins_dev_pin_matches_settings_ref`; run `unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_settings.py tests/test_images.py`: fails.
- Green: settings, pyproject, `uv lock`, README; regenerate goldens with `UPDATE_GOLDEN=1`; run the task's verify: passes.

## Notes

- `tests/test_settings.py:test_env_names_documented_in_readme` requires every setting documented as `ORCH_<NAME>` in README `## Configuration`.
- The golden diff is the any-mcp ref only; on_start.py does not change here.
- Orchestrator tests need Docker (testcontainers) and `VIRTUAL_ENV` unset; recreate a stale `.venv` with `uv sync`.
- (orchestrator note 2026-10-27) orch-plugins-dev-dependency added `[tool.uv] override-dependencies = ["any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.4.0"]` to pyproject.toml because the plugins package's workspace pins any-mcp v0.5.0 and uv refused two URLs. This task's pin move to v0.5.0 must bump that override to v0.5.0 or remove it if uv no longer needs it, and uv.lock must resolve one any-mcp.

- 2026-10-27 done
