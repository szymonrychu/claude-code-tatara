---
title: orch chart schedule relay
status: todo
repo: agents-orchestrator
value: the orchestrator chart turns the schedule relay on with its token kept in a Secret
files: [chart/agents-orchestrator/values.yaml, chart/agents-orchestrator/templates/secret.yaml, chart/agents-orchestrator/templates/_config.tpl, chart/agents-orchestrator/templates/configmap.yaml, chart/agents-orchestrator/templates/deployment.yaml, README.md, tests/test_chart_config.py]
verify: "uv run --frozen pytest tests/test_chart_config.py tests/test_chart_deployments.py && mise run lint"
depends_on: [orch-schedule-relay-contract]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 936557
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch chart schedule relay

## Requirement

README Goal G5, verbatim: "Schedule calls go through the orchestrator, which relays them to a token-protected listener on agents-schedule that records each schedule's owner; the agent token never leaves the orchestrator."

Design D16, verbatim: "The orchestrator chart takes `schedule.url`, `schedule.token` or `schedule.existingSecret`; the schedule chart takes `relay.tokenSha256` or `relay.tokenSecret`."

Design D7, verbatim: "Settings both set or both empty; both empty gives 503 `schedules_unconfigured`".

Scope (agents-orchestrator chart): `chart/agents-orchestrator/values.yaml` (`schedule.url`, `schedule.token`, `schedule.existingSecret`), `templates/secret.yaml`, `templates/_config.tpl`, `templates/configmap.yaml`, `templates/deployment.yaml` (ORCH_SCHEDULE_TOKEN as a secretKeyRef on the api container only), README (Secrets), `tests/test_chart_config.py`. Mirrors Matrix orch-chart-chat.

## Acceptance conditions

- ac1: schedule.url renders ORCH_SCHEDULE_URL in the settings ConfigMap [evidence: test:tests/test_chart_config.py::test_schedule_url_in_configmap]
- ac2: schedule.token renders a chart Secret and ORCH_SCHEDULE_TOKEN as a secretKeyRef on the api container only, schedule.existingSecret wins over it, and the token never appears in the ConfigMap [evidence: test:tests/test_chart_config.py::test_schedule_token_secret_on_api_only]
- ac3: a schedule URL without a token source, or a token source without a URL, fails the render with a message naming both values [evidence: test:tests/test_chart_config.py::test_schedule_url_and_token_together]
- ac4: without schedule values neither ORCH_SCHEDULE_URL nor ORCH_SCHEDULE_TOKEN is rendered [evidence: test:tests/test_chart_config.py::test_schedule_absent_by_default]
- ac5: no secret value reaches the ConfigMap [evidence: test:tests/test_chart_config.py::test_no_secret_values_in_configmap]
- ac6: README Secrets documents schedule.url, schedule.token and schedule.existingSecret [evidence: command:grep -q 'schedule.existingSecret' README.md && grep -q 'ORCH_SCHEDULE_TOKEN' README.md]
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

- Values: `schedule: {url: "", token: "", existingSecret: ""}`; the chart Secret key `schedule-token` (or the existing Secret's key named in values, as the chat block does).

## Expected outcome

The orchestrator chart can turn the schedule relay on with its token kept in a Secret.

## Steps

- Red: add the five chart tests; run `uv run --frozen pytest tests/test_chart_config.py`: fail.
- Green: values, templates, README; run the task's verify and `mise run lint:chart`. Quote the summary line.

## Notes

- Copy the shape of the Matrix chat block (orch-chart-chat) next to it; if both blocks repeat the same helper logic, factor one named template both use (boy scout, same files).
