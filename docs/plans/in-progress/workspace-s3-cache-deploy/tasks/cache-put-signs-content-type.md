---
title: cache put signs content type
status: todo
repo: agents-orchestrator
value: workspace cache saves succeed on Ceph RGW
files: [src/agents_orchestrator/cache/presign.py, src/agents_orchestrator/cache/transfer.py, tests/test_cache_presign.py, tests/test_cache_cli.py]
verify: "uv run pytest -q -o addopts='-m \"not integration and not e2e\"' tests/test_cache_presign.py tests/test_cache_cli.py && uv run ruff check ."
depends_on: []
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 4
expected_tokens: 669602
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# cache put signs content type

## Requirement

Live apply 2026-10-26 (diagnosis in the task notes): the workspace cache save fails with upload_failed: HTTP 403 AccessDenied on Ceph RGW 20.2.4. cache/transfer.py save() sends `Content-Type: application/zstd` on the presigned PUT, while cache/presign.py signs only `host` (X-Amz-SignedHeaders=host); RGW then treats the request as anonymous. Probes from the reconciler pod: the same URL without the header returns 200, and a URL presigned with ContentType=application/zstd and sent with that header returns 200. Fix in agents-orchestrator: presign signs the content type for PUT (botocore Params ContentType) from one shared constant that the CLI also sends, so the two cannot drift; GET is unchanged. Update the presign docstring, whose claim that Content-Type need not match does not hold on RGW. Tests: the PUT URL's SignedHeaders include content-type, the CLI sends exactly that value, and a moto round trip still passes.

## Acceptance conditions

- AC1: a PUT URL signs content-type and the CLI sends the same constant [evidence: test:tests/test_cache_presign.py::test_put_signs_content_type]
- AC2: the suite and lint pass [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/cache/presign.py`
- `src/agents_orchestrator/cache/transfer.py`
- `tests/test_cache_presign.py`
- `tests/test_cache_cli.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
