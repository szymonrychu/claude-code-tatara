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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
