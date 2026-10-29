# Decouple S3 session cache from presets design

## Summary

A preset's `cache.key` becomes a Jinja2 cache name template, rendered once per session at create with the preset name, preset id, session slug and creating service; empty means the default `<preset>-<session>`. One rendered name per session names both S3 objects (workspace archive and Claude transcripts) and is pinned in `status.cache`. The preset-id-derived key and the reserved `preset-` prefix go away. The reconciler, the only S3 credential holder, copies the objects of every session that existed before the change to its new name (server-side, copy only) and repoints it, so rotation keeps working. agents-web edits the template and shows the effective name. The plan follows every recommended answer in Open questions; a "no" there changes the named tasks before the build.

## Intent and why

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I also want to decouple s3 cache from preset. There must be a way to define S3 backup name with jonja2 template with default as preset-sessionname. This must also copy caches of existing sessions, so after rotation everything will work properly." (jonja2 = Jinja2)

Today every session of a preset shares one workspace archive `preset-<sha256(preset id)[:16]>` (`spec.py:413 default_cache_key`), so sessions of one preset overwrite each other (last writer wins), and the name says nothing about the session. The user wants per-session names they can shape. Changing names without a copy would make every recreated session restore nothing (`miss`), hence the copy. The sibling epic s3-cache-management-section (a web section over the cache objects) is blocked on this one and needs a stable naming model.

## Goals

- G1: A preset's `cache.key` is a Jinja2 cache name template; a session created from it stores the rendered name, and an empty template renders the default `<preset>-<session>` that always fits the key rule.
- G2: Templates are checked at preset save (422 on an unsafe or invalid template, or a trial render that breaks the key rule) and rendered in a restricted Jinja2 sandbox; a raw-spec key is rendered with the session variables only.
- G3: One cache name per session names both its workspace archive and its Claude transcripts object, pinned in `status.cache` (`key`, `object`, `sessions_object`) at the first restore.
- G4: No preset-id-derived key remains: `default_cache_key`, the reserved `preset-` prefix and the copy rule are removed, and presets that stored their own derived key get the default.
- G5: The caches of sessions that existed before this epic (workspace and transcripts) are copied server-side to their new names, never moved, deleted or overwritten, and each session is repointed so its next save and a session recreated from the same preset with the same slug use the new name.
- G6: agents-web edits the cache name template on a preset (the default shown from `/meta`) and the discard dialog names the effective cache name and when it is restored.

## Non-goals

- The S3 cache management section and any orchestrator list, inspect or delete API over cache objects (sibling epic s3-cache-management-section).
- Deleting, moving or expiring old `preset-*` or `sessions/<slug>` objects, bucket lifecycle rules, or a quota change.
- A per-session template override at session create or in the new session dialog.
- Changes to agents-helmfile, agents-webhook, agents-schedule, agents-matrix-connector, agents-common or claude-code-wrapper.
- Retiring the migration code once no pre-epic session remains.
- Cache name uniqueness enforcement or locking.
- The live-session transcript backup trigger (cct2 queue item 4).

## Anti-goals

- Any S3 object moved, deleted or overwritten by this epic (leader constraint: copy only).
- A recreated pre-epic session restoring nothing or a stale copy (the timing trap: a live session saves to its pinned name at discard).
- A template that can run loops, call functions, read attributes or inflate output in the api or reconciler process.
- A second S3 credential path, or S3 credentials in the api.
- A legacy-key fallback on restore or any compatibility shim (the pre-epic key formula lives only in the migration, to recognise old sessions).
- The sibling's seam made harder: the naming module must stay importable by the api (no `reconciler` or `k8s` import).

## Constraints

- Python only except the web frontend (TypeScript); services talk over HTTP; one writer per table: the api writes `sessions.spec` and `presets`, the reconciler writes `sessions.status`. So the migration repoints `status.cache` only and leaves a pre-epic session's `spec.cache.key` as its old literal (my call).
- Only the reconciler holds the S3 credentials (workspace-s3-cache D2); the api may not import `reconciler` or `k8s` (`test_api_never_imports_k8s_or_wrapper`).
- TDD, no em dashes, no backward compatibility unless asked.
- Rendered names keep `spec.CACHE_KEY_RE` `^[a-z0-9][a-z0-9._-]{0,62}$` (a strict subset of the AWS safe key set; brief-docs section 2).
- Ceph RGW ignores destination `If-None-Match` on CopyObject and moto 5.2.4 does too (brief-docs section 3), so never-overwrite relies on HEAD-then-copy under the single-writer reconciler.
- Sequencing: the in-progress epics hive decoupling and slash commands from chat change the same files (agents-orchestrator README.md, MEMORY.md, openapi.json, pyproject.toml, uv.lock, spec.py, api/schemas.py, tests/test_migrations.py; agents-web vendored orchestrator schema), so they are this epic's README blockers (`ticket.py` file overlap rule) (my call).
- Builder start (builder-check Q1, my call): the builder waits for both README blockers (hive decoupling, slash commands from chat) to land on main, rebases onto them, and takes the next free SQL migration number at build time (main has migrations up to 0009 today). They stay README blockers; nothing in the plan changes.
- Deploy order (interrogate, Noted): the orchestrator tasks ship together in one release; orch-transcripts-follow-name never ships before orch-cache-name-migration, because without the migration's pending rule (D9) a pre-epic session's transcripts restore would read `sessions/<legacy key>`, a name that never existed. The epic lands on main as one close, so no orchestrator image is cut between them (my call).
- No Docker in agent pods: DB-backed tests run in CI; reviewers read the CI result for them.

## Decisions

### D1: The template lives in the preset's `cache.key`

`WorkspaceCache.key` accepts a cache name template (at most 256 characters, checked by `cache.naming.check_template`); empty means the default; a literal key (no template syntax) renders to itself, so today's explicit shared keys keep working unchanged. A stored session's `spec.cache.key` holds the rendered literal. Alternatives: a new field `cache.name_template` beside a literal `key` (two fields meaning one thing, a contract shape change for three consumers); a global setting `ORCH_CACHE_NAME_TEMPLATE` (no per-preset control, needs a deploy to change). Why: one field, the existing contract shape, and every stored literal key is already a valid template. Open question Q2.

### D2: Variables and the default

Variables `preset` (`slugify(preset name)`), `preset_id`, `session` (slug), `created_by` (service token name or `""`). `DEFAULT_CACHE_NAME_TEMPLATE` renders `<preset>-<session>`, shortening the preset part so the result always matches the key rule (40 + 1 + 40 = 81 > 63; a preset name may slugify to empty). Every rendered name must match `CACHE_KEY_RE`, else 422. Alternatives: the raw preset name (uppercase and spaces break the key rule); the session id (not known before the INSERT, `db/sessions.py:120-122`); rejecting long defaults (the default must never fail). Why: the user's "default as preset-sessionname", made always valid. The exact default text is left to the builder within that boundary. `<preset>-<session>` is ambiguous across presets (`a-b` + `c` equals `a` + `b-c`); accepted, names may be shared by design (my call). Open question Q3.

### D3: A restricted in-process Jinja2 sandbox in agents-orchestrator

One module-level `ImmutableSandboxedEnvironment` (`StrictUndefined`, no loader, no extensions, emptied globals, `*` and `**` intercepted), a 256-character cap, an AST allowlist (output expressions only: no `for`, `if` block, `macro`, `call`, `set`, `include`, `import`, `extends`, `with` or `filter` block, no function or method call, no attribute access), filters `lower`, `upper`, `replace`, `trim`, `truncate`, variables limited by `meta.find_undeclared_variables`, every exception mapped to `ValueError`, and the key rule after render. Alternatives: agents-webhook's forkserver child with time and memory bounds (`prompt.py`), heavier and needed there because prompts allow loops; sharing through agents-common (AO does not depend on it); a regex substitution engine (the user asked for Jinja2). Why: the allowlist, the filter overrides and the per-step cap bound the work, so no child process is needed in the api or the reconciler (my call). Open question Q7.

Amended 2026-10-29 (interrogate Act on 1, builder-check Q4 and Q5): the earlier rationale "the allowlist bounds the work by template length" was false. `"%0999999999d" % 1` allocates about 1 GB (`%` is not intercepted by the sandbox) and chained `replace("", X)` grows multiplicatively (lead verified: `"%060d" % 1` renders 60 characters, two `replace("","xyz")` links take `ab` to 47), and the key rule runs only after the render. So:
- The AST allowlist is exact (my call, builder-check Q4): `Template`, `Output`, `TemplateData`, `Name` (an allowed variable), `Const` string literals, integer `Const` only as slice bounds and filter arguments, `Getitem` only with a `Slice`, `CondExpr`, `Concat` (`~`), and `Filter` nodes of the five allowed filters with literal arguments. Every other node is refused, so every `BinOp` (`+`, `-`, `*`, `/`, `//`, `%`, `**`) is refused; `~` is a `Concat` node and stays allowed. The `*` and `**` interception stays as a second line.
- `replace` is a module filter that refuses an empty `old` with `ValueError`.
- Every filter refuses an input and an output longer than 256 characters, and a rendered output longer than 256 characters is refused, each with `ValueError`, before the key rule runs.
- A template that does not parse (a Jinja2 `TemplateSyntaxError`) is re-raised as `ValueError` (my call, builder-check Q5).
Alternatives: intercept `%` only (leaves `+` and the other BinOps to reason about one by one); a render time limit (needs a child process, rejected above). Acts: orch-cache-name-template AC5, AC11, AC12, AC13.

### D4: Render points

Session create from a preset renders the preset template (or the default) per slug attempt and stores the result; a raw-spec session still needs `cache.key` and renders it with `session` and `created_by` only (a template using `preset` answers 422); preset create and replace check the template and trial-render it with the preset's name, a sample id, a 40-character sample slug and an empty `created_by`. Alternatives: render at every restore and save (the name could change under a live session when a preset is edited); render in the reconciler (the api already has every variable). Why: render once, pin forever.

### D5: One name per session for both objects, pinned in status

The workspace archive is `<prefix><name>.tar.zst` and the transcripts object becomes `<prefix>sessions/<name>.tar.zst` (was `sessions/<slug>`). The first restore of either target pins `status.cache.key`, `object` and the new `sessions_object`; every later run uses the pinned key. Alternatives: transcripts keep `sessions/<slug>` (already not preset-coupled, but then "the S3 backup name" covers only half the backup, and two presets' sessions with one slug share transcripts). Why: in the API and UI the backup is both objects (`SessionView.backup`), and the leader's queue reads one name covering both. Consequence: sessions sharing a name also share transcripts, and a recreated session resumes the last conversation saved under it. Open question Q1.

### D6: The derived key and the reserved prefix are removed

`default_cache_key`, `CACHE_KEY_RESERVED_PREFIX`, `check_caller_cache_key`, `check_spec`'s `derived_cache_key`, `_without_derived_key` and the web mirrors go, with their tests (named in the tasks as no longer accurate). A preset copy keeps its cache as is. Alternatives: keep reserving `preset-` (protects nothing once names are not id-derived); reserve rendered names (not computable for arbitrary templates). Why: the prefix guarded the unguessable derived keys (workspace-s3-cache security review); with `<preset>-<session>` any API caller can already create a session from that preset with that slug and reach the same cache, so the rule adds no protection. Open question Q6.

### D7: The copy migration runs in the reconciler, per session, before any cache step

`reconciler/cache_migration.py`, called in `_converge` before the transcripts restore and in `_discard` before the workdir save. A session is pre-epic when `spec.cache` is set, the cache is configured, it has no `status.cache.migration`, and either `status.cache.key` is pinned without `sessions_object` or its `spec.cache.key` equals the pre-epic preset key of its `preset_id`. Its new name is what a session created now from its source preset with its slug would get (the preset's current template or the default, the current preset name; the stored `preset_name` and the default if the preset was deleted); other sessions keep their name. It copies the workspace object when the name changes and `sessions/<slug>` to `sessions/<name>`, then repoints `status.cache` and records `migration`. Alternatives: a startup pass (a session created by the old api between pass and first converge would be missed); an SQL migration (cannot reach S3); a separate Job (would need the Secret, against D2 of workspace-s3-cache); copy without repoint (a live session's discard saves to the old name, and the recreated session restores a stale copy). Why: the reconciler is the singleton credential holder and sole `status` writer, and level-triggered per-session steps are the `CacheRunner` pattern. "Rotation" is read as discard plus recreate with the same slug (open question Q4).

Amended 2026-10-29 (interrogate Act on 2, 4, 6):
- Eligibility (item 2): "no `status.cache.migration` yet" becomes "no `status.cache.migration` record, or one in state `failed`"; a `done` record is final. Otherwise a converge failure followed by a discard could skip the migration, save under the old name, and the recreated session would restore nothing: the timing trap this decision exists to close.
- Deleted presets (item 6): `sessions.preset_id` is `ON DELETE SET NULL` (`0002_presets.sql:19`), so the pre-epic preset key of a deleted preset cannot be computed. A session with `preset_id` NULL, `preset_name` set and a key (`status.cache.key`, else `spec.cache.key`) matching `preset-[0-9a-f]{16}` counts as being on its pre-epic preset key; its new name is the default rendered with `slugify(preset_name)`.
- Save in flight at deploy (item 4): the migration does nothing while a save run of either target is `running` (the save step advances it); when a save of a target has finished, the copy runs after it, from the object that save just wrote, so the new name never carries a stale or half-overwritten copy. Alternative: abort the running save (loses the live workdir). Acts: orch-cache-name-migration AC14, AC16, AC17.

### D8: Copy if absent, server-side, single request

`cache/copy.py:copy_if_absent`: HEAD the destination (200: `exists`, nothing written); on 404 HEAD the source (404: `source_missing`); else `copy_object` with `CopySource` as a dict, `CopySourceIfMatch` the source ETag and the default `MetadataDirective=COPY` (`copied`); any other status raises `CopyError` without credentials. One CopyObject (objects are at most 5 GiB, `CACHE_MAX_BYTES_LIMIT`; largest today 434 MB); the one `presign._client`; called with `asyncio.to_thread`. Alternatives: destination `If-None-Match: *` (ignored by RGW and moto on copy); download and upload through the reconciler (slow, memory); UploadPartCopy (not needed under 5 GiB). Why: brief-docs section 3.

### D9: Migration failure handling

A render error records `migration: failed` once and keeps the old names. A `CopyError` while converging records `failed` with `failures` and `next_at` (`settings.retry_delay_seconds`, database clock), keeps the old names and retries; the restore meanwhile reads the old name, whose content is the same. During a discard it repoints anyway and records the failure, so the save writes the live workdir under the new name and the discard is never held. Alternatives: hold the session until the copy succeeds (a 403 would block it forever); give up after one failure (a transient RGW error would leave the session coupled) (my call).

Amended 2026-10-29 (interrogate Act on 2, 3, 5):
- Discard retries (item 2): in `_discard` every record that is not `done` (none, or `failed` from a render or a copy) is retried at once, regardless of `next_at`, and then repointed or kept per target as below; the discard is still never held.
- Transcripts while pending (item 3): "the old name has the same content" holds for the workspace only; before the migration a pre-epic session's transcripts live at `sessions/<slug>`, never at `sessions/<legacy key>`. While a session's migration is pending (eligible under D7 with no `done` record, including `failed`), the transcripts restore and save presign the legacy `<prefix>sessions/<slug>.tar.zst` and `status.cache.sessions_object` is not pinned; it is pinned only by the migration's repoint or, for a session that is not pre-epic, by the first restore. Once `sessions_object` is pinned, the sessions target presigns exactly that object. Alternative: hold the transcripts restore until the migration has an outcome (bounded wait; a 403 would hold every converge until the bound).
- Repoint after a failed copy (item 5): in `_discard` the repoint is per target. The workspace target (`key`, `object`) and the transcripts target (`sessions_object`) each take the new name when their copy succeeded (`copied`, `exists`, `source_missing`, `unchanged`) or when `save_skip(settings.cache_available, status, target)` (`cache/save_rule.py`) is None, so their save lands under the new name; a target whose copy failed and whose save is skipped (`never_converged`, a failed restore, `not_configured`) keeps its old object, and the record is `failed` naming that target. Alternative: repoint everything anyway (the earlier text: nothing lands under the new name and the status points at a name holding nothing). Acts: orch-cache-name-migration AC8, AC9, AC15, AC18, AC19.

### D10: Presets that stored their own derived key get the default

An SQL migration removes `cache.key` from presets whose stored key equals their own pre-epic derived key (`'preset-' || left(encode(sha256('workspace-cache:' || uuid_send(id)), 'hex'), 16)`); other literal keys stay. Alternatives: leave them (they would stay coupled to one shared preset-wide name, the opposite of the request); strip every `preset-*` key (a user may have chosen one deliberately). Why: such a key is the old default written out (possible through a preset edit, `_validated` accepted the own derived key) (my call). Open question Q9.

### D11: The default applies to every preset, trigger presets included

Webhook and schedule sessions use per-event slugs (`wh-<event id>`, schedule run slugs), so under the default each gets a fresh cache that is never restored, instead of today's shared per-preset cache; objects accumulate against the bucket quota (100G, 100000 objects) until the sibling epic manages them. A preset that wants a shared cache sets the template `{{ preset }}`. Alternatives: a different default for trigger-created sessions (the user named one default); migrating trigger presets to `{{ preset }}` (changes presets the user did not ask to change). Open question Q5.

### D12: agents-web

The preset form's cache field becomes `Cache name template` (placeholder: the orchestrator default from `/meta`; helper text: the variables and sharing semantics); the client checks only the 256-character cap and shows the orchestrator's 422; the reserved-prefix rule and the copy rule go. The discard dialog names the effective name (`status.cache.key`, else `spec.cache.key`) for both objects and says they come back for the next session with the same cache name, replacing the wrong "restored when a session with the same slug is created". Alternatives: a client-side Jinja2 renderer or preview endpoint (idea from the cartographer, not needed to deliver the request; noted, not doing now).

### D13: `/meta` exposes the default template

`GET /api/v1/meta` `cache.default_name_template` carries `DEFAULT_CACHE_NAME_TEMPLATE`, so the web never duplicates it. Alternative: hard-code the default in the web (drifts) (my call).

### D14: The template is per preset only

No per-session override at create (`CreateSession` has no cache field; the new session dialog is unchanged). Alternatives: a `cache_name` field on `POST /api/v1/sessions` and in the new session dialog (cartographer idea; widens the create contract for webhook, schedule and matrix callers). Why: presets are where the cache is configured and sessions snapshot them. Open question Q8.

## Research

| Lens | Ran or skipped | Adopted ideas | Rejected ideas |
|---|---|---|---|
| codebase-cartographer (research-code-internal) | ran, `/workdir/workdir/.scratchpad/s3-cache/brief-cartographer.md` | render at `_create_from_preset` per slug attempt (`api/sessions.py:257-295`); pin in `status.cache` (`reconciler/cache.py:350-356`); migration in the reconciler with the `CacheRunner` crash-safe pattern; naming module importable by the api (section 6); questions 1-7 (section 7) | per-session template override in `NewSessionDialog.tsx` (D14); template preview endpoint (D12) |
| research-docs | ran, `/workdir/workdir/.scratchpad/s3-cache/brief-docs.md` | `ImmutableSandboxedEnvironment` + `StrictUndefined` + emptied globals + intercepted `*`/`**` (section 1, jinja.palletsprojects.com/en/3.1.x/sandbox/); `jinja2>=3.1.6` for GHSA-q2x7-8rv6-6q7h and GHSA-cpwx-vrp4-4pq7; HEAD-then-CopyObject with `CopySourceIfMatch` (section 3); key rule satisfies AWS and RGW (section 2) | destination `If-None-Match` on copy (RGW `rgw_rest_s3.cc` does not read it); UploadPartCopy; full-bucket listing as the migration source (the DB names the sources, idea 4) |
| research-code-external | skipped: the one analogue (a sandboxed user template) is in-house, agents-webhook `src/agents_webhook/prompt.py`, read by the cartographer | none | none |
| research-papers | skipped: no scientific or algorithmic core | none | none |
| interrogate (plan review panel: A fable, B opus, C sonnet; lead cct2-1) | ran 2026-10-29 on README, design.md and tasks, verdict `/workdir/workdir/.scratchpad/s3-cache/interrogate.md` | Act on 1-6, all applied: sandbox render cost (D3; orch-cache-name-template), failed-then-discarded migration, transcripts of an unconverged session, discard in flight at deploy, repoint after a failed copy with a skipped save, deleted-preset sessions (D7, D9; orch-cache-name-migration); Noted deploy order (Constraints); Consider items as open questions Q10 and Q11 | Dismissed by the panel: a one-writer violation (the migration writes only `status`); concurrent reconcilers (sessions reconcile sequentially, `loop.py:150`) |
| builder check (sonnet) | ran 2026-10-29, `/workdir/workdir/.scratchpad/s3-cache/builder-check.md` | Q1 wait for the blockers, next free migration number (Constraints, my call); Q3 as open question Q11; Q4 exact AST node list (D3, my call); Q5 syntax error as `ValueError` (D3, my call) | Q2 (are Q1-Q9 approved) is the gate's question, not a plan change |

## Research inputs

Retro proposals of the most recently done epics that bear on this epic (ticket.py retro --history), recurring workflow ones first:

- Recurring (matrix-connector-agent-initi, deploy-safe-agent-sessions, parked-epic-stage): task files created with empty Steps. Every task here carries written Steps before the gate. Acts: all tasks.
- Recurring (matrix-connector-agent-initi, deploy-safe-agent-sessions, file-editor-with-tabs-and-hi): defects passing per-task review and found only at the epic review; run the security checklist per task and check the headline promise end to end. Acts: each orchestrator task's Notes carry the per-task security check; orch-cache-name-migration AC2 proves migrate, save, recreate and restore in one test.
- Recurring (matrix-connector-agent-initi, deploy-safe-agent-sessions, file-editor-with-tabs-and-hi): no Docker in the pod makes DB tests CI-only. Acts: every orchestrator task's Notes say the reviewer reads CI for DB tests; orch-cache-name-template and orch-cache-copy-if-absent are pure-module tests that run locally.
- Recurring (file-editor-with-tabs-and-hi, markdown-rendering-in-chat): save the failing test name and output tail before a rerun. Acts: all tasks' Notes.
- matrix-connector-agent-initi: web `openapi/orchestrator.source` pinned an epic-branch commit, so the orchestrator PR needed a merge commit. Acts: web-preset-cache-name-field Notes.
- deploy-safe-agent-sessions: `test_lightkube_default_client_uses_env_config` fails in-cluster and is listed again unfixed. Not this epic's scope; named in the orchestrator task Notes so it is not mistaken for a regression. Acts: orchestrator tasks' Notes.

Brief plan inputs:

- reuse `presign._client` for head and copy (brief-docs reuse; cartographer section 5). Acts: orch-cache-copy-if-absent.
- reuse `spec.CACHE_KEY_RE` as the post-render validator and `spec.slugify` for `preset` (both briefs). Acts: orch-cache-name-template.
- reuse the `status.cache.key` pinning and the `CacheRunner` crash-safe status pattern (cartographer). Acts: orch-transcripts-follow-name, orch-cache-name-migration.
- reuse `npm run sync:api -- orchestrator` and the OpenAPI regen command (cartographer section 8). Acts: orch-cache-name-on-create, web-preset-cache-name-field.
- do-not-build: moving or deleting old objects, a list or delete API, lifecycle rules, locking, a claude-code-wrapper change, an agents-common dependency, a legacy-key fallback on restore, multipart copy, hand-rolled pagination (both briefs). Placed in Non-goals and Anti-goals.
- fix-as-ac: `jinja2>=3.1.6` runtime dependency (orch-cache-name-template AC1); sandbox settings, 256-character cap, variable allowlist, trial render 422 (orch-cache-name-template AC5-AC8, orch-cache-name-on-create AC4); rendered name must match the key rule (orch-cache-name-template AC7); copy never overwrites, 403 is an error, `CopySource` dict, metadata COPY (orch-cache-copy-if-absent AC2, AC4); off the event loop (orch-cache-name-migration Interfaces); tests do not claim destination `If-None-Match` (orch-cache-copy-if-absent Notes); both objects copied (orch-cache-name-migration AC1); discard dialog wording and effective name (web-discard-effective-name AC1-AC3); README and contract notes on `default_cache_key` (orch-cache-name-on-create AC10); reserved prefix vs a preset named "preset..." (resolved by D6).
- ideas adopted: migration outcome per session in `status.cache.migration` (cartographer; orch-cache-name-migration); sources derived from the DB, not a bucket listing (brief-docs idea 4; orch-cache-name-migration). Rejected: per-session override (D14), preview endpoint (D12), recording the Ceph release in agents-helmfile MEMORY (other repo; noted, not doing now).

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 template in cache.key | orch-cache-name-on-create, web-preset-cache-name-field |
| D2 variables and default | orch-cache-name-template, orch-cache-name-on-create |
| D3 restricted sandbox | orch-cache-name-template |
| D4 render points | orch-cache-name-on-create |
| D5 one name for both objects | orch-transcripts-follow-name, orch-cache-name-migration |
| D6 derived key and prefix removed | orch-cache-name-on-create, web-preset-cache-name-field |
| D7 copy migration in the reconciler | orch-cache-name-migration |
| D8 copy if absent | orch-cache-copy-if-absent |
| D9 migration failure handling | orch-cache-name-migration |
| D10 presets with their own derived key | orch-preset-legacy-key-strip |
| D11 default for every preset | orch-cache-name-on-create |
| D12 agents-web | web-preset-cache-name-field, web-discard-effective-name |
| D13 meta default template | orch-cache-name-on-create, web-preset-cache-name-field |
| D14 per preset only | orch-cache-name-on-create |

## Review focus

- The sandbox (orch-cache-name-template): can any template within 256 characters loop, call, read an attribute, reach a global, or render unbounded output; are all exceptions mapped to `ValueError`; is `StrictUndefined` in force. Specifically: every `BinOp` (`%` included) refused, `replace` with an empty `old` refused, and no filter input, filter output or rendered output over 256 characters (D3 amendment).
- The migration failure paths (orch-cache-name-migration, D7 and D9 amendments): a `failed` record is retried, in discard at once; nothing runs while a save is `running`; a pre-epic session's transcripts read `sessions/<slug>` until the repoint; a failed copy with a skipped save keeps that target's old object; a deleted preset's session is recognised.
- Copy only (orch-cache-copy-if-absent, orch-cache-name-migration): no delete, put or overwrite anywhere in the diff; a 403 HEAD never reads as absent; no credential or presigned query in a reason, log or error.
- The timing trap (orch-cache-name-migration): after the migration a live session's discard saves under the new names, and a session recreated from the same preset with the same slug restores exactly those objects.
- Pinning (orch-transcripts-follow-name): once `status.cache.key` is set, no restore or save of either target reads the spec key or the slug.
- One writer: the reconciler writes only `status`; the api writes `spec` and `presets`; the SQL migration touches only presets carrying their own derived key.
- The api still imports neither `reconciler` nor `k8s`.

## Left to the builder

- The exact text of `DEFAULT_CACHE_NAME_TEMPLATE`, within D2's boundary (renders `<preset>-<session>` for short inputs, always matches the key rule), documented in the module.
- How the AST allowlist walk is written, within D3's node and filter lists.
- How the migration is wired as a class or functions, and the exact `status.cache.migration` key order, within D7 and D9.
- The helper text wording in the web form, within D12.
- The SQL migration number: the next free one on the base branch at build time.

## Assumptions and unknown facts

- Which live session (cct2, claude-code-tatara, mx-34) carries which `spec.cache.key` and `status.cache`: unknown, needs `SELECT slug, spec->'cache', status->'cache' FROM sessions` or the public API with a token; the migration's per-session `status.cache.migration` record shows it after deploy. Who: the orchestrator, read-only probe before the deploy.
- Ceph RGW CopyObject on the deployed release (not pinned in the workbench): assumed supported (RGW features list); confirmed by the first migration record (`copied`) after deploy, never by a test.
- HEAD answering 404 (not 403) for a missing object needs `s3:ListBucket`; assumed true for the ObjectBucketClaim owner (Rook default, unverified); a 403 surfaces as `migration: failed` with the status code.
- "Rotation" means a session discarded and recreated with the same slug (matrix `mx-<run_id>` reuses its slug per binding); a StatefulSet pod replacement keeps the PVC and runs no cache Job, so it is unaffected. Open question Q4.
- agents-helmfile smoke: sessions A and B share the raw key `smoke-workspace-cache`, so under D5 B also restores A's transcripts and may resume its conversation; the smoke only greps the workspace marker, so it is assumed to stay green; confirmed by the post-deploy smoke.
- Whether any preset stores its own derived key: unknown (DB read); the D10 migration is correct either way.
- No transcripts object of a live session exists today (cartographer probe), so `sessions/<slug>` copies will mostly answer `source_missing`.

## Open questions

The plan follows each recommended answer; a "no" changes the tasks named in the decision before the build.
- Q1: Does the one cache name cover both S3 objects of a session, the workspace archive and the Claude transcripts, which move from sessions/<slug> to sessions/<name>? Sessions sharing a name then also share transcripts, and a recreated session resumes the last conversation saved under it. D5 [recommended: yes, one name covers both objects]
- Q2: Is the template the preset's existing cache.key field read as a Jinja2 template, empty meaning the default and a literal key keeping today's shared-cache behaviour, rather than a new field or a global setting? D1 [recommended: yes, cache.key is the template]
- Q3: Are the template variables preset (slugified preset name), preset_id, session (slug) and created_by, with the default rendering <preset>-<session> and shortening the preset part so it always fits the 63-character key rule, and a rendered name that breaks the rule refused with 422? D2 [recommended: yes, those four variables and that default]
- Q4: Does rotation mean a session discarded and recreated with the same slug, so the migration copies each existing session's objects to its new name and repoints the session so its next save goes to the new name? D7 [recommended: yes, rotation is discard plus recreate with the same slug]
- Q5: Does the per-session default apply to every preset, including webhook and schedule presets, so each trigger session gets its own cache that is never restored again and objects accumulate until the cache management section cleans them, while a preset that wants today's shared cache sets the template {{ preset }}? D11 [recommended: yes, one default for every preset]
- Q6: Drop the reserved preset- prefix rule and the preset-id-derived key, since any API caller can already create a session from a preset with a free slug and so reach the same cache? D6 [recommended: yes, drop both]
- Q7: Render templates in-process in agents-orchestrator with a restricted Jinja2 sandbox: output expressions only, no loops or calls, filters lower, upper, replace, trim, truncate, 256 characters at most, instead of agents-webhook's child-process renderer or a shared library? D3 [recommended: yes, restricted in-process sandbox]
- Q8: Is the template set per preset only, with no per-session override field on session create or in the new session dialog? D14 [recommended: yes, per preset only]
- Q9: Remove cache.key from presets that stored their own preset-derived key, so they get the per-session default instead of staying on one shared preset-wide name? D10 [recommended: yes, strip only a preset's own derived key]
- Q10: The default <preset>-<session> is ambiguous across presets (preset a-b with session c equals preset a with session b-c, and truncation adds more collisions), and a shared name now shares the workspace archive (which may hold .env files and git credentials) and the transcripts (Q1). Should the default carry a short preset_id hash, for example <preset>-<session>-<first 6 hex of preset_id>, so two presets never share a cache by accident while a template can still share on purpose? D2 (interrogate Consider) [recommended: yes, add a short preset_id hash to the default]

## Irreversible operations in scope

- New S3 objects written by the migration (one copy per pre-epic session and object, about 435 MB today) count against the bucket quota; nothing is moved, deleted or overwritten (leader constraint). Safeguard: copy-if-absent, single-writer reconciler; the old objects stay, so a rollback still finds them.
- `status.cache` of live sessions repointed to the new names: a rollback to the previous orchestrator would keep saving under the new names, which the old code does not derive; the old objects remain for a manual repoint. Covered by approving this plan.
- The SQL migration removes `cache.key` from presets that stored their own derived key; reversible only by recomputing the key (the formula is in the migration and pinned by its test). Covered by approving this plan.
