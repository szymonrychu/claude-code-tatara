---
title: cache presign
status: done
repo: agents-orchestrator
value: "the reconciler signs one short-lived URL per object, so S3 credentials stay in the reconciler"
files: [src/agents_orchestrator/cache/presign.py, pyproject.toml, uv.lock, tests/test_cache_presign.py]
verify: "uv run pytest -q tests/test_cache_presign.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [cache-config, cache-transfer-cli]
model: opus
review: ""
verified_head: 781151a
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: 3
actual_minutes: 4
actual_tokens: 959207
actual_roles: "impl 4, review 1"
actual_role_tokens: "impl 842702, review 116505"
---

# cache presign

## Requirement

Presign the cache object URLs in the reconciler (design D2, D8). Runs after the epic orchestrator-rename-sessions lands. Paths are in code/agents-orchestrator under the post-rename names (design Constraints: if that epic chose other module names, the same symbols apply and the orchestrator amends this file list first).

`src/agents_orchestrator/cache/presign.py`:
- `object_name(settings, key) -> str` = `f"{settings.cache_s3_prefix}{key}.tar.zst"` (one object per key, reused on every save).
- `presign(settings, method: Literal["GET", "PUT"], key: str) -> str`: a boto3 S3 client with `endpoint_url` (None when `cache_s3_endpoint` is empty), `region_name`, signature version `s3v4`, addressing style `path` when `cache_s3_path_style` else `virtual`, `verify=cache_s3_verify_tls`, and the credentials from `cache_s3_access_key_id` and `cache_s3_secret_access_key`; `ExpiresIn = cache_timeout_seconds + 600`. Presigning makes no network call.
- `pyproject.toml`: dependency `boto3`; dev dependency `moto[server]`; `uv.lock` refreshed with `uv lock`.
- A round trip proves the URLs work with the CLI of task cache-transfer-cli: moto's `ThreadedMotoServer` as the endpoint (path style), a bucket created in the test, presign PUT then `orch cache save`, presign GET then `orch cache restore` into a fresh directory.

## Acceptance conditions

- AC1: with path style on, the URL host is the endpoint host and the path starts with the bucket [evidence: test:tests/test_cache_presign.py::test_path_style_url]
- AC2: with path style off, the bucket is in the host [evidence: test:tests/test_cache_presign.py::test_virtual_style_url]
- AC3: the URL expires after the cache timeout plus 600 seconds [evidence: test:tests/test_cache_presign.py::test_expiry]
- AC4: the object name is prefix, key and .tar.zst [evidence: test:tests/test_cache_presign.py::test_object_name]
- AC5: save through a presigned PUT then restore through a presigned GET round-trips the workdir on a moto server [evidence: test:tests/test_cache_presign.py::test_round_trip_through_moto]
- AC6: a presigned GET of a missing key restores as a miss [evidence: test:tests/test_cache_presign.py::test_missing_object_is_miss]
- AC7: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/cache/presign.py`
- `pyproject.toml`
- `uv.lock`
- `tests/test_cache_presign.py`

## Interfaces

- `cache/presign.py:object_name(settings, key) -> str`, `presign(settings, method, key) -> str`.
- Consumes the settings of cache-config and the CLI of cache-transfer-cli.

## Expected outcome

With endpoint `http://rgw:80`, path style on and bucket `b`, `presign(s, "PUT", "k")` returns `http://rgw:80/b/workspace-cache/k.tar.zst?X-Amz-...&X-Amz-Expires=2400`; the moto round trip restores the saved tree.

## Steps

- `uv add boto3` and `uv add --dev 'moto[server]'`.
- Red: write `tests/test_cache_presign.py` (the six named tests; moto `ThreadedMotoServer(port=0)` fixture, bucket made with a boto3 client); run it: fails.
- Green: write `presign.py`; run the verify command.

## Notes

- `boto3.client("s3", endpoint_url=..., region_name=..., aws_access_key_id=..., aws_secret_access_key=..., verify=..., config=botocore.config.Config(signature_version="s3v4", s3={"addressing_style": ...}))`, then `generate_presigned_url("get_object"|"put_object", Params={"Bucket", "Key"}, ExpiresIn=...)`.
- For the PUT, do not sign a ContentType the CLI does not send; if signing it, the CLI's `application/zstd` must match.
- Build the client per call or cache it on the settings identity; presigning is local.

- 2026-10-26 done: Moto does not enforce SigV4, so single-method and single-object scoping is unproven against real RGW; check it in the live smoke (workspace-s3-cache-deploy).
