---
title: Agent ServiceAccounts do not inherit api annotations
status: done
repo: agents-orchestrator
value: Cloud-identity annotations on the api ServiceAccount can never leak to agent pods or Jobs
files: [chart/agents-orchestrator/templates/serviceaccount.yaml, chart/agents-orchestrator/values.yaml, tests/test_chart_kube_access.py, README.md]
verify: "unset VIRTUAL_ENV && uv run pytest tests/test_chart_kube_access.py -q -o addopts=\"\" && mise run lint:chart"
depends_on: [chart-kube-access-rbac]
model: sonnet
review: ""
verified_head: 876e70f70b8add65eca1840a259853353a3a4ad8
points: 1
expected_minutes: 4
expected_tokens: 661202
points_actual: 1
actual_minutes: 2
actual_tokens: 235424
actual_roles: "impl 1, review 1"
actual_role_tokens: "impl 172723, review 62701"
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

- values: `agentServiceAccount.annotations: {}`, `kubeAccess.annotations: {}` (new); `serviceAccount.annotations` unchanged for api and reconciler.
- templates/serviceaccount.yaml: the `-agent` and `-kube-access` documents read their own annotations.

## Expected outcome

No agent-facing ServiceAccount can pick up the api ServiceAccount's annotations; each has its own empty-by-default annotations value.

## Steps

- Red: add the two tests to tests/test_chart_kube_access.py; run the task's verify; expect ac1 to fail.
- Green: edit values.yaml and serviceaccount.yaml, README; run the task's verify and the ac3 command on the committed HEAD.

## Notes

- From the phase-5 security review (security-researcher, sonnet), verified by reading serviceaccount.yaml lines 37-40 and 55-58.
- Keep the word cluster out of new text except cluster-admin, ClusterRole, ClusterRoleBinding; nomenclature checks tracked files, so run it after committing.

- 2026-10-26 done
