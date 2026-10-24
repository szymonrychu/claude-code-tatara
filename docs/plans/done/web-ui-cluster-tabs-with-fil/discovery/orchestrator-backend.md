# Discovery: agent-orchestrator backend and chart (epics A web-ui, B presets)

Mapped at agent-orchestrator d5a7738 (research.md line numbers, from 3004ed3, are stale). Paths relative to `code/agent-orchestrator/`. No LSP tool available.

## App and routers

- `src/agent_orchestrator/api/app.py:create_app` (23-77): routers `clusters`, `messages`, `streams` (all `APIRouter(prefix="/api/v1")`) at 56-58; SPA mounted at `/` (73-74, `api/spa.py:SpaStaticFiles` 404s `api/*`); `SourceAllowlist` last (76).
- The middleware is `api/allowlist.py:SourceAllowlist`, not `AllowlistMiddleware`. Pure ASGI over `http` and `websocket` scopes; a disallowed WS peer gets `websocket.close` 1008 before accept (45-46). Reads `scope["client"]` only, never headers.
- `uvicorn[standard]` brings `websockets` 17.3 and `wsproto` (uv.lock); `httpx` 0.28.1 is a direct dep. No WS client lib (`httpx-ws`) and no WebSocket route anywhere.
- Errors: `api/errors.py` `ApiError`, `{"error":{code,message}}`; 405 maps to `bad_request`.

## Reaching wrapper pods today

- api never does: README `## Architecture` table says api "never calls wrappers or Kubernetes"; MEMORY D5 says "the api never holds wrapper tokens". Test `tests/test_api_clusters.py:test_api_never_imports_k8s_or_wrapper` (212-231) bans `agent_orchestrator.k8s|wrapper|reconciler` imports in `api/*.py`. Epic A must amend this test and MEMORY, or keep proxy code free of those imports.
- `wrapper/client.py:WrapperClient(base_url, token, http=None)`: httpx, `Authorization: Bearer`, `_url` = `{base}/v1{path}`, errors `WrapperError`/`WrapperUnreachable`. Built in `dispatcher/loop.py:_wrapper` (54-64), `ingester/loop.py:_default_factory` (245).
- Pod URL: `k8s/render.py:pod_url` = `http://<pod>.agent-<slug>.<ns>.svc.<domain>:<wrapper_port>`; stored by the reconciler in `agents.url`, plus `agents.session_id`. The api can read them via `db/agents.py:get_agent`/`list_agents` without importing k8s. `db/views.py:agent_rows` does not select url/session_id.
- Token: `tokens.py:tokens_for(settings, cluster_id).auth` (HMAC of `ORCH_MASTER_KEY`), via `Settings.require_master_key`. Chart already gives every Deployment `ORCH_MASTER_KEY` (`templates/_config.tpl:agent-orchestrator.env` 86-97, used at `deployment.yaml:56,71`).

## Settings

`settings.py:Settings(BaseSettings)`, `env_prefix="ORCH_"`, flat fields 57-124; CSV lists are `CsvList` plus `_split` validator (145); per-field `@field_validator`s. `test_settings.py:test_env_names_documented_in_readme` requires every field as `` `ORCH_X` `` in README `## Configuration` table. `ORCH_WRAPPER_PORT`, `ORCH_CLUSTER_DOMAIN`, `ORCH_MASTER_KEY` "Read by" columns need api added.

## Migrations

`db/migrate.py:run_migrations`: files `NNNN_name.sql` (`_NAME` 4 digits), sorted, each in its own transaction, recorded in `schema_migrations`, session advisory lock; `orch migrate` initContainer. Only `0001_init.sql` exists; next is `0002_*.sql`. Idempotency is by version row only, so seed with `INSERT ... ON CONFLICT DO NOTHING`. `tests/test_migrations.py:41-53` asserts `versions == ["0001"]` and a `TABLES` set; both change.

## Clusters (epic B)

- `db/clusters.py`: `Cluster` dataclass (32-41, needs preset fields), `_from_row`, `_dump`, `create(conn, slug, spec)` (71), `get`, `get_by_slug`, `list_clusters`, `count_active`, `update_spec` (105-121, only caller PATCH), `request_delete`, `set_status`, `purge`. `ClusterDeleting` used only by `update_spec`/PATCH.
- Single writer: clusters written by api; reconciler writes `status`, `observed_generation`, deletes row (README 287-300). A `presets` row needs a README writer entry (api) and `## Data model` row.
- `api/clusters.py`: `_check_spec(spec, settings, stored=None)` (82-90) = `spec.validate_spec` then `spec.fill_resource_defaults` (write-time fill); `create_cluster` POST (131-153, advisory `_CREATE_LOCK`, `max_clusters` 409, `ClusterExists` 409); `patch_cluster` (169-187). `validate_spec(..., stored)` param exists only for PATCH (spec.py:185-206).
- `spec.py`: `validate_slug` (51-55: DNS-1123, max `SLUG_MAX=40`, `orchestrator*` reserved), `ClusterSpec` (97-112, `replicas` default 1). Generated slug must fit 40 and dodge the reserved prefix.
- `api/schemas.py`: `CreateCluster` (14-18, `extra="forbid"`, `spec` defaulted), `PatchCluster` (21-24), `ClusterView` (37-46).
- PATCH removal touches `tests/test_api_clusters.py` 88-97, 110, 353-367, 452-457, 460-482; `tests/test_clusters_repo.py` 58, 72; README `### PATCH`; `frontend/src/api/client.ts` patchCluster. After removal `PATCH /clusters/{id}` returns 405 (GET/DELETE share the path); verify with SPA mount too. README API intro says "`/api/v1` is additive only ... never removed"; retiring PATCH contradicts it.

## OpenAPI and schema.d.ts

- `uv run python -m agent_orchestrator.api.openapi > openapi.json` (`api/openapi.py:export`).
- `cd frontend && npm run gen:api` (openapi-typescript); CI `npm run check:api`.
- `tests/test_readme_api.py`: `test_openapi_json_matches_app`, `test_frontend_schema_matches_openapi` (needs `frontend/node_modules`), `test_every_route_documented`/`test_no_stale_route_in_readme` (README `### \`METHOD /api/v1...\`` headings, regex GET|POST|PATCH|PUT|DELETE only, `APIRoute` only). WebSocket routes are invisible to OpenAPI and this test; document them by hand.

## README API structure

`## API` (375): intro (base path, error shape, versioning, allowlist, error codes list), one `### \`METHOD path\`` per route with body/response/errors prose, then `### Events` table. `## Security` (177) and `### Ingress` (152) hold ingress guidance; no `proxy-read-timeout` text exists yet.

## Chart

- `values.yaml`: `env: {}` is the only settings channel (any `ORCH_*` key into ConfigMap, `templates/configmap.yaml:4-8,23-25`). `ingress.annotations`, `denySourceRanges`, `allowSourceRanges` (63-77) rendered by `templates/ingress.yaml`.
- Tests: `tests/test_chart_*.py` via `tests/helm_render.py` (real helm).

## Tests and e2e

- `tests/conftest.py`: testcontainers `postgres:18-alpine` session container, migrated template DB, per-test `dsn`, `empty_dsn`, `pool`. Docker required; unavailable in this sandbox (DB tests cannot run here).
- API tests: `httpx.ASGITransport(app, client=PEER)` (`test_api_clusters.py:client_for`); no WS test client yet. `tests/fakes/fake_wrapper.py:FakeWrapper` is uvicorn on a real socket (WS capable), kept honest by `test_fake_wrapper_contract.py` against the real image (`-m integration`).
- e2e: `scripts/e2e.sh` (kind, chart with `e2e/values-kind.yaml`, `ORCH_ALLOWED_CIDRS=127.0.0.0/8`, port-forward 18080), `tests/e2e/test_e2e_kind.py` fixtures `api`, `cluster` (POST raw spec). Agent image `e2e/agent-test.Dockerfile` pins wrapper `BASE_IMAGE ...:ca2ddf3`/`WRAPPER_SHA`; pyproject dev dep pins the same SHA. Epic A needs both bumped to the wrapper release with the new APIs.

## Verify commands (mise.toml)

- `mise run lint` (`uv run ruff check . && uv run ruff format --check .`) - ran: "All checks passed!", "97 files already formatted".
- `mise run test` (`uv run pytest`, excludes integration/e2e); targeted: `uv run pytest tests/test_readme_api.py tests/test_settings.py -q` - ran: 30 passed.
- `mise run test:chart`, `mise run lint:chart`, `mise run test:integration`, `mise run test:e2e`; frontend `npm run lint && npm test && npm run build && npm run check:api`.
- No mypy: not in deps, config or CI.

## Unknowns

- Origin policy for clients sending no Origin (headless, e2e): not decidable from code.
- Whether the WS relay may use the `websockets` transitive dep or must add an explicit dep.

## Plan inputs

- A: new `api/workspace.py` (or similar) router registered in `create_app`; resolve agent via `db/agents`, token via `tokens_for`; amend `test_api_never_imports_k8s_or_wrapper` (or avoid `wrapper` import) and MEMORY D5, README Architecture row.
- A: `ORCH_ALLOWED_ORIGINS` field in `Settings` + README Configuration row + `e2e/values-kind.yaml`; WS check in or beside `SourceAllowlist`.
- A: hand-written README sections for WS routes; extend `FakeWrapper`; bump wrapper SHA in pyproject, `uv.lock`, `e2e/agent-test.Dockerfile`.
- A: README `### Ingress` timeouts (`nginx.ingress.kubernetes.io/proxy-read-timeout`/`proxy-send-timeout` via `ingress.annotations`); chart test optional.
- B: `0002_presets.sql`; `db/presets.py`; `Cluster` gains `preset_id`/`preset_name`; `CreateCluster` exactly one of `spec`/`preset_id`; slug generator within 40 chars, not `orchestrator*`.
- B: delete `patch_cluster`, `PatchCluster`, `update_spec`, `ClusterDeleting`, `validate_spec` `stored` param, listed tests; add 405 test; fix README versioning sentence; update `test_migrations` versions/TABLES.
- Both: regen `openapi.json` then `npm run gen:api`; docker needed for DB tests.
