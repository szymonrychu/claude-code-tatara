# configuration improvements design

## Summary

More of tatara-new's configurability reaches the Python platform. A preset or cluster spec gets a typed `wrapper` block (hooks, idle auto-compact and a fixed list of other claude-code-wrapper settings), an optional `leader_lease_seconds` for hive clusters and an optional `autoclose_after_seconds`. The renderer merges the block into the wrapper config after the reserved entries, with every user string escaped against `${VAR}` interpolation. A lease expiry is a handover applied by the dispatcher at the leader's turn boundary. Autoclose is a status-guarded flip to `deleting` by the api, so the existing discard path does the rest. The agents-web UI (built by frontend-decoupling) gets form inputs for every field and a Clusters page in the hamburger Settings list above Presets. Each capability is documented in the orchestrator README, proven by an API-only kind e2e test, released, pinned, applied and smoked.

## Intent and why

The user's request (README, verbatim): expose more claude-code-wrapper settings (including hooks and idle_auto_compact), an optional leader lease timeout, an optional autoclose of a cluster after a time, and a Clusters entry in the hamburger menu above Presets. The overall target is to get more of tatara-new's configurability into this platform. Today the orchestrator exposes only model, effort, auto_compact_pct, env, peers and replicas of the wrapper; a leader holds leadership indefinitely; a cluster lives until someone discards it; and clusters have no settings page.

## Goals

- G1: `POST /api/v1/clusters` and the preset routes accept `spec.wrapper` with the typed settings of D1, validated server side with named errors, and the rendered wrapper config carries them after the reserved entries (D2).
- G2: no user string in `spec.wrapper` can read a pod env variable through wrapper interpolation; a `${CLAUDE_CODE_OAUTH_TOKEN}` value renders as that literal text.
- G3: a hive cluster with `leader_lease_seconds` set changes leader with reason `lease_expired` once the lease has run out and the leader is between turns; a running turn is never interrupted; with no ready peer the leader stays.
- G4: a cluster with `autoclose_after_seconds` set goes to `deleting` within about 10 s of `created_at + autoclose_after_seconds` and is then discarded as by `DELETE /api/v1/clusters/{id}`; values below the floor (default 300 s) are refused.
- G5: the cluster view shows `closes_at`, `leader_since` and `leader_reason`.
- G6: the agents-web Settings list shows Clusters first, above Presets; it opens a Clusters page with every cluster and open, new and discard actions.
- G7: each capability is documented in the orchestrator README and covered by an API-only kind e2e test; the agents namespace runs the release and the live smoke passes.

## Non-goals

- A raw wrapper config overlay, or exposing `extra_args`, `boot`, `server`, `paths`, peers internals, `claude_json`, `config_files`, `permission_mode` or secret-kind Claude env vars.
- Any claude-code-wrapper code change or release.
- A pod TTL, a handoff turn before autoclose, or a stop/pause cluster state.
- Making `LEADER_GRACE_SECONDS` or `PUSH_INTERVAL_SECONDS` configurable (hive D14).
- Editing the new fields on a running cluster.

## Anti-goals

- A reserved renderer entry (the onStart hook, the lock-check hook, the built-in permission denies, the `any-mcp` MCP server, the ASK_IN_WRITING prompt) removed or reordered by user config.
- A second writer of `clusters` outside the api.
- An agent taking leadership (hive D21), or a lease rotation interrupting a running turn.
- UI changes landing in `agent-orchestrator/frontend` instead of agents-web.

## Constraints

- Hard rules: Python only except the TypeScript web UI; single writer per table, queue tables only through status-guarded updates.
- Spec is immutable after create except `replicas` and `init_scripts` (MEMORY 2026-10-24 amending D4); the new fields are create-time only and snapshotted from the preset.
- Hive D14: `LEADER_GRACE_SECONDS` and `PUSH_INTERVAL_SECONDS` stay module constants.
- The wrapper accepts these settings since 0.2.0 (`code/claude-code-wrapper/src/claude_code_wrapper/config.py:HooksConfig`, `AutoCompactConfig`, `SessionsConfig`, `LimitsConfig`, `PluginsConfig`); the orchestrator dev dependency pins wrapper 1f64e9f (0.2.0), and `tests/test_render.py::test_rendered_ccw_config_validates` loads the rendered config with the wrapper's own `load_config`.
- `/api/v1` is additive only (README Versioning).
- Order: runs after agent-init-scripts, cluster-scaling and frontend-decoupling (README blockers). UI work lands in the agents-web repo that frontend-decoupling creates.

## Decisions

### D1: Typed wrapper settings under `spec.wrapper`
`ClusterSpec.wrapper: WrapperSettings | None` with `extra="forbid"` models mirroring the wrapper: `hooks` (map of the 21 `HOOK_EVENTS` to at most 20 actions each; `command` {run, env} or `webhook` {url, secret, headers, retries}; common timeout_seconds, blocking, on_error, matcher on onAgentToolCall/onToolResult only, interval_seconds and when on onTick only with interval required), `auto_compact` {idle_seconds >= 0, instructions one line <= 2000 chars without control characters, min_context_tokens >= 0}, `system_append` (<= 16384 chars), `permissions` {allow, deny}, `mcp_servers` (stdio {command, args, env} or http/sse {url, headers}; name `any-mcp` refused), `plugins` {marketplaces [{name, source}], install [{plugin name@marketplace, scope, required}], marketplace known or `claude-plugins-official`}, `turn_stall_seconds` >= 0, `max_restarts` 0..10, `restart_continue_prompt`, `turn_max_seconds` >= 0, `agent_commands` (subset of compact, context, mcp, reload-plugins, reload-skills). The orchestrator defines its own models because the wrapper is only a dev dependency; a render test proves the wrapper accepts every rendered value. Alternatives: a raw overlay (rejected by the user: exposes extra_args, boot, server and paths), flat top-level fields (rejected, my call: the block keeps the spec readable and presets sparse). Serves A1.

### D2: Reserved entries first, user strings escaped
`k8s/render.py:_ccw_config` appends user hooks after the reserved `onStart` and lock-check `onAgentToolCall` entries, appends user denies after `EnterPlanMode, ExitPlanMode, AskUserQuestion` (deduplicated), adds user MCP servers beside `any-mcp`, appends `system_append` after `ASK_IN_WRITING_PROMPT` with a blank line, and maps the other keys to `sessions.turn_stall_seconds`, `sessions.max_restarts`, `sessions.restart_continue_prompt`, `sessions.auto_compact`, `sessions.commands.agent`, `limits.turn_max_seconds`, `claude.permissions.allow`, `plugins`. Every string value from `spec.wrapper` (not keys, which the wrapper never interpolates) has `$` replaced by `$$` (user decision), so the wrapper's `interpolation.py:interpolate` yields the literal text and a shell command still sees `$VAR` at run time. Alternatives: rejecting `${` in user text (rejected, my call: breaks legitimate shell). Serves A1, A2.

### D3: Command and webhook hooks, with the exposure documented
Both hook types are allowed (user decision). The README `## Security` section states that command hooks run `sh -c` in the agent pod with the wrapper's full environment, which carries `CLAUDE_CODE_OAUTH_TOKEN`, `CCW_AUTH_TOKEN`, `CCW_PEER_TOKEN` and `ORCH_AGENT_TOKEN`; that preset editors can already run code through terminals and init scripts; that a webhook `secret` is stored in the preset and cluster spec in plain text and returned by the API; and that wrapper interpolation is disabled for these values (D2). Serves A2.

### D4: Leader lease as a handover at a turn boundary
`ClusterSpec.leader_lease_seconds: int | None` (60..604800, hive clusters only: refused when `max_replicas` is 1, my call). `db/leadership.py:leadership_pass` gets step 4 after the lost-leader step: when the leader row's `since` is older than the lease, the leader is ready and between turns (its `agent_status.state` is `idle` and no message assigned to it is `dispatching` or `verifying`), and `_free_longest` finds another ready agent, `_set_leader` moves leadership with reason `lease_expired` (epoch + 1, `since = now()` starts the next term, NOTIFY `leader_changed`, the push loop sends `hive_state` to every agent). A busy leader keeps leadership until its turn ends; no ready peer keeps the leader and the lease is re-checked on every pass. `_CANDIDATES` adds the lease condition so the dispatcher's periodic wake (`dispatch_poll_seconds`) runs the pass. This respects hive D21 (no agent takes leadership; the change is a handover of the current leader's term, never a takeover) but amends hive D26 ("no forced handover") for clusters that opt in; the amendment is recorded in MEMORY.md and is gate question Q1. Alternatives: a note asking the leader to hand over (rejected, my call: an advisory lease never expires), configurable `LEADER_GRACE_SECONDS` (rejected: hive D14). Serves A3.

### D5: Autoclose from creation through the discard path, swept by the api
`ClusterSpec.autoclose_after_seconds: int | None`, counted from `clusters.created_at` (user decision). A sweeper task started in the api lifespan (`api/autoclose.py`, poll `AUTOCLOSE_POLL_SECONDS = 10`, a module constant like hive D14) calls `db/clusters.py:close_expired`, one status-guarded `UPDATE clusters SET desired = 'deleting', generation = generation + 1 WHERE desired = 'active' AND spec ? 'autoclose_after_seconds' AND created_at + make_interval(secs => (spec->>'autoclose_after_seconds')::int) <= now()` with a `cluster_changed` NOTIFY per row, the same write `request_delete` makes. The reconciler's `_discard` (quiesce, discard hook export, delete, purge) runs unchanged. The api stays the only writer of `clusters.desired`, every `desired` reader is unchanged, and two api replicas are safe through the guard. No handoff turn (user decision). Alternatives: a derived closing predicate read by every `desired` reader (rejected, my call: eight readers to change and a window where a closing cluster still accepts messages), the reconciler flipping `desired` (rejected: a second writer of `clusters`). Serves A4.

### D6: The autoclose floor is a setting
`Settings.autoclose_min_seconds` (`ORCH_AUTOCLOSE_MIN_SECONDS`, default 300, the user's minimum) is checked in `spec.validate_spec`, like `max_replicas`; the kind e2e values set 30 so the e2e does not wait five minutes. (my call) Serves A4.

### D7: Clusters page in the agents-web Settings list, above Presets
agents-web `App.tsx` passes `settingsCategories` with `{id: 'clusters', label: 'Clusters'}` first and Presets second; a new `clusters/ClustersPage.tsx` lists every cluster (slug, preset, state, pods ready of replicas, created, time left to `closes_at` or "never") with open (selects the cluster view), new (`NewClusterDialog`) and discard (`DiscardClusterDialog`) actions. The Sessions quick-switch list stays. Webhook and schedule epics later insert their entries between Clusters and Presets (cross-epic contract `web-settings-menu-order`). Serves A5, A8.

### D8: Preset form inputs for every new field
agents-web `PresetForm.tsx` and `clusterSpecForm.ts`: number inputs for leader lease (shown for hive specs only), autoclose, auto-compact idle seconds and min context tokens, turn stall, max restarts, turn max; text inputs for auto-compact instructions, system append and restart continue prompt; a multi-select for agent commands; comma lists for permissions allow and deny; JSON text areas (the existing any-mcp pattern) for hooks, MCP servers and plugins. Empty inputs stay unset so presets stay sparse. (my call) Serves A1, A3, A4.

### D9: Documented API and API-only kind e2e per capability
README `### Cluster configuration` under `## API` documents `spec.wrapper`, `leader_lease_seconds`, `autoclose_after_seconds`, the floor setting, the new view fields and every validation message family. `tests/e2e/test_e2e_kind.py` adds three API-only tests: a hook and idle auto-compact cluster (a command hook writes a file read back through the files API; a `compacted` event appears through the events API), a lease cluster (`leader_reason` becomes `lease_expired` and the epoch rises), an autoclose cluster (`closes_at` shown, then 404). The live smoke creates a cluster with every new field and checks the view. (user decision) Serves A6.

### D10: Release is the main builds, pinned, applied and smoked
The orchestrator and agents-web main builds publish their charts and images on merge; agents-helmfile pins both, then `mise run diff`, `mise run apply` and `mise run smoke` run. No wrapper or any-mcp release. (user decision) Serves A7.

### D11: View fields for lease and autoclose
`ClusterView` adds `closes_at: datetime | None` (`created_at + autoclose_after_seconds`), `leader_since: datetime | None` and `leader_reason: str | None` from `cluster_leaders`. (my call) Serves A3, A4, A5.

### D12: Sequencing after the three blockers, UI in agents-web
The epic starts after agent-init-scripts, cluster-scaling and frontend-decoupling are done; the UI tasks target the agents-web repo. agents-web paths below assume frontend-decoupling moves `frontend/` with its layout (`src/...`, a vendored `openapi/agent-orchestrator.json`); the two web tasks and the deploy pin are amended with `ticket.py amend` if its plan names other paths. (orchestrator ruling) Serves A8.

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| start-discovery (code, LSP, cartographers) | ran: `discovery.md` (this epic), frontend-decoupling `discovery.md` | typed settings mirror `claude_code_wrapper/config.py`; discard reuse (`db/clusters.py:request_delete`, `reconciler/loop.py:Reconciler._discard`); `cluster_leaders.since` as the term start (`0003_hive.sql`) | raw overlay (credentials and PTY control) |
| research-code-internal | ran inside discovery (Plan inputs reuse list) | `_lock_check_hook`, `leadership_pass`, `_free_longest`, `summarize`, `SessionsMenu`, `PresetsPage`, `DiscardClusterDialog` | none |
| research-code-external | ran (tatara-new prior art) | LifecycleHooks are shell commands (`tatara-operator/api/v1alpha1/project_types.go:AgentSpec.Hooks`); TTL floor 300 s enforced by a reconcile loop (`ProjectSpec.AgentPodTTLSeconds`, `internal/controller/task_stage.go`) | one handoff turn before close (`TTLStopper.StopWithHandoff`): discard already exports history |
| research-papers | skipped: no algorithmic core (config plumbing, a timer, a UI page) | none | none |
| research-docs | skipped: no external API used in a new way; the wrapper surface is in-house and pinned by the render validation test | none | none |

## Research inputs

| Source | Entry | Lands in |
|---|---|---|
| discovery reuse | ClusterSpec, validate_spec | spec-config-fields |
| discovery reuse | check_spec (create and preset paths) | config-cluster-views |
| discovery reuse | _ccw_config, _lock_check_hook, interpolate, HooksConfig, AutoCompactConfig | render-wrapper-settings |
| discovery reuse | leadership_pass, _free_longest, _set_leader | leader-lease-expiry |
| discovery reuse | request_delete, Reconciler._discard, _quiesce, pre_discard, reconcile_once | autoclose-sweeper (reconcile_once unchanged: rejected as the deadline check, see D5) |
| discovery reuse | summarize | config-cluster-views |
| discovery reuse | SessionsMenu settingsCategories, PresetsPage, DiscardClusterDialog | web-clusters-page |
| discovery reuse | PresetForm, clusterSpecForm | web-form-config-fields |
| discovery do-not-build | idle auto-compact timer, hook runner, wrapper release | rejected: provided by wrapper 0.2.0; no task builds them |
| discovery do-not-build | a new close/stop path | rejected: autoclose-sweeper reuses the discard path |
| discovery do-not-build | a lease table or column | rejected: leader-lease-expiry reads `cluster_leaders.since` |
| discovery fix-as-ac | config interpolation of user text | render-wrapper-settings AC2 |
| discovery fix-as-ac | reserved entries overridable | render-wrapper-settings AC1 |
| discovery fix-as-ac | second writer of clusters | autoclose-sweeper AC4 |
| discovery fix-as-ac | spec immutability | spec-config-fields AC5 |
| discovery fix-as-ac | protocol constants | leader-lease-expiry AC6 |
| discovery fix-as-ac | openapi drift | config-cluster-views AC5, web-form-config-fields AC1 |
| discovery fix-as-ac | frontend reserved env drift (noted only) | rejected: not changed by this epic |
| discovery ideas | adopted: LifecycleHooks are shell commands | D3 |
| discovery ideas | adopted: TTL floor 300 s, deadline by a loop | D5, D6 |
| discovery ideas | rejected: handoff turn before close | D5 |
| discovery ideas | rejected: raw overlay | D1 |
| discovery ideas | rejected: configurable LEADER_GRACE_SECONDS | D4 |
| discovery ideas | adopted: derived closing predicate | rejected in favour of the api sweeper (D5) |
| frontend-decoupling brief | SettingsCategory menu entries; UI in agents-web | web-clusters-page |
| frontend-decoupling brief | vendored openapi copy per backend | web-form-config-fields |

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 Typed wrapper settings under `spec.wrapper` | spec-config-fields, render-wrapper-settings |
| D2 Reserved entries first, user strings escaped | render-wrapper-settings |
| D3 Command and webhook hooks, with the exposure documented | render-wrapper-settings |
| D4 Leader lease as a handover at a turn boundary | spec-config-fields, leader-lease-expiry |
| D5 Autoclose from creation through the discard path | spec-config-fields, autoclose-sweeper |
| D6 The autoclose floor is a setting | spec-config-fields, kind-e2e-config |
| D7 Clusters page above Presets | web-clusters-page |
| D8 Preset form inputs for every new field | web-form-config-fields |
| D9 Documented API and API-only kind e2e | config-cluster-views, kind-e2e-config, smoke-config-check |
| D10 Release is the main builds, pinned, applied and smoked | deploy-pin-config |
| D11 View fields for lease and autoclose | config-cluster-views |
| D12 Sequencing after the three blockers | web-form-config-fields, web-clusters-page |

## Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| `orch-spec-config-fields` | spec-config-fields | render-wrapper-settings, leader-lease-expiry, autoclose-sweeper, config-cluster-views | `code/agent-orchestrator/src/agent_orchestrator/spec.py` |
| `orch-leader-lease` | leader-lease-expiry | kind-e2e-config | `code/agent-orchestrator/src/agent_orchestrator/db/leadership.py` |
| `orch-cluster-autoclose` | autoclose-sweeper | kind-e2e-config | `code/agent-orchestrator/src/agent_orchestrator/db/clusters.py` |
| `orch-cluster-config-api` | config-cluster-views | kind-e2e-config, web-form-config-fields, web-clusters-page, smoke-config-check | `code/agent-orchestrator/README.md` |
| `web-orch-schema-config` | web-form-config-fields | web-clusters-page | `code/agents-web/src/api/schema.d.ts` |
| `web-settings-menu-order` | web-clusters-page | none | `code/agents-web/src/App.tsx` |

`web-settings-menu-order` has no consumer yet: the webhook and schedule epics register `contract use` when they are planned behind this epic.

Cross-epic contracts used, owned elsewhere: `orch-leadership-pass` and `orch-render-hash-invariant` (hive), `orch-presets-api`, `orch-cluster-create-api` (cluster-presets), `orch-settings-menu` (web-ui epic, moved by frontend-decoupling), `agent-orchestrator-settings-env`, `agent-orchestrator-chart`, `agent-orchestrator-image`.

## Review focus

- render: no reserved entry removable or reordered; every user string value escaped, keys untouched; rendered config loads with the wrapper's `load_config`; config hash changes only with the spec.
- leadership step 4: runs inside the existing claim-lock transaction; never moves a leader that is busy or has a dispatching/verifying message; epoch fence intact; no takeover path; `LEADER_GRACE_SECONDS` untouched.
- autoclose: one guarded UPDATE, database clock, NOTIFY in the same transaction, no write besides `desired` and `generation`; sweeper task cancelled cleanly on shutdown.
- e2e: every created cluster torn down; waits bounded.

## Left to the builder

- Exact UI copy and layout of the Clusters page and the new form inputs, within D7 and D8.
- Internal names of the orchestrator's wrapper-settings models, within the field list of D1.
- Whether the sweeper sleeps a fixed 10 s or until the next deadline, capped at 10 s.

## Assumptions and unknowns

- agents-web paths (`src/...`, `openapi/agent-orchestrator.json`, the agents-web chart values file and release test in agents-helmfile) follow the frontend-decoupling brief; confirmed by reading frontend-decoupling's task files when they exist, and amended with `ticket.py amend` (D12).
- The fake claude in the kind agent image handles `/compact` (`code/claude-code-wrapper/tests/fake_claude/fake_claude.py` documents it) and the ingester stores every event type, so a `compacted` event is visible through `GET /api/v1/clusters/{id}/events?types=compacted`; confirmed by the kind e2e.
- The dispatcher wakes at least every `dispatch_poll_seconds` and runs `_drain_leadership` on each wake (`dispatcher/loop.py`), so a lease expiry is acted on without a NOTIFY; pinned by the leadership-pass tests.
- Agent pods have no NetworkPolicy limiting webhook egress (none in `k8s/render.py`); a user webhook reaches whatever the cluster network allows.

## Open questions

- Q1: A leader lease expiry is a handover the dispatcher applies at the leader's turn boundary, which amends hive D26 (no forced handover) for clusters that set leader_lease_seconds; accept this? [recommended: yes]

## Irreversible operations in scope

- `mise run apply` of the agents namespace (deploy-pin-config): covered by the user's scope approval (releases, pin bumps, helmfile apply plus smoke are tasks of this epic); reversible by re-pinning the previous charts and images and applying again.
- Publishing the orchestrator and agents-web main-build charts and images on merge to main (immutable versions); covered by the same approval.
- Autoclose discards clusters and their history when their time runs out; only clusters that set `autoclose_after_seconds` are affected, and the discard hook export runs first.
