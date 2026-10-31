# frontend decoupling implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: sonnet)

### S1: orch drop spa mount

- Status: done
- Files: `src/agent_orchestrator/api/spa.py`, `src/agent_orchestrator/api/app.py`, `src/agent_orchestrator/settings.py`, `tests/test_spa.py`, `tests/test_settings.py`, `Dockerfile`, `README.md`
- Verify: `uv run pytest -q tests/test_spa.py tests/test_settings.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 9b5d3ae

#### Requirement

The orchestrator api stops serving the UI (design D9; amends prior D1 and D12). Paths are in code/agent-orchestrator. Deletion pinned by retirement tests.

- Delete `src/agent_orchestrator/api/spa.py`; `api/app.py:create_app` no longer mounts anything at `/` (drop the `SpaStaticFiles` import and the `static_dir` branch).
- `settings.py:Settings.static_dir` removed; an `ORCH_STATIC_DIR` left in an environment is ignored (settings already use `extra="ignore"`).
- `Dockerfile`: drop `ORCH_STATIC_DIR=/app/static` from the `ENV` line (the node stage goes in task orch-drop-frontend-build).
- `tests/test_spa.py` becomes the retirement test: `git ls-files src/agent_orchestrator/api/spa.py` is empty; `GET /`, `GET /index.html` and `GET /clusters/x` on the api answer 404 with the JSON error body `error.code == "not_found"`; `PATCH /api/v1/clusters/{id}` still answers 405 from the API itself.
- `tests/test_settings.py`: the `static_dir` default assertion is replaced by one proving the field is gone and `ORCH_STATIC_DIR` is ignored.
- `README.md`: remove the `ORCH_STATIC_DIR` row; `orch api` serves `/api/v1` and `/healthz`, `/readyz` only; the components table no longer says the api serves the SPA.

#### Acceptance conditions

- AC1: spa.py is no longer tracked [evidence: test:tests/test_spa.py::test_spa_module_untracked]
- AC2: GET / and client-route paths on the api answer the JSON 404 [evidence: test:tests/test_spa.py::test_root_is_json_404]
- AC3: PATCH on a cluster still answers 405 from the API [evidence: test:tests/test_spa.py::test_patch_cluster_still_405]
- AC4: static_dir is gone and ORCH_STATIC_DIR is ignored [evidence: test:tests/test_settings.py::test_static_dir_retired]
- AC5: no ORCH_STATIC_DIR in the image or README, no SPA claim in the README [evidence: command:! grep -n ORCH_STATIC_DIR Dockerfile README.md && ! grep -nE 'serves the SPA|/api/v1., the UI' README.md]
- AC6: lint passes [evidence: command:mise run lint]

#### Files

- `src/agent_orchestrator/api/spa.py`
- `src/agent_orchestrator/api/app.py`
- `src/agent_orchestrator/settings.py`
- `tests/test_spa.py`
- `tests/test_settings.py`
- `Dockerfile`
- `README.md`

#### Interfaces

- Removes `api/spa.py:SpaStaticFiles` and `Settings.static_dir` (contract `agent-orchestrator-settings-env`: `ORCH_STATIC_DIR` leaves the documented env). The `/api/v1` surface is unchanged.

#### Expected outcome

The api is API-only: `/` is a JSON 404 and the image no longer sets `ORCH_STATIC_DIR`.

#### Steps

- Red: rewrite `tests/test_spa.py` and the settings test; `uv run pytest -q tests/test_spa.py tests/test_settings.py` fails (spa.py tracked, `/` still mounted when a static dir is set).
- Green: delete the module and the mount, remove the field, the Dockerfile env and the README row.
- `uv run pytest -q tests/test_spa.py tests/test_settings.py && mise run lint`: pass. Name "deletion pinned by a retirement test" in tests.note.

#### Notes

- Retirement tests assert on `git ls-files`, never on the filesystem.
- The live orchestrator keeps serving the UI until deploy-pin-orch-no-spa; the web cutover happens first (design D8).

- 2026-10-25 done

### S2: repin web after review fixes

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-web/common.yaml`, `tests/test_web_release.py`
- Verify: `uv run pytest -q -p no:cacheprovider && uv run ruff check .`
- Verified head: c99cfdc

#### Requirement

Epic review findings (agents-web PRs #3 regctl pin, #4 chart config.json validation parity and helm test bypassing the SSO sidecar) merged as cedcbbcd72f82c6ff9ff6cb5251412cbda5a90ad and published (run 40189450653). Re-pin the agents-web release in agents-helmfile from db1f482 to cedcbbc (chart 0.1.0-main.cedcbbc and image tag), update the pin test, confirm `helm show chart` for the new version, keep every test green. The orchestrator applies live and runs the smoke; the implementer never applies.

#### Acceptance conditions

- AC1: the agents-web chart and image are pinned to cedcbbc and the pin test asserts it [evidence: command:grep -q "0.1.0-main.cedcbbc" helmfile.yaml.gotmpl && grep -q "cedcbbc" values/agents-web/common.yaml]
- AC2: the offline suite and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider && uv run ruff check .]
- AC3: applied live with no drift and a green smoke [evidence: judgement:the apply, post-apply diff and smoke last line quoted in the task notes]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-web/common.yaml`
- `tests/test_web_release.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

What is true and observable when the task is done.

#### Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.

Orchestrator notes (2026-10-25): implementer re-pinned (c99cfdc, red: `assert 'db1f482' == 'cedcbbc'`), agents-helmfile PR #19 merged (cc33dd2). Pre-apply diff: agents-web image db1f482 -> cedcbbc, new Service agents-web-test, labels. `mise run apply`: agents-web 0.1.0-main.cedcbbc deployed. Post-apply diff: `No affected releases`. `mise run smoke` last line: `smoke: OK`.

- 2026-10-25 done

- 2026-10-25 actuals: no agent records

### S3: web openapi vendor

- Status: done
- Files: `openapi/orchestrator.json`, `openapi/orchestrator.source`, `scripts/sync-api.mjs`, `scripts/sync-api.test.mjs`, `package.json`, `src/api/schema.d.ts`, `README.md`
- Verify: `npm ci --no-audit --no-fund && node --test scripts/sync-api.test.mjs && npm run check:api && npm run lint`
- Verified head: b2d2d30

#### Requirement

Vendor the orchestrator's OpenAPI document into agents-web and generate the UI types from that copy (design D5). Paths are in code/agents-web; `code/agents-web` was created by epic agents-web-component with `frontend/` of agent-orchestrator at its root.

- `openapi/orchestrator.json`: byte-identical to `openapi.json` of agent-orchestrator at the commit named in `openapi/orchestrator.source`.
- `openapi/orchestrator.source`: one line `agent-orchestrator <sha40>`.
- `scripts/sync-api.mjs` (node, no dependency), run as `npm run sync:api -- <backend-id> [--from <checkout>]`: `<backend-id>` names the vendored file (`orchestrator` maps to the agent-orchestrator repo); `--from` defaults to `../agent-orchestrator` (the workbench sibling). It refuses, exit 1 naming the path, when the source `openapi.json` has uncommitted changes in that checkout; it refuses an unknown backend id with exit 2; otherwise it copies `openapi.json` to `openapi/<id>.json`, writes `openapi/<id>.source` from `git -C <checkout> rev-parse HEAD`, and runs `gen:api`.
- `package.json` scripts: `gen:api` is `openapi-typescript openapi/orchestrator.json -o src/api/schema.d.ts`; `check:api` diffs a fresh generation from `openapi/orchestrator.json` against `src/api/schema.d.ts` (as today, temp file under `${TMPDIR:-/tmp}`); `sync:api` runs the script. No script references `../openapi.json`.
- `src/api/schema.d.ts` is regenerated and unchanged in meaning (a diff only if the vendored commit is newer than the import).
- `README.md` `## API types`: how a backend's document is vendored, the source line, and that every orchestrator route or schema change is followed by `npm run sync:api -- orchestrator` here (contract agents-web-openapi-vendor).

#### Acceptance conditions

- AC1: sync copies the document, records the source commit and refuses a dirty source or an unknown backend [evidence: command:node --test scripts/sync-api.test.mjs]
- AC2: the generated types match the vendored document [evidence: command:npm run check:api]
- AC3: the vendored copy equals agent-orchestrator openapi.json at the recorded commit [evidence: command:read -r repo sha < openapi/orchestrator.source && test "$repo" = agent-orchestrator && curl -fsSL "https://raw.githubusercontent.com/szymonrychu/agent-orchestrator/$sha/openapi.json" | diff -q - openapi/orchestrator.json]
- AC4: no script reads the old sibling path [evidence: command:! grep -n '\.\./openapi.json' package.json]
- AC5: the README documents the vendoring rule [evidence: doc-section:README.md#API types]

#### Files

- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `scripts/sync-api.mjs`
- `scripts/sync-api.test.mjs`
- `package.json`
- `src/api/schema.d.ts`
- `README.md`

#### Interfaces

- Owns contract `agents-web-openapi-vendor` (docs/plans/contracts.json): `openapi/<backend-id>.json` plus `openapi/<backend-id>.source` (`<repo> <sha40>`), `npm run sync:api -- <backend-id> [--from <checkout>]`, `npm run check:api`. Later backends (webhooks, schedules) add their id to the script's map.

#### Expected outcome

`npm run check:api` passes against the vendored copy; `npm run sync:api -- orchestrator` refreshes it from the sibling checkout and records the commit.

#### Steps

- Red: `scripts/sync-api.test.mjs` (node:test) builds a temp git repo holding an `openapi.json`, runs the script with `--from` and asserts the copy, the source line, exit 1 on a dirty file and exit 2 on an unknown id; `node --test scripts/sync-api.test.mjs` fails (no script).
- Green: write `scripts/sync-api.mjs` and the package scripts; run it once against agent-orchestrator main (`--from` the workbench `code/agent-orchestrator`, or a fresh clone of https://github.com/szymonrychu/agent-orchestrator at main).
- `npm run check:api`, `npm run lint`: pass.

#### Notes

- The script must not run `gen:api` through a shell string built from the backend id (fixed map only).
- agent-orchestrator `/api/v1` is additive-only (README Versioning), so a UI built against an older copy keeps working.

- 2026-10-25 done

### S4: web runtime config

- Status: done
- Files: `public/config.json`, `src/config/backends.ts`, `src/config/backends.test.ts`, `src/main.tsx`, `src/api/client.ts`, `src/api/terminals.ts`, `src/api/client.test.ts`, `vite.config.ts`
- Verify: `npm ci --no-audit --no-fund && npx vitest run src/config/backends.test.ts src/api/client.test.ts src/terminal/terminalSocket.test.ts && npm run lint`
- Verified head: 37e5a1b

#### Requirement

The UI reads its backends from a runtime `config.json` and every orchestrator URL follows the configured base path (design D3). Paths are in code/agents-web.

- `src/config/backends.ts`:
  - types `Backend {id, label, basePath}` and `RuntimeConfig {backends: Backend[]}`;
  - `parseConfig(json: unknown): RuntimeConfig` throws `ConfigError` with a message naming the field when: `backends` is not an array; an `id` does not match `^[a-z][a-z0-9-]*$` or repeats; a `label` is empty; a `basePath` does not start with `/`, ends with `/`, or contains `//`, `://`, `?` or `#`; no backend has id `orchestrator`. Unknown keys are ignored.
  - `loadConfig(fetchFn = fetch)`: GET `/config.json` with `cache: 'no-store'`, rejects a non-2xx answer with a `ConfigError` naming the status, parses with `parseConfig`, and makes the result current.
  - `backendBase(id)` returns the current base path of a configured backend and throws `ConfigError` for an unconfigured one; `isConfigured(id)` returns a boolean.
- `src/api/client.ts`: the orchestrator base comes from `backendBase('orchestrator')` at call time; `request`, `eventStreamUrl` and `statusStreamUrl` stay relative. Until a config is loaded (unit tests) the base is `/api/v1`.
- `src/api/terminals.ts:terminalSocketUrl`: `ws(s)://${location.host}${orchestrator base}/agents/.../attach`, still same origin.
- `src/main.tsx`: awaits `loadConfig()` before rendering `App`; on a `ConfigError` it renders a plain page with the message and makes no API call.
- `public/config.json`: `{"backends": [{"id": "orchestrator", "label": "Orchestrator", "basePath": "/api/v1"}]}` (dev server and image default; the chart replaces it).
- `vite.config.ts`: the dev server proxies the first path segment of each backend in `public/config.json` (with `ws: true`) to `AGENTS_WEB_PROXY_<ID>` (id upper-cased, `-` to `_`), default `http://localhost:8000` for `orchestrator`.
- Existing tests that assert relative `/api/v1/...` URLs keep passing unchanged; `src/api/client.test.ts` adds one case with `basePath` `/orch/api/v1` proving request, stream and socket URLs follow it.

#### Acceptance conditions

- AC1: parseConfig accepts a valid config and rejects each invalid case naming the field; loadConfig rejects a non-2xx answer [evidence: command:npx vitest run src/config/backends.test.ts]
- AC2: orchestrator request, stream and socket URLs follow the configured base path and stay relative [evidence: command:npx vitest run src/api/client.test.ts src/terminal/terminalSocket.test.ts src/chat/ChatLog.test.tsx src/files/FilesPanel.test.tsx]
- AC3: no absolute backend URL in non-test source [evidence: command:! grep -rEn "[\"'\`]https?://" src --include='*.ts' --include='*.tsx' --exclude='*.test.ts' --exclude='*.test.tsx' --exclude=schema.d.ts]
- AC4: the bundle builds and lints [evidence: command:npm run build && npm run lint]
- AC5: main.tsx renders App only after a valid config and a plain error page otherwise [evidence: judgement:reviewer reads src/main.tsx against the requirement]

#### Files

- `public/config.json`
- `src/config/backends.ts`
- `src/config/backends.test.ts`
- `src/main.tsx`
- `src/api/client.ts`
- `src/api/terminals.ts`
- `src/api/client.test.ts`
- `vite.config.ts`

#### Interfaces

- Owns `backends-config` (contract `agents-web-backends-config`): `/config.json` = `{"backends": [{"id", "label", "basePath"}]}`, rules as in the requirement; `src/config/backends.ts:parseConfig`, `loadConfig`, `backendBase`, `isConfigured`, `ConfigError`.
- Keeps `src/api/stream.ts:openStream` unchanged.

#### Expected outcome

The same bundle runs in dev, kind and live: only `/config.json` decides where each backend is, and the default keeps today's `/api/v1`.

#### Steps

- Red: `src/config/backends.test.ts` with one case per rejection, the happy path and a `loadConfig` 500; plus the `/orch/api/v1` case in `client.test.ts`; `npx vitest run src/config/backends.test.ts src/api/client.test.ts` fails.
- Green: implement `backends.ts`, wire `client.ts`, `terminals.ts`, `main.tsx`, `public/config.json`, `vite.config.ts`.
- Run the AC commands: pass.

#### Notes

- The page and every backend share one origin (design D2): no CORS and no absolute URL anywhere.
- Dev: list `http://localhost:5173` in the orchestrator's `ORCH_ALLOWED_ORIGINS` for terminal sockets (README of agent-orchestrator `## Security`).

- 2026-10-25 done

### S5: orch drop frontend build

- Status: done
- Files: `frontend`, `Dockerfile`, `.github/workflows/ci.yaml`, `tests/test_readme_api.py`, `tests/test_frontend_retired.py`, `.gitignore`, `README.md`, `MEMORY.md`
- Verify: `uv run pytest -q tests/test_frontend_retired.py tests/test_readme_api.py tests/test_images.py && uv run ruff check . && uv run ruff format --check .`
- Verified head: 2dec27b

#### Requirement

Remove the UI source and its build from agent-orchestrator; it lives in agents-web now (design D9, D11). Paths are in code/agent-orchestrator. Deletion pinned by retirement tests.

Precondition, checked first: read `<ao-sha>` from agents-web `MEMORY.md` (`curl -fsSL https://raw.githubusercontent.com/szymonrychu/agents-web/main/MEMORY.md`, the `agent-orchestrator <sha40>` import line). `git diff --quiet <ao-sha> HEAD -- frontend` must pass: no frontend change landed after the import. Otherwise end `blocked` with the `git log --oneline <ao-sha>..HEAD -- frontend` list, whoCanClear "orchestrator: port these commits to agents-web, then rerun".

- `git rm -r frontend`.
- `Dockerfile`: no node stage and no `COPY --from=frontend`; nothing under `/app/static`.
- `.github/workflows/ci.yaml`: delete the `frontend` job; the `test` job loses `actions/setup-node` and `npm ci`. Every other job unchanged.
- `tests/test_readme_api.py`: delete `test_frontend_schema_matches_openapi` (the agents-web `check:api` against its vendored copy replaces it); the README and `openapi.json` drift tests stay.
- `tests/test_frontend_retired.py`: `git ls-files frontend` is empty; the Dockerfile has no `FROM node` and no `/app/static`; the workflow has no `npm`, `setup-node` or `frontend` job.
- `.gitignore`: drop `frontend/dist/`.
- `README.md`: the opening line describes a headless `/api/v1` whose web UI is the agents-web component (link https://github.com/szymonrychu/agents-web); `## Development` has no npm step; the openapi regeneration note says "then `npm run sync:api -- orchestrator` in agents-web".
- `MEMORY.md`: a dated 2026-10-25 entry amending D1 and D12: the UI moved to agents-web at `<ao-sha>` and the api is API-only; why: services talk only through HTTP, and other services need UI entries without living in the orchestrator.
- The kind e2e (API-only) keeps passing; it builds the image without a node stage now.

#### Acceptance conditions

- AC1: frontend/ is no longer tracked [evidence: test:tests/test_frontend_retired.py::test_frontend_untracked]
- AC2: the image has no node stage and no static dir [evidence: test:tests/test_frontend_retired.py::test_dockerfile_has_no_frontend_stage]
- AC3: CI runs no npm and has no frontend job [evidence: test:tests/test_frontend_retired.py::test_ci_has_no_npm]
- AC4: the schema drift test is retired and the README and openapi drift tests pass [evidence: command:uv run pytest -q tests/test_readme_api.py && ! grep -n test_frontend_schema_matches_openapi tests/test_readme_api.py]
- AC5: the image builds and runs [evidence: command:docker build -t agent-orchestrator:no-ui . && docker run --rm agent-orchestrator:no-ui --help]
- AC6: the API-only kind e2e passes [evidence: command:mise run test:e2e]
- AC7: README and MEMORY point at agents-web [evidence: command:grep -q agents-web README.md && grep -q agents-web MEMORY.md && ! grep -n 'npm ' README.md | grep -v 'sync:api -- orchestrator']
- AC8: no frontend change landed after the import [evidence: judgement:the task notes quote the empty git diff --stat <ao-sha> HEAD -- frontend]

#### Files

- `frontend`
- `Dockerfile`
- `.github/workflows/ci.yaml`
- `tests/test_readme_api.py`
- `tests/test_frontend_retired.py`
- `.gitignore`
- `README.md`
- `MEMORY.md`

#### Interfaces

- Owns `orch-no-ui` (contract `orch-ui-retired`): agent-orchestrator has no `frontend/`; UI work targets agents-web; an orchestrator route change is followed by `npm run sync:api -- orchestrator` in agents-web. Contract `agent-orchestrator-image` keeps its name and tag scheme.

#### Expected outcome

agent-orchestrator is a Python-only repo: pytest needs no node, the image is smaller, CI has no npm, and the kind e2e is green.

#### Steps

- Check the precondition; quote the diff in the notes.
- Red: `tests/test_frontend_retired.py`; `uv run pytest -q tests/test_frontend_retired.py` fails (frontend tracked, node stage present).
- Green: `git rm -r frontend`, edit Dockerfile, ci.yaml, test_readme_api.py, .gitignore, README.md, MEMORY.md.
- `uv run pytest -q tests/test_frontend_retired.py tests/test_readme_api.py tests/test_images.py && mise run lint`: pass. Then the docker build and `mise run test:e2e`. Name "deletion pinned by a retirement test" in tests.note.

#### Notes

- Local testcontainers Postgres may fail to start on this machine (discovery brief section 1); the targeted tests here need no database. If `mise run test:e2e` fails for a local Docker reason, quote the output and the CI `e2e` job result of the pushed branch.
- `.github/` in the diff makes the review tier full.

- 2026-10-25 amended: AC7 contradicted the requirement's README note 'npm run sync:api -- orchestrator in agents-web'; the grep now allows that one note

- 2026-10-25 done

### S6: web backend menu

- Status: done
- Files: `src/backends/registry.ts`, `src/backends/registry.test.ts`, `src/App.tsx`, `src/App.test.tsx`
- Verify: `npm ci --no-audit --no-fund && npx vitest run src/backends/registry.test.ts src/App.test.tsx && npm run lint`
- Verified head: 61c1def

#### Requirement

Settings-menu entries come from a backend registry and appear only for configured backends (design D3). Paths are in code/agents-web.

- `src/backends/registry.ts`: `MenuEntry {id, label, order, backend, render(onBack): ReactNode}`; `BACKEND_MENUS: Record<string, MenuEntry[]>` keyed by backend id; `menuEntries(config: RuntimeConfig): MenuEntry[]` returns the entries of the configured backends sorted by `order`, then `label`; a configured id with no registered entries is skipped with one `console.warn` naming it.
- The orchestrator registers every settings entry the UI has at move time (Presets, `order` 40, and any entry agent-init-scripts or cluster-scaling added). Reserved order slots, documented in the file header: 10 Clusters (configuration-improvements), 20 Webhooks (agents-webhook-microservice), 30 Schedules (agents-schedule-microservice), 40 Presets.
- `src/App.tsx`: `settingsCategories` for `TopBar` are built from `menuEntries(current config)`; the main area shows the selected cluster or the selected entry's `render(() => back to cluster)`. With the default config the UI behaves as before: the Presets entry opens `PresetsPage`.
- `src/App.test.tsx`: with the default config Presets is listed and opens the presets page; a test-registered entry of a second backend is shown only when that backend is in the config.

#### Acceptance conditions

- AC1: menuEntries filters by configured backends, orders by order then label and warns once for an unregistered id [evidence: command:npx vitest run src/backends/registry.test.ts]
- AC2: App lists Presets with the default config and shows a second backend's entry only when configured [evidence: command:npx vitest run src/App.test.tsx]
- AC3: types and lint pass [evidence: command:npx tsc -b && npm run lint]

#### Files

- `src/backends/registry.ts`
- `src/backends/registry.test.ts`
- `src/App.tsx`
- `src/App.test.tsx`

#### Interfaces

- Owns `backend-registry` (contract `agents-web-backend-registry`): `src/backends/registry.ts:BACKEND_MENUS`, `menuEntries`, `MenuEntry`, the order slots. Uses `backends-config` from web-runtime-config.
- Replaces the role of contract `orch-settings-menu` (`SessionsMenu` `settingsCategories` `{id, label, onOpen}` is unchanged).

#### Expected outcome

A later service adds its UI by registering entries under its backend id; the chart's `config.json` decides whether they appear.

#### Steps

- Red: `src/backends/registry.test.ts` and the new `App.test.tsx` cases; `npx vitest run src/backends/registry.test.ts src/App.test.tsx` fails.
- Green: implement the registry, move the Presets entry into it, build `settingsCategories` from it in `App.tsx`.
- `npx tsc -b && npm run lint`: pass.

#### Notes

- No router is introduced; the existing `view` state now holds `'cluster'` or an entry id.

- 2026-10-25 done

### S7: web nginx image

- Status: done
- Files: `Dockerfile`, `.dockerignore`, `nginx/default.conf`, `scripts/image-smoke.sh`, `README.md`
- Verify: `docker build -t agents-web:smoke . && bash scripts/image-smoke.sh agents-web:smoke && shellcheck --severity=error scripts/image-smoke.sh`
- Verified head: 42dd178

#### Requirement

Ship the UI as a static image served by nginx-unprivileged, with the cache and fallback rules of agent-orchestrator `api/spa.py:SpaStaticFiles` (design D4). Paths are in code/agents-web.

- `Dockerfile`: stage `build` on `node:24-bookworm-slim` runs `npm ci` and `npm run build`; the runtime stage is `nginxinc/nginx-unprivileged` pinned to a version tag (no `latest`), copies `dist/` to `/usr/share/nginx/html` and `nginx/default.conf` to `/etc/nginx/conf.d/default.conf`, listens on 8080 and runs as the image's non-root user. No node in the runtime image.
- `.dockerignore`: `node_modules`, `dist`, `.git`, `chart`.
- `nginx/default.conf`, server on 8080, `server_tokens off`:
  - only GET and HEAD; anything else 405 with `Allow: GET, HEAD`;
  - `/healthz`: 200 `ok`;
  - `/api`, `/api/...`, and `/<segment>/api`, `/<segment>/api/...`: 404 with a JSON body, never `index.html` (another backend's path that reaches this pod is an error, not the SPA);
  - `/assets/...`: the file with `Cache-Control: public, max-age=31536000, immutable`, or 404 when missing (no fallback);
  - `/config.json`: the file with `Cache-Control: no-cache`;
  - `/`, `/index.html` and every other unknown path: `index.html` with `Cache-Control: no-cache`.
- `scripts/image-smoke.sh <image>` (bash, `set -euo pipefail`, trap removes the container, bounded waits): runs the image on a free local port, once with the default `config.json` and once with a mounted override, and checks each rule above, including that `/config.json` lists backend `orchestrator` and that the override is served. Exit 1 naming the failed case.
- `README.md` `## Image`: the serving rules and how to run the smoke.

#### Acceptance conditions

- AC1: the image builds and every serving rule holds in the image smoke [evidence: command:docker build -t agents-web:smoke . && bash scripts/image-smoke.sh agents-web:smoke]
- AC2: the smoke script is shellcheck clean [evidence: command:shellcheck --severity=error scripts/image-smoke.sh]
- AC3: the runtime image is non-root and has no node [evidence: command:test "$(docker run --rm --entrypoint id agents-web:smoke -u)" != 0 && ! docker run --rm --entrypoint sh agents-web:smoke -c 'command -v node']
- AC4: the nginx base is pinned to a version tag [evidence: command:grep -Eq '^FROM (docker.io/)?nginxinc/nginx-unprivileged:[0-9]+\.[0-9]+' Dockerfile && ! grep -q ':latest' Dockerfile]
- AC5: the smoke cases cover every case of agent-orchestrator tests/test_spa.py [evidence: judgement:reviewer maps each test_spa.py test to a smoke case]
- AC6: the README documents the image [evidence: doc-section:README.md#Image]

#### Files

- `Dockerfile`
- `.dockerignore`
- `nginx/default.conf`
- `scripts/image-smoke.sh`
- `README.md`

#### Interfaces

- Owns `web-image`: port 8080, `/healthz`, config file path `/usr/share/nginx/html/config.json`, non-root. Uses `backends-config` (the default `public/config.json`).

#### Expected outcome

`docker build` gives a small static image whose behaviour matches what the orchestrator's SPA mount did, plus `/healthz` and `/config.json`.

#### Steps

- Red: write `scripts/image-smoke.sh` first; with no Dockerfile `docker build` fails, then with a bare nginx stage the smoke fails on the cache and fallback cases.
- Green: write `nginx/default.conf` and the Dockerfile until the smoke passes.
- `shellcheck --severity=error scripts/image-smoke.sh`: clean.

#### Notes

- Reuse: agent-orchestrator `src/agent_orchestrator/api/spa.py:SpaStaticFiles` and `tests/test_spa.py` are the rule set.
- The oauth2-proxy injector renames the container port `http` to its sidecar; probes therefore use the port number 8080 (agents-helmfile `values/agent-orchestrator/common.yaml` comment).
- `readOnlyRootFilesystem` in the chart needs writable `/tmp` (pid and temp paths of nginx-unprivileged); keep every nginx temp path under `/tmp`.

- 2026-10-25 done

### S8: web chart workload

- Status: done
- Files: `chart/agents-web/Chart.yaml`, `chart/agents-web/values.yaml`, `chart/agents-web/templates/_helpers.tpl`, `chart/agents-web/templates/deployment.yaml`, `chart/agents-web/templates/service.yaml`, `chart/tests/workload.test.mjs`, `package.json`, `package-lock.json`
- Verify: `npm ci --no-audit --no-fund && node --test chart/tests/workload.test.mjs && helm lint chart/agents-web --set image.tag=ci`
- Verified head: 77a42eb

#### Requirement

Add the agents-web Helm chart's workload: Deployment and Service (design D4, D10). Paths are in code/agents-web.

- `chart/agents-web/Chart.yaml`: `apiVersion: v2`, `name: agents-web`, `version: 0.1.0`, `appVersion` set by CI.
- `chart/agents-web/values.yaml`: `image {repository: harbor.szymonrichert.pl/containers/agents-web, tag: "", pullPolicy: IfNotPresent}` (empty tag fails the render naming `image.tag`), `imagePullSecrets: []` (and `global.imagePullSecrets` honoured), `replicaCount: 1`, `podAnnotations: {}`, `podSecurityContext` and `securityContext` (non-root, no privilege escalation, all capabilities dropped, `readOnlyRootFilesystem: true` with an `emptyDir` at `/tmp`), `resources`, `livenessProbe`/`readinessProbe` (httpGet `/healthz`, port 8080 by number), `service {type: ClusterIP, port: 8080}`.
- `templates/_helpers.tpl`: name, fullname, labels, selector labels.
- `templates/deployment.yaml`: one container `web` with port `name: http, containerPort: 8080`, the probes, the security contexts and pod annotations from values.
- `templates/service.yaml`: port `service.port`, `targetPort: http` (so the oauth2-proxy sidecar, which takes the name `http`, receives the traffic when injected).
- `chart/tests/workload.test.mjs` (node:test, `helm template` output parsed with the `yaml` package): the render fails without `image.tag`; the Deployment uses the image, port name `http` 8080, numeric-port probes on `/healthz`, non-root read-only root with `/tmp` writable; pod annotations pass through; the Service targets `http`; `imagePullSecrets` from values and from `global`.
- `package.json`: devDependency `yaml`; scripts `test:chart` (`node --test chart/tests/`) and `lint:chart` (`helm lint chart/agents-web --set image.tag=ci`); `package-lock.json` updated by `npm install`.

#### Acceptance conditions

- AC1: the workload renders as required and refuses an empty image tag [evidence: command:node --test chart/tests/workload.test.mjs]
- AC2: the chart lints [evidence: command:helm lint chart/agents-web --set image.tag=ci]
- AC3: the lockfile matches package.json [evidence: command:npm ci --no-audit --no-fund]

#### Files

- `chart/agents-web/Chart.yaml`
- `chart/agents-web/values.yaml`
- `chart/agents-web/templates/_helpers.tpl`
- `chart/agents-web/templates/deployment.yaml`
- `chart/agents-web/templates/service.yaml`
- `chart/tests/workload.test.mjs`
- `package.json`
- `package-lock.json`

#### Interfaces

- Owns `web-chart` (contract `agents-web-chart`, completed by web-chart-config-ingress): values keys above. Uses `web-image` (port, `/healthz`, non-root).

#### Expected outcome

`helm template chart/agents-web --set image.tag=x` renders a hardened Deployment and Service that work with or without the oauth2-proxy sidecar.

#### Steps

- Red: `chart/tests/workload.test.mjs` with the cases above; `node --test chart/tests/workload.test.mjs` fails (no chart).
- Green: write the chart files; `npm install -D yaml`.
- `helm lint chart/agents-web --set image.tag=ci`: pass.

#### Notes

- Reuse the shape of agent-orchestrator `chart/agent-orchestrator/templates/service.yaml` and `deployment.yaml` (port name `http`, probes by number).
- The ConfigMap, the config mount and the Ingress are web-chart-config-ingress.

- 2026-10-25 done

### S9: web chart config ingress

- Status: done
- Files: `chart/agents-web/values.yaml`, `chart/agents-web/templates/configmap.yaml`, `chart/agents-web/templates/deployment.yaml`, `chart/agents-web/templates/ingress.yaml`, `chart/agents-web/templates/tests/test-connection.yaml`, `chart/tests/config-ingress.test.mjs`, `chart/agents-web/README.md`
- Verify: `npm ci --no-audit --no-fund && node --test chart/tests/ && helm lint chart/agents-web --set image.tag=ci`
- Verified head: d9aefa2

#### Requirement

Complete the agents-web chart: the runtime `config.json` from values, and the Ingress on `/` (design D2, D3, D7). Paths are in code/agents-web.

- `values.yaml`: `backends` (default `[{id: orchestrator, label: Orchestrator, basePath: /api/v1}]`); `ingress {enabled: false, className, annotations, denySourceRanges, allowSourceRanges, hosts: [{host, paths: [{path: /, pathType: Prefix}]}], tls}`.
- `templates/configmap.yaml`: `<fullname>-config` with key `config.json` = `{"backends": <values.backends>}` as JSON. The render fails naming the entry when a backend lacks `id`, `label` or `basePath`, when `basePath` does not start with `/`, or when no backend has id `orchestrator` (same rules as `src/config/backends.ts:parseConfig`).
- `templates/deployment.yaml`: mounts that key at `/usr/share/nginx/html/config.json` (`subPath`, read-only) and carries a `checksum/config` pod annotation so a backends change rolls the pod.
- `templates/ingress.yaml`: same shape as agent-orchestrator's `templates/ingress.yaml` (hosts[].paths[] to this Service's port, annotations, `denySourceRanges` to `nginx.ingress.kubernetes.io/denylist-source-range`, `allowSourceRanges` to the whitelist annotation, tls).
- `templates/tests/test-connection.yaml`: a helm test pod that GETs `/healthz` and `/config.json` on the Service.
- `chart/tests/config-ingress.test.mjs`: config.json content for the default and a two-backend value; each refusal; the mount, the checksum changing with `backends`; the Ingress rendered only when enabled, with paths, tls and the deny annotation.
- `chart/agents-web/README.md`: values reference, the URL layout rule (contract `agents-web-url-layout`: one host; the UI owns `/`; agent-orchestrator owns `/api`; each later service owns one prefix `/<prefix>/` with its UI-facing API at `/<prefix>/api/v1`, reserved `webhooks` and `schedules`; only one Ingress of the host carries the cert-manager annotations, the others reference the same TLS secret).

#### Acceptance conditions

- AC1: config.json, its refusals, the mount, the checksum and the Ingress render as required [evidence: command:node --test chart/tests/config-ingress.test.mjs]
- AC2: the workload tests still pass and the chart lints [evidence: command:node --test chart/tests/ && helm lint chart/agents-web --set image.tag=ci]
- AC3: the chart README states the URL layout rule [evidence: doc-section:chart/agents-web/README.md#URL layout]

#### Files

- `chart/agents-web/values.yaml`
- `chart/agents-web/templates/configmap.yaml`
- `chart/agents-web/templates/deployment.yaml`
- `chart/agents-web/templates/ingress.yaml`
- `chart/agents-web/templates/tests/test-connection.yaml`
- `chart/tests/config-ingress.test.mjs`
- `chart/agents-web/README.md`

#### Interfaces

- Owns `url-layout` (contract `agents-web-url-layout`) and completes `web-chart`. Uses `backends-config` (same validation rules) and `web-image` (config path).

#### Expected outcome

`helm template` with `backends` and `ingress` values gives the pod its `config.json` and an Ingress on `/` for the host.

#### Steps

- Red: `chart/tests/config-ingress.test.mjs`; `node --test chart/tests/config-ingress.test.mjs` fails.
- Green: values, ConfigMap, mount and checksum, Ingress, helm test pod, README.
- `node --test chart/tests/ && helm lint chart/agents-web --set image.tag=ci`: pass.

#### Notes

- Reuse agent-orchestrator `chart/agent-orchestrator/templates/ingress.yaml` (copy its shape, not a shared library chart).
- `subPath` mounts do not update in place; the checksum annotation is what rolls the pod.

- 2026-10-25 done

### S10: smoke web ui

- Status: done
- Files: `scripts/smoke.sh`, `tests/test_smoke_script.py`, `README.md`, `mise.toml`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_smoke_script.py tests/test_mise_tasks.py && uv run ruff check . && uv run ruff format --check . && shellcheck --severity=error scripts/smoke.sh`
- Verified head: 024e352

#### Requirement

The smoke checks the UI on the agents-web release and the path routing of the host (design D2, D8). Paths are in code/agents-helmfile.

- `scripts/smoke.sh` step 1 is split:
  - UI: without `HOST`, port-forward `svc/${WEB_RELEASE:-agents-web}` port 8080 to `127.0.0.1:${SMOKE_WEB_LOCAL_PORT:-18080}` (killed by the existing trap); `GET /` answers HTML and `GET /config.json` is JSON listing a backend `orchestrator` with `basePath` `/api/v1`. With `HOST` set, both go to `https://$HOST`.
  - API: `GET /api/v1/openapi.json` through the api port-forward as today.
  - Ingress routing, in the existing ingress query: for host `lab.szymonrichert.pl` the path `/` routes to Service `agents-web` and the path `/api` to Service `agent-orchestrator`; any other mapping fails naming it. No Ingress at all still passes (existing test).
- `tests/test_smoke_script.py`: the fake server and fake kubectl cover the web port-forward; new tests: the happy path checks the web UI and config, a non-HTML web root fails, a config without `orchestrator` fails, `/` routed to the api Service fails, `/api` missing fails. Every existing test keeps passing.
- `README.md` and the `smoke` task description in `mise.toml`: the UI is checked on agents-web.

#### Acceptance conditions

- AC1: the smoke checks the UI and its config on the agents-web Service [evidence: test:tests/test_smoke_script.py::test_ui_checked_on_web_service]
- AC2: a config without the orchestrator backend fails the smoke [evidence: test:tests/test_smoke_script.py::test_web_config_without_orchestrator_fails]
- AC3: the root path routed to the api fails the smoke [evidence: test:tests/test_smoke_script.py::test_root_path_routed_to_api_fails]
- AC4: a missing /api path fails the smoke [evidence: test:tests/test_smoke_script.py::test_api_path_missing_fails]
- AC5: the script stays strict, bounded and shellcheck clean and every smoke test passes [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_smoke_script.py tests/test_mise_tasks.py && shellcheck --severity=error scripts/smoke.sh]

#### Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `README.md`
- `mise.toml`

#### Interfaces

- Uses `web-chart` (Service `agents-web`, port 8080), `backends-config` (`config.json`) and `url-layout` (`/` to agents-web, `/api` to agent-orchestrator).

#### Expected outcome

`mise run smoke` proves the split: UI from agents-web, API from the orchestrator, and the host's path routing.

#### Steps

- Red: the new tests in `tests/test_smoke_script.py`; `uv run pytest -q tests/test_smoke_script.py` fails.
- Green: edit `scripts/smoke.sh`, README, `mise.toml` description.
- Run the AC5 command: pass.

#### Notes

- Keep the script's existing guarantees: `set -euo pipefail`, bounded curls, trap cleanup of both port-forwards (`test_script_is_strict_bounded_and_traps`).
- This smoke runs live only after deploy-pin-web; before that the host still routes `/` to the api.

- 2026-10-25 done

### S11: web ci release

- Status: done
- Files: `.github/workflows/ci.yaml`, `scripts/chart-version.sh`, `scripts/ci.test.mjs`, `.mise.toml`, `README.md`
- Verify: `npm ci --no-audit --no-fund && node --test scripts/ci.test.mjs && shellcheck --severity=error scripts/*.sh`
- Verified head: d071d6e

#### Requirement

GitHub Actions CI for agents-web that tests everything and publishes the image and chart to Harbor like agent-orchestrator (design D10). Paths are in code/agents-web.

Precondition, checked first: `gh secret list -R szymonrychu/agents-web` lists `HARBOR_USERNAME` and `HARBOR_PASSWORD` (set by the user, gate question). Otherwise write the workflow and tests anyway, then end `blocked` with whoCanClear "user: gh secret set HARBOR_USERNAME and HARBOR_PASSWORD -R szymonrychu/agents-web".

- `.github/workflows/ci.yaml`, on push to main, tags `v*` and pull requests:
  - `web`: setup-node 24 with npm cache, `npm ci`, `npm run lint`, `npm test`, `npm run build`, `npm run check:api`;
  - `images`: `docker build -t agents-web:ci .`, `bash scripts/image-smoke.sh agents-web:ci`, and on main only the regctl chunked push (50 MB chunks, the Cloudflare 413 limit) to `harbor.szymonrichert.pl/containers/agents-web:<sha7>`;
  - `chart`: mise, `mise run lint:chart`, `mise run test:chart`;
  - `chart-publish` (needs chart and images, main only): version from `scripts/chart-version.sh branch`, refuses an existing version, `helm package --version <v> --app-version <sha7>`, push to `oci://harbor.szymonrichert.pl/charts`;
  - `chart-publish-tag` (tags only): version from `scripts/chart-version.sh tag`, refuses an existing version, requires the image `<sha7>` in Harbor, package and push.
- `scripts/chart-version.sh`: copied from agent-orchestrator with the chart path `chart/agents-web` (`branch <ref> <sha>` gives `<Chart.version>-main.<sha7>` on main; `tag v<X.Y.Z> <sha>` gives `X.Y.Z` and refuses a tag that differs from Chart.yaml).
- `.mise.toml`: tools `node` (kept), `helm` and `shellcheck` pinned; tasks `test:chart` (`npm run test:chart`), `lint:chart` (`npm run lint:chart`), `smoke:image` (`docker build -t agents-web:smoke . && bash scripts/image-smoke.sh agents-web:smoke`); `lint` also runs shellcheck on `scripts/*.sh`.
- `scripts/ci.test.mjs` (node:test, parses the workflow with `yaml`): the triggers, the five jobs and their steps above, pushes only on main or tags, the chunk size, and `chart-version.sh` cases (main, tag, mismatched tag).
- `README.md` `## Release`: what main and a tag publish, and the Harbor secrets the repo needs.

#### Acceptance conditions

- AC1: the workflow and the version script behave as required [evidence: command:node --test scripts/ci.test.mjs]
- AC2: the chart tasks and shellcheck run through mise [evidence: command:mise run lint:chart && mise run test:chart && shellcheck --severity=error scripts/*.sh]
- AC3: the repo has the Harbor secrets CI pushes with [evidence: command:test "$(gh secret list -R szymonrychu/agents-web | grep -cE '^HARBOR_(USERNAME|PASSWORD)\b')" = 2]
- AC4: the README documents the release [evidence: doc-section:README.md#Release]

#### Files

- `.github/workflows/ci.yaml`
- `scripts/chart-version.sh`
- `scripts/ci.test.mjs`
- `.mise.toml`
- `README.md`

#### Interfaces

- Owns contract `agents-web-image` (`harbor.szymonrichert.pl/containers/agents-web:<sha7>` on main) and publishes `agents-web-chart` (`oci://harbor.szymonrichert.pl/charts/agents-web`, `0.1.0-main.<sha7>` on main, `X.Y.Z` on tag `vX.Y.Z`). Uses `web-image`, `web-chart`, `openapi-vendor`.

#### Expected outcome

Every PR runs lint, tests, build, check:api, the image smoke and the chart tests; a merge to main publishes the image and chart the helmfile pins.

#### Steps

- Red: `scripts/ci.test.mjs`; `node --test scripts/ci.test.mjs` fails (no workflow).
- Green: workflow, `scripts/chart-version.sh`, `.mise.toml` tasks.
- Run the AC commands; check the precondition last and end blocked if the secrets are missing.

#### Notes

- Reuse agent-orchestrator `.github/workflows/ci.yaml` jobs `images`, `chart-publish`, `chart-publish-tag` and `scripts/chart-version.sh` (Harbor robot login via the helm registry config.json, regctl chunked push).
- No kind e2e here: the UI has no browser e2e (do-not-build).

- 2026-10-25 done

### S12: web docs memory

- Status: done
- Files: `README.md`, `AGENTS.md`, `MEMORY.md`
- Verify: `grep -q '^## Runtime config' README.md && grep -q '^## Backends and menu' README.md && grep -q '^## URL layout' README.md && grep -q react-resizable-panels MEMORY.md`
- Verified head: e20b79d

#### Requirement

Document agents-web and carry its UI lessons over (design D1, D2, D3). Paths are in code/agents-web. Doc-only.

- `README.md`: what the component is (the web UI of the agents system, the only TypeScript component); `## Development` (`npm ci`, `npm run dev`, the `AGENTS_WEB_PROXY_<ID>` proxy targets, list `http://localhost:5173` in the orchestrator's `ORCH_ALLOWED_ORIGINS` for terminal sockets); `## Runtime config` (the `config.json` schema and rules, default, set by the chart's `backends`); `## Backends and menu` (how a backend registers menu entries in `src/backends/registry.ts`, the order slots 10 Clusters, 20 Webhooks, 30 Schedules, 40 Presets); `## URL layout` (the contract rule, pointing at the chart README); links to `## API types`, `## Image`, `## Release` written by the other tasks.
- `AGENTS.md`: the commands (`mise run test`, `lint`, `fmt`, `test:chart`, `lint:chart`, `smoke:image`, `npm run sync:api -- orchestrator`) and the rule that the UI calls backends only through relative paths from `config.json`.
- `MEMORY.md`: the UI lessons from agent-orchestrator `MEMORY.md` (the react-resizable-panels `Separator` flex-basis pitfall, the FilesPanel polling decision, and every other UI-only entry present at the import), each with its original date and "moved from agent-orchestrator MEMORY.md".
- `ROADMAP.md` is not touched (human-owned).

#### Acceptance conditions

- AC1: the README documents runtime config [evidence: doc-section:README.md#Runtime config]
- AC2: the README documents backends and menu [evidence: doc-section:README.md#Backends and menu]
- AC3: the README documents the URL layout [evidence: doc-section:README.md#URL layout]
- AC4: the README documents development [evidence: doc-section:README.md#Development]
- AC5: the UI lessons are in MEMORY.md [evidence: command:grep -q react-resizable-panels MEMORY.md && grep -q FilesPanel MEMORY.md && grep -q "moved from agent-orchestrator" MEMORY.md]
- AC6: AGENTS.md lists the commands [evidence: command:grep -q "sync:api" AGENTS.md && grep -q "smoke:image" AGENTS.md]

#### Files

- `README.md`
- `AGENTS.md`
- `MEMORY.md`

#### Interfaces

- Documents contracts `agents-web-backends-config`, `agents-web-backend-registry`, `agents-web-url-layout`. Uses `backend-registry`.

#### Expected outcome

A developer of a later service learns from agents-web's README alone how to add a backend, its menu entries and its path prefix.

#### Steps

- Write the sections; run the AC commands; all pass.

#### Notes

- No TDD cycle applies: doc edit exception.

- 2026-10-25 done

### S13: deploy pin web

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-web/common.yaml`, `values/agent-orchestrator/common.yaml`, `tests/test_web_release.py`, `tests/test_orchestrator_release.py`, `README.md`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_web_release.py tests/test_orchestrator_release.py -k "not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster and not test_web_release_chart" && uv run ruff check . && uv run ruff format --check .`
- Verified head: 46ef967

#### Requirement

Add the agents-web release and split the host's paths (design D2, D6, D7, D10). Paths are in code/agents-helmfile.

Precondition, checked first: the agents-web PR of this epic is merged to main and its main CI published `harbor.szymonrichert.pl/containers/agents-web:<sha7>` and chart `oci://harbor.szymonrichert.pl/charts/agents-web` `0.1.0-main.<sha7>` (`helm show chart ... --version 0.1.0-main.<sha7>` succeeds). The orchestrator writes `<sha7>` into this task with `ticket.py amend` once the PR merges; otherwise end `blocked` with whoCanClear "orchestrator: merge the agents-web PR of frontend-decoupling and wait for its main CI".

- `helmfile.yaml.gotmpl`: release `agents-web`, namespace `agents`, chart `oci://harbor.szymonrichert.pl/charts/agents-web`, version `0.1.0-main.<sha7>`, timeout 600, labels `purpose: agents`, `application: agents-web`, `<<: *default`.
- `values/agents-web/common.yaml`: `image.tag` `<sha7>`; `podAnnotations` for the oauth2-proxy webhook identical to the api's (enable, redeem-url, `secret-name: agent-orchestrator-proxy`, `secret-namespace: agents`); `backends: [{id: orchestrator, label: Orchestrator, basePath: /api/v1}]`; `ingress`: enabled, className nginx, `denySourceRanges` the same node IPs as the orchestrator, host `lab.szymonrichert.pl` path `/` Prefix, tls `agent-orchestrator-tls` for that host, and no `cert-manager.io/cluster-issuer` or `kubernetes.io/tls-acme` annotation.
- `values/agent-orchestrator/common.yaml`: the ingress path becomes `/api` (Prefix). Its cert-manager annotations, timeouts, TLS, `ORCH_ALLOWED_ORIGINS` (`https://lab.szymonrichert.pl`, unchanged: same origin) stay.
- `tests/test_web_release.py`: `test_web_pin_matches_image` (chart version and image tag carry the same `<sha7>`, read as text, offline), `test_web_behind_oauth2_proxy_with_orchestrator_secret`, `test_web_ingress_owns_root_without_cert_annotations`, `test_web_backends_list_orchestrator_api`, `test_web_release_chart` (helmfile build: chart, namespace, labels).
- `tests/test_orchestrator_release.py`: `test_orchestrator_ingress_path_is_api`; `test_ingress_lan_only_no_ingress_auth` and the others keep passing.
- `README.md`: the agents-web release and the URL layout of the host.

#### Acceptance conditions

- AC1: chart version and image tag of agents-web agree and the test runs offline [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- AC2: the web pod uses the orchestrator's oauth2-proxy secret [evidence: test:tests/test_web_release.py::test_web_behind_oauth2_proxy_with_orchestrator_secret]
- AC3: the web Ingress owns / with the shared TLS secret and no cert-manager annotation [evidence: test:tests/test_web_release.py::test_web_ingress_owns_root_without_cert_annotations]
- AC4: the web config lists the orchestrator at /api/v1 [evidence: test:tests/test_web_release.py::test_web_backends_list_orchestrator_api]
- AC5: the orchestrator Ingress serves /api only [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_ingress_path_is_api]
- AC6: the pinned chart and image exist in Harbor [evidence: judgement:the task notes quote helm show chart and docker manifest inspect for the pinned sha]
- AC7: the offline release tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_web_release.py tests/test_orchestrator_release.py -k "not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster and not test_web_release_chart" && uv run ruff check . && uv run ruff format --check .]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-web/common.yaml`
- `values/agent-orchestrator/common.yaml`
- `tests/test_web_release.py`
- `tests/test_orchestrator_release.py`
- `README.md`

#### Interfaces

- Consumes contracts `agents-web-chart` and `agents-web-image`; implements `agents-web-url-layout` and `agents-web-backends-config` for the live host.

#### Expected outcome

`helmfile diff` shows a new `agents-web` release and the orchestrator Ingress path changing from `/` to `/api`, nothing else.

#### Steps

- Check the precondition; otherwise end blocked as the requirement says.
- Red: `tests/test_web_release.py` and the new orchestrator test; they fail (no release, path `/`).
- Green: release block, values files, orchestrator path, README.
- Run the AC7 command: pass.

#### Notes

- `values/agents-web/default.secrets.yaml` is not needed (no secret values); the `default` template's `missingFileHandler: Warn` covers it, confirmed by `mise run diff` in apply-smoke-web-cutover.
- Only one Ingress per host carries cert-manager annotations (design D7), so there is one Certificate for `agent-orchestrator-tls`.

- 2026-10-25 done

### S14: apply smoke web cutover

- Status: done
- Files: `MEMORY.md`
- Verify: `mise run diff && mise run smoke`
- Verified head: 863180f

#### Requirement

Apply the agents-web release and the path split to the live `agents` namespace and prove it (design D6, D8; user-approved: releases, pin bumps and the helmfile apply plus smoke are tasks of this epic). Paths are in code/agents-helmfile. The orchestrator still serves its old SPA here; nothing reaches it on `/` any more.

- `mise run diff` first, output quoted in the notes. Expected: the new `agents-web` release (Deployment, Service, ConfigMap, Ingress) and the agent-orchestrator Ingress path `/` to `/api`; anything else stops the task `blocked` with the diff, whoCanClear "user".
- `mise run apply` (it runs lint, test and the kube-context guard; never bypass the guard or set EXPECTED_KUBE_CONTEXT).
- `mise run diff` again: exit 0.
- `mise run smoke`: exit 0, including the web UI, config and routing checks.
- Live checks, quoted in the notes: `curl -s -o /dev/null -w '%{http_code} %{redirect_url}' https://lab.szymonrichert.pl/` and `.../api/v1/meta` both answer a redirect to Keycloak (each path is behind a sidecar); the web and api pods' oauth2-proxy sidecars have the same cookie name, cookie domain and cookie secret source (the `env` of both sidecar containers compared with `kubectl get pod -o json | jq`); `kubectl -n agents get certificate` shows one Ready certificate for `agent-orchestrator-tls`.
- `MEMORY.md`: a dated line: applied agents-web `0.1.0-main.<sha7>` and the `/api` path split, smoke green (quote the smoke's last line).
- A failing apply is not retried blindly: read the helm error and report its tail. Rollback is reverting this epic's helmfile commits and re-applying.

#### Acceptance conditions

- AC1: the live namespace has no drift from the pinned helmfile [evidence: command:mise run diff]
- AC2: the smoke passes with the web UI, config and routing checks [evidence: command:mise run smoke]
- AC3: both sidecars share one cookie configuration [evidence: command:for app in agents-web agent-orchestrator; do kubectl -n agents get pod -l app.kubernetes.io/name=$app -o json | jq -c '[.items[0].spec.containers[] | select(.name | test("oauth2")) | .env[] | select(.name | test("COOKIE_(NAME|DOMAINS?|SECRET)")) | {name, v: (.value // .valueFrom)}] | sort_by(.name)'; done | uniq | test "$(wc -l)" -eq 1]
- AC4: MEMORY.md records the applied web release [evidence: command:grep -q "agents-web 0.1.0-main" MEMORY.md]
- AC5: the pre-apply diff showed only the web release and the orchestrator path change, and both public paths redirect to Keycloak [evidence: judgement:the diff and curl output quoted in the task notes]

#### Files

- `MEMORY.md`

#### Interfaces

- `mise run diff|apply|smoke` in code/agents-helmfile; the live host `lab.szymonrichert.pl`.

#### Expected outcome

The live UI is served by agents-web on `/`, the API by the orchestrator on `/api`, behind one SSO session, and the smoke is green.

#### Steps

- `mise run diff`: quote it (exit 2 means changes).
- `mise run apply`: exit 0.
- `mise run diff`: exit 0.
- `mise run smoke`: exit 0; quote its last line into MEMORY.md and the notes.
- Run the live checks and AC3.

#### Notes

- No TDD cycle applies: this task runs an apply and writes one MEMORY.md line (doc edit exception).
- If the pod label differs from `app.kubernetes.io/name`, use the charts' selector labels in AC3's command and say so in the notes.

Orchestrator notes (2026-10-25; the orchestrator runs live applies, the classifier refuses them in subagents):
- First apply at pin cb291df failed: `release agents-web failed, and has been uninstalled due to rollback-on-failure ... .spec.template.spec.imagePullSecrets: duplicate entries for key [name="regcred"]`; agent-orchestrator was not changed (stayed rev 13). Fixed at the root in agents-web PR #2 (chart dedupes pull secrets, db1f482) and re-pinned (75ecb0e).
- Pre-apply `mise run diff`: agents-web Deployment, Ingress, Service, ConfigMap agents-web-config added; agent-orchestrator Ingress changed (path / -> /api); "Affected releases are: agent-orchestrator UPDATED, agents-web UPDATED". Nothing else.
- `mise run apply`: agents-web 0.1.0-main.db1f482 deployed, agent-orchestrator 0.1.0-main.3b9926d (Ingress only). Post-apply `mise run diff`: "No affected releases".
- `curl` https://lab.szymonrichert.pl/ -> `302 https://auth.szymonrichert.pl/realms/master/protocol/openid-connect/auth?...`; /api/v1/meta -> `302 https://auth.szymonrichert.pl/...`.
- AC3 cookie comparison: 1 distinct line for both sidecars.
- `mise run smoke` (after smoke fixes 14a1d94 and the id-key fix): last line `smoke: OK`.
- User browser check (Q6): user confirmed the UI loads after login.

- 2026-10-25 done

- 2026-10-25 actuals: no agent records

### S15: deploy pin orch no spa

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agent-orchestrator/common.yaml`, `tests/test_orchestrator_release.py`
- Verify: `uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py -k "not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster and not test_web_release_chart" && uv run ruff check . && uv run ruff format --check .`
- Verified head: 13c35f9

#### Requirement

Pin agents-helmfile to the agent-orchestrator build without the UI (design D8, D10). Paths are in code/agents-helmfile.

Precondition, checked first: the agent-orchestrator PR of this epic (tasks orch-drop-spa-mount and orch-drop-frontend-build) is merged to main and its CI published chart `0.1.0-main.<sha7>` and image `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>`. The orchestrator writes `<sha7>` into this task with `ticket.py amend` once the PR merges; otherwise end `blocked` with whoCanClear "orchestrator: merge the agent-orchestrator PR of frontend-decoupling and wait for its main CI".

- `helmfile.yaml.gotmpl`: release `agent-orchestrator` chart version `0.1.0-main.<sha7>`.
- `values/agent-orchestrator/common.yaml`: `image.tag` `<sha7>`. Nothing else changes.
- `tests/test_orchestrator_release.py`: `test_orchestrator_pin_matches_image` asserts the new `<sha7>` on both.

#### Acceptance conditions

- AC1: chart version and image tag agree on the orchestrator merge sha and the test runs offline [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- AC2: the pinned chart and image exist in Harbor [evidence: judgement:the task notes quote helm show chart or docker manifest inspect for the pinned sha]
- AC3: only the orchestrator chart version and image tag change [evidence: judgement:the task diff reviewed against the requirement]
- AC4: the offline release tests and lint pass [evidence: command:uv run pytest -q -p no:cacheprovider tests/test_orchestrator_release.py tests/test_web_release.py -k "not test_release_chart_version_and_needs and not test_db_secret_matches_rendered_cnpg_cluster and not test_web_release_chart" && uv run ruff check . && uv run ruff format --check .]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

#### Interfaces

- Consumes `agent-orchestrator-chart` and `agent-orchestrator-image` at the merge of this epic; uses `orch-no-ui`.

#### Expected outcome

`helmfile diff` shows only the agent-orchestrator chart version and image tag changing.

#### Steps

- Check the precondition; otherwise end blocked.
- Red: update the pin test to the new sha; it fails on the old pins.
- Green: bump chart version and image tag; run the AC4 command: pass.

#### Notes

- Same shape as agent-init-scripts deploy-pin-init-scripts; take the sha of the orchestrator main merge that contains this epic.

- 2026-10-25 done

### S16: apply smoke orch no spa

- Status: done
- Files: `MEMORY.md`
- Verify: `mise run diff && mise run smoke`
- Verified head: 29bd7c7

#### Requirement

Apply the orchestrator without the UI to the live `agents` namespace and prove it (design D8; user-approved: releases, pin bumps and the helmfile apply plus smoke are tasks of this epic). Paths are in code/agents-helmfile.

- `mise run diff` first, quoted in the notes. Expected: only the agent-orchestrator chart version and image tag (and what the chart renders from them); anything else stops the task `blocked` with the diff, whoCanClear "user".
- `mise run apply` (lint, test and kube-context guard; never bypass it).
- `mise run diff` again: exit 0.
- `mise run smoke`: exit 0.
- Live checks, quoted in the notes: through `kubectl -n agents port-forward deploy/agent-orchestrator-api 18001:8000`, `GET /` answers 404 with a JSON body and `GET /api/v1/openapi.json` 200; `https://lab.szymonrichert.pl/` still redirects to Keycloak.
- `MEMORY.md`: a dated line: applied agent-orchestrator `0.1.0-main.<sha7>` without the UI, smoke green (quote the smoke's last line).

#### Acceptance conditions

- AC1: the live namespace has no drift from the pinned helmfile [evidence: command:mise run diff]
- AC2: the smoke passes against the API-only orchestrator and the agents-web UI [evidence: command:mise run smoke]
- AC3: MEMORY.md records the applied orchestrator release without the UI [evidence: command:grep -q "without the UI" MEMORY.md]
- AC4: the pre-apply diff showed only the orchestrator chart version and image tag, and the api answers / with a JSON 404 [evidence: judgement:the diff and curl output quoted in the task notes]

#### Files

- `MEMORY.md`

#### Interfaces

- `mise run diff|apply|smoke` in code/agents-helmfile.

#### Expected outcome

The live orchestrator is API-only and the UI keeps working from agents-web.

#### Steps

- `mise run diff`: quote it.
- `mise run apply`: exit 0.
- `mise run diff`: exit 0.
- `mise run smoke`: exit 0; quote the last line into MEMORY.md and the notes.
- The port-forward checks.

#### Notes

- No TDD cycle applies: an apply and one MEMORY.md line (doc edit exception).

Orchestrator notes (2026-10-25; the orchestrator runs live applies): pre-apply `mise run diff`, every non-label +/- line: 8x `image: ...agent-orchestrator:3b9926d` -> `:a4be86b`, plus "Changes suppressed on sensitive content of type Secret" (label bump); affected release agent-orchestrator only. `mise run apply`: agent-orchestrator 0.1.0-main.a4be86b deployed. Post-apply diff: "No affected releases". `mise run smoke` last line: `smoke: OK`. Port-forward deploy/agent-orchestrator-api 18001:8000: `GET /` -> `{"error":{"code":"not_found","message":"Not Found"}} 404`; `GET /api/v1/openapi.json` -> 200. https://lab.szymonrichert.pl/ -> 302 to auth.szymonrichert.pl (Keycloak).

- 2026-10-25 done

- 2026-10-25 actuals: no agent records

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
