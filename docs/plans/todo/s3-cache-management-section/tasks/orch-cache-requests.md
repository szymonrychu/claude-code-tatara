---
title: orch cache requests
status: todo
repo: agents-orchestrator
value: "A user's delete of one cache object runs in the reconciler, which refuses anything a session still uses or that changed since listing"
files: [src/agents_orchestrator/reconciler/cache_requests.py, src/agents_orchestrator/db/cache.py, src/agents_orchestrator/reconciler/loop.py, README.md, MEMORY.md, tests/test_cache_requests.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_requests.py && mise run lint  # DB-backed tests need Docker: CI only here"
depends_on: [orch-cache-pins, orch-cache-inventory]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1919629
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch cache requests

## Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I want to have dedicated section (as presets, sessions, webhooks) for s3 cache management."

README Goal G3, verbatim: "a user deletes one object after typing its name; the orchestrator's reconciler refuses an object pinned by any session row (live, starting or discarding) or rewritten since it was listed, and the outcome (done, refused with reason, failed with reason) is shown."

README Goal G4, verbatim: "S3 credentials stay on the reconciler only; the new routes are on the web port only (not the agent or service ports)."

Design D2 (Delete and refresh requests through a guarded queue), verbatim: "`cache_requests` (id, kind `delete|refresh`, object, etag, size, status `queued|running|done|refused|failed`, reason, timestamps): the api inserts `queued` rows and notifies a new channel `cache_requested` (added to the reconciler's `CHANNELS`); the reconciler claims `queued->running` and executes inside its sequential pass, so no restore, save, backup or migration Job it starts can begin between check and delete: (1) refuse `in_use` per `cache.pins` over every existing session row; (2) HEAD: 404 -> `done/gone`, ETag differs -> `refused/changed`; (3) `delete_object(Key, IfMatch=etag)`, 412 -> `refused/changed`; success removes the inventory row, then `done`. An S3 403 or other error -> `failed` with the reason. The api's own 409 `in_use` check is advisory. If-Match is a backup guard (RGW release unknown; HEAD plus ETag under the single-writer reconciler is the real one). User Q1, Q6."

Design D8 (Relation to the cleanup epic), verbatim: "This epic lists old copies and deletes them one at a time on explicit action. The cleanup epic keeps bulk deletion of proven-copied objects (it needs a durable copy record, because migration records vanish with discarded rows) and will run its deletes as `cache_requests` rows: one executor, one refusal rule. User Q2."

Design anti-goal, verbatim: "Deleting an object a session row pins (live, starting, unconverged or discarding), or one rewritten since the user saw it."

Cartographer plan input (fix-as-ac), verbatim: "deleting an object pinned by a live session (`status.cache.key/object/sessions_object`) or mid-save (`save`/`sessions_save`/`sessions_backup` running) must be refused by the reconciler at execution time."

Open questions Q1 and Q6 are planned on their recommended answers (user decision: "Q1-Q6 in design.md are open; plan on the recommended answers").

This task delivers the executor of D2 in agents-orchestrator, new module `src/agents_orchestrator/reconciler/cache_requests.py`:

- `CacheRequestRunner.run_once()` runs inside `Reconciler.reconcile_once`, right after `self.checks.run_once()` and before the session loop, only when `settings.cache_available`. It first finishes any `delete` request left `running` by a pass that stopped mid-request, then claims queued `delete` requests one at a time, oldest first, `queued->running` with a status-guarded update, until none is left.
- Per request: (1) read every existing session row (`sessions.list_sessions`, every `desired`) and refuse with reason `in_use: <sorted slugs>` when `cache.pins.pins_by_object` names the object; (2) HEAD `<prefix><object>`: 404 -> `done` with reason `gone` and the object's inventory rows removed; an ETag different from the request's -> `refused` with reason `changed`; (3) `delete_object(Bucket, Key, IfMatch=etag)`: 412 -> `refused` with reason `changed`; success removes the object's inventory rows, then `done`. Any other S3 error, including 403 -> `failed` with reason `<Error.Code> <HTTP status>`. No reason or log line holds a credential, signature or URL.
- S3 calls run with `asyncio.to_thread` through the one `presign._client`; no other module calls `delete_object`.
- Every completion is `UPDATE ... WHERE id = %s AND status = 'running'`.
- README `## Workspace cache` gains `### Cache deletes` (the refusal rules and outcomes, and that the cleanup epic reuses this executor); MEMORY.md gains a dated entry (why deletes run in the reconciler pass; HEAD plus ETag as the guard, If-Match as backup).

Review fix (interrogate 2026-10-29, act on 2: S3 errors and hangs block the whole reconcile pass): every request is wrapped. Any exception while executing a request (a connection error, a read timeout, an error from `cache.pins` or from reading the session rows, anything other than cancellation) ends that request `failed` with the exception class name as reason (for example `EndpointConnectionError`, `ReadTimeoutError`); a `ClientError` keeps the `<Error.Code> <HTTP status>` reason above. `CacheRequestRunner.run_once` never raises out of the runner (only `asyncio.CancelledError` propagates): a failure outside a request is logged and the runner returns, so `reconcile_once` always reaches the session loop in the same pass. HEAD and `delete_object` use the bounded client of `presign._client` (connect and read timeouts and a retry bound, added by orch-cache-inventory), so a hung RGW ends the request `failed` within that bound instead of stalling every pass.

## Acceptance conditions

- AC1: a delete is refused in_use, naming the slug, for an object pinned by a live row's status.cache.key, object or sessions_object, by spec.cache.key of a row never restored, by a row in desired deleting, and by a row whose save, sessions_save or sessions_backup run is running; the object is still in the bucket [evidence: test:tests/test_cache_requests.py::test_pinned_objects_refused_at_execution]
- AC2: an object whose ETag differs from the request's is refused changed and kept [evidence: test:tests/test_cache_requests.py::test_changed_object_refused]
- AC3: an object already gone ends done with reason gone and its inventory row removed [evidence: test:tests/test_cache_requests.py::test_missing_object_done_gone]
- AC4: an unpinned, unchanged object is deleted from the bucket with IfMatch set to the request's ETag, its inventory row removed, and the request ends done [evidence: test:tests/test_cache_requests.py::test_unpinned_object_deleted]
- AC5: a 412 from delete_object ends refused changed [evidence: test:tests/test_cache_requests.py::test_if_match_failure_refused_changed]
- AC6: a 403 or other S3 error ends failed with a reason naming the error code and status and holding no access key, secret or URL [evidence: test:tests/test_cache_requests.py::test_s3_error_fails_without_secrets]
- AC7: a delete request left running is executed by the next pass, completes exactly once, and a request no longer running is never completed again [evidence: test:tests/test_cache_requests.py::test_running_request_resumed_and_completed_once]
- AC8: reconcile_once executes queued deletes before converging any session, and does nothing with the cache unconfigured [evidence: test:tests/test_cache_requests.py::test_reconcile_pass_executes_deletes_first]
- AC9: only the reconciler's request module calls delete_object [evidence: command:test "$(grep -rl delete_object src/agents_orchestrator)" = "src/agents_orchestrator/reconciler/cache_requests.py"]
- AC10: the refusal uses cache.pins and carries no second copy of the pin fields [evidence: command:grep -q "pins_by_object" src/agents_orchestrator/reconciler/cache_requests.py && ! grep -nE "sessions_object|from_key" src/agents_orchestrator/reconciler/cache_requests.py]
- AC11: README documents the deletes and MEMORY.md records the guard [evidence: command:grep -q "### Cache deletes" README.md && grep -qE "If-Match|IfMatch" MEMORY.md]
- AC12: lint passes [evidence: command:mise run lint]
- AC13: a connection error and a hang (an endpoint that accepts and never answers, timeouts lowered in the test) on HEAD or delete_object end the request failed with the exception class name as reason, and the session loop still converges a session in the same reconcile_once pass (interrogate act on 2) [evidence: test:tests/test_cache_requests.py::test_s3_connection_error_and_hang_fail_request_and_pass_continues]
- AC14: any other exception while executing a request (for example raised by cache.pins) ends it failed with the exception class name as reason, the next queued request still runs, and run_once does not raise (interrogate act on 2) [evidence: test:tests/test_cache_requests.py::test_any_request_exception_ends_failed_without_raising]

## Files

- `src/agents_orchestrator/reconciler/cache_requests.py`
- `src/agents_orchestrator/db/cache.py`
- `src/agents_orchestrator/reconciler/loop.py`
- `README.md`
- `MEMORY.md`
- `tests/test_cache_requests.py`

## Interfaces

- `src/agents_orchestrator/reconciler/cache_requests.py` (new): `class CacheRequestRunner(pool, settings)` with `async run_once() -> None`; reasons `in_use: <slugs>`, `changed`, `gone`, `<Error.Code> <HTTP status>`.
- `db/cache.py` gains `CacheRequest` (id, kind, object, etag, size, status, reason, created_at, started_at, finished_at), `running_deletes(conn) -> list[CacheRequest]`, `claim_delete(conn) -> CacheRequest | None` (`UPDATE ... SET status='running', started_at=now() WHERE id = (SELECT id ... WHERE kind='delete' AND status='queued' ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED) AND status='queued' RETURNING ...`), `complete_request(conn, id, status, reason) -> bool` (guarded on `running`), `drop_object(conn, key) -> None` (every generation's row of that key).
- `reconciler/loop.py`: `Reconciler.cache_requests` built when `settings.cache_available`; `reconcile_once` calls it after `self.checks.run_once()`.
- Uses `cache.pins.pins_by_object(rows, settings.cache_s3_prefix)` and `presign._client(...)`; never imports from `api`.

## Expected outcome

A queued delete request is executed by the reconciler within one pass: refused when any session row pins the object or it changed since listing, done when deleted or already gone, failed with the S3 reason otherwise; the cleanup epic can queue its deletes into the same table and get the same rules.

## Steps

- Read `reconciler/loop.py` (`reconcile_once`, wiring), `reconciler/checks.py` (`CheckRunner` claim and observe), `reconciler/cache_inventory.py`, `db/cache.py`, `db/sessions.py` (`list_sessions`), `cache/pins.py`, `cache/presign.py` (`_client`), `cache/copy.py` (ClientError handling of HEAD), `tests/test_cache_presign.py` and `tests/test_cache_inventory.py` (moto and pool fixtures) in one pass.
- Red: write `tests/test_cache_requests.py` with every test named in the acceptance conditions (moto server for the bucket; `botocore.stub.Stubber` or a patched client for the 412 and 403 cases; rows inserted as the api will insert them); run `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_requests.py`; expect failure on the missing module (DB tests: on CI or a local Postgres).
- Green: write the module, the `db/cache.py` functions and the loop wiring; rerun the verify; expect passed.
- Write README `### Cache deletes` and the MEMORY.md entry; `mise run lint`; expect exit 0.

## Notes

- The bucket keeps no versions: a delete is permanent (design Constraints, Q1). Under-refusing is the failure to avoid; when unsure, refuse.
- `head_object` raises `botocore.exceptions.ClientError`; read `error.response["Error"]["Code"]` and `ResponseMetadata.HTTPStatusCode`; 404 is `"404"`/`NoSuchKey`. HEAD answers 403 instead of 404 without `s3:ListBucket`; that is `failed`, never `gone`.
- moto 5.2.4 honours `IfMatch` on DeleteObject (architecture sources); the deployed RGW release may ignore it, which is why the HEAD comparison is the real guard.
- Accepted race (architecture): a session the api creates between the check and the delete restores `miss` and starts empty.
- Per-task security check (retro, recurring): the object name comes from a user; it is used only as `<prefix><object>` in a Key parameter (never a path or a shell), and no credential, signature or URL reaches a reason, a log line or an exception stored in the database.
- Builds after decouple-s3-session-cache-fr and live-session-transcript-back landed on main (README blockers). Use their names as landed: `cache/naming.py` (`render_cache_name`, `DEFAULT_CACHE_NAME_TEMPLATE`), `cache/copy.py`, `reconciler/cache_migration.py`, and `status.cache` `key`, `object`, `sessions_object`, `restore`, `save`, `sessions_restore`, `sessions_save`, `sessions_backup`, `migration`. Read the landed code first; where a landed name differs from this task's text, use the landed name and say so in the task Notes, never guess.
- Tree state: `mise run lint` green. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers; agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. Pure and moto-only tests run locally. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, recurring).
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: interrogate 2026-10-29 act on 2
