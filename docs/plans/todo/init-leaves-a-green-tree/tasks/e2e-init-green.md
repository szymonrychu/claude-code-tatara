---
title: e2e init green
status: todo
repo: workbench
value: proof that a fresh workbench starts green
files: [scripts/tests/e2e/test_instantiate.py, scripts/tests/e2e/helpers.py, scripts/tests/e2e/conftest.py]
verify: pytest scripts/tests/e2e/test_instantiate.py -q
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

## Files

- `scripts/tests/e2e/test_instantiate.py`
- `scripts/tests/e2e/helpers.py`
- `scripts/tests/e2e/conftest.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
