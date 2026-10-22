# agent-orchestrator design

## Summary

agent-orchestrator is a new component at `code/agent-orchestrator` (public origin `github.com/szymonrychu/agent-orchestrator`): one Python repo and one image with four long-running entrypoints (`orch api`, `orch dispatcher`, `orch ingester`, `orch reconciler`) plus `orch migrate` and the `orch bench` CLI, coordinating only through its own CNPG Postgres (SKIP LOCKED queue tables and LISTEN/NOTIFY wake-ups). Each cluster of agents is a StatefulSet of single-session claude-code-wrapper pods sharing one RWX CephFS PVC, with peers enabled and any-mcp preinstalled. A React/MUI web UI (theme ported from the ros2 web_ui) shows a left ribbon of clusters with state, pod count and a circular context gauge, and a virtualised chat of every agent's activity. The headless `/api/v1` (REST plus SSE) is the same API the UI uses and is the unified router that tatara and magic-trainer will use.

## Intent and why

The user wants to orchestrate pods running claude-code-wrapper from one place: see which sessions are waiting or working, how many agent pods run and how full each context is; read and drive the chat of a session; define and discard pods and clusters with their config. Messages to a cluster go round-robin to the agent that has been free the longest. The point is an experiment: does round-robin plus multiple agents plus agents messaging each other make the work faster, more robust and more correct? The headless API fixes the router's shape now, because tatara and magic-trainer will consume it later.

## Goals

- G1: `/api/v1` REST plus two SSE streams cover clusters, agents, messages, commands, events and checks; every route is documented in README.md and the README parity test passes.
- G2: A message posted to a cluster is delivered to the ready, idle agent with the oldest `free_since`; while every agent is busy it stays queued and is dispatched when one frees; two concurrent dispatchers never double-dispatch.
- G3: Creating, editing and discarding a cluster through the API reconciles a StatefulSet, headless Service, RWX PVC, ConfigMap and Secret, all labelled; discard removes every labelled object including the PVC.
- G4: The web UI shows a left ribbon (clusters with working/waiting state, ready/replicas count, circular 0-100% context gauge; expandable agents with their own gauge), a virtualised chat (newest 200 on open, older pages on scroll-up, live append) with user inputs, assistant output, thinking, tool calls and peer messages, a composer, a queue strip, a cluster form and a discard dialog.
- G5: Every agent session starts with any-mcp registered as a stdio MCP server, from an agent image that installs any-mcp from a pinned git tag.
- G6: `orch bench spec.yaml` runs the experiment arms against the public API and writes JSONL plus a summary table.
- G7: GitHub CI runs Python lint and tests, frontend lint, tests, build and API type drift, builds and pushes both images to Harbor `containers/`, and runs the kind e2e.

## Non-goals

- No authentication; the UI and API are LAN-only behind the ingress whitelist (the ingress is in the deploy epic).
- No special prompts for clustered agents.
- No answering AskUserQuestion from the UI (`ask_user_question: deny`).
- No Helm chart, helmfile release or superrepo docs here: those are the deploy epic `agents-k8s-deploy` (infrastructure) and the superrepo docs task D4.
- No wrapper changes here: they are the epic `claude-code-wrapper-orchestr`.
- No per-message callback URL for consumers.

## Anti-goals

- A second copy of model context-window sizes in the orchestrator (it drifts; the wrapper reports the window).
- Proxying the wrapper's event log instead of storing it (no merged timeline, no history after pod deletion, no backward paging).
- Kubernetes credentials or wrapper tokens reachable from the no-auth `api` process.
- A CRD or operator framework for what one table and a loop already do.
- Starting the frontend on old majors (ESLint 8, Vite 5, MUI 6).

## Constraints

- Component hard rules (superrepo AGENTS.md), as amended by the user: Python only except web frontends; the orchestrator may call the Kubernetes API; services talk only through the queue or HTTP APIs, no shared state, interpreted as one writer per table (D2).
- Postgres only (CNPG per app); no Redis, NATS or other broker.
- Python 3.12, uv, ruff, mise, FastAPI 0.160.0 (native SSE `fastapi.sse.EventSourceResponse`), psycopg 3.3.6 async, lightkube 1.0.1, httpx; npm: react 19.3.1, @mui/material 9.5.0, vite 8.3.5, vitest 5.0.5, react-virtuoso 4.18.19, eslint 10.13.0, openapi-typescript 7.13.0.
- Wrapper facts: bearer auth on `/v1`; a turn to a busy session returns 409; session create is synchronous; `sessions_root` is globbed at startup (a shared one leaks sessions between pods); peers need a unique name, a reachable `advertise_url`, and a shared token of at least 16 characters that differs from `auth_token`; a seed equal to `self_url` is skipped; never expose a wrapper through an ingress.
- Infra facts: `rook-ceph-rwx` is the default StorageClass; `regcred` exists in every release namespace; Harbor tags are immutable; Kubernetes v1.33.0.
- Depends on epic `claude-code-wrapper-orchestr` (context, idle_since, user_message, `/v1/peers`) and epic `any-mcp` (a pinned git tag with a stdio entrypoint). Tasks that consume them name the contract in `uses`.
- Verify commands are targeted pytest or vitest files plus lint, never the full suite.

## Decisions

### D1: One repo, one image, four entrypoints

`agent-orchestrator` is one uv project and one image whose entrypoint is `orch <cmd>`: `api` (FastAPI REST, SSE, serves the SPA; never calls wrappers or Kubernetes), `dispatcher` (claims messages and commands, calls wrapper turns, interrupt and compact), `ingester` (one SSE subscription per agent, writes events, agent status and turns), `reconciler` (renders and applies Kubernetes objects, observes pods, bootstraps sessions, runs checks, executes restart), `migrate` (initContainer), and the undeployed `bench` CLI. Alternatives: a single process (puts Kubernetes credentials and wrapper tokens behind the no-auth UI process and is not decentralised), a repo per service (four pipelines, schema drift). Serves A5, A11.

### D2: Postgres-only coordination and the single-writer rule

Every cross-process signal goes through Postgres: `messages`, `commands` and `checks` are SKIP LOCKED queues; `clusters.generation > observed_generation` is the reconcile queue; NOTIFY channels `cluster_changed`, `agent_free`, `events {cluster_id, max_id}` and `status {cluster_id}` are wake-up hints carrying ids only. Every loop also polls (dispatcher 2 s, reconciler 10 s) because NOTIFY is lost while a listener is disconnected. "No shared state" is interpreted as one writer per table; queue tables are the only multi-writer tables, and only through state-machine-guarded UPDATEs (`WHERE status = '<expected>'`). The rule is written into the component README and MEMORY.md (superrepo AGENTS.md is the deploy epic's D4). Alternative: a generic job library (procrastinate) - rejected, the claim joins against agent availability. Serves A6, A11.

### D3: Schema 0001 and table writers

Plain SQL migrations, psycopg 3 async, no ORM. Tables and writers: `clusters` [api; reconciler writes only `status`, `observed_generation`, `deleted_at`], `agents` [reconciler; `last_dispatched_at` is written by the dispatch claim, D23], `agent_status` [ingester], `messages` [api inserts and cancels while queued; dispatcher the rest], `turns` [ingester], `events` [ingester; UNIQUE(agent_id, session_id, seq), global bigserial id used as SSE id and page cursor], `commands` [api inserts; dispatcher claims interrupt and compact and also inserts `rebootstrap` after a wrapper 404; reconciler claims restart and rebootstrap], `checks` [api inserts; reconciler the rest]. Events are kept until the cluster is purged and deleted by cascade on purge; no partitioning. Serves A11.

### D4: Round-robin to the agent free the longest

The dispatcher claims the oldest dispatchable queued message of a cluster under a per-cluster advisory lock, then picks the ready, idle agent of that cluster with the oldest `free_since` whose `free_since` is newer than `agents.last_dispatched_at` (closing the race between a 202 and the ingester seeing busy), locks it SKIP LOCKED, writes `last_dispatched_at`, marks the message `dispatching`, commits, then POSTs the turn. Outcomes are mapped by D23 and D24: 202 sets `sent` and `turn_id`; 409 returns it to `queued`; unavailable increments `attempts` and returns it to `queued`, or sets `failed` at `max_attempts`; every non-accept outcome releases the agent. `max_attempts` defaults to 1 (no automatic retry); `POST /messages/{id}/retry` and a Retry button re-queue a failed message (my call, Q5). A `target_agent_id` restricts the pick. Dispatch is FIFO per cluster; completion order is not guaranteed. Serves A6.

### D5: Store events, do not proxy them

The ingester holds one SSE subscription per agent session with `Last-Event-ID = agent_status.last_seq`, reconnecting with 1-30 s backoff; on attach it reads the snapshot (state, `idle_since`, context) and `GET /v1/peers`. Inserts are `ON CONFLICT DO NOTHING` (at-least-once delivery, exactly-once storage); a seq hole after resume writes a synthetic `gap` row. `session_state` sets `agent_status.state` and `free_since` and NOTIFYs `agent_free` and `status`; `context` events set the context columns; turn events project into `turns`. Wrapper callbacks are not used. Serves A2.

### D6: Kubernetes model per cluster

Per cluster `<slug>` in the clusters namespace (`ORCH_CLUSTERS_NAMESPACE`, default `agents-clusters`, D26; the orchestrator itself runs in `agents`), labelled `agents.szymonrichert.pl/cluster=<slug>` and `app.kubernetes.io/managed-by=agent-orchestrator`: PVC `agent-<slug>-workspace` (RWX, `rook-ceph-rwx`), Secret `agent-<slug>-ccw`, ConfigMap `agent-<slug>-config` (ccw `config.yaml` and `any-mcp.yaml`), headless Service `agent-<slug>` (publishNotReadyAddresses), StatefulSet `agent-<slug>` (Parallel, `imagePullSecrets: [regcred]`, uid/fsGroup 1000, `/healthz` and `/readyz` probes, PVC subPath `workdir` at `/workdir` shared (sessions and check Jobs both work in `/workdir/<spec.workdir>`, D27), `subPathExpr: sessions/$(POD_NAME)` at `/sessions` per pod, emptyDir `/opt/mise`, `CLAUDE_CODE_OAUTH_TOKEN` from Secret `agent-orchestrator-claude`, which the deploy chart also renders into the clusters namespace). One pod runs one session (`max_sessions: 1`), and a single pod is a cluster of 1 (my call, Q2 and Q3). Reconcile is level-triggered (10 s plus `cluster_changed`): render, server-side apply (field manager `agent-orchestrator`, force), prune labelled objects not desired, upsert `agents` from pods, bootstrap or adopt sessions, set `observed_generation`. Alternatives rejected: bare pods, Deployment (no per-pod DNS), CRD plus operator, volumeClaimTemplates, imperative create and delete. Serves A4, A8.

### D7: Per-cluster derived tokens

`CCW_AUTH_TOKEN = HMAC-SHA256(master, "auth:" + cluster_id)` and `CCW_PEER_TOKEN = HMAC-SHA256(master, "peer:" + cluster_id)`, hex encoded, so they always differ and exceed 16 characters. The master key is one orchestrator Secret (SOPS in helmfile, deploy epic); dispatcher, ingester and reconciler derive the same tokens, so no token is stored and no process reads Secrets back. One token per cluster is one trust domain, matching the shared peer token. Serves A7.

### D8: Rendered wrapper config, validated in tests

The ConfigMap's `config.yaml` sets `server.auth_token: ${CCW_AUTH_TOKEN}`, `paths {workdir_root: /workdir, sessions_root: /sessions}`, `claude.env` (OAuth token, `disable_autoupdater`), `claude.model`, `claude.effort`, `claude.mcp_servers.any-mcp {type: stdio, command: /opt/any-mcp/bin/any-mcp, args: [--config, /etc/any-mcp/any-mcp.yaml]}`, `sessions {max_sessions: 1, resume_on_start: true, idle_timeout_seconds: 0, ask_user_question: deny}`, and, when `spec.peers`, `peers {enabled, name: ${POD_NAME}, advertise_url: ${CCW_PEER_URL}, token: ${CCW_PEER_TOKEN}, static: [every ordinal URL]}`. A test validates the rendered YAML with `claude_code_wrapper.config.load_config`, from a dev dependency pinned by git to the same wrapper sha as the agent image, so config drift fails CI. `ask_user_question: deny` (my call, Q11). Serves A4, A7, A9.

### D9: RBAC limited to the reconciler

A namespaced Role in the clusters namespace (D26), bound only to the reconciler's ServiceAccount (which lives in `agents`): statefulsets, services, configmaps, persistentvolumeclaims (get, list, watch, create, patch, delete); secrets (create, patch, delete only: names are deterministic, so the reconciler can never read the orchestrator's or any other Secret); pods (get, list, watch, delete); jobs (get, list, watch, create, delete); pods/log (get); never pods/exec. The verb list is documented in README.md and exercised by the kind e2e's Role manifest; the production Role is in the deploy epic's chart. Serves A13.

### D10: Checks run as Jobs mounting the cluster PVC

`POST /clusters/{id}/checks {command}` queues a check; the reconciler runs it as a Job in the cluster's namespace mounting the cluster PVC at `/workdir`, then records `exit_code` and a bounded `log_tail` from pods/log. Bench verify steps are checks. Serves A10.

### D11: Headless API v1 over REST and SSE

`/api/v1`, JSON, errors `{"error": {"code", "message"}}` as in the wrapper: clusters (`GET|POST /clusters`, `GET|PATCH|DELETE /clusters/{id}`, `?purge=true`), agents (`GET /clusters/{id}/agents`, `POST /agents/{id}/interrupt|compact|restart` returning 202), messages (`POST /clusters/{id}/messages {text, target_agent_id?}` returning 202, list, get with turn status and final_text, cancel while queued, retry), events (`GET /clusters/{id}/events?before_id=&after_id=&limit=&agent_id=&types=`), SSE `GET /clusters/{id}/events/stream` (id = events.id, honours Last-Event-ID) and `GET /stream` (cluster_status, agent_status, message_status deltas), checks, `GET /meta`, `/api/v1/openapi.json`. URL major `/v1`, additive-only within v1, README parity test. SSE over WebSocket: the channel is one-directional, resume semantics match the wrapper. Serves A5.

### D12: Frontend stack and ported theme

`frontend/` with React 19.3, MUI 9.5, Vite 8.3, vitest 5, ESLint 10 flat config, TypeScript strict, npm. Port from `ros2-lerobot-sverve-platform/nodes/web_ui/frontend/src`: `theme.ts` TOKENS and overrides (dark, flat, one grey accent), `main.tsx`, `index.css`, `layout/useLayout.ts`, `layout/ConfirmDialog.tsx`, `components/StatusItem.tsx`, `layout/designRules.ts` and its test, the Virtuoso ChatLog configuration and the socket backoff logic re-targeted to EventSource. State is hand-rolled reducers; API types come from `openapi-typescript` over the committed `openapi.json` with a CI drift check. Current majors (my call, Q6). Serves A3.

### D13: Ribbon indicator

Each cluster row shows a working mark when any agent is busy and waiting otherwise, `ready/replicas`, and a determinate circular gauge whose value is the maximum `used_percentage` over its agents (my call, Q9); an expandable agent row shows the agent's own state and gauge. The gauge's denominator is the full model window (the statusline contract) and it draws a tick at the auto-compact point; null context draws as an empty ring with an "unknown" label (my call, Q10). Serves A1.

### D14: Chat with smart loading

`chatModel.ts` reduces stored events into items: user_message, assistant, thinking (collapsed), tool (paired by tool_use_id), denied, turn_end, error, peer, gap; rows carry the agent ordinal with filter chips. `useClusterChat` loads the newest 200 on open, pages older by `before_id` on start-reached, appends live SSE events (resuming by Last-Event-ID) and trims the window. ChatLog uses react-virtuoso with `firstItemIndex` prepend and `followOutput`. Serves A2.

### D15: Discard semantics

`DELETE /clusters/{id}` sets `desired = deleting`; the reconciler's desired set becomes empty, so every labelled object including the PVC is deleted, then `deleted_at` is set. History (messages, events, turns) is kept until `?purge=true`, which deletes the cluster row and cascades. The UI discard dialog names the PVC deletion and needs the slug typed to confirm (my call, Q4). Serves A4.

### D16: any-mcp preinstalled in a derived agent image

`agent-image/Dockerfile`: `FROM harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>`, then `python -m venv /opt/any-mcp && /opt/any-mcp/bin/pip install "any-mcp @ git+https://github.com/szymonrychu/any-mcp@vX.Y.Z"`; the isolated venv keeps any-mcp's dependencies away from ccw's. The wrapper config entry is D8; `any-mcp.yaml` comes from `spec.any_mcp_config` (default from settings) through the ConfigMap. Rejected: an init container copying a venv (shebangs break on move), `uvx` at start (network and unpinned resolve), baking any-mcp into the wrapper image (couples the projects). Pinned git tag (my call, Q8). Serves A9.

### D17: Images and CI

GitHub Actions on ubuntu-latest: Python lint and tests, frontend `npm ci`, lint, test, build and `check:api` drift; on main, build and push `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>` (multi-stage: node build into the Python image's static dir) and `containers/agent-orchestrator-agent:<sha7>`, with a smoke step running `any-mcp --help` in the agent image; then the kind e2e job. Images go to Harbor `containers/` (my call, Q12). Serves A13.

### D18: Bench CLI for the experiment

`orch bench spec.yaml` creates one cluster per arm `{replicas, peers}` (for example 1/off, 3/off, 3/on), runs each task `{prompt, verify}` n times through the public API with an optional chaos step (`POST /agents/{id}/restart` mid-run), runs verify as a check, and records wall time queued-to-completed, failed turns, tokens (from turns usage) and verify pass rate as JSONL plus a summary table. It talks only to the public API. Serves A10.

### D19: Testing strategy

Unit tests for the renderer (golden objects plus ccw config validation), tokens, SSE parser, chat reducer and pick ordering. Postgres tests use a real Postgres through testcontainers (docker), including two concurrent dispatchers and NOTIFY loss recovered by polling. Wrappers are an in-process fake (`tests/fakes/fake_wrapper.py`) whose behaviour is pinned by a contract test that also runs against the real wrapper image with the wrapper's `tests/fake_claude` (integration marker). Kubernetes loops use a `KubeApi` protocol with an in-memory fake. The kind e2e (`mise run test:e2e`) creates a 2-replica cluster through the API with a test image (wrapper plus fake_claude), sends 3 messages, and asserts round-robin by `free_since`, the merged event stream, and that deletion removes every labelled object. Serves A12, A13.

### D20: Singletons, migrations and shutdown

The ingester and reconciler each hold a Postgres advisory lock for their lifetime (a second replica waits as a hot standby and takes over when the lock frees; failover is hardened by D25); api and dispatcher scale freely. `orch migrate` runs the SQL files in order under an advisory lock, recording applied versions, idempotently. Every entrypoint stops cleanly on SIGTERM: loops finish the current iteration, open streams close, the pool closes. Serves A11.

### D21: New component repo

The code lives in a new submodule `code/agent-orchestrator` with public origin `github.com/szymonrychu/agent-orchestrator`, created by the orchestrator after the gate (repo, `main` branch, Harbor push secrets, submodule pointer) before the run. The component has its own README.md (the spec), MEMORY.md and ROADMAP.md. Serves A13.

### D22: Source allowlist and ClusterSpec hardening

In-cluster callers (LLM-driven agent pods, check Jobs) can reach the api Service and flannel enforces no NetworkPolicy, so the api enforces a source-address allowlist on the direct socket peer: `ORCH_ALLOWED_CIDRS` (default 192.168.1.0/24; ingress-nginx is hostNetwork so ingress traffic arrives from node IPs and the pod CIDR is refused). `Forwarded` and `X-Forwarded-For` are ignored, uvicorn runs without proxy headers, `/healthz` and `/readyz` are exempt, and everything else is 403 `forbidden`. `ClusterSpec` is hardened at the same time: `image` only from a server-side allowlist (`ORCH_AGENT_IMAGES` plus the configured agent image), `env` rejects `CCW_*`, `POD_NAME`, `CLAUDE_*`, `ANTHROPIC_*`, `*_PROXY` and `*_BASE_URL` keys, the renderer sets `claude.passthrough_env` to the accepted env names so they reach the claude child (its environment is an allow-list), `any_mcp_config` is validated against the real any-mcp config model, and replicas, PVC size and cluster count are capped from settings (`ORCH_MAX_REPLICAS`, `ORCH_MAX_PVC_SIZE`, `ORCH_MAX_CLUSTERS`). Rejected: a NetworkPolicy (flannel does not enforce it). Serves A14.

### D23: Dispatch correctness: release, one clock, claim write, FIFO, head-of-line

(a) The reservation is released on every outcome where no turn was accepted: the claim stores the agent's previous `last_dispatched_at` and `release_agent` restores it after 409, unavailable, gone, config error, rejected and requeue; an accepted send keeps it until a newer `free_since`. (b) One clock: Postgres `now()` for every comparison; the ingester sets `free_since` from the database clock at the moment it records a transition into idle, and the wrapper's `idle_since` is stored for display only. (c) The claim transaction writes `agents.last_dispatched_at`, the row change that forces READ COMMITTED to recheck the predicate; the pick reads that column; a forced-interleaving test with two connections proves it. (d) A targeted message whose target is busy is skipped and one whose target is gone fails with `target_gone`. (e) A per-cluster transaction-level advisory lock in the claim keeps per-cluster FIFO under concurrent dispatchers. The wrapper client maps every status (202 sent, 409 busy, 404 or 410 gone, 401 or 403 config error, 413 or 422 rejected, 5xx and connect errors unavailable). Serves A15, A16, A23, A24.

### D24: Send timeout and ambiguous outcomes

The wrapper send timeout (`ORCH_WRAPPER_SEND_TIMEOUT_SECONDS`, 15 s) stays at most half of the dispatching stale cutoff (60 s); the dispatching row heartbeats while a send is in flight, and the stale rule uses `coalesce(heartbeat_at, dispatched_at)`. An ambiguous outcome (read timeout or connection reset after the request was written) is never retried automatically: the message becomes `failed` with reason `ambiguous`, the agent stays reserved, and Retry is the user's explicit choice. Serves A18.

### D25: Singleton failover

The lock connection of the ingester and reconciler uses libpq keepalives and `tcp_user_timeout`, a heartbeat every few seconds (`ORCH_LOCK_HEARTBEAT_SECONDS`) verifies the lock is still held, and loss exits non-zero so Kubernetes restarts the pod; a test blackholes the holder's connection. Serves A17.

### D26: Separate namespace for agent clusters, reserved names, no Secret reads

Agent clusters live in their own namespace (`ORCH_CLUSTERS_NAMESPACE`, default `agents-clusters`, created by the helmfile release of the deploy epic; the orchestrator runs in `agents`), so a cluster slug can never collide with the orchestrator's own objects. Object names use the reserved prefix `agent-<slug>`, the slugs `orchestrator` and `orchestrator-*` are rejected, and the reconciler refuses to apply over, or prune, any object lacking both the managed-by and the cluster label. The reconciler's Role grants secrets only create, patch and delete in that namespace (names are deterministic: no get, list or watch), so it deletes the cluster Secret by name and never lists Secrets. The namespace needs `regcred` and the `agent-orchestrator-claude` Secret (deploy epic). Serves A19, A20.

### D27: Session adoption and one workdir path

Bootstrap adopts only sessions in state creating, ready or busy; stopped or failed sessions with a transcript are resumed through `POST .../resume`; anything else gets a new session; a 404 on a turn submit makes the dispatcher enqueue a `rebootstrap` command so the reconciler clears the agent's session and bootstraps again. Sessions are created with the workdir name `spec.workdir` (the wrapper resolves `/workdir/<name>`), and the renderer exposes `workdir_path(spec)` and `workdir_mount(spec)`, used by the StatefulSet and by check Jobs (which work in `/workdir/<spec.workdir>`), pinned by tests in all three tasks. Serves A21, A22.

## Research

| Lens | Ran or skipped | Adopted ideas | Rejected ideas |
|---|---|---|---|
| research-code-internal (claude-code-wrapper) | ran (brief-wrapper.md) | per-pod `sessions_root` (manager.py:1251-1255), peers seed list via pod DNS (peers.py:92, README:3262), `claude.mcp_servers` stdio entry (config.py:194) | deriving context % from usage events plus a model table (router.py:257) |
| research-code-internal (ros2 web_ui) | ran (brief-ui.md) | theme.ts TOKENS, designRules test, Virtuoso ChatLog config, agentSocket backoff | WebSocket transport (server.py:1285), ESLint 8 / Vite 5 / MUI 6 |
| research-code-internal (infrastructure) | ran (brief-infra.md) | `rook-ceph-rwx` default SC, `regcred` per namespace, CNPG `cnpg/cluster` 0.9.0 | redis broker pattern (ai/buzz-redis) |
| research-docs | ran (brief-docs.md) | statusline `context_window.used_percentage` as the gauge source, full-window denominator (code.claude.com/docs/en/statusline) | transcript usage parsing (undocumented schema) |
| research-code-external | ran inside the architect pass (design-orchestrator.md sources) | FastAPI native SSE (fastapi.tiangolo.com/tutorial/server-sent-events), lightkube server-side apply | procrastinate job library |
| research-papers | skipped: no algorithmic question; the experiment is the bench | none | none |

## Research inputs

| Source | Entry | Lands in |
|---|---|---|
| brief-docs.md Plan inputs: Pins | mcp/fastmcp pins | rejected: any-mcp epic owns the library choice |
| brief-docs.md Plan inputs: Library decision | FastMCP vs mcp | rejected: any-mcp epic |
| brief-docs.md Plan inputs: Notifications | list_changed on both eras | rejected: any-mcp epic |
| brief-docs.md Plan inputs: Tool list shape | deterministic tool list | rejected: any-mcp epic |
| brief-docs.md Plan inputs: Entrypoint | stdio, logs to stderr, exit on EOF | container-images-ci (smoke `any-mcp --help`), k8s-object-renderer (stdio entry) |
| brief-docs.md Plan inputs: Claude Code install | stdio entry written by the wrapper, no committed `.mcp.json` approval | k8s-object-renderer |
| brief-docs.md Plan inputs: Gauge | statusline used_percentage, null as unknown, reset on compact, full-window denominator | ingester, fe-context-gauge |
| brief-docs.md Plan inputs: Open gaps | MCP stdio behaviour checks | rejected: any-mcp epic |
| brief-wrapper.md section 6 | context, idle_since, backward history, user_message, peers view gaps | rejected: wrapper epic claude-code-wrapper-orchestr (consumed via contracts) |
| brief-wrapper.md Unknowns | shared `sessions_root` leaks sessions | k8s-object-renderer (`subPathExpr: sessions/$(POD_NAME)`) |
| brief-wrapper.md section 3 | peers need unique name, advertise_url, shared token != auth_token | k8s-object-renderer, cluster-token-derivation |
| brief-infra.md section 4 | orchestrator-created pods need `imagePullSecrets: [regcred]` | k8s-object-renderer |
| brief-infra.md section 1-2 | chart, helmfile, renovate regex | rejected: deploy epic agents-k8s-deploy |
| brief-ui.md section 5 | copy list and reimplement list | fe-scaffold, fe-theme-port, fe-shell-and-ribbon, fe-chat-log-paging |
| brief-ui.md section 4 | frontend CI never ran | spa-serving-and-dockerfile (CI job) |
| design-orchestrator.md section 8 | two-dispatcher and NOTIFY-loss tests | dispatch-queue-sql, dispatcher-loop |

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 One repo, one image, four entrypoints | scaffold-repo-and-cli, entrypoints-and-singleton |
| D2 Postgres-only coordination and the single-writer rule | dispatch-queue-sql, dispatcher-loop, readme-api-and-openapi |
| D3 Schema 0001 and table writers | migrations-and-schema, clusters-repository, events-store |
| D4 Round-robin to the agent free the longest | dispatch-queue-sql, dispatcher-loop, api-messages-and-commands |
| D5 Store events, do not proxy them | events-store, ingester, wrapper-client-and-sse |
| D6 Kubernetes model per cluster | k8s-object-renderer, reconciler-loop, session-bootstrap |
| D7 Per-cluster derived tokens | cluster-token-derivation |
| D8 Rendered wrapper config, validated in tests | k8s-object-renderer |
| D9 RBAC limited to the reconciler | reconciler-loop, kind-e2e |
| D10 Checks run as Jobs mounting the cluster PVC | check-jobs |
| D11 Headless API v1 over REST and SSE | api-clusters-and-agents, api-messages-and-commands, api-events-and-streams, readme-api-and-openapi |
| D12 Frontend stack and ported theme | fe-scaffold, fe-theme-port, fe-api-client-and-stream |
| D13 Ribbon indicator | fe-context-gauge, fe-shell-and-ribbon |
| D14 Chat with smart loading | fe-chat-model, fe-chat-log-paging, fe-composer-and-queue-strip |
| D15 Discard semantics | api-clusters-and-agents, fe-cluster-form |
| D16 any-mcp preinstalled in a derived agent image | container-images-ci |
| D17 Images and CI | spa-serving-and-dockerfile, container-images-ci |
| D18 Bench CLI for the experiment | bench-cli |
| D19 Testing strategy | fake-wrapper-contract, kind-e2e |
| D20 Singletons, migrations and shutdown | entrypoints-and-singleton, migrations-and-schema |
| D21 New component repo | scaffold-repo-and-cli, settings-model |
| D22 Source allowlist and ClusterSpec hardening | scaffold-repo-and-cli, settings-model, clusters-repository, api-clusters-and-agents, k8s-object-renderer, entrypoints-and-singleton, container-images-ci, readme-api-and-openapi, kind-e2e |
| D23 Dispatch correctness | migrations-and-schema, dispatch-queue-sql, ingester, wrapper-client-and-sse, fake-wrapper-contract, dispatcher-loop, api-messages-and-commands |
| D24 Send timeout and ambiguous outcomes | settings-model, migrations-and-schema, dispatch-queue-sql, wrapper-client-and-sse, fake-wrapper-contract, dispatcher-loop, api-messages-and-commands |
| D25 Singleton failover | settings-model, entrypoints-and-singleton |
| D26 Separate namespace, reserved names, no Secret reads | settings-model, clusters-repository, k8s-object-renderer, reconciler-loop, check-jobs, kind-e2e |
| D27 Session adoption and one workdir path | k8s-object-renderer, session-bootstrap, check-jobs, wrapper-client-and-sse, fake-wrapper-contract, dispatch-queue-sql, dispatcher-loop, migrations-and-schema |

## Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| `orch-cli` | scaffold-repo-and-cli | entrypoints-and-singleton, bench-cli | `src/agent_orchestrator/cli.py` |
| `settings` | settings-model | cluster-token-derivation, k8s-object-renderer, api-clusters-and-agents, entrypoints-and-singleton, clusters-repository, dispatcher-loop | `src/agent_orchestrator/settings.py` |
| `schema-v1` | migrations-and-schema | clusters-repository, dispatch-queue-sql, events-store, reconciler-loop, ingester, api-clusters-and-agents | `src/agent_orchestrator/db/migrations/0001_init.sql` |
| `pg-fixture` | migrations-and-schema | clusters-repository, dispatch-queue-sql, events-store, reconciler-loop, ingester, dispatcher-loop, api-clusters-and-agents | `tests/conftest.py` |
| `cluster-spec` | clusters-repository | k8s-object-renderer, api-clusters-and-agents | `src/agent_orchestrator/spec.py` |
| `queue-sql` | dispatch-queue-sql | dispatcher-loop, reconciler-loop, check-jobs, api-messages-and-commands | `src/agent_orchestrator/db/queue.py` |
| `events-repo` | events-store | ingester, api-events-and-streams | `src/agent_orchestrator/db/events.py` |
| `wrapper-client` | wrapper-client-and-sse | fake-wrapper-contract, ingester, dispatcher-loop, session-bootstrap | `src/agent_orchestrator/wrapper/client.py` |
| `fake-wrapper` | fake-wrapper-contract | ingester, dispatcher-loop, session-bootstrap | `tests/fakes/fake_wrapper.py` |
| `cluster-tokens` | cluster-token-derivation | k8s-object-renderer, ingester, dispatcher-loop, session-bootstrap | `src/agent_orchestrator/tokens.py` |
| `k8s-render` | k8s-object-renderer | reconciler-loop, check-jobs | `src/agent_orchestrator/k8s/render.py` |
| `kube-api` | reconciler-loop | check-jobs, entrypoints-and-singleton | `src/agent_orchestrator/k8s/kube.py` |
| `agents-repo` | reconciler-loop | session-bootstrap, check-jobs | `src/agent_orchestrator/db/agents.py` |
| `api-app` | api-clusters-and-agents | api-messages-and-commands, api-events-and-streams, readme-api-and-openapi, spa-serving-and-dockerfile, entrypoints-and-singleton | `src/agent_orchestrator/api/app.py` |
| `openapi-v1` | readme-api-and-openapi | fe-api-client-and-stream, bench-cli | `openapi.json` |
| `fe-theme` | fe-theme-port | fe-context-gauge, fe-shell-and-ribbon, fe-chat-log-paging, fe-cluster-form | `frontend/src/theme.ts` |
| `fe-api` | fe-api-client-and-stream | fe-shell-and-ribbon, fe-chat-model, fe-chat-log-paging, fe-composer-and-queue-strip, fe-cluster-form | `frontend/src/api/client.ts` |
| `context-gauge` | fe-context-gauge | fe-shell-and-ribbon | `frontend/src/ribbon/ContextGauge.tsx` |
| `chat-model` | fe-chat-model | fe-chat-log-paging | `frontend/src/chat/chatModel.ts` |
| `agent-image` | container-images-ci | kind-e2e | `agent-image/Dockerfile` |

## Cross-epic contracts

Registered in `docs/plans/contracts.json` (this superrepo) and `infrastructure/docs/plans/contracts.json`:

| Contract | Owner epic | Consumer epic | Used by tasks |
|---|---|---|---|
| `wrapper-idle-since` | claude-code-wrapper-orchestr | agent-orchestrator | wrapper-client-and-sse, ingester |
| `wrapper-context-surface` | claude-code-wrapper-orchestr | agent-orchestrator | wrapper-client-and-sse, ingester |
| `wrapper-user-message-event` | claude-code-wrapper-orchestr | agent-orchestrator | wrapper-client-and-sse, ingester |
| `wrapper-peers-view` | claude-code-wrapper-orchestr | agent-orchestrator | wrapper-client-and-sse, ingester |
| `wrapper-history-backward` | claude-code-wrapper-orchestr | agent-orchestrator | fake-wrapper-contract |
| `any-mcp-cli` | any-mcp | agent-orchestrator | container-images-ci, k8s-object-renderer |
| `any-mcp-config` | any-mcp | agent-orchestrator | k8s-object-renderer, clusters-repository, scaffold-repo-and-cli |
| `any-mcp-release` | any-mcp | agent-orchestrator | container-images-ci |
| `agent-orchestrator-settings-env` | agent-orchestrator | agents-k8s-deploy | settings-model |
| `agent-orchestrator-image` | agent-orchestrator | agents-k8s-deploy | container-images-ci |
| `agent-orchestrator-claude-secret` | agents-k8s-deploy | agent-orchestrator | k8s-object-renderer |

## Review focus

- dispatch-queue-sql and dispatcher-loop: the claim and pick SQL, the reservation rule `free_since > last dispatched_at`, the 409/503 transitions; two concurrent dispatchers must never send one message twice or two messages to one agent.
- ingester: resume by Last-Event-ID, gap rows, idempotent insert, `free_since` only moving on a transition to idle.
- reconciler-loop: prune must only ever touch objects carrying both labels; a `deleting` cluster deletes the PVC; field manager and force apply.
- cluster-token-derivation: tokens never logged, never stored, never returned by the API.
- api: no route reaches Kubernetes or a wrapper; error shape matches the wrapper; the source allowlist checks the direct peer only (D22).
- dispatch: every non-accept outcome releases the agent, the claim writes `last_dispatched_at`, the per-cluster advisory lock keeps FIFO, ambiguous sends are never retried (D23, D24).
- reconciler Role: secrets create, patch, delete only, clusters namespace only (D26).
- k8s-object-renderer: the rendered ccw config must validate with the pinned wrapper's `load_config`.

## Left to the builder

- Module layout inside `src/agent_orchestrator/` beyond the files named in tasks, as long as each contract stays defined in its one file.
- Exact pydantic model names, log fields and SQL index names.
- Frontend component internals and copy text within the theme and designRules.
- Bench summary table formatting.

## Assumptions and unknowns

- The wrapper image sha7 that contains the `claude-code-wrapper-orchestr` changes is known only when that epic lands; the agent image `FROM` and the ccw dev dependency pin take that sha (confirmed by `git -C code/claude-code-wrapper rev-parse --short=7 origin/main` after it merges).
- The any-mcp tag `vX.Y.Z` is known only when the any-mcp epic tags its release; container-images-ci pins it (confirmed with `git ls-remote --tags https://github.com/szymonrychu/any-mcp`).
- Harbor push credentials: the orchestrator sets the repo secrets `HARBOR_USERNAME` and `HARBOR_PASSWORD` on the new GitHub repo at origin creation, with the same robot as claude-code-wrapper; if the value cannot be read, the user provides it (confirmed by `gh secret list -R szymonrychu/agent-orchestrator`).
- Docker is available locally (docker 29.8.2 probed) and on GitHub ubuntu-latest, so testcontainers Postgres runs in both; kind is installed through mise.

## Open questions
- Q1: The tatara rule 'services talk only through the queue or HTTP APIs; no shared state' conflicts with a Postgres-only queue, which is itself a shared table. Is it read as: one writer per table, with queue tables the only multi-writer tables, changed only through state-machine-guarded UPDATEs? [answer: yes, single-writer interpretation, written into the component README and MEMORY.md (accepted as recommended)]
- Q2: Does each agent pod run exactly one wrapper session (max_sessions 1)? [answer: yes, 1 pod = 1 session (accepted as recommended)]
- Q3: Is a single pod modelled as a cluster with one replica, so there is no separate single-pod type? [answer: yes, a single pod is a cluster of 1 (accepted as recommended)]
- Q4: On discard, are the cluster's Kubernetes objects deleted including the shared PVC and its files, with history kept until an explicit purge? [answer: discard deletes everything: the Kubernetes objects, the PVC and the chat history (messages, events, turns); there is no separate purge. An optional pre-discard hook (a command or webhook URL from settings, a webhook URL from the cluster spec; none by default) receives the cluster's full history export as JSONL before anything is deleted (changed by the user, D15)]
- Q5: When a message cannot be delivered (wrapper 503 or a network error), is it retried automatically? [answer: automatic: bounded attempts with exponential backoff on definite non-accepts; an ambiguous outcome is checked against the wrapper (did the turn start: turn metadata and snapshot current_turn_id) before any retry, so a turn is never sent twice (changed by the user, D24)]
- Q6: Does the frontend start on the current majors (React 19.3, MUI 9.5, Vite 8.3, vitest 5, ESLint 10 flat config) rather than the ros2 versions (React 18, MUI 6, Vite 5, ESLint 8)? [answer: yes, current majors (accepted as recommended)]
- Q7: Which helmfile bucket hosts the agent-orchestrator and agent-orchestrator-db releases in namespace agents? [answer: a separate helmfile-like repo agents-helmfile (code/agents-helmfile, public szymonrychu/agents-helmfile, SOPS secrets) manages namespace agents with local mise diff/apply tasks; epic agents-helmfile; the infrastructure epic agents-k8s-deploy is dropped (changed by the user)]
- Q8: How is any-mcp installed into the agent image? [answer: no derived agent image: the agents run the wrapper image directly and the orchestrator renders one onStart hook script per cluster that pip-installs any-mcp from the pinned git tag into /opt/any-mcp and writes its config (changed by the user, D16)]
- Q9: What does a cluster row's context gauge show when the cluster has several agents? [answer: the maximum used percentage over its agents (accepted as recommended)]
- Q10: What is the context gauge's denominator? [answer: the full model context window with a tick at the auto-compact percentage (accepted as recommended)]
- Q11: How do agent sessions handle AskUserQuestion, given the UI does not answer it? [answer: AskUserQuestion is disabled (ask_user_question deny plus permissions.deny); agents get an appended system prompt telling them to ask questions in writing as a numbered list, each with a recommended answer (changed by the user, D8)]
- Q12: Where are the orchestrator and agent images pushed? [answer: Harbor containers/ (accepted as recommended); with Q8 only containers/agent-orchestrator:<sha7> is built here]
- Q13: How are the agent-orchestrator-db CNPG backups configured? [recommended: copy the backup configuration of the existing CNPG release in the ai bucket]
- Q14: Do agent clusters live in their own namespace `agents-clusters` (configurable `ORCH_CLUSTERS_NAMESPACE`, created by the helmfile release, regcred and the Claude Secret provided there) while the orchestrator runs in `agents`? [recommended: yes, for blast radius: the reconciler Role then cannot touch the orchestrator's objects]

## Irreversible operations in scope

- Creating the public GitHub repository `szymonrychu/agent-orchestrator` and pushing to it: covered by the gate approval (D21).
- Pushing images to Harbor `containers/agent-orchestrator` and `containers/agent-orchestrator-agent`: Harbor tags are immutable; tags are commit sha7s, so a push never overwrites. Covered by D17.
- Cluster discard deletes the cluster PVC and its data at run time (a product behaviour, D15): safeguarded by the typed-slug confirmation in the UI; purge deletes history only with `?purge=true`.
