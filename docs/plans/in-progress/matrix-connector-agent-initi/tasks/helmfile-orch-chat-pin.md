---
title: helmfile orch chat pin
status: todo
repo: agents-helmfile
value: the merged orchestrator chat relay and plugins v0.2.0 run live before the connector lands
files: [values/agents-orchestrator/common.yaml, helmfile.yaml.gotmpl, tests/test_orchestrator_release.py, MEMORY.md]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_smoke_script.py && mise run lint"
depends_on: [orch-chat-tools-allow]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 556633
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile orch chat pin

## Requirement

User rule (2026-10-28, mx-34 msg 190), verbatim in memory deploy-small-often: deploy small and often; each reviewed, independently runnable task or small group merges to its component main and deploys at once (check-pins, apply, smoke); backend before web.

The orchestrator half of this epic is merged: agents-orchestrator PR #30, merge commit 37edd586a8ba754769419bec9b01e573c1704709 (orch-chat-relay, orch-chart-chat, orch-plugins-pin-0-3-0, orch-chat-contract, orch-chat-tools-allow). Without `chat.url` and the chat token the relay routes answer 503 `chat_unconfigured` (design B7), so it is safe to deploy before the connector.

Scope (agents-helmfile), no apply here (the orchestrator session applies, never a subagent):
- `values/agents-orchestrator/common.yaml`: `image.tag` 37edd58 and `env.ORCH_ANY_MCP_PLUGINS_REF: v0.2.0` (design D13: the orchestrator pins plugins v0.2.0; the ref rolls agent pods, which the deploy-safe OnDelete replacer does idle-only).
- `helmfile.yaml.gotmpl`: agents-orchestrator chart version `0.1.0-main.37edd58` (CI-published from main).
- `tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions` is no longer accurate (named): it pins `v0.1.0`; it asserts `v0.2.0`.
- No `chat.url`, no chat secret: those stay with helmfile-chat-secrets and helmfile-chat-values.
- MEMORY.md: a dated entry for the early orchestrator deploy and why.

## Acceptance conditions

- ac1: the orchestrator values pin image 37edd58 and the chart version 0.1.0-main.37edd58 [evidence: command:grep -q "tag: 37edd58" values/agents-orchestrator/common.yaml && grep -q "0.1.0-main.37edd58" helmfile.yaml.gotmpl]
- ac2: new sessions install the orchestrator plugin at v0.2.0 (updated) [evidence: test:tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions]
- ac3: every pin has a green published build [evidence: command:mise run check-pins]
- ac4: MEMORY.md records the early orchestrator deploy [evidence: command:grep -q "37edd58" MEMORY.md]
- ac5: the targeted tests and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_smoke_script.py && mise run lint]

## Files

- `values/agents-orchestrator/common.yaml`
- `helmfile.yaml.gotmpl`
- `tests/test_orchestrator_release.py`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
