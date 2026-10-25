# frontend-decoupling - discovery brief

Date: 2026-10-25. Scope: code/agent-orchestrator, code/agents-helmfile; prior art from
/Users/szymonri/Documents/tatara-new and the oauth2-proxy injector in
/Users/szymonri/Documents/infrastructure. Read-only except this file.

## 1. Tree state and verification commands

| Repo | Tree | CI / PRs | Verification |
|---|---|---|---|
| agent-orchestrator | `main...origin/main` clean, 918dc0a | main ci success on 918dc0a. PR #10 (agent-init-scripts) OPEN, MERGEABLE, `UNSTABLE`: lint, test, frontend, images, chart green, e2e still running | `mise run test`, `mise run lint`, `mise run test:chart`, `mise run lint:chart`, `mise run test:e2e` (kind); frontend: `npm --prefix frontend test`, `run lint`, `run build`, `run check:api`; after a route change `uv run python -m agent_orchestrator.api.openapi > openapi.json` then `npm --prefix frontend run gen:api` |
| agents-helmfile | `main...origin/main` clean, 7dcb257 | no open PRs, no CI runs | `mise run test`, `mise run lint`, `mise run diff`, `mise run apply`, `mise run smoke` |

Baseline run here (2026-10-25):
- agents-helmfile `mise run test`: `64 passed in 50.18s`; `mise run lint`: `no leaks found`.
- agent-orchestrator `mise run lint`: `127 files already formatted`; frontend `npm test`:
  `Tests 205 passed (205)`; `npm run check:api`: rc 0; `tests/test_spa.py`: `7 passed`.
- agent-orchestrator `mise run test`: `301 passed, 41 deselected, 351 errors` - every error is the
  local testcontainers Postgres (`postgres:18-alpine`) failing its readiness exec ("container ...
  is not running") within 120 s. Local Docker environment, not code: the same suite is green in
  CI on 918dc0a and on PR #10. Implementers need a working Docker Postgres or must rely on CI.
- Superrepo: `main` ahead of origin by 164, one untracked file
  (`docs/plans/todo/configuration-improvements/discovery.md`, another epic's brief).

Component docs read: agent-orchestrator `AGENTS.md`, `MEMORY.md`, `README.md`; agents-helmfile
`AGENTS.md`, `MEMORY.md`. Both AGENTS.md only point at mise test/lint/fmt.

## 2. Facts, with evidence

### Build and serving today
- One image. `Dockerfile` stage `frontend` (node:24) runs `npm ci` and `npm run build` with
  `openapi.json` copied to `/build/openapi.json`; the Python stage copies `dist` to `/app/static`
  and sets `ORCH_STATIC_DIR=/app/static`.
- `src/agent_orchestrator/api/app.py:create_app` mounts
  `api/spa.py:SpaStaticFiles` at `/` when `settings.static_dir` is a directory.
  `SpaStaticFiles.get_response`: GET/HEAD only (405 otherwise), `api/*` stays a JSON 404,
  unknown paths fall back to `index.html`, `index.html` is `no-cache`, `assets/*` is
  `public, max-age=31536000, immutable`. Pinned by `tests/test_spa.py` (7 tests).
- `settings.py:Settings.static_dir` (default ""), pinned by `tests/test_settings.py:45`.
  README `## Commands` says `orch api` serves "/api/v1, the UI"; prior design
  `docs/plans/done/agent-orchestrator/design.md` D1 says the api "serves the SPA".
- The frontend's only build-time coupling to the repo is `../openapi.json`
  (`frontend/package.json` scripts `gen:api`, `check:api`). 63 TS/TSX files, about 8000 lines
  excluding `schema.d.ts`. No other `../` import.

### API client and URLs
- `frontend/src/api/client.ts:BASE = '/api/v1'`, `request()` uses relative `fetch`; stream URLs
  `eventStreamUrl`, `statusStreamUrl` are relative; `api/stream.ts:openStream` wraps EventSource
  with backoff and `after_id` resume.
- `frontend/src/api/terminals.ts:terminalSocketUrl` builds `ws(s)://${location.host}${BASE}/...`:
  the terminal socket assumes the API is on the page's own origin.
- Tests assume relative same-origin URLs: `api/client.test.ts`, `chat/ChatLog.test.tsx`,
  `files/FilesPanel.test.tsx`, `terminal/TerminalPanel.test.tsx`, `terminal/terminalSocket.test.ts`.
- Types: `openapi-typescript` over the committed `openapi.json` into `src/api/schema.d.ts`; drift is
  checked twice: CI `frontend` job `npm run check:api`, and
  `tests/test_readme_api.py:test_frontend_schema_matches_openapi`, which runs
  `frontend/node_modules/.bin/openapi-typescript` (this is why the CI `test` job runs `npm ci`).
- Menu extension point for other services' UI: `frontend/src/layout/SessionsMenu.tsx:SettingsCategory`
  (`{id, label, onOpen}`), passed from `App.tsx` via `TopBar settingsCategories`; `App.tsx` has no
  router, a `view` state switches between cluster and presets.

### Auth, origin, source allowlist, SSE
- The api has no auth of its own. `api/allowlist.py:SourceAllowlist` admits only direct socket
  peers in `ORCH_ALLOWED_CIDRS`; forwarded headers are never read (README `## Security`, D22).
- `api/origin.py:OriginAllowlist` (WebSocket upgrades) and `require_allowed_origin` (terminal
  POST/DELETE) require the `Origin` to be in `ORCH_ALLOWED_ORIGINS`. There is no CORS middleware:
  the design relies on same origin.
- `api/allowlist.py:PortGate`: port 8000 serves everything but `/agent/v1`; port 8001 only
  `/agent/v1`, `/healthz`, `/readyz`.
- Live deployment (agents-helmfile `values/agent-orchestrator/common.yaml`): host
  `lab.szymonrichert.pl`, one Ingress path `/` (Prefix) to the api Service; Keycloak SSO by the
  oauth2-proxy admission webhook on `components.api.podAnnotations` (secret
  `agent-orchestrator-proxy`); `ORCH_ALLOWED_CIDRS: 127.0.0.1/32` (only the sidecar);
  `ORCH_ALLOWED_ORIGINS: https://lab.szymonrichert.pl`; ingress `proxy-read/send-timeout 3600` for
  SSE and the terminal socket; node-IP `denySourceRanges`.
- Injector (`infrastructure/code/containers/apps/oauth2proxy-injector/webhook.go`): per-pod sidecar
  on 4180, upstream `127.0.0.1:<port>`, fixed `OAUTH2_PROXY_COOKIE_NAME=oauth2-authorization-cookie`,
  cookie domain and cookie secret from the named Secret (`proxy-cookie-domain`,
  `proxy-cookie-secret`), `SKIP_JWT_BEARER_TOKENS=true`. Annotations: enable, port-name,
  port-number, secret-name, secret-namespace, redeem-url. No skip-auth-route annotation.

### Chart, CI, release, e2e
- Chart `chart/agent-orchestrator`, `templates/ingress.yaml` renders `hosts[].paths[]` to the api
  Service; any path layout is a values change, no template change. `templates/tests/test-connection.yaml`
  hits `/healthz` only.
- CI `.github/workflows/ci.yaml`: jobs `lint`, `test` (with `npm ci` in frontend), `frontend`
  (lint, test, build, check:api), `images` (docker build, `--help` smoke, regctl chunked push to
  `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>` on main), `chart`, `e2e` (kind),
  `chart-publish` (`<version>-main.<sha7>` via `scripts/chart-version.sh`), `chart-publish-tag`.
- kind e2e (`scripts/e2e.sh`, `tests/e2e/test_e2e_kind.py`) is API-only: port-forward to the api
  Service, no request to `/` or any UI asset. It builds the full image, so the node stage is on
  its path today. `e2e/values-kind.yaml` sets `ORCH_ALLOWED_ORIGINS` to the port-forward origin.
- agents-helmfile: release `agent-orchestrator` pinned `0.1.0-main.a5b5a75`, image tag `a5b5a75`.
  `scripts/smoke.sh` step 1 checks `${BASE}/` returns HTML and `/api/v1/openapi.json` answers,
  through a port-forward to `deploy/agent-orchestrator-api:8000`; pinned by
  `tests/test_smoke_script.py` (fake server answers `/`). `tests/test_orchestrator_release.py`
  pins ingress host, TLS secret `agent-orchestrator-tls`, annotations, CIDRs and
  `test_allowed_origins_is_ingress_host`.

### tatara-new prior art
- No web UI at all: no `package.json` in any of its 10 components. Operator, chat and memory are
  Go services, each with its own chart and Ingress on one shared host `tatara.szymonrichert.pl`
  with path routing (operator `/`, chat `/api/v1/chat`, operator-stamped memory ingresses with a
  rewrite), each validating OIDC bearer tokens itself
  (`tatara-helmfile/values/tatara-chat/default.yaml`, `values/tatara-operator/default.yaml`).
  No gateway or BFF. So the shape to copy is "one host, ingress path routing, one chart per
  service", not a UI structure.

### Overlaps with in-flight and planned epics
- agent-init-scripts (PR #10, branch `agent-init-scripts`): touches `frontend/src/App.tsx`,
  `App.test.tsx`, `api/client.ts`, `client.test.ts`, `schema.d.ts`, new
  `clusters/InitScriptsDialog.tsx`, `clusters/clusterSpecForm.ts`, `layout/TopBar.tsx`,
  `TopBar.test.tsx`, `presets/PresetForm.tsx`, `PresetForm.test.tsx`, plus `openapi.json`.
- cluster-scaling (todo, planned): tasks `scale-ui-control` (`frontend/src/chat/ScaleControl.tsx`,
  `ChatView.tsx`, `api/client.ts:scaleCluster`), `agents-strip-leaving-mark`
  (`chat/AgentsStrip.tsx`, `ChatView.tsx`), `public-scale-route` and `agent-scale-route`
  (regenerate `frontend/src/api/schema.d.ts`).
- configuration-improvements (todo): adds a Clusters entry to `SessionsMenu` and spec fields to
  `clusterSpecForm.ts` and `PresetForm.tsx`.
- agents-webhook-microservice and agents-schedule-microservice (todo): menu entries in the same UI
  (webhook "between Clusters and Presets", schedule "in the hamburger menu"), each a separate
  backend with its own DB and API.

## 3. Known, assumed, unknown

Known: everything in section 2.

Assumed (verify in the plan or live):
- A1. Pods behind the injector that share the Secret `agent-orchestrator-proxy` share one SSO
  session on `lab.szymonrichert.pl` (same cookie name, domain and secret), so a login done
  through the web pod's sidecar is accepted by the api sidecar and by later service sidecars.
- A2. The OAuth callback `proxy-redirect-url` (one per Secret) lands on whichever pod owns that
  path; with the web release on `/` the web sidecar completes the login. Needs a live check.
- A3. ingress-nginx merges several Ingress objects for one host by path; longest prefix wins
  (`/api` beats `/`).
- A4. Two Ingresses on one host each with `cert-manager.io/cluster-issuer` and the same TLS
  secretName would create two competing Certificates; only one Ingress should carry the
  cert-manager annotation, the others reference the same secret.
- A5. `/api/v1` is additive-only (README Versioning), so a UI built against an older
  `openapi.json` keeps working against a newer orchestrator.

Unknown:
- U1. Whether oauth2-proxy answers an expired-session XHR with a redirect the SPA can recover from
  (unchanged from today, but every backend sidecar now has the same behaviour).
- U2. Path prefixes the future webhook and schedule services will serve (decided here, see Q2).
- U3. noted, not doing now: the webhook receiver path must bypass SSO, and the injector has no
  skip-auth annotation (belongs to agents-webhook-microservice).

## 4. Options

| | (a) new component `agents-web` | (b) same repo, separate image and Deployment | (c) BFF / gateway in front of the backends | (d) micro-frontends, each service ships its UI |
|---|---|---|---|---|
| Shape | new TS repo: Vite app, static image, own chart, own CI | `frontend/` stays in agent-orchestrator, a second image and Deployment from the same chart | a service that serves the UI and proxies `/api/*` to each backend | a shell app loads per-service bundles at runtime |
| Meets "UI entries without living in the orchestrator" | yes | no: webhook and schedule UI would live in the orchestrator repo | yes | yes |
| Routing several backends | ingress path routing on one host, one Ingress per chart | same | BFF routing table | ingress plus a manifest |
| Auth | one oauth2-proxy sidecar per pod, shared cookie (A1) | same | BFF's sidecar only; backends see the BFF pod IP, which breaks `SourceAllowlist` (pod CIDR must be refused, README Security) | same as (a) plus cross-bundle auth |
| CORS / Origin | none needed, same origin; `ORCH_ALLOWED_ORIGINS` unchanged | same | same origin, but SSE and the terminal WebSocket must be re-proxied with 3600 s timeouts | same as (a) |
| API types | vendored `openapi/<service>.json` per backend plus a sync and check | unchanged `../openapi.json` | per backend | each service owns its types |
| kind e2e of orchestrator | unchanged (API-only), image build gets faster | unchanged | needs the BFF in kind | unchanged |
| Cost | new repo, Harbor repo, CI, chart, helmfile release | smallest | a new Python service on the hot path of every request | highest; module federation for 3 small UIs |
| Verdict | **recommended** | rejected: fails the brief's Why | rejected: breaks the direct-peer trust model and duplicates SSE/WS proxying | rejected: overkill |

Recommendation (a): a new component `agents-web` (TypeScript, the only non-Python component, as
the hard rule allows), moved from `agent-orchestrator/frontend` with its history. It ships a
static image (index `no-cache`, `assets/*` immutable, SPA fallback, `/api*` never served) and its
own chart with an Ingress on `/` and the oauth2-proxy annotations. Every backend keeps its own
chart and Ingress on the same host under its own path prefix. The browser stays same-origin, so
no CORS. The orchestrator's ingress path becomes `/api`. `agent-orchestrator` drops the node
build stage, `SpaStaticFiles`, `ORCH_STATIC_DIR`, the `frontend` CI job and the npm step of
`test`. The UI keeps relative URLs per backend, read from a small runtime `config.json` the web
chart renders, so a webhook or schedule entry appears only when that backend is configured (Q3).
Cutover order inside the epic (least destructive): deploy agents-web and split the ingress while
the orchestrator still serves the SPA, smoke, then release the orchestrator without it.

## 5. Questions for the user

- Q1. Topology: a new component repo `agents-web` (own image, chart, CI, helmfile release) or
  keep `frontend/` in agent-orchestrator with a separate image? Recommended: new repo
  `agents-web`, history preserved. Needs a new GitHub repo, a Harbor image repo and CI secrets
  (`workbench:component-add`).
- Q2. URL layout: one host `lab.szymonrichert.pl`, UI at `/`, orchestrator unchanged at
  `/api/v1`, each new service under its own native prefix (for example `/webhook/api/v1`,
  `/schedule/api/v1`), versus a subdomain per service? Recommended: one host with path prefixes.
  Subdomains need CORS, cross-origin WebSockets and cross-subdomain cookies.
- Q3. Backend list: a runtime `config.json` from the web chart's values (UI entries appear only for
  configured backends, adding one is a values change) or compiled into the bundle? Recommended:
  runtime `config.json`.
- Q4. Static server in the web image: `nginx-unprivileged` with a config file (no application
  code), or a small Python Starlette server reusing the `SpaStaticFiles` rules? Recommended:
  nginx-unprivileged. It is configuration, not a second language, and keeps a Python runtime out
  of the TypeScript repo. Choose Python if "Python only" covers servers too.
- Q5. Sequencing: decouple right after PR #10 (agent-init-scripts) merges and before
  cluster-scaling, configuration-improvements, webhook and schedule, re-targeting their planned
  `frontend/` tasks to `agents-web`? Or after cluster-scaling and configuration-improvements, so
  their plans stay as written? Recommended: right after PR #10. Every later UI change then lands
  in one place, and the cluster-scaling re-target is 2 UI tasks plus 2 schema regenerations.

## Plan inputs

reuse
- SpaStaticFiles cache and fallback rules - agent-orchestrator src/agent_orchestrator/api/spa.py:SpaStaticFiles - web image server config and its tests (the cases of tests/test_spa.py become the web image smoke)
- openStream EventSource backoff - agent-orchestrator frontend/src/api/stream.ts:openStream - moved unchanged to agents-web
- request and BASE - agent-orchestrator frontend/src/api/client.ts:request - per-backend base path in agents-web
- terminalSocketUrl - agent-orchestrator frontend/src/api/terminals.ts:terminalSocketUrl - unchanged, same origin
- SettingsCategory menu entries - agent-orchestrator frontend/src/layout/SessionsMenu.tsx:SettingsCategory - per-backend menu entries from config.json
- ingress hosts[].paths - agent-orchestrator chart/agent-orchestrator/templates/ingress.yaml - orchestrator path `/api` by values only, no chart change
- images job (build, --help smoke, regctl chunked push) - agent-orchestrator .github/workflows/ci.yaml:images - agents-web CI
- chart-publish and chart-publish-tag jobs - agent-orchestrator .github/workflows/ci.yaml:chart-publish, scripts/chart-version.sh - agents-web chart release
- oauth2-proxy pod annotations - agents-helmfile values/agent-orchestrator/common.yaml:components.api.podAnnotations - agents-web values
- smoke step 1 (UI HTML, openapi) - agents-helmfile scripts/smoke.sh - re-pointed at the web release
- release pin tests - agents-helmfile tests/test_orchestrator_release.py - pattern for an agents-web release test
- workbench:component-add - plugins/workbench skill - creates code/agents-web with origin

do-not-build
- CORS middleware - same-origin path routing on one host - section 2 Auth (no CORS today, OriginAllowlist)
- BFF or gateway service - ingress-nginx path routing per chart - tatara-new tatara-helmfile values, chart ingress.yaml
- auth layer in the web app - oauth2-proxy sidecar per pod with the shared cookie - oauth2proxy-injector webhook.go
- a new orchestrator chart ingress template - existing hosts[].paths - chart/agent-orchestrator/templates/ingress.yaml
- browser e2e (Playwright) - none exists today; vitest jsdom plus image smoke plus live smoke - frontend tests, scripts/smoke.sh

fix-as-ac
- schema drift test reads the repo's own frontend - agent-orchestrator tests/test_readme_api.py:test_frontend_schema_matches_openapi - retired with a retirement test; agents-web CI `check:api` runs against its vendored openapi copy, which records the orchestrator commit it came from
- SPA served by the api - agent-orchestrator api/app.py:create_app, api/spa.py, settings.py:static_dir, Dockerfile frontend stage and ORCH_STATIC_DIR - removed; GET `/` on the api answers 404 JSON; the image has no node stage and no /app/static; README Configuration, Commands and Images updated
- CI couples pytest to npm - agent-orchestrator .github/workflows/ci.yaml jobs `test` (npm ci) and `frontend` - both npm steps removed; `mise run test` needs no node
- UI checked through the api port-forward - agents-helmfile scripts/smoke.sh step 1 and tests/test_smoke_script.py - UI HTML checked on the agents-web Service; openapi still on the api
- orchestrator Ingress owns `/` - agents-helmfile values/agent-orchestrator/common.yaml ingress.hosts paths - `/api` Prefix; agents-web owns `/`; only one Ingress carries the cert-manager annotation, both use secret `agent-orchestrator-tls` (A4); tests/test_orchestrator_release.py updated
- docs claim the api serves the UI - agent-orchestrator README `## Commands`, `## Development`, MEMORY.md - updated, MEMORY entry with date and why amending D1/D12
- no absolute backend URL in the bundle - agents-web src/api/* - every backend URL is relative, from config.json, so the bundle runs unchanged in kind, dev and live
- dev server proxy only for /api - agent-orchestrator frontend/vite.config.ts:server.proxy - one proxy entry per configured backend; dev origin http://localhost:5173 documented for ORCH_ALLOWED_ORIGINS

ideas
- adopted: one host, ingress path routing, one chart per service - tatara-new tatara-helmfile values (operator `/`, chat `/api/v1/chat`)
- adopted: move frontend/ with history (git subtree split or filter-repo) - keeps blame for the UI MEMORY lessons (react-resizable-panels, FilesPanel polling)
- adopted: cutover in two steps, web release and ingress split first, orchestrator SPA removal second - least destructive action first (AGENTS.md rule 6)
- adopted: runtime config.json listing backends {id, label, basePath, menu position} - lets webhook and schedule add entries without rebuilding the UI (pending Q3)
- rejected: BFF - SourceAllowlist trusts the direct peer only and must refuse pod-CIDR callers (README Security, D22)
- rejected: subdomain per service - needs CORS, cross-origin WebSocket Origin lists and cross-subdomain cookies (pending Q2)
- rejected: micro-frontends / module federation - three small UIs from one team do not need independent runtime composition
- rejected: same repo, separate image - fails the brief's Why (webhook and schedule UI would live in the orchestrator)
