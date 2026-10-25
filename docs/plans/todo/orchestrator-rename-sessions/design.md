# orchestrator rename and sessions design

## Summary

agent-orchestrator becomes agents-orchestrator everywhere (GitHub repo, submodule, Python package, chart, OCI
chart, Harbor image, helm releases, Kubernetes objects, CNPG database, Secrets, docs), and the orchestrator's unit
"cluster" becomes "session" throughout: HTTP and agent APIs, DB tables and columns, Kubernetes labels, the
agents-common client, agents-webhook, any-mcp's orchestrator plugin and every web UI label and component. The
wrapper's own session id, which today owns the word "session" in the orchestrator, becomes `wrapper_session_id`.
The live namespace moves by a new release set: the old app release is uninstalled, a new CNPG cluster is imported
from the old one (which is then hibernated, never deleted), and the new releases come up under the new names. No
aliases, shims or fallbacks anywhere.

## Intent and why

User request 2026-10-25: "Agent-orchestrator 1. Rename to agents-orchestrator (consistency) 2. Nomenclature
cleanup leading to webUI fixes -> clusters == sessions". Every other component is `agents-*`; the orchestrator is
the odd one out. The UI already says "Sessions" in its menu but "New cluster", "No clusters yet" and "Message the
cluster" everywhere else, and the API, client and docs say cluster. One word for one thing, before
workspace-s3-cache and agents-schedule-microservice build more on the old names.

## Goals

- G1: no tracked file in any touched repo names `agent-orchestrator` or `agent_orchestrator` outside dated
  history (MEMORY.md, CHANGELOG.md, ROADMAP.md, docs/plans/); the GitHub repo, submodule, package, chart, image and
  releases carry `agents-orchestrator`.
- G2: no tracked file in any touched repo uses "cluster" for the orchestrator's unit; the remaining hits are
  Kubernetes, CNPG or kind clusters only, pinned by a per-repo nomenclature guard test.
- G3: the HTTP API is `/api/v1/sessions...` with `session_id` fields; the agent API takes `X-Orch-Session`; the DB
  has `sessions`, `session_leaders` and `session_id` columns.
- G4: the web UI says session in every label, title, placeholder, tooltip and empty state.
- G5: the live namespace runs the renamed releases with the presets carried over, and the smoke is green.
- G6: no live data is deleted: the old database is kept hibernated.

## Non-goals

- Deleting the old CNPG cluster, its PVCs or its S3 backups (kept; a later user decision).
- Deleting the old Harbor repositories `containers/agent-orchestrator` and `charts/agent-orchestrator`.
- Renaming the `ORCH_` env prefix, the `orch` CLI, the `X-Orch-*` header family or the `agent-<slug>` object prefix
  of session pods (they name the orchestrator and the agents, not the repo or the unit).
- Renaming the claude-code-wrapper's own `/v1/sessions` API (it is the wrapper's vocabulary).
- Amending agents-schedule-microservice and workspace-s3-cache tasks (orchestrator step after the gate, see
  Orchestrator steps).

## Anti-goals

- A compatibility alias of any kind: old routes, old header, old env name, old DB view, old label, old Secret name.
- A red main in any repo between tasks: each task keeps its repo's suite green.
- Data loss: the presets (2 live rows) must survive the move, checked by the cutover.
- Renaming Kubernetes or CNPG "cluster" terms (`cluster.local`, `ClusterIP`, `ClusterIssuer`, CNPG `Cluster`,
  `cluster:` chart key, kind cluster) by an over-eager sed.

## Constraints

- House rules: no backward compatibility; least destructive action first; every irreversible operation named at
  the gate; test first (renames are pinned by guard tests, deletions by `git ls-files` retirement tests).
- The GitHub repo rename and the submodule move are orchestrator (main session) steps, never subagents.
- Live applies (`mise run apply`) are run by the orchestrator in the main session; subagents run `mise run diff`
  and `mise run smoke` only.
- Each repo keeps its own verify commands (facts pack): `uv run pytest <files>` plus
  `uv run ruff check . && uv run ruff format --check .` for Python repos; `npx vitest run <files>`,
  `npm run lint`, `npm run check:api` for agents-web.
- Tags are never re-pointed (any-mcp, agents-common).

## Decisions

### D1: Names (the rename table)

| Thing | Old | New |
|---|---|---|
| GitHub repo | szymonrychu/agent-orchestrator | szymonrychu/agents-orchestrator (GitHub keeps redirects) |
| Submodule | code/agent-orchestrator, section `agent-orchestrator` | code/agents-orchestrator, section `agents-orchestrator` |
| Python dist / package | agent-orchestrator / agent_orchestrator | agents-orchestrator / agents_orchestrator (CLI `orch` unchanged) |
| Chart dir / name / helpers | chart/agent-orchestrator, `agent-orchestrator.*` defines | chart/agents-orchestrator, `agents-orchestrator.*` |
| OCI chart / image | charts/agent-orchestrator, containers/agent-orchestrator | charts/agents-orchestrator, containers/agents-orchestrator |
| managed-by label value | agent-orchestrator | agents-orchestrator |
| Helm releases | agent-orchestrator, agent-orchestrator-db | agents-orchestrator, agents-orchestrator-db |
| CNPG cluster / DB / owner | agent-orchestrator-db-cluster / agent_orchestrator | agents-orchestrator-db-cluster / agents_orchestrator |
| S3 backup path | /agent-orchestrator-db/ | /agents-orchestrator-db/ |
| Services | agent-orchestrator{,-agents,-services} | agents-orchestrator{,-agents,-services} |
| Chart Secrets | agent-orchestrator-{claude,master-key,services} | agents-orchestrator-{claude,master-key,services} (same SOPS values, moved file) |
| TLS Secret | agent-orchestrator-tls | agents-orchestrator-tls (cert-manager, owned by the orchestrator ingress) |
| SSO Secret / Keycloak client | agent-orchestrator-proxy / agent-orchestrator | agents-orchestrator-proxy / agents-orchestrator (user-run terraform, D9) |
| Webhook orchestrator URL | http://agent-orchestrator-services:8002 | http://agents-orchestrator-services:8002 |
| helmfile values dirs | values/agent-orchestrator{,-db}/ | values/agents-orchestrator{,-db}/ (old db dir stays while the old db is hibernated) |

### D2: Session vocabulary (the API and schema contract)

Every repo implements exactly this table; it is the cross-repo contract `orch-sessions-api` (see Contracts).

| Surface | Old | New |
|---|---|---|
| Public routes | /api/v1/clusters, /api/v1/clusters/{cluster_id}/... | /api/v1/sessions, /api/v1/sessions/{session_id}/... (every sub-route) |
| Schemas | ClusterSpec, ClusterSummary, ClusterView, CreateCluster | SessionSpec, SessionSummary, SessionView, CreateSession |
| Fields | `cluster_id` (CheckView, EventView, FileContent, FileListing, InitScriptsView, Me, MessageView, ScaleResult, TerminalView, ...) | `session_id` |
| Fields | EventView.session_id (the wrapper's) | `wrapper_session_id` |
| Fields | MetaCaps.max_clusters | `max_sessions` |
| Error codes | cluster_deleting, static_cluster, cluster_limit | session_deleting, static_session, session_limit |
| Init scripts | applies `next_cluster` | `next_session` |
| SSE / NOTIFY | cluster_status, cluster_removed, cluster_changed | session_status, session_removed, session_changed |
| Agent API | header X-Orch-Cluster, pod env ORCH_CLUSTER_ID, any-mcp plugin key `cluster` | X-Orch-Session, ORCH_SESSION_ID, `session` |
| Settings | ORCH_MAX_SESSIONS replaces ORCH_MAX_CLUSTERS; any other `*CLUSTER*` setting naming the unit likewise | ORCH_CLUSTER_DOMAIN stays (Kubernetes) |
| k8s label | agents.szymonrichert.pl/cluster | agents.szymonrichert.pl/session |
| DB tables | clusters, cluster_leaders | sessions, session_leaders |
| DB columns | `cluster_id` everywhere; agents.session_id, agents.session_created_at, events.session_id | `session_id`; wrapper_session_id, wrapper_session_created_at, wrapper_session_id |
| DB indexes/constraints | names containing `cluster` or the wrapper `session` | renamed to match the new column and table names |
| Python | Cluster, ClusterTokens, render_cluster, list_clusters, cluster_max_attempts, db/clusters.py, ... | Session, SessionTokens, render_session, list_sessions, session_max_attempts, db/sessions.py, ... |
| agents-common | Cluster, create_cluster, get_cluster, running_cluster, RunRef.cluster_id, set_cluster, discard_cluster, remove_cluster, reason cluster_not_found | Session, create_session, get_session, running_session, RunRef.session_id, set_session, discard_session, remove_session, session_not_found |
| agents-webhook | events.cluster_id, cluster_slug; EventView/EventDetail fields; reason cluster_not_found | session_id, session_slug; same fields; session_not_found |
| agents-web | src/clusters/, ClustersPage, NewClusterDialog, DiscardClusterDialog, clusterSpecForm, useClusters, useClusterChat, menu entry `clusters`/"Clusters", every visible "cluster" | src/sessions/, SessionsPage, NewSessionDialog, DiscardSessionDialog, sessionSpecForm, useSessions, useSessionChat, entry `sessions`/"Sessions", "session" |

Alternatives: keep "cluster" internally and rename only the UI (rejected: the user said throughout); rename to
"session" without disambiguating the wrapper's session (rejected: `agents.session_id` would read as a foreign key
to `sessions`, D3).

### D3: The wrapper's session id becomes wrapper_session_id (my call)

The orchestrator stores the claude-code-wrapper's session id in `agents.session_id`, `agents.session_created_at`
and `events.session_id`, and exposes it as EventView.session_id. Once the unit is called session, these collide
with `session_id` the foreign key. They become `wrapper_session_*` in the DB, the code and the API, in their own
migration and task before the unit rename. The `wrapper/` client module keeps the wrapper's own vocabulary
(`/v1/sessions`). Alternative: `ccw_session_id` (rejected: "wrapper" is the word the code already uses).

### D4: DB-level rename by forward migrations

Two new forward-only migrations in agents-orchestrator: `0004_wrapper_session_id.sql` (D3) and
`0005_sessions.sql` (tables, columns, indexes, FK and unique constraint names). `ALTER ... RENAME` keeps every row
and is transactional (the runner applies each file in one transaction). agents-webhook gets
`0005_sessions.sql` renaming `events.cluster_id`/`cluster_slug` (0005, not 0004: webhook-event-filters owns 0004;
the runner applies any unapplied version, so the order of landing does not matter). Alternative: keep DB names and
map in code (rejected: two vocabularies forever). Gate question Q1.

### D5: Live database path: new CNPG cluster imported from the old one

A release rename is a new release, so `agents-orchestrator-db` is a new CNPG cluster bootstrapped with the cnpg
chart's `mode: recovery`, `recovery.method: import`, `import.type: microservice` from database `agent_orchestrator`
on `agent-orchestrator-db-cluster-rw` (user `agent_orchestrator`, password from Secret
`agent-orchestrator-db-cluster-app` key `password`, `sslMode: verify-full` against
`agent-orchestrator-db-cluster-ca` key `ca.crt`), into database `agents_orchestrator` owned by
`agents_orchestrator`, with its own S3 backup path `/agents-orchestrator-db/`. The import runs after the old app is
uninstalled, so the copy is consistent. The new app's migrate initContainer then applies 0004 and 0005 to the copy;
the old database is never migrated and stays the rollback point.

Options with risk:

| Option | Risk | Verdict |
|---|---|---|
| A: import into a new cluster (chosen) | import failure leaves the old DB untouched; minutes of downtime | recommended |
| B: keep `agent-orchestrator-db` release, Cluster and DB names | zero data movement, but the old names stay forever (fails G1) | rejected |
| C: recover the new cluster from the old cluster's S3 backup | depends on the last backup (daily), may miss writes; DB name stays `agent_orchestrator` | rejected |
| D: pg_basebackup | physical copy keeps DB name and owner `agent_orchestrator` | rejected |

Live facts (probe 2026-10-25, read-only): 0 sessions (clusters table empty), 0 messages, 0 events, 2 presets,
schema_migrations 0001-0003, no agent StatefulSets, no PrometheusRule, ServiceMonitor or Grafana dashboard for the
orchestrator. Gate question Q2.

### D6: Old database is hibernated, not deleted

After the smoke is green, the old cluster gets the CNPG declarative hibernation annotation
`cnpg.io/hibernation: "on"` through `cluster.annotations` in `values/agent-orchestrator-db/common.yaml` and its
scheduled backups are dropped: pods stop, PVCs and existing S3 backups stay, and removing the annotation brings it
back. The release `agent-orchestrator-db` and its values dir stay declared (the only allowed old names, listed in
the guard allowlist with a comment). Deleting it is a later user decision. Gate question Q3.

### D7: Cutover sequence (helmfile, orchestrator-run applies)

The final helmfile state declares: `agent-orchestrator` with `installed: false`; `agent-orchestrator-db` (old,
installed); `agents-orchestrator-db` (import); `agents-orchestrator`; agents-webhook and agents-web on the new names.
The orchestrator applies it in three selector-scoped steps so ordering never depends on helmfile internals and the
two ingresses never claim `lab.szymonrichert.pl/api` at once (ingress-nginx refuses a duplicate host and path):

1. Precondition probes: no session rows with `desired = 'active'` in the old DB, Secret
   `agents-orchestrator-proxy` exists (U1), the pinned charts exist in Harbor.
2. `mise run apply -- --selector name=agent-orchestrator`: uninstalls the old app (downtime starts; the DB is now
   quiescent).
3. `mise run apply -- --selector name=agents-orchestrator-db`: the import; wait until the Cluster is healthy and
   `select count(*) from presets` equals the old count.
4. `mise run apply`: the new app (migrate applies 0004, 0005), agents-webhook (migrate 0005, new URL) and
   agents-web; then `mise run diff` shows no drift and `mise run smoke` is green.
5. Once Certificate `agents-orchestrator-tls` is Ready, the orchestrator deletes the orphan Secret
   `agent-orchestrator-tls` (the old Certificate went with the old Ingress).

Rollback before step 4 completes: set `agent-orchestrator` back to installed with the previous pins (the old DB is
untouched). Known window: `/api` and the webhook worker's orchestrator calls fail between steps 2 and 4; the worker
already treats an unreachable orchestrator as retryable (`OrchestratorUnavailable`).

### D8: No relabel migration for Kubernetes objects

The label key, managed-by value and Service names change, and StatefulSet selectors are immutable, so live session
objects would be orphaned. There are none (D5 probe), and the cutover precondition refuses to proceed while any
session is active. No relabel code is written.

### D9: SSO Secret and Keycloak client (user-run, outside the workbench)

`agent-orchestrator-proxy` is written by the infrastructure repo's terraform
(`/Users/szymonri/Documents/infrastructure/code/terraform/keycloak/keycloak_clients.tf`, map `agents`, key
`agent-orchestrator`, pinned by its `tests/test_keycloak_agents_clients.py`), outside this workbench. U1 (user,
before the cutover): add key `agents-orchestrator = { url = "lab.szymonrichert.pl" }` next to the old one and apply,
creating Secret `agents-orchestrator-proxy`. U2 (user, after the smoke): remove the old key and apply, deleting the
old Keycloak client and Secret. Two steps, so SSO never breaks. Gate question Q4.

### D10: ORCH_ prefix and other kept names (my call)

`ORCH_`, `orch`, `X-Orch-*`, the `orch:` localStorage prefix, the advisory lock key and the `agent-<slug>` object
prefix stay: they abbreviate the orchestrator or name the agents, not the repo or the unit. Gate question Q5 for
the prefix only.

### D11: Releases and pins

- any-mcp v0.3.0 (plugin `session` key and `X-Orch-Session`), tagged by the orchestrator after its PR merges;
  agents-orchestrator pins it (pyproject, uv.lock, `any_mcp_ref` default, helmfile `ORCH_ANY_MCP_REF`).
- agents-common v0.3.0 (session client), tagged likewise; agents-webhook pins it.
- agents-orchestrator, agents-webhook and agents-web publish `0.1.0-main.<sha7>` builds from main as today; the
  helmfile tasks pin them after the orchestrator merges each PR and writes the sha with `ticket.py amend`.
- Harbor creates `containers/agents-orchestrator` and `charts/agents-orchestrator` on the first push (same project).

### D12: Nomenclature guard tests

Each touched repo gets `tests/test_nomenclature.py` (agents-web: `src/nomenclature.test.ts`) that runs
`git ls-files` over a list of guarded paths and fails on any line matching `/cluster/i` or
`agent[-_]orchestrator` that is not covered by an allowlist of literal phrases naming Kubernetes, CNPG or kind
clusters (`cluster.local`, `ClusterIP`, `clusterIP`, `ClusterIssuer`, `cluster-issuer`, `ClusterRole`,
`in-cluster`, `cluster-internal`, `cluster node`, `cluster-info`, CNPG `Cluster` kind and `cluster:` values key,
`db-cluster`, kind cluster names) or the dated-history files (MEMORY.md, CHANGELOG.md, ROADMAP.md, docs/plans/).
The rename tasks of a repo extend the guarded path list one area at a time (red first), the last one guards the
whole repo. Retired paths are pinned with `git ls-files <path>` returning nothing.

### D13: Superrepo and other epics (orchestrator steps)

Mapped to orch-package-rename, the first task that needs O2 done; O3 runs after the epic. O2 regenerates the superrepo's `.mise.toml`, AGENTS.md project block and docs/architecture.md with
`mise run init:refresh` after the submodule move. O3 amends agents-schedule-microservice tasks (orchestrator URL,
routes, client names, Secret names, contract names) and records workspace-s3-cache's new names with
`ticket.py amend` once this epic's names are merged.

### D14: Ordering against webhook-event-filters (my call)

Both epics touch agents-webhook (events store, schemas, openapi.json, tests) and agents-web (`src/webhooks/`,
`openapi/webhooks.json`). webhook-event-filters runs first; this epic's agents-webhook and agents-web tasks start
from main after it merged. Gate question Q6.

### D15: Sizing exception for the two atomic sweeps (my call)

The orchestrator reads rows with `dict_row` and hands them to API views, so a DB column, its Python field and its
API field change together; renaming a class or type means touching every importer. Splitting
orch-sessions-sweep (DB 0005, Python identifiers, public API, label key) or web-api-layer-sessions (vendored
schema, client and every importer's identifiers) into smaller tasks would need temporary aliases between them,
which the no-compatibility rule forbids. Each stays one task with directory entries in `files`, a guard test plus
a migration or client test as its behaviour, and the component suite plus lint as verify. Every other area that
can move alone (package, chart and CI, wrapper session id, agent API, docs, UI pages, UI workspace) is its own task.

## Orchestrator steps

Run by the main session, in this order, outside the task loop:

- O1 (after the gate, before `ticket.py move ... in-progress`): `gh repo rename agents-orchestrator -R
  szymonrychu/agent-orchestrator --yes`; check `gh repo view szymonrychu/agents-orchestrator` and that the old URL
  redirects (`git ls-remote https://github.com/szymonrychu/agent-orchestrator HEAD`).
- O2 (right after O1, on superrepo main): `git mv code/agent-orchestrator code/agents-orchestrator`;
  `git config -f .gitmodules --rename-section submodule.agent-orchestrator submodule.agents-orchestrator`;
  `git config -f .gitmodules submodule.agents-orchestrator.url https://github.com/szymonrychu/agents-orchestrator`;
  `git submodule sync`; `mise run init:refresh` (role text: sessions instead of clusters); `mise run lint`; commit
  `chore: rename submodule agent-orchestrator to agents-orchestrator`. The task trees of this epic are created
  after this, so `repo: agents-orchestrator` resolves.
- Mid-epic: merge each repo's PR when its tasks are done, push tags (any-mcp v0.3.0, agents-common v0.3.0), and
  write the merged sha7 into the pin tasks with `ticket.py amend`.
- U1 before deploy-cutover, U2 after it (user-run, D9).
- The applies of deploy-cutover and hibernate-old-orch-db (D7, D6), and the orphan TLS Secret deletion.
- O3 after the epic merges (D13).

## Research

| Lens | Ran / skipped | Adopted | Rejected |
|---|---|---|---|
| discovery (planner recon) | ran: origin/main of all six repos in detached trees, live namespace read-only, live DB row counts | D5 facts, D2 inventory (`git grep` over src, tests, chart, openapi.json) | - |
| research-code-internal | skipped: no new helper or subsystem, a rename plus two SQL migrations | - | - |
| research-code-external | skipped: no open design fork beyond D5, settled by the cnpg chart docs | - | - |
| research-papers | skipped: no algorithmic core | - | - |
| research-docs | ran (chart values): `helm show values cnpg/cluster --version 0.9.0` | `mode: recovery`, `recovery.method: import`, `import.type: microservice`, `source.passwordSecret`, `sslRootCertSecret` | pg_basebackup, object_store (D5) |

## Research inputs

- Wrapper session id collides with the new `session_id` (agents.session_id, events.session_id, EventView) - 0001_init.sql, api/streams.py - orch-wrapper-session-id.
- The migration runner applies each pending file in one transaction under an advisory lock - db/migrate.py:run_migrations - orch-wrapper-session-id, orch-sessions-sweep.
- SQL naming clusters or cluster_id lives in 21 src files beyond db/, and dict rows carry column names straight into API views (db/views.py dict_row), so DB, Python and API names move together - `git grep` - orch-sessions-sweep (D15).
- orchestrator tests import any_mcp.orchestrator and any_mcp.config - tests/test_agent_scale.py, tests/test_on_start.py - orch-agent-api-sessions (pin v0.3.0).
- Label key and managed-by value gate ownership in kube.py:owns - k8s/labels.py, k8s/kube.py - orch-package-rename (managed-by), orch-sessions-sweep (label key).
- agents-web vendors openapi from a sibling checkout by repo name - scripts/sync-api.mjs:11 - web-api-layer-sessions.
- UI menu already says "Sessions" while the rest says cluster - src/layout/SessionsMenu.tsx:34-36 - web-workspace-sessions.
- agents-webhook stores cluster_id and cluster_slug and exposes them - migrations/0001_init.sql:54, api/schemas.py:74 - webhook-session-columns.
- agents-common client, fake and run tracker carry the cluster API - orchestrator.py, fake_orchestrator.py, runs.py - common-client-sessions.
- cnpg/cluster 0.9.0 supports import bootstrap - `helm show values` - helmfile-orch-db-import.
- Old TLS Secret has no owner reference; its Certificate is owned by the old Ingress - live probe - deploy-cutover.
- SSO Secret is terraform-owned outside the workbench - infrastructure keycloak_clients.tf:71-78 - deploy-cutover (U1/U2).
- Retro (test-temp-dirs-outside-the-c, recurring): deletion and cleanup steps get "what runs if the producing step fails" in review - deploy-cutover, hibernate-old-orch-db (precondition probes stop the task before any apply).

## Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| `orch-sessions-api` (D2: routes, schemas, fields, codes, SSE) | orch-sessions-sweep | common-client-sessions, web-api-layer-sessions, helmfile-smoke-sessions | `code/agents-orchestrator/README.md`, `openapi.json` |
| `orch-agent-api-session-header` (X-Orch-Session, ORCH_SESSION_ID, plugin key `session`) | orch-agent-api-sessions | anymcp-plugin-session | `code/agents-orchestrator/README.md` |
| `any-mcp-release-v0-3-0` | anymcp-release-v0-3-0 | orch-agent-api-sessions, helmfile-orch-release-rename | `code/any-mcp/pyproject.toml` |
| `agents-common-release-v0-3-0` | common-release-v0-3-0 | webhook-worker-sessions | `code/agents-common/pyproject.toml` |
| `orch-schema-sessions` (0004, 0005) | orch-wrapper-session-id, orch-sessions-sweep | deploy-cutover | `code/agents-orchestrator/src/agents_orchestrator/db/migrations/` |
| `webhook-events-session-fields` | webhook-session-columns | web-webhooks-session-fields | `code/agents-webhook/openapi.json` |
| `agents-orchestrator-chart` / `-image` | orch-package-rename | helmfile-orch-release-rename | `code/agents-orchestrator/.github/workflows/ci.yaml` |
| `agents-orchestrator-db-release` | helmfile-orch-db-import | helmfile-orch-release-rename, deploy-cutover | `code/agents-helmfile/helmfile.yaml.gotmpl` |

Cross-epic: these supersede the registered `agent-orchestrator-chart`, `agent-orchestrator-image`,
`agent-orchestrator-settings-env`, `orch-cluster-create-api`, `orch-cluster-*`, `orch-services-service`,
`web-settings-menu-order` (entry id `sessions`) and `preset-mapping-model` (RunRef.session_id) for consumers
agents-schedule-microservice and workspace-s3-cache. This repo's ticket.py (plugin 2.0.0) has no `contract`
subcommand, so the orchestrator updates `docs/plans/contracts.json` in O3.

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 Names | orch-package-rename, orch-chart-ci-rename, helmfile-orch-db-import, helmfile-orch-release-rename, helmfile-consumers-rename, webhook-docs-sessions, web-docs-names |
| D2 Session vocabulary | orch-sessions-sweep, orch-agent-api-sessions, orch-docs-e2e-sessions, anymcp-plugin-session, common-client-sessions, webhook-session-columns, webhook-worker-sessions, web-api-layer-sessions, web-sessions-pages, web-workspace-sessions, web-webhooks-session-fields |
| D3 wrapper_session_id | orch-wrapper-session-id |
| D4 Forward migrations | orch-wrapper-session-id, orch-sessions-sweep, webhook-session-columns |
| D5 Import into a new CNPG cluster | helmfile-orch-db-import, deploy-cutover |
| D6 Hibernate the old DB | hibernate-old-orch-db |
| D7 Cutover sequence | helmfile-orch-release-rename, deploy-cutover |
| D8 No relabel migration | orch-sessions-sweep, deploy-cutover |
| D9 SSO Secret | helmfile-orch-release-rename, helmfile-consumers-rename, deploy-cutover |
| D10 Kept names | orch-package-rename, orch-docs-e2e-sessions |
| D11 Releases and pins | anymcp-release-v0-3-0, common-release-v0-3-0, orch-agent-api-sessions, webhook-worker-sessions, helmfile-orch-release-rename, helmfile-consumers-rename |
| D12 Guard tests | orch-package-rename, orch-chart-ci-rename, orch-sessions-sweep, anymcp-plugin-session, common-client-sessions, orch-docs-e2e-sessions, webhook-docs-sessions, web-sessions-pages, web-docs-names, helmfile-smoke-sessions |
| D13 Superrepo and other epics | orch-package-rename |
| D14 Ordering | webhook-session-columns, web-webhooks-session-fields |
| D15 Sizing exception | orch-sessions-sweep, web-api-layer-sessions |

## Review focus

- orch-wrapper-session-id and orch-sessions-sweep: the migrations keep every row (tests seed rows at 0003 and read
  them back), rename indexes and constraints, and no SQL string in src still names an old table or column.
- orch-sessions-sweep: `owns()` and selectors use the new label key and managed-by value together.
- orch-agent-api-sessions: header, env and plugin key agree with any-mcp v0.3.0; the token binding is unchanged.
- The nomenclature allowlists: each phrase is a Kubernetes, CNPG or kind cluster, never the orchestrator's unit.
- helmfile-orch-db-import: the import source, TLS and password Secret names, and that the old release is untouched.
- deploy-cutover: precondition probes stop before any apply; preset count equality after the import.

## Left to the builder

- Exact names of renamed indexes and constraints, as long as none contains `cluster` and each matches its new
  column or table.
- Helper and variable names inside a module, within the D2 vocabulary.
- The allowlist's exact phrases, within D12's boundary.
- Splitting a test file renamed with its module (for example test_clusters_repo.py to test_sessions_repo.py) as a
  `git mv` plus edits.

## Assumptions and unknown facts

- helmfile with `--selector name=<release>` applies only the selected release (no `--include-needs`); confirmed by
  `mise run diff -- --selector ...` output in deploy-cutover before each apply.
- CNPG microservice import restores objects owned by the new owner `agents_orchestrator`; confirmed in
  deploy-cutover by `\dt` ownership and the new app's migrate succeeding.
- The cnpg chart leaves an imported Cluster's bootstrap section unchanged on later applies (no diff); confirmed by
  `mise run diff` after the cutover (any Cluster spec diff stops the task blocked).
- The webhook worker retries `OrchestratorUnavailable` during the downtime window; confirmed in
  webhook-worker-sessions by reading worker.py (an existing test pins it, else the task adds one).

## Open questions
- Q1: Rename the DB tables and columns too (clusters to sessions, cluster_id to session_id) through two forward migrations, rather than keeping cluster in the DB? [answer: yes, recommended answer (user: 'Go' on the combined gate, 2026-10-25)]
- Q2: Move the live database to a new CNPG cluster agents-orchestrator-db imported from the old one after the old app is uninstalled, rather than keeping the old agent-orchestrator-db name? [answer: yes, recommended answer (user: 'Go' on the combined gate, 2026-10-25)]
- Q3: After a green smoke, keep the old database hibernated (pods stopped, PVCs and S3 backups kept, reversible) rather than deleting it? [answer: yes, recommended answer (user: 'Go' on the combined gate, 2026-10-25)]
- Q4: Rename the SSO Secret and Keycloak client to agents-orchestrator(-proxy) through a user-run terraform change in the infrastructure repo (add the new client before the cutover, remove the old one after)? [answer: yes, recommended answer (user: 'Go' on the combined gate, 2026-10-25)]
- Q5: Keep the ORCH_ env prefix, the orch CLI and the X-Orch- header family (they abbreviate orchestrator)? [answer: yes, recommended answer (user: 'Go' on the combined gate, 2026-10-25)]
- Q6: Let webhook-event-filters land first and start this epic's agents-webhook and agents-web tasks after it? [recommended: yes]
- Q7: The wrapper's own session id becomes wrapper_session_id in the orchestrator DB and API, so session means only the orchestrator's unit? [recommended: yes]

## Irreversible operations in scope

- GitHub repo rename szymonrychu/agent-orchestrator to agents-orchestrator (O1; reversible by renaming back, old
  URL redirects until a new repo takes the old name).
- Tags any-mcp v0.3.0 and agents-common v0.3.0 pushed to origin (never re-pointed).
- Helm uninstall of release `agent-orchestrator` (deploy-cutover step 2): deletes its Deployments, Services,
  Ingress, ConfigMap, Secrets agent-orchestrator-{claude,master-key,services} (values stay in SOPS, moved), the
  cert-manager Certificate, and the helm release history (no `helm rollback` to it).
- Forward migrations 0004 and 0005 on the new live orchestrator DB, and 0005 on the live agents-webhook DB
  (column renames, no rows dropped).
- Deletion of the orphan Secret `agent-orchestrator-tls` (a certificate, reissuable).
- User-run terraform U2: deletes Keycloak client `agent-orchestrator` and Secret `agent-orchestrator-proxy`.
- Downtime of `/api` and the webhook worker's orchestrator calls during the cutover (minutes).
- Not in scope: deleting the old CNPG cluster, its PVCs, its S3 backups or the old Harbor repositories.
