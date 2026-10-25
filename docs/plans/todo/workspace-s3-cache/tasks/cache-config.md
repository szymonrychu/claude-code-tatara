---
title: cache config
status: todo
repo: agents-orchestrator
value: presets and sessions can carry a validated cache setting and the orchestrator reads generic S3 settings
files: [src/agents_orchestrator/settings.py, src/agents_orchestrator/spec.py, tests/test_cache_config.py]
verify: "uv run pytest -q tests/test_cache_config.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# cache config

## Requirement

Add the workspace cache configuration surface (design D6, D7, D8). Runs after the epic orchestrator-rename-sessions lands. Paths are in code/agents-orchestrator under the post-rename names (design Constraints: if that epic chose other module names, the same symbols apply and the orchestrator amends this file list first).

- `src/agents_orchestrator/settings.py`: fields `cache_s3_endpoint: str = ""` (an http or https URL when set), `cache_s3_region: str = "us-east-1"`, `cache_s3_bucket: str = ""`, `cache_s3_prefix: str = "workspace-cache/"`, `cache_s3_path_style: bool = False`, `cache_s3_verify_tls: bool = True`, `cache_s3_access_key_id: str = ""`, `cache_s3_secret_access_key: str = ""` (never in repr or logs), `cache_image: str = ""`, `cache_max_bytes: int = 5368709120` (1 to 5368709120: the single-PUT limit), `cache_timeout_seconds: int = 1800` (60 to 86400). Env names `ORCH_CACHE_S3_ENDPOINT`, `ORCH_CACHE_S3_REGION`, `ORCH_CACHE_S3_BUCKET`, `ORCH_CACHE_S3_PREFIX`, `ORCH_CACHE_S3_PATH_STYLE`, `ORCH_CACHE_S3_VERIFY_TLS`, `ORCH_CACHE_S3_ACCESS_KEY_ID`, `ORCH_CACHE_S3_SECRET_ACCESS_KEY`, `ORCH_CACHE_IMAGE`, `ORCH_CACHE_MAX_BYTES`, `ORCH_CACHE_TIMEOUT_SECONDS` (contract orch-cache-settings-env). A bad value raises `SettingsError` naming the variable.
- Property `cache_available` = `bool(cache_s3_bucket)`. Method `require_cache()`: when the bucket is set and any of `cache_s3_access_key_id`, `cache_s3_secret_access_key`, `cache_image` is empty, raise `SettingsError` naming each missing variable (the api, dispatcher and ingester never call it; the reconciler does, task cache-restore-runner).
- `src/agents_orchestrator/spec.py`: `WorkspaceCache` (strict) with `key: str | None = None` matching `^[a-z0-9][a-z0-9._-]{0,62}$` and `exclude: list[str] = []` (at most 50 entries, each non-empty, at most 256 characters, not absolute, no `..` segment); constants `CACHE_KEY_RE`, `CACHE_EXCLUDE_MAX = 50`, `CACHE_ALWAYS_EXCLUDE = (INIT_DIR,)`; `SessionSpec.cache: WorkspaceCache | None = None`, sparse: unset is not stored or dumped in a preset (contract orch-session-spec-cache).
- `validate_spec`: `spec.cache` set while `not settings.cache_available` adds the error "workspace cache is not configured (ORCH_CACHE_S3_BUCKET is unset)", except when `stored` is given and `stored.cache == spec.cache` (the preset PUT rule the image, model and effort checks use).

## Acceptance conditions

- AC1: the cache settings load from their ORCH_CACHE_* names with the stated defaults [evidence: test:tests/test_cache_config.py::test_cache_settings_defaults_and_env]
- AC2: max bytes above 5368709120, a non-http endpoint and a timeout out of range are refused naming the variable [evidence: test:tests/test_cache_config.py::test_cache_settings_refused]
- AC3: require_cache names each missing credential or image when a bucket is set, and passes with no bucket [evidence: test:tests/test_cache_config.py::test_require_cache_names_missing]
- AC4: the secret access key never appears in the settings repr [evidence: test:tests/test_cache_config.py::test_secret_key_not_in_repr]
- AC5: WorkspaceCache enforces the key pattern and the exclude limits [evidence: test:tests/test_cache_config.py::test_workspace_cache_validation]
- AC6: a spec without cache dumps no cache key (sparse presets) [evidence: test:tests/test_cache_config.py::test_cache_sparse_dump]
- AC7: validate_spec refuses a cache while unavailable and accepts an unchanged stored cache [evidence: test:tests/test_cache_config.py::test_validate_spec_cache_unavailable]
- AC8: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/settings.py`
- `src/agents_orchestrator/spec.py`
- `tests/test_cache_config.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
