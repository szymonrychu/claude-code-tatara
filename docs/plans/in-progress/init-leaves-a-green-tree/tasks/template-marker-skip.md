---
title: template marker skip
status: escalated
repo: workbench
value: template-only self-tests stop failing in every initialised workbench
files: [pyproject.toml, scripts/tests/conftest.py, scripts/init_engine/project_files.py, scripts/init_engine/cli.py, scripts/init_engine/update.py, scripts/doctor.py, scripts/tests/test_root_config.py, scripts/tests/init_engine/test_project_files.py]
verify: "mise exec -- pytest scripts/tests/test_root_config.py scripts/tests/init_engine/test_project_files.py scripts/tests/test_doctor.py -q && mise run lint:root"
depends_on: [init-writes-allow-entries, secrets-skip-gitlinks, personal-allow-file, license-every-plugin, skill-text-local-bare-move]
owns: [is-initialised]
uses: []
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/init-leaves-a-green-tree-template-marker-skip
branch: init-leaves-a-green-tree-template-marker-skip
verified_head: 5619cda9d76f90d8717064e2dddaac772bfe5bdd
run: init-leaves-a-green-tree
provides: [is-initialised]
acs_for_audit: [AC4]
process_gaps: []
---

# template marker skip

## Requirement

Register a `template` marker in pyproject.toml. scripts/tests/conftest.py skips marked tests when the workbench root is initialised, and is a no-op in the uninitialised template (the marker never skips anything there). One helper is_initialised(root) in scripts/init_engine/project_files.py (AGENTS.md has no uninitialised block) owns the check; cli.py, update.py and doctor.py call it instead of their copies. Every test that asserts the uninitialised template state, or whose fixture copies the live root's template files, gets the marker (list in discovery brief section 5: the e2e instantiate/template_update tests, the listed finalize, project_files, refresh, update, update_conflicts, update_unrelated, agents_md, check_personal, lint_personal_task, marketplace, root_stubs, root_tooling and secret_scanning tests). Tests that pass on an initialised tree stay unmarked. The whole-suite run on an initialised copy is e2e-init-green AC4. scripts/doctor.py is a standalone script: load project_files through the sibling loader pattern (finalize.collision_override) or sys.path, whichever doctor already supports. Pack/plugin test roots get the same hook only if still red after license-every-plugin.

## Acceptance conditions

- AC1: is_initialised is true for an initialised AGENTS.md and false for the template one [evidence: test:scripts/tests/init_engine/test_project_files.py::test_is_initialised]
- AC2: the template marker is registered and skips nothing in the uninitialised template [evidence: test:scripts/tests/test_root_config.py::test_template_marker_registered_and_noop_in_template]
- AC3: a TEMPLATE_ONLY id that names no collected test fails collection, so the list cannot rot [evidence: test:scripts/tests/test_root_config.py::test_template_only_ids_all_exist]
- AC4: cli, update and doctor use the shared helper [evidence: symbol:scripts/init_engine/project_files.py::is_initialised]

## Files

- `pyproject.toml`
- `scripts/tests/conftest.py`
- `scripts/init_engine/project_files.py`
- `scripts/init_engine/cli.py`
- `scripts/init_engine/update.py`
- `scripts/doctor.py`
- `scripts/tests/test_root_config.py`
- `scripts/tests/init_engine/test_project_files.py`

## Interfaces

project_files.is_initialised(root) -> bool; pytest marker `template`; scripts/tests/conftest.py collection hook.

## Expected outcome

Template-only tests skip in an initialised workbench, run in the template; the suite is green on an initialised copy.

## Steps

- Write failing tests for is_initialised, marker registration and the initialised-copy suite run; run red.
- Add the helper, replace the copies in cli.py, update.py, doctor.py, register the marker, add the conftest hook, mark the template-only tests; run green, then `mise run lint:root`.

## Notes

Design D5. The marker is applied centrally: conftest.py holds the TEMPLATE_ONLY list of test node ids and adds the template marker to them at collection, so no other test file is edited. Test list in the discovery brief section 5. Do not touch owned.INSTANCE_OWNED. The marker must be a no-op in the template.
