---
title: helm chart deployments
status: done
repo: agent-orchestrator
value: The chart runs the four orchestrator processes with migrations first and Kubernetes credentials only on the reconciler
files: [chart/agent-orchestrator/values.yaml, chart/agent-orchestrator/templates/deployment.yaml, chart/agent-orchestrator/templates/service.yaml, chart/agent-orchestrator/templates/serviceaccount.yaml, chart/agent-orchestrator/templates/NOTES.txt, chart/agent-orchestrator/templates/tests/test-connection.yaml, tests/test_chart_deployments.py]
verify: "uv run pytest tests/test_chart_deployments.py -q && mise run lint && mise run lint:chart"
depends_on: [helm-chart-config-postgres, helm-chart-scaffold, scaffold-repo-and-cli]
model: ""
review: ""
verified_head: bb95fe6dbebe5198caf1ae4c2efc6241cf9b3afd
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helm chart deployments

## Requirement

The chart's four component Deployments, Service, ServiceAccounts, NOTES and helm test (D28, D1, D9, D20). Each template starts from its `helm create` version.

New `values.yaml` keys:
- `components`: `{api: {replicas: 1, resources: {}, extraArgs: [], livenessProbe: {}, readinessProbe: {}}, dispatcher: {replicas: 1, ...}, ingester: {replicas: 1, ...}, reconciler: {replicas: 1, ...}}`
- `terminationGracePeriodSeconds: 30`, which must exceed `ORCH_SHUTDOWN_GRACE_SECONDS` (default 20)

`templates/deployment.yaml` ranges over the four components and renders Deployment `<fullname>-<component>`:
- labels from `agent-orchestrator.componentLabels`
- replicas from values
- pod and container security contexts, imagePullSecrets, nodeSelector, tolerations, affinity
- initContainer `migrate` running `orch migrate` with the same image and env
- container `orch <component>` with `extraArgs`, image `<repository>:<tag | default .Chart.AppVersion>`, and the env from `agent-orchestrator.env` (helm-chart-config-postgres)
- resources
- a `checksum/settings` pod annotation over the settings ConfigMap, so a settings change rolls every component
- The api container exposes port `http` 8000 (`ORCH_HTTP_PORT`), with liveness `/healthz` and readiness `/readyz` by default. The other components get only the probes given in values.
- Only the reconciler Deployment uses ServiceAccount `<fullname>-reconciler`. The api, dispatcher and ingester use the default ServiceAccount with `automountServiceAccountToken: false` on the pod, so no Kubernetes credential reaches them (D1).

`templates/serviceaccount.yaml`:
- the `helm create` ServiceAccount (`agent-orchestrator.serviceAccountName`, `automountServiceAccountToken: false`)
- plus `<fullname>-reconciler`, rendered when `serviceAccount.create`

Other templates:
- `templates/service.yaml`: the `helm create` Service on `service.port`, targetPort `http`, selecting the api component only.
- `templates/NOTES.txt`: adapted to the api Service (port-forward hint, or the ingress URL when enabled).
- `templates/tests/test-connection.yaml`: the `helm create` test pod, calling `<fullname>:<service.port>/healthz`.

## Acceptance conditions

- AC1: four Deployments render, each with a migrate initContainer running orch migrate and the shared env [evidence: test:tests/test_chart_deployments.py::test_four_deployments_with_migrate_init]
- AC2: each Deployment runs orch <component> with its replicas, resources and extraArgs from values [evidence: test:tests/test_chart_deployments.py::test_component_commands_and_values]
- AC3: only the reconciler pod uses the reconciler ServiceAccount; the other three do not mount a token [evidence: test:tests/test_chart_deployments.py::test_only_reconciler_gets_kube_token]
- AC4: the Service selects only the api pods on the http port, and the api has healthz and readyz probes [evidence: test:tests/test_chart_deployments.py::test_api_service_and_probes]
- AC5: the image tag defaults to appVersion and an explicit tag wins [evidence: test:tests/test_chart_deployments.py::test_image_tag_defaults_to_app_version]
- AC6: the helm test pod calls the api healthz [evidence: test:tests/test_chart_deployments.py::test_helm_test_targets_healthz]
- AC7: a settings change changes the checksum annotation of every component [evidence: test:tests/test_chart_deployments.py::test_settings_checksum_rolls_components]

## Files

- `chart/agent-orchestrator/values.yaml`
- `chart/agent-orchestrator/templates/deployment.yaml`
- `chart/agent-orchestrator/templates/service.yaml`
- `chart/agent-orchestrator/templates/serviceaccount.yaml`
- `chart/agent-orchestrator/templates/NOTES.txt`
- `chart/agent-orchestrator/templates/tests/test-connection.yaml`
- `tests/test_chart_deployments.py`

## Interfaces

- values `components.*`, `terminationGracePeriodSeconds`, `serviceAccount.*`, `service.*` (contract `agent-orchestrator-chart`)
- Deployments `<fullname>-api|dispatcher|ingester|reconciler`, Service `<fullname>`, ServiceAccount `<fullname>-reconciler` (bound by helm-chart-rbac-and-ingress)

## Expected outcome

`helm template` with ci/lint-values.yaml renders the full runnable orchestrator: four Deployments behind one migrate step, one api Service, and Kubernetes credentials only on the reconciler.

## Steps

- Write tests/test_chart_deployments.py with the seven named tests. Run `uv run pytest tests/test_chart_deployments.py -q` and expect failures.
- Copy deployment.yaml, service.yaml, serviceaccount.yaml, NOTES.txt and tests/test-connection.yaml from a fresh `helm create` and adapt them, then add the values keys.
- Rerun and expect `7 passed`, then run `mise run lint` and `mise run lint:chart`.

## Notes

The ingester and reconciler hold advisory locks (D20, D25), so a second replica is a hot standby and replicas above 1 are safe. RollingUpdate is fine for every component. `orch migrate` is idempotent under concurrent initContainers (migrations-and-schema). The image's static dir and `ORCH_STATIC_DIR` come from spa-serving-and-dockerfile's Dockerfile, not from the chart.
