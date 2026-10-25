---
title: smoke webhook check
status: todo
repo: agents-helmfile
value: "the live smoke proves the public ingest, the webhook API and the orchestrator service port work after every apply"
files: [scripts/smoke.sh, tests/test_smoke_script.py, README.md]
verify: "uv run pytest -q -p no:cacheprovider tests/test_smoke_script.py && mise run lint"
depends_on: [helmfile-webhook-releases, helmfile-web-webhooks-entry]
owns: []
uses: [orch-service-tokens, webhook-ingest-api]
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# smoke webhook check

## Requirement

Extend the smoke (design D13, D14). Paths are in code/agents-helmfile.

- `scripts/smoke.sh` webhook steps, each bounded and cleaned up by the existing trap, all non-destructive (no mapping created, no cluster started):
  1. `deploy/agents-webhook-ingest`, `-api`, `-worker` are Available.
  2. Port-forward to the ingest Service: `POST /webhooks/github` with a valid signature over a minimal `issues` opened payload for the repo `smoke/never-mapped` -> 202 with status `ignored`, reason `no_mapping`; the same with a wrong signature -> 401; `GET /healthz` 200. The GitHub secret is read in-process from the cluster Secret by the script, never echoed.
  3. Port-forward to the api container port (bypassing the sidecar): `GET /webhooks/api/v1/events?source=github&limit=5` lists that event id as `ignored`.
  4. From an in-cluster pod (as the existing agent `me` check): `GET http://agent-orchestrator-services:8002/api/v1/presets` with the webhook token -> 200, without -> 401.
  5. Through the public ingress: `POST https://lab.szymonrichert.pl/webhooks/grafana` without a token -> 401 (the path is public and reaches the ingest pod, not SSO).
- `tests/test_smoke_script.py` with the fake binaries: happy path; each failing check fails the smoke and cleans up; no secret value printed.
- README: a `## agents-webhook` section: the releases, how to read the three source secrets with the project's secret helper, the URLs to configure in GitHub, GitLab and Grafana.

## Acceptance conditions

- AC1: the smoke checks ingest signature handling, the events API and the service port, and passes on the happy path [evidence: test:tests/test_smoke_script.py::test_webhook_checks_happy_path]
- AC2: each webhook check failing fails the smoke and cleans up [evidence: test:tests/test_smoke_script.py::test_webhook_check_failures]
- AC3: no secret value is printed [evidence: test:tests/test_smoke_script.py::test_webhook_smoke_prints_no_secret]
- AC4: the existing smoke tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_smoke_script.py && mise run lint]

## Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `README.md`

## Interfaces

- Uses `orch-service-tokens` and `webhook-ingest-api`.

## Expected outcome

`mise run smoke` covers the webhook service end to end without side effects beyond one ignored event row.

## Steps

- Red: tests with fakes; run: fail. Green: smoke steps and README; run the verify command.

## Notes

- Pattern: the existing steps and fakes in `tests/test_smoke_script.py` (`test_agent_me_check_runs_in_pod_with_its_own_env`).
