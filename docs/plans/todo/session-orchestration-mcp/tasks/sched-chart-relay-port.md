---
title: sched chart relay port
status: todo
repo: agents-schedule
value: "the deployed agents-schedule exposes its relay listener through its own Service, the hash only in a Secret"
files: [chart/agents-schedule/values.yaml, chart/agents-schedule/templates/service-relay.yaml, chart/agents-schedule/templates/deployment.yaml, chart/agents-schedule/templates/_config.tpl, chart/agents-schedule/templates/secret.yaml, README.md, tests/test_chart.py]
verify: "uv run pytest tests/test_chart.py tests/test_chart_ingress.py && mise run lint"
depends_on: [sched-relay-routes]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 8
expected_tokens: 1828146
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# sched chart relay port

## Requirement

README Goal G5, verbatim: "Schedule calls go through the orchestrator, which relays them to a token-protected listener on agents-schedule that records each schedule's owner; the agent token never leaves the orchestrator."

Design D15, verbatim: "Port 8001 is free in the api container. The relay gets its own Service `agents-schedule-api-relay`, port 8001 to container port `relay` 8001, selecting only the api component (my call, mirrors the connector's `-api-agents` Service)."

Design D16, verbatim: "the schedule chart takes `relay.tokenSha256` or `relay.tokenSecret`."

Scope (agents-schedule chart): `chart/agents-schedule/values.yaml` (`relay.port: 8001`, `relay.tokenSha256`, `relay.tokenSecret.{name,key}`), new `templates/service-relay.yaml` (`<fullname>-api-relay`), `templates/deployment.yaml` (container port `relay` and `SCHED_RELAY_TOKEN_SHA256` secretKeyRef on the api container only), `templates/_config.tpl` (`SCHED_RELAY_PORT`), `templates/secret.yaml` (the hash Secret when `relay.tokenSha256` is set), README (chart values), `tests/test_chart.py`. The relay is on only when a hash source is set.

## Acceptance conditions

- ac1: with a relay hash set the chart renders the -api and -api-relay Services, the relay Service on port 8001 targeting port relay and selecting only the api component [evidence: test:tests/test_chart.py::test_relay_service]
- ac2: the api container exposes port relay 8001 and the worker container does not [evidence: test:tests/test_chart.py::test_relay_port_on_api_only]
- ac3: SCHED_RELAY_TOKEN_SHA256 reaches only the api container through a secretKeyRef (chart Secret from relay.tokenSha256, or relay.tokenSecret, which wins), never the ConfigMap, and a malformed hash fails the render [evidence: test:tests/test_chart.py::test_relay_hash_secret_on_api_only]
- ac4: the ConfigMap renders SCHED_RELAY_PORT, and without relay values no relay Service, port or variable is rendered [evidence: test:tests/test_chart.py::test_relay_absent_by_default]
- ac5: helm lint passes [evidence: command:mise run lint:chart]
- ac6: the targeted tests and lint pass [evidence: command:uv run pytest tests/test_chart.py tests/test_chart_ingress.py && mise run lint]

## Files

- `chart/agents-schedule/values.yaml`
- `chart/agents-schedule/templates/service-relay.yaml`
- `chart/agents-schedule/templates/deployment.yaml`
- `chart/agents-schedule/templates/_config.tpl`
- `chart/agents-schedule/templates/secret.yaml`
- `README.md`
- `tests/test_chart.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
