---
title: helmfile deploy pin
status: in-progress
repo: agents-helmfile
value: the deployment runs generic any-mcp with the orchestrator plugin from the plugins repo
files: [helmfile.yaml.gotmpl, values/agents-orchestrator/common.yaml, values/agents-web/common.yaml, tests/test_orchestrator_release.py, tests/test_web_release.py, tests/test_smoke_script.py, README.md]
verify: "uv run --frozen pytest -q tests/test_orchestrator_release.py tests/test_web_release.py tests/test_smoke_script.py && mise run lint"
depends_on: [orch-render-plugin-sources, web-preset-plugin-sources]
model: opus
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile deploy pin

## Requirement

Goal G6 (epic README), verbatim: "Deployed through agents-helmfile; agent sessions still get the orchestrator tools." Orchestrator design call, verbatim: "agents-helmfile: pin new orchestrator chart/image, ORCH_ANY_MCP_REF v0.5.0 and ORCH_ANY_MCP_PLUGINS_REF tag". Design D11, verbatim: "agents-helmfile pins the new orchestrator and web charts and images, `ORCH_ANY_MCP_REF: v0.5.0` and `ORCH_ANY_MCP_PLUGINS_REF: v0.1.0`."

Needs merged upstreams: the agents-orchestrator PR of this epic merged with its image `b3a2975` and chart `0.1.0-main.b3a2975` published by main CI; the agents-web PR merged with its image and chart `0.1.0-main.4701820` published (design Rollout R3). The shas are filled in by `ticket.py amend` before dispatch.

Scope (agents-helmfile, base: the merged state of epic cross-session-messaging-and):
- `helmfile.yaml.gotmpl`: agents-orchestrator chart `0.1.0-main.b3a2975`; agents-web chart `0.1.0-main.4701820`.
- `values/agents-orchestrator/common.yaml`: `image.tag: b3a2975` (quoted if all digits); `env.ORCH_ANY_MCP_REF: v0.5.0`; new `env.ORCH_ANY_MCP_PLUGINS_REPO: https://github.com/szymonrychu/any-mcp-tatara-plugins` and `env.ORCH_ANY_MCP_PLUGINS_REF: v0.1.0` with a comment: the reserved orchestrator plugin is installed from that repo at that tag.
- `values/agents-web/common.yaml`: `image.tag: "4701820"`.
- Tests no longer accurate because the pins move (design D11): `tests/test_orchestrator_release.py` (`PIN`; `test_any_mcp_configured_for_new_sessions` asserts v0.5.0 and the two plugins values), `tests/test_web_release.py` (the agents-web sha), `tests/test_smoke_script.py::test_any_mcp_version_is_the_orchestrator_values_ref` (`0.5.0`).
- `README.md`: the any-mcp line names the plugins repo source of the orchestrator tools.
- Never the word "cluster" outside the allowed phrases of `tests/test_nomenclature.py`.

## Acceptance conditions

- ac1: the orchestrator chart version and image tag agree on the orchestrator merge sha [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- ac2: new sessions install any-mcp v0.5.0 and the orchestrator plugin from https://github.com/szymonrychu/any-mcp-tatara-plugins at v0.1.0 [evidence: test:tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions]
- ac3: the agents-web chart version and image tag agree on the agents-web merge sha [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- ac4: the smoke script expects any-mcp 0.5.0 from the orchestrator values [evidence: test:tests/test_smoke_script.py::test_any_mcp_version_is_the_orchestrator_values_ref]
- ac5: the whole helmfile test suite, including the stale-path and nomenclature tests, passes [evidence: command:mise run test]
- ac6: lint (ruff, shellcheck, gitleaks) passes [evidence: command:mise run lint]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_orchestrator_release.py`
- `tests/test_web_release.py`
- `tests/test_smoke_script.py`
- `README.md`

## Interfaces

- `values/agents-orchestrator/common.yaml` `env`: `ORCH_ANY_MCP_REPO`, `ORCH_ANY_MCP_REF: v0.5.0`, `ORCH_ANY_MCP_PLUGINS_REPO: https://github.com/szymonrychu/any-mcp-tatara-plugins`, `ORCH_ANY_MCP_PLUGINS_REF: v0.1.0` (read by `scripts/smoke.sh` in task helmfile-smoke-plugin-tools).
- Chart and image pins: `0.1.0-main.<sha7>` and `<sha7>` for agents-orchestrator and agents-web.

## Expected outcome

`mise run diff` shows only the new orchestrator and web releases with the new settings; after the apply new sessions install any-mcp v0.5.0 and the orchestrator plugin from the plugins repo.

## Steps

- Red: update the pinned values in the three test files; run `uv run --frozen pytest -q tests/test_orchestrator_release.py tests/test_web_release.py tests/test_smoke_script.py`: fails.
- Green: helmfile.yaml.gotmpl and the two values files, README; run the task's verify, then `mise run test`: pass.

## Notes

- The shas come from Rollout R3 through `ticket.py amend` before dispatch (precedent: epic leader-auto-handover task helmfile-deploy-pin); an all-digit sha7 is quoted in YAML.
- The apply, diff and smoke are orchestrator steps (Rollout R4, R5), never this task's.
- Never the word "cluster" outside the allowed phrases of `tests/test_nomenclature.py`.
