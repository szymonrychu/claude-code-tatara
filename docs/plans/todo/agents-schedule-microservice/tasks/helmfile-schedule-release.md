---
title: helmfile schedule release
status: todo
repo: agents-helmfile
value: "the schedule service is declared in the agents namespace, wired to its database, the orchestrator and the shared host"
files: [helmfile.yaml.gotmpl, values/agents-schedule/common.yaml, tests/test_schedule_release.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_schedule_release.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [helmfile-schedule-db-release, chart-ingress-and-test-hook]
owns: [agents-schedule-release-values]
uses: [agents-schedule-db-release, agents-schedule-chart, agents-schedule-settings-env, orch-service-tokens, web-ingress-path-layout]
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

# helmfile schedule release

## Requirement

Add release `agents-schedule` (design D13, D14; approval A6): chart `oci://harbor.szymonrichert.pl/charts/agents-schedule` (version pinned by `deploy-schedule`; a placeholder `0.1.0` here), `needs: [agents/agents-schedule-db]`, labels as the db. `values/agents-schedule/common.yaml`:

- `postgres.existingSecret: agents-schedule-db-cluster-app`, `existingSecretKey: uri`.
- `orchestrator.url`: the orchestrator's service-token endpoint (contract `orch-service-tokens`), `orchestrator.token.existingSecret: agents-schedule-orchestrator-token`, key `token`.
- `env.SCHED_ALLOWED_CIDRS: 127.0.0.1/32` (only the sidecar).
- `components.api.podAnnotations`: the oauth2-proxy injector annotations with the shared secret `agent-orchestrator-proxy` (as `values/agent-orchestrator/common.yaml`).
- `ingress`: host `lab.szymonrichert.pl`, path `/schedules/api` Prefix, TLS secret `agent-orchestrator-tls`, no cert-manager annotation (contract `web-ingress-path-layout`), the node-IP `denySourceRanges` and SSE timeouts the orchestrator uses.

## Acceptance conditions

- AC1: the release needs the db release and pins the OCI chart [evidence: test:tests/test_schedule_release.py::test_release_declared]
- AC2: database and orchestrator token come from their Secrets [evidence: test:tests/test_schedule_release.py::test_secrets_wired]
- AC3: the ingress routes /schedules/api on the lab host with the shared TLS secret and no cert-manager annotation [evidence: test:tests/test_schedule_release.py::test_ingress_path]
- AC4: the api pod carries the SSO annotations and the allowlist admits only the sidecar [evidence: test:tests/test_schedule_release.py::test_sso_and_allowlist]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-schedule/common.yaml`
- `tests/test_schedule_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
