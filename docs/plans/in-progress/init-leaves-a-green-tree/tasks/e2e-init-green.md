---
title: e2e init green
status: in-progress
repo: workbench
value: proof that a fresh workbench starts green
files: [scripts/tests/e2e/test_instantiate.py, scripts/tests/e2e/helpers.py, scripts/tests/e2e/conftest.py]
verify: mise exec -- pytest scripts/tests/e2e/test_instantiate.py -q
depends_on: [personal-allow-file, init-writes-allow-entries, secrets-skip-gitlinks, license-every-plugin, template-marker-skip, skill-text-local-bare-move]
owns: []
uses: [personal-allow-local, is-initialised]
model: ""
estimate: 5
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

# e2e init green

## Requirement

e2e tests initialise a template copy (new and adopt) whose project name and adopted repo owner are terms whose digests are in that copy's denylist, adopt a component whose checkout holds a secret-shaped fixture built at run time, then add a second component, and assert `mise run lint` and `mise run test` exit 0 and `git status` is clean after each step. Uses the personal-allow.local.json writer and reader, the gitlink-skipping secrets task, the all-LICENSE holder and is_initialised/template marker from the other tasks.

## Acceptance conditions

- AC1: new init leaves lint and test green and a clean status [evidence: test:scripts/tests/e2e/test_instantiate.py::test_new_init_leaves_green_tree]
- AC2: adopt of a repo with a colliding owner and secret-shaped fixture leaves lint and test green [evidence: test:scripts/tests/e2e/test_instantiate.py::test_adopt_leaves_green_tree]
- AC3: a second component add keeps lint and test green [evidence: test:scripts/tests/e2e/test_instantiate.py::test_second_component_add_stays_green]
- AC4: the scripts suite run against an initialised copy has no failures [evidence: test:scripts/tests/e2e/test_instantiate.py::test_suite_green_on_initialised_copy]

## Files

- `scripts/tests/e2e/test_instantiate.py`
- `scripts/tests/e2e/helpers.py`
- `scripts/tests/e2e/conftest.py`

## Interfaces

none

## Expected outcome

New init, adopt with a colliding owner and secret fixture, and a second component add each leave lint and test green and git status clean.

## Steps

- Write the failing e2e tests in test_instantiate.py first (red if any other task is missing).
- Fix any remaining gap they expose in the owning task's files; run green.

## Notes

Design D7. Build the secret-shaped fixture at run time; pick a project name and owner whose digests are in the copy's denylist.
