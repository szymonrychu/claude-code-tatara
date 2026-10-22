---
title: refresh writes allow entries
status: in-progress
repo: workbench
value: an already-initialised workbench can take the template update without a red personal lint
files: [scripts/init_engine/cli.py, scripts/tests/init_engine/test_refresh.py, scripts/tests/init_engine/test_update.py]
verify: "mise exec -- pytest scripts/tests/init_engine/test_refresh.py scripts/tests/init_engine/test_update.py -q && mise run lint:personal"
depends_on: [init-writes-allow-entries, template-marker-skip, license-every-plugin, personal-allow-file, e2e-init-green]
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/init-leaves-a-green-tree-refresh-writes-allow-entries
branch: init-leaves-a-green-tree-refresh-writes-allow-entries
verified_head: ""
run: ""
provides: []
---

# refresh writes allow entries

## Requirement

`init:refresh` (scripts/init_engine/cli.py cmd_refresh, which template-update also runs after its merge at update.py:261) calls finalize.allow_vocabulary, so a workbench initialised before the allow file existed gains its project-vocabulary allow entries on refresh and on template-update. Found updating claude-code-tatara (initialised with the pre-fix template): init:update refused because lint:personal still failed on the project name in AGENTS.md and docs/architecture.md. The refresh writes and stages scripts/personal-allow.local.json in its own commit; literal pattern hits stay un-allowed; an already-correct allow file is left byte-identical.

## Acceptance conditions

- AC1: refresh on an initialised workbench whose project name digest is denylisted writes the allow entry and lint:personal passes [evidence: test:scripts/tests/init_engine/test_refresh.py::test_refresh_allows_project_vocabulary]
- AC2: template-update of such a workbench (initialised without an allow file) completes and lint:personal passes [evidence: test:scripts/tests/init_engine/test_update.py::test_update_backfills_allow_file]
- AC3: refresh with a correct allow file leaves it byte-identical [evidence: test:scripts/tests/init_engine/test_refresh.py::test_refresh_allow_file_idempotent]

## Files

- `scripts/init_engine/cli.py`
- `scripts/tests/init_engine/test_refresh.py`
- `scripts/tests/init_engine/test_update.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

Refresh and template-update leave lint:personal green on a workbench initialised before the allow file existed.

What is true and observable when the task is done.

## Steps

- Write the three failing tests (refresh allows vocabulary, update backfills, idempotent); run red.
- Call finalize.allow_vocabulary from cmd_refresh and stage the allow file in its commit; run green, then mise run lint:personal.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
