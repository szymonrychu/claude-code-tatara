---
title: helm chart rbac and ingress
status: in-progress
repo: agent-orchestrator
value: The chart gives the reconciler least-privilege RBAC in one namespace and an opt-in ingress with no homelab defaults
files: [chart/agent-orchestrator/values.yaml, chart/agent-orchestrator/templates/role.yaml, chart/agent-orchestrator/templates/rolebinding.yaml, chart/agent-orchestrator/templates/ingress.yaml, tests/test_chart_rbac_ingress.py, README.md]
verify: "uv run pytest tests/test_chart_rbac_ingress.py -q && mise run lint && mise run lint:chart"
depends_on: [helm-chart-deployments]
owns: []
uses: [helm-render, agent-orchestrator-chart]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-helm-chart-rbac-and-ingress/agent-orchestrator
branch: agent-orchestrator-helm-chart-rbac-and-ingress
verified_head: ""
run: ""
provides: []
---

# helm chart rbac and ingress

## Requirement

The reconciler's RBAC and the optional ingress (D9, D26, D28).

New `values.yaml` key: `rbac: {create: true}`.

`templates/role.yaml`, rendered when `rbac.create`: a namespaced Role `<fullname>-reconciler` in the release namespace (`agents`, D26) with exactly these rules (D9):
- apps statefulsets; core services, configmaps and persistentvolumeclaims: get, list, watch, create, patch, delete
- core secrets: create, patch, delete only (no get, list or watch)
- core pods: get, list, watch, delete
- batch jobs: get, list, watch, create, delete
- core pods/log: get

Never pods/exec, never a wildcard, and no ClusterRole or ClusterRoleBinding.

`templates/rolebinding.yaml`: binds that Role to ServiceAccount `<fullname>-reconciler` only (helm-chart-deployments).

`templates/ingress.yaml`: the `helm create` ingress, kept optional:
- `ingress.enabled: false` by default
- `className`, `annotations`, `hosts[].paths[]` and `tls` all come from values, routed to the api Service port
- the default annotations are `{}`, and className is empty

No homelab defaults anywhere in values.yaml: no `szymonrichert.pl` outside `image.repository`, and no `rook-ceph`, `letsencrypt`, `192.168.`, `regcred`, `whitelist-source-range` or `nginx` default. agents-helmfile sets those through values.

README `## Helm chart` gains the rbac and ingress values and an example with LAN-only ingress annotations, as an example only.

## Acceptance conditions

- AC1: the Role grants exactly the D9 rules in the release namespace [evidence: test:tests/test_chart_rbac_ingress.py::test_role_has_exactly_d9_rules]
- AC2: secrets verbs are create, patch and delete only, and no rule grants pods/exec or a wildcard [evidence: test:tests/test_chart_rbac_ingress.py::test_secrets_write_only_and_no_exec]
- AC3: the RoleBinding binds only the reconciler ServiceAccount, and no cluster-scoped RBAC renders [evidence: test:tests/test_chart_rbac_ingress.py::test_rolebinding_binds_reconciler_only]
- AC4: rbac.create false renders no Role or RoleBinding [evidence: test:tests/test_chart_rbac_ingress.py::test_rbac_create_false]
- AC5: the ingress is off by default and, when enabled, takes className, annotations, hosts and tls from values to the api Service [evidence: test:tests/test_chart_rbac_ingress.py::test_ingress_optional_from_values]
- AC6: values.yaml carries no homelab defaults [evidence: test:tests/test_chart_rbac_ingress.py::test_values_have_no_homelab_defaults]

## Files

- `chart/agent-orchestrator/values.yaml`
- `chart/agent-orchestrator/templates/role.yaml`
- `chart/agent-orchestrator/templates/rolebinding.yaml`
- `chart/agent-orchestrator/templates/ingress.yaml`
- `tests/test_chart_rbac_ingress.py`
- `README.md`

## Interfaces

- values `rbac.create`, `ingress.*` (contract `agent-orchestrator-chart`)
- Role and RoleBinding `<fullname>-reconciler`: the production form of D9, the one the kind e2e installs

## Expected outcome

The chart grants the reconciler exactly the D9 verbs in its own namespace, never Secret reads. Its ingress is opt-in and fully driven by values.

## Steps

- Write tests/test_chart_rbac_ingress.py with the six named tests. Run `uv run pytest tests/test_chart_rbac_ingress.py -q` and expect failures.
- Write role.yaml and rolebinding.yaml, adapt ingress.yaml from `helm create`, and add the values and the README lines.
- Rerun and expect `6 passed`, then run `mise run lint` and `mise run lint:chart`.

## Notes

The verb list must match README `## Kubernetes permissions` (reconciler-loop). The kind e2e proves the list is sufficient by installing this chart, and FakeKube (reconciler-loop) simulates the same Role.

agents-helmfile sets the ingress through these values: className nginx, host agents.szymonrichert.pl, letsencrypt-prod, whitelist 192.168.1.0/24, proxy timeouts 3600.
