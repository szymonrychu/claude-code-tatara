# frontend decoupling design

## Summary

The web UI leaves agent-orchestrator and becomes its own TypeScript component, `agents-web` (history of `agent-orchestrator/frontend` kept), with a static nginx-unprivileged image, its own chart and CI, published to Harbor. The browser stays on one host, `lab.szymonrichert.pl`: ingress path routing sends `/` to agents-web and `/api` to the orchestrator, and every later service gets one path prefix, so everything stays same-origin (no CORS). The UI reads its backends from a runtime `config.json` rendered by its chart; a backend's menu entries appear only when it is configured. The orchestrator becomes API-only. Cutover in two live steps: agents-web plus the path split first, then the orchestrator without the UI.

## Intent and why

User request 2026-10-25: "decouple frontend from orchestrator microservice", toward more of tatara-new. The hard rule is that services talk only through the queue or HTTP; the next services (agents-webhook, agents-schedule) need UI pages without living in the orchestrator repo. Today one image builds the React app in a node stage and the api mounts it at `/` (`api/app.py:create_app`, `api/spa.py:SpaStaticFiles`).

## Goals

- G1: `code/agents-web` holds the UI with its history (created by epic agents-web-component) and builds, tests, lints and type-checks there; its types come from a vendored orchestrator OpenAPI copy with a recorded commit.
- G2: the agents-web image serves the bundle with the cache and fallback rules of `SpaStaticFiles`, plus `/healthz` and `/config.json`, and never answers an `api` path with the SPA.
- G3: the agents-web chart renders `config.json` from `backends`, a hardened Deployment, a Service on port name `http` and an Ingress; CI publishes image `harbor.szymonrichert.pl/containers/agents-web:<sha7>` and chart `0.1.0-main.<sha7>` on main.
- G4: live: `/` on `lab.szymonrichert.pl` is agents-web, `/api` the orchestrator, both behind the same SSO session; `mise run smoke` checks the UI, its config and the routing.
- G5: agent-orchestrator has no `frontend/`, no node stage, no `SpaStaticFiles`, no `ORCH_STATIC_DIR`, no npm in CI; `GET /` on the api is a JSON 404; its API stays documented and tested API-only and the kind e2e passes.
- G6: later services add a backend by a `backends` value plus registry entries in agents-web (contracts registered).

## Non-goals

- No UI feature change; no webhook or schedule UI (their epics).
- No CORS middleware, BFF, gateway, auth layer in the web app, subdomains or micro-frontends.
- No browser e2e (Playwright).
- No change to the oauth2-proxy injector or its Secret.

## Anti-goals

- A live window where `/` serves nothing: the web release and path split go live before the orchestrator stops serving the SPA (D8).
- UI changes landing in `agent-orchestrator/frontend` after the import (lost on deletion; D11).
- An absolute backend URL compiled into the bundle.
- A second Certificate for the host fighting the first (D7).

## Constraints

- Python only except web frontends (TypeScript): agents-web is the TypeScript component; its tests are vitest and node:test, its server is nginx configuration, not code.
- Order (orchestrator ruling): runs after agent-init-scripts (PR agent-orchestrator#10) and cluster-scaling have merged; it moves the frontend as it stands then, including their UI. README blockers: agent-init-scripts, cluster-scaling, agents-web-component.
- Repo creation is the one-task superrepo epic agents-web-component (`mise run component:add`, public GitHub repo, outward-facing, listed at the gate). It is separate because ticket.py refuses an epic that mixes superrepo and component tasks, and treats a task repo without a `code/<repo>` checkout as a superrepo task. After it closes, the orchestrator runs `git submodule update --init code/agents-web` in the main checkout before this epic starts.
- Headless parity (user decision): the orchestrator API stays documented and tested API-only; the kind e2e must keep passing after the split.
- Releases follow the agent-init-scripts precedent: a deploy-pin task waits, blocked, for the PR merge and main CI publish, the orchestrator writes `<sha7>` with `ticket.py amend`, then an apply-smoke task applies and smokes.
- Harbor CI secrets on the new repo are set by the user (agents cannot read secret values).
- Local testcontainers Postgres is unreliable on this machine (discovery section 1); the targeted verifies here need no database.

## Decisions

### D1: New component agents-web, history kept
The UI moves to `code/agents-web` (TypeScript), created by `workbench:component-add` with a public GitHub origin; `git subtree split --prefix=frontend` plus `git merge --allow-unrelated-histories` puts the frontend history at the repo root on top of the scaffold (epic agents-web-component). Alternatives: a second image from the same repo (fails the Why: webhook and schedule UI would live in the orchestrator), a fresh copy without history (loses blame for the UI MEMORY lessons). Serves T1.

### D2: One host, ingress path routing, one prefix per service
`lab.szymonrichert.pl`: agents-web owns `/`, agent-orchestrator `/api` (its `/api/v1` unchanged), each later service one prefix `/<prefix>/` with its UI-facing API at `/<prefix>/api/v1` (reserved `webhooks`, `schedules`). One Ingress per chart; ingress-nginx merges them by path, longest prefix wins. Same origin, so no CORS and `ORCH_ALLOWED_ORIGINS` stays `https://lab.szymonrichert.pl`. Alternative: a subdomain per service (needs CORS, cross-origin WebSocket Origin lists and cross-subdomain cookies). Contract `agents-web-url-layout`. Serves U2.

### D3: Runtime config.json and a backend registry
The bundle fetches `/config.json` (`{backends: [{id, label, basePath}]}`, `orchestrator` required) before rendering; every backend URL is relative and built from its `basePath`. The chart renders the file from `backends`. Menu entries live in `src/backends/registry.ts` keyed by backend id and appear only for configured backends, ordered by slots 10 Clusters, 20 Webhooks, 30 Schedules, 40 Presets. Alternative: backends compiled into the bundle (a rebuild per environment and per new service). Contracts `agents-web-backends-config`, `agents-web-backend-registry`. Serves C3.

### D4: nginx-unprivileged static image with the SpaStaticFiles rules
Runtime stage `nginxinc/nginx-unprivileged` pinned to a version, port 8080, non-root, read-only root with `/tmp` writable: GET/HEAD only (405 otherwise), `index.html` and unknown paths no-cache with SPA fallback, `assets/*` immutable and never falling back, `config.json` no-cache, any `api` path segment a JSON 404, `/healthz`. `scripts/image-smoke.sh` proves each rule, mirroring `tests/test_spa.py`. Alternative: a small Python Starlette server reusing `SpaStaticFiles` (a Python runtime in the TypeScript repo for what is configuration). Serves N4.

### D5: Vendored OpenAPI per backend with a recorded source commit
`openapi/orchestrator.json` plus `openapi/orchestrator.source` (`agent-orchestrator <sha40>`), refreshed by `npm run sync:api -- orchestrator`; `check:api` in agents-web CI replaces the orchestrator's `test_frontend_schema_matches_openapi`. `/api/v1` is additive-only, so an older copy keeps working. Contract `agents-web-openapi-vendor`. Serves T1, H6.

### D6: SSO by one oauth2-proxy sidecar per pod sharing one Secret
The agents-web pod carries the same injector annotations as the api pod (Secret `agent-orchestrator-proxy`): same cookie name, domain and secret, so one login is valid on both. The web sidecar owns `/` and therefore the OAuth callback. Checked live by comparing both sidecars' cookie env (apply-smoke-web-cutover AC3). Alternative: a BFF holding the only sidecar (breaks the api's direct-peer `SourceAllowlist`, re-proxies SSE and WebSockets). Serves U2.

### D7: One Certificate per host (my call)
Only the agent-orchestrator Ingress keeps `cert-manager.io/cluster-issuer` and `kubernetes.io/tls-acme`; the agents-web Ingress references the same secret `agent-orchestrator-tls` without them, so cert-manager keeps one Certificate. The orchestrator's Ingress is kept as the owner because its Certificate already exists. Serves U2.

### D8: Two-step cutover, least destructive first
Step 1: deploy agents-web and move the orchestrator Ingress to `/api` while the orchestrator image still serves the SPA; apply and smoke. Step 2: pin and apply the orchestrator build without the UI; apply and smoke. The orchestrator code removal may be built in parallel; only its pin waits for step 1. Rollback of step 1 is reverting its helmfile commits and re-applying. Serves R5.

### D9: The orchestrator becomes API-only
Delete `api/spa.py`, the `/` mount, `Settings.static_dir` and `ORCH_STATIC_DIR`, `frontend/`, the node Docker stage, the `frontend` CI job and the npm steps of `test`; retirement tests on `git ls-files`; README and MEMORY amend prior D1 and D12. The kind e2e (already API-only) keeps passing. Contract `orch-ui-retired`. Serves H6.

### D10: Releases are main builds, pinned, applied and smoked
agents-web CI publishes image and chart on main like agent-orchestrator (regctl chunked push, `chart-version.sh`); agents-helmfile adds the `agents-web` release, later re-pins the orchestrator; each step is `mise run diff`, `apply`, `diff`, `smoke`. Serves R5.

### D11: frontend/ is frozen from the import until deleted
The import records `agent-orchestrator <sha40>` in agents-web `MEMORY.md`; orch-drop-frontend-build first checks `git diff --quiet <sha> HEAD -- frontend` and stops blocked with the commit list if a UI change landed in the orchestrator after the import. Serves O7.

### D12: T1 new component repo
New component repo agents-web (TypeScript, history of agent-orchestrator/frontend kept). (user decision, working answer re-asked at the gate)

### D13: U2 one host with path routing
One host lab.szymonrichert.pl with ingress path routing: UI at /, orchestrator /api, one prefix per later service. (user decision, working answer re-asked at the gate)

### D14: C3 runtime config.json
Runtime config.json listing backends, set by the chart. (user decision, working answer re-asked at the gate)

### D15: N4 nginx-unprivileged static image
nginx-unprivileged static image. (user decision, working answer re-asked at the gate)

### D16: R5 releases, pins, apply and smoke in the epic
Releases, pin bumps and the helmfile apply plus smoke are tasks of this epic, as in agent-init-scripts. (user decision)

### D17: H6 headless parity
The orchestrator API stays documented and tested API-only; the kind e2e must keep passing after the split. (user decision)

### D18: O7 order after agent-init-scripts and cluster-scaling
This epic runs after agent-init-scripts and cluster-scaling have merged and moves the frontend as it stands then, including their UI. (orchestrator ruling)

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| start-discovery | ran: discovery.md (agent-orchestrator, agents-helmfile, tatara-new, oauth2proxy-injector) | one host and path routing per chart (tatara-new `tatara-helmfile/values/tatara-chat/default.yaml`); SpaStaticFiles rules (`api/spa.py`); injector cookie sharing (`oauth2proxy-injector/webhook.go`); two-step cutover | BFF, subdomains, micro-frontends, same-repo second image (discovery section 4) |
| research-code-internal | ran inside discovery (reuse list, shared parts) | `ci.yaml:images`, `chart-publish`, `scripts/chart-version.sh`, `templates/ingress.yaml`, `smoke.sh` step 1 | none |
| research-code-external | skipped: nginx SPA serving and ingress-nginx path merging are settled practice; the risky part (cookie sharing) is checked live | none | none |
| research-papers | skipped: no algorithmic question | none | none |
| research-docs | skipped: no third-party API decision open | none | none |

## Research inputs

| Source | Entry | Lands in |
|---|---|---|
| discovery Plan inputs reuse | SpaStaticFiles cache and fallback rules | web-nginx-image |
| discovery Plan inputs reuse | openStream EventSource backoff | moved unchanged (agents-web-component); kept by web-runtime-config |
| discovery Plan inputs reuse | request and BASE | web-runtime-config |
| discovery Plan inputs reuse | terminalSocketUrl | web-runtime-config |
| discovery Plan inputs reuse | SettingsCategory menu entries | web-backend-menu |
| discovery Plan inputs reuse | ingress hosts[].paths of the orchestrator chart | deploy-pin-web (values only); web-chart-config-ingress copies the shape |
| discovery Plan inputs reuse | images job | web-ci-release |
| discovery Plan inputs reuse | chart-publish, chart-publish-tag, chart-version.sh | web-ci-release |
| discovery Plan inputs reuse | oauth2-proxy pod annotations | deploy-pin-web |
| discovery Plan inputs reuse | smoke step 1 | smoke-web-ui |
| discovery Plan inputs reuse | release pin tests | deploy-pin-web |
| discovery Plan inputs reuse | workbench:component-add | epic agents-web-component, task create-agents-web-repo |
| discovery do-not-build | CORS middleware | rejected: same origin (D2) |
| discovery do-not-build | BFF or gateway | rejected: D6 |
| discovery do-not-build | auth layer in the web app | rejected: D6 |
| discovery do-not-build | a new orchestrator chart ingress template | rejected: values only (deploy-pin-web) |
| discovery do-not-build | browser e2e | rejected: non-goal |
| discovery fix-as-ac | schema drift test reads the repo's own frontend | orch-drop-frontend-build AC4, web-openapi-vendor AC2, AC3 |
| discovery fix-as-ac | SPA served by the api | orch-drop-spa-mount AC1-AC5, orch-drop-frontend-build AC2 |
| discovery fix-as-ac | CI couples pytest to npm | orch-drop-frontend-build AC3 |
| discovery fix-as-ac | UI checked through the api port-forward | smoke-web-ui AC1 |
| discovery fix-as-ac | orchestrator Ingress owns / | deploy-pin-web AC3, AC5 |
| discovery fix-as-ac | docs claim the api serves the UI | orch-drop-spa-mount AC5, orch-drop-frontend-build AC7 |
| discovery fix-as-ac | no absolute backend URL in the bundle | web-runtime-config AC3 |
| discovery fix-as-ac | dev server proxy only for /api | web-runtime-config (vite proxy per backend), web-docs-memory AC4 |
| discovery ideas adopted | one host, path routing, one chart per service | D2 |
| discovery ideas adopted | move frontend/ with history | D1 |
| discovery ideas adopted | two-step cutover | D8 |
| discovery ideas adopted | runtime config.json listing backends | D3 |
| discovery ideas rejected | BFF, subdomains, micro-frontends, same repo | Non-goals, D2, D6 |
| discovery A1, A2 | shared SSO session, callback on the web pod | apply-smoke-web-cutover AC3, AC5 |
| discovery A3 | ingress-nginx longest prefix | smoke-web-ui AC3, AC4; apply-smoke-web-cutover AC2 |
| discovery A4 | one Certificate per host | D7; deploy-pin-web AC3 |

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 New component agents-web, history kept | web-openapi-vendor, web-docs-memory |
| D2 One host, path routing, one prefix per service | web-chart-config-ingress, deploy-pin-web, smoke-web-ui |
| D3 Runtime config.json and a backend registry | web-runtime-config, web-backend-menu, web-chart-config-ingress, deploy-pin-web |
| D4 nginx-unprivileged static image | web-nginx-image, web-chart-workload |
| D5 Vendored OpenAPI per backend | web-openapi-vendor, web-ci-release, orch-drop-frontend-build |
| D6 SSO sidecar per pod sharing one Secret | deploy-pin-web, apply-smoke-web-cutover |
| D7 One Certificate per host | deploy-pin-web, apply-smoke-web-cutover |
| D8 Two-step cutover | apply-smoke-web-cutover, deploy-pin-orch-no-spa, apply-smoke-orch-no-spa |
| D9 The orchestrator becomes API-only | orch-drop-spa-mount, orch-drop-frontend-build |
| D10 Releases are main builds, pinned, applied, smoked | web-ci-release, deploy-pin-web, apply-smoke-web-cutover, deploy-pin-orch-no-spa, apply-smoke-orch-no-spa |
| D11 frontend/ frozen from the import | orch-drop-frontend-build |
| D12 T1 new component repo | web-openapi-vendor, web-runtime-config, web-backend-menu, web-nginx-image, web-chart-workload, web-chart-config-ingress, web-ci-release, web-docs-memory |
| D13 U2 one host with path routing | web-chart-config-ingress, deploy-pin-web, smoke-web-ui, apply-smoke-web-cutover |
| D14 C3 runtime config.json | web-runtime-config, web-backend-menu, web-chart-config-ingress, deploy-pin-web |
| D15 N4 nginx-unprivileged image | web-nginx-image, web-ci-release |
| D16 R5 releases, pins, apply and smoke | web-ci-release, deploy-pin-web, apply-smoke-web-cutover, deploy-pin-orch-no-spa, apply-smoke-orch-no-spa |
| D17 H6 headless parity | orch-drop-spa-mount, orch-drop-frontend-build |
| D18 O7 order | orch-drop-frontend-build, web-openapi-vendor |

## Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| `openapi-vendor` | web-openapi-vendor | web-ci-release | `code/agents-web/scripts/sync-api.mjs` |
| `backends-config` | web-runtime-config | web-backend-menu, web-nginx-image, web-chart-config-ingress, smoke-web-ui, deploy-pin-web | `code/agents-web/src/config/backends.ts` |
| `backend-registry` | web-backend-menu | web-docs-memory | `code/agents-web/src/backends/registry.ts` |
| `web-image` | web-nginx-image | web-chart-workload, web-chart-config-ingress, web-ci-release | `code/agents-web/Dockerfile` |
| `web-chart` | web-chart-workload | web-chart-config-ingress, web-ci-release, smoke-web-ui, deploy-pin-web | `code/agents-web/chart/agents-web/values.yaml` |
| `url-layout` | web-chart-config-ingress | web-docs-memory, smoke-web-ui, deploy-pin-web | `code/agents-web/chart/agents-web/README.md` |
| `orch-no-ui` | orch-drop-frontend-build | deploy-pin-orch-no-spa | `code/agent-orchestrator/README.md` |

Cross-epic (docs/plans/contracts.json): `agents-web-repo` (owner agents-web-component), `agents-web-url-layout`, `agents-web-backends-config`, `agents-web-backend-registry`, `agents-web-openapi-vendor`, `agents-web-chart`, `agents-web-image`, `orch-ui-retired`. configuration-improvements owns `web-settings-menu-order` (Clusters first), which fits slot 10 of `agents-web-backend-registry`.

## Review focus

- `nginx/default.conf`: no `api` path ever falls back to `index.html`; assets never fall back; the 405 rule.
- `src/config/backends.ts` validation: a `basePath` can never become absolute or cross-origin.
- `values/agents-web/common.yaml`: same oauth2-proxy Secret as the api, no cert-manager annotations, node-IP deny list.
- The orchestrator diff: only deletions plus retirement tests; `/api/v1` untouched; kind e2e green.
- `.github/workflows/ci.yaml` of agents-web: pushes only on main or tags.

## Left to the builder

- Module state or a React context for the loaded config, as long as `backendBase` and `isConfigured` are the API.
- The exact nginx-unprivileged version tag (pinned, current stable).
- How `App.tsx` stores the selected menu entry (no router).
- Whether chart tests share a helper for `helm template` parsing.

## Assumptions and unknowns

- A1 (shared SSO session across pods with the same Secret): checked live by apply-smoke-web-cutover AC3 (sidecar cookie env identical) and the redirect checks; a browser login is gate question Q4.
- A2 (the callback lands on the web sidecar): follows from `/` routing; the redirect checks show both paths behind a sidecar.
- A3 (longest prefix wins in ingress-nginx): checked by the live smoke routing step.
- A4 (two annotated Ingresses would compete): avoided by D7; checked by `kubectl get certificate` in apply-smoke-web-cutover.
- U1 (an expired-session XHR redirect): unchanged behaviour, now per sidecar; not addressed here.
- Harbor accepts the new repositories `containers/agents-web` and `charts/agents-web` with the existing robot credentials: proven by the first main CI run; if refused, web-ci-release's follow-up is blocked on the user (Harbor project permissions).

## Open questions
- Q1: Topology: the UI moves to a new public GitHub component repo agents-web (TypeScript, own image, chart, CI, helmfile release) with the history of agent-orchestrator/frontend kept? [recommended: yes, public like agent-orchestrator]
- Q2: URL layout: one host lab.szymonrichert.pl with ingress path routing, UI at /, orchestrator at /api (/api/v1 unchanged), one prefix per later service (/webhooks/, /schedules/)? [recommended: yes]
- Q3: Backends: the UI reads a runtime config.json listing its backends, set by the agents-web chart, so a service's menu entries appear only when it is configured? [recommended: yes]
- Q4: Static server: the agents-web image is nginx-unprivileged with a config file (no Python server)? [recommended: yes]
- Q5: Harbor CI secrets: you run gh secret set HARBOR_USERNAME and HARBOR_PASSWORD -R szymonrychu/agents-web once the repo exists (agents cannot read the values); web-ci-release stays blocked until then? [recommended: yes]
- Q6: SSO check: after the web cutover apply you log in once at https://lab.szymonrichert.pl and confirm the cluster list loads; the run does not wait for it (the agent compares both sidecars' cookie settings itself)? [recommended: yes]
- Q7: Repo creation runs as its own one-task superrepo epic agents-web-component that blocks this epic, because ticket.py cannot mix superrepo and component tasks in one epic? [recommended: yes]

## Irreversible operations in scope

- Creating the public GitHub repo `szymonrychu/agents-web` and pushing its main (epic agents-web-component, task create-agents-web-repo): approved by name at the gate.
- Publishing images and charts to Harbor under immutable versions (web-ci-release on main; orchestrator main CI): versions are never overwritten (refuse-existing step).
- Two live `helmfile apply` runs on namespace `agents` (apply-smoke-web-cutover, apply-smoke-orch-no-spa): guarded by lint, test and the kube-context guard; rollback is reverting the helmfile commits and re-applying.
- Deleting `frontend/` from agent-orchestrator (orch-drop-frontend-build): history stays in both repos; guarded by the freeze check (D11).
