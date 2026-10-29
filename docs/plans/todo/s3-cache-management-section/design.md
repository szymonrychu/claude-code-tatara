# S3 cache management section design

## Summary

A Cache section in agents-web lists every S3 cache object with its kind, class, size and age, shows a quota
gauge, and deletes one object at a time after a typed-name confirm. The reconciler, the only S3 credential
holder, keeps a bucket inventory table (full listing every 15 minutes or on Refresh) and executes delete
requests queued by the api in a status-guarded table, refusing objects any session row still pins or that
changed since listing. The api classifies objects on every read from session rows and presets through a pure
`cache.pins` module shared with the reconciler. Bulk deletion of old copies stays in the cleanup epic, which
will reuse this delete path. Source decision: `.scratchpad/s3-section/architecture.md` (architect-researcher,
opus); code map `.scratchpad/s3-section/brief-cartographer.md`.

## Intent and why

User (2026-10-29 04:52Z, mx-34 #343), verbatim: "I want to have dedicated section (as presets, sessions,
webhooks) for s3 cache management." Cleanup follow-up (#355), verbatim: "Migration copies, but there is a
follow-up epic to cleanup them". After decouple-s3-session-cache-fr every session gets its own objects, so
the bucket fills until its quota (100G / 100000 objects); objects of discarded sessions are invisible
without a listing; a corrupt archive is repaired only by deleting its object (orchestrator MEMORY D11),
which no tool can do today.

## Goals

As in README.md G1-G5.

## Non-goals

As in README.md: no bulk delete, no overwrite/upload/download/rename, no MCP or service-port access, no
bucket configuration change, no wrapper/plugins/common change.

## Anti-goals

- S3 credentials in the api, web or any new component (workspace-s3-cache D2, decouple anti-goal).
- Deleting an object a session row pins (live, starting, unconverged or discarding), or one rewritten since
  the user saw it.
- The list badge and the reconciler's refusal disagreeing (two copies of the pin rule).
- A page view triggering a full bucket listing.
- Cache routes reachable from agent or service tokens.
- Overlap with the cleanup epic's bulk deletion.

## Constraints

- AGENTS.md: services over HTTP or a queue; one writer per table; queue rows change only through
  status-guarded updates; Python and TypeScript; no shims.
- The api must not import `reconciler`/`k8s` (`tests/test_api_sessions.py:237`); it may import `cache.*`
  (it already imports `cache.save_rule`). The legacy key formula stays in `reconciler/cache_migration.py`.
- `commands` cannot carry cache requests (`agent_id NOT NULL`, kind CHECK, `0001_init.sql:89-99`); the
  `checks` queue (`db/queue.py:713`, `reconciler/checks.py:105`) is the pattern.
- The bucket has no versioning (`agents-helmfile/raw/workspace-cache-bucket.pre.yaml`): a delete is
  permanent.
- Blockers: decouple-s3-session-cache-fr (names, `sessions_object`, migration records) and
  live-session-transcript-back (`sessions_backup` runs, same cache files). One SQL migration, numbered
  `<MIGRATION>` = next free at build time (0010, 0012 and decouple's are claimed).
- Web: no router; menu from `backends/registry.ts:26 BACKEND_MENUS`; `layout/ConfirmDialog.tsx` is the one
  confirm pattern; design rules in `layout/designRules.ts`; `nomenclature.test.ts`.

## Decisions

### D1: Reconciler-owned inventory table

`cache_objects` (key, kind, size, etag, last_modified, generation), written only by the reconciler: a full
`list_objects_v2` pass every `ORCH_CACHE_INVENTORY_INTERVAL_SECONDS` (default 900) or at once on a refresh
request, in its own asyncio task off the session pass (`asyncio.to_thread`, botocore paginator); a pass
writes a new generation and drops the old one in one transaction. Alternatives: on-demand listing per view
(up to 100 S3 calls per page view, no history); a credentialed component (forbidden). User Q3.

### D2: Delete and refresh requests through a guarded queue

`cache_requests` (id, kind `delete|refresh`, object, etag, size, status `queued|running|done|refused|failed`,
reason, timestamps): the api inserts `queued` rows and notifies a new channel `cache_requested` (added to the
reconciler's `CHANNELS`); the reconciler claims `queued->running` and executes inside its sequential pass,
so no restore, save, backup or migration Job it starts can begin between check and delete: (1) refuse
`in_use` per `cache.pins` over every existing session row; (2) HEAD: 404 -> `done/gone`, ETag differs ->
`refused/changed`; (3) `delete_object(Key, IfMatch=etag)`, 412 -> `refused/changed`; success removes the
inventory row, then `done`. An S3 403 or other error -> `failed` with the reason. The api's own 409 `in_use`
check is advisory. If-Match is a backup guard (RGW release unknown; HEAD plus ETag under the single-writer
reconciler is the real one). User Q1, Q6.

### D3: One pin rule, `cache.pins`

A pure module importable by the api and the reconciler (like `save_rule.py`): a session row pins its
`status.cache.key`/`object`/`sessions_object`, the names it will pin from `spec.cache.key`, and, while its
decouple migration is pending, the legacy `sessions/<slug>` and `from_key` sources; any row saving, backing
up, restoring or migrating pins its object. Rows of every `desired` state count until purged.

### D4: Classes computed at read time

`in_use` (session slugs; not deletable), `preset` (named by a preset whose template renders without the
session variables; preset name; deletable: the D11 repair, user Q5), `legacy` (`preset-[0-9a-f]{16}.tar.zst`;
"copied by N live sessions" from `migration` records in state `done`; deletable, user Q2), `saved` (other
names in the scheme, usually a discarded session restorable on recreate; deletable), `other` (outside the
scheme: smoke objects, strays; deletable).

### D5: API on the web port only

`GET /api/v1/cache` (available, prefix, listed_at, listing state, totals, quota), `GET /api/v1/cache/objects`
(`class`, `q`, `after`, `limit<=500`, ordered by key), `POST /api/v1/cache/deletions {object, etag}` 202
(404 not listed, 409 `in_use`, 503 `cache_not_configured`), `POST /api/v1/cache/refresh` 202,
`GET /api/v1/cache/requests/{id}`. Not in `service_auth.ALLOWED_ROUTES`, not on the agent port. README route
table, `openapi.json`, web `sync:api`.

### D6: Web Cache section

`BACKEND_MENUS.orchestrator` gains Cache at order 50 (`registry.test.ts` exact list updated). Summary bar
(quota gauge when known, "listed <age>", Refresh); class filter chips and name search; table Object, Kind,
Class, Size, Last modified, Delete (disabled for `in_use`, with a tooltip); `ConfirmDialog` with typed object
name, size, "cannot be undone" and "a later session with this name starts empty"; the request is polled every
5 s (`usePoll`) to its outcome; `formatBytes` moves from `DiscardSessionDialog.tsx:45` to a shared module.

### D7: Quota settings

`ORCH_CACHE_QUOTA_BYTES` and `ORCH_CACHE_QUOTA_OBJECTS` (default unset, gauge hidden), set in agents-helmfile
values from the OBC quota (100G, 100000). User Q4.

### D8: Relation to the cleanup epic

This epic lists old copies and deletes them one at a time on explicit action. The cleanup epic keeps bulk
deletion of proven-copied objects (it needs a durable copy record, because migration records vanish with
discarded rows) and will run its deletes as `cache_requests` rows: one executor, one refusal rule. User Q2.

### D9: Deploy and live check

Release orchestrator and web, pin in agents-helmfile with the quota values, apply under the deploy lease; the
live check lists the bucket in the section and deletes one disposable object created for the check (a smoke
object, never a session's cache) (my call).

## Research

| Lens | Ran / skipped | Adopted | Rejected |
|---|---|---|---|
| codebase-cartographer (opus) | ran 2026-10-29, `.scratchpad/s3-section/brief-cartographer.md`, on top of the s3-cache and live-backup briefs | `checks` queue pattern, `BACKEND_MENUS`, `ConfirmDialog`, `usePoll`, `presign._client`, web-port-only routes | reusing `commands`; a new web backend id |
| architect-researcher (opus) | ran, `.scratchpad/s3-section/architecture.md` | D1-D8 | on-demand listing; credentialed component; list-only; folding the cleanup epic in |
| research-docs | covered by the architect (S3/RGW conditional delete: AWS docs 2025-09, RH bz 2375000/2375001; botocore 1.43.118 `IfMatch`; moto 5.2.4 honours it) and `.scratchpad/s3-cache/brief-docs.md` (ListObjectsV2 paging on RGW) | If-Match as backup guard | relying on If-Match alone |
| research-code-internal | covered by the cartographer's Plan inputs (reuse list) | reuse above | - |
| research-code-external, research-papers | skipped: no open fork left; no scientific core | - | - |

## Research inputs

- `registry.test.ts` exact orchestrator list - web task AC.
- README route table and `openapi.json` drift tests (`tests/test_readme_api.py`) - api task AC.
- `ALLOWED_ROUTES` stays without cache routes - api task AC.
- Delete refused for pinned or saving objects at execution time - requests task AC.
- No versioning: deletes permanent - Q1, confirm text.

## Decision coverage

Filled by the planner from the task slugs.

## Review focus

- The reconciler's check-then-delete: every session state pins; ETag comparison; claim guard.
- `cache.pins` shared by api and reconciler, no duplicate rule.
- Inventory generation swap is atomic; listing failures keep the previous generation.
- Web-port-only routes; no credentials outside the reconciler.

## Left to the builder

Module placement, helper names, table indexes, the inventory task's loop structure and test file split,
within D1-D9.

## Assumptions and unknown facts

- The OBC key has DeleteObject (owner key); if not, the first delete ends `failed` with the 403 reason; the
  live check confirms.
- Deployed RGW release and If-Match support: unknown; not relied on.
- Inventory size well under 100000 rows; a pass under 60 s (architect "changes my mind").

## Open questions

- Q1: May a user permanently delete one S3 cache object from the Cache section, after typing its name, with no undo since the bucket keeps no versions (the orchestrator refuses any object a session still uses or that changed since it was listed)? [recommended: yes]
- Q2: Old preset-* copies are listed and deletable one by one here, and bulk deletion of proven copies stays in the cleanup epic, which will use the same delete path? [recommended: yes]
- Q3: Refresh the object list every 15 minutes plus a Refresh button, while "in use" is always current? [recommended: yes]
- Q4: Show a quota gauge by setting the 100G / 100000-object limits as orchestrator settings in agents-helmfile? [recommended: yes]
- Q5: May an object named by a preset's fixed cache name be deleted, so the preset's next session starts empty (the bad-archive repair)? [recommended: yes]
- Q6: One object at a time in this epic, no multi-select? [recommended: yes]

## Irreversible operations in scope

- User-initiated permanent deletion of single S3 cache objects (no bucket versioning) - Q1, typed-name
  confirm, reconciler refusal rules.
- The live check deletes one disposable object created for it.
- SQL migration `<MIGRATION>` (new tables, additive); orchestrator and web releases; helmfile apply under the
  deploy lease.
