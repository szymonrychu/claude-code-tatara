---
title: cache key on create
status: todo
repo: agents-orchestrator
value: "every cached session gets the user's key or a stable preset-derived one, and clients see whether caching is available"
files: [src/agents_orchestrator/spec.py, src/agents_orchestrator/api/sessions.py, src/agents_orchestrator/api/schemas.py, openapi.json, tests/test_api_cache.py]
verify: "uv run pytest -q tests/test_api_cache.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [cache-config]
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

# cache key on create

## Requirement

Resolve the cache key at session create and expose cache availability (design D7, D8). Runs after the epic orchestrator-rename-sessions lands. Paths are in code/agents-orchestrator under the post-rename names (design Constraints: if that epic chose other module names, the same symbols apply and the orchestrator amends this file list first).

- `src/agents_orchestrator/spec.py`: `default_cache_key(preset_id: UUID) -> str` = `"preset-" + sha256(b"workspace-cache:" + preset_id.bytes).hexdigest()[:16]` (pseudorandom, derived from the immutable preset id, so a preset rename keeps the cache and a copy gets a new one).
- `src/agents_orchestrator/api/sessions.py`: `POST /api/v1/sessions` with `preset_id`: when the snapshotted spec has `cache` with `key` None, set `key` to `default_cache_key(preset.id)` before the insert, so the stored session spec always carries the key. With a raw `spec`, a `cache` without `key` is a 422 `invalid_request` "cache.key is required without a preset". Preset POST and PUT store `cache` sparse, without resolving the key.
- `GET /api/v1/meta` gains `cache: {available: settings.cache_available, max_bytes: settings.cache_max_bytes}` (`api/schemas.py`: `MetaCache`, `Meta.cache`; contract orch-meta-cache).
- `openapi.json` regenerated with `uv run python -m agents_orchestrator.api.openapi > openapi.json` (the command `tests/test_readme_api.py::test_openapi_json_matches_app` names).

## Acceptance conditions

- AC1: default_cache_key is stable for one preset id, differs between ids and matches the key pattern [evidence: test:tests/test_api_cache.py::test_default_cache_key]
- AC2: a session from a preset with a keyless cache stores the derived key in its spec [evidence: test:tests/test_api_cache.py::test_create_from_preset_derives_key]
- AC3: a session from a preset with a key keeps that key [evidence: test:tests/test_api_cache.py::test_create_from_preset_keeps_user_key]
- AC4: a raw spec with a keyless cache is a 422 naming cache.key [evidence: test:tests/test_api_cache.py::test_raw_spec_needs_key]
- AC5: a preset stores its cache sparse and unresolved [evidence: test:tests/test_api_cache.py::test_preset_cache_stored_sparse]
- AC6: meta reports cache availability and max bytes [evidence: test:tests/test_api_cache.py::test_meta_cache]
- AC7: the committed openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- AC8: lint and format pass [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_orchestrator/spec.py`
- `src/agents_orchestrator/api/sessions.py`
- `src/agents_orchestrator/api/schemas.py`
- `openapi.json`
- `tests/test_api_cache.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
