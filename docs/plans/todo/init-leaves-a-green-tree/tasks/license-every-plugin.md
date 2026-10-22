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

finalize.license_file(root, opts, first): rewrites root LICENSE and every plugins/*/LICENSE; default_holder(root) is the fallback.

## Expected outcome

Every LICENSE Copyright line carries the same holder after init; --license none removes only the root file.

## Steps

- Write failing tests (every plugin LICENSE equals root; default-holder fallback) and update test_license_options; run red.
- Extend license_file in scripts/init_engine/finalize.py, align plugins/workbench-secrets/LICENSE, edit init SKILL.md; run green.

## Notes

Design D4. test_pack_infra.py::test_license_and_readme and test_root_stubs.py::test_license_mit_identical must stay green in the template.
