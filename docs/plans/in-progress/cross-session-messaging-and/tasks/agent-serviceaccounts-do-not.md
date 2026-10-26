---
title: Agent ServiceAccounts do not inherit api annotations
status: todo
repo: agents-orchestrator
value: Cloud-identity annotations on the api ServiceAccount can never leak to agent pods or Jobs
files: [chart/agents-orchestrator/templates/serviceaccount.yaml, chart/agents-orchestrator/values.yaml, tests/test_chart_kube_access.py, README.md]
verify: "unset VIRTUAL_ENV && uv run pytest tests/test_chart_kube_access.py -q -o addopts=\"\" && mise run lint:chart"
depends_on: [chart-kube-access-rbac]
model: sonnet
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 661202
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Agent ServiceAccounts do not inherit api annotations

## Requirement

Security review finding (MEDIUM, verified by the orchestrator 2026-10-27): chart/agents-orchestrator/templates/serviceaccount.yaml renders the new `<fullname>-agent` and `<fullname>-kube-access` ServiceAccounts with `{{- with .Values.serviceAccount.annotations }}`, copied from the api ServiceAccount. If an operator sets cloud-identity annotations on the api ServiceAccount (IRSA, GKE Workload Identity), every agent pod and Job would inherit that identity, and such webhooks inject credentials even with automountServiceAccountToken false, breaking goal G3 ("Every other agent pod and every Job runs with an explicit ServiceAccount and no mounted token"). Fix: the agent and kube-access ServiceAccounts no longer read serviceAccount.annotations; they read their own values `agentServiceAccount.annotations` and `kubeAccess.annotations`, both default `{}` in values.yaml and documented in the README values/ServiceAccount text. The api and reconciler ServiceAccounts keep serviceAccount.annotations unchanged.

## Acceptance conditions

- ac1: with serviceAccount.annotations set, the agent and kube-access ServiceAccounts render without those annotations while the api and reconciler ServiceAccounts keep them [evidence: test:tests/test_chart_kube_access.py::test_agent_accounts_do_not_inherit_api_annotations]
- ac2: agentServiceAccount.annotations and kubeAccess.annotations render on their own ServiceAccount only, and both default to empty in values.yaml [evidence: test:tests/test_chart_kube_access.py::test_agent_account_annotations_own_values]
- ac3: chart tests, helm lint, nomenclature and lint pass [evidence: command:unset VIRTUAL_ENV && uv run pytest tests/test_chart_*.py tests/test_nomenclature.py -q -o addopts="" && mise run lint:chart && mise run lint]

## Files

- `chart/agents-orchestrator/templates/serviceaccount.yaml`
- `chart/agents-orchestrator/values.yaml`
- `tests/test_chart_kube_access.py`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
