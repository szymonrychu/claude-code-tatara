---
title: helmfile webhook releases
status: in-progress
repo: agents-helmfile
value: agents-webhook and its own CNPG database are declared in the agents namespace with SSO on the API and a public ingest
files: [helmfile.yaml.gotmpl, values/agents-webhook/common.yaml, values/agents-webhook-db/common.yaml, values/agents-webhook-db/default.secrets.yaml, tests/test_webhook_release.py]
verify: "uv run pytest -q -p no:cacheprovider tests/test_webhook_release.py -k \"not helmfile_build\" && uv run ruff check . && uv run ruff format --check ."
depends_on: [deploy-pin-orch-service-port, webhook-ci-images, webhook-docs-memory]
model: ""
review: full
verified_head: ""
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile webhook releases

## Requirement

The release pair for agents-webhook (design D2, D12, D13, D18; re-plan 2026-10-25: no source secrets; public ingest prefix `/webhook/`). Paths are in code/agents-helmfile.

Precondition, checked first: the agents-webhook PR of this epic is merged to main and chart `oci://harbor.szymonrichert.pl/charts/agents-webhook` `0.1.0-main.<sha7>` and image `<sha7>` exist (task webhook-ci-images notes); the orchestrator amends `<sha7>` in. Otherwise end `blocked`, whoCanClear "orchestrator: merge the agents-webhook PR and wait for its main CI".

- `helmfile.yaml.gotmpl`: `agents-webhook-db` (`cnpg/cluster` 0.9.0, `force: false`, as `agent-orchestrator-db`) and `agents-webhook` (OCI chart pinned `0.1.0-main.<sha7>`, `needs: [agents/agents-webhook-db, agents/agent-orchestrator]`), namespace `agents`, labels `application: agents-webhook`.
- `values/agents-webhook-db/common.yaml`: initdb database and owner `agents_webhook`, storage classes and backups as `agent-orchestrator-db` with its own backup path; `default.secrets.yaml` only if the db release needs one (as agent-orchestrator-db does).
- `values/agents-webhook/common.yaml`: `image.tag <sha7>`; `postgres.existingSecret: agents-webhook-db-cluster-app`, key `uri`; `orchestrator.url: http://agent-orchestrator-services:8002`; `publicBaseUrl: https://lab.szymonrichert.pl`; `trustedProxies`: the CIDR the ingress controller connects from (probed read-only, e.g. the pod CIDRs from `kubectl get nodes -o jsonpath='{.items[*].spec.podCIDR}'`, quoted in the task notes); `components.api.podAnnotations`: the same oauth2-proxy annotations as `values/agent-orchestrator/common.yaml` (`agent-orchestrator-proxy` Secret); `components.ingest.podAnnotations: {}`; `ingress`: enabled, host `lab.szymonrichert.pl`, TLS secret `agent-orchestrator-tls`, no cert-manager annotation, the api Ingress with the same node-IP `denySourceRanges` as the orchestrator and the ingest Ingress public; `env`: `WEBHOOK_BOT_LOGINS` empty, `WEBHOOK_ALLOWED_AUTHORS` empty (working answer Q8: optional, off).
- `tests/test_webhook_release.py` (offline, reading the layered values as the existing tests do): pins agree; DB secret name matches the CNPG release; api pod has the oauth2-proxy annotations and ingest has none; the ingress host and TLS secret; the orchestrator URL is the services Service; `publicBaseUrl` and `trustedProxies` are set; no `sources` value anywhere; no plaintext secret in common values; a test that needs `helmfile build` is named `test_*_helmfile_build`.

## Acceptance conditions

- AC1: agents-webhook and agents-webhook-db are declared with the pinned chart and needs [evidence: test:tests/test_webhook_release.py::test_webhook_pin_and_needs]
- AC2: SSO annotations are on the api pod only and the ingest pod has none [evidence: test:tests/test_webhook_release.py::test_sso_on_api_only]
- AC3: the database URL comes from the CNPG app secret, the orchestrator URL is the services Service, and the public base URL and trusted proxies are set [evidence: test:tests/test_webhook_release.py::test_database_and_orchestrator_wiring]
- AC4: the ingress uses the lab host and the shared TLS secret without cert-manager annotations [evidence: test:tests/test_webhook_release.py::test_ingress_host_and_tls]
- AC5: the offline release tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_webhook_release.py -k "not helmfile_build" && uv run ruff check . && uv run ruff format --check .]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-webhook/common.yaml`
- `values/agents-webhook-db/common.yaml`
- `values/agents-webhook-db/default.secrets.yaml`
- `tests/test_webhook_release.py`

## Interfaces

- Consumes `agents-webhook-chart`, `agents-webhook-image`, `orch-services-service`.

## Expected outcome

`mise run diff` shows the two new releases.

## Steps

- Check the precondition.
- Red: `tests/test_webhook_release.py`; run: fail. Green: releases and values; run the verify command.

## Notes

- Pattern: the `agent-orchestrator-db` / `agent-orchestrator` pair and `tests/test_orchestrator_release.py`, `tests/test_db_release.py`.
- The public ingest exposure was approved at the gate (A7).

- 2026-10-25 amended: re-plan 2026-10-25: per-webhook endpoints (/webhook/<suffix>, one type, one preset, basic auth) replace per-source secrets and mappings; agent reuse is opt-in per preset (design D3, D7, D16-D19)
