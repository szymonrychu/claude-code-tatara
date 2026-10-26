---
title: cache put signs content type
status: done
repo: agents-orchestrator
value: workspace cache saves succeed on Ceph RGW
files: [src/agents_orchestrator/cache/presign.py, src/agents_orchestrator/cache/transfer.py, tests/test_cache_presign.py, tests/test_cache_cli.py]
verify: "uv run pytest -q -o addopts='-m \"not integration and not e2e\"' tests/test_cache_presign.py tests/test_cache_cli.py && uv run ruff check ."
depends_on: []
model: ""
review: ""
verified_head: 9c8bb44
points: 1
expected_minutes: 4
expected_tokens: 669602
points_actual: 1
actual_minutes: 4
actual_tokens: 440023
actual_roles: "impl 4, review 1"
actual_role_tokens: "impl 339337, review 100686"
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

See the Requirement; no new cross-repo contract.

## Expected outcome

Every acceptance condition holds on the committed HEAD.

## Steps

- Red: write the AC tests; run the task verify: they fail.
- Green: implement the Requirement; rerun the verify: they pass.
- Run the repo's full suite and lint: green.

## Notes

- See the Requirement and the epic design.md.

- 2026-10-26 done
