# secrets-vault: central secrets vault, attached to presets by reference

Status: spec, open (the one human gate: section 12). Docs only; nothing implemented.
Taskboard: epic T-72. Related: T-19 projects (S1-S7 answered), T-18 preset change proposals
(shipped), T-55 kube access split, T-57 preset copy leaves protected vars unset, T-67 a bad manual
copy of a GPG key on one preset broke research runs.

Source, user request verbatim: "Create central secrets vault - idea here is: I will put all
secrets I own into central place with their descriptions (e.g. HARBOR_USERNAME, HARBOR_PASSWORD
with "Harbor credentials for building containers"). Any superleader session will be able to
attach these secrets (or update existing secrets) to presets based on the description and key
names without looking into the secrets contents."

Leader's scope: the user stores each secret once with a name and a description; any superleader
lists the vault (names and descriptions only) and attaches an entry to a preset env var by
reference, or updates an existing attachment; no agent ever sees a value; rotating an entry
updates every attached preset. Tools: `vault_list`, `vault_attach`, `vault_detach` (MCP,
superleaders); user-only put and rotate in the web UI. Default rule: agents cannot attach to
privileged presets; that stays human-only.

Research date: 2026-11-08, against `origin/main` of agents-orchestrator `5277d17` (v6.2.0-3),
agents-web `f0424d5`, any-mcp-tatara-plugins (v0.23.0). The superrepo pins are stale
(orchestrator pin is v3.9.0, plugins pin v0.5.1); line numbers below are at origin/main.
Paths are relative to each repo. Notes: `.scratchpad/secrets-vault/research-orchestrator.md`,
`.scratchpad/secrets-vault/research-web.md`. No secret value, env file or kube Secret was read.

## 1. What and why

Today every secret an agent needs is a protected env var stored per preset:

- a value is entered per preset and per var, so the same credential (Harbor, a GPG key, a git
  token) lives in N independent copies;
- copying a preset leaves every protected var unset (T-57), so a copied preset fails at session
  create with `secret_unset` until someone re-enters each value;
- re-entering a value by hand is error prone: a bad manual copy of a GPG key on one preset broke
  research runs (T-67);
- a superleader that wants to wire a credential into a preset has only `secret_set`, which reads
  the value inside its own pod (`from_file`, `from_env`, `from_command`), so the value must
  already be reachable from the superleader pod; that is the copy path that produced T-67;
- rotating a credential means finding and updating every preset that holds a copy.

The vault turns the value into one object with a name, a description and versions. Presets (and,
with T-19, projects) hold references to vault entries, never values. The user is the only writer
of values. Superleaders choose which entry goes where from the name and the description alone.
Rotation writes one new version; every attached preset uses it for the next session it starts.

Out of scope: a general-purpose secret manager (no external KMS, no Vault/OpenBao, no per-user
ACLs), reading a value back through any API, and changing how webhook endpoint credentials are
stored (`webhook-<id>-password`, k8s/secrets.py:704-749).

## 2. Research findings

### 2.1 How protected preset env vars work today (agents-orchestrator)

- Spec model: `spec.env` maps `NAME` to `{value, protected, expand}` (migration
  `0019_env_entries.sql`; `spec.py:314`). A protected entry never carries a value in the stored
  spec; values are split out of the request (`api/presets.py:69`, `_save` :113-156) or written
  through the secret route.
- Store: `src/agents_orchestrator/k8s/secrets.py` (module doc :1-16). One k8s Secret per preset,
  var and version, name `ps-<preset id[:8]>-<sha256(name)[:6]>-v<version>`, single key `value`
  (:38, :70-72), `immutable: true`, type Opaque, label `MANAGED_BY` (:103-121). Write is
  delete-leftover-then-apply, no get (:103-121).
- Versioning: next version = max over `preset_secrets` and `change_proposal_secrets` plus one,
  under `pg_advisory_xact_lock(hashtextextended('<preset_id>/<name>'))` (:84-100); the preset row
  is locked FOR UPDATE first and a `recheck` callback re-validates the locked spec
  (`set_secret` :179-227).
- GC: `gc()` (:275-337) deletes every version that is neither current nor referenced by
  `sessions.secret_versions` nor reserved in `change_proposal_secrets`; the `swept` column bounds
  work; `sync_declared` (:230-257) retires undeclared names; `forget_unsaved` (:672-701) and
  `reap_unreserved` (:607-669) clean rolled-back writes. Driven by `api/proposal_sweep.py`.
- Single k8s writer: only the api process, through `api/secret_store.py` (:1-6, lazy
  LightkubeApi :76-83). RBAC: chart `templates/role-api.yaml:12-15` and `templates/role.yaml:18-20`
  grant `secrets` verbs `create`, `patch`, `delete` only, no `get`/`list`/`watch`. The
  orchestrator cannot read a value back; pods consume values through `secretKeyRef`.
- Pinning: session create calls `snapshot_versions(conn, preset.id, spec.protected_env)`
  (secrets.py:124-150) inside the session insert transaction (`api/sessions.py:490-498`); a
  missing value raises `SecretUnset` (error `secret_unset`). The pins are stored in
  `sessions.secret_versions` jsonb `{ENV: <secret name>}` (0018:16-18, `db/sessions.py:68`,
  :139-158). Rotation never changes a running session (`secret_view.py:29-37`).
- Pod render: one `env[].valueFrom.secretKeyRef {name: <pinned>, key: value}` per var, not
  `envFrom` (`k8s/render.py:512-533`); a missing pin raises ValueError (:527-528).
- Read side: `secret_view.redact_spec` rebuilds protected entries as
  `{protected, expand, set, version, updated_at}` (`secret_view.py:48-77`); used by preset views
  (`api/presets.py:32-45`), session views (`api/sessions.py:138`) and export
  (`db/export.py:77`).

### 2.2 Tables

- `preset_secrets(preset_id, name, version, swept, retired_at, updated_at, PK(preset_id, name))`,
  no FK to presets, current version only, no hash of the value (`0018_preset_secrets.sql`).
- `change_proposal_secrets(preset_id, name, version, proposal_id, revision, state staged|bound)`
  and `change_proposal_items.secret set|changed` (`0038_change_proposals.sql:51,60-72`).
- `presets.superleader_manageable bool default false` (0023).
- Migrations: own forward-only runner `db/migrate.py`, files `NNNN_*.sql`. Next free number on
  main is 0039; 0037 is taken by `origin/projects-s1` (projects table, unmerged).

### 2.3 Who can set values today

- Human, main port: `PUT /api/v1/presets/{preset}/secrets/{name}` body `SecretIn{value}`
  (`api/presets.py:539-549`, `schemas.py:90-104`), max 1 MiB (413 `secret_too_large`,
  presets.py:23,96-99), name must be a declared protected var (422, :504-509), store failure 502
  `secret_store_failed` (:102-103).
- Superleader, agent port: `PUT /agent/v1/admin/presets/{ref}/secrets/{name}`
  (`api/admin.py:273-282`), same `put_secret(..., superleader=True)`; the preset must be
  `superleader_manageable` else 404 (admin.py:205-210); a privileged target is 403
  `privileged_target` (`guard_agent_edit(..., privileged=True)`, presets.py:501-516).
- MCP `secret_set` is a local handler tool in any-mcp-tatara-plugins
  `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/secrets_local.py:297-333`: the
  plugin process in the agent pod resolves `from_file|from_env|from_command` and PUTs the value.
  The model does not see the value; the pod does.
- Privileged preset = any of `kube_cluster_access`, `kube_namespace_access`, `session_messaging`,
  `docker` (`preset_policy.py:42-48`, `privileged()` :142). Human-only fields may only move toward
  safe for agents (:1-25, :146); an agent may not remove or unprotect a stored protected var
  (:15-16); on privileged targets only NON_SECURITY paths change (:55-83, :179-199).
- Superleader = a session whose spec has `session_messaging` (admin.py:53-61). Superleader copy
  strips grants (`strip_grants`, presets.py:448-451). `superleader_manageable` is set only on the
  main port (presets.py:178-181).
- Auth: agent port needs `X-Orch-Session`, the per-session bearer and the peer IP of a live agent
  pod (`api/agent.py:1-5`, `allowlist.py` PortGate). Main port has no in-app user identity;
  humans arrive through oauth2-proxy and no SSO header is read
  (agents-helmfile `values/agents-orchestrator/common.yaml:95-98,119-130`,
  `ORCH_ALLOWED_CIDRS: 127.0.0.1/32`). User-only means main-port-only.

### 2.4 Copy (T-57) and the GPG incident (T-67)

- `POST /api/v1/presets/{id}/copy` (presets.py:435-470, admin twin admin.py:262-270) calls
  `repo.create` with the source spec only: protected entries stay declared but unset, so a session
  from the copy fails with `secret_unset`. The web shows "Protected value not copied"
  (agents-web `src/presets/PresetForm.tsx:294`).
- Neither T-57 nor T-67 is referenced in code or commit logs; the facts above are taken from the
  epic context. The vault removes the copy step that produced both.

### 2.5 Audit and events

- `events` table (`0001_init.sql:74`, `db/events.py`, NOTIFY `events`). Every agent admin call
  writes an `admin_call` event with method, path, status, session slug, `secrets` (names only)
  and `fields` (`api/admin.py:92-128`, `AdminRoute` :131-155).
- Human secret writes on the main port are only log lines (`secret set: preset=.. name=..
  version=..`, secrets.py:224); no event row.
- T-18 proposals stage secret values as `orchestrator.proposal=<id>` labelled Secret versions and
  promote them on approval (secrets.py:340-484, `api/proposals.py:1-20`).

### 2.6 MCP surface (any-mcp-tatara-plugins)

- Admin tools are declarative `AdminRow(name, method, path, description, schema, body, query)`
  rows (`admin.py:59-67`, `ADMIN_TOOLS`), built into HTTP bindings in `__init__.py` `load_tools`
  (:391-430); value-carrying tools are local handlers (`secrets_local.py`).
- The orchestrator renders the plugin entry and allowlist: `k8s/on_start.py:19-20` (plugin
  `orchestrator`, subdir `orchestration/orchestrator`), `ADMIN_TOOLS` :49-64 (superleaders only,
  :67-87). Plugin ref default `settings.py:237`.
- Adding a tool = orchestrator route plus `ADMIN_VISIBILITY` row (admin.py:177-199) and
  openapi regen; plugin `AdminRow`, `tests/test_admin_tools.py` EXPECTED (:82),
  `tests/fixtures/orchestrator_openapi.json`; name in `on_start.ADMIN_TOOLS`; plugin release and
  ref bump.

### 2.7 agents-web

- Preset env editing: `src/sessions/sessionSpecForm.ts:13-41` (`EnvRow`, `sendsValue`,
  `envRowFromStored`, which ignores `version`), `:560-563` (`envEntry`);
  `src/presets/PresetForm.tsx:229-248` (save: `setPresetSecret` before the spec PUT),
  `:294-318` (stored protected row: "set, updated <ts>" / "unset", Replace value), `:86-102`
  (paste .env). API wrapper `src/api/client.ts:113-115`.
- Settings pages are menu entries: `src/backends/registry.ts:1-17` (slot doc), `:32-47`
  (`MenuEntry`, orchestrator entries Sessions 10, Presets 40, Proposals 42, Backups 45); feature
  `menu.ts` pattern (`src/proposals/menu.ts`). Free slots: 41, 43, 44.
- Patterns to reuse: `src/backups/BackupsPage.tsx` (table, ConfirmDialog, FormError, formatAge),
  `src/webhooks/EndpointsList.tsx` (rotate behind confirm), `src/layout/ConfirmDialog.tsx`,
  `src/triggers/usePoll.ts`.
- Typed client from `openapi/orchestrator.json` (`npm run sync:api -- orchestrator`, CI
  `check:api`). Tests: vitest + Testing Library, page pattern `src/backups/BackupsPage.test.tsx`.
- Proposals review already renders secret items without values (`src/proposals/ItemCard.tsx:19-24,
  49-52`).

### 2.8 T-19 projects (answered decisions this design must fit)

S1 a session gets the secrets of its preset's project at create. S2 a preset env var wins over a
project secret of the same name. S3 the user, plus superleaders by reference and through
proposals, control which secrets a pod gets. S4 every preset of a project receives its project
secrets. S5 rotation is pinned at session create; the web lists sessions on old versions. S6
existing per-preset secrets stay as a second layer, no migration. S7 ship with a logical
boundary; cluster-access sessions can read Secrets until T-55.

S3 ("by reference") and S5 (pinning) are exactly the vault model; the vault is the value source
that project secrets reference. The on-disk projects plan (`docs/plans/projects/plan.md:414`)
predates S1-S7 and still says credentials stay per preset; it is superseded on that point.

## 3. Design

### 3.1 Where it lives

In agents-orchestrator (Q1). It already owns the only k8s Secret writer, the RBAC, the pinning
transaction and the GC; pinning a vault version must happen in the same transaction as the
session insert. A separate service would need Secret RBAC of its own, a cross-service pin
protocol and a second GC. The vault tables have exactly one writer (the orchestrator api
process), as the hard rules require.

### 3.2 Data model

New migration `0039_vault.sql` (renumbered if projects lands first):

```sql
CREATE TABLE vault_entries (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,                 -- ^[A-Z_][A-Z0-9_]{0,127}$, unique among live entries
  description text NOT NULL,          -- 1..500 chars, required
  agent_attachable boolean NOT NULL DEFAULT true,   -- Q3
  current_version int NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  deleted_at timestamptz
);
CREATE UNIQUE INDEX vault_entries_live_name ON vault_entries (name) WHERE deleted_at IS NULL;

CREATE TABLE vault_versions (
  entry_id uuid NOT NULL REFERENCES vault_entries(id),
  version int NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  retired_at timestamptz,             -- set when superseded
  swept boolean NOT NULL DEFAULT false,
  PRIMARY KEY (entry_id, version)
);
```

- Name rules: env-var shaped, immutable after create (a rename is a new entry plus re-attach).
  Names and descriptions are not secret: agents and logs may see them.
- No value, hash or length of a value is stored anywhere in Postgres.
- k8s Secret per version: `vault-<entry uuid>-v<version>`, key `value`, `immutable: true`, type
  Opaque, labels `MANAGED_BY` plus `orchestrator.vault=<entry uuid>`. Same write pattern as
  `k8s/secrets.py:103-121` (delete leftover, then apply). 1 MiB cap as today. Values are stored
  byte for byte: no trimming, no newline normalisation (T-67).
- Versioning: `pg_advisory_xact_lock(hashtextextended('vault/<entry uuid>'))`, entry row
  FOR UPDATE, next = max(version)+1, write the Secret, insert the row, bump `current_version`,
  retire the old one; on rollback the existing `forget_unsaved`/`reap_unreserved` pattern removes
  the orphan Secret.

### 3.3 Attachment: a reference inside the spec (Q2)

An env entry gains a third shape: `{"vault": "HARBOR_PASSWORD"}` (mutually exclusive with
`value` and `protected`; `expand` is always false for vault refs). The env var name and the entry
name may differ (`GPG_PRIVATE_KEY: {vault: RESEARCH_GPG_KEY}`); the attach tool defaults the env
name to the entry name.

Consequences:

- Copy (T-57): the copy carries the references, so a copied preset starts sessions with the same
  values. Superleader copy (`strip_grants`) also drops refs to entries the agent could not attach
  itself (`agent_attachable=false`) and lists them in the response as `dropped_vault_refs`.
- Proposals (T-18): attaching or changing a ref is an ordinary spec path change (`env.NAME`); no
  value is staged, so `change_proposal_secrets` is not involved.
- Export/import (`db/export.py:77`): refs export as-is; import fails 422 `vault_entry_unknown` if
  the target has no such entry.
- Validation on every preset save (main and agent port): the entry must exist and be live, else
  422 `vault_entry_unknown`.
- Session-level spec overrides (session create body, session spec patch) may not add or change a
  vault ref (422 `vault_ref_not_allowed`); vault refs come only from the preset (and, later, the
  project). Otherwise an agent could mint a session with any entry and no preset guard.
- `spec.protected_env` stays as is; a new `spec.vault_env` returns `{ENV: entry name}`.
- Precedence inside one preset is trivial (one entry per env name). Across layers, S2 applies:
  preset env (plain, protected or vault ref) wins over a project secret of the same name.

### 3.4 Pinning at session create and rendering

- In the session insert transaction (`api/sessions.py:490-498`), after `snapshot_versions` for
  inline protected vars, a new `vault.snapshot(conn, spec.vault_env)` takes
  `SELECT id, current_version FROM vault_entries WHERE name = ANY(..) AND deleted_at IS NULL
  FOR SHARE` (blocks a concurrent rotate or delete for the length of the insert) and returns
  `{ENV: "vault-<uuid>-v<n>"}`. Both maps merge into `sessions.secret_versions`; no schema change.
  A missing entry raises the existing `SecretUnset` path with error `vault_entry_unknown`.
- Render (`k8s/render.py:512-533`) iterates the union of `protected_env` and `vault_env` and
  emits the same `secretKeyRef {name: <pinned>, key: value}`. The only change is the key set it
  iterates; the missing-pin ValueError stays.
- Project secrets (T-19 S1, S4) later add a third input to the same snapshot: project refs, with
  preset names masking them (S2).

### 3.5 GC and immutability

- A vault version is deletable when it is not the entry's current version and no session that
  still has a pod (the same liveness rule `gc()` uses at secrets.py:275-337) pins its Secret name
  in `secret_versions`. `vault.gc()` runs in the existing sweeper (`api/proposal_sweep.py`),
  marks `swept`, and drops fully swept rows of deleted entries.
- A deleted entry (Q8 A: only when unattached) gets `deleted_at`; its current version is deleted
  once no live session pins it.
- `sync_declared` (secrets.py:230-257) retires the inline `preset_secrets` row when an env var
  switches from inline protected to a vault ref, so the old per-preset Secret is collected as
  today.

### 3.6 Main-port routes (human, user-only)

| Method and path | Body | Result |
|---|---|---|
| `GET /api/v1/vault` | - | `[VaultEntryView]`: name, description, agent_attachable, version, updated_at, attachment count, sessions on older versions count |
| `POST /api/v1/vault` | `{name, description, value: SecretStr, agent_attachable?}` | 201 view; 409 `vault_name_taken`; 413 `secret_too_large`; 502 `secret_store_failed` |
| `GET /api/v1/vault/{name}` | - | describe: view plus versions, attachments `[{preset id, preset name, env}]`, live sessions per version |
| `PATCH /api/v1/vault/{name}` | `{description?, agent_attachable?}` | 200 view |
| `PUT /api/v1/vault/{name}/value` | `{value: SecretStr}` | rotate: 200 view with the new version |
| `DELETE /api/v1/vault/{name}` | - | 204; 409 `vault_entry_attached` with the attachment list (Q8) |
| `GET /api/v1/vault/{name}/events` | - | the entry's vault events, newest first (Q9) |
| `GET /api/v1/vault/candidates` | - | stage 2 (Q7): inline protected vars grouped by env name across presets, `[{env, presets: [{id, name, version, updated_at}]}]` |
| `POST /api/v1/vault/{name}/adopt` | `{targets: [{preset, env}]}` | stage 2 (Q7): turns each listed inline var into a ref to the entry in one transaction |

Attaching on the main port is a normal preset spec save from the preset form; no extra route.
No route anywhere returns a value. Main-port vault routes are absent from the agent and service
ports (they are not in `ADMIN_VISIBILITY` and not on the service-port route list).

### 3.7 Agent-port routes and MCP tools (superleaders)

| Tool | Route | Body / query |
|---|---|---|
| `vault_list` | `GET /agent/v1/admin/vault` | `?q=` substring over name and description; returns name, description, agent_attachable, version, updated_at, attachments `[{preset, env}]` |
| `vault_attach` | `PUT /agent/v1/admin/presets/{ref}/vault/{env}` | `{entry, replace: false}`; env defaults to the entry name in the tool, the route takes it explicitly |
| `vault_detach` | `DELETE /agent/v1/admin/presets/{ref}/vault/{env}` | removes the env var if it is a vault ref; 409 `not_vault_ref` otherwise |

Rules on attach and detach, in this order:

1. Caller is a superleader (admin.py:53-61), else 403 as for every admin route.
2. Preset not `superleader_manageable`: 404 (admin.py:205-210).
3. Preset privileged (preset_policy.py:142): 403 `privileged_target`; with Q4 B the body adds
   `proposable: true` and the superleader files a T-18 proposal whose item is `env.<ENV>`.
4. Entry unknown: 422 `vault_entry_unknown`; entry `agent_attachable=false`: 403
   `vault_entry_human_only` (Q3). Detach of a ref to a human-only entry is allowed.
5. The env var exists and is not a ref to the same entry: 409 `env_exists` unless
   `replace: true`. Replacing an inline protected var with a vault ref is allowed for agents
   (the value stays protected, so it is not an "unprotect", preset_policy.py:15-16); replacing a
   plain var too. Re-pointing an existing ref to another entry is the "update an attachment" case.
6. Write through the same locked preset save as `set_secret` (row FOR UPDATE plus `recheck`).

The generic agent preset edit (`PUT /agent/v1/admin/presets/{ref}`) applies rules 3 to 5 to any
vault ref it adds or changes, so the tools are not a bypass and not the only way.

MCP: three `AdminRow` rows in any-mcp-tatara-plugins `admin.py` (plain HTTP bindings, no value
crosses them, so no local handler); names added to `on_start.ADMIN_TOOLS` (:49-64) so only
superleaders get them. Tool descriptions say: choose by name and description; never copy a
value with `secret_set`.

### 3.8 `secret_set` (Q6)

Recommended: keep it for values an agent produced itself (a generated deploy key), and add one
guard: `PUT .../secrets/{name}` on a var that is a vault ref returns 409 `vault_attached`
(detach first). The tool description steers copies of existing credentials to `vault_attach`.
This closes the T-67 path (overwriting a shared credential with a hand copy) without removing a
working capability.

### 3.9 Permissions summary

| Action | User (web, main port) | Superleader (agent port) | Other sessions |
|---|---|---|---|
| list names and descriptions | yes | yes (`vault_list`) | no |
| read a value | no (write-only) | no | only the pods it is attached to, as env |
| create, rotate, delete entry | yes | no | no |
| edit description, `agent_attachable` | yes | no (Q5) | no |
| attach / re-point / detach on a manageable non-privileged preset | yes | yes, if `agent_attachable` | no |
| attach on a privileged preset | yes | no; proposal with Q4 B | no |
| set `superleader_manageable` | yes | no (unchanged) | no |

### 3.10 Rotation and propagation (S5)

Rotate writes version n+1 and makes it current. Running sessions keep their pinned version
(their pod env cannot change without a restart, and S5 pins at create). Every session created
after the rotate, on any attached preset, gets n+1: that is "rotating updates every attached
preset". The Vault page shows per entry how many live sessions run an older version, with links
to them; the user ends or restarts them as they see fit. The old version's Secret is deleted by
GC once its last pinning session is gone.

### 3.11 Audit and events (Q9)

- New event kinds in `events` (names and versions only, never values): `vault_created`,
  `vault_rotated`, `vault_updated` (description or flag; old and new description stored, they are
  not secret), `vault_deleted`, `vault_attached`, `vault_detached` (preset id, env, entry, old
  entry on re-point). Actor: `user` for the main port (no identity is read today, 2.3), the
  session slug for the agent port.
- Agent calls keep writing their `admin_call` row (admin.py:92-128) as well.
- Human writes of inline protected vars also get an event (`secret_set`, names only), closing
  the "logs only" gap of 2.5.
- Web: an Events tab on the vault entry dialog (`GET /api/v1/vault/{name}/events`).
- A canary test asserts a known test value never appears in responses, events, logs or the
  rendered pod spec (only the Secret name does).

### 3.12 Migration of existing per-preset secrets (Q7)

The orchestrator cannot read existing values (no `get` RBAC, 2.1), so neither import nor dedup is
possible without granting read access. Options weighed:

- Keep both layers (S6): inline protected vars keep working unchanged; the user creates vault
  entries as needed. Zero risk, no automation.
- Assisted adopt (stage 2): `GET /api/v1/vault/candidates` groups inline protected vars by env
  name across presets (names only); the user enters the value once into a new entry and ticks the
  presets to convert; `adopt` rewrites each ticked var to a ref in one transaction. The user
  decides equality, so no value is ever read. This is the T-67 fix for the GPG key.
- One-off import Job with a ServiceAccount that may `get` the `ps-*` Secrets: creates one entry
  per preset var (names like `<PRESET>_<ENV>`), could dedup by hashing inside the Job. Needs a
  temporary read grant in the agents namespace and still needs a human to write descriptions.

### 3.13 Web UI (agents-web)

- Vault page (`src/vault/`, menu slot 43 "Vault", orchestrator backend): table of name,
  description, version, updated, attachments, "sessions on older versions"; Create dialog (name,
  description, value as a multiline password field plus "load from file" so keys are not
  pasted by hand, agent attachable switch); Rotate behind ConfirmDialog (pattern
  `EndpointsList.tsx`); Edit description; Delete (409 shows the attachment list); entry detail
  with attachments, versions, live sessions per version and the Events tab.
- Preset form env rows (`PresetForm.tsx:294-318`, `sessionSpecForm.ts:13-41,560-563`): a row
  mode "From vault" with an Autocomplete over `GET /vault` showing name and description; a stored
  ref shows "vault: HARBOR_PASSWORD v3" with a link to the entry; protected inline rows keep
  their current UI and gain "Use vault entry". `envEntry` sends `{vault}` for such rows; `EnvRow`
  gains `vault?: string`.
- Copy dialog: helper text changes to "Protected values not copied; vault references are".
- Proposal review (`ItemCard.tsx`): an `env.X` item whose after-value is a vault ref renders as
  "vault: NAME (description)".
- Session view: pinned versions per vault var, flagged when behind current.
- Stage 2: "Adopt into vault" flow on the Vault page over `/vault/candidates`.

### 3.14 Projects (T-19) reconciliation

The vault is the single value store. Per-preset inline protected vars are the second layer (S6)
and stay. Project secrets, when the projects epic implements S1-S4, are a table
`project_env(project, env, entry_id)` of vault refs (no values of their own), snapshotted by the
same `vault.snapshot` at create (S1, S4), masked by preset env names (S2), changed by the user
and by superleaders through the same attach rules and proposals (S3), pinned (S5). This epic
ships the vault and preset refs; project refs ship with the projects stage that adds S1 (Q10).

## 4. Files and components touched

agents-orchestrator:

- `migrations/0039_vault.sql` (new).
- `src/agents_orchestrator/spec.py`: env entry `vault` shape, validation, `vault_env`.
- `src/agents_orchestrator/k8s/vault.py` (new, beside `k8s/secrets.py`): Secret naming, write,
  snapshot, gc; reuse helpers from `k8s/secrets.py` rather than copy them.
- `src/agents_orchestrator/db/vault.py` (new): entries, versions, events queries.
- `src/agents_orchestrator/api/vault.py` (new): main-port routes; `api/secret_store.py`: vault
  ops (stays the single k8s-importing api module).
- `api/admin.py`: three agent routes, `ADMIN_VISIBILITY` rows, `secrets` 409 guard.
- `api/presets.py`: save validation, copy keeps refs and drops human-only ones for superleaders.
- `preset_policy.py`: a vault ref add or change is a security change on privileged presets;
  attachability check.
- `api/sessions.py:490-498`: vault snapshot; session-level spec refuses vault refs.
- `k8s/render.py:512-533`: iterate the union.
- `secret_view.py`: redact shows `{vault, version, updated_at}`.
- `api/proposal_sweep.py`: call `vault.gc()`.
- `api/proposals.py` (Q4 B): vault ref items accepted.
- `db/export.py`, `schemas.py`, `openapi.json`, `k8s/on_start.py` (ADMIN_TOOLS), `settings.py:237`
  plugin ref.
- Tests under `tests/`; `MEMORY.md` entry.

any-mcp-tatara-plugins: `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/admin.py`
(three rows), `secrets_local.py` (description, 409 message), `tests/test_admin_tools.py`,
`tests/fixtures/orchestrator_openapi.json`; release tag.

agents-web: `src/vault/{menu.ts, VaultPage.tsx, VaultEntryDialog.tsx, api.ts, *.test.tsx}`,
`src/backends/registry.ts` (slot 43 and its doc), `src/presets/PresetForm.tsx`,
`src/sessions/sessionSpecForm.ts`, `src/proposals/ItemCard.tsx`, session detail view,
`openapi/orchestrator.json` and generated schema via `sync:api`, `MEMORY.md`.

agents-helmfile: orchestrator, web and plugins pins only. No RBAC change: create, patch and
delete on Secrets already cover the vault.

## 5. Test approach

- Orchestrator (pytest, fake lightkube as existing secret tests):
  - entry create, rotate, describe, patch, delete (409 while attached), name rules, 1 MiB cap;
  - concurrent rotates serialise (advisory lock), rollback leaves no orphan Secret;
  - session create pins the current version; rotate after create leaves the session pin;
    concurrent rotate and create cannot pin a deleted version;
  - render emits `secretKeyRef` for vault vars with the pinned name;
  - GC keeps a version pinned by a live session and deletes it after the session ends;
  - agent attach matrix: not superleader, not manageable (404), privileged (403, `proposable`
    with Q4 B), unknown entry (422), human-only entry (403), existing env without and with
    `replace`, re-point, detach of a non-ref (409); the same rules through the generic preset PUT;
  - session create body with a vault ref is 422;
  - copy keeps refs; superleader copy drops human-only refs and reports them;
  - `secret_set` on a vault ref is 409;
  - events written for every human and agent write, with names only;
  - canary: a fixed test value never appears in any response, event, log record or rendered pod
    spec.
- Plugins: EXPECTED rows, openapi fixture refresh, allowlist membership in the orchestrator
  `on_start` tests.
- Web (vitest + Testing Library): Vault page list, create, rotate confirm, delete 409; preset form
  vault picker round trip (`envEntry` sends `{vault}`); stored ref display; ItemCard rendering;
  registry order test.
- Live check after the helmfile bump: create a test entry with a throwaway value, attach it to a
  test preset through `vault_attach` from a superleader, start a session, and compare
  `sha256sum` of the env var inside the pod with the hash of the throwaway value (no value
  printed); rotate and confirm the next session gets the new hash and the old session keeps the
  old one.

## 6. Risks

1. A pod an entry is attached to can read the value (it is in its env), and its transcript could
   carry it. "No agent sees a value" holds for the attaching superleader, not for the consumer.
   This is the same as inline protected vars today. Mitigation: `agent_attachable=false` for
   high-value entries (Q3); privileged presets human-only.
2. A superleader can attach an attachable entry to a manageable preset and then start a session
   of it, which is a path for an agent to obtain any attachable value. Accepted by the request
   (superleaders choose wiring); bounded by `agent_attachable` and `superleader_manageable`, and
   every step is an event.
3. Sessions with kube cluster or namespace edit/exec access can read every Secret in the agents
   namespace, vault versions included (S7, until T-55). Labels make the vault Secrets easy to
   find. Not fixed here.
4. Name collisions: entry names are unique among live entries; env names are unique per preset;
   project vs preset collisions resolve by S2. A re-created entry with a deleted entry's name is a
   different uuid, so old pins never resolve to it.
5. Deleting an attached entry would break every attached preset at the next session create; Q8 A
   refuses it.
6. Rotation to a wrong value breaks every attached preset at once (the flip side of one source).
   Mitigation: the previous version stays until GC; stage 3 adds "roll back to previous version"
   only if it is asked for (noted, not doing now).
7. Pinning takes a FOR SHARE lock per vault entry in the session insert; a long rotate (k8s write)
   could delay session creates. The Secret is written before the lock-holding transaction
   bumps `current_version`, keeping the lock window short.
8. Two layers (inline and vault) coexist indefinitely under S6; the web must show which one a var
   uses or users will rotate the wrong one. Covered by 3.13.

## 7. Scope from MVP to complete, staged, with agent wall-clock estimates

Stage 1, MVP (about 5 to 6 h agent wall-clock including reviews):

- orchestrator: tables, Secret store, main-port routes, spec refs and validation, pinning, render,
  GC, agent routes with the rules of 3.7, events, copy behaviour, canary test (about 3 h);
- plugins: three rows, allowlist, release (about 45 min);
- web: Vault page (list, create, rotate, edit, delete), preset form picker and display, copy
  helper text (about 1.5 h);
- helmfile pins and the live check (about 45 min).

Stage 2 (about 2.5 h):

- assisted adopt (`candidates`, `adopt`, web flow) (Q7);
- privileged attach through T-18 proposals (Q4 B), ItemCard rendering;
- `secret_set` 409 guard and description (Q6 B);
- sessions on older versions per entry, session view flags, Events tab (Q9).

Stage 3, complete (with the projects epic, about 1.5 h on top of it):

- project refs (`project_env`) through the same snapshot and attach rules (Q10), web project
  secrets panel;
- final review against this spec and `docs/plans/secrets-vault/retro.md`.

Noted, not doing now: user identity on the main port (actor stays `user`), value rollback, an
external KMS backend, fixing the stale `_FLAGS = ("kube_access", ...)` in the plugins
`admin.py`.

## 8. Questions

Each question marks one option Recommended and one MVP; they may coincide. Replying "yes"
accepts every Recommended option.

- Q1. Where does the vault live?
  - A (Recommended, MVP): In agents-orchestrator beside preset secrets. Reuses the Secret writer,
    RBAC, pinning transaction and GC.
  - B: A new agents-vault service with its own Postgres and Secret RBAC. Cleaner ownership but
    needs a cross-service pin protocol and a second GC.
- Q2. How does a preset reference a vault entry?
  - A (Recommended, MVP): A `{vault: NAME}` env entry inside the preset spec. Copy, export and
    T-18 proposals carry the reference with no extra code.
  - B: A side table of attachments outside the spec. Spec stays unchanged but copy, export and
    proposals each need new handling.
- Q3. Which entries may superleaders attach?
  - A (MVP): Every entry, to any manageable non-privileged preset. Simplest; every value is
    reachable by superleaders.
  - B (Recommended): Every entry by default; the user can mark an entry human-only. Lets the user
    fence off crown-jewel credentials.
  - C: Only entries the user explicitly marks agent-attachable. Safest default but every new
    entry needs an extra click.
- Q4. How does an attach to a privileged preset happen?
  - A (MVP): Only the user attaches it in the web preset form; agents get 403. Matches today's
    privileged rule exactly.
  - B (Recommended): Agents get 403 with `proposable: true` and file a T-18 proposal. The human
    still decides each attach, but the superleader can prepare it.
- Q5. Can agents edit entry descriptions?
  - A (Recommended, MVP): No, descriptions are user-only. The description is what agents trust
    when choosing, so only the owner writes it.
  - B: Agents may propose description edits through T-18 proposals. Helps keep descriptions
    current at the cost of a new proposal target.
  - C: Superleaders edit descriptions directly. Fastest, but an agent could mislabel an entry.
- Q6. What happens to the existing `secret_set` tool?
  - A (MVP): Keep it unchanged. No work; copies over a vault-backed var stay possible.
  - B (Recommended): Keep it for agent-generated values; 409 on a vault-backed var. Closes the
    T-67 copy path without losing a working capability.
  - C: Remove `secret_set` and the agent secret PUT route. Agents never handle values, but they
    lose a way to store credentials they generate.
- Q7. How do existing per-preset protected vars move into the vault?
  - A (MVP): Keep both layers; the user creates entries and attaches by hand. Zero risk, matches
    S6, no tooling.
  - B (Recommended): Assisted adopt: user enters each value once and ticks presets to convert.
    No value is read; fixes duplicated keys like the T-67 GPG key.
  - C: One-off import Job with temporary Secret get access, one entry per preset var. Automatic,
    but needs a read grant and still needs descriptions.
- Q8. What does deleting an entry that is still attached do?
  - A (Recommended, MVP): Refuse with 409 and list the attachments. Nothing breaks silently; the
    user detaches first.
  - B: Cascade: detach everywhere, then delete. One click, but attached presets silently lose the
    var.
  - C: Soft delete: hidden from `vault_list`, existing attachments keep working. Nothing breaks,
    but dead entries linger.
- Q9. How much audit trail for vault writes?
  - A (MVP): Event rows for every vault write; human writes no longer only logs. Durable,
    queryable record with names only.
  - B (Recommended): A plus an Events tab per entry in the web. The user sees who attached or
    rotated what, and when.
  - C: Logs plus existing `admin_call` rows only. No new event kinds; human writes stay
    unrecorded.
- Q10. Do project-level vault references ship in this epic?
  - A (Recommended, MVP): No; this epic ships preset refs; projects reuses the vault for S1-S4. Keeps
    T-72 independent of the unmerged projects branch.
  - B: Yes; T-72 also ships `project_env` refs. One delivery, but blocked until projects stage 1
    merges.
