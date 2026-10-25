---
title: web chart config ingress
status: todo
repo: agents-web
value: "the chart sets the UI's backends and owns / of the host"
files: [chart/agents-web/values.yaml, chart/agents-web/templates/configmap.yaml, chart/agents-web/templates/deployment.yaml, chart/agents-web/templates/ingress.yaml, chart/agents-web/templates/tests/test-connection.yaml, chart/tests/config-ingress.test.mjs, chart/agents-web/README.md]
verify: "npm ci --no-audit --no-fund && node --test chart/tests/ && helm lint chart/agents-web --set image.tag=ci"
depends_on: [web-chart-workload]
owns: [url-layout]
uses: [web-chart, backends-config, web-image]
model: ""
estimate: 6
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

# web chart config ingress

## Requirement

Complete the agents-web chart: the runtime `config.json` from values, and the Ingress on `/` (design D2, D3, D7). Paths are in code/agents-web.

- `values.yaml`: `backends` (default `[{id: orchestrator, label: Orchestrator, basePath: /api/v1}]`); `ingress {enabled: false, className, annotations, denySourceRanges, allowSourceRanges, hosts: [{host, paths: [{path: /, pathType: Prefix}]}], tls}`.
- `templates/configmap.yaml`: `<fullname>-config` with key `config.json` = `{"backends": <values.backends>}` as JSON. The render fails naming the entry when a backend lacks `id`, `label` or `basePath`, when `basePath` does not start with `/`, or when no backend has id `orchestrator` (same rules as `src/config/backends.ts:parseConfig`).
- `templates/deployment.yaml`: mounts that key at `/usr/share/nginx/html/config.json` (`subPath`, read-only) and carries a `checksum/config` pod annotation so a backends change rolls the pod.
- `templates/ingress.yaml`: same shape as agent-orchestrator's `templates/ingress.yaml` (hosts[].paths[] to this Service's port, annotations, `denySourceRanges` to `nginx.ingress.kubernetes.io/denylist-source-range`, `allowSourceRanges` to the whitelist annotation, tls).
- `templates/tests/test-connection.yaml`: a helm test pod that GETs `/healthz` and `/config.json` on the Service.
- `chart/tests/config-ingress.test.mjs`: config.json content for the default and a two-backend value; each refusal; the mount, the checksum changing with `backends`; the Ingress rendered only when enabled, with paths, tls and the deny annotation.
- `chart/agents-web/README.md`: values reference, the URL layout rule (contract `agents-web-url-layout`: one host; the UI owns `/`; agent-orchestrator owns `/api`; each later service owns one prefix `/<prefix>/` with its UI-facing API at `/<prefix>/api/v1`, reserved `webhooks` and `schedules`; only one Ingress of the host carries the cert-manager annotations, the others reference the same TLS secret).

## Acceptance conditions

- AC1: config.json, its refusals, the mount, the checksum and the Ingress render as required [evidence: command:node --test chart/tests/config-ingress.test.mjs]
- AC2: the workload tests still pass and the chart lints [evidence: command:node --test chart/tests/ && helm lint chart/agents-web --set image.tag=ci]
- AC3: the chart README states the URL layout rule [evidence: doc-section:chart/agents-web/README.md#URL layout]

## Files

- `chart/agents-web/values.yaml`
- `chart/agents-web/templates/configmap.yaml`
- `chart/agents-web/templates/deployment.yaml`
- `chart/agents-web/templates/ingress.yaml`
- `chart/agents-web/templates/tests/test-connection.yaml`
- `chart/tests/config-ingress.test.mjs`
- `chart/agents-web/README.md`

## Interfaces

- Owns `url-layout` (contract `agents-web-url-layout`) and completes `web-chart`. Uses `backends-config` (same validation rules) and `web-image` (config path).

## Expected outcome

`helm template` with `backends` and `ingress` values gives the pod its `config.json` and an Ingress on `/` for the host.

## Steps

- Red: `chart/tests/config-ingress.test.mjs`; `node --test chart/tests/config-ingress.test.mjs` fails.
- Green: values, ConfigMap, mount and checksum, Ingress, helm test pod, README.
- `node --test chart/tests/ && helm lint chart/agents-web --set image.tag=ci`: pass.

## Notes

- Reuse agent-orchestrator `chart/agent-orchestrator/templates/ingress.yaml` (copy its shape, not a shared library chart).
- `subPath` mounts do not update in place; the checksum annotation is what rolls the pod.
