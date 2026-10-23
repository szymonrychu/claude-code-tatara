---
title: helm chart scaffold
status: done
repo: agent-orchestrator
value: The repo ships a standard helm-create-shaped chart skeleton that every later chart task and agents-helmfile build on
files: [chart/agent-orchestrator/Chart.yaml, chart/agent-orchestrator/values.yaml, chart/agent-orchestrator/.helmignore, chart/agent-orchestrator/templates/_helpers.tpl, chart/agent-orchestrator/ci/lint-values.yaml, tests/helm_render.py, tests/test_chart_scaffold.py, mise.toml]
verify: "uv run pytest tests/test_chart_scaffold.py -q && mise run lint && mise run lint:chart"
depends_on: [scaffold-repo-and-cli]
owns: [helm-render, agent-orchestrator-chart]
uses: []
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-helm-chart-scaffold/agent-orchestrator
branch: agent-orchestrator-helm-chart-scaffold
verified_head: dcbbab0f2f70a4beb460343a797d4caff0b8e7c0
run: agent-orchestrator
provides: [helm-render]
acs_for_audit: []
process_gaps: []
---

# helm chart scaffold

## Requirement

Scaffold `chart/agent-orchestrator` with `helm create`, so the chart follows Helm's standard layout, helper names and labels (D28).

- Run `helm create agent-orchestrator` in a temp dir. Keep its `Chart.yaml`, `values.yaml`, `.helmignore` and `templates/_helpers.tpl` in `chart/agent-orchestrator/`.
- Do not copy the other generated templates in this task: deployment, service, serviceaccount, ingress, NOTES.txt and tests/test-connection.yaml arrive in later chart tasks, each adapted from its `helm create` version. `hpa.yaml` is dropped for good, because the ingester and reconciler are singletons (D28), and so are any other generated files (for example an httproute).
- `Chart.yaml`: apiVersion v2, name `agent-orchestrator`, type application, description, `version: 0.1.0`, `appVersion: "dev"`. CI sets `--app-version <sha7>` when it packages (helm-chart-ci-publish).
- `values.yaml`: the `helm create` keys minus `autoscaling` and the generated probes:
  - image `{repository: harbor.szymonrichert.pl/containers/agent-orchestrator, pullPolicy: IfNotPresent, tag: ""}`, where the tag defaults to appVersion
  - imagePullSecrets, nameOverride, fullnameOverride, serviceAccount, podAnnotations, podLabels
  - podSecurityContext `{runAsNonRoot: true, runAsUser: 1000, fsGroup: 1000}`, securityContext (drop ALL, no privilege escalation)
  - service `{type: ClusterIP, port: 80}`, ingress `{enabled: false, ...}`, resources, nodeSelector, tolerations, affinity
  - each key commented as helm create does
- `_helpers.tpl`: the generated `agent-orchestrator.name`, `.fullname`, `.chart`, `.labels`, `.selectorLabels` and `.serviceAccountName`, plus `agent-orchestrator.componentLabels` (selectorLabels plus `app.kubernetes.io/component`).
- `ci/lint-values.yaml`: the minimal values that make the full chart render (`agentImage`, `postgres.url`, `masterKey.value`, `claude.token`; the keys come from helm-chart-config-postgres). `helm lint` and CI use it.
- `tests/helm_render.py`, the shared render helper:
  - `render(values=None, *, show_only=None, namespace="agents", release="agent-orchestrator") -> list[dict]` runs `helm template` through subprocess with a temp values file and returns the parsed documents.
  - `render_error(values) -> str` returns stderr of a render that must fail.
  - `lint(values_file) -> subprocess.CompletedProcess`.
  - A missing helm binary is a test failure, never a skip.
- `mise.toml`:
  - adds the `helm` tool, pinned
  - task `test:chart` (`uv run pytest tests/test_chart_*.py -q`)
  - task `lint:chart` (`helm lint chart/agent-orchestrator -f chart/agent-orchestrator/ci/lint-values.yaml`)

## Acceptance conditions

- AC1: Chart.yaml is a v2 application chart named agent-orchestrator at version 0.1.0 with appVersion dev [evidence: test:tests/test_chart_scaffold.py::test_chart_metadata]
- AC2: the helm create helpers render the standard labels (name, instance, version, managed-by, helm.sh/chart) and the component label [evidence: test:tests/test_chart_scaffold.py::test_standard_helpers_and_labels]
- AC3: helm lint passes with ci/lint-values.yaml [evidence: test:tests/test_chart_scaffold.py::test_helm_lint_passes]
- AC4: hpa.yaml is not tracked and values.yaml has no autoscaling key [evidence: test:tests/test_chart_scaffold.py::test_hpa_dropped]
- AC5: render and render_error return parsed documents and the failure text [evidence: test:tests/test_chart_scaffold.py::test_render_helper_roundtrip]
- AC6: mise defines test:chart and lint:chart with a pinned helm [evidence: command:mise tasks | grep -q 'test:chart' && mise tasks | grep -q 'lint:chart' && grep -q 'helm' mise.toml]

## Files

- `chart/agent-orchestrator/Chart.yaml`
- `chart/agent-orchestrator/values.yaml`
- `chart/agent-orchestrator/.helmignore`
- `chart/agent-orchestrator/templates/_helpers.tpl`
- `chart/agent-orchestrator/ci/lint-values.yaml`
- `tests/helm_render.py`
- `tests/test_chart_scaffold.py`
- `mise.toml`

## Interfaces

- `chart/agent-orchestrator/values.yaml` (contract `agent-orchestrator-chart`, consumed by kind-e2e and epic agents-helmfile); later chart tasks add their keys to it
- `tests/helm_render.py:render`, `render_error`, `lint` (contract `helm-render`)
- helpers `agent-orchestrator.fullname`, `.labels`, `.selectorLabels`, `.componentLabels`, `.serviceAccountName`

## Expected outcome

`mise run lint:chart` passes on a helm-create-shaped chart skeleton, and chart tests have one render helper.

## Steps

- Write tests/test_chart_scaffold.py with the five named tests. AC4 asserts with `git ls-files chart/agent-orchestrator/templates/hpa.yaml`. Run `uv run pytest tests/test_chart_scaffold.py -q` and expect failures.
- Run `helm create` in a temp dir, copy and adapt the four files, then write ci/lint-values.yaml, tests/helm_render.py and the mise entries.
- Rerun and expect `5 passed`, then run `mise run lint` and `mise run lint:chart`.

## Notes

The template of record is `helm create` from the pinned Helm. Do not copy the infrastructure charts' layout. brief-infra section 1 shows the house test style: pytest shelling to `helm template` plus yaml asserts (charts/tests/test_<chart>_chart.py), which is reused here.

mise.toml is also edited by scaffold-repo-and-cli (earlier) and kind-e2e (later). Add entries; never rewrite the file.
