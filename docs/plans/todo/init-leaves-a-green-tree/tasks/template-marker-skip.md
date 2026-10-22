---
title: template marker skip
status: todo
repo: workbench
value: template-only self-tests stop failing in every initialised workbench
files: [pyproject.toml, scripts/tests/conftest.py, scripts/init_engine/project_files.py, scripts/init_engine/cli.py, scripts/init_engine/update.py, scripts/doctor.py, scripts/tests/test_root_config.py, scripts/tests/init_engine/test_project_files.py]
verify: "pytest scripts/tests/test_root_config.py scripts/tests/init_engine/test_project_files.py scripts/tests/test_doctor.py -q && mise run lint:python"
depends_on: [init-writes-allow-entries, secrets-skip-gitlinks, personal-allow-file, license-every-plugin]
owns: [is-initialised]
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

# template marker skip

## Requirement

Register a `template` marker in pyproject.toml. scripts/tests/conftest.py skips marked tests when the workbench root is initialised, and is a no-op in the uninitialised template (the marker never skips anything there). One helper is_initialised(root) in scripts/init_engine/project_files.py (AGENTS.md has no uninitialised block) owns the check; cli.py, update.py and doctor.py call it instead of their copies. Every test that asserts the uninitialised template state, or whose fixture copies the live root's template files, gets the marker (list in discovery brief section 5: the e2e instantiate/template_update tests, the listed finalize, project_files, refresh, update, update_conflicts, update_unrelated, agents_md, check_personal, lint_personal_task, marketplace, root_stubs, root_tooling and secret_scanning tests). Tests that pass on an initialised tree stay unmarked. A test runs the suite against an initialised copy and asserts no failures; pack/plugin test roots get the same hook only if still red after license-every-plugin.

## Acceptance conditions

- AC1: is_initialised is true for an initialised AGENTS.md and false for the template one [evidence: test:scripts/tests/init_engine/test_project_files.py::test_is_initialised]
- AC2: the template marker is registered and skips nothing in the uninitialised template [evidence: test:scripts/tests/test_root_config.py::test_template_marker_registered_and_noop_in_template]
- AC3: the scripts suite run against an initialised copy has no failures [evidence: test:scripts/tests/e2e/test_instantiate.py::test_suite_green_on_initialised_copy]
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
