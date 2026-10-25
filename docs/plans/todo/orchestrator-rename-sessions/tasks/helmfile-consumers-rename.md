---
title: helmfile consumers rename
status: todo
repo: agents-helmfile
value: agents-webhook and agents-web reach the renamed orchestrator and share its renamed Secrets
files: [helmfile.yaml.gotmpl, values/agents-webhook/common.yaml, values/agents-web/common.yaml, tests/test_webhook_release.py, tests/test_web_release.py]
verify: "uv run pytest -q tests/test_webhook_release.py tests/test_web_release.py && mise run lint"
depends_on: [helmfile-orch-release-rename, webhook-docs-sessions, web-docs-names]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile consumers rename

## Requirement

Point agents-webhook and agents-web at the renamed orchestrator and pin their renamed builds (design D1, D9, D11). Paths are in code/agents-helmfile.

Precondition, checked first: this epic's agents-webhook and agents-web PRs are merged to main and their CI published `0.1.0-main.<sha7>` charts and images; the orchestrator writes both sha7 values into this task with `ticket.py amend`; otherwise end `blocked`, whoCanClear "orchestrator: merge the agents-webhook and agents-web PRs and wait for their main CI".

- `helmfile.yaml.gotmpl`: agents-webhook `needs` `agents/agents-orchestrator` (and its own db); chart versions of agents-webhook and agents-web pinned to the merged sha7s.
- `values/agents-webhook/common.yaml`: `orchestrator.url: http://agents-orchestrator-services:8002`; image tag; SSO `secret-name: agents-orchestrator-proxy`; ingress TLS `secretName: agents-orchestrator-tls`; comments.
- `values/agents-web/common.yaml`: image tag; SSO `secret-name: agents-orchestrator-proxy`; TLS `agents-orchestrator-tls`; comments ("one Certificate for agents-orchestrator-tls").
- Tests first: `tests/test_webhook_release.py` (`test_database_and_orchestrator_wiring` on the new URL, `test_webhook_pin_and_needs` on `agents/agents-orchestrator`, `test_sso_on_api_only` and `test_ingress_host_and_tls` on the new Secrets, `test_db_values_match_orchestrator_db_shape` against `agents-orchestrator-db`); `tests/test_web_release.py` (`test_web_behind_oauth2_proxy_with_orchestrator_secret`, `test_web_ingress_owns_root_without_cert_annotations`, `test_web_pin_matches_image`).

## Acceptance conditions

- AC1: the webhook calls the orchestrator at agents-orchestrator-services:8002 [evidence: test:tests/test_webhook_release.py::test_database_and_orchestrator_wiring]
- AC2: the webhook release needs agents-orchestrator [evidence: test:tests/test_webhook_release.py::test_webhook_pin_and_needs]
- AC3: agents-web and agents-webhook use the agents-orchestrator-proxy and agents-orchestrator-tls Secrets [evidence: command:uv run pytest -q tests/test_web_release.py tests/test_webhook_release.py]
- AC4: the pinned charts and images exist in Harbor [evidence: judgement:the task notes quote helm show chart for both pinned sha7s]
- AC5: lint passes [evidence: command:mise run lint]

## Files

- `helmfile.yaml.gotmpl`
- `values/agents-webhook/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_webhook_release.py`
- `tests/test_web_release.py`

## Interfaces

- agents-webhook `orchestrator.url: http://agents-orchestrator-services:8002`; shared Secrets `agents-orchestrator-proxy`, `agents-orchestrator-tls`.

## Expected outcome

agents-webhook and agents-web are declared against the renamed orchestrator, Secrets and their renamed builds; nothing is applied here.

## Steps

- Check the precondition (both merged sha7s and Harbor charts) first.
- Red: update the named tests in `tests/test_webhook_release.py` and `tests/test_web_release.py`; they fail.
- Green: helmfile needs and pins, both values files; the verify passes.

## Notes

- agents-web and agents-webhook ingresses carry no cert-manager annotation; the orchestrator ingress owns `agents-orchestrator-tls`.
