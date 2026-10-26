---
title: restore resets workdir on unreadable archive
status: in-progress
repo: agents-orchestrator
value: A corrupt cache key repairs itself instead of blocking its key forever
files: [src/agents_orchestrator/cache/transfer.py, src/agents_orchestrator/reconciler/cache.py, tests/test_cache_cli.py, tests/test_cache_save.py, README.md, MEMORY.md]
verify: mise run test
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 999852
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# restore resets workdir on unreadable archive

## Requirement

User decision 2026-10-26 (open question from workspace-s3-cache): "cache repair- start empty". A cache key whose archive cannot be read must repair itself: the session starts with an empty workdir and the discard save overwrites the bad archive.

1. `src/agents_orchestrator/cache/transfer.py` `restore`: when `archive.unpack` raises `archive.ExtractError` (tar/zstd decode error, refused member, expansion past the cap: the archive itself is unreadable or untrusted), remove every entry inside `CACHE_DIR` (keep the directory itself, do not follow symlinks), then emit the new outcome state `reset` with `reason="extract_failed: <error>"` and exit `EXIT_OK`. If removing the entries fails, emit `failed` `extract_failed: <error>; reset failed: <error>` and exit `EXIT_FAILED` as today.
2. Any other failure after body bytes were delivered (transport drop, OSError such as ENOSPC) stays `failed` `extract_failed` with no wipe, and the save stays skipped: the stored archive may be good.
3. `src/agents_orchestrator/reconciler/cache.py`: add `reset` to `SAVE_OK_RESTORE_STATES`, so the save after a reset runs and overwrites the bad object. Update the comment above it. A restore state `reset` must not count as failed anywhere it is reported (status, events, API state values); check every consumer of the restore state.
4. Docs: README cache state table and the save paragraph (README.md near line 395-397) describe `reset`; replace "a corrupt archive is fixed by deleting the object". Add a dated MEMORY.md line amending D11 with the why.
5. No change to agents-web unless it hard-codes the set of cache states; if it does, report it as a question instead of editing (other repo).

## Acceptance conditions

- AC1: A restore of a corrupt archive (bad zstd bytes) over a workdir with pre-existing files leaves the workdir existing and empty, prints state `reset` with reason starting `extract_failed: `, and exits 0 [evidence: test:tests/test_cache_cli.py]
- AC2: A restore whose stream drops after some bytes (non-ExtractError) still prints `failed` `extract_failed` and leaves the workdir untouched [evidence: test:tests/test_cache_cli.py]
- AC3: A wipe that fails yields `failed` with `reset failed` in the reason and a non-zero exit [evidence: test:tests/test_cache_cli.py]
- AC4: A save after a restore in state `reset` creates the save Job; `failed` restores still skip [evidence: test:tests/test_cache_save.py]
- AC5: README and MEMORY.md describe `reset` and amend D11 [evidence: doc-section:README.md]

## Files

- `src/agents_orchestrator/cache/transfer.py`
- `src/agents_orchestrator/reconciler/cache.py`
- `tests/test_cache_cli.py`
- `tests/test_cache_save.py`
- `README.md`
- `MEMORY.md`

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
- DB tests: Docker disk is full, so testcontainers fail; use the shared local Postgres at postgresql://test@127.0.0.1:55433/postgres (trust auth) through a temporary, uncommitted fixture override with a fresh template DB name (for example `csr_tpl_1`). Run the full suite through plugins/workbench/skills/worktree-merge/scripts/suite-lock.sh in the workbench root.
- D11 in MEMORY.md is the save allow-list decision this amends; keep the allow-list shape (fail safe), only add `reset`.
