---
title: presets review fixes
status: todo
repo: agent-orchestrator
value: "the migration is proven on a live database, early form edits survive, and the writers table is accurate"
files: [tests/test_migrations.py, frontend/src/presets/PresetForm.tsx, frontend/src/presets/PresetForm.test.tsx, README.md]
verify: "uv run pytest -q -p no:cacheprovider tests/test_migrations.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check . && mise x node@24.20.0 -- npm --prefix frontend ci && mise x node@24.20.0 -- npm --prefix frontend test -- src/presets && mise x node@24.20.0 -- npm --prefix frontend run lint && mise x node@24.20.0 -- npm --prefix frontend run build"
depends_on: []
owns: []
uses: []
model: sonnet
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# presets review fixes

## Requirement

Close the cluster-presets epic review findings (2026-10-24).

1. Upgrade path test: tests/test_migrations.py gains a test that applies only 0001 (run_migrations against a directory holding 0001 alone), inserts a cluster row, then applies the full migrations directory, and asserts the existing cluster keeps its spec, has preset_id and preset_name null, and the Default preset exists.
2. PresetForm loses early edits: frontend/src/presets/PresetForm.tsx rebuilds the form when /meta resolves and drops what the user typed before. Either keep the fields disabled until /meta has loaded or merge the meta-derived defaults under the user's already-set keys; edits made before /meta arrives must never be lost.
3. README writers table (README.md Data model single-writer rows): note that clusters.preset_id is also set to null by the ON DELETE SET NULL cascade when the api deletes a preset (an api-originated write, design D1).

## Acceptance conditions

- AC1: 0002 applied on top of a 0001 database with a cluster keeps the cluster and leaves preset_id and preset_name null [evidence: test:tests/test_migrations.py::test_presets_migration_on_existing_clusters]
- AC2: a field edited before /meta resolves keeps its value after /meta arrives [evidence: command:mise x node@24.20.0 -- npm --prefix frontend test -- src/presets/PresetForm.test.tsx -t "keeps edits made before meta loads"]
- AC3: the README single-writer rows mention the preset delete cascade on clusters.preset_id [evidence: doc-section:README.md#data-model]

## Files

- `tests/test_migrations.py`
- `frontend/src/presets/PresetForm.tsx`
- `frontend/src/presets/PresetForm.test.tsx`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
