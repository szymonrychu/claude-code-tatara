---
title: web preset cache name field
status: todo
repo: agents-web
value: "Users edit a preset's cache name template in the web form, with the orchestrator default shown"
files: [src/sessions/sessionSpecForm.ts, src/presets/PresetForm.tsx, src/presets/PresetForm.test.tsx, src/api/schema.d.ts, openapi/orchestrator.json, openapi/orchestrator.source]
verify: "npm ci --no-audit --no-fund && npx vitest run src/presets/PresetForm.test.tsx && npm run check:api && npm run lint"
depends_on: [orch-cache-name-on-create]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 10
expected_tokens: 1875101
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web preset cache name field

## Requirement

User request (2026-10-29 04:52Z, mx-34 #343), verbatim: "I also want to decouple s3 cache from preset. There must be a way to define S3 backup name with jonja2 template with default as preset-sessionname. This must also copy caches of existing sessions, so after rotation everything will work properly." (jonja2 = Jinja2)

Leader constraint: the migration copies only, never moves or deletes S3 objects.

This task delivers design D12 (preset side) in agents-web.

- The preset form's cache field is labelled `Cache name template` and takes a Jinja2 template. Its placeholder is the orchestrator's default from `GET /api/v1/meta` `cache.default_name_template`; its helper text names the variables `preset`, `preset_id`, `session` and `created_by` and says that sessions whose names render the same share one cache (last save wins). Empty sends no `key` (the orchestrator renders the default).
- Client checks: at most 256 characters, nothing else; the orchestrator validates the template and its 422 message is shown under the field, as today. Removed: the client cache key regex (`CACHE_KEY`), the reserved `preset-` rule (`CACHE_KEY_RESERVED_PREFIX`, `cacheKeyError`'s stored-key parameter, `validate`'s `storedCacheKey`) and `PresetForm.tsx`'s copy rule that drops a `preset-` key: a copy keeps the source cache as it is.
- `openapi/orchestrator.json`, `openapi/orchestrator.source` and `src/api/schema.d.ts` are synced to the agents-orchestrator commit that adds `cache.default_name_template` (`npm run sync:api -- orchestrator`), and `npm run check:api` passes.

Tests no longer accurate, rewritten in src/presets/PresetForm.test.tsx because the field now takes a template under a new label and the reserved prefix is removed (design D6, D12): `saves an empty cache when enabled without a key`, `saves the cache key and excludes`, `rejects an invalid cache key`, `shows the server message for a reserved cache key`, `disables the cache section when the orchestrator has no cache`, `loads a stored cache`, `a copy drops a preset-derived cache key`.

## Acceptance conditions

- AC1: the field is labelled Cache name template, shows the meta default_name_template as its placeholder, and an empty field saves `cache: {}` [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "cache name template defaults to the orchestrator default"]
- AC2: a template such as `{{ preset }}-shared` is saved verbatim as cache.key [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "saves a cache name template verbatim"]
- AC3: more than 256 characters blocks submit, while template syntax and names starting with `preset-` are not refused client side [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "cache name template client checks"]
- AC4: the orchestrator's 422 message for an invalid template shows under the field [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "shows the server message for an invalid cache name template"]
- AC5: a copy keeps the source cache, including a key starting with `preset-` [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t "a copy keeps the source cache"]
- AC6: the reserved prefix rule is gone from src [evidence: command:! grep -rnE "CACHE_KEY_RESERVED_PREFIX|reserved for preset-derived" src]
- AC7: the vendored orchestrator schema is in sync [evidence: command:npm run check:api]
- AC8: the whole PresetForm suite and lint pass [evidence: command:npx vitest run src/presets/PresetForm.test.tsx && npm run lint]

## Files

- `src/sessions/sessionSpecForm.ts`
- `src/presets/PresetForm.tsx`
- `src/presets/PresetForm.test.tsx`
- `src/api/schema.d.ts`
- `openapi/orchestrator.json`
- `openapi/orchestrator.source`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
