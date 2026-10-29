---
title: orch cache copy if absent
status: todo
repo: agents-orchestrator
value: "The reconciler can copy a cache object server-side without ever overwriting, moving or deleting one"
files: [src/agents_orchestrator/cache/copy.py, tests/test_cache_copy.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_copy.py && mise run lint"
depends_on: []
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 967422
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch cache copy if absent

## Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I also want to decouple s3 cache from preset. There must be a way to define S3 backup name with jonja2 template with default as preset-sessionname. This must also copy caches of existing sessions, so after rotation everything will work properly." (jonja2 = Jinja2)

Leader constraint: the migration copies only, never moves or deletes S3 objects.

This task delivers design D8 in agents-orchestrator: a new module `src/agents_orchestrator/cache/copy.py` with `copy_if_absent(settings, source: str, dest: str) -> Literal["copied", "exists", "source_missing"]`, a synchronous server-side copy of one object key to another in `settings.cache_s3_bucket` through the one `presign._client` (no second credential path).

Recipe (brief-docs section 3): `head_object(dest)`: 200 answers `exists` and nothing is written (never overwrite). 404, then `head_object(source)`: 404 answers `source_missing`. 200, then `copy_object(Bucket, Key=dest, CopySource={"Bucket": ..., "Key": source}, CopySourceIfMatch=<the source ETag>)` with the default `MetadataDirective=COPY`, answering `copied`. Any other status (403 on a HEAD, 412 from a source rewritten meanwhile, 5xx) raises `CopyError`, whose message carries the operation and the status code and never a credential or a URL query.

The module never calls `delete_object`, `delete_objects` or `put_object` (copy only: the leader constraint). It is a single CopyObject (every object is at most `CACHE_MAX_BYTES_LIMIT`, 5 GiB); no multipart copy. Destination `If-None-Match` is not relied on (Ceph RGW and moto 5.2.4 ignore it on copy).

## Acceptance conditions

- AC1: a present source is copied to an absent destination; the source is unchanged and the destination holds the same bytes [evidence: test:tests/test_cache_copy.py::test_copies_when_dest_absent]
- AC2: an existing destination answers exists and keeps its bytes [evidence: test:tests/test_cache_copy.py::test_existing_dest_is_never_overwritten]
- AC3: an absent source answers source_missing and writes nothing [evidence: test:tests/test_cache_copy.py::test_missing_source_writes_nothing]
- AC4: a 403 on a HEAD raises CopyError and is never read as absent [evidence: test:tests/test_cache_copy.py::test_forbidden_head_raises]
- AC5: a 412 from CopySourceIfMatch raises CopyError [evidence: test:tests/test_cache_copy.py::test_source_changed_raises]
- AC6: a CopyError message carries the operation and status and no access key, secret or signature [evidence: test:tests/test_cache_copy.py::test_error_carries_no_secret]
- AC7: the copy module calls no delete or put [evidence: command:! grep -nE "delete_object|delete_objects|put_object" src/agents_orchestrator/cache/copy.py]
- AC8: lint passes [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/cache/copy.py`
- `tests/test_cache_copy.py`

## Interfaces

- `src/agents_orchestrator/cache/copy.py` (new): `CopyOutcome = Literal["copied", "exists", "source_missing"]`, `class CopyError(Exception)`, `copy_if_absent(settings: Settings, source: str, dest: str) -> CopyOutcome` (synchronous; callers run it with `asyncio.to_thread`).
- Uses `presign._client(settings.cache_s3_endpoint, settings.cache_s3_region, settings.cache_s3_path_style, settings.cache_s3_verify_tls, settings.cache_s3_access_key_id, settings.cache_s3_secret_access_key)`; no second client or credential path (MEMORY 2026-10-28, one `_client`).

## Expected outcome

`copy_if_absent(s, "workspace-cache/preset-x.tar.zst", "workspace-cache/my-repo-alpha.tar.zst")` copies once and answers `copied`, answers `exists` on a second call without writing, answers `source_missing` when the source is absent, and raises `CopyError` on any other S3 answer.

## Steps

- Read cache/presign.py, settings.py (cache fields) and tests/test_cache_presign.py (its ThreadedMotoServer fixture and `_no_ambient_aws`) in one pass.
- Red: write tests/test_cache_copy.py with the tests named in the acceptance conditions (moto server for AC1-AC3, `botocore.stub.Stubber` on the client for the 403 and 412 cases); run `uv run --frozen pytest -q -p no:cacheprovider tests/test_cache_copy.py`; expect failure on the missing module.
- Green: write cache/copy.py; rerun; expect all passed.
- `mise run lint`; expect exit 0.

## Notes

- brief-docs section 3 holds the recipe and citations: RGW does not read destination `If-None-Match` on CopyObject and moto 5.2.4 ignores it, so never-overwrite is HEAD-then-copy, safe because the reconciler is the single writer.
- `head_object` raises `botocore.exceptions.ClientError`; read `error.response["Error"]["Code"]` and `ResponseMetadata.HTTPStatusCode`; 404 is `"404"`/`NoSuchKey`. HEAD answers 403 instead of 404 without `s3:ListBucket`; that must raise, never read as absent.
- Pass `CopySource` as a dict so botocore URL-encodes the key; keep the default `MetadataDirective=COPY` (the stored Content-Type is the one the presigned PUT signed).
- These tests need no Postgres, so they run locally.
- Tree state (pictures baseline, 2026-10-28): `mise run lint` green; the full suite is red-env only. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers, and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, markdown-rendering-in-chat).
- Per-task security check (retro, recurring): user input reaching S3 keys or a template engine is the high-risk surface here; check size bounds, refusal paths and that no credential or presigned query reaches a log, a status reason or an error message.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
