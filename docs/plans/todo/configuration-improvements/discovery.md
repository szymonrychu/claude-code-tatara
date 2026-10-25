# configuration-improvements discovery

Phase 1 brief, 2026-10-25. Read-only. Paths are relative to `code/<repo>/` unless absolute;
tatara-new paths are relative to `/Users/szymonri/Documents/tatara-new/code`.

## Tree state and verification

| Repo | Branch / state | Last main CI | Verify |
|---|---|---|---|
| agent-orchestrator | `main...origin/main` clean, 918dc0a | ci success on 918dc0a | `mise run test`, `mise run lint`, `mise run test:chart`, `mise run lint:chart`, `mise run test:e2e` (kind); frontend: `npm --prefix frontend run test`, `run lint`, `run build`, `run check:api`; after route/schema change `uv run python -m agent_orchestrator.api.openapi > openapi.json` and `npm --prefix frontend run gen:api` (tests/test_readme_api.py fails on drift) |
| claude-code-wrapper | `main...origin/main` clean, 1f64e9f (release 0.2.0) | main success on 1f64e9f | `mise run test`, `mise run lint`, `mise run precommit`, `mise run test:integration` |
| agents-helmfile | `main...origin/main` clean, 7dcb257 | no Actions runs on main | `mise run test`, `mise run lint`, `mise run diff`, `mise run apply`, `mise run smoke` |

Baseline test runs were not executed in this phase (CI on each main head is green).
Open worktrees: 8 agent-init-scripts worktrees in agent-orchestrator, 4 in agents-helmfile, 1 in
claude-code-wrapper, plus older orchestrator and wrapper task worktrees. PR agent-orchestrator#10
(`agent-init-scripts`) is OPEN, MERGEABLE, `UNSTABLE` (e2e pending; test, lint, frontend, chart pass).

Component docs read: agent-orchestrator AGENTS.md, MEMORY.md, ROADMAP.md; agents-helmfile
AGENTS.md, MEMORY.md, ROADMAP.md. claude-code-wrapper has no AGENTS.md, MEMORY.md or ROADMAP.md;
it has CLAUDE.md (conventions: test-first, `uv run`, fake claude only, never write service files into a workdir).

Binding memory entries: spec is immutable after create except `replicas` and `init_scripts`
(MEMORY 2026-10-24 amending D4; `PATCH /clusters/{id}` is 405); `LEADER_GRACE_SECONDS` and
`PUSH_INTERVAL_SECONDS` are deliberately module constants (MEMORY 2026-10-24, hive D14);
single writer per table (README `### Single-writer interpretation`, `clusters` writer = api; the
reconciler writes only `status`, `observed_generation` and deletes the row).

## 1. Wrapper settings (hooks, idle auto-compact)

### What the wrapper accepts (claude-code-wrapper `src/claude_code_wrapper/config.py:Config`)

- `server` (`ServerConfig`): host, port, internal_port, auth_token, allow_anonymous, log_level, callback_secret.
- `paths` (`PathsConfig`): workdir_root, sessions_root.
- `claude` (`ClaudeConfig`): binary, model, effort, permission_mode (default `bypassPermissions`),
  extra_args, env (`claude_env.py:ClaudeEnv`, 401 typed Claude Code env vars plus `extra`;
  12 secret-kind), passthrough_env, passthrough_env_exclude, main_agent_only_tools,
  permissions {allow, deny}, settings (settings.json overlay; overlay `hooks` are appended after the
  relay hooks in `bootstrap/settings.py`), claude_json, mcp_servers (stdio/http), config_files,
  boot (`BootConfig`: timeouts, dialogs keys, ready_markers, fatal_patterns).
- `init` (`InitConfig`): workdir {mode empty/mounted/clone, repo_url, branch, depth, submodules}, git {user_name, user_email}, setup_commands.
- `prompts` (`PromptsConfig`): global_claude_md, system_append, initial_prompt, templates.
- `mise` (`MiseConfig`), `plugins` (`PluginsConfig`: marketplaces, install, disable, timeout).
- `hooks` (`HooksConfig`): 21 events in `HOOK_EVENTS` (onCreate, onResume, onDestroy, onTurn,
  onTurnComplete, onStop, onTick, onAgentResponse, onAgentToolCall, onToolResult, onSubagentStart,
  onSubagentStop, onInterrupt, onCommand, onCommandComplete, onError, preJoin, postJoin, preLeave,
  postLeave, onStart); 7 can veto (`VETO_EVENTS`). Actions are `CommandAction` (`run`, `env`) or
  `WebhookAction` (`url`, `secret`, `headers`, `retries`), common `_Action` keys timeout_seconds,
  blocking, on_error, matcher (only onAgentToolCall/onToolResult), interval_seconds and when (only onTick, interval required).
- `sessions` (`SessionsConfig`): max_sessions, idle_timeout_seconds, turn_stall_seconds (1800),
  interrupt_settle_seconds, max_restarts (3), ask_user_question, turn_marker, resume_on_start,
  defer_stop_on_background_tasks, probe_alive_token, exit_when_last_destroyed, exit_when_dead,
  restart_continue_prompt, commands (`CommandsConfig`: agent, client, timeout_seconds, continue_prompt, allow_force, quiet_seconds),
  auto_compact (`AutoCompactConfig`: idle_seconds (0 = off), instructions (one line, max 2000), min_context_tokens).
  `_auto_compact_before_reaper` requires idle_seconds < idle_timeout_seconds when both > 0.
  Idle compact is armed after each turn in `router.py:SessionRouter._arm_auto_compact` / `_auto_compact_due`.
- `limits` (`LimitsConfig`): prompt/file caps, turn_max_seconds (0 = off), event ring/log, SSE, shutdown_timeout_seconds, terminal caps.
- `peers` (`PeersConfig`), `notes` (`NotesConfig`).

"idle_auto_compact" in the request = `sessions.auto_compact` (all three keys). The wrapper already
implements everything asked; no wrapper code change is known to be needed.

### What agent-orchestrator exposes today

`spec.py:ClusterSpec` fields and where they go (`k8s/render.py:_ccw_config`, `_container`, `k8s/on_start.py`):

| ClusterSpec field | Rendered to |
|---|---|
| model, effort | `claude.model`, `claude.effort` (allowlisted by `validate_spec`) |
| auto_compact_pct | `claude.env.claude_autocompact_pct_override` (default `Settings.default_auto_compact_pct` 95); also orchestrator plugin config |
| env | pod env plus `claude.passthrough_env`; keys `CCW_*`, `CLAUDE_*`, `ANTHROPIC_*`, `ORCH_*`, `POD_NAME`, `*_PROXY`, `*_BASE_URL` rejected (`ClusterSpec._env`) |
| peers, replicas, max_replicas, static | `peers.*`, `notes.enabled` (hive), plugin allow list |
| any_mcp_config | any-mcp config file via on-start.sh (not the wrapper config) |
| image, resources, pvc_size, workdir | pod spec / PVC |
| max_attempts, discard_hook_url | orchestrator only (dispatcher, discard) |
| init_scripts (PR #10, not on main) | orchestrator init Job runner |

Hard-coded by the renderer (reserved, must stay): `server.auth_token`, `paths`, oauth token and
`disable_autoupdater`, `main_agent_only_tools`, `permissions.deny` [EnterPlanMode, ExitPlanMode,
AskUserQuestion], `mcp_servers.any-mcp`, `hooks.onStart` (`sh /etc/ccw/on-start.sh`, blocking,
deny), `hooks.onAgentToolCall` lock check webhook (`_lock_check_hook`, hive only),
`sessions` {max_sessions 1, resume_on_start, idle_timeout_seconds 0, ask_user_question deny},
`prompts.system_append` (`ASK_IN_WRITING_PROMPT`), `limits.shutdown_timeout_seconds`, `peers.*`.

### Missing (wrapper supports, orchestrator does not expose)

hooks (all 21 events), sessions.auto_compact, permission_mode, permissions allow/extra deny,
system_append (user part), global_claude_md, initial_prompt/templates, extra mcp_servers, plugins
(marketplaces/install/disable), mise tools, sessions.turn_stall_seconds, max_restarts,
restart_continue_prompt, defer_stop_on_background_tasks, commands (agent/client lists),
limits.turn_max_seconds, typed Claude env vars (blocked by the `CLAUDE_*`/`ANTHROPIC_*` env rule),
claude.settings overlay (native Claude Code hooks, statusLine), extra_args, boot, claude_json, config_files, init.git.

### tatara-new equivalent

- `tatara-operator/api/v1alpha1/project_types.go:AgentSpec`: Model, Image, PermissionMode,
  MaxTurnsPerTask, TurnTimeoutSeconds, StallProbeGraceSeconds, StallProbeMaxAttempts,
  MaxTurnsPerPod, MaxReviewRounds, MaxPodRecreations, ContextWindowTokens,
  HandoverThresholdPercent, MaxLifecycleIterations, Effort, MaxTaskTokens, ModelByKind,
  EffortByKind, SkillsRef, Hooks, ExtraEnvs, ExtraEnvsFrom, ExtraVolumes, ExtraVolumeMounts,
  ExtraSidecarContainers, ExtraInitContainers, MCPServers, SkillSources, PromptAppendByKind.
- Hooks = `LifecycleHooks`, six shell commands run by the wrapper (PreClone, PostClone,
  ConversationStart, ConversationRestart, AgentTurnFinished, ConversationFinished), rendered to
  `HOOK_*` env by `internal/agent/pod.go:BuildPod`, run by `tatara-claude-code-wrapper/internal/bootstrap/hooks_lifecycle.go:RunHook`.
  Rough mapping to ccw: PostClone/ConversationStart ~ onCreate/onStart, ConversationRestart ~ onResume,
  AgentTurnFinished ~ onTurnComplete, ConversationFinished ~ onDestroy. The only native Claude Code hook is a hard-coded Stop hook (`internal/bootstrap/settings.go:writeSettings`).
- No idle auto-compact in tatara-new (searched compact, idle, auto_compact). Nearest:
  HandoverThresholdPercent (~ our auto_compact_pct) and scm ConversationIdleMinutes (idle budget,
  not compaction). Our wrapper's `examples/tatara.config.yaml` uses `auto_compact.idle_seconds: 1800`.

### Highest-risk surface (credentials, PTY)

- Command hooks run `sh -c` with the full, unscrubbed service env: `hooks.py:HookDispatcher._command`
  merges `self._base_env`, which `manager.py` sets to `self.service_env` (line ~1349) and
  `hooks.py:instance_dispatcher` sets to `service_env`. That env carries `CLAUDE_CODE_OAUTH_TOKEN`,
  `CCW_AUTH_TOKEN`, `CCW_PEER_TOKEN`, `ORCH_AGENT_TOKEN` (render.py `_container`). Terminals, by
  contrast, get a scrubbed env (wrapper README security section).
- The wrapper interpolates `${VAR}` / `${VAR:-d}` in every config string scalar against the pod
  env (`interpolation.py:interpolate`, called by `config.py:load_config`; `$$` escapes). Any user
  string rendered into config.yaml (hook url, headers, run, auto_compact instructions, prompts)
  could read `${CLAUDE_CODE_OAUTH_TOKEN}` and, in a webhook url/header, send it anywhere. Today no
  free user text reaches config.yaml, so this is new exposure.
- PTY control: `claude.extra_args` (CLI flags; `session.py` rejects only `DANGEROUS_FLAG`),
  `claude.boot` (dialog keystrokes, ready markers), `sessions.turn_marker`, `probe_alive_token`.
  `permission_mode` other than bypassPermissions/acceptEdits would make claude block on permission
  prompts nobody answers. `claude.settings` overlay can replace `statusLine` and add native hooks
  inside claude. Reserved renderer entries (onStart, lock-check webhook, permissions.deny,
  any-mcp) must not be removable by user config.
- ClusterSpec is shared by presets and clusters; the api has no per-user auth (SSO in front), so
  whoever edits a preset can already run code via terminals and init scripts.

## 2. Leader lease timeout

- Leadership today (`db/leadership.py:leadership_pass`, dispatcher only, under the per-cluster
  claim advisory lock `db/queue.py:_CLAIM_LOCK_NAMESPACE`): (1) initial leader = lowest-ordinal
  ready agent with a session; (2) queued `leadership_requests` (kind `handover` by the leader,
  epoch-fenced; kind `user`, no fence) judged by `_judge`; (3) lost leader: gone, or not ready for
  longer than `LEADER_GRACE_SECONDS = 30` (`unready_since`), replaced by `_free_longest`.
- A leader holds leadership indefinitely: there is no term or expiry. `cluster_leaders` (migration
  `0003_hive.sql`) has `since timestamptz`, `epoch`, `reason`, `unready_since`, so a term check
  `since < now() - lease` needs no new column. Leader changes NOTIFY `leader_changed`; the push loop
  (`dispatcher/hive.py`) sends the `hive_state` note to every agent. Routing: untargeted messages
  go to the leader (hive D8/D18), so a change only redirects the next untargeted message; a running
  turn is not interrupted.
- Hive design decisions in tension: D21 "handover only", D25 "no takeovers by agents (Q4), no
  forced handover (Q9)", D26 "advise, never force", D14 constants. A lease expiry is a forced,
  dispatcher-applied change; it needs explicit user confirmation and a MEMORY amendment.
- "Lease" could also mean making the 30 s unready grace configurable (Kubernetes Lease sense).
- tatara-new: no agent leader and no hive. The only leader election is the operator manager's own
  controller-runtime lease (`tatara-operator/cmd/manager/main.go`, LeaderElectionID
  `tatara-operator-leader`, `internal/config/config.go:LeaderElection`), no duration override. No parity reference.

## 3. Autoclose after time

- Lifecycle: `clusters.desired` is `active` or `deleting` (`0001_init.sql`). The only close path is
  discard: `DELETE /api/v1/clusters/{id}` (`api/clusters.py:discard_cluster`) calls
  `db/clusters.py:request_delete` (status-guarded `WHERE desired = 'active'`, generation + 1,
  NOTIFY). `reconciler/loop.py:Reconciler.reconcile_once` runs `_discard` for deleting
  clusters: `_quiesce` (scale to 0, ingester drain, `discard_quiesce_timeout_seconds`), `pre_discard`
  (discard hook export, `reconciler/discard_hook.py`), delete objects, `clusters.purge` (cascades
  every table). There is no stop/pause state.
- Readers of `desired`: dispatcher claim `db/queue.py` (`c.desired = 'active'`), leadership
  candidates, `db/views.py:summarize` (state `deleting`), `api/messages.py`, `api/workspace.py`,
  `reconciler/checks.py`, reconciler restart/rebootstrap.
- The reconciler loops every `reconcile_poll_seconds` (10) or on NOTIFY, so it can enforce a
  deadline with at most ~10 s lag. But `clusters` has one writer (api); the reconciler setting
  `desired = 'deleting'` would be a second writer of `clusters` (hard rule). Writer-safe options:
  (a) a derived predicate `created_at + spec.<autoclose> <= now()` read as closing by every
  `desired` reader and by `reconcile_once` (no migration, no new writer); (b) an api-process timer
  flipping `desired` (api has no background loop today); (c) amend the writer table so the
  reconciler may flip `desired` through a guarded UPDATE.
- Spec is immutable after create, so an autoclose spec field is fixed per cluster (snapshot from the preset).
- tatara-new: `ProjectSpec.AgentPodTTLSeconds` (default 3600, min 300) limits one pod's life,
  not the Task. `internal/agent/ttlstop.go:TTLDeadline` anchors on pod start or last conversation
  event; `internal/controller/task_stage.go` checks `agent.TTLExpired`, `TaskReconciler.ttlStop`
  calls `TTLStopper.StopWithHandoff` (one handoff turn, `TTLGrace` 60 s, then pod delete); the
  wrapper refuses turns past TTL with 410 (`session.ErrPodTTLExpired`). Clocks via
  `stage.ArmedClock` and `RequeueAfter`. No project-level auto-close.

## 4. Clusters in the hamburger menu

- `frontend/src/layout/TopBar.tsx:TopBar` opens `layout/SessionsMenu.tsx:SessionsMenu`, a left
  Drawer: top section "Sessions" lists every cluster (click selects it); bottom section "Settings"
  renders `settingsCategories`. `App.tsx:App` passes one category `{id: 'presets', label:
  'Presets'}` and switches `view` between `'cluster'` and `'presets'` (no router); `presets/PresetsPage.tsx`
  is the only settings page. There is no Clusters page; clusters are created from a preset
  (`clusters/NewClusterDialog.tsx`) and discarded from the tab menu (`DiscardClusterDialog`).
- tatara-new has no web UI.
- Other epics also add hamburger entries: agents-schedule-microservice and
  agents-webhook-microservice (todo), and frontend-decoupling (todo) moves the frontend out.

## Overlaps with other epics

- agent-init-scripts (PR #10, branch `agent-init-scripts`, not merged): diff vs main touches
  `spec.py` (adds `init_scripts`, `INIT_DIR`, `init_scripts_hash`), `api/clusters.py`,
  `api/schemas.py`, `db/clusters.py`, `reconciler/loop.py`, `reconciler/init.py`,
  `reconciler/checks.py`, `api/agent.py`, `tests/test_render.py`, `openapi.json`,
  `frontend/src/api/schema.d.ts`, `clusters/clusterSpecForm.ts`, `presets/PresetForm.tsx`,
  `layout/TopBar.tsx` (new `onInitScripts` prop, "Init scripts" action), `App.tsx`, `api/client.ts`, README, MEMORY.
  Every one of spec.py, clusterSpecForm.ts, PresetForm.tsx, TopBar.tsx, App.tsx, openapi.json and
  schema.d.ts is also touched here: build this epic on top of PR #10 after it merges.
- cluster-scaling (todo): touches `reconciler/loop.py`, `settings.py`, `db/clusters.py`,
  `api/clusters.py`, `api/schemas.py`, `k8s/on_start.py`, `api/agent.py`, `openapi.json`,
  `schema.d.ts`, `api/client.ts`, `chat/ChatView.tsx`; uses `orch-leadership-pass` (scale-down of
  a leader interacts with a lease rotation) and `orch-spec-runtime-mutable`. Overlap: spec.py
  validators (`_cap`), the reconciler loop, leadership, openapi and generated types.
- agents-helmfile: both epics end with a deploy pin, apply and smoke on
  `helmfile.yaml.gotmpl`, `values/agent-orchestrator/common.yaml`, `tests/test_orchestrator_release.py`, `scripts/smoke.sh`.

## Known, assumed, unknown

Known: every wrapper setting asked for exists in the wrapper 0.2.0 deployed image; the
orchestrator exposes model, effort, auto_compact_pct, env, peers and replicas only; leadership
has no expiry; the only close path is discard; the menu has a Sessions list and a Settings list
with Presets.

Assumed: no wrapper change or release (settings exist); the new fields are ClusterSpec fields,
so they live in presets and are snapshotted at create; "hooks" means ccw lifecycle hooks (the
`hooks:` section), not native Claude Code settings hooks.

Unknown: whether an idle `/compact` in a hive interacts with dispatch (does a compacting agent
report busy and get skipped by `_PICK`); whether user webhook hooks need egress from agent pods
beyond today's NetworkPolicy (none found in render.py); how a lease rotation should behave while
cluster-scaling drains the leader.

## Questions for the user (preferences)

1. Which wrapper settings to expose? Recommended: a typed set, not a raw config overlay:
   `hooks` (all 21 events, command and webhook, user entries added after the reserved onStart and
   lock-check entries), `auto_compact` {idle_seconds, instructions, min_context_tokens},
   `system_append` (added after the built-in prompt), extra `permissions` allow/deny (built-in
   denies kept), extra `mcp_servers` (`any-mcp` reserved), `plugins` {marketplaces, install},
   `turn_stall_seconds`, `max_restarts`, `restart_continue_prompt`, `turn_max_seconds`, and the
   agent `commands` list. Not exposed: extra_args, boot, server, paths, peers internals,
   claude_json, config_files, permission_mode, secret-kind Claude env vars.
2. Command hooks run with the pod's credentials in their environment. Allow command hooks as
   well as webhook hooks? Recommended: yes, both (tatara-new hooks are shell commands; preset
   editors can already run code via terminals and init scripts), with the risk stated in the README.
3. What should the leader lease timeout do at expiry? Recommended: optional per-cluster
   `leader_lease_seconds` (unset = today's indefinite lease); when a leader has led that long, the
   dispatcher moves leadership to the ready agent free the longest (reason `lease_expired`,
   epoch + 1, the hive_state note informs everyone), keeps the leader when no peer is ready, and
   never interrupts a running turn. This overrides hive "no forced handover" for clusters that set it.
4. What does autoclose do and when does the clock start? Recommended: optional per-cluster
   `autoclose_after_seconds` (minimum 300, like tatara-new's TTL floor), counted from cluster
   creation; at expiry the cluster is discarded through the existing path (agents stopped,
   discard hook export, everything deleted), with no handoff turn; the UI shows the time left.
5. What does the Clusters menu entry open? Recommended: a Clusters page in the main area, listed
   first in the Settings section above Presets, showing every cluster (slug, preset, state,
   pods ready, created, autoclose time left) with open, new and discard actions; the Sessions
   quick-switch list stays.

## Plan inputs

reuse
- ClusterSpec - agent-orchestrator src/agent_orchestrator/spec.py:ClusterSpec - new spec fields (hooks, auto_compact, lease, autoclose)
- validate_spec - agent-orchestrator src/agent_orchestrator/spec.py:validate_spec - server-side validation of new fields
- check_spec - agent-orchestrator src/agent_orchestrator/api/clusters.py:check_spec - create and preset paths
- _ccw_config - agent-orchestrator src/agent_orchestrator/k8s/render.py:_ccw_config - render hooks, auto_compact and other wrapper keys
- _lock_check_hook - agent-orchestrator src/agent_orchestrator/k8s/render.py:_lock_check_hook - reserved hook entry to keep ahead of user hooks
- HooksConfig / HookAction - claude-code-wrapper src/claude_code_wrapper/config.py:HooksConfig - shape and rules to mirror in ClusterSpec validation
- AutoCompactConfig - claude-code-wrapper src/claude_code_wrapper/config.py:AutoCompactConfig - shape and rules of idle auto-compact
- interpolate - claude-code-wrapper src/claude_code_wrapper/interpolation.py:interpolate - the `$$` escape the renderer must apply
- leadership_pass / _free_longest / _set_leader - agent-orchestrator src/agent_orchestrator/db/leadership.py:leadership_pass - lease expiry step
- request_delete / _discard / _quiesce / pre_discard - agent-orchestrator src/agent_orchestrator/db/clusters.py:request_delete, src/agent_orchestrator/reconciler/loop.py:Reconciler._discard - autoclose reuses discard
- Reconciler.reconcile_once - agent-orchestrator src/agent_orchestrator/reconciler/loop.py:Reconciler.reconcile_once - deadline check
- summarize - agent-orchestrator src/agent_orchestrator/db/views.py:summarize - state and time-left in views
- SessionsMenu settingsCategories - agent-orchestrator frontend/src/layout/SessionsMenu.tsx:SessionsMenu - Clusters entry
- PresetsPage - agent-orchestrator frontend/src/presets/PresetsPage.tsx:PresetsPage - pattern for a Clusters page
- PresetForm / clusterSpecForm - agent-orchestrator frontend/src/presets/PresetForm.tsx, frontend/src/clusters/clusterSpecForm.ts:FormValues - new fields in the preset editor
- DiscardClusterDialog - agent-orchestrator frontend/src/clusters/DiscardClusterDialog.tsx - discard action on the Clusters page

do-not-build
- idle auto-compact timer - claude-code-wrapper sessions.auto_compact (router.py:SessionRouter._arm_auto_compact) - wrapper 0.2.0
- hook runner (command and webhook) - claude-code-wrapper hooks.py:HookDispatcher - wrapper 0.2.0
- a wrapper release - every setting exists in wrapper 0.2.0, already pinned in agents-helmfile values/agent-orchestrator/common.yaml
- a new close/stop path - discard path (request_delete, Reconciler._discard) - reconciler/loop.py
- a lease table or column - cluster_leaders.since already records the term start - 0003_hive.sql

fix-as-ac
- config interpolation of user text - render.py:_ccw_config - every user string rendered into config.yaml has `$` escaped as `$$`, pinned by a test that a `${CLAUDE_CODE_OAUTH_TOKEN}` hook url or instruction renders literally
- reserved entries overridable - render.py:_ccw_config - the onStart hook, the lock-check hook, permissions.deny defaults and mcp_servers any-mcp survive any user value; user hooks are appended after them
- second writer of clusters - reconciler/loop.py - autoclose adds no writer of clusters.desired outside the api (or the README writer table and MEMORY are amended explicitly)
- spec immutability - spec.py:ClusterSpec - new fields are create-time only; MEMORY D4 amendment list stays replicas and init_scripts
- protocol constants - db/leadership.py:LEADER_GRACE_SECONDS - stays a module constant; the lease is a spec field, not a setting
- openapi drift - openapi.json, frontend/src/api/schema.d.ts - regenerated, tests/test_readme_api.py and `npm run check:api` pass
- frontend reserved env drift - frontend/src/clusters/clusterSpecForm.ts:RESERVED_KEY - not changed by this epic (noted only)

ideas
- adopted: tatara-new LifecycleHooks are shell commands run by the wrapper; ccw hooks are the superset - tatara-operator/api/v1alpha1/project_types.go:AgentSpec.Hooks
- adopted: TTL floor of 300 s and deadline enforced by the reconcile loop - tatara-operator ProjectSpec.AgentPodTTLSeconds, internal/controller/task_stage.go
- rejected: one handoff turn before close - tatara-new TTLStopper.StopWithHandoff; discard already exports history through the discard hook
- rejected: raw wrapper config overlay in ClusterSpec - would expose extra_args, boot, server and paths (credentials and PTY control)
- rejected: configurable LEADER_GRACE_SECONDS as "the lease" - hive D14 keeps it a constant; open in question 3
- adopted: derived closing predicate on created_at + spec field keeps clusters single-writer - README single-writer table
