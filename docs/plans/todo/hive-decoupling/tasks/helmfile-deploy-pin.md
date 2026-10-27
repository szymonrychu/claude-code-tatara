---
title: helmfile deploy pin
status: todo
repo: agents-helmfile
value: the live namespace is pinned to the hive-decoupling orchestrator and plugins release
files: [helmfile.yaml.gotmpl, values/agents-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py && mise run lint"
depends_on: [orch-e2e-hive-activity, plugins-release-0-4-0, helmfile-smoke-activity]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 544297
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile deploy pin

## Requirement

README Goal G5, verbatim: "Released and deployed: any-mcp-tatara-plugins next minor tag, orchestrator pins, agents-helmfile bump, apply, a smoke covering the activity route and tool, and a live handoff proof."

Design D9, verbatim: "agents-helmfile: orchestrator chart version and image tag (CI-published merge sha7), `ORCH_ANY_MCP_PLUGINS_REF` to the new tag; agent image unchanged (whatever release tag the epics before left)."

Scope (agents-helmfile):
- `helmfile.yaml.gotmpl`: agents-orchestrator chart `0.1.0-main.<orchestrator merge sha7>`, the agents-orchestrator `main` commit that carries every orchestrator task of this epic (CI-published).
- `values/agents-orchestrator/common.yaml`: `image.tag` `<the same sha7>`; `env.ORCH_ANY_MCP_PLUGINS_REF: v0.4.0`. `agentImage` and `ORCH_AGENT_IMAGES` unchanged.
- `tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions` is no longer accurate (named): it asserts the previous plugins ref; it asserts `v0.4.0`.
- The sha7 is filled in by `ticket.py amend` when the orchestrator PR merges; confirm the image tag and chart version exist in Harbor before changing the values.
- No apply here (helmfile-apply-live-proof).

## Acceptance conditions

- ac1: the orchestrator chart version and image tag agree on the orchestrator merge sha7 [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- ac2: new sessions get the v0.4.0 plugins ref (updated, named) [evidence: test:tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions]
- ac3: the agent image pins still agree [evidence: test:tests/test_orchestrator_release.py::test_agent_image_pins_agree]
- ac4: the pinned sha7 is an agents-orchestrator main commit that contains every orchestrator task of this epic, with green CI [evidence: judgement:reviewer checks git merge-base --is-ancestor of each orchestrator task's verified_head against the pinned sha and the CI run of that sha]
- ac5: the release tests and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py && mise run lint]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
