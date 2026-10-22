---
title: license every plugin
status: todo
repo: workbench
value: "the chosen holder appears in every LICENSE, not only the root"
files: [scripts/init_engine/finalize.py, scripts/tests/init_engine/test_finalize.py, plugins/workbench-secrets/LICENSE, plugins/workbench/skills/init/SKILL.md]
verify: "pytest scripts/tests/init_engine/test_finalize.py scripts/tests/test_root_stubs.py -q && mise run lint:personal"
depends_on: []
owns: []
uses: []
model: ""
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

# license every plugin

## Requirement

finalize.license_file rewrites the Copyright line of the root LICENSE and of every plugins/*/LICENSE with the same holder (explicit --license-holder, else default_holder, the git author). --license none removes only the root LICENSE; plugin licenses stay and are rewritten. plugins/workbench-secrets/LICENSE in the template is aligned with the root holder. test_license_options is updated; tests pin every plugins/*/LICENSE == root after init and the default-holder fallback. The init SKILL.md says the holder defaults to the git author.

## Acceptance conditions

- AC1: after init with --license-holder every plugins/*/LICENSE Copyright line equals the root one [evidence: test:scripts/tests/init_engine/test_finalize.py::test_license_holder_in_every_plugin]
- AC2: without --license-holder the git author is used in all licenses [evidence: test:scripts/tests/init_engine/test_finalize.py::test_license_default_holder_fallback]
- AC3: --license none removes only the root LICENSE [evidence: test:scripts/tests/init_engine/test_finalize.py::test_license_options]
- AC4: the pack LICENSE test passes [evidence: test:plugins/workbench-infra/tests/test_pack_infra.py::test_license_and_readme]
- AC5: init SKILL.md states the git-author default [evidence: judgement:]

## Files

- `scripts/init_engine/finalize.py`
- `scripts/tests/init_engine/test_finalize.py`
- `plugins/workbench-secrets/LICENSE`
- `plugins/workbench/skills/init/SKILL.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
