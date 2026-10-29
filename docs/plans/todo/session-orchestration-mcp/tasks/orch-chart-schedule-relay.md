---
title: orch chart schedule relay
status: todo
repo: agents-orchestrator
value: the orchestrator chart turns the schedule relay on with its token kept in a Secret
files: [chart/agents-orchestrator/values.yaml, chart/agents-orchestrator/templates/secret.yaml, chart/agents-orchestrator/templates/_config.tpl, chart/agents-orchestrator/templates/deployment.yaml, README.md, tests/test_chart_config.py]
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

Design D16, verbatim: "The orchestrator chart takes `schedule.url`, `schedule.token` or `schedule.existingSecret`; the schedule chart takes `relay.tokenSha256` or `relay.tokenSecret`." and (staleness refresh 2026-10-29) "`ORCH_SCHEDULE_URL` and `ORCH_SCHEDULE_TOKEN` are env of the api main container only, always together, rendered by one `agents-orchestrator.scheduleEnv` helper next to `agents-orchestrator.chatEnv`, never in the shared settings ConfigMap, the migrate init containers or the other components (orchestrator MEMORY 2026-10-28, orch-chat-env-scope: the chart once put `ORCH_CHAT_URL` in the shared ConfigMap with the token on the api only, and every migrate init container crash-looped on a URL without its token)."

Design D7, verbatim: "Settings both set or both empty; both empty gives 503 `schedules_unconfigured`".

Scope (agents-orchestrator chart): `chart/agents-orchestrator/values.yaml` (`schedule.url`, `schedule.token`, `schedule.existingSecret`, `schedule.existingSecretKey`, documented like the `chat` block), `templates/secret.yaml` (the chart Secret `<fullname>-schedule`), `templates/_config.tpl` (`scheduleEnabled`, `scheduleSecretName`, `scheduleEnv` next to the chat helpers), `templates/deployment.yaml` (`scheduleEnv` included in the api main container only, a `checksum/schedule-secret` pod annotation so the api pod rolls when the chart-made token changes), README (Configuration and Secrets), `tests/test_chart_config.py`. The settings ConfigMap is not touched. Mirrors the chat block (`chatEnabled`, `chatSecretName`, `chatEnv`); if both blocks repeat the same helper logic, factor one named template both use (boy scout, same files).

## Acceptance conditions

- ac1: with schedule values set (inline token or existingSecret) the settings ConfigMap carries neither ORCH_SCHEDULE_URL nor ORCH_SCHEDULE_TOKEN [evidence: test:tests/test_chart_config.py::test_configmap_has_no_schedule_url]
- ac2: in every container of every component, init containers included, ORCH_SCHEDULE_URL is present exactly when ORCH_SCHEDULE_TOKEN is, and only in the api main container [evidence: test:tests/test_chart_config.py::test_schedule_pair_rendered_together_per_container]
- ac3: the api main container gets ORCH_SCHEDULE_URL as a plain value and ORCH_SCHEDULE_TOKEN as a secretKeyRef to the chart Secret <fullname>-schedule key schedule-token, or to schedule.existingSecret and schedule.existingSecretKey, which win [evidence: test:tests/test_chart_config.py::test_api_container_has_schedule_pair]
- ac4: schedule.token renders the chart Secret <fullname>-schedule and the api pod template carries a checksum/schedule-secret annotation that changes with the token [evidence: test:tests/test_chart_config.py::test_schedule_token_secret_on_api_only]
- ac5: a schedule URL without a token source, or a token source without a URL, fails the render with a message naming schedule.url, schedule.token and schedule.existingSecret [evidence: test:tests/test_chart_config.py::test_schedule_url_and_token_together]
- ac6: without schedule values neither variable nor the schedule Secret is rendered anywhere [evidence: test:tests/test_chart_config.py::test_schedule_absent_by_default]
- ac7: the chat block keeps rendering as before (its per-container and ConfigMap tests stay green) [evidence: command:uv run --frozen pytest tests/test_chart_config.py -k chat]
- ac8: README documents schedule.url, schedule.token, schedule.existingSecret and that both variables are env of the api main container only, never in the ConfigMap [evidence: command:grep -q 'schedule.existingSecret' README.md && grep -q 'ORCH_SCHEDULE_TOKEN' README.md]
- ac9: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_chart_config.py tests/test_chart_deployments.py && mise run lint]

## Files

- `chart/agents-orchestrator/values.yaml`
- `chart/agents-orchestrator/templates/secret.yaml`
- `chart/agents-orchestrator/templates/_config.tpl`
- `chart/agents-orchestrator/templates/deployment.yaml`
- `README.md`
- `tests/test_chart_config.py`

## Interfaces

- Values: `schedule: {url: "", token: "", existingSecret: "", existingSecretKey: schedule-token}`, documented like the `chat` block (`values.yaml`).
- `_config.tpl`: `agents-orchestrator.scheduleEnabled` (fails the render on half a pair, naming schedule.url, schedule.token and schedule.existingSecret), `agents-orchestrator.scheduleSecretName` (existingSecret wins over `<fullname>-schedule`), `agents-orchestrator.scheduleEnv` (the `ORCH_SCHEDULE_URL` value and the `ORCH_SCHEDULE_TOKEN` secretKeyRef, empty when off), next to `chatEnabled`, `chatSecretName`, `chatEnv`.
- `deployment.yaml`: `scheduleEnv` included only under `{{- if eq $component "api" }}` in the main container, right after `chatEnv`; pod annotation `checksum/schedule-secret` next to `checksum/chat-secret`.
- Tests in `tests/test_chart_config.py` reuse `_containers` (init containers included), `_env_names`, `_is_api_main` and the `CHAT_VALUES` parametrize pattern.

## Expected outcome

The orchestrator chart can turn the schedule relay on with its token kept in a Secret, and no container other than the api main one ever sees half of the pair.

## Steps

- Red: add the six schedule chart tests; run `uv run --frozen pytest tests/test_chart_config.py -k schedule`: they fail.
- Green: values, helpers, Secret, deployment, README; run the task's verify and `mise run lint:chart`. Quote the summary line.

## Notes

- Copy the shape of the chat block next to it; if both blocks repeat the same helper logic, factor one named template both use (boy scout, same files).
- Never touch `templates/configmap.yaml` or the `agents-orchestrator.settings` data: the 2026-10-28 incident (orchestrator MEMORY, orch-chat-env-scope) came from a relay URL in the shared ConfigMap, which every migrate init container loads; `Settings` refuses a URL without its token, so they crash-looped.
- helmfile MEMORY gotcha (a changed service Secret does not restart the api pods) is why the `checksum/schedule-secret` annotation is in scope.

- 2026-10-29 amended: staleness refresh: schedule pair api-main-only via scheduleEnv, never the ConfigMap (2026-10-28 chat env incident)
