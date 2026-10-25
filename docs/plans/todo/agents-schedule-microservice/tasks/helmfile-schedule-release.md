---
title: helmfile schedule release
status: todo
repo: agents-helmfile
value: "the schedule service is declared in the agents namespace, wired to its database, the orchestrator and the shared host"
files: [helmfile.yaml.gotmpl, values/agents-schedule/common.yaml, tests/test_schedule_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_schedule_release.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [helmfile-schedule-db-release, chart-ingress-and-test-hook, schedule-service-token]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile schedule release

## Requirement

Add release `agents-schedule` (design D13, D14; approval A6): chart `oci://harbor.szymonrichert.pl/charts/agents-schedule` (version pinned by `deploy-schedule`; `0.1.0` here), `needs: [agents/agents-schedule-db]`, labels as the db. `values/agents-schedule/common.yaml`:

- `postgres.existingSecret: agents-schedule-db-cluster-app`, `existingSecretKey: uri`.
- `orchestrator.url: http://agents-orchestrator-services:8002` (the orchestrator's service port, contract `orch-services-service`); `orchestrator.token` comes from SOPS `values/agents-schedule/default.secrets.yaml` (task schedule-service-token).
- `env.SCHED_ALLOWED_CIDRS: 127.0.0.1/32` (only the sidecar).
- `components.api.podAnnotations`: the oauth2-proxy injector annotations with the shared secret `agents-orchestrator-proxy` (as `values/agents-orchestrator/common.yaml`).
- `ingress`: host `lab.szymonrichert.pl`, path `/schedules` Prefix, TLS secret `agents-orchestrator-tls`, no cert-manager annotation (contract `agents-web-url-layout`), the node-IP `denySourceRanges` the orchestrator uses.

## Acceptance conditions

- AC1: the release needs the db release and pins the OCI chart [evidence: test:tests/test_schedule_release.py::test_release_declared]
- AC2: database and orchestrator token come from their Secrets and the URL is the service port [evidence: test:tests/test_schedule_release.py::test_secrets_wired]
- AC3: the ingress routes /schedules on the lab host with the shared TLS secret and no cert-manager annotation [evidence: test:tests/test_schedule_release.py::test_ingress_path]
- AC4: the api pod carries the SSO annotations and the allowlist admits only the sidecar [evidence: test:tests/test_schedule_release.py::test_sso_and_allowlist]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-schedule/common.yaml`
- `tests/test_schedule_release.py`

## Interfaces

- Release `agents-schedule` values (part `agents-schedule-release-values`).

## Expected outcome

The schedule service is declared behind the shared SSO under `/schedules` on the lab host.

## Steps

- Write tests/test_schedule_release.py; run: fails.
- Add the release and values; the test passes.
- `mise run lint` clean.

## Notes

- Never the orchestrator's port 8000 (403 from its CIDR allowlist); port 8002 takes bearer service tokens (`orch-service-tokens`).

- 2026-10-25 amended: align to released agents-common v0.3.0 session names and the reuse rule
