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
- Ordering (accepted queue, 2026-10-29): this epic runs right after slash-commands-from-chat, its
  only README blocker; nothing is dispatched until slash-commands-from-chat has merged on every
  repo it touches (B6; the first task is baseline-facts). hive-decoupling and
  matrix-connector-agent-initi are done (docs/plans/done). immediate-message-delivery-w lists this
  epic as its blocker and takes the numbers after it (migration 0014, plugins v0.7.0). Shared
  files with slash-commands-from-chat: orchestrator `settings.py`, `db/queue.py`,
  `api/messages.py`, `api/agent.py`, `k8s/on_start.py`, `tests/test_migrations.py`, the helmfile
  values.
- Numbers, negotiated 2026-10-29 (mx-34 #469/#470), never guessed:
  - orchestrator migration `0013_session_orchestration.sql`: main ends at 0011 (2d6d722,
    `0011_drop_feed_cursor.sql`); slash-commands-from-chat ships `0010_slash_messages.sql` and
    `0012_command_outcome_index.sql`; the migrator applies by set;
  - any-mcp-tatara-plugins v0.6.0: the latest tag is v0.5.1 (ef17204, hive-decoupling's advice
    floor on top of slash's v0.5.0), which slash-commands-from-chat pins
    (`ORCH_ANY_MCP_PLUGINS_REF` default v0.5.1); the plugin lists 16 tools (`ALL_TOOLS`), 32
    after this epic;
  - agents-schedule migration 0002 (only `0001_schedules.sql` exists; slash-commands-from-chat
    adds none, no other epic claims one);
  - agents-schedule release v0.2.0 from v0.1.0 (negotiated, user answer pending; tatara agreed).
  baseline-facts confirms each on main; on a mismatch the orchestrator session proposes the new
  number on mx-34, waits for the confirmation and amends the dependent tasks.
- Live today (handover note 2026-10-29): orchestrator 2d6d722, plugins ref v0.4.0, agent image
  0.3.3; the slash-commands-from-chat deploy moves the plugins ref to v0.5.1 and the agent image
  to wrapper 0.4.1 or 0.4.2 before this epic deploys.
- Standing user rules: deploy whenever possible (live applies need no approval); tags are
  irreversible and listed below; send mx-5 one line before an apply restarts agent pods;
  every release tag is proposed via mx-34 and confirmed before tagging.
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
- A write is allowed only while every message that delivered the caller's current turn (`agent_status.current_turn_id`, same join as `db/queue.py:turn_hop`) has an origin in `ORCH_ORCHESTRATION_ORIGINS`, default `user,service:agents-matrix-connector`; else 403 `not_user_turn`.
- Rejected by default: session messages, `service:agents-webhook`, `service:agents-schedule`,
  and turns with no message (background completions, peer sends).
- New column `messages.origin text`, written at insert: `user` on the main port; `service:<name>` on the service port (the name `ServiceGate` already hands to the routes, `api/service_auth.py:calling_service`, landed with migration 0009); `session` in `enqueue_message` when a sender is present; NULL for command-kind messages (builder check B4, below). Rows from before the migration stay NULL and never pass the gate (my call).
- Every message that delivered the turn counts, not only the newest (my call, staleness refresh 2026-10-29): immediate-message-delivery-w, which builds on this epic, lets several messages share one turn_id, and one disallowed message in the turn refuses the write.
- Main has two enqueue call sites after slash-commands-from-chat: `api/messages.py:post_message`
  (main and service port; it gains `request: Request`) and `api/agent.py:session_send`. No
  orchestrator-internal enqueue exists (staleness audit 2026-10-29).
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
- Presets (builder check Q9): session create and schedule create or update may name only a
  preset the caller created (`presets.created_by_session_id` equals the caller), else 403
  `not_owner`, so a UI-made preset with secrets in `env` never reaches an agent-controlled pod;
  an explicit spec is still allowed (the caller can only write what it can read, and reads
  mask other presets). The check runs before the escalation check.

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
- Staleness refresh 2026-10-29 (my call): agents-schedule answers DELETE with an empty 204 and run-now with 202: the relay passes an empty 204 through unchanged; any other non-JSON answer is 503 `schedules_unavailable`. The relay reuses the forward and body-cap code of `api/chat.py` (`forward`, `_capped_body`, `new_client`, `close_client`), generalised to take the upstream URL, token and unavailable code, instead of a second copy; the schedule client is closed in the app lifespan like the chat client.
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
- `ORCH_ORCHESTRATION_ACTIONS_PER_HOUR` (30): ok writes per caller, `schedule_run` included (B2), else 429 `rate_limited`.
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
- The release is any-mcp-tatara-plugins v0.6.0, the next minor after the latest tag v0.5.1 that slash-commands-from-chat leaves pinned (negotiated 2026-10-29, mx-34 #469/#470). The allow-list change lands with the pin in one task, per Matrix D13 (`test_allowed_tools_exist_in_plugin` needs both).
- The plugin lists 16 tools on main (`ALL_TOOLS`, asserted by `test_lists_all_tools`), 32
  after this epic. `orchestrator_activity` (hive-decoupling's digest) and
  `orchestrator_orchestration_actions` (the caller's audit rows) are different tools; their
  descriptions say which is which. The plugin files avoid the words `tests/test_nomenclature.py`
  bans.
- The tag is proposed on mx-34 and confirmed before it is pushed (standing rule), although the
  number itself was negotiated.

### D12: Matrix compatibility
No connector change; the tools are leader-only like the chat tools; a session cannot delete
itself, so mx-5 never releases its own room binding; deleting an owned session bound to a room
releases that binding through the existing Matrix Q10 sweep (intended). The relay module
mirrors `api/chat.py`; `settings.py` gains `ORCH_SCHEDULE_*` next to `ORCH_CHAT_*`.

### D13: one orchestrator migration for the whole epic (my call)
`0013_session_orchestration.sql` (negotiated 2026-10-29, mx-34 #469/#470; slash-commands-from-chat ships 0010 and 0012, main ends at 0011) adds `messages.origin`, the two `created_by_*` pairs and `orchestration_actions` in the first task, so later tasks consume no migration numbers and cannot collide with another epic's. Alternative: one migration per
task (several numbers, more collision risk with the epics queued behind). Idempotent like 0003-0007,
no down step. Four tests in `tests/test_migrations.py` hard-code the migration list and count
(`test_fresh_database_gets_all_tables`, `test_presets_migration_on_existing_sessions`,
`test_concurrent_migrate_serialises`, `test_0005_renames_clusters_to_sessions`): they become
no longer accurate and gain 0013, nothing else.

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
Staleness refresh 2026-10-29 (my call, the orchestrator chart's own rule since the incident): `ORCH_SCHEDULE_URL` and `ORCH_SCHEDULE_TOKEN` are env of the api main container only, always together, rendered by one `agents-orchestrator.scheduleEnv` helper next to `agents-orchestrator.chatEnv`, never in the shared settings ConfigMap, the migrate init containers or the other components (orchestrator MEMORY 2026-10-28, orch-chat-env-scope: the chart once put `ORCH_CHAT_URL` in the shared ConfigMap with the token on the api only, and every migrate init container crash-looped on a URL without its token).
A `checksum/schedule-secret` pod annotation rolls the api pod when the chart-made token changes,
and agents-helmfile renders the release in a test that asserts the pair lands only on the api
main container (helmfile-orchestration-pins).

### D17: pins and deploy order
- agents-schedule is pinned by its release tag v0.2.0 (negotiated, user answer pending): chart `0.2.0`, published by the tag's `chart-publish-tag` job, and image `<sha7>` of the tagged commit, published by its main build, the way v0.1.0 is pinned today (chart `0.1.0`, image `6cfa955`). The orchestrator and agents-web are pinned by main sha7 as today; the agent image stays on its release tag. `mise run check-pins` resolves `0.2.0` through tag `v0.2.0` and must pass before any apply.
- Why the change (staleness refresh 2026-10-29; replaces the earlier main-build pin
  `0.1.0-main.<sha7>`, my call then): Harbor retention pruned the sha7 image tags of every
  main-built release within hours (incident 2026-10-28) while chart versions survive, and the
  user's standing rule is "latest stable always deployed". The release is task
  sched-release-0-2-0, tagged by the orchestrator session after the mx-34 confirmation.
  The image is still a sha7 tag (agents-schedule CI pushes images only on main), so it stays
  exposed to retention until semver-image-tags-at-the-end (queued at the end of the chain; it
  removes `chart-publish-tag`, so sched-release-0-2-0 lands before it).
- Every image tag and chart version is checked in Harbor before any apply (retro proposal).
- Apply order, `--selector` per release, `mise run diff` reviewed before each (`mise run apply` runs lint, test and check-pins first): agents-schedule (its migration 0002 runs in the init container; the relay listener comes up), agents-orchestrator (its migration 0013; the new plugins ref changes the rendered config hash, and the OnDelete rollout reconciler replaces each agent pod once it is idle, one per session, leaders last, mx-5 included: one line to mx-5 first), agents-web.
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

## Builder check settlements (2026-10-27)

Settled after the builder check of the plan. Each is the user's call unless marked otherwise. The
tasks named were amended with `ticket.py amend`; where this section and an earlier decision
differ, this section wins.

- B2 (my call): `schedule_run` counts as an ok write against `ORCH_ORCHESTRATION_ACTIONS_PER_HOUR`
  (D9). The global `max_sessions` is the only bound on fired sessions: no per-run or per-owner
  cap is added in the orchestrator or in agents-schedule. Tasks: orch-orchestration-gate (the
  count covers every ok action), orch-schedule-relay (run is a write, audited `schedule_run`),
  sched-relay-routes (run-now adds no cap).
- B3 (my call): agent-created schedules may be created enabled; the relay forwards `enabled`
  untouched. Orphans after the owner's deletion stay and are managed from the UI (D4: ownership
  is by session id, nothing is validated against a live session). Tasks: sched-relay-routes,
  orch-schedule-relay, sched-schedule-owner (UI replace and delete of an orphan work).
- B4 (my call): the build uses the merged slash-commands code. Origin `session` or `user` is
  stored the same way on every enqueue path: `enqueue_message` takes `origin: str | None` as a
  required keyword, no default, so no path can omit it (D3's "`session` in `enqueue_message`
  when a sender is present" is now one case of that rule). Command-kind messages and
  orchestrator-internal enqueues (no sender, no port) store NULL and never pass the user-turn
  gate, whatever `ORCH_ORCHESTRATION_ORIGINS` holds. Tasks: orch-message-origin (two new ACs,
  the call-site files recorded by baseline-facts are in scope), orch-orchestration-gate,
  orch-orchestration-sessions (prompt origin explicit).
- B5 (my call): on approval of the gate, the plan builds on the recommended answers of Q1 to Q9
  as written; no task waits for a separate reply.
- B6 (my call): the build starts only after hive-decoupling, matrix-connector-agent-initi and
  slash-commands-from-chat have all merged. New first task `baseline-facts` reads the real
  orchestrator and schedule migration numbers, the plugins version and latest tag, the plugin
  tool count and every `messages` enqueue call site from main, records them in agents-orchestrator
  `MEMORY.md`, and the orchestrator session amends the dependent tasks (orch-message-origin,
  sched-schedule-owner, plugin-orchestration-tools, plugins-release-orch-tools,
  orch-orchestration-tools-pin) so no AC carries an assumed number. orch-message-origin and
  sched-schedule-owner now depend on it. The `files` entries that still name `NNNN` or `0002`
  are replaced by the orchestrator session when it amends, from the recorded numbers.
- Q9 (gate question, recommended yes): a flagged session may create sessions or schedules only
  from presets it created itself (or from an explicit spec); presets made in the UI, which may
  hold secrets in env, are refused `not_owner`, so their secrets never reach a pod the agent
  controls. D5 gains this rule. One shared predicate `require_own_preset` in
  `api/orchestration.py` (orch-orchestration-gate) is called by session create with a
  `preset_id` (orch-orchestration-sessions) and by schedule create and update in the
  orchestrator relay (orch-schedule-relay), the only place that knows who made a preset.
  sched-relay-routes writes the rule into the relay contract (README and `openapi-relay.json`);
  the listener keeps `_check_preset` for existence only. plugin-orchestration-tools descriptions
  state it. Not added to the live smoke (a not_owner probe would need a throwaway UI-made
  preset): noted, not doing now.

## Staleness refresh (2026-10-29)

The plan was re-checked against origin/main before the build (audit
`.scratchpad/orch-mcp/staleness.md`; handover note `docs/plans/2026-10-29-tatara-handover-to-cct2.md`;
heads read: agents-orchestrator 2d6d722, any-mcp-tatara-plugins ef17204 (v0.5.1), agents-schedule
7651e29 (v0.1.0), agents-helmfile c2855fc, agents-web ab78d97, and the slash-commands-from-chat
branches). Where this section and an earlier decision or settlement differ, this section wins.
Tasks changed through `ticket.py amend`, each with its reason in Notes.

- Blockers: slash-commands-from-chat only (B6's three-blocker rule is now one blocker);
  numbers negotiated (Constraints). baseline-facts confirms them instead of deriving them.
- D3: `ServiceGate` already hands the service name to the routes (`calling_service`), so
  orch-message-origin edits `api/agent.py` instead of `api/service_auth.py`; the two real call
  sites are named; `turn_origin` returns every message of the turn and the gate needs all of them
  allowed (orch-message-origin, orch-orchestration-gate). B4's "orchestrator-internal enqueues"
  has no instance on main.
- D7: empty 204 and 202 pass through; the chat forward helper is shared (orch-schedule-relay).
- D11: v0.6.0 from v0.5.1, 16 to 32 tools, `test_lists_all_tools`, the nomenclature test, the
  mx-34 tag proposal (plugin-orchestration-tools, plugins-release-orch-tools,
  orch-orchestration-tools-pin; the allow list covers both `orchestrator_allow` branches and
  `chat=False`).
- D13: 0013 and the four migration-list tests named (orch-message-origin); agents-schedule 0002
  and its two migration tests named (sched-schedule-owner).
- D16: the schedule pair is api-main-only, never the ConfigMap (orch-chart-schedule-relay,
  helmfile-orchestration-pins); the earlier ac `test_schedule_url_in_configmap` would have
  repeated the 2026-10-28 crash loop.
- D17: agents-schedule pinned by release v0.2.0 (negotiated, user answer pending), new task
  sched-release-0-2-0 (the only added task; the release needs its own version bump and tag);
  check-pins in helmfile-orchestration-pins; idle-only rollout and the apply-from-pod procedure
  in orchestration-live-smoke.
- Smoke: the script sources `scripts/lib/smoke-common.sh` (orchestration-smoke-script, Notes
  and Files only).
- Reuse notes added to orch-orchestration-sessions (`_insert(**provenance)`),
  orch-creator-messaging (`kind`), sched-relay-listener (not behind `SourceAllowlist`),
  orch-schedule-relay-contract (the chat contract files), orch-orchestration-presets
  (kubernetes-secret-backed-pre).
- Not adopted from the audit: adding immediate-message-delivery-w and decouple-s3-session-cache-fr
  as blockers (the accepted queue runs this epic right after slash-commands-from-chat, and
  immediate-message-delivery-w already blocks on it); refusing trigger-created sessions in the
  orchestration gate (no requirement asks for it; the user-turn gate already refuses
  webhook and schedule turns).

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| architecture (opus architect-researcher) | ran: `.scratchpad/design/session-orchestration-mcp-arch.md` | option A, D1-D12 (sections Decisions, Why A) | options B, C, D (section Options) |
| codebase probe (planner) | ran | Service and port facts (D15: `chart/agents-schedule/templates/service.yaml`, `values.yaml:36,52`); schedule pin by main build (`scripts/chart-version.sh`); `ScheduleIn.prompt` max 16384 (`api/schemas.py:18`) for D14; no NetworkPolicy in any chart | a schedule release tag (main builds are published) |
| retro history | ran (`ticket.py retro --history`) | see Research inputs | calibration-seed proposals (the tool fills minutes and tokens) |
| security review | skipped at plan time: the epic review runs it (authz surface); `workbench:interrogate` is recommended before the gate (authz, secrets) | | |
| staleness audit (2026-10-29) | ran: `.scratchpad/orch-mcp/staleness.md` against origin/main and the slash branches | section Staleness refresh | new blockers beyond slash-commands-from-chat; a trigger-session refusal |

## Research inputs

Architect Plan inputs, every entry:

- reuse `api/agent.py:require_agent`, `_leads`, the `session_send` refusal pattern (arch Plan inputs): orch-orchestration-gate, orch-creator-messaging.
- reuse `db/queue.py:turn_hop` current-turn join (arch): orch-message-origin (`turn_origin`).
- reuse `api/sessions.py:check_spec`, `_create_from_preset`, `_CREATE_LOCK` (arch): orch-orchestration-sessions.
- reuse `db/sessions.py:request_delete`, `set_replicas` (arch): orch-orchestration-sessions.
- reuse `api/presets.py:_validated` (arch): orch-orchestration-presets.
- reuse `api/service_auth.py:ServiceGate` gate pattern carrying the service name (arch): already on main as `calling_service` (migration 0009), read by orch-message-origin; the gate pattern itself by sched-relay-listener.
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
- fix-as-ac: service name passed from ServiceGate to the app (arch): already on main (`calling_service`); orch-message-origin ac4 asserts it is used and `ServiceGate` unchanged.
- fix-as-ac: writes refused in non-user turns, tested per origin (arch): orch-orchestration-gate.
- fix-as-ac: no escalation through presets, specs or schedule presets (arch): orch-orchestration-gate, orch-orchestration-presets, orch-orchestration-sessions, orch-schedule-relay.
- fix-as-ac: `self_delete`, `not_owner`, `protected_target` (arch): orch-orchestration-sessions.
- fix-as-ac: masked secrets in non-owned preset views (arch): orch-orchestration-presets.
- fix-as-ac: an audit row for every write, refusals included (arch): orch-orchestration-gate, orch-orchestration-presets, orch-orchestration-sessions, orch-schedule-relay.
- fix-as-ac: the agent token never forwarded to agents-schedule (arch): orch-schedule-relay.
- idea, noted not doing now: UI page for `orchestration_actions`, bearer gate in agents-common, owner-sender marking on connector messages, schedule owner provenance on fired sessions (arch): README Non-goals.
- fact not settled: next orchestrator migration number (arch): negotiated 0013 (Constraints, D13); baseline-facts, orch-message-origin.
- fact not settled: plugin version after hive-decoupling's pin (arch): negotiated v0.6.0 from v0.5.1 (Constraints, D11); baseline-facts, plugins-release-orch-tools.
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

Retro proposals of the epics done since the plan (`ticket.py retro --history`, 2026-10-29), recurring workflow ones first:

- recurring (hive-decoupling, matrix-connector-agent-initi, deploy-safe-agent-sessions, file-editor-with-tabs-and-hi, leader-auto-handover, generic-any-mcp-with-git-and): defects found only in the epic review; a finding that breaches a design anti-goal is never rated Consider, and a value derived from a config field is checked against that field's bounds: Review focus.
- recurring (hive-decoupling and four more): no Docker in the pod makes DB tests CI-only: unchanged, Notes of every DB task.
- one-off (hive-decoupling): plugins v0.5.1 was tagged without the mx-34 proposal: the tag step of plugins-release-orch-tools and sched-release-0-2-0 (ac on the proposal and confirmation).
- one-off (hive-decoupling): the live apply waited because a plugins ref change rolls agent pods and an idle leader with a running subagent would lose it: orchestration-live-smoke Notes.
- tech debt (hive-decoupling): migration 0010 merging after 0011 rests on the migrator applying by set: 0013 lands after both, no reorder (D13).
- one-off (fix-preset-env-paste-auto-ap): deploy from a pod needs a short GNUPGHOME and a built kubeconfig: orchestration-live-smoke Notes.
- 2026-10-28 incident (orchestrator MEMORY orch-chat-env-scope): a relay URL in the shared ConfigMap crash-looped every migrate init container: D16, orch-chart-schedule-relay, helmfile-orchestration-pins ac9.
- 2026-10-28 incident (semver-image-tags-at-the-end README): Harbor retention pruned sha7 image tags within hours: D17, sched-release-0-2-0, orchestration-live-smoke.

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 flag | orch-orchestration-flag, orch-orchestration-tools-pin, web-orchestration-switch |
| D2 who may call | orch-orchestration-gate |
| D3 user request | orch-message-origin, orch-orchestration-gate, plugin-orchestration-tools |
| D4 target scope | orch-message-origin, orch-orchestration-presets, orch-orchestration-sessions, sched-schedule-owner, sched-relay-routes, web-created-by, web-schedule-owner |
| D5 no escalation | orch-orchestration-gate, orch-orchestration-presets, orch-orchestration-sessions, orch-schedule-relay, sched-relay-routes, plugin-orchestration-tools |
| D6 delete safety | orch-orchestration-sessions, orch-orchestration-presets |
| D7 schedule relay | orch-schedule-relay, orch-schedule-relay-contract, sched-schedule-owner, sched-relay-listener, sched-relay-routes |
| D8 audit | orch-message-origin, orch-orchestration-gate |
| D9 limits | orch-orchestration-gate, orch-orchestration-sessions, sched-relay-listener, sched-relay-routes |
| D10 created sessions work | orch-orchestration-sessions, orch-creator-messaging |
| D11 tools and release | baseline-facts, plugin-orchestration-tools, plugins-release-orch-tools, orch-orchestration-tools-pin |
| D12 Matrix compatibility | orch-schedule-relay, orch-orchestration-sessions |
| D13 one migration | baseline-facts, orch-message-origin |
| D14 body cap | orch-orchestration-gate, orch-schedule-relay |
| D15 relay Service and port | sched-chart-relay-port, helmfile-orchestration-pins |
| D16 relay token secrets | orch-chart-schedule-relay, sched-chart-relay-port, helmfile-relay-secrets, helmfile-orchestration-pins |
| D17 pins and deploy | sched-release-0-2-0, helmfile-orchestration-pins, orchestration-live-smoke |
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
- The schedule URL and token never in the settings ConfigMap or on any container but the api main one (D16; the 2026-10-28 crash loop).
- The user-turn gate over every message of the turn, not the newest one (D3).
- Anti-goal breaches are findings to fix, never Consider; values derived from a config field are checked against its bounds (hive-decoupling retro).

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
- The plugins version and the migration numbers: negotiated (Constraints), confirmed on main by baseline-facts.
- hive-decoupling landed (done 2026-10-29): it added `orchestrator_activity`, so the plugin lists 16 tools on main and 32 after this epic; `orchestrator_allow(spec, *, chat=True)` is its version as slash-commands-from-chat leaves it.
- The Matrix connector's service token name is `agents-matrix-connector`: confirmed (agents-helmfile `values/agents-orchestrator/service-token-agents-matrix-connector.secrets.yaml`).

## Open questions
- Q1: A flagged session may change only the sessions, presets and schedules it created, and may read everything with secrets masked? [recommended: yes]
- Q2: Grant mx-5 by flagging its preset in the UI and recreating the session (spec stays immutable)? [recommended: yes]
- Q3: Writes are allowed only in turns started from the UI or the Matrix connector, and you flag only the owner DM's preset, so group chats cannot drive it? [recommended: yes]
- Q4: A session and the sessions it created may message each other even when neither is a superleader? [recommended: yes]
- Q5: Agent-created schedules may fire at most every 15 minutes, at most 10 per session; at most 5 live owned sessions and 30 writes per hour? [recommended: yes]
- Q6: No separate confirmation step before a delete; the user-turn gate plus ownership is the safeguard? [recommended: yes]
- Q7: agents-web shows 'created by <slug>' on sessions, presets and schedules? [recommended: yes]
- Q8: After the deploy you flag mx-5's preset in the UI and recreate mx-5 yourself (the orchestrator sends mx-5 one line and never edits mx-5's preset or recreates it, since that drops mx-5's context), and the epic closes on the throwaway-session live smoke without waiting for the grant? [recommended: yes]
- Q9: A flagged session may create sessions or schedules only from presets it created itself (or from an explicit spec); presets made in the UI, which may hold secrets in env, are refused not_owner, so their secrets never reach a pod the agent controls? [recommended: yes]

## Irreversible operations in scope

Standing user rules: deploy whenever possible, live applies need no approval (2026-10-27, msg
105); every release tag is proposed via mx-34 and confirmed before tagging (2026-10-29). Tags are
listed here for the gate.

- Tag: any-mcp-tatara-plugins v0.6.0 (negotiated, mx-34 #469/#470), pushed to origin on the
  merge commit of plugins-release-orch-tools by the orchestrator session after green CI and the
  mx-34 confirmation of the tag. Safeguard: the mx-34 proposal and confirmation (ac5), the ac on
  the tag checked after the push.
- Tag: agents-schedule v0.2.0 (negotiated, user answer pending), annotated, pushed on the merge
  commit of sched-release-0-2-0 by the orchestrator session after green CI and the mx-34
  confirmation; its `chart-publish-tag` job publishes the immutable chart 0.2.0. Safeguard: the
  mx-34 proposal and confirmation (ac5), the tag, chart and image checks after the push.
- Live orchestrator migration `0013_session_orchestration.sql` on the agents-orchestrator
  database, applied on the orchestrator apply: additive (one column on `messages`, two pairs of
  columns, one table), no down step. Safeguard: idempotence and schema tests in
  orch-message-origin.
- Live agents-schedule migration `0002_schedule_owner.sql` on the agents-schedule database in its
  init container: two nullable columns, no down step. Safeguard: idempotence test in
  sched-schedule-owner.
- New credential: the relay token generated by `bootstrap-secrets.sh` and committed
  SOPS-encrypted; never rotates, both files or neither.
- Live applies (orchestration-live-smoke): agents-schedule, agents-orchestrator (the new plugins
  ref changes the agent config hash; the OnDelete rollout reconciler replaces each agent pod once
  idle, the mx-5 hive included; one line to mx-5 first), agents-web. Safeguard: standing deploy
  rule, `mise run apply` gated by lint, test and check-pins, `mise run diff` before each,
  `--selector` per release.
- Live smoke objects: a throwaway preset, session and disabled schedule created and deleted
  through the public API and the orchestration routes, plus audit rows in
  `orchestration_actions` that stay by design (no delete path). Safeguard: the trap deletes every
  object the script created, and only those.
