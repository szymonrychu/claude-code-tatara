---
title: helmfile chat values
status: done
repo: agents-helmfile
value: agents-helmfile pins the connector and orchestrator builds with the chat path and the v0.2.0 plugins
files: [values/agents-matrix-connector/common.yaml, values/agents-orchestrator/common.yaml, helmfile.yaml.gotmpl, tests/test_matrix_connector_release.py, tests/test_orchestrator_release.py]
verify: "uv run pytest tests/test_matrix_connector_release.py tests/test_orchestrator_release.py && mise run lint"
depends_on: [helmfile-chat-secrets, mxc-e2e-agent-sends, mxc-chart-agent-port, orch-chart-chat, orch-chat-tools-allow, plugins-release-0-3-0]
model: sonnet
review: ""
verified_head: ab481511369e1480041c6ed329cbad1f965e02fd
points: 3
expected_minutes: 6
expected_tokens: 941421
points_actual: 2
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile chat values

## Requirement

README Goal, verbatim: "Docs, tests (unit, contract, e2e) and a live smoke in the owner DM covering send without inbound, quoted reply and reaction."

Design D14, verbatim (values): "Values: connector image tag and chart version, agent port; orchestrator image tag and chart version, `chat.url: http://agents-matrix-connector-api-agents:8001`, `ORCH_ANY_MCP_PLUGINS_REF: v0.2.0`; agents-web tag with the toggle."

Design D18, verbatim: "(3) Apply the connector first (migration 0002 runs in its init container; the agent listener comes up), then the orchestrator with its chat secret and the v0.2.0 plugins ref (until then the routes answer 503 `chat_unconfigured`; the ref rolls agent pods), then agents-web. (4) The orchestrator session runs every apply with `--selector` in that order; no AC runs an apply. Gate question Q6 settles how this deploy relates to the one deploy epic approved for the four earlier epics."

Open question Q6 (pending gate), verbatim: "This epic's agents-helmfile values and live smoke run only after the one deploy approved for the four earlier epics (file-download, markdown, file-editor, slash-commands) has applied, so this epic's applies move only the connector, the orchestrator (chat config, plugins v0.2.0) and agents-web; if that deploy epic does not exist when this epic reaches helmfile-chat-values, the orchestrator creates and runs it first?" recommended "yes".

Retro tech debt (file-download-in-file-browse), verbatim: "Deploy coupling: orchestrator `FileEntry.target_type` is required, so the orchestrator image must deploy with wrapper >= 4581f3b; the later deploy epic must pin them together."

Scope (agents-helmfile): `values/agents-matrix-connector/common.yaml` (image tag = the connector `main` sha7 that carries every connector task of this epic, CI-published; `agentApi.port` 8001 if not the chart default), `helmfile.yaml.gotmpl` (connector and orchestrator chart versions `0.1.0-main.<sha7>`), `values/agents-orchestrator/common.yaml` (image tag = the orchestrator `main` sha7 that carries every orchestrator task of this epic; `chat.url`; `ORCH_ANY_MCP_PLUGINS_REF: v0.2.0`; the agent image stays what the earlier deploy pinned). Named tests no longer accurate: `tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions` pins the plugins ref of the earlier deploy; it asserts `v0.2.0`. No apply here: the orchestrator session applies in chat-live-smoke.

## Acceptance conditions

- ac1: the connector image tag and chart version name the same connector main sha7, and the release still needs its database [evidence: test:tests/test_matrix_connector_release.py::test_matrix_connector_pin_and_needs]
- ac2: the orchestrator image tag and chart version name the same orchestrator main sha7 [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- ac3: the orchestrator values set chat.url to http://agents-matrix-connector-api-agents:8001 and no plaintext chat token [evidence: test:tests/test_orchestrator_release.py::test_chat_upstream_wired]
- ac4: new sessions install the orchestrator plugin at v0.2.0 (updated) [evidence: test:tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions]
- ac5: the pinned connector sha7 contains mxc-e2e-agent-sends and the pinned orchestrator sha7 contains orch-chat-tools-allow and orch-chart-chat, both on their repos' main with green CI [evidence: judgement:reviewer checks git merge-base --is-ancestor of each task's verified_head against the pinned sha and the CI run of that sha]
- ac6: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_matrix_connector_release.py tests/test_orchestrator_release.py && mise run lint]

## Files

- `values/agents-matrix-connector/common.yaml`
- `values/agents-orchestrator/common.yaml`
- `helmfile.yaml.gotmpl`
- `tests/test_matrix_connector_release.py`
- `tests/test_orchestrator_release.py`

## Interfaces

- `values/agents-orchestrator/common.yaml`: `chat.url`, `env.ORCH_ANY_MCP_PLUGINS_REF: v0.2.0`, `image.tag`.
- `values/agents-matrix-connector/common.yaml`: `image.tag`.
- `helmfile.yaml.gotmpl`: chart `version` of both releases.

## Expected outcome

agents-helmfile describes the deployed state this epic needs; one apply per release (connector, then orchestrator) brings it live.

## Steps

- Confirm Q6's precondition: the earlier four epics' deploy is applied (the orchestrator image and agent image pins already moved past b3a2975 and claude-code-wrapper 0.3.0); stop and report if not.
- Red: add `test_chat_upstream_wired`, update `test_any_mcp_configured_for_new_sessions` and the pin expectations; run `uv run pytest tests/test_matrix_connector_release.py tests/test_orchestrator_release.py`: they fail.
- Green: values and chart versions; run the task's verify: passes. Quote the summary line with counts.

## Notes

- Tests that run `helmfile build` or `helm pull oci://harbor...` fail without network in this pod (discovery sec 5); quote them as environmental and name which ones.
- The image tags must exist in Harbor (CI images job of each merge); chat-live-smoke checks them before applying.
- agents-helmfile has no CI workflow: the reviewer's local verify is the evidence.

- 2026-10-28 amended: plugins release number swap (design B2): this epic releases v0.2.0 on top of v0.1.0; slash-commands releases v0.3.0

- 2026-10-28 done

- 2026-10-28 actuals: no agent records
