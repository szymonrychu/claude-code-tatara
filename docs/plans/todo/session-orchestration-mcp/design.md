# session orchestration mcp design

## Summary

A per-preset (or per-spec) capability flag `session_orchestration`, set by the user only,
gives that session's leader orchestrator MCP tools to manage presets, sessions and cron
schedules it owns, through orchestrator `/agent/v1/orchestration/*` routes (architecture
option A, `.scratchpad/design/session-orchestration-mcp-arch.md`). Writes run only in turns the
user started (UI or Matrix connector origin); every write, refusals included, lands in an
orchestrator audit table; schedule calls are relayed by the orchestrator to a token-protected
relay listener on agents-schedule that records the owner. The plugin release, the pins, the
agents-helmfile values, the live applies and a live smoke are part of the epic.

## Intent and why

User request (2026-10-27, msg 124), verbatim: "Allow for session to orchestrate other sessions
through appropriate mcp tooling. Eg you (matrix connected agent) would be allowed to define
presets, sessions, cronjobs, etc on user request."

The decision is how an agent's authority is bounded when the only proven identity is "session
S's leader is calling" (`api/agent.py:require_agent`). "On user request" must be checked by the
server, because mx-5 takes in text from places other than the user: session messages from any
session's leader, webhook-started content and non-owner senders in Matrix group chats. The user
wants mx-5 to set up presets, sessions and schedules from chat now that the chat path exists.

## Goals

README Goals G1-G7, verbatim there. In short: flagged sessions get the tools (G1), writes only
in user turns (G2), ownership scoping, masking, no escalation and delete safety (G3), audit and
limits (G4), schedules relayed with the agent token kept in the orchestrator (G5), the web
switch and "created by" (G6), released, deployed and live-smoked (G7).

## Non-goals

README Non-goals, verbatim there (architect's do-not-build list plus the noted ideas).

## Anti-goals

- Any session gaining create or delete power without the user flagging its preset (option B's
  failure: silent privilege on upgrade).
- The agent token, or any orchestrator credential usable from an agent pod, reaching
  agents-schedule or any other service.
- A flagged session deleting or editing what the user made in the UI, or deleting itself.
- An agent-written preset, session spec or schedule preset carrying more privilege than the
  caller holds.
- A write that leaves no audit row, or an audit row that disappears with a purged session.
- Live smoke leftovers: a throwaway preset, session or schedule still present after the run.

## Constraints

- Services talk only over HTTP or the queue. Each table has one writer (`orchestration_actions`:
  the orchestrator api; `schedules`: agents-schedule). Queue rows change only through
  status-guarded updates.
- The only stable agent identity is session plus pod IP (`require_agent`); agent pods hold no
  other secret safely.
- Spec is immutable on a running session except `replicas` and `init_scripts`; tool lists are
  fixed at render time.
- No backward-compatibility shims. Python only, except agents-web (TypeScript).
- Ordering: blocked on hive-decoupling, which follows matrix-connector-agent-initi. Shared files
  with Matrix and hive-decoupling: orchestrator `settings.py`, the plugin `__init__.py`,
  `k8s/on_start.py`, the helmfile values. Every version and migration number that depends on
  those epics follows a rule, never a guessed number:
  - orchestrator migration: the next free number in `src/agents_orchestrator/db/migrations/`
    at build time (after slash-commands' 0008 and whatever hive-decoupling adds); written
    `NNNN` in the task files;
  - plugins release: the next minor after the plugins version hive-decoupling leaves pinned in
    the orchestrator (`ORCH_ANY_MCP_PLUGINS_REF`) at build time;
  - agents-schedule migration: the next free number at build time (0002 today; no other epic
    adds one).
- Standing user rules: deploy whenever possible (live applies need no approval); tags are
  irreversible and listed below; send mx-5 one line before an apply restarts agent pods.
- No Docker in agent pods: orchestrator and schedule DB tests run in CI; each task keeps
  non-DB cases where the behaviour allows, so the local verify has signal.

## Decisions

### D1: the capability flag `session_orchestration`
- `SessionSpec.session_orchestration: bool | None = Field(default=None, strict=True)`, sparse
  like `session_messaging` and `kube_access`.
- Settable only through the public API or UI (preset, or spec at create).
- The orchestrator tools render only when the flag is true: `orchestrator_allow` adds
  `ORCHESTRATION_TOOLS`, as with `scale`. `me` gains `orchestration: bool`.
- Alternatives: B superleader-only (every existing superleader silently gains create and delete
  power; conflates messaging with destructive authority), C per-preset grant lists (schema and
  UI editor for a one-user deployment; slug globs break on reuse), D a separate admin token in
  the pod (no pod-IP binding, no caller identity, so no ownership or audit). Why A: the only
  option keeping the identity `require_agent` proves, which makes ownership and an attributable
  audit possible (architect, "Why A").

### D2: who may call, checks in order
Every `/agent/v1/orchestration/*` route: 1. `require_agent`; 2. the flag on the caller's
session, else 403 `not_orchestrator`; 3. `_leads`, else 403 `not_leader`; 4. for writes only,
the user-turn gate (D3). Alternatives: per-route ad-hoc checks (drift between routes). One
FastAPI dependency carries the chain (my call).

### D3: what "on user request" means
- A write is allowed only while the caller's current turn (`agent_status.current_turn_id`,
  same join as `db/queue.py:turn_hop`) was delivered by a message whose origin is in
  `ORCH_ORCHESTRATION_ORIGINS`, default `user,service:agents-matrix-connector`; else 403
  `not_user_turn`.
- Rejected by default: session messages, `service:agents-webhook`, `service:agents-schedule`,
  and turns with no message (background completions, peer sends).
- New column `messages.origin text`, written at insert: `user` on the main port;
  `service:<name>` on the service port (ServiceGate puts the service name in
  `scope["state"]`); `session` in `enqueue_message` when a sender is present. Rows from before
  the migration stay NULL and never pass the gate (my call).
- Reads skip the gate. No two-step confirmation token: an injected model would call both steps.
- Tool descriptions require the agent to name the target to the user before deleting.

### D4: target scope is ownership
- Writes only on objects owned by the caller session: `sessions.created_by_session_id` and
  `created_by_slug`; `presets.created_by_session_id` and `created_by_slug`; schedules
  `owner_session_id` and `owner_slug` (D7). Otherwise 403 `not_owner` (404 on the schedule
  relay, D7).
- Reads cover everything through trimmed views. Sessions: slug, id, preset, state, replicas,
  superleader, orchestration, created_by, no spec. Presets: spec with `env` values,
  `wrapper.hooks.*.secret`, header values and command `env` values masked, except on own
  presets. No copy tool.
- Ownership is by session id; when the owner is deleted, its objects stay and are managed from
  the UI. Alternative: ownership plus "anything the user made" (would let mx-5 delete UI work;
  architect "Changes my mind").
- The public `SessionView` and `PresetView` gain `created_by_slug` (additive; null for objects
  the user made) so agents-web can show it (Q7; my call pending the gate).

### D5: no escalation
- Applies to an agent-written preset spec, an agent-created session spec (from a spec or a
  preset) and the preset named by an agent-written schedule (the relay reads it first).
- `session_orchestration: true` is always refused; `kube_access` or `session_messaging` true
  only if the caller's own session has that same flag. Refusal: 403 `privilege_escalation`.

### D6: delete safety (session delete), checks in order
1. 404 `not_found`; 2. 422 `self_delete`; 3. 403 `not_owner`; 4. 409 `protected_target` (the
target has `session_orchestration` or `session_messaging`); 5. 409 `session_deleting`. Then
`request_delete`. Preset delete: own only; the `PresetDefault` and `LastPreset` refusals still
apply. Owned-session scale goes through `set_replicas`.

### D7: schedules relay through the orchestrator
- Rejected: agents calling agents-schedule directly (CIDR allowlist, no identity, the agent
  token would leave the orchestrator) and orchestrator-side schedule storage (a second owner of
  schedule facts).
- Orchestrator `api/orchestration_relay.py` forwards `/agent/v1/orchestration/schedules*` to
  `{ORCH_SCHEDULE_URL}/relay/v1/schedules*` with `Authorization: Bearer <ORCH_SCHEDULE_TOKEN>`,
  `X-Orch-Session` and `X-Orch-Slug`, never the agent token. Settings both set or both empty;
  both empty gives 503 `schedules_unconfigured`; a connection error, timeout or non-JSON answer
  gives 503 `schedules_unavailable` (my call, mirrors Matrix D2 `chat_unavailable`).
- agents-schedule: a second listener `SCHED_RELAY_PORT` with a bearer gate on
  `SCHED_RELAY_TOKEN_SHA256`, mirroring the connector's agent listener and `ServiceGate`, not
  bound when the hash is empty. Migration (next free number, 0002 today) adds
  `owner_session_id uuid NULL` and `owner_slug text NULL`. Relay routes: list all (read);
  create, update, delete, run-now and runs on owned schedules (404 `not_found` when not owned).
  The UI API is unchanged except the schedule view gains `owner_slug` (additive); UI writes
  never change the owner (my call). The listener contract is committed as
  `openapi-relay.json` and vendored by the orchestrator, like Matrix D16.

### D8: audit trail
- New table `orchestration_actions`; the orchestrator api is the only writer; no FK, so rows
  outlive purged sessions. Columns: `id bigserial`, `caller_session_id`, `caller_slug`,
  `message_id` (the turn's triggering message), `action`, `target_kind`, `target_id`,
  `target_name`, `outcome` (`ok` or the refusal code), `created_at`.
- One row per write call that passed `require_agent`, refusals included, plus one log line in
  the `ServiceGate` style (never a token or a body).
- Read through `GET /api/v1/orchestration/actions` (main port) and the agent tool
  `orchestration_actions` (the caller's own rows).

### D9: rate limits
- Counts from `orchestration_actions`, advisory like cross-session-messaging D10.
- `ORCH_ORCHESTRATION_ACTIONS_PER_HOUR` (30): ok writes per caller, else 429 `rate_limited`.
- `ORCH_ORCHESTRATION_MAX_OWNED_SESSIONS` (5): live owned sessions, else 409 `owned_limit`; the
  global `max_sessions` still applies.
- Schedule side: `SCHED_RELAY_MAX_PER_OWNER` (10) owned schedules, else 409 `owned_limit` (my
  call on the code); `SCHED_RELAY_MIN_INTERVAL_MINUTES` (15): the next three fires must be at
  least this far apart, else 422 `too_frequent`.
- Figures are Q5, pending the gate.

### D10: giving created sessions work
- `session_create` takes an optional `prompt`, queued as a session message: sender the caller,
  hop the caller's hop plus 1, origin `session`.
- The `session_send` rule gains "or one session created the other", so replies can come back to
  a non-superleader owner (Q4, pending the gate).

### D11: tools and release
- Plugin tools (prefix `orchestrator_`, leader-only, rendered only when flagged): presets
  `presets_list`, `preset_get`, `preset_create`, `preset_update`, `preset_delete`; sessions
  `sessions_overview`, `session_create`, `session_scale`, `session_delete`; schedules
  `schedules_list`, `schedule_create`, `schedule_update`, `schedule_delete`, `schedule_run`,
  `schedule_runs`; audit `orchestration_actions`.
- The release is the next minor after the version hive-decoupling leaves pinned. The allow-list
  change lands with the pin in one task, per Matrix D13 (`test_allowed_tools_exist_in_plugin`
  needs both).

### D12: Matrix compatibility
No connector change; the tools are leader-only like the chat tools; a session cannot delete
itself, so mx-5 never releases its own room binding; deleting an owned session bound to a room
releases that binding through the existing Matrix Q10 sweep (intended). The relay module
mirrors `api/chat.py`; `settings.py` gains `ORCH_SCHEDULE_*` next to `ORCH_CHAT_*`.

### D13: one orchestrator migration for the whole epic (my call)
`NNNN_session_orchestration.sql` (next free number at build time) adds `messages.origin`, the
two `created_by_*` pairs and `orchestration_actions` in the first task, so later tasks consume
no migration numbers and cannot collide with another epic's. Alternative: one migration per
task (several numbers, more collision risk with hive-decoupling). Idempotent like 0003-0007,
no down step.

### D14: body cap on every orchestration write (my call)
Every orchestration write route and the schedule relay cap the request body at 256 KiB (413
`payload_too_large`, before parsing, no upstream call). The largest valid schedule body is a
16384-character prompt (agents-schedule `ScheduleIn`), up to 196608 bytes JSON-escaped, plus
the name and fields; 256 KiB covers it and matches Matrix D5. Retro proposal
(file-editor-with-tabs-and-hi): check every write route for a size cap. Alternative: no cap
(the main port has none today, but agents can loop).

### D15: agents-schedule relay Service and port (probe)
Probed: release `agents-schedule`, chart fullname `agents-schedule`, so the UI Service is
`agents-schedule-api` (port 80 to container port `http` 8000,
`chart/agents-schedule/templates/service.yaml`, `values.yaml` `components.api.port: 8000`).
Port 8001 is free in the api container. The relay gets its own Service
`agents-schedule-api-relay`, port 8001 to container port `relay` 8001, selecting only the api
component (my call, mirrors the connector's `-api-agents` Service). The orchestrator values set
`schedule.url: http://agents-schedule-api-relay:8001`. No NetworkPolicy exists in either chart
or the helmfile, so none is added.

### D16: relay token secrets (mirrors Matrix D14)
`scripts/bootstrap-secrets.sh` generates one relay token: the orchestrator file
`values/agents-orchestrator/schedule-token.secrets.yaml` (`schedule.token`) and the schedule
file `values/agents-schedule/relay-token.secrets.yaml` (`relay.tokenSha256`, its sha256), both
SOPS-encrypted, both or neither, never rotated. The orchestrator chart takes `schedule.url`,
`schedule.token` or `schedule.existingSecret`; the schedule chart takes `relay.tokenSha256` or
`relay.tokenSecret`.

### D17: pins and deploy order
- agents-schedule is pinned by its main build: chart `0.1.0-main.<sha7>`
  (`scripts/chart-version.sh`) and image `<sha7>`, no schedule tag (my call; the 0.1.0 release
  pin is replaced). The orchestrator and agents-web are pinned by main sha7 as today; the agent
  image stays on its release tag (Harbor prunes wrapper sha7 tags).
- Every image tag and chart version is checked in Harbor before any apply (retro proposal).
- Apply order, `--selector` per release, `mise run diff` reviewed before each: agents-schedule
  (its migration runs in the init container; the relay listener comes up), agents-orchestrator
  (its migration; the new plugins ref changes the rendered config hash and rolls every running
  agent pod, including mx-5: one line to mx-5 first), agents-web.
- helmfile MEMORY gotcha: a changed service Secret does not restart the orchestrator api pods;
  when the relay answers `schedules_unconfigured` or upstream 401 after the apply, run
  `kubectl rollout restart deploy/agents-orchestrator-api` (least destructive first).

### D18: live smoke from a throwaway flagged session (my call)
`scripts/orchestration-smoke.sh` (mise task `orchestration-smoke`), separate from
`scripts/smoke.sh`. It creates a throwaway alone session with `session_orchestration` true
through the public API, posts it a user message (main port, origin `user`) that keeps the turn
open (the agent runs a bounded `sleep`), waits until that turn is current, and from the
session's pod (its own `ORCH_AGENT_*` env, never printed) calls the orchestration routes:
`me`, presets list, preset create and update, a refused `privilege_escalation` preset, session
create from the own preset, overview, session delete, schedule create (disabled, `0 3 * * *`),
update, runs and delete, preset delete, and the actions list; after the turn ends it checks one
write is refused `not_user_turn`. Each wait has its own deadline; a trap deletes everything the
script created through the public API on success, failure and interrupt. Alternative: drive the
real model through tool calls (non-deterministic) or use mx-5 (would need its recreation).

### D19: the mx-5 grant is the user's act
D1 makes the flag user-only. After the deploy the orchestrator session sends mx-5 one line: flag
mx-5's preset in the UI and recreate mx-5 to get the tools; it does not edit mx-5's preset or
recreate mx-5 itself (recreating drops mx-5's context). The live smoke probes and records mx-5's
preset name and whether the owner DM is bound to mx-5 (facts the repos do not hold). Q2, Q3 and
Q8, pending the gate.

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| architecture (opus architect-researcher) | ran: `.scratchpad/design/session-orchestration-mcp-arch.md` | option A, D1-D12 (sections Decisions, Why A) | options B, C, D (section Options) |
| codebase probe (planner) | ran | Service and port facts (D15: `chart/agents-schedule/templates/service.yaml`, `values.yaml:36,52`); schedule pin by main build (`scripts/chart-version.sh`); `ScheduleIn.prompt` max 16384 (`api/schemas.py:18`) for D14; no NetworkPolicy in any chart | a schedule release tag (main builds are published) |
| retro history | ran (`ticket.py retro --history`) | see Research inputs | calibration-seed proposals (the tool fills minutes and tokens) |
| security review | skipped at plan time: the epic review runs it (authz surface); `workbench:interrogate` is recommended before the gate (authz, secrets) | | |

## Research inputs

Architect Plan inputs, every entry:

- reuse `api/agent.py:require_agent`, `_leads`, the `session_send` refusal pattern (arch Plan inputs): orch-orchestration-gate, orch-creator-messaging.
- reuse `db/queue.py:turn_hop` current-turn join (arch): orch-message-origin (`turn_origin`).
- reuse `api/sessions.py:check_spec`, `_create_from_preset`, `_CREATE_LOCK` (arch): orch-orchestration-sessions.
- reuse `db/sessions.py:request_delete`, `set_replicas` (arch): orch-orchestration-sessions.
- reuse `api/presets.py:_validated` (arch): orch-orchestration-presets.
- reuse `api/service_auth.py:ServiceGate` gate pattern carrying the service name (arch): orch-message-origin, sched-relay-listener.
- reuse Matrix D1/D2/D12/D13/D16 relay, settings pair, contract vendoring, pin with allow list (arch): orch-schedule-relay, orch-schedule-relay-contract, orch-orchestration-tools-pin.
- reuse `OrchestratorPlugin.on_error` (arch): plugin-orchestration-tools.
- reuse agents-web Superleader switch pattern (arch): web-orchestration-switch.
- reuse agents-schedule `api/schedules.py` handlers and `_check_preset` (arch): sched-relay-routes.
- do-not-build: agents calling agents-schedule directly (arch): README Non-goals; orch-schedule-relay is the only path.
- do-not-build: an admin or service token in agent pods (arch): README Non-goals; orch-schedule-relay ac (agent token never forwarded).
- do-not-build: scope lists or globs (arch): README Non-goals.
- do-not-build: a confirm-token round trip (arch): README Non-goals; plugin-orchestration-tools descriptions instead.
- do-not-build: a preset copy tool (arch): orch-orchestration-presets ac (no copy route).
- do-not-build: any agents-common or connector change (arch): README Non-goals.
- do-not-build: orchestrator-side schedule storage (arch): orch-schedule-relay (stores nothing).
- do-not-build: making the flag editable in place on a running session (arch): orch-orchestration-flag (spec stays immutable).
- fix-as-ac: `messages.origin` on every insert path (arch): orch-message-origin.
- fix-as-ac: service name passed from ServiceGate to the app (arch): orch-message-origin.
- fix-as-ac: writes refused in non-user turns, tested per origin (arch): orch-orchestration-gate.
- fix-as-ac: no escalation through presets, specs or schedule presets (arch): orch-orchestration-gate, orch-orchestration-presets, orch-orchestration-sessions, orch-schedule-relay.
- fix-as-ac: `self_delete`, `not_owner`, `protected_target` (arch): orch-orchestration-sessions.
- fix-as-ac: masked secrets in non-owned preset views (arch): orch-orchestration-presets.
- fix-as-ac: an audit row for every write, refusals included (arch): orch-orchestration-gate, orch-orchestration-presets, orch-orchestration-sessions, orch-schedule-relay.
- fix-as-ac: the agent token never forwarded to agents-schedule (arch): orch-schedule-relay.
- idea, noted not doing now: UI page for `orchestration_actions`, bearer gate in agents-common, owner-sender marking on connector messages, schedule owner provenance on fired sessions (arch): README Non-goals.
- fact not settled: next orchestrator migration number (arch): rule in Constraints and D13; orch-message-origin.
- fact not settled: plugin version after hive-decoupling's pin (arch): rule in Constraints and D11; plugins-release-orch-tools.
- fact not settled: agents-schedule Service name and relay port (arch): probed, D15; sched-chart-relay-port, helmfile-orchestration-pins.
- fact not settled: connector group-chat messages share the connector service token, sender not recorded (arch): accepted risk, Q3; no task.
- fact not settled: mx-5's preset name and whether its room is the owner DM (arch): not in any repo; probed live in orchestration-live-smoke (D19).
- questions 1-7 (arch): Open questions Q1-Q7.

Retro proposals (`ticket.py retro --history`), recurring workflow ones first:

- recurring (leader-auto-handover, generic-any-mcp-with-git-and, file-editor-with-tabs-and-hi): defects per-task review missed, found in the epic review; check every write route for a size cap (file-editor-with-tabs-and-hi): D14, orch-orchestration-gate, orch-schedule-relay.
- recurring (file-download-in-file-browse, leader-auto-handover, file-editor-with-tabs-and-hi): no Docker in agent pods makes DB tests CI-only: Notes of every orchestrator and schedule DB task (non-DB cases first, CI is the DB gate).
- recurring (generic-any-mcp-with-git-and, file-editor-with-tabs-and-hi): the deploy depends on Harbor holding image tags; plan pins that survive pruning and check them before apply: D17, orchestration-live-smoke ac1.
- recurring (leader-auto-handover): for smoke-script tasks every timeout or deadline is checked against the AC: orchestration-smoke-script ac (per-wait deadlines).
- recurring (generic-any-mcp-with-git-and): fakes must match real output samples: orchestration-smoke-script and orch-schedule-relay-contract (vendored contract, judgement ac).
- recurring (leader-auto-handover): `new-task` leaves template sections: this plan fills Interfaces, Expected outcome, Steps and Notes in every task.
- recurring (leader-auto-handover): run the duplicate-predicate sweep before the last code task merges: Review focus (ownership and live-count predicates single-sourced), orch-orchestration-sessions Notes.
- one-off (file-editor-with-tabs-and-hi): an implementer changed a test without reporting it: every task names each test that is no longer accurate.
- one-off (generic-any-mcp-with-git-and): GitGuardian false positives on fake tokens: Notes of the relay, listener and secrets tasks (build fake tokens at runtime).
- code (leader-auto-handover): agents-helmfile has no CI: helmfile tasks rest on the local verify; noted in their Notes.
- helmfile MEMORY 2026-10-26: a new service Secret does not restart the orchestrator api pods: D17, orchestration-live-smoke Notes.

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 flag | orch-orchestration-flag, orch-orchestration-tools-pin, web-orchestration-switch |
| D2 who may call | orch-orchestration-gate |
| D3 user request | orch-message-origin, orch-orchestration-gate, plugin-orchestration-tools |
| D4 target scope | orch-message-origin, orch-orchestration-presets, orch-orchestration-sessions, sched-schedule-owner, sched-relay-routes, web-created-by, web-schedule-owner |
| D5 no escalation | orch-orchestration-gate, orch-orchestration-presets, orch-orchestration-sessions, orch-schedule-relay |
| D6 delete safety | orch-orchestration-sessions, orch-orchestration-presets |
| D7 schedule relay | orch-schedule-relay, orch-schedule-relay-contract, sched-schedule-owner, sched-relay-listener, sched-relay-routes |
| D8 audit | orch-message-origin, orch-orchestration-gate |
| D9 limits | orch-orchestration-gate, orch-orchestration-sessions, sched-relay-listener, sched-relay-routes |
| D10 created sessions work | orch-orchestration-sessions, orch-creator-messaging |
| D11 tools and release | plugin-orchestration-tools, plugins-release-orch-tools, orch-orchestration-tools-pin |
| D12 Matrix compatibility | orch-schedule-relay, orch-orchestration-sessions |
| D13 one migration | orch-message-origin |
| D14 body cap | orch-orchestration-gate, orch-schedule-relay |
| D15 relay Service and port | sched-chart-relay-port, helmfile-orchestration-pins |
| D16 relay token secrets | orch-chart-schedule-relay, sched-chart-relay-port, helmfile-relay-secrets |
| D17 pins and deploy | helmfile-orchestration-pins, orchestration-live-smoke |
| D18 live smoke | orchestration-smoke-script, orchestration-live-smoke |
| D19 mx-5 grant | orchestration-live-smoke |

## Review focus

- The check order of D2 and D6 and the user-turn gate (D3): one dependency, every route through
  it, every origin tested; reads never gated, writes always.
- Ownership predicates and the live-owned-session count: one SQL predicate each, single-sourced
  (retro: duplicate predicates found late).
- No escalation (D5) on all three paths: preset spec, session spec or preset, schedule preset.
- Masking (D4): every secret-bearing field of `SessionSpec` (`env`, `WrapperSettings` hooks
  `secret` and `headers`, `CommandHook.env`, `McpStdio.env`, `McpRemote.headers`) masked on
  non-owned presets, keys kept.
- Audit (D8): a row for every write past `require_agent`, refusals included; no FK.
- The relay never forwards the agent token or any inbound header; the schedule relay listener
  token never reaches a log or an error body.
- The smoke's cleanup trap and per-wait deadlines.

## Left to the builder

- Internal module layout under `api/` beyond the named modules (`api/orchestration.py`,
  `api/orchestration_presets.py`, `api/orchestration_sessions.py`,
  `api/orchestration_relay.py`), as long as the gate is one dependency.
- The masked placeholder string (for example `"***"`), the same everywhere.
- Index choice on `orchestration_actions` (caller and created_at at least).
- The exact help texts of the web switch and the tool descriptions, within the ACs.

## Assumptions and unknown facts

- mx-5's preset name and whether the owner DM is bound to mx-5: not in any repo; probed live by
  orchestration-live-smoke (GET `/api/v1/sessions`, the connector room binding) and recorded.
- The plugins version and the orchestrator migration number: rules in Constraints, resolved at
  build time by reading the orchestrator settings and the migrations directory.
- hive-decoupling has no design yet: if it adds tools, the plugin tool count test follows its
  count plus the sixteen of this epic; if it touches `orchestrator_allow`, this epic builds on
  its version.
- The Matrix connector's service token name is `agents-matrix-connector` (helmfile
  `service-token-agents-matrix-connector.secrets.yaml`); orch-message-origin confirms it from the
  rendered `ORCH_SERVICE_TOKENS` key names before fixing the default origins.

## Open questions
- Q1: A flagged session may change only the sessions, presets and schedules it created, and may read everything with secrets masked? [recommended: yes]
- Q2: Grant mx-5 by flagging its preset in the UI and recreating the session (spec stays immutable)? [recommended: yes]

## Irreversible operations in scope

Standing user rule (2026-10-27, msg 105): deploy whenever possible, live applies need no
approval; tags are report-first and listed here for the gate.

- Tag: any-mcp-tatara-plugins release tag (the next minor after hive-decoupling's pin), pushed
  to origin on the merge commit of plugins-release-orch-tools by the orchestrator session after
  green CI. Safeguard: approval at this gate; ac on the tag checked after the push.
- Live orchestrator migration `NNNN_session_orchestration.sql` (next free number) on the
  agents-orchestrator database, applied on the orchestrator apply: additive (one column on
  `messages`, two pairs of columns, one table), no down step. Safeguard: idempotence and schema
  tests in orch-message-origin.
- Live agents-schedule migration (next free number, 0002 today) on the agents-schedule database
  in its init container: two nullable columns, no down step. Safeguard: idempotence test in
  sched-schedule-owner.
- New credential: the relay token generated by `bootstrap-secrets.sh` and committed
  SOPS-encrypted; never rotates, both files or neither.
- Live applies (orchestration-live-smoke): agents-schedule, agents-orchestrator (the new plugins
  ref rolls every running agent pod, including the mx-5 hive; one line to mx-5 first),
  agents-web. Safeguard: standing deploy rule, `mise run diff` before each, `--selector` per
  release.
- Live smoke objects: a throwaway preset, session and disabled schedule created and deleted
  through the public API and the orchestration routes, plus audit rows in
  `orchestration_actions` that stay by design (no delete path). Safeguard: the trap deletes every
  object the script created, and only those.
