---
title: chart kube access rbac
status: todo
repo: agents-orchestrator
value: the deployment can grant full Kubernetes access to opted-in sessions behind one chart value
files: [chart/agents-orchestrator/values.yaml, chart/agents-orchestrator/templates/serviceaccount.yaml, chart/agents-orchestrator/templates/clusterrolebinding.yaml, chart/agents-orchestrator/templates/configmap.yaml, tests/test_chart_kube_access.py, tests/test_chart_config.py, tests/test_chart_deployments.py, README.md]
verify: "unset VIRTUAL_ENV && uv run pytest tests/test_chart_*.py -q && mise run lint:chart && mise run lint"
depends_on: [orch-session-options-spec]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 977684
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# chart kube access rbac

## Requirement

Epic description, verbatim: "Kubernetes access is additionally gated by the deployment (a chart value that creates the privileged ServiceAccount); without it the option is refused." Goal G2 (epic README), verbatim: "agent pods of a session with it on run as a ServiceAccount bound to cluster-admin with its token mounted". Goal G3, verbatim: "Every other agent pod and every Job runs with an explicit ServiceAccount and no mounted token." Non-goal, verbatim: "No scoped or per-namespace Kubernetes roles; access is all-or-nothing cluster-admin." Design D2, D3, D4, D16.

Scope (agents-orchestrator chart `chart/agents-orchestrator`):
- `values.yaml`: `kubeAccess: {enabled: false}` with a comment: renders the privileged ServiceAccount and its binding to cluster-admin; sessions with `kube_access` are refused while it is off.
- `templates/serviceaccount.yaml` (under `serviceAccount.create`, as today): a third ServiceAccount `<fullname>-agent` (labels as the others, `app.kubernetes.io/component: agent`, `automountServiceAccountToken: false`, no binding); and, when `kubeAccess.enabled`, a ServiceAccount `<fullname>-kube-access` (`app.kubernetes.io/component: kube-access`, `automountServiceAccountToken: false`). When `serviceAccount.create` is false and `kubeAccess.enabled` is true, the chart still renders `<fullname>-kube-access` (it is the feature's identity).
- New `templates/clusterrolebinding.yaml`: when `kubeAccess.enabled` and `rbac.create`, a ClusterRoleBinding `<fullname>-kube-access` with `roleRef {apiGroup: rbac.authorization.k8s.io, kind: ClusterRole, name: cluster-admin}` and the single subject ServiceAccount `<fullname>-kube-access` in the release namespace.
- `templates/configmap.yaml`: `ORCH_AGENT_SERVICE_ACCOUNT` is `<fullname>-agent` when `serviceAccount.create`, else `default`; `ORCH_KUBE_ACCESS_SERVICE_ACCOUNT` is `<fullname>-kube-access` only when `kubeAccess.enabled`.
- The reconciler Role and RoleBinding do not change.
- Tests no longer accurate, updated with the reason: `tests/test_chart_config.py::test_settings_configmap` pins the exact ConfigMap keys and now must include `ORCH_AGENT_SERVICE_ACCOUNT` (design D4); `tests/test_chart_deployments.py::test_only_reconciler_gets_kube_token` pins the exact ServiceAccount set and now must include `<fullname>-agent` with automount false (design D4). Their other assertions stay. `tests/test_chart_rbac_ingress.py` stays accurate unchanged (default values render no ClusterRoleBinding; `rbac.create: false` renders none).
- `README.md` `### RBAC`: "No ClusterRole or ClusterRoleBinding is ever rendered" becomes the value-gated exception (only `kubeAccess.enabled` with `rbac.create` renders one ClusterRoleBinding, of `<fullname>-kube-access` to cluster-admin; no ClusterRole is rendered); `## Kubernetes permissions` says the same and that the reconciler's Role is unchanged and holds no RBAC verbs; `### Settings ConfigMap` lists the two keys.

## Acceptance conditions

- ac1: with default values the chart renders no ClusterRoleBinding, no kube-access ServiceAccount and no ORCH_KUBE_ACCESS_SERVICE_ACCOUNT, and values.yaml has kubeAccess.enabled false [evidence: test:tests/test_chart_kube_access.py::test_kube_access_off_by_default]
- ac2: with kubeAccess.enabled the chart renders ServiceAccount <fullname>-kube-access with automountServiceAccountToken false and one ClusterRoleBinding of exactly that subject to ClusterRole cluster-admin, and the ConfigMap sets ORCH_KUBE_ACCESS_SERVICE_ACCOUNT to it [evidence: test:tests/test_chart_kube_access.py::test_kube_access_enabled_renders_binding]
- ac3: with kubeAccess.enabled and rbac.create false no ClusterRoleBinding is rendered while the ServiceAccount and setting are [evidence: test:tests/test_chart_kube_access.py::test_kube_access_without_rbac_create]
- ac4: the chart renders ServiceAccount <fullname>-agent with automountServiceAccountToken false and no binding, and ORCH_AGENT_SERVICE_ACCOUNT names it, or default when serviceAccount.create is false [evidence: test:tests/test_chart_kube_access.py::test_agent_service_account]
- ac5: the reconciler Role rules are unchanged with kubeAccess.enabled [evidence: test:tests/test_chart_kube_access.py::test_reconciler_role_unchanged_with_kube_access]
- ac6: every chart test, including the updated ConfigMap and ServiceAccount tests and the unchanged RBAC tests, passes and helm lint is clean [evidence: command:unset VIRTUAL_ENV && uv run pytest tests/test_chart_*.py -q && mise run lint:chart]
- ac7: README and nomenclature tests pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_nomenclature.py tests/test_readme_api.py]
- ac8: lint passes [evidence: command:mise run lint]

## Files

- `chart/agents-orchestrator/values.yaml`
- `chart/agents-orchestrator/templates/serviceaccount.yaml`
- `chart/agents-orchestrator/templates/clusterrolebinding.yaml`
- `chart/agents-orchestrator/templates/configmap.yaml`
- `tests/test_chart_kube_access.py`
- `tests/test_chart_config.py`
- `tests/test_chart_deployments.py`
- `README.md`

## Interfaces

- Chart value `kubeAccess.enabled` (bool, default false).
- Rendered objects: ServiceAccount `<fullname>-agent`; with the value, ServiceAccount `<fullname>-kube-access` and ClusterRoleBinding `<fullname>-kube-access` -> ClusterRole `cluster-admin`.
- ConfigMap keys `ORCH_AGENT_SERVICE_ACCOUNT`, `ORCH_KUBE_ACCESS_SERVICE_ACCOUNT` (settings from task orch-session-options-spec).
- agents-helmfile sets `kubeAccess.enabled: true` (task helmfile-deploy-pin).

## Expected outcome

Installing the chart with `kubeAccess.enabled` gives the orchestrator a privileged identity to reference and nothing else; without it the deployment refuses `kube_access` sessions; the reconciler's RBAC is the same as before.

## Steps

- Red: write `tests/test_chart_kube_access.py` with the five tests named in the acceptance conditions and update the two inaccurate assertions; run `unset VIRTUAL_ENV && uv run pytest tests/test_chart_*.py -q`: fails.
- Green: edit `values.yaml`, `serviceaccount.yaml`, `configmap.yaml`, add `clusterrolebinding.yaml`; run the task's verify: passes.
- README; run ac6, ac7 and ac8 commands: pass.

## Notes

- Rulings and their pin tests: binding needs both `kubeAccess.enabled` and `rbac.create` (ac2, ac3); kube-access SA rendered even with `serviceAccount.create` false (ac3 or ac2 variant); built-in `cluster-admin`, no chart ClusterRole (ac2); privileged SA automount false, pods opt in (ac2).
- Research: helm-owned binding to a fixed SA needs no new reconciler RBAC (rbac A9, A11); never edit the built-in cluster-admin (D7).
- `tests/helm_render.py` renders the chart; `ci/lint-values.yaml` is the lint input.
- `cluster-admin`, `ClusterRole` and `ClusterRoleBinding` are allowed by the nomenclature guard (after task orch-session-options-spec); no other "cluster" word.
- Chart tests need helm on PATH; run with `VIRTUAL_ENV` unset.
