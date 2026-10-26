---
title: helmfile deploy pin
status: in-progress
repo: agents-helmfile
value: the live namespace is pinned to the auto-handover release
files: [helmfile.yaml.gotmpl, values/agents-orchestrator/common.yaml, values/agents-web/common.yaml, tests/test_orchestrator_release.py, tests/test_web_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-release-0-3-0, orch-wrapper-pin-0-3-0, kind-e2e-auto-handover, web-leader-reason, web-scale-hint, smoke-scale-below-leader]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 6
expected_tokens: 546295
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile deploy pin

## Requirement

Goal G6, verbatim: "released and deployed: wrapper release, orchestrator pins, agents-helmfile bump, apply and a smoke step covering a scale-down below the leader." Design D12: agents-helmfile pins the orchestrator chart and image, the agent image `claude-code-wrapper:0.3.0` and the agents-web chart and image. Precedent: done epic hive-mode-leadership-handove task helmfile-deploy-pin.

Scope:
- `helmfile.yaml.gotmpl`: agents-orchestrator chart `0.1.0-main.<orchestrator merge sha7>`; agents-web chart `0.1.0-main.<agents-web merge sha7>`.
- `values/agents-orchestrator/common.yaml`: `image.tag` `<orchestrator sha7>`; `agentImage` and `env.ORCH_AGENT_IMAGES` `harbor.szymonrichert.pl/containers/claude-code-wrapper:0.3.0` (a release tag: Harbor prunes sha7 tags). `ORCH_ANY_MCP_REF` stays `v0.3.0`.
- `values/agents-web/common.yaml`: `image.tag` `<agents-web sha7>`.
- Tests: `tests/test_orchestrator_release.py` (chart version and image tag agree; agent image pins agree on 0.3.0) and `tests/test_web_release.py` (chart version and image tag agree).

The shas are filled in by `ticket.py amend` when the orchestrator and agents-web PRs merge. Chart-pull tests blocked by a container network policy may be deselected in a local run (precedent ruling in done epic web-ui-cluster-tabs-with-fil task deploy-pin); they run unblocked before the apply.

Notes: `tests/test_orchestrator_release.py` also holds `test_values_dir_moved`, which once blocked an apply (retro agents-schedule-deploy); it must pass here so the apply is not stopped by a stale test.

## Acceptance conditions

- AC1: the orchestrator chart version and image tag agree on the orchestrator merge sha [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: agentImage and ORCH_AGENT_IMAGES agree on claude-code-wrapper:0.3.0 [evidence: test:tests/test_orchestrator_release.py::test_agent_image_pins_agree]
- AC3: the agents-web chart version and image tag agree on the agents-web merge sha [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- AC4: the agent image is the 0.3.0 release [evidence: command:grep -q "claude-code-wrapper:0.3.0" values/agents-orchestrator/common.yaml]
- AC5: the release test files pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py]
- AC6: lint passes [evidence: command:mise run lint]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_orchestrator_release.py`
- `tests/test_web_release.py`

## Interfaces

See the Requirement and the acceptance conditions above.

## Expected outcome

See the Requirement and the acceptance conditions above.

## Steps

- Red: update the pins expected by `tests/test_orchestrator_release.py` and `tests/test_web_release.py` (orchestrator and agents-web shas from the amendment, wrapper 0.3.0); run the task's verify command: fails.
- Green: change `helmfile.yaml.gotmpl` and the two values files; run the task's verify command: passes.

## Notes

See the Requirement and the acceptance conditions above.
