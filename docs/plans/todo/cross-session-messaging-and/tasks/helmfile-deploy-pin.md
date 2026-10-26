---
title: helmfile deploy pin
status: todo
repo: agents-helmfile
value: the live namespace is pinned to the versions with both options and Kubernetes access enabled
files: [helmfile.yaml.gotmpl, values/agents-orchestrator/common.yaml, values/agents-web/common.yaml, tests/test_orchestrator_release.py, tests/test_web_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py && mise run lint"
depends_on: [smoke-session-options, web-preset-session-options, web-chat-session-messages]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 6
expected_tokens: 553016
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile deploy pin

## Requirement

Goal G5 (epic README), verbatim: "Deployed: new orchestrator, any-mcp and agents-web versions applied through agents-helmfile with the Kubernetes access chart value on; the "facebook chat" preset has messaging on (its running session discarded) and "claude-code-tatara" has Kubernetes access on." Design D12, D15. This task is the pin and values change; the apply, smoke and preset updates are orchestrator steps (design Rollout R3 to R7).

Needs merged upstreams: the agents-orchestrator PR of this epic merged with its image `<orchestrator sha7>` and chart `0.1.0-main.<orchestrator sha7>` published by main CI; the agents-web PR merged with its image and chart `0.1.0-main.<agents-web sha7>` published; any-mcp tag `v0.4.0` released. The shas are filled in by `ticket.py amend` before dispatch (precedent: done epic leader-auto-handover task helmfile-deploy-pin).

Scope (agents-helmfile):
- `helmfile.yaml.gotmpl`: agents-orchestrator chart `0.1.0-main.<orchestrator sha7>`; agents-web chart `0.1.0-main.<agents-web sha7>`.
- `values/agents-orchestrator/common.yaml`: `image.tag: <orchestrator sha7>` (quoted if all digits); `env.ORCH_ANY_MCP_REF: v0.4.0`; `kubeAccess: {enabled: true}` with a comment: sessions with `kube_access` get full Kubernetes access through the chart's kube-access ServiceAccount.
- `values/agents-web/common.yaml`: `image.tag: "<agents-web sha7>"`.
- `tests/test_orchestrator_release.py`: `PIN` becomes the orchestrator sha7; `test_any_mcp_configured_for_new_sessions` asserts `v0.3.0` and is no longer accurate because the pinned any-mcp release moves to v0.4.0 (design D12), so it asserts `v0.4.0`; new `test_kube_access_enabled`.
- `tests/test_web_release.py`: the hardcoded agents-web sha becomes the new one.
- Never the word "cluster" outside the allowed phrases of `tests/test_nomenclature.py`.

## Acceptance conditions

- ac1: the orchestrator chart version and image tag agree on the orchestrator merge sha [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- ac2: new sessions install any-mcp v0.4.0 [evidence: test:tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions]
- ac3: the orchestrator release values set kubeAccess.enabled true [evidence: test:tests/test_orchestrator_release.py::test_kube_access_enabled]
- ac4: the agents-web chart version and image tag agree on the agents-web merge sha [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- ac5: the whole helmfile test suite, including the stale-path and nomenclature tests, passes [evidence: command:mise run test]
- ac6: lint (ruff, shellcheck, gitleaks) passes [evidence: command:mise run lint]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_orchestrator_release.py`
- `tests/test_web_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
