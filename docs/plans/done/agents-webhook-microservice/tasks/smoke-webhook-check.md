---
title: smoke webhook check
status: done
repo: agents-helmfile
value: "the live smoke proves the public ingest, the webhook API and the orchestrator service port work after every apply"
files: [scripts/smoke.sh, tests/test_smoke_script.py, README.md]
verify: "uv run pytest -q -p no:cacheprovider tests/test_smoke_script.py && mise run lint"
depends_on: [helmfile-webhook-releases, helmfile-web-webhooks-entry]
model: ""
review: ""
verified_head: 6d2a9e0
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: 2
actual_minutes: 11
actual_tokens: 1042209
actual_roles: "impl 7, review 5"
actual_role_tokens: "impl 830158, review 212051"
---

# smoke webhook check

## Requirement

Extend the smoke (design D13, D14; re-plan 2026-10-25: per-webhook endpoints with basic auth). Paths are in code/agents-helmfile.

- `scripts/smoke.sh` webhook steps, each bounded and cleaned up by the existing trap; no cluster is started:
  1. `deploy/agents-webhook-ingest`, `-api`, `-worker` are Available.
  2. Port-forward to the api container port (bypassing the sidecar): `POST /webhooks/api/v1/endpoints {type: github-issue, preset_id: <the default preset id from GET /api/v1/presets>, suffix: smoke-<random>}` -> 201 with a username and password held in shell variables only, never echoed; the trap deletes the endpoint (`DELETE /webhooks/api/v1/endpoints/{id}`) on every exit path.
  3. Port-forward to the ingest Service: `POST /webhook/smoke-<random>` with those credentials and a minimal GitHub `issues` closed payload -> 202 with status `ignored`, reason `action_ignored` (no cluster); the same with a wrong password -> 401; an unknown suffix -> 401 with the same body; `GET /healthz` 200.
  4. `GET /webhooks/api/v1/events?endpoint_id=<id>&limit=5` lists that event as `ignored`.
  5. From an in-cluster pod (as the existing agent `me` check): `GET http://agent-orchestrator-services:8002/api/v1/presets` with the webhook token -> 200, without -> 401.
  6. Through the public ingress: `POST https://lab.szymonrichert.pl/webhook/smoke-unknown` without credentials -> 401 with `WWW-Authenticate: Basic realm="agents-webhook"` (the path is public and reaches the ingest pod, not SSO).
- `tests/test_smoke_script.py` with the fake binaries: happy path; each failing check fails the smoke and still deletes the smoke endpoint; no secret value printed.
- README: a `## agents-webhook` section: the releases, how to create an endpoint and paste its URL and credentials into GitHub, GitLab and Grafana, and that the password is shown once.

## Acceptance conditions

- AC1: the smoke checks endpoint basic auth, the events API and the service port, and passes on the happy path [evidence: test:tests/test_smoke_script.py::test_webhook_checks_happy_path]
- AC2: each webhook check failing fails the smoke and still deletes the smoke endpoint [evidence: test:tests/test_smoke_script.py::test_webhook_check_failures]
- AC3: no secret value is printed [evidence: test:tests/test_smoke_script.py::test_webhook_smoke_prints_no_secret]
- AC4: the existing smoke tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_smoke_script.py && mise run lint]

## Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `README.md`

## Interfaces

- Uses `orch-service-tokens` and `webhook-ingest-api`.

## Expected outcome

`mise run smoke` covers the webhook service end to end without side effects beyond one ignored event row and a temporary endpoint it deletes.

## Steps

- Red: tests with fakes; run: fail. Green: smoke steps and README; run the verify command.

## Notes

- Pattern: the existing steps and fakes in `tests/test_smoke_script.py` (`test_agent_me_check_runs_in_pod_with_its_own_env`).

- 2026-10-25 amended: re-plan 2026-10-25: per-webhook endpoints (/webhook/<suffix>, one type, one preset, basic auth) replace per-source secrets and mappings; agent reuse is opt-in per preset (design D3, D7, D16-D19)

- 2026-10-25 done
