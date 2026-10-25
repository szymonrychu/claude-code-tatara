---
title: deploy pin web
status: done
repo: agents-helmfile
value: the agents namespace gets the agents-web release and the / and /api path split
files: [helmfile.yaml.gotmpl, values/agents-web/common.yaml, values/agent-orchestrator/common.yaml, tests/test_web_release.py, tests/test_orchestrator_release.py, README.md]
verify: "uv run pytest -q -p no:cacheprovider tests/test_web_release.py tests/test_orchestrator_release.py -k \"not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster and not test_web_release_chart\" && uv run ruff check . && uv run ruff format --check ."
depends_on: [web-docs-memory, web-ci-release, web-backend-menu, web-chart-config-ingress]
model: ""
review: ""
verified_head: 46ef967
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: 1
actual_minutes: 2
actual_tokens: 321160
actual_roles: "impl 1, review 1"
actual_role_tokens: "impl 201193, review 119967"
---

# deploy pin web

## Requirement

Add the agents-web release and split the host's paths (design D2, D6, D7, D10). Paths are in code/agents-helmfile.

Precondition, checked first: the agents-web PR of this epic is merged to main and its main CI published `harbor.szymonrichert.pl/containers/agents-web:<sha7>` and chart `oci://harbor.szymonrichert.pl/charts/agents-web` `0.1.0-main.<sha7>` (`helm show chart ... --version 0.1.0-main.<sha7>` succeeds). The orchestrator writes `<sha7>` into this task with `ticket.py amend` once the PR merges; otherwise end `blocked` with whoCanClear "orchestrator: merge the agents-web PR of frontend-decoupling and wait for its main CI".

- `helmfile.yaml.gotmpl`: release `agents-web`, namespace `agents`, chart `oci://harbor.szymonrichert.pl/charts/agents-web`, version `0.1.0-main.<sha7>`, timeout 600, labels `purpose: agents`, `application: agents-web`, `<<: *default`.
- `values/agents-web/common.yaml`: `image.tag` `<sha7>`; `podAnnotations` for the oauth2-proxy webhook identical to the api's (enable, redeem-url, `secret-name: agent-orchestrator-proxy`, `secret-namespace: agents`); `backends: [{id: orchestrator, label: Orchestrator, basePath: /api/v1}]`; `ingress`: enabled, className nginx, `denySourceRanges` the same node IPs as the orchestrator, host `lab.szymonrichert.pl` path `/` Prefix, tls `agent-orchestrator-tls` for that host, and no `cert-manager.io/cluster-issuer` or `kubernetes.io/tls-acme` annotation.
- `values/agent-orchestrator/common.yaml`: the ingress path becomes `/api` (Prefix). Its cert-manager annotations, timeouts, TLS, `ORCH_ALLOWED_ORIGINS` (`https://lab.szymonrichert.pl`, unchanged: same origin) stay.
- `tests/test_web_release.py`: `test_web_pin_matches_image` (chart version and image tag carry the same `<sha7>`, read as text, offline), `test_web_behind_oauth2_proxy_with_orchestrator_secret`, `test_web_ingress_owns_root_without_cert_annotations`, `test_web_backends_list_orchestrator_api`, `test_web_release_chart` (helmfile build: chart, namespace, labels).
- `tests/test_orchestrator_release.py`: `test_orchestrator_ingress_path_is_api`; `test_ingress_lan_only_no_ingress_auth` and the others keep passing.
- `README.md`: the agents-web release and the URL layout of the host.

## Acceptance conditions

- AC1: chart version and image tag of agents-web agree and the test runs offline [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- AC2: the web pod uses the orchestrator's oauth2-proxy secret [evidence: test:tests/test_web_release.py::test_web_behind_oauth2_proxy_with_orchestrator_secret]
- AC3: the web Ingress owns / with the shared TLS secret and no cert-manager annotation [evidence: test:tests/test_web_release.py::test_web_ingress_owns_root_without_cert_annotations]
- AC4: the web config lists the orchestrator at /api/v1 [evidence: test:tests/test_web_release.py::test_web_backends_list_orchestrator_api]
- AC5: the orchestrator Ingress serves /api only [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_ingress_path_is_api]
- AC6: the pinned chart and image exist in Harbor [evidence: judgement:the task notes quote helm show chart and docker manifest inspect for the pinned sha]
- AC7: the offline release tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_web_release.py tests/test_orchestrator_release.py -k "not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster and not test_web_release_chart" && uv run ruff check . && uv run ruff format --check .]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-web/common.yaml`
- `values/agent-orchestrator/common.yaml`
- `tests/test_web_release.py`
- `tests/test_orchestrator_release.py`
- `README.md`

## Interfaces

- Consumes contracts `agents-web-chart` and `agents-web-image`; implements `agents-web-url-layout` and `agents-web-backends-config` for the live host.

## Expected outcome

`helmfile diff` shows a new `agents-web` release and the orchestrator Ingress path changing from `/` to `/api`, nothing else.

## Steps

- Check the precondition; otherwise end blocked as the requirement says.
- Red: `tests/test_web_release.py` and the new orchestrator test; they fail (no release, path `/`).
- Green: release block, values files, orchestrator path, README.
- Run the AC7 command: pass.

## Notes

- `values/agents-web/default.secrets.yaml` is not needed (no secret values); the `default` template's `missingFileHandler: Warn` covers it, confirmed by `mise run diff` in apply-smoke-web-cutover.
- Only one Ingress per host carries cert-manager annotations (design D7), so there is one Certificate for `agent-orchestrator-tls`.

- 2026-10-25 done
