# agent-orchestrator design

## Summary

agent-orchestrator is a new component at `code/agent-orchestrator` (public origin `github.com/szymonrychu/agent-orchestrator`). It is one Python repo and one image with four long-running entrypoints (`orch api`, `orch dispatcher`, `orch ingester`, `orch reconciler`), plus `orch migrate` and the `orch bench` CLI. The processes coordinate only through their own Postgres (SKIP LOCKED queue tables and LISTEN/NOTIFY wake-ups).

Each cluster of agents is a StatefulSet of single-session claude-code-wrapper pods in the namespace `agents`, sharing one RWX CephFS PVC, with peers enabled. A per-cluster rendered onStart hook installs any-mcp into every agent pod before its session starts. A React/MUI web UI (theme ported from the ros2 web_ui) shows a left ribbon of clusters with state, pod count and a circular context gauge, and a virtualised chat of every agent's activity. The headless `/api/v1` (REST plus SSE) is the same API the UI uses, and it is the unified router that tatara and magic-trainer will use.

The repo ships its own Helm chart (`chart/agent-orchestrator`), published to `oci://harbor.szymonrichert.pl/charts`. The chart needs a Postgres connection and offers CNPG as an optional feature.

## Intent and why

The user wants to orchestrate pods running claude-code-wrapper from one place: see which sessions are waiting or working, how many agent pods run and how full each context is; read and drive the chat of a session; define and discard pods and clusters with their config. Messages to a cluster go round-robin to the agent that has been free the longest. The point is an experiment: does round-robin plus multiple agents plus agents messaging each other make the work faster, more robust and more correct? The headless API fixes the router's shape now, because tatara and magic-trainer will consume it later.

## Goals

- G1: `/api/v1` REST plus two SSE streams cover clusters, agents, messages, commands, events and checks. Every route is documented in README.md and the README parity test passes.
- G2: A message posted to a cluster is delivered to the ready, idle agent with the oldest `free_since`. While every agent is busy it stays queued, and it is dispatched when one frees. Two concurrent dispatchers never double-dispatch. A definite non-accept is retried automatically with bounded backoff. An ambiguous send is checked against the wrapper before any retry, so a turn is never sent twice.
- G3: Creating, editing and discarding a cluster through the API reconciles a StatefulSet, headless Service, RWX PVC, ConfigMap and Secret, all labelled, in namespace `agents`. Discard removes every labelled object including the PVC, and the cluster's whole history. An optional pre-discard hook receives the JSONL history export first.
- G4: The web UI shows:
  - a left ribbon: clusters with working/waiting state, a ready/replicas count and a circular 0-100% context gauge, and expandable agents with their own gauge
  - a virtualised chat: newest 200 on open, older pages on scroll-up, live append; it shows user inputs, assistant output, thinking, tool calls and peer messages
  - a composer, a queue strip, a cluster form and a discard dialog
- G5: Every agent session starts with any-mcp registered as a stdio MCP server. The rendered onStart hook installs it from a pinned git tag at pod start, so there is no derived agent image.
- G6: `orch bench spec.yaml` runs the experiment arms against the public API and writes JSONL plus a summary table.
- G7: GitHub CI does the following:
  - runs Python lint and tests, and frontend lint, tests, build and API type drift
  - builds and pushes the orchestrator image to Harbor `containers/`
  - lints and tests the Helm chart and publishes it to `oci://harbor.szymonrichert.pl/charts`
  - runs the kind e2e, which installs that chart
- G8: Agents never block on AskUserQuestion. The tool is disabled, and an appended system prompt makes them ask in writing as a numbered list, each question with a recommended answer.

## Non-goals

- No authentication. The UI and API are LAN-only behind the ingress whitelist, which epic agents-helmfile configures through the chart's ingress values.
- No special prompts for clustered agents beyond the ask-in-writing instruction (D8).
- No answering AskUserQuestion from the UI: the tool is disabled.
- No helmfile release, SOPS secrets or superrepo docs here. Those are epic `agents-helmfile` (code/agents-helmfile) and the superrepo docs.
- No wrapper changes here. They are epic `claude-code-wrapper-orchestr`, which also adds the onStart hook.
- No per-message callback URL for consumers.

## Anti-goals

- A second copy of model context-window sizes in the orchestrator (it drifts; the wrapper reports the window).
- Proxying the wrapper's event log instead of storing it (no merged timeline, no history after pod deletion, no backward paging).
- Kubernetes credentials or wrapper tokens reachable from the no-auth `api` process.
- A CRD or operator framework for what one table and a loop already do.
- Starting the frontend on old majors (ESLint 8, Vite 5, MUI 6).
- Homelab specifics baked into the chart defaults (ingress annotations, hosts, storage classes, CNPG on by default).
- A retry that can paste one message into a session twice.

## Constraints

- Component hard rules (superrepo AGENTS.md), as amended by the user:
  - Python only, except web frontends.
  - The orchestrator may call the Kubernetes API.
  - Services talk only through the queue or HTTP APIs, with no shared state, interpreted as one writer per table (D2).
- Postgres only (CNPG per app, or any Postgres the chart is pointed at); no Redis, NATS or other broker.
- Pinned versions:
  - Python side: Python 3.12, uv, ruff, mise, FastAPI 0.160.0 (native SSE `fastapi.sse.EventSourceResponse`), psycopg 3.3.6 async, lightkube 1.0.1, httpx.
  - npm side: react 19.3.1, @mui/material 9.5.0, vite 8.3.5, vitest 5.0.5, react-virtuoso 4.18.19, eslint 10.13.0, openapi-typescript 7.13.0.
  - Chart: Helm through mise.
- Wrapper facts:
  - Auth and turns: bearer auth on `/v1`. A turn to a busy session returns 409. Session create is synchronous.
  - Sessions root: `sessions_root` is globbed at startup, so a shared one leaks sessions between pods.
  - Peers need a unique name, a reachable `advertise_url`, and a shared token of at least 16 characters that differs from `auth_token`. A seed equal to `self_url` is skipped. Never expose a wrapper through an ingress.
  - Turn metadata: a turn's client `metadata` is kept on the turn record (README.md:329, turns.py:105, readable with `GET /v1/sessions/{id}/turns/{turn_id}`).
  - AskUserQuestion: `sessions.ask_user_question` accepts forward, deny or allow (README.md:2693). `claude.permissions.deny` removes tools (config.py:148-150). `prompts.system_append` appends text to the session CLAUDE.md (README.md:2600).
  - There is no instance-start hook today: onCreate runs after claude starts (manager.py:594-605), and `init.setup_commands` run per created session only (manager.py:474-482, workdir.py:149-160). The wrapper epic adds `hooks.onStart` (contract `wrapper-on-start-hook`).
  - The wrapper image is python:3.12-slim with git (Dockerfile:18, :31), so `python3 -m venv` and a git pip install work in it.
- Infra facts: `rook-ceph-rwx` is the default StorageClass; `regcred` exists in every release namespace; Harbor tags are immutable; Kubernetes v1.33.0.
- Depends on two epics. Tasks that consume them name the contract in `uses`.
  - `claude-code-wrapper-orchestr`: context, idle_since, user_message, `/v1/peers`, onStart.
  - `any-mcp`: a pinned git tag with a stdio entrypoint.
- Verify commands are targeted pytest or vitest files plus lint, never the full suite.

## Decisions

### D1: One repo, one image, four entrypoints

`agent-orchestrator` is one uv project and one image whose entrypoint is `orch <cmd>`:
- `api`: FastAPI REST and SSE, serves the SPA; never calls wrappers or Kubernetes.
- `dispatcher`: claims messages and commands, calls wrapper turns, interrupt and compact, and verifies ambiguous sends.
- `ingester`: one SSE subscription per agent; writes events, agent status and turns.
- `reconciler`: renders and applies Kubernetes objects, observes pods, bootstraps sessions, runs checks, executes restart, and runs the pre-discard hook.
- `migrate`: the initContainer.
- `bench`: the CLI, not deployed.

Alternatives: a single process (puts Kubernetes credentials and wrapper tokens behind the no-auth UI process, and is not decentralised), or a repo per service (four pipelines, schema drift). Serves A5, A11.

### D2: Postgres-only coordination and the single-writer rule

Every cross-process signal goes through Postgres:
- `messages`, `commands` and `checks` are SKIP LOCKED queues.
- `clusters.generation > observed_generation` is the reconcile queue.
- NOTIFY channels `cluster_changed`, `agent_free`, `events {cluster_id, max_id}` and `status {cluster_id}` are wake-up hints carrying ids only.

Every loop also polls (dispatcher 2 s, reconciler 10 s), because NOTIFY is lost while a listener is disconnected. "No shared state" is interpreted as one writer per table. The queue tables are the only multi-writer tables, and only through state-machine-guarded UPDATEs (`WHERE status = '<expected>'`). The rule is written into the component README and MEMORY.md.

Alternative: a generic job library (procrastinate), rejected because the claim joins against agent availability. Serves A6, A11.

### D3: Schema 0001 and table writers

Plain SQL migrations, psycopg 3 async, no ORM. Tables and their writers:
- `clusters`: the api. The reconciler writes only `status` and `observed_generation`, and deletes the row when a discard completes (D15).
- `agents`: the reconciler. `last_dispatched_at` is written by the dispatch claim (D23).
- `agent_status`: the ingester.
- `messages`: the api inserts, and cancels while queued; the dispatcher does the rest, including `verifying`, `not_before` and `ambiguous_at` (D24).
- `turns`: the ingester.
- `events`: the ingester. UNIQUE(agent_id, session_id, seq); the global bigserial id is the SSE id and the page cursor.
- `commands`: the api inserts. The dispatcher claims interrupt and compact, and also inserts `rebootstrap` after a wrapper 404. The reconciler claims restart and rebootstrap.
- `checks`: the api inserts; the reconciler does the rest.

Events are kept for the cluster's lifetime and deleted by cascade when the discard deletes the cluster row. There is no partitioning and no purged or deleted_at column. Serves A11, A25.

### D4: Round-robin to the agent free the longest

The dispatcher claims the oldest dispatchable queued message of a cluster (`not_before` null or past) under a per-cluster advisory lock. It then:
- picks the ready, idle agent of that cluster with the oldest `free_since` whose `free_since` is newer than `agents.last_dispatched_at` (this closes the race between a 202 and the ingester seeing busy)
- locks it SKIP LOCKED, writes `last_dispatched_at` and marks the message `dispatching`
- commits, then POSTs the turn with `metadata {orch_message_id, orch_attempt}`

Outcomes are mapped by D23 and D24. A `target_agent_id` restricts the pick. Dispatch is FIFO per cluster: a head message waiting out its backoff holds its cluster's queue (my call). Completion order is not guaranteed. Serves A6, A15.

### D5: Store events, do not proxy them

The ingester holds one SSE subscription per agent session with `Last-Event-ID = agent_status.last_seq`, reconnecting with 1-30 s backoff. On attach it reads the snapshot (state, `idle_since`, context) and `GET /v1/peers`.

Inserts are `ON CONFLICT DO NOTHING` (at-least-once delivery, exactly-once storage), and a seq hole after resume writes a synthetic `gap` row. Projections:
- `session_state` sets `agent_status.state` and `free_since`, and NOTIFYs `agent_free` and `status`.
- `context` events set the context columns.
- Turn events project into `turns`.

Wrapper callbacks are not used. Serves A2.

### D6: Kubernetes model per cluster

Everything lives in the one namespace `settings.namespace` (`ORCH_NAMESPACE`, default `agents`; the chart sets it to the release namespace; D26). Every object of cluster `<slug>` is labelled `agents.szymonrichert.pl/cluster=<slug>` and `app.kubernetes.io/managed-by=agent-orchestrator`. The objects:
- PVC `agent-<slug>-workspace`: RWX, `rook-ceph-rwx`.
- Secret `agent-<slug>-ccw`.
- ConfigMap `agent-<slug>-config`: ccw `config.yaml` and the onStart script `on-start.sh`.
- Headless Service `agent-<slug>`: publishNotReadyAddresses.
- StatefulSet `agent-<slug>`:
  - Parallel, `imagePullSecrets: [regcred]` (omitted when the setting is empty), uid/fsGroup 1000
  - a `/healthz` startupProbe sized to the onStart timeout, plus `/healthz` and `/readyz` probes
  - PVC subPath `workdir` at `/workdir`, shared: sessions and check Jobs both work in `/workdir/<spec.workdir>` (D27)
  - `subPathExpr: sessions/$(POD_NAME)` at `/sessions`, per pod
  - emptyDirs `/opt/mise` and `/opt/any-mcp`
  - `CLAUDE_CODE_OAUTH_TOKEN` from the chart's Claude Secret (`ORCH_CLAUDE_SECRET_NAME`)

One pod runs one session (`max_sessions: 1`), and a single pod is a cluster of 1 (user answers Q2, Q3).

Reconcile is level-triggered (every 10 s, and on `cluster_changed`): render, server-side apply (field manager `agent-orchestrator`, force), prune labelled objects not desired, upsert `agents` from pods, bootstrap or adopt sessions, set `observed_generation`.

Rejected alternatives: bare pods, a Deployment (no per-pod DNS), a CRD plus operator, volumeClaimTemplates, imperative create and delete. Serves A4, A8.

### D7: Per-cluster derived tokens

`CCW_AUTH_TOKEN = HMAC-SHA256(master, "auth:" + cluster_id)` and `CCW_PEER_TOKEN = HMAC-SHA256(master, "peer:" + cluster_id)`, hex encoded, so they always differ and exceed 16 characters. The master key is one orchestrator Secret: chart `masterKey.existingSecret` or `masterKey.value`, SOPS-encrypted in agents-helmfile. The dispatcher, ingester and reconciler derive the same tokens, so no token is stored and no process reads Secrets back. One token per cluster is one trust domain, matching the shared peer token. Serves A7.

### D8: Rendered wrapper config, validated in tests

The ConfigMap's `config.yaml` sets:
- `server.auth_token: ${CCW_AUTH_TOKEN}`
- `paths {workdir_root: /workdir, sessions_root: /sessions}`
- `claude`:
  - `env`: the OAuth token and `disable_autoupdater`
  - `model` and `effort`
  - `permissions.deny: [EnterPlanMode, ExitPlanMode, AskUserQuestion]`
  - `mcp_servers.any-mcp {type: stdio, command: /opt/any-mcp/bin/any-mcp, args: [--config, /opt/any-mcp/etc/any-mcp.yaml]}`
- `hooks.onStart` running the rendered `on-start.sh` (D16)
- `sessions {max_sessions: 1, resume_on_start: true, idle_timeout_seconds: 0, ask_user_question: deny}`
- `prompts.system_append`: the ask-in-writing instruction. When the agent needs a decision or information from the user, it asks in writing in its reply, as a numbered list of questions, each followed by its recommended answer, worded so that "yes" accepts it.
- when `spec.peers`: `peers {enabled, name: ${POD_NAME}, advertise_url: ${CCW_PEER_URL}, token: ${CCW_PEER_TOKEN}, static: [every ordinal URL]}`

AskUserQuestion is disabled twice. `ask_user_question: deny` refuses a call, and `permissions.deny` keeps the tool out of the session, so an agent never blocks on a dialog nobody answers. This is the user's answer to Q11.

A test validates the rendered YAML with `claude_code_wrapper.config.load_config`, from a dev dependency pinned by git to the wrapper sha of the configured agent image, so config drift fails CI. Serves A4, A7, A9, A26.

### D9: RBAC limited to the reconciler

A namespaced Role in `agents` (D26) is bound only to the reconciler's ServiceAccount. Its verbs:
- statefulsets, services, configmaps and persistentvolumeclaims: get, list, watch, create, patch, delete
- secrets: create, patch and delete only. Names are deterministic, so the reconciler can never read the orchestrator's or any other Secret.
- pods: get, list, watch, delete
- jobs: get, list, watch, create, delete
- pods/log: get
- never pods/exec

The other three Deployments run with `automountServiceAccountToken: false`. The verb list is documented in README.md and rendered by the chart (`chart/agent-orchestrator/templates/role.yaml`, D28), and the kind e2e installs that chart, which proves the list is sufficient. Serves A13, A20.

### D10: Checks run as Jobs mounting the cluster PVC

`POST /clusters/{id}/checks {command}` queues a check. The reconciler runs it as a Job in `agents` mounting the cluster PVC at `/workdir`, then records `exit_code` and a bounded `log_tail` from pods/log. Bench verify steps are checks. Serves A10.

### D11: Headless API v1 over REST and SSE

`/api/v1`, JSON, errors `{"error": {"code", "message"}}` as in the wrapper. Routes:
- clusters: `GET|POST /clusters`, `GET|PATCH|DELETE /clusters/{id}`. DELETE is the discard (D15); there is no purge parameter.
- agents: `GET /clusters/{id}/agents`; `POST /agents/{id}/interrupt|compact|restart` returning 202.
- messages:
  - `POST /clusters/{id}/messages {text, target_agent_id?}` returns 202.
  - list, and get with status, attempts, next attempt time, turn status and final_text.
  - cancel while queued, and retry a failed message.
- events: `GET /clusters/{id}/events?before_id=&after_id=&limit=&agent_id=&types=`.
- SSE: `GET /clusters/{id}/events/stream` (id = events.id, honours Last-Event-ID) and `GET /stream` (cluster_status, agent_status and message_status deltas).
- checks, `GET /meta` and `/api/v1/openapi.json`.

The URL major is `/v1`, additive-only within v1, guarded by a README parity test. SSE is chosen over WebSocket because the channel is one-directional and the resume semantics match the wrapper. Serves A5.

### D12: Frontend stack and ported theme

`frontend/` uses React 19.3, MUI 9.5, Vite 8.3, vitest 5, an ESLint 10 flat config, strict TypeScript and npm. Ported from `ros2-lerobot-sverve-platform/nodes/web_ui/frontend/src`:
- `theme.ts` TOKENS and overrides (dark, flat, one grey accent)
- `main.tsx` and `index.css`
- `layout/useLayout.ts` and `layout/ConfirmDialog.tsx`
- `components/StatusItem.tsx`
- `layout/designRules.ts` and its test
- the Virtuoso ChatLog configuration
- the socket backoff logic, re-targeted to EventSource

State is hand-rolled reducers. API types come from `openapi-typescript` over the committed `openapi.json`, with a CI drift check. Current majors (user answer Q6). Serves A3.

### D13: Ribbon indicator

Each cluster row shows:
- a working mark when any agent is busy, and waiting otherwise
- `ready/replicas`
- a determinate circular gauge whose value is the maximum `used_percentage` over its agents (user answer Q9)

An expandable agent row shows the agent's own state and gauge. The gauge's denominator is the full model window (the statusline contract), and it draws a tick at the auto-compact point. A null context draws as an empty ring with an "unknown" label (user answer Q10). Serves A1.

### D14: Chat with smart loading

`chatModel.ts` reduces stored events into items: user_message, assistant, thinking (collapsed), tool (paired by tool_use_id), denied, turn_end, error, peer and gap. Rows carry the agent ordinal, with filter chips.

`useClusterChat` loads the newest 200 on open, pages older by `before_id` when the start is reached, appends live SSE events (resuming by Last-Event-ID) and trims the window. ChatLog uses react-virtuoso with `firstItemIndex` prepend and `followOutput`. Serves A2.

### D15: Discard deletes everything, after an optional pre-discard hook

`DELETE /clusters/{id}` sets `desired = deleting` and returns 202; a repeated DELETE is also 202. On a deleting cluster the reconciler does the following, in order:
1. When a pre-discard hook is configured and the cluster status does not yet record `discard_hook_delivered`, it streams the cluster's full history as JSONL to the hook. Record kinds: `cluster`, `agent`, `message`, `turn`, `event` and `check`, in id order. On success it records `discard_hook_delivered` in the cluster status.
2. It deletes every labelled object, including the PVC, and the Secret by name.
3. Once no labelled object remains, it deletes the cluster row, and the cascade removes messages, events, turns, commands and checks.

The hook:
- Sources: `spec.discard_hook_url` (a webhook) wins over the settings `ORCH_DISCARD_HOOK_URL` or `ORCH_DISCARD_HOOK_COMMAND` (at most one of the two). The default is none.
- A command gets the JSONL on stdin plus `ORCH_CLUSTER_ID` and `ORCH_CLUSTER_SLUG`, and succeeds on exit 0.
- A webhook gets `POST` with `Content-Type: application/x-ndjson` and the headers `X-Orch-Cluster-Id` and `X-Orch-Cluster-Slug`, and succeeds on a 2xx.
- Both are bounded by `ORCH_DISCARD_HOOK_TIMEOUT_SECONDS`.
- A failed hook deletes nothing. It records `discard_hook_failed: <reason>` in the status and is retried on later reconciles with backoff, so a configured export is never skipped.
- Delivery is at least once.
- A command hook comes only from settings, because the API has no auth and a spec command would run inside the reconciler that holds the Kubernetes credentials (my call).

The UI discard dialog names the PVC and history deletion and the hook when one is configured, and it needs the slug typed to confirm. This is the user's answer to Q4. Serves A4, A25.

### D16: any-mcp installed by a rendered onStart hook

There is no derived agent image. Agent pods run the claude-code-wrapper image named by `ORCH_AGENT_IMAGE`. For every cluster, the renderer writes `on-start.sh` into the ConfigMap, and `hooks.onStart` runs it with `blocking: true`, `on_error: deny` and `timeout_seconds` = `ORCH_ON_START_TIMEOUT_SECONDS` (600). The wrapper fires onStart once per process start, before the service listens, joins peers or resumes a session (contract `wrapper-on-start-hook`). The script (POSIX sh, `set -eu`):
1. Unless `/opt/any-mcp/.ref` already holds the pinned ref, it creates `/opt/any-mcp` with `python3 -m venv` and installs `any-mcp @ git+<ORCH_ANY_MCP_REPO>@<ORCH_ANY_MCP_REF>` into it.
2. It writes the resolved any-mcp config as JSON to `/opt/any-mcp/etc/any-mcp.yaml`, through a quoted heredoc. The config is `spec.any_mcp_config`, else the settings file, else `{}`; JSON is valid YAML (contract `any-mcp-install`).
3. It runs `/opt/any-mcp/bin/any-mcp --help` as a smoke check.

`/opt/any-mcp` is an emptyDir, so a container restart reuses the venv, and a new pod reinstalls it at the pinned tag. A failed install exits the wrapper non-zero, so the pod restarts and the failure is visible.

Rejected:
- a derived image (the user's answer to Q8)
- `init.setup_commands` (they run per created session and never on resume)
- onCreate (it fires after claude has started its MCP servers)
- `uvx` at session start (network on every session, unpinned resolve)

Serves A9.

### D17: Image, chart and CI

GitHub Actions on ubuntu-latest:
- Python lint and tests; frontend `npm ci`, lint, test, build and the `check:api` drift check.
- On main, build and push `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>` (multi-stage: the node build goes into the Python image's static dir), with a `--help` smoke step. This is the only image built here (user answer Q12, as changed by Q8).
- The chart job runs `helm lint` and the chart pytest files, then publishes the chart (D28).
- Then the kind e2e job runs.

Serves A13, A27.

### D18: Bench CLI for the experiment

`orch bench spec.yaml` creates one cluster per arm `{replicas, peers}` (for example 1/off, 3/off, 3/on). It runs each task `{prompt, verify}` n times through the public API, with an optional chaos step (`POST /agents/{id}/restart` mid-run), and runs verify as a check. It records wall time from queued to completed, failed turns, tokens (from turns usage) and the verify pass rate, as JSONL plus a summary table. At the end it discards its clusters unless `--keep`. It talks only to the public API. Serves A10.

### D19: Testing strategy

- Unit tests cover the renderer (golden objects plus ccw config validation), tokens, the SSE parser, the chat reducer, pick ordering, the backoff schedule, the discard hook and the chart templates (pytest over `helm template`).
- Postgres tests use a real Postgres through testcontainers (docker), including two concurrent dispatchers and NOTIFY loss recovered by polling.
- Wrappers are an in-process fake (`tests/fakes/fake_wrapper.py`). A contract test pins its behaviour and also runs against the real wrapper image with the wrapper's `tests/fake_claude` (integration marker).
- Kubernetes loops use a `KubeApi` protocol with an in-memory fake.
- The kind e2e (`mise run test:e2e`) installs the chart into namespace `agents` with a test agent image (the wrapper plus fake_claude). It creates a 2-replica cluster through the API and sends 3 messages. It asserts round-robin by `free_since`, the merged event stream, any-mcp installed by onStart, and that discard removes every labelled object and the history while leaving the chart's own objects alone.

Serves A12, A13.

### D20: Singletons, migrations and shutdown

The ingester and reconciler each hold a Postgres advisory lock for their lifetime. A second replica waits as a hot standby and takes over when the lock frees; failover is hardened by D25. The api and dispatcher scale freely. `orch migrate` runs the SQL files in order under an advisory lock, recording applied versions, idempotently. Every entrypoint stops cleanly on SIGTERM: loops finish the current iteration, open streams close and the pool closes. Serves A11.

### D21: New component repo

The code lives in a new submodule `code/agent-orchestrator` with the public origin `github.com/szymonrychu/agent-orchestrator`. The orchestrator creates it after the gate and before the run: the repo, the `main` branch, the Harbor push secrets and the submodule pointer. The component has its own README.md (the spec), MEMORY.md and ROADMAP.md. Serves A13.

### D22: Source allowlist and ClusterSpec hardening

In-cluster callers (LLM-driven agent pods and check Jobs, now in the same namespace) can reach the api Service, and flannel enforces no NetworkPolicy. The api therefore enforces a source-address allowlist on the direct socket peer:
- `ORCH_ALLOWED_CIDRS`, default 192.168.1.0/24. ingress-nginx is hostNetwork, so ingress traffic arrives from node IPs and the pod CIDR is refused.
- `Forwarded` and `X-Forwarded-For` are ignored, and uvicorn runs without proxy headers.
- `/healthz` and `/readyz` are exempt; everything else is 403 `forbidden`.

`ClusterSpec` is hardened at the same time:
- `image` comes only from a server-side allowlist: `ORCH_AGENT_IMAGES` plus the configured agent image.
- `env` rejects `CCW_*`, `POD_NAME`, `CLAUDE_*`, `ANTHROPIC_*`, `*_PROXY` and `*_BASE_URL` keys. The renderer sets `claude.passthrough_env` to the accepted env names, so they reach the claude child, whose environment is an allow-list.
- `any_mcp_config` is validated against the real any-mcp config model.
- `discard_hook_url` must be an http or https URL.
- Replicas, PVC size and cluster count are capped from settings (`ORCH_MAX_REPLICAS`, `ORCH_MAX_PVC_SIZE`, `ORCH_MAX_CLUSTERS`).

Rejected: a NetworkPolicy, because flannel does not enforce it. Serves A14.

### D23: Dispatch correctness: release, one clock, claim write, FIFO, head-of-line

(a) Release on every non-accept. The reservation is released on every outcome where no turn was accepted. The claim stores the agent's previous `last_dispatched_at`, and `release_agent` restores it after 409, unavailable, gone, config error, rejected and requeue. A send verified as not started (D24) clears the reservation only when `last_dispatched_at` still equals the message's `dispatched_at`. An accepted send keeps the reservation until a newer `free_since`.

(b) One clock. Postgres `now()` is used for every comparison. The ingester sets `free_since` from the database clock at the moment it records a transition into idle. The wrapper's `idle_since` is stored for display only.

(c) The claim write. The claim transaction writes `agents.last_dispatched_at`, the row change that forces READ COMMITTED to recheck the predicate, and the pick reads that column. A forced-interleaving test with two connections proves it.

(d) Targeted messages. A targeted message whose target is busy is skipped, and one whose target is gone fails with `target_gone`.

(e) FIFO. A per-cluster transaction-level advisory lock in the claim keeps per-cluster FIFO under concurrent dispatchers.

The wrapper client maps every status:
- 202: sent
- 409: busy
- 404 or 410: gone
- 401 or 403: config error
- 413 or 422: rejected
- 5xx and connect errors: unavailable
- a read timeout or a reset after the request was written: ambiguous

Serves A15, A16, A23, A24.

### D24: Automatic retry with backoff; ambiguous sends verified before any retry

Definite non-accepts are retried automatically, with bounded attempts and backoff:
- Busy (409) is requeued immediately, with no attempt counted.
- Unavailable (5xx, connect errors) and gone (404, 410; also enqueues `rebootstrap`) count an attempt. While `attempts < spec.max_attempts` (default 5, 1-10), the message returns to `queued` with `not_before = now() + least(ORCH_RETRY_BACKOFF_BASE_SECONDS * 2^(attempts-1), ORCH_RETRY_BACKOFF_MAX_SECONDS)` (defaults 2 s and 60 s). At max it becomes `failed`.
- Config error (401, 403) and rejected (413, 422) are permanent: they fail at once, because a resend cannot succeed (my call).

An ambiguous outcome (a read timeout or reset after the request was written), and a `dispatching` row past the stale cutoff, move the message to `verifying` with `ambiguous_at = now()`. The agent stays reserved. The dispatcher's verifier then asks the original agent's wrapper whether the turn started:
- It reads the snapshot. When `current_turn_id` is set, it fetches that turn record; otherwise it fetches the records of the newest 10 turns of `GET /v1/sessions/{id}/turns`.
- It looks for a turn whose `metadata.orch_message_id` is this message.
- Found: the message becomes `sent` with that turn_id.
- Not found, while the wrapper answers and at least `ORCH_AMBIGUOUS_SETTLE_SECONDS` (60, at least twice the send timeout) have passed since `ambiguous_at`: a definite non-accept. The reservation is cleared, an attempt is counted, and the message is requeued with backoff, or fails at max.
- Unreachable wrapper, missing session or still inside the window: it checks again on the next pass. After `ORCH_AMBIGUOUS_DEADLINE_SECONDS` (600) with no definite answer, the message becomes `failed` with reason `ambiguous`, and only the user's explicit Retry re-sends it.

The send timeout (`ORCH_WRAPPER_SEND_TIMEOUT_SECONDS`, 15 s) stays at most half of the dispatching stale cutoff (60 s). The dispatching row heartbeats while a send is in flight, and the stale rule uses `coalesce(heartbeat_at, dispatched_at)`. This is the user's answer to Q5. Serves A15, A18.

### D25: Singleton failover

The lock connection of the ingester and reconciler uses libpq keepalives and `tcp_user_timeout`. A heartbeat every few seconds (`ORCH_LOCK_HEARTBEAT_SECONDS`) verifies the lock is still held, and loss exits non-zero so Kubernetes restarts the pod. A test blackholes the holder's connection. Serves A17.

### D26: One namespace, label-partitioned clusters, reserved names, no Secret reads

Everything lives in the one namespace `agents` (user answer Q14): the orchestrator's Deployments, Service, settings ConfigMap and Secrets, the database when the chart's CNPG feature is on, and every agent cluster. Clusters are told apart by the label `agents.szymonrichert.pl/cluster=<slug>`. There is no `ORCH_CLUSTERS_NAMESPACE`. Guards that keep the reconciler off the orchestrator's own objects:
- Object names use the reserved prefix `agent-<slug>`, and the slugs `orchestrator` and `orchestrator-*` are rejected. The chart's own `agent-orchestrator-*` names therefore never collide with a cluster's.
- The reconciler refuses to apply over, or prune, any object lacking both the managed-by and the cluster label, and it deletes pods only by its cluster's selector.
- The reconciler's Role grants secrets only create, patch and delete (no get, list or watch). It deletes a cluster Secret by its deterministic name `agent-<slug>-ccw`, never lists Secrets, and so can never read the master key, the Claude token or the database credentials.

The namespace needs `regcred` (agents-helmfile) and the Claude Secret (rendered by the chart). Serves A19, A20.

### D27: Session adoption and one workdir path

Bootstrap:
- It adopts only sessions in state creating, ready or busy.
- Stopped or failed sessions with a transcript are resumed through `POST .../resume`.
- Anything else gets a new session.
- A 404 on a turn submit makes the dispatcher enqueue a `rebootstrap` command, so the reconciler clears the agent's session and bootstraps again.

Sessions are created with the workdir name `spec.workdir` (the wrapper resolves `/workdir/<name>`). The renderer exposes `workdir_path(spec)` and `workdir_mount(spec)`, which the StatefulSet and the check Jobs use (the Jobs work in `/workdir/<spec.workdir>`). Tests in all three tasks pin this. Serves A21, A22.

### D28: Helm chart in the repo

`chart/agent-orchestrator` starts from `helm create`, to keep Helm's standard layout, helpers and labels, and is then adapted:
- `Chart.yaml`: type application, `version` 0.1.0, `appVersion` = the image tag.
- `values.yaml`: no homelab defaults.
- `_helpers.tpl`, and a settings ConfigMap holding the `ORCH_*` env. `ORCH_NAMESPACE` is the release namespace; `agentImage` is required; extra `ORCH_*` keys go in `env`.
- Secrets: the master key, the Claude token, and the Postgres URL when given by value. Each one can be replaced by an `existingSecret`.
- A Postgres connection is required by default: `postgres.url`, or `host`/`port`/`database`/`user`/`password`, or `postgres.existingSecret`. A missing connection fails `helm template` with a message.
- CNPG is optional: `cnpg.enabled: false` by default. When on, the chart renders a `postgresql.cnpg.io/v1` Cluster, `cnpg.backup` passed through verbatim (user answer Q13), and takes `ORCH_DATABASE_URL` from the CNPG app Secret key `uri`.
- Four component Deployments (api, dispatcher, ingester, reconciler), each with the `orch migrate` initContainer, and the api Service. The `helm create` test-connection hook is kept and points at `/healthz`. The HPA is dropped, because two components are singletons (my call).
- ServiceAccounts: the reconciler's own, plus a default one with no token mounted. The reconciler Role and RoleBinding (D9).
- Ingress: optional (`ingress.enabled: false`), with className, hosts, tls and annotations all from values.

Tests are pytest over `helm template` (`tests/test_chart_*.py`), with Helm installed through mise. CI runs `helm lint` and those tests. On a `vX.Y.Z` tag, and on main, CI publishes to `oci://harbor.szymonrichert.pl/charts` with immutable versions:
- A tag publishes `X.Y.Z`, which must equal Chart.yaml's `version`.
- Main publishes `<version>-main.<sha7>`.
- `appVersion` is the image sha7.
- CI refuses to push a version that already exists.

The agents-helmfile epic consumes the chart, settings env and image contracts. Serves A27.

## Research

| Lens | Ran or skipped | Adopted ideas | Rejected ideas |
|---|---|---|---|
| research-code-internal (claude-code-wrapper) | ran (brief-wrapper.md, plus the gate-answer probe of hooks and turns) | per-pod `sessions_root` (manager.py:1251-1255); peers seed list via pod DNS (peers.py:92, README:3262); `claude.mcp_servers` stdio entry (config.py:194); turn `metadata` on the record for the ambiguity check (api/turns.py:45, turns.py:105); `permissions.deny` and `system_append` for Q11 (config.py:148, README:2600) | deriving context % from usage events plus a model table (router.py:257); onCreate or `init.setup_commands` for the any-mcp install (manager.py:474-482, 594-605) |
| research-code-internal (ros2 web_ui) | ran (brief-ui.md) | theme.ts TOKENS, designRules test, Virtuoso ChatLog config, agentSocket backoff | WebSocket transport (server.py:1285), ESLint 8 / Vite 5 / MUI 6 |
| research-code-internal (infrastructure) | ran (brief-infra.md) | `rook-ceph-rwx` default SC, `regcred` per namespace, CNPG cluster CR and backup values, chart tests as pytest over `helm template` (charts/tests), Harbor OCI chart push with immutable versions | redis broker pattern (ai/buzz-redis); homelab ingress defaults in the chart |
| research-docs | ran (brief-docs.md) | statusline `context_window.used_percentage` as the gauge source, full-window denominator (code.claude.com/docs/en/statusline) | transcript usage parsing (undocumented schema) |
| research-code-external | ran inside the architect pass (design-orchestrator.md sources) | FastAPI native SSE (fastapi.tiangolo.com/tutorial/server-sent-events), lightkube server-side apply, `helm create` scaffold | procrastinate job library |
| research-papers | skipped: no algorithmic question; the experiment is the bench | none | none |

## Research inputs

| Source | Entry | Lands in |
|---|---|---|
| brief-docs.md Plan inputs: Pins | mcp/fastmcp pins | rejected: any-mcp epic owns the library choice |
| brief-docs.md Plan inputs: Library decision | FastMCP vs mcp | rejected: any-mcp epic |
| brief-docs.md Plan inputs: Notifications | list_changed on both eras | rejected: any-mcp epic |
| brief-docs.md Plan inputs: Tool list shape | deterministic tool list | rejected: any-mcp epic |
| brief-docs.md Plan inputs: Entrypoint | stdio, logs to stderr, exit on EOF | k8s-object-renderer (stdio entry, onStart smoke `any-mcp --help`), kind-e2e |
| brief-docs.md Plan inputs: Claude Code install | stdio entry written by the wrapper, no committed `.mcp.json` approval | k8s-object-renderer |
| brief-docs.md Plan inputs: Gauge | statusline used_percentage, null as unknown, reset on compact, full-window denominator | ingester, fe-context-gauge |
| brief-docs.md Plan inputs: Open gaps | MCP stdio behaviour checks | rejected: any-mcp epic |
| brief-wrapper.md section 6 | context, idle_since, backward history, user_message, peers view gaps | rejected: wrapper epic claude-code-wrapper-orchestr (consumed via contracts) |
| brief-wrapper.md Unknowns | shared `sessions_root` leaks sessions | k8s-object-renderer (`subPathExpr: sessions/$(POD_NAME)`) |
| brief-wrapper.md section 3 | peers need unique name, advertise_url, shared token != auth_token | k8s-object-renderer, cluster-token-derivation |
| gate probe: wrapper hooks | no instance-start hook exists (config.py:419-439, manager.py:474-482, 594-605) | wrapper epic task on-start-instance-hook; k8s-object-renderer consumes it |
| gate probe: wrapper turns | client metadata persisted on the turn record (api/turns.py:45, turns.py:105) | wrapper-client-and-sse, fake-wrapper-contract, ambiguous-send-verifier |
| brief-infra.md section 4 | orchestrator-created pods need `imagePullSecrets: [regcred]` | k8s-object-renderer |
| brief-infra.md section 1 | chart tests as pytest over helm template, OCI push to Harbor charts, immutable versions | helm-chart-scaffold, helm-chart-ci-publish |
| brief-infra.md section 2 | helmfile release, SOPS, IP-restricted ingress annotations | rejected: epic agents-helmfile (values only; the chart keeps annotations configurable) |
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
| D9 RBAC limited to the reconciler | reconciler-loop, helm-chart-rbac-and-ingress, kind-e2e |
| D10 Checks run as Jobs mounting the cluster PVC | check-jobs |
| D11 Headless API v1 over REST and SSE | api-clusters-and-agents, api-messages-and-commands, api-events-and-streams, readme-api-and-openapi |
| D12 Frontend stack and ported theme | fe-scaffold, fe-theme-port, fe-api-client-and-stream |
| D13 Ribbon indicator | fe-context-gauge, fe-shell-and-ribbon |
| D14 Chat with smart loading | fe-chat-model, fe-chat-log-paging, fe-composer-and-queue-strip |
| D15 Discard deletes everything, after an optional pre-discard hook | clusters-repository, migrations-and-schema, settings-model, reconciler-loop, discard-hook-and-export, api-clusters-and-agents, fe-cluster-form, bench-cli |
| D16 any-mcp installed by a rendered onStart hook | settings-model, k8s-object-renderer, container-images-ci, kind-e2e |
| D17 Image, chart and CI | spa-serving-and-dockerfile, container-images-ci, helm-chart-ci-publish |
| D18 Bench CLI for the experiment | bench-cli |
| D19 Testing strategy | fake-wrapper-contract, kind-e2e |
| D20 Singletons, migrations and shutdown | entrypoints-and-singleton, migrations-and-schema |
| D21 New component repo | scaffold-repo-and-cli, settings-model |
| D22 Source allowlist and ClusterSpec hardening | scaffold-repo-and-cli, settings-model, clusters-repository, api-clusters-and-agents, k8s-object-renderer, entrypoints-and-singleton, container-images-ci, readme-api-and-openapi, kind-e2e |
| D23 Dispatch correctness | migrations-and-schema, dispatch-queue-sql, ingester, wrapper-client-and-sse, fake-wrapper-contract, dispatcher-loop, api-messages-and-commands |
| D24 Automatic retry with backoff; ambiguous sends verified before any retry | settings-model, migrations-and-schema, clusters-repository, dispatch-queue-sql, wrapper-client-and-sse, fake-wrapper-contract, dispatcher-loop, ambiguous-send-verifier, api-messages-and-commands, fe-composer-and-queue-strip |
| D25 Singleton failover | settings-model, entrypoints-and-singleton |
| D26 One namespace, label-partitioned clusters, reserved names, no Secret reads | settings-model, clusters-repository, k8s-object-renderer, reconciler-loop, check-jobs, helm-chart-rbac-and-ingress, kind-e2e |
| D27 Session adoption and one workdir path | k8s-object-renderer, session-bootstrap, check-jobs, wrapper-client-and-sse, fake-wrapper-contract, dispatch-queue-sql, dispatcher-loop, migrations-and-schema |
| D28 Helm chart in the repo | helm-chart-scaffold, helm-chart-config-postgres, helm-chart-deployments, helm-chart-rbac-and-ingress, helm-chart-ci-publish, kind-e2e |

## Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| `orch-cli` | scaffold-repo-and-cli | entrypoints-and-singleton, bench-cli | `src/agent_orchestrator/cli.py` |
| `settings` | settings-model | cluster-token-derivation, k8s-object-renderer, api-clusters-and-agents, entrypoints-and-singleton, clusters-repository, dispatcher-loop, ambiguous-send-verifier, discard-hook-and-export | `src/agent_orchestrator/settings.py` |
| `schema-v1` | migrations-and-schema | clusters-repository, dispatch-queue-sql, events-store, reconciler-loop, ingester, api-clusters-and-agents, discard-hook-and-export | `src/agent_orchestrator/db/migrations/0001_init.sql` |
| `pg-fixture` | migrations-and-schema | clusters-repository, dispatch-queue-sql, events-store, reconciler-loop, ingester, dispatcher-loop, api-clusters-and-agents, ambiguous-send-verifier, discard-hook-and-export | `tests/conftest.py` |
| `cluster-spec` | clusters-repository | k8s-object-renderer, api-clusters-and-agents, discard-hook-and-export | `src/agent_orchestrator/spec.py` |
| `queue-sql` | dispatch-queue-sql | dispatcher-loop, ambiguous-send-verifier, reconciler-loop, check-jobs, api-messages-and-commands | `src/agent_orchestrator/db/queue.py` |
| `events-repo` | events-store | ingester, api-events-and-streams | `src/agent_orchestrator/db/events.py` |
| `wrapper-client` | wrapper-client-and-sse | fake-wrapper-contract, ingester, dispatcher-loop, ambiguous-send-verifier, session-bootstrap | `src/agent_orchestrator/wrapper/client.py` |
| `fake-wrapper` | fake-wrapper-contract | ingester, dispatcher-loop, ambiguous-send-verifier, session-bootstrap, kind-e2e | `tests/fakes/fake_wrapper.py` |
| `cluster-tokens` | cluster-token-derivation | k8s-object-renderer, ingester, dispatcher-loop, session-bootstrap | `src/agent_orchestrator/tokens.py` |
| `k8s-render` | k8s-object-renderer | reconciler-loop, check-jobs | `src/agent_orchestrator/k8s/render.py` |
| `kube-api` | reconciler-loop | check-jobs, entrypoints-and-singleton, discard-hook-and-export | `src/agent_orchestrator/k8s/kube.py` |
| `agents-repo` | reconciler-loop | session-bootstrap, check-jobs | `src/agent_orchestrator/db/agents.py` |
| `api-app` | api-clusters-and-agents | api-messages-and-commands, api-events-and-streams, readme-api-and-openapi, spa-serving-and-dockerfile, entrypoints-and-singleton | `src/agent_orchestrator/api/app.py` |
| `openapi-v1` | readme-api-and-openapi | fe-api-client-and-stream, bench-cli | `openapi.json` |
| `fe-theme` | fe-theme-port | fe-context-gauge, fe-shell-and-ribbon, fe-chat-log-paging, fe-cluster-form | `frontend/src/theme.ts` |
| `fe-api` | fe-api-client-and-stream | fe-shell-and-ribbon, fe-chat-model, fe-chat-log-paging, fe-composer-and-queue-strip, fe-cluster-form | `frontend/src/api/client.ts` |
| `context-gauge` | fe-context-gauge | fe-shell-and-ribbon | `frontend/src/ribbon/ContextGauge.tsx` |
| `chat-model` | fe-chat-model | fe-chat-log-paging | `frontend/src/chat/chatModel.ts` |
| `helm-render` | helm-chart-scaffold | helm-chart-config-postgres, helm-chart-deployments, helm-chart-rbac-and-ingress, helm-chart-ci-publish | `tests/helm_render.py` |
| `agent-orchestrator-chart` | helm-chart-scaffold | helm-chart-config-postgres, helm-chart-deployments, helm-chart-rbac-and-ingress, helm-chart-ci-publish, kind-e2e | `chart/agent-orchestrator/values.yaml` |

## Cross-epic contracts

Registered in `docs/plans/contracts.json`:

| Contract | Owner epic | Consumer epic | Used by tasks |
|---|---|---|---|
| `wrapper-idle-since` | claude-code-wrapper-orchestr | agent-orchestrator | wrapper-client-and-sse, ingester |
| `wrapper-context-surface` | claude-code-wrapper-orchestr | agent-orchestrator | wrapper-client-and-sse, ingester |
| `wrapper-user-message-event` | claude-code-wrapper-orchestr | agent-orchestrator | wrapper-client-and-sse, ingester |
| `wrapper-peers-view` | claude-code-wrapper-orchestr | agent-orchestrator | wrapper-client-and-sse, ingester |
| `wrapper-history-backward` | claude-code-wrapper-orchestr | agent-orchestrator | fake-wrapper-contract |
| `wrapper-on-start-hook` | claude-code-wrapper-orchestr | agent-orchestrator | k8s-object-renderer, kind-e2e |
| `any-mcp-cli` | any-mcp | agent-orchestrator | k8s-object-renderer, kind-e2e |
| `any-mcp-config` | any-mcp | agent-orchestrator | k8s-object-renderer, clusters-repository, scaffold-repo-and-cli |
| `any-mcp-release` | any-mcp | agent-orchestrator | settings-model, container-images-ci |
| `any-mcp-install` | any-mcp | agent-orchestrator | k8s-object-renderer |
| `agent-orchestrator-chart` | agent-orchestrator | agents-helmfile | helm-chart-scaffold (owner) |
| `agent-orchestrator-settings-env` | agent-orchestrator | agents-helmfile | settings-model (owner) |
| `agent-orchestrator-image` | agent-orchestrator | agents-helmfile | container-images-ci (owner) |

The Claude Secret is rendered by this repo's chart (`claude.token` or `claude.existingSecret`); agents-helmfile only supplies the SOPS value.

## Review focus

- dispatch-queue-sql and dispatcher-loop: the claim and pick SQL, the reservation rule `free_since > last_dispatched_at`, and the 409/503 transitions. Two concurrent dispatchers must never send one message twice or two messages to one agent.
- ambiguous-send-verifier: a resend happens only after the original wrapper answered, showed no turn with this `orch_message_id`, and the settle window passed. The reservation is cleared only when it still belongs to this message.
- Retry: the backoff schedule, the `not_before` head-of-line hold, and that config error and rejected never retry (D24).
- ingester: resume by Last-Event-ID, gap rows, idempotent insert, and `free_since` only moving on a transition to idle.
- reconciler-loop and discard-hook-and-export:
  - prune only ever touches objects carrying both labels
  - a deleting cluster runs the hook before deleting anything, deletes the PVC, then deletes the row
  - a failed hook deletes nothing
  - the field manager and force apply
- cluster-token-derivation: tokens are never logged, never stored and never returned by the API.
- api: no route reaches Kubernetes or a wrapper; the error shape matches the wrapper; the source allowlist checks the direct peer only (D22).
- Reconciler Role: secrets create, patch and delete only, in namespace `agents` (D26); the chart renders exactly this.
- k8s-object-renderer:
  - the rendered ccw config validates with the pinned wrapper's `load_config`
  - the onStart script is idempotent and writes JSON config through a quoted heredoc
  - AskUserQuestion is denied twice
- Chart: no homelab defaults; a missing Postgres connection fails; immutable versions on publish.

## Left to the builder

- Module layout inside `src/agent_orchestrator/` beyond the files named in tasks, as long as each contract stays defined in its one file.
- Exact pydantic model names, log fields and SQL index names.
- Frontend component internals and copy text within the theme and designRules.
- Bench summary table formatting.
- Chart helper template names and the exact `values.yaml` comments, within the keys of contract `agent-orchestrator-chart`.

## Assumptions and unknowns

- Wrapper image sha: the sha7 that contains the `claude-code-wrapper-orchestr` changes (including onStart) is known only when that epic lands. The agent image default, the e2e test image `BASE_IMAGE` and the ccw dev dependency pin take that sha. Confirm with `git -C code/claude-code-wrapper rev-parse --short=7 origin/main` after it merges.
- any-mcp tag: `vX.Y.Z` (planned v0.1.0) is known only when the any-mcp epic tags its release. `ORCH_ANY_MCP_REF` defaults to it. Confirm with `git ls-remote --tags https://github.com/szymonrychu/any-mcp`.
- Harbor push credentials: at origin creation the orchestrator sets the repo secrets `HARBOR_USERNAME` and `HARBOR_PASSWORD` from the copied `.env`, using the same robot as claude-code-wrapper; that robot also needs push on the Harbor `charts` project. If a value is absent, ask the user. Confirm with `gh secret list -R szymonrychu/agent-orchestrator`.
- Helm 4 OCI login: `helm registry login` against a Harbor robot can fail with 401 on Helm 4. The CI step writes the registry config.json directly when that happens (field note helm4-harbor-robot-login).
- Docker is available locally (docker 29.8.2 probed) and on GitHub ubuntu-latest, so testcontainers Postgres runs in both; kind and helm are installed through mise.
- Agent pods reach github.com: needed for the onStart pip install. The kind e2e on ubuntu-latest has egress.
- Residual double-send window: a turn request held inside the wrapper for longer than `ORCH_AMBIGUOUS_SETTLE_SECONDS` (60 s, four times the send timeout) and accepted after the verifier saw no turn. The wrapper records the turn synchronously before answering 202 (router.py:779), so this needs a stalled wrapper. The settle setting widens the window when needed.

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
- Q13: How are the agent-orchestrator-db CNPG backups configured? [answer: copy the backup configuration of the existing CNPG release (accepted as recommended); the chart's optional cnpg.backup passes it through verbatim]
- Q14: Do agent clusters live in their own namespace `agents-clusters` (configurable `ORCH_CLUSTERS_NAMESPACE`, created by the helmfile release, regcred and the Claude Secret provided there) while the orchestrator runs in `agents`? [answer: everything in namespace agents, clusters told apart by labels; ORCH_CLUSTERS_NAMESPACE and agents-clusters are removed; the reserved agent-<slug> prefix and the refuse-unlabelled apply and prune guard stay (changed by the user, D26)]


## Irreversible operations in scope

- Creating the public GitHub repository `szymonrychu/agent-orchestrator` and pushing to it: covered by the gate approval (D21, 5.1 approved).
- Pushing the image `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>`: Harbor tags are immutable and the tags are commit sha7s, so a push never overwrites. Covered by D17.
- Publishing chart versions to `oci://harbor.szymonrichert.pl/charts/agent-orchestrator`: the versions are immutable (`X.Y.Z` on a tag, `X.Y.Z-main.<sha7>` on main), and CI refuses to push an existing version. Covered by D28.
- Cluster discard deletes the cluster's Kubernetes objects, its PVC with its files, and its whole chat history (messages, events, turns, commands, checks) at run time. This is a product behaviour (D15), safeguarded by the typed-slug confirmation in the UI and by the optional pre-discard hook, which receives the full JSONL export first. A failed hook blocks the deletion.
