---
title: web chart workload
status: todo
repo: agents-web
value: the UI deploys with its own hardened chart
files: [chart/agents-web/Chart.yaml, chart/agents-web/values.yaml, chart/agents-web/templates/_helpers.tpl, chart/agents-web/templates/deployment.yaml, chart/agents-web/templates/service.yaml, chart/tests/workload.test.mjs, package.json, package-lock.json]
verify: "npm ci --no-audit --no-fund && node --test chart/tests/workload.test.mjs && helm lint chart/agents-web --set image.tag=ci"
depends_on: [web-nginx-image, web-openapi-vendor]
owns: [web-chart]
uses: [web-image]
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

# web chart workload

## Requirement

Add the agents-web Helm chart's workload: Deployment and Service (design D4, D10). Paths are in code/agents-web.

- `chart/agents-web/Chart.yaml`: `apiVersion: v2`, `name: agents-web`, `version: 0.1.0`, `appVersion` set by CI.
- `chart/agents-web/values.yaml`: `image {repository: harbor.szymonrichert.pl/containers/agents-web, tag: "", pullPolicy: IfNotPresent}` (empty tag fails the render naming `image.tag`), `imagePullSecrets: []` (and `global.imagePullSecrets` honoured), `replicaCount: 1`, `podAnnotations: {}`, `podSecurityContext` and `securityContext` (non-root, no privilege escalation, all capabilities dropped, `readOnlyRootFilesystem: true` with an `emptyDir` at `/tmp`), `resources`, `livenessProbe`/`readinessProbe` (httpGet `/healthz`, port 8080 by number), `service {type: ClusterIP, port: 8080}`.
- `templates/_helpers.tpl`: name, fullname, labels, selector labels.
- `templates/deployment.yaml`: one container `web` with port `name: http, containerPort: 8080`, the probes, the security contexts and pod annotations from values.
- `templates/service.yaml`: port `service.port`, `targetPort: http` (so the oauth2-proxy sidecar, which takes the name `http`, receives the traffic when injected).
- `chart/tests/workload.test.mjs` (node:test, `helm template` output parsed with the `yaml` package): the render fails without `image.tag`; the Deployment uses the image, port name `http` 8080, numeric-port probes on `/healthz`, non-root read-only root with `/tmp` writable; pod annotations pass through; the Service targets `http`; `imagePullSecrets` from values and from `global`.
- `package.json`: devDependency `yaml`; scripts `test:chart` (`node --test chart/tests/`) and `lint:chart` (`helm lint chart/agents-web --set image.tag=ci`); `package-lock.json` updated by `npm install`.

## Acceptance conditions

- AC1: the workload renders as required and refuses an empty image tag [evidence: command:node --test chart/tests/workload.test.mjs]
- AC2: the chart lints [evidence: command:helm lint chart/agents-web --set image.tag=ci]
- AC3: the lockfile matches package.json [evidence: command:npm ci --no-audit --no-fund]

## Files

- `chart/agents-web/Chart.yaml`
- `chart/agents-web/values.yaml`
- `chart/agents-web/templates/_helpers.tpl`
- `chart/agents-web/templates/deployment.yaml`
- `chart/agents-web/templates/service.yaml`
- `chart/tests/workload.test.mjs`
- `package.json`
- `package-lock.json`

## Interfaces

- Owns `web-chart` (contract `agents-web-chart`, completed by web-chart-config-ingress): values keys above. Uses `web-image` (port, `/healthz`, non-root).

## Expected outcome

`helm template chart/agents-web --set image.tag=x` renders a hardened Deployment and Service that work with or without the oauth2-proxy sidecar.

## Steps

- Red: `chart/tests/workload.test.mjs` with the cases above; `node --test chart/tests/workload.test.mjs` fails (no chart).
- Green: write the chart files; `npm install -D yaml`.
- `helm lint chart/agents-web --set image.tag=ci`: pass.

## Notes

- Reuse the shape of agent-orchestrator `chart/agent-orchestrator/templates/service.yaml` and `deployment.yaml` (port name `http`, probes by number).
- The ConfigMap, the config mount and the Ingress are web-chart-config-ingress.
