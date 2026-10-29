---
title: orch cache name on create
status: todo
repo: agents-orchestrator
value: "Sessions get their own rendered cache name instead of the preset-derived key, and presets validate their template on save"
files: [src/agents_orchestrator/spec.py, src/agents_orchestrator/api/sessions.py, src/agents_orchestrator/api/presets.py, src/agents_orchestrator/api/schemas.py, openapi.json, README.md, MEMORY.md, tests/test_api_cache.py]
verify: "uv run --frozen pytest -q -p no:cacheprovider tests/test_api_cache.py tests/test_readme_api.py tests/test_cache_naming.py && mise run lint"
depends_on: [orch-cache-name-template]
model: opus
review: ""
verified_head: ""
points: 8
expected_minutes: 16
expected_tokens: 3197775
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch cache name on create

## Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I also want to decouple s3 cache from preset. There must be a way to define S3 backup name with jonja2 template with default as preset-sessionname. This must also copy caches of existing sessions, so after rotation everything will work properly." (jonja2 = Jinja2)

Leader constraint: the migration copies only, never moves or deletes S3 objects.

This task delivers design D1, D4, D6 and D13 in agents-orchestrator.

- `spec.cache.key` is a cache name template (Jinja2, `cache.naming`): `WorkspaceCache.key` accepts any string that passes `naming.check_template` (at most 256 characters). A literal key such as `mine` keeps working and names one shared cache, as today.
- Session create from a preset (`api/sessions.py:_create_from_preset`) renders the preset's `spec.cache.key`, or `naming.DEFAULT_CACHE_NAME_TEMPLATE` when it is empty, with `preset` = `slugify(preset.name)`, `preset_id`, `session` = the session's slug (the caller's, or each generated slug attempt) and `created_by` = the calling service or `""`, and stores the rendered name as the session's `spec.cache.key`. A render error answers 422 `invalid_request` naming the preset.
- A raw-spec session (`POST /api/v1/sessions` with `spec`) still needs `cache.key` (422 without it, as today). It is rendered with `session` and `created_by` only, so a template that refers to `preset` or `preset_id` answers 422.
- Preset create and replace (`api/presets.py:_validated`) answer 422 `invalid_request` when `naming.check_template` refuses the key or a trial render fails with this preset's name, a sample preset id, a 40-character sample slug and an empty `created_by`. The preset stores the template as sent.
- Removed with no replacement (no backward compatibility): `spec.default_cache_key`, `spec.CACHE_KEY_RESERVED_PREFIX`, `spec.check_caller_cache_key`, `check_spec`'s `derived_cache_key` parameter and `api/presets.py:_without_derived_key`. A preset copy keeps the source's `cache` as it is.
- `GET /api/v1/meta` `cache` gains `default_name_template` (the text of `DEFAULT_CACHE_NAME_TEMPLATE`). `openapi.json` is regenerated (`uv run python -m agents_orchestrator.api.openapi > openapi.json`).
- README `### Spec and key` describes the cache name template, its variables, the default, the 256-character and key-rule limits and the render points. MEMORY.md records the decisions (dated, with the why).

Tests no longer accurate, removed or rewritten in tests/test_api_cache.py, because the user asked to decouple the cache from the preset: `test_default_cache_key` and `test_default_cache_key_is_pinned` (the preset-id-derived key no longer exists), `test_create_from_preset_derives_key` (the default is now the rendered `<preset>-<session>`), `test_preset_prefix_reserved` and `test_copy_drops_source_derived_key` (the reserved prefix and the derived key are removed, design D6), `test_meta_cache` (its exact dict gains `default_name_template`).

## Acceptance conditions

- AC1: two sessions created from a keyless cache preset named `My Repo` with slugs `alpha` and `beta` get cache keys `my-repo-alpha` and `my-repo-beta` [evidence: test:tests/test_api_cache.py::test_create_from_preset_renders_default_name]
- AC2: a session created from a preset without a slug gets the default rendered with its generated slug [evidence: test:tests/test_api_cache.py::test_generated_slug_renders_into_name]
- AC3: a preset template `{{ preset }}-shared` gives every session of that preset the same key, and a literal preset key `mine` is kept as is [evidence: test:tests/test_api_cache.py::test_preset_template_and_literal_key]
- AC4: preset create and replace answer 422 for a template with an unknown variable, a for loop, a syntax error, or one whose trial render with a 40-character slug breaks the key rule [evidence: test:tests/test_api_cache.py::test_preset_template_validated_on_save]
- AC5: a raw-spec session renders `{{ session }}-x` into `<slug>-x`, answers 422 for a template using `preset`, and still answers 422 without `cache.key` [evidence: test:tests/test_api_cache.py::test_raw_spec_key_template]
- AC6: keys starting with `preset-` are accepted like any other key on presets and raw specs, and a preset copy keeps the source cache unchanged [evidence: test:tests/test_api_cache.py::test_no_reserved_prefix_and_copy_keeps_cache]
- AC7: default_cache_key, CACHE_KEY_RESERVED_PREFIX, check_caller_cache_key, derived_cache_key and _without_derived_key are gone from src [evidence: command:! grep -rnE "default_cache_key|CACHE_KEY_RESERVED_PREFIX|check_caller_cache_key|derived_cache_key|_without_derived_key" src]
- AC8: GET /api/v1/meta cache carries available, max_bytes and default_name_template equal to naming.DEFAULT_CACHE_NAME_TEMPLATE [evidence: test:tests/test_api_cache.py::test_meta_cache]
- AC9: the committed openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- AC10: README and MEMORY.md describe the cache name template [evidence: command:grep -qi "cache name template" README.md && grep -qi "cache name template" MEMORY.md]
- AC11: lint passes [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/spec.py`
- `src/agents_orchestrator/api/sessions.py`
- `src/agents_orchestrator/api/presets.py`
- `src/agents_orchestrator/api/schemas.py`
- `openapi.json`
- `README.md`
- `MEMORY.md`
- `tests/test_api_cache.py`

## Interfaces

- `spec.WorkspaceCache.key: str | None` validated by `naming.check_template` (was `CACHE_KEY_RE`); `spec.CACHE_KEY_RE` stays the rule for a rendered name.
- `api/sessions.py:check_spec(spec, settings, stored=None)` (no `derived_cache_key`); `_create_from_preset` renders inside the slug loop; `create_session` renders a raw-spec key.
- `api/presets.py:_validated` trial-renders; `copy_preset` copies `source.spec` unchanged.
- `api/schemas.py:MetaCache` gains `default_name_template: str`; `openapi.json` regenerated.
- Contract change (docs/plans/contracts.json, updated by the orchestrator, not this task): `orch-session-spec-cache` key is a template on presets and raw specs and the rendered name on stored sessions; `orch-meta-cache` gains `default_name_template`.

## Expected outcome

`POST /api/v1/sessions {"preset_id": <My Repo>, "slug": "alpha"}` answers a session whose `spec.cache.key` is `my-repo-alpha`; a preset with an unsafe template is refused with 422; `/meta` shows the default template; nothing in `src` mentions the preset-derived key.

## Steps

- Read spec.py (WorkspaceCache, default_cache_key, check_caller_cache_key), api/sessions.py, api/presets.py, api/schemas.py (MetaCache), README.md `## Workspace cache`, tests/test_api_cache.py and tests/test_api_sessions.py helpers (`client_for`, `make_settings`, `assert_error`) in one pass.
- Red: rewrite tests/test_api_cache.py: drop the five tests named in the Requirement, add the tests named in the acceptance conditions, extend `test_meta_cache`; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_api_cache.py`; DB tests error locally without Docker, so confirm red on CI or with a local Postgres; the non-DB tests must fail on the missing behaviour.
- Green: change spec.py, api/sessions.py, api/presets.py, api/schemas.py; regenerate `uv run python -m agents_orchestrator.api.openapi > openapi.json`; rerun the verify; expect the non-DB tests and `tests/test_readme_api.py::test_openapi_json_matches_app` passed.
- Update README `### Spec and key` and add the MEMORY.md entry; `mise run lint`; expect exit 0.

## Notes

- Render in `_create_from_preset` per slug attempt (`generated_slug` changes each retry, `api/sessions.py` around l.288-293); the session id is not available there and is not a variable.
- `created_by` is `calling_service(request)` or `""`; `preset` is `slugify(preset.name)` (preset names allow uppercase, spaces, `.`, `_`, 40 characters, `db/presets.py:19-20`).
- Trial render at preset save uses a 40-character sample slug (worst case) so a template that can break the key rule is caught at save, not at session create.
- Security: dropping the reserved prefix is design D6 (open question Q6): any API caller can already create a session from any preset with any free slug and so reach that cache; the prefix protected nothing once names are `<preset>-<session>`.
- Do not touch tests/test_api_create_from_preset.py or tests/test_api_presets.py unless a test there fails because of the removed derived key; then name it as no longer accurate in the report.
- Tree state (pictures baseline, 2026-10-28): `mise run lint` green; the full suite is red-env only. Tests that use the `pool`/`dsn` fixtures need Postgres through testcontainers, and agent pods have no Docker, so they error locally (`DockerException`) and run in CI on the PR: the reviewer reads the CI job for them and quotes its summary line. `tests/test_reconciler.py::test_lightkube_default_client_uses_env_config` fails in-cluster for an unrelated reason (KUBERNETES_SERVICE_HOST).
- If a verify run fails, save the failing test name and the output tail before any rerun (retro, markdown-rendering-in-chat).
- Per-task security check (retro, recurring): user input reaching S3 keys or a template engine is the high-risk surface here; check size bounds, refusal paths and that no credential or presigned query reaches a log, a status reason or an error message.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
