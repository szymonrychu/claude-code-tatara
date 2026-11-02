# agent-preset-editing: agents edit presets, humans keep the security switches

Status: Approved 2026-11-02 by the user (mx-99 #919, chat m184: 'Go for preset and inactivity. Put
into the hive which can pick it up faster'). Every Recommended option accepted. Assigned to
claude-code-tatara-2. Not yet built.

Coordination notes:
- Orchestrator migrations take the next free number at merge time, 0029 or later (0028 is claimed
  by session-orchestration-mcp; `migrate.py` is set-based, never reuse a number). Wherever this
  plan says 0028, read "next free number at merge".
- Versions are the next free minor at merge, whatever this plan names.
- The small first step (section 4) closes a live escalation: superleaders can set `kube_access`
  and `session_messaging` through admin preset create/replace. It should go first.
- hive-inactivity-limits (`docs/future/hive-inactivity-limits.md`) is a separate plan; the two do
  not depend on each other.

Status: spec (brainstorming plan), the one human gate. Docs only; nothing implemented.
Research date: 2026-11-02, against `origin/main` of agents-orchestrator (`2ff61fa`),
any-mcp-tatara-plugins and agents-web.

## 1. What and why

The user, verbatim: "Eventually I want superleaders to be able to edit nearly everything in the
system (including presets). I want to reserve only few fields for human operators (gate for
Kubernetes access, gate for superleader and other security related settings). I also want session
leader to be able to adjust its preset if needed (with the same limitations)."

Two needs this epic must unblock soon:

- (a) per-preset usage quota holds, for example 80% for the webhook, schedule and chat presets
  (`spec.usage_quota.five_hour_pct` / `seven_day_pct`);
- (b) updating a preset's `SSH_PRIVATE_KEY_B64` env value after infra rotates the key.

Today both are done by the user in the web UI (main API `/api/v1` behind oauth2-proxy). Agents
reach only `/agent/v1` (agent token) and superleaders also `/agent/v1/admin`.

The goal is one rule, enforced in one place on the server: every preset field is agent-editable
except a short human-only list; a superleader edits the presets it may manage, a session leader
edits only its own session's source preset; every edit is validated exactly like a user edit,
never echoes a secret, and leaves an audit record the user can read.

## 2. Research findings

### 2.1 The spec model (agents-orchestrator `src/agents_orchestrator/spec.py`)

`SessionSpec` (spec.py:628-677), every field, with what bounds it today:

| Field | Bound today | Security note |
|---|---|---|
| `replicas`, `max_replicas`, `static` | 1-16, `ORCH_MAX_REPLICAS` (validate_spec 1017-1022) | cost only |
| `image` | must be in `image_allowlist()` (spec.py:962-967, settings.py:762-766, `ORCH_AGENT_IMAGES` + `ORCH_AGENT_IMAGE`) | allowlist is a deploy setting |
| `model`, `effort` | settings lists (spec.py:972-983) | none |
| `peers` | bool | ccw peer messaging |
| `workdir` | DNS label | none |
| `pvc_size`, `resources` | caps, cpu/memory only (spec.py:125-138, 1009-1032) | cost only |
| `env` | `EnvVar {value, protected, expand}` (spec.py:298-336); reserved names `POD_NAME`, `CCW_*`, `CLAUDE_*`, `ANTHROPIC_*`, `ORCH_*`, `*_PROXY`, `*_BASE_URL` refused (spec.py:39-40, 807-827); at most 50 protected | protected values are write-only |
| `any_mcp_config` | any-mcp model, `orchestrator` plugin name reserved, https git sources only (spec.py:1041-1057) | code in the agent pod |
| `max_attempts`, `auto_compact_pct` | ranges | none |
| `discard_hook_url` | http(s) URL (spec.py:829-836) | the reconciler POSTs the full JSONL export of the session to it (`reconciler/discard_hook.py:1-5, 36-37`): transcript exfiltration and SSRF from the orchestrator's network position |
| `init_scripts` | 20 x 16 KiB templates | code in the init Job |
| `start_prompt` | Jinja template | prompt |
| `any_mcp_sources` | https git only, no credentials in URL (spec.py:151-170, 760-777) | code in the agent pod |
| `wrapper.hooks` | known events, command or webhook (spec.py:380-409, 502-525) | command runs in the pod; webhook `secret`/`headers` may reference `${ENV}` |
| `wrapper.mcp_servers` | reserved names `any-mcp`, `ccw` | stdio command in the pod; `env`/`headers` may reference `${ENV}` |
| `wrapper.plugins`, `system_append`, `auto_compact`, stall/restart settings, `agent_commands` | shapes and sizes | prompt/behaviour |
| `wrapper.permissions` (allow/deny) | free lists | Claude Code permission rules |
| `wrapper.permission_mode` | `bypassPermissions` or `auto`, unset = bypass (spec.py:256-259, 497) | `auto` is the stricter mode |
| `leader_lease_seconds`, `autoclose_after_seconds`, `discard_after_idle_seconds` | ranges | none |
| `reuse_running_agent` | bool, read only by trigger services (spec.py:657-660) | none |
| `session_messaging` | bool, the superleader flag (spec.py:661-663) | grants the admin API and `secret_set` (admin.py:42-52, on_start.py:58-77) |
| `kube_access` | bool, needs `ORCH_KUBE_ACCESS_SERVICE_ACCOUNT` (spec.py:664-666, 990-997) | cluster-admin-equivalent ServiceAccount (orchestrator MEMORY 2026-10-26 D2/D3) |
| `usage_quota` | 1-100 per metric (spec.py:619-625, 669) | budget; a set value replaces `ORCH_USAGE_QUOTA_DEFAULT` (default 100), also upward (usage_gate.py:48-72) |
| `docker` + `docker_storage/cpu/memory` | needs `ORCH_DOCKER_IMAGE`; sizes capped (spec.py:670-675, 998-1008) | privileged DinD sidecar, root-equivalent on the node (agents-web PresetForm.tsx:423) |
| `cache` | keys; `preset-` prefix reserved except own (spec.py:546-578) | a custom restore key can read another preset's archive |

Preset row columns besides the spec (`db/presets.py:39-48`): `name`, `is_default` (not settable
by any API), `superleader_manageable` (migration 0023, read live, MEMORY 2026-11-01
preset-superleader-switch), `labels` (0027), `created_at`, `updated_at`. There is no revision or
version column.

`validate_spec(spec, settings, stored)` (spec.py:950-1081) is the one server rule set; `stored`
exempts a model/effort/image/cache/kube_access/docker value that left the settings when it is
unchanged from the stored preset.

### 2.2 Preset write paths

- Main API (`api/presets.py`): `POST /api/v1/presets` (258-263), `PUT /api/v1/presets/{id}`
  full replace (272-277), `DELETE` (280-286), `POST .../copy` (319-324),
  `PUT /api/v1/presets/{preset}/secrets/{name}` write-only secret (340-377). The service functions
  `create` (164-186), `replace` (197-227), `remove`, `copy` (299-316), `put_secret` (340-364) are
  shared with the admin routes. `_validated` (53-71) splits protected values out and runs
  `check_spec` (sessions.py:183-203, which is `check_caller_cache_key` plus `validate_spec` plus
  resource defaults) with the stored spec. `_save` (85-128) writes the row, new Secret versions and
  `sync_declared` in one transaction and deletes written versions on failure.
- `db/presets.update` (120-148) is last-write-wins: `SELECT ... FOR UPDATE` then replace name and
  spec, `updated_at = now()`. No optimistic concurrency, no revision, no NOTIFY ("nothing
  listens for preset changes", db/presets.py:1-5).
- Generation and rollout: a preset write never touches a running session. A session snapshots
  the preset spec at create (`_create_from_preset`, sessions.py:400-410; migration 0002 comment)
  and the protected Secret names in `sessions.secret_versions` (MEMORY superleader-crud O4). A
  rotated secret reaches only sessions created after it; a restart reuses the snapshot.
- Two in-place write-backs already go session to source preset: `PUT /agent/v1/init-scripts`
  (agent.py:188-197, `sessions.edit_init_scripts` 511-538, `db/sessions.set_init_scripts`
  346-383, no generation bump) and the main-port `PUT /api/v1/sessions/{id}/permission-mode`
  (sessions.py:558-580, `db/sessions.set_permission_mode` 386-430, bumps generation when the value
  changes). The init-scripts route is open to any agent of the session (not only the leader) and
  checks neither `superleader_manageable` nor any other preset switch: it is the existing
  "agent writes its own source preset" precedent.

### 2.3 Agent and admin API, auth

- `require_agent` (agent.py:69-95): `X-Orch-Session`, bearer equal to
  `tokens_for(settings, session_id).agent` (one token per session, shared by all its agents), and
  the socket peer IP of a live agent pod of that session. There is no separate leader token:
  leadership is a row (`leadership.current_leader`), an alone session's only agent leads
  (`_leads`, agent.py:401-406). Leader-only routes answer 403 `not_leader`.
- Superleader detection: `require_superleader` (admin.py:42-52) is `require_agent` plus
  `session.spec.session_messaging` true, whoever created the session (MEMORY 2026-11-01 user
  decision). Any agent of a superleader session passes, not only its leader.
- Admin preset routes (admin.py:157-224) are by id or name and see only
  `superleader_manageable` presets (`_manageable_preset` 160-165, others 404). Admin create forces
  `superleader_manageable = true`; sending `false` is 422 `manageable_main_port_only`
  (presets.py:150-153, 171-174, 205-207). Admin session create requires a manageable preset
  (sessions.py:284-285, 406).
- **Finding F1 (live escalation):** the admin `POST`/`PUT /agent/v1/admin/presets` accept every
  spec field. A superleader can today create or edit a manageable preset with `kube_access: true`,
  `session_messaging: true`, `docker: true` or any `discard_hook_url`, then start a session from it
  (`session_create`), granting itself cluster-admin, new superleaders or a privileged sidecar. No
  test refuses it (`tests/test_admin_presets.py` has no case on these fields). The plugin offers
  the tools (`preset_create`, `preset_replace`, plugin admin.py:112-129).
- **Finding F2 (round-trip friction):** `GET` returns protected entries as
  `{protected, expand, set, version, updated_at}` (`secret_view.redact_spec_dict`,
  secret_view.py:48-59), but the request model `EnvVarIn` is `extra="forbid"` with only
  `value/protected/expand` (spec.py:339-357). A read-modify-write `preset_replace` of a preset with
  a protected variable is 422 unless the agent strips the three output fields first. The web form
  rebuilds rows and does not hit it (PresetForm.tsx:227-237).
- **Finding F3 (needs (a) and (b) are reachable today on manageable presets):** `preset_replace`
  can set `usage_quota`, and the local `secret_set` tool (plugin secrets_local.py, reference
  `from_file`/`from_env`/`from_command`, value never in the transcript) sets a protected value
  through `PUT /agent/v1/admin/presets/{ref}/secrets/{name}` (admin.py:217-224). What blocks them
  is (i) the webhook, schedule and chat presets being manageable or not (unknown from the repo; a
  question), (ii) F2, (iii) whether `SSH_PRIVATE_KEY_B64` is a protected variable or a plain one
  (a plain value is readable by every preset GET and would have to pass through a tool call).

### 2.4 Secrets

- Stored specs never hold a protected value: `SessionSpecIn.split` (spec.py:921-947) moves values
  out; each value becomes an immutable Secret `ps-<id8>-<sha6>-v<N>` (`k8s/secrets.py`, MEMORY O3)
  written by the api's Secrets create/patch/delete Role (no get). Reads always rebuild protected
  entries from metadata (secret_view.py:1-5). A 1 MiB cap is 413 `secret_too_large`.
- The admin audit (admin.py:63-95) logs one line and writes one `events` row
  (`type admin_call`, data method, path, status, session slug, secret names) with no values and no
  bodies; gate refusals are not audited. The plugin refuses a protected value inside
  `preset_create`/`preset_replace`/`session_create` (secrets_local.py:55-70).
- Accepted risk R1 (README Security, MEMORY O11): a superleader can exfiltrate a protected value
  through a child session (or a hook header `${NAME}`, an init script, an MCP env). Write-only
  secrets are transcript hygiene, not a boundary against a hostile editor.
- `db/export.py` selects an explicit column list, so `secret_versions` never reaches agents-history.

### 2.5 Audit and history of preset edits

None beyond the `admin_call` event row above. Main-port preset writes, the init-scripts and
permission-mode write-backs and secret writes on the main port are not recorded anywhere; there is
no before/after, no field list, no revision table (no migration mentions one). The user identity
does not reach the api (no oauth2-proxy user header is read anywhere in the orchestrator, chart or
helmfile). agents-web has no view of `admin_call` rows (no `admin_call` string in `src/`).

### 2.6 Plugins, web, tool allowlist

- any-mcp-tatara-plugins `orchestration/orchestrator/.../admin.py:101-140`: declarative
  `AdminRow`s (`presets_list`, `preset_get`, `preset_create`, `preset_replace`, `preset_delete`,
  `preset_copy`, ...); a contract test pins every row to `tests/fixtures/orchestrator_openapi.json`
  (plugin MEMORY superleader-crud PL1). Non-admin rows (`init_scripts_get/edit`, `self_close`,
  task tools) live in `__init__.py` and `tasks.py`.
- The orchestrator renders the allowed tool names into each pod's any-mcp config
  (`k8s/on_start.py:44-55` `ADMIN_TOOLS`, `orchestrator_allow` 58-77): admin tools exactly when
  `session_messaging` is on; init-scripts tools for every session.
- agents-web `src/presets/PresetForm.tsx`: switches "Superleader" (`session_messaging`, 409-410),
  "Superleader can manage" (413-414), Docker (420-428), Kubernetes access, usage quota fields
  (388-394), protected env rows replaced through the secret route (227-232).

### 2.7 Versions, migrations, overlapping work

- Latest tags: agents-orchestrator `v3.5.0`, any-mcp-tatara-plugins `v0.11.0`, agents-web
  `v0.15.1`.
- Migrations on origin/main: 0001-0024 (0010 missing) and 0027. 0025 is taken by
  cache-retention-settings (PR #57, `0025_cache_sweep_settings.sql`), 0026 is claimed by
  hive-self-close (docs/plans/hive-self-close/implementation.md:20). **Next free: 0028.**
- Open orchestrator PRs: #57 cache-retention-settings (migration 0025, no preset code), #36
  slash-commands-from-chat (stale: touches `api/agent.py`, `spec.py`, migrations 0010/0012 that
  collide with main). hive-self-close (planned) edits `api/agent.py` and `k8s/on_start.py`, the
  same files as phase 3 here. agents-taskboard ("decisions answered once") is the natural channel
  for a later "agent asks a human to change a human-only field" flow; no code overlap now.
  knowledge-notes item 4 (would add a `spec.knowledge` preset switch) is deferred.

## 3. Design

### 3.1 Human-only fields (proposed)

Changeable only through the main API (`/api/v1`, the user's web UI). Every agent route refuses a
change to any of them with 403 `human_only_field` naming the fields, before any side effect.

| Field | Why human-only |
|---|---|
| `kube_access` | cluster-admin-equivalent ServiceAccount in every namespace |
| `session_messaging` | the superleader flag: grants the admin API, `secret_set` and messaging every leader; an agent must not mint superleaders or promote itself |
| `superleader_manageable` (column) | the operator's access switch that scopes the admin API; already main-port-only for `false`, admin create forces `true` (keep) |
| `leader_editable` (new column, 3.2) | the switch that allows leader self-edit; an agent must not open its own gate |
| `docker` | privileged sidecar, root-equivalent on the node (sizes stay agent-editable within the caps once a human turned docker on) |
| `discard_hook_url` | the reconciler sends the whole transcript there from inside the cluster: exfiltration and SSRF channel the agent pod itself does not have |
| `wrapper.permission_mode` | `auto` to `bypassPermissions` removes the permission classifier; the user already has a dedicated route for it |
| `wrapper.permissions` | the deny list is the remaining tool guard under bypass mode |

Not human-only, and why it is safe enough: `image` (bounded by the deploy-time allowlist, which no
API can change), `model`/`effort`/sizes/replicas (deploy-time lists and caps), plain and protected
env values (write-only, reserved names already refused), hooks, MCP servers, plugins, any-mcp
sources and config, init scripts, prompts (all run inside the agent pod, which the agent already
controls; the persistence risk is in 7), `usage_quota` (see Q8), labels, name, cache, timers.

Never editable by any API (unchanged): `is_default`, the allowlists and caps, reserved env and
MCP names, the `orchestrator` plugin name.

Enforcement: one declarative table `HUMAN_ONLY` (spec paths plus the two columns) and one pure
function `human_only_changes(stored, new)` (returns the changed field paths) in a new module
`agents_orchestrator/preset_policy.py`. Comparison is on normalised values (`None`, absent and
`false` are equal for the bool flags, so a sparse spec does not trip it). It runs on every agent
write: admin `POST` (stored = empty spec), `PUT`, `PATCH`, `copy` (Q10) and the leader route.
With Q2 option (b), a change "toward safe" is allowed: a grant turned off or removed,
`permission_mode` set to `auto`, deny rules added, allow rules removed.

### 3.2 Auth model

- **Superleader** (`session_messaging` session, existing `require_superleader` gate): edits any
  `superleader_manageable` preset through `/agent/v1/admin/presets/...`, human-only fields
  excluded. Unchanged visibility: other presets are 404.
- **Session leader**: edits only the source preset of its own session (`sessions.preset_id`)
  through a new `/agent/v1/preset` (GET, PATCH, `PUT /agent/v1/preset/secrets/{name}`), only when
  that preset has the new human-only column `presets.leader_editable` (default `false`, live like
  `superleader_manageable`). Leader = the current leader row of a hive or the only agent of an
  alone session (`_leads`); other agents 403 `not_leader`; a session without a preset (raw spec,
  or the preset was deleted) 404 `preset`; a preset with the switch off 403 `preset_not_editable`.
  Same human-only list.
- No new token: both use the per-session agent token plus pod IP binding (`require_agent`).
- Humans: the main API is unchanged and can change every field.

### 3.3 Write semantics

- New `PATCH /agent/v1/admin/presets/{ref}` and `PATCH /agent/v1/preset`, body
  `{name?, labels?, spec?}` where `spec` is a JSON merge patch (RFC 7396: objects merge, `null`
  deletes a key, arrays replace). It removes F2 (no read-modify-write of redacted entries) and
  lost updates on disjoint keys.
- Server steps, in one transaction: lock the row (`FOR UPDATE`), apply the patch to the stored
  spec, parse as `SessionSpecIn`, `split`, `human_only_changes` against the stored row, then the
  exact user-API path: `_validated(..., stored=...)` (same `check_spec`, same stored exemptions,
  same 422 texts) and `_save` (same Secret sync). The existing admin `PUT` and `POST` gain the same
  guard (closes F1).
- Optimistic concurrency (Q9): a new `presets.revision bigint` bumped by every spec, name,
  labels or column write (also the init-scripts and permission-mode write-backs); responses carry
  `ETag: "<revision>"`; `If-Match` is honoured on PATCH and PUT on both ports (412
  `revision_mismatch` with the current revision). The web sends it.
- Rollout: none. A preset edit changes only sessions created afterwards (trigger fires included);
  running sessions, generations and config hashes are untouched, as today. Q6 decides whether the
  leader route may also apply an edit to its own running session.

### 3.4 Secret handling

- An agent writes `SSH_PRIVATE_KEY_B64` without reading anything back: declare or keep the entry
  `{protected: true}` (PATCH), then `secret_set` (admin) or a new local `own_preset_secret_set`
  (leader) resolves the value in the plugin process from `from_file`/`from_env`/`from_command` and
  PUTs it once. Response: `{name, set, version, updated_at}` only.
- A protected entry carrying a `value` in any agent PATCH/PUT/POST body is refused server-side
  with 422 `secret_in_spec` (today only the plugin refuses it; the server accepts it), so the only
  agent path for a value is the secret route.
- Redaction: responses go through `redact_spec_dict` as today; log lines and audit rows carry
  field paths and secret names and versions, never values. A test asserts a canary value appears
  in no response, log record, event row or revision row.
- Removing or unprotecting a protected variable by an agent: Q7.
- Reaching running sessions after a rotation: Q5 (today only new sessions get the new version).
- Recommendation outside the code: `SSH_PRIVATE_KEY_B64` should be a protected variable; if it is
  plain today, the user flips it to protected once in the web UI (Q11).

### 3.5 Audit trail

- New table `preset_revisions` (migration 0028), single writer the api, written in the same
  transaction as the preset change: `id bigserial`, `preset_id uuid` (no FK, outlives the preset),
  `revision bigint`, `at timestamptz`, `actor_kind` (`user`, `superleader`, `leader`,
  `write_back`), `actor_session_id`, `actor_slug`, `actor_pod`, `route`, `changed text[]` (field
  paths), `spec jsonb` (the stored spec after the change, which by construction holds no secret
  value), `name`, `labels`, `superleader_manageable`, `leader_editable`, and `secrets jsonb`
  (`[{name, version}]` written by this change). Before/after = this row and the previous one.
  Backfill one revision-1 row per existing preset.
- Retention: Q12.
- Where the user sees it: `GET /api/v1/presets/{id}/revisions` and a "History" tab on the
  preset in agents-web (who, when, which fields, side-by-side redacted diff). Superleaders read
  `GET /agent/v1/admin/presets/{ref}/revisions`. The `admin_call` event row stays and gains
  `fields` (changed paths).
- User identity: the api sees none today, so main-port rows say `user`. Passing an oauth2-proxy
  user header is noted, not doing now.

### 3.6 Changes per component

agents-orchestrator:
- `preset_policy.py` (new): `HUMAN_ONLY`, `human_only_changes`, merge-patch apply.
- `api/presets.py`: `patch` service function; guard hook and `actor` parameter on
  `create`/`replace`/`copy`/`put_secret`; ETag/If-Match; revisions route.
- `api/admin.py`: `PATCH /presets/{ref}`, `GET /presets/{ref}/revisions`, guard on POST/PUT/copy,
  `ADMIN_VISIBILITY` rows, audit `fields`.
- `api/agent.py` (phase 3): `GET|PATCH /agent/v1/preset`, `PUT /agent/v1/preset/secrets/{name}`.
- `api/schemas.py`: `PresetPatch`, `PresetRevisionView`, `PresetView.revision`,
  `leader_editable`.
- `db/presets.py`: patch under lock, revision bump, revision insert, `leader_editable`;
  `db/sessions.py` write-backs bump the revision and insert a `write_back` row.
- `db/migrations/0028_preset_revisions.sql`; `k8s/on_start.py` tool lists; `openapi.json`;
  README Security (human-only list, R1 restated); MEMORY.

any-mcp-tatara-plugins:
- `admin.py` rows `preset_patch` (PATCH) and `preset_history` (GET revisions); `__init__.py`
  rows `own_preset_get`, `own_preset_patch`; `secrets_local.py`: `SPEC_TOOLS` gains the two patch
  tools, new local `own_preset_secret_set`; refreshed OpenAPI fixture; README.

agents-web:
- `PresetForm.tsx`: "Leader can edit this preset" switch, "Human only" helper text on the
  human-only switches, `If-Match` on save with a 412 reload prompt; new `PresetHistory.tsx`;
  API types (`revision`, `leader_editable`, revisions).

agents-helmfile: pin bumps after the releases.

### 3.7 Migrations and versions

- Migration `0028_preset_revisions.sql` (next free after 0027 on main and the 0025/0026 claims):
  `presets.revision`, `presets.leader_editable`, `preset_revisions` plus backfill. Additive and
  idempotent like 0023. Renumber at merge time if another branch takes 0028 first.
- Releases: orchestrator next free minor at release time (`v3.6.0` if nothing lands first;
  cache-retention-settings and hive-self-close may take 3.6/3.7), plugins `v0.12.0`, web
  `v0.16.0`. Order: orchestrator, then plugins (the fixture needs the released OpenAPI), then
  helmfile pins orchestrator plus `ORCH_ANY_MCP_PLUGINS_REF`, then web.

## 4. Small first step (unblocks (a) and (b) fast)

Step 0, zero code, today (Q11): in the web UI the user marks the webhook, schedule and chat
presets "Superleader can manage" and makes `SSH_PRIVATE_KEY_B64` a protected variable. Then a
superleader can already do (b) with `secret_set` and (a) with `preset_get`, stripping
`set/version/updated_at` from protected env entries, and `preset_replace`.

Step 1, one orchestrator PR plus one plugin PR, no migration, no web change:
1. `preset_policy.py` with the human-only table (Q1/Q2 answer) and the guard on admin `POST`,
   `PUT` and `copy` (closes F1).
2. `PATCH /agent/v1/admin/presets/{ref}` (merge patch, row-locked, same validation and save path
   as PUT, guard, 422 `secret_in_spec`).
3. `admin_call` audit data gains `fields` (changed paths); still no values.
4. Plugin row `preset_patch`, `SPEC_TOOLS` updated, fixture refreshed; on_start `ADMIN_TOOLS`
   gains `preset_patch`.

With step 1 a superleader sets `usage_quota: {five_hour_pct: 80, seven_day_pct: 80}` with one
`preset_patch` per preset and rotates the key with `secret_set`, and can no longer grant
human-only capabilities.

## 5. Test approach

TDD in each repo, through `mise run test`:
- Table-driven guard test: every human-only field times every agent write route (admin POST, PUT,
  PATCH, copy, leader PATCH) is 403 `human_only_field`, the row and its Secrets are unchanged;
  "toward safe" cases pass when Q2 (b) is chosen; normalisation cases (absent vs `false`).
- Parity test: a corpus of invalid specs gives the same 422 body through main PUT, admin PUT and
  admin PATCH.
- Merge-patch tests: nested merge, `null` deletes, arrays replace, protected entry kept without a
  value, protected value refused, `labels`/`name` patch, default preset rename refused.
- Concurrency: two PATCHes of disjoint keys both survive; stale `If-Match` is 412; write-backs
  bump the revision.
- Secret canary: a value set through the secret route never appears in any response, log record
  (`caplog`), `events` row or `preset_revisions` row.
- Leader route: leader ok, non-leader 403, no preset 404, switch off 403, other preset
  unreachable, superleader of another session cannot use it for a foreign preset.
- Migration test (0028 applies twice, backfill), OpenAPI snapshot, plugin contract test against
  the refreshed fixture, web vitest for the History tab, the switch and the 412 prompt.

## 6. Risks

1. F1 is live now: until step 1 merges, a superleader can grant `kube_access`,
   `session_messaging` or `docker` through a manageable preset.
2. Prompt-injection persistence: a trigger or chat session reads attacker-influenced text; a
   leader allowed to edit its own preset can persist instructions (system_append, start_prompt,
   hooks, init scripts) into every future session of that preset. Mitigation: `leader_editable`
   off by default, revision history with diffs, restore in the complete scope.
3. R1 stays: write-only secrets do not stop an editor from exfiltrating a secret through a hook
   header, MCP env, init script or child session. Documented, not solved.
4. The init-scripts write-back lets any agent (not only the leader) of any session edit its
   source preset without a switch; it becomes inconsistent with the new model (Q13).
5. Agents raising `usage_quota` defeat the hold the user sets (Q8).
6. Allowlist growth: new tool names in `on_start.py` change the rendered any-mcp config; check
   whether that rolls running pods (hive-self-close faces the same and lands first).
7. File overlap with hive-self-close (`api/agent.py`, `on_start.py`) and the migration-number
   race (0025/0026/0028); rebase and renumber at merge.
8. Rotation does not reach running sessions (snapshot); a revoked old key breaks long-lived chat
   sessions until they are recreated (Q5).

## 7. Scope from MVP to complete

1. Step 0 (user, web UI): manageable flags and protected `SSH_PRIVATE_KEY_B64`.
2. MVP = step 1 (section 4): human-only guard on all admin writes, admin PATCH, audit field
   names, plugin `preset_patch`.
3. Audit and concurrency: migration 0028 (`revision`, `preset_revisions`, backfill), ETag and
   If-Match on both ports, revisions routes, web History tab and 412 handling, write-backs
   recorded.
4. Leader self-edit: `leader_editable` column and web switch, `/agent/v1/preset` routes, plugin
   `own_preset_get`, `own_preset_patch`, `own_preset_secret_set`, allowlist update.
5. Complete: restore a revision (main API and web; agents only for agent-editable fields),
   opt-in secret refresh on restart (Q5 b), "toward safe" rules (Q2 b), a taskboard decision flow
   for an agent to request a human-only change, oauth2-proxy user identity in the audit.

## 8. Decisions (user, 2026-11-02)

The user accepted every Recommended option. Rejected options, one line each.

1. Human-only field list: (b) grants plus `discard_hook_url`, `wrapper.permission_mode`,
   `wrapper.permissions` and the new `leader_editable`. Rejected: (a) grants only (MVP);
   (c) (b) plus `image`, `any_mcp_sources`, `any_mcp_config`, hooks, MCP servers, plugins.
2. How strict is "human-only": (b) agents may only move toward safe: turn a grant off or remove
   it, set `permission_mode` to `auto`, add deny rules, remove allow rules. Rejected: (a) any
   change by an agent is refused (MVP).
3. Shape of the agent write API: (b) JSON merge-patch `PATCH` on the whole preset with the
   human-only guard, plus the guard on the existing POST/PUT/copy (MVP and Recommended).
   Rejected: (a) narrow routes for the two needs only; (c) keep full `PUT` only with the guard.
4. Leader self-edit gate (always leader only, own source preset only): (b) new human-only
   per-preset switch `leader_editable`, default off. Rejected: (a) no leader self-edit (MVP);
   (c) reuse `superleader_manageable`; (d) any leader, no switch.
5. Secret rotation and running sessions: (b) opt-in `refresh_secrets` on a session restart
   re-snapshots `secret_versions` from the preset and rolls the pods (complete scope). Rejected:
   (a) new sessions only (MVP); (c) every rotation re-snapshots and rolls all sessions.
6. Effect of a leader's edit on its own running session: (a) the preset only; it applies to
   sessions created afterwards (MVP and Recommended). Rejected: (b) also apply in place for
   fields not rendered into pods (`usage_quota`).
7. Protected variable declarations by agents: (b) agents may add protected variables and set
   values; removing or unprotecting one stays human-only (MVP and Recommended). Rejected:
   (a) agents only set values of existing protected variables; (c) agents may add, remove and
   unprotect.
8. `usage_quota` edits by agents: (b) superleader any value; a leader on its own preset may only
   lower it. Rejected: (a) any value 1-100 for both (MVP); (c) both may only lower it.
9. Optimistic concurrency: (b) `presets.revision`, `ETag`, `If-Match` honoured on PATCH and PUT
   on both ports, sent by the web and the plugin. Rejected: (a) none (MVP); (c) as (b) with
   `If-Match` required on agent writes.
10. Agent create and copy of presets with grants: (b) an agent copy clears the grant flags
    (`kube_access`, `session_messaging`, `docker`, `discard_hook_url`) and keeps the
    restrictions. Rejected: (a) copy keeps every field, create guarded like an edit of an empty
    preset (MVP).
11. Step 0 now, in the web UI (mark the webhook, schedule and chat presets "Superleader can
    manage" and make `SSH_PRIVATE_KEY_B64` protected on every preset that has it): (a) yes,
    before step 1 ships (MVP and Recommended). Rejected: (b) wait for step 1.
12. Audit storage and retention: (b) `preset_revisions` table for every writer (user, agents,
    write-backs), redacted snapshots, web History tab, keep the last 200 revisions per preset.
    Rejected: (a) only the `admin_call` event gains changed field names, no migration (MVP);
    (c) as (b), kept forever, plus restore.
13. The existing init-scripts write-back (any agent, no switch): (a) leave it as is; record it
    in the risks (MVP and Recommended). Rejected: (b) align it with the new model.
