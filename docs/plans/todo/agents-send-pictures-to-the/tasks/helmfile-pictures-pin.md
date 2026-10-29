---
title: helmfile pictures pin
status: todo
repo: agents-helmfile
value: "the live namespace is pinned to the picture-capable connector, orchestrator, web and plugins release"
files: [helmfile.yaml.gotmpl, values/agents-matrix-connector/common.yaml, values/agents-orchestrator/common.yaml, values/agents-web/common.yaml, tests/test_matrix_connector_release.py, tests/test_orchestrator_release.py, tests/test_web_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_matrix_connector_release.py tests/test_orchestrator_release.py tests/test_web_release.py && mise run lint"
depends_on: [plugins-release-images, mxc-e2e-image-send, mxc-room-messages-msgtype, orch-plugins-pin-and-tool, web-chat-image-tool, web-room-messages-picture]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 8
expected_tokens: 1003544
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile pictures pin

## Requirement

README Goal G5, verbatim: "released and deployed in order (plugins, connector, orchestrator, web, helmfile) and proven by a live smoke that posts one real picture with a caption to the owner's Messenger DM."

Design D9, verbatim: "Release and deploy order: plugins, connector, orchestrator, web, helmfile (image tags, chart versions, `ORCH_ANY_MCP_PLUGINS_REF: <TAG>`, connector image settings)."

User decision (binding), verbatim: "Release numbers are placeholders resolved at build time, exactly as /workdir/workdir/docs/plans/in-progress/hive-decoupling does (read its design.md 'Build-time settlements' and tasks orch-activity-route, plugins-release-0-4-0, orch-plugins-pin-0-4-0, helmfile-deploy-pin for the pattern): <MIGRATION> for the connector migration (0003 is claimed by immediate-message-delivery-w), <TAG>/<VERSION> for the plugins release (v0.3.0-v0.5.0 claimed). The first task needing each reads it from main and amends dependents."

`<TAG>` is filled by `ticket.py amend` from plugins-release-images; each `<sha7>` below is filled by `ticket.py amend` when that repo's PR merges to `main` and CI publishes the image and chart.

Scope (agents-helmfile):
- `helmfile.yaml.gotmpl` and `values/agents-matrix-connector/common.yaml`: connector chart `0.1.0-main.<connector sha7>` and `image.tag` `<connector sha7>`, the connector `main` commit carrying every connector task of this epic.
- `helmfile.yaml.gotmpl` and `values/agents-orchestrator/common.yaml`: orchestrator chart and `image.tag` `<orchestrator sha7>`; `env.ORCH_ANY_MCP_PLUGINS_REF: <TAG>`.
- `helmfile.yaml.gotmpl` and `values/agents-web/common.yaml`: web chart and `image.tag` `<web sha7>`.
- "connector image settings" is read as the connector image pins above: the picture limits keep their connector defaults (`MATRIX_IMAGE_MAX_BYTES` 8000000, `MATRIX_AGENT_IMAGE_RATE_PER_MINUTE` 5) and no connector value is added (my call: the connector chart has no generic env map and the defaults are the decided limits).
- `tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions` is no longer accurate (named): it asserts the previous plugins ref; it asserts `<TAG>`.
- Before changing a value, confirm that image tag and chart version exist in Harbor (retro: Harbor prunes tags). No apply here (pictures-live-smoke).

## Acceptance conditions

- ac1: the connector chart version and image tag agree on the connector merge sha7 and the release still needs its database [evidence: test:tests/test_matrix_connector_release.py::test_matrix_connector_pin_and_needs]
- ac2: the orchestrator chart version and image tag agree on the orchestrator merge sha7 [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- ac3: the web chart version and image tag agree on the web merge sha7 [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- ac4: new sessions get the <TAG> plugins ref (updated, named) [evidence: test:tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions]
- ac5: each pinned sha7 is a main commit of its repo containing every task of this epic in that repo, with green CI [evidence: judgement:reviewer checks git merge-base --is-ancestor of each task's verified_head against the pinned sha and the CI run of that sha]
- ac6: every pin's main CI is green [evidence: command:mise run check-pins]
- ac7: (orchestrator session) Harbor holds each pinned image tag and chart version [evidence: judgement:orchestrator records the registry check of each tag and chart in the task Notes]
- ac8: the release tests and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_matrix_connector_release.py tests/test_orchestrator_release.py tests/test_web_release.py && mise run lint]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-matrix-connector/common.yaml`
- `values/agents-orchestrator/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_matrix_connector_release.py`
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
