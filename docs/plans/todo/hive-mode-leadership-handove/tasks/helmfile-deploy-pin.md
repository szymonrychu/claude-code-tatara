---
title: helmfile deploy pin
status: todo
repo: agents-helmfile
value: the live namespace is pinned to the hive release
files: [helmfile.yaml.gotmpl, values/agent-orchestrator/common.yaml, scripts/smoke.sh, tests/test_orchestrator_release.py, tests/test_smoke_script.py]
verify: "mise x -- uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_smoke_script.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [kind-e2e-hive, ui-leader-badge, spec-form-cap-static, bench-hive-arm, hive-docs-memory]
owns: []
uses: [orch-agents-service]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# helmfile deploy pin

## Requirement

Pin agents-helmfile to this epic's merged builds (precedent: done epic web-ui-cluster-tabs-with-fil task deploy-pin):

- `helmfile.yaml.gotmpl`: agent-orchestrator chart `0.1.0-main.<orchestrator merge sha7>`.
- `values/agent-orchestrator/common.yaml`: `image.tag` `<orchestrator sha7>`; `agentImage` and `env.ORCH_AGENT_IMAGES` `harbor.szymonrichert.pl/containers/claude-code-wrapper:<wrapper 0.2.0 merge sha7>`; `ORCH_ANY_MCP_REF` left to the chart default `v0.2.0` unless set today.
- `scripts/smoke.sh`: expects any-mcp 0.2.0 and checks that the `<release>-agents` Service exists on port 8001 and is not an ingress backend.
- Tests: `tests/test_orchestrator_release.py` (chart version and image tag agree; agent image pins agree) and `tests/test_smoke_script.py` (version 0.2.0, agents Service check).

The shas are filled in by amendment when the orchestrator and wrapper PRs merge. Chart-pull tests blocked by a container network policy may be deselected in the verify (precedent ruling).

## Acceptance conditions

- AC1: chart version and image tag agree on the orchestrator sha [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: agentImage and ORCH_AGENT_IMAGES agree on the wrapper sha [evidence: test:tests/test_orchestrator_release.py::test_agent_image_pins_agree]
- AC3: smoke expects any-mcp 0.2.0 and fails without the agents Service [evidence: test:tests/test_smoke_script.py::test_wrong_any_mcp_version_fails]
- AC4: the smoke agents Service check is covered [evidence: test:tests/test_smoke_script.py::test_missing_agents_service_fails]
- AC5: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/common.yaml`
- `scripts/smoke.sh`
- `tests/test_orchestrator_release.py`
- `tests/test_smoke_script.py`

## Interfaces

- Consumes the published chart `0.1.0-main.<sha7>`, images `agent-orchestrator:<sha7>` and `claude-code-wrapper:<sha7>`, and `orch-agents-service`.

## Expected outcome

`helmfile diff` shows only the pins, the agents Service and the new settings.

## Steps

- Red: update the tests for the new pins and the agents Service smoke check; run the verify command: fails.
- Green: change the pins and the smoke script; run the verify command: passes.

## Notes

- Precedent: `docs/plans/done/web-ui-cluster-tabs-with-fil/tasks/deploy-pin.md`, including the ruling on chart-pull tests blocked by the network policy.
