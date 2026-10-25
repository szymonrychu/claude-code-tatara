---
title: cache key reserved prefix
status: todo
repo: agents-orchestrator
value: "no caller can read or poison another preset's workspace cache"
files: [src/agents_orchestrator/spec.py, src/agents_orchestrator/api/sessions.py, src/agents_orchestrator/api/presets.py, tests/test_api_cache.py, README.md]
verify: "uv run pytest -q -o addopts='-m \"not integration and not e2e\"' tests/test_api_cache.py && uv run ruff check ."
depends_on: []
model: ""
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 531208
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# cache key reserved prefix

## Requirement

Epic security review 2026-10-26 (medium): without a preset, spec.cache.key is caller-supplied and only regex-checked, so an SSO user can set key to another preset's derived key (visible in that preset's session status) and read that preset's cached workspace on restore or overwrite it on save, planting hooks (.claude/settings.json, .git/hooks) that the victim preset's next session runs. Fix in agents-orchestrator: the `preset-` prefix is reserved for derived keys. A caller-supplied cache.key (raw spec, preset create/update, session create) that starts with `preset-` is rejected with 422 invalid_request "cache.key prefix preset- is reserved for preset-derived keys"; a stored spec whose key equals default_cache_key(its preset) stays valid. User slugs outside the prefix keep working (user requirement: optional user-provided slug). Document it in the README Workspace cache section.

## Acceptance conditions

- AC1: a caller-supplied cache.key starting with preset- is rejected with 422 on session create, raw spec and preset create/update [evidence: test:tests/test_api_cache.py::test_preset_prefix_reserved]
- AC2: the preset-derived key still resolves and other user slugs still work [evidence: test:tests/test_api_cache.py::test_create_from_preset_derives_key]
- AC3: the suite and lint pass [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/spec.py`
- `src/agents_orchestrator/api/sessions.py`
- `src/agents_orchestrator/api/presets.py`
- `tests/test_api_cache.py`
- `README.md`

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
