---
title: cache save allowlist
status: todo
repo: agents-orchestrator
value: a failed restore can never overwrite a good cache archive
files: [src/agents_orchestrator/reconciler/cache.py, tests/test_cache_save.py, README.md, MEMORY.md]
verify: "uv run pytest -q -o addopts='-m \"not integration and not e2e\"' tests/test_cache_save.py && uv run ruff check ."
depends_on: [cache-key-reserved-prefix]
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

# cache save allowlist

## Requirement

Epic whole-diff review 2026-10-26 (medium, .scratchpad/cache-epic-review.md): the save skip rule in reconciler/cache.py (SAVE_SKIP_RESTORE_REASONS) is a deny-list that omits restore failures able to leave a partial workdir: `exit <code>` (an OOM kill mid-extract), `bad_output`, `no_cache_key`, and `extract_failed` also still saves. A save then replaces a good archive with a partial tree, the design's anti-goal. Orchestrator ruling: invert to an allow-list. A save Job runs only when the session's restore outcome is a success: restored, or the archive did not exist yet (a cache miss on first use). It is skipped on every other restore state or reason, present or future, and on the cache being unavailable. Keep the skip recorded with its reason as now. Update the README Workspace cache section and the MEMORY.md D11 line to the allow-list rule.

Also check how a missing archive is reported. A presigned GET for a missing key returns 404 when the bucket owner can list the bucket, else 403. Make sure the restore maps 404 to the cache-miss outcome. If the CLI cannot tell a 403-missing from a 403-denied, record that in the README; the live smoke checks it.

## Acceptance conditions

- AC1: a save runs only after a successful restore or a cache miss, and is skipped for every other restore outcome [evidence: test:tests/test_cache_save.py::test_save_only_after_successful_restore]
- AC2: a restore of a missing archive is a cache miss and is followed by a save [evidence: test:tests/test_cache_save.py::test_cache_miss_then_save]
- AC3: the suite and lint pass [evidence: command:mise run lint]

## Files

- `src/agents_orchestrator/reconciler/cache.py`
- `tests/test_cache_save.py`
- `README.md`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
