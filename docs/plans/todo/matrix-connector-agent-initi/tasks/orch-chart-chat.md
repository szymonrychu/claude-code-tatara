---
title: orch chart chat
status: todo
repo: agents-orchestrator
value: the orchestrator chart can turn the chat relay on with its token kept in a Secret
files: [chart/agents-orchestrator/values.yaml, chart/agents-orchestrator/templates/secret.yaml, chart/agents-orchestrator/templates/_config.tpl, chart/agents-orchestrator/templates/configmap.yaml, chart/agents-orchestrator/templates/deployment.yaml, README.md, tests/test_chart_config.py]
verify: "uv run --frozen pytest tests/test_chart_config.py tests/test_chart_deployments.py && mise run lint"
depends_on: [orch-chat-relay]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 941421
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch chart chat

## Requirement

README Goal, verbatim: "Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator."

Design D12, verbatim (chart): "The chart takes `chat.url`, `chat.token` or `chat.existingSecret`/`chat.existingSecretKey`, renders `ORCH_CHAT_URL` in the settings ConfigMap and `ORCH_CHAT_TOKEN` from a Secret, on the api container only (my call)."

Design D14, verbatim (value shape): "`values/agents-orchestrator/chat-token.secrets.yaml` (`{chat: {token}}`)".

Scope (agents-orchestrator chart): `values.yaml` (`chat: {url: "", token: "", existingSecret: "", existingSecretKey: chat-token}`), `templates/secret.yaml` (chart Secret `<fullname>-chat` when `chat.token` is set and no `existingSecret`), `templates/_config.tpl` (`ORCH_CHAT_TOKEN` secretKeyRef helper, the Secret name helper; a URL without a token source, or a token without a URL, fails the render), `templates/configmap.yaml` (`ORCH_CHAT_URL`), `templates/deployment.yaml` (the env on the api container only), README `### Secrets` names the chat values.

## Acceptance conditions

- ac1: chat.url renders ORCH_CHAT_URL in the settings ConfigMap [evidence: test:tests/test_chart_config.py::test_chat_url_in_configmap]
- ac2: chat.token renders a chart Secret and ORCH_CHAT_TOKEN as a secretKeyRef on the api container only, chat.existingSecret wins over it, and the token never appears in the ConfigMap [evidence: test:tests/test_chart_config.py::test_chat_token_secret_on_api_only]
- ac3: a chat URL without a token source, or a token source without a URL, fails the render with a message naming both values [evidence: test:tests/test_chart_config.py::test_chat_url_and_token_together]
- ac4: without chat values neither ORCH_CHAT_URL nor ORCH_CHAT_TOKEN is rendered [evidence: test:tests/test_chart_config.py::test_chat_absent_by_default]
- ac5: no secret value reaches the ConfigMap [evidence: test:tests/test_chart_config.py::test_no_secret_values_in_configmap]
- ac6: README Secrets documents chat.url, chat.token and chat.existingSecret [evidence: command:grep -q 'chat.existingSecret' README.md && grep -q 'ORCH_CHAT_TOKEN' README.md]
- ac7: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_chart_config.py tests/test_chart_deployments.py && mise run lint]

## Files

- `chart/agents-orchestrator/values.yaml`
- `chart/agents-orchestrator/templates/secret.yaml`
- `chart/agents-orchestrator/templates/_config.tpl`
- `chart/agents-orchestrator/templates/configmap.yaml`
- `chart/agents-orchestrator/templates/deployment.yaml`
- `README.md`
- `tests/test_chart_config.py`

## Interfaces

- `values.yaml`: `chat.url`, `chat.token`, `chat.existingSecret`, `chat.existingSecretKey` (default `chat-token`).
- Secret `<fullname>-chat` key `chat-token` (chart-made) or the named existing Secret.

## Expected outcome

Deploying the orchestrator chart with a chat URL and token turns the chat routes on, with the token only in a Secret mounted on the api container.

## Steps

- Red: add the four chart tests; run `uv run --frozen pytest tests/test_chart_config.py`: they fail.
- Green: values and templates, README; run the task's verify: passes. Quote the summary line with counts.

## Notes

- Mirror the `masterKey` and `serviceApi` patterns already in `templates/secret.yaml` and `_config.tpl`.
- Chart tests render with `helm`; if this pod lacks a helm version (as in the connector), the CI chart job is the gate; quote its run.
- `tests/test_chart_deployments.py` guards the other containers; it must still pass with the env only on the api container.
