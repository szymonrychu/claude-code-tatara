---
title: ci workflow test pins e2e job
status: in-progress
repo: workbench
value: "the template's full suite is green again after the e2e CI job was added"
files: [scripts/tests/test_ci_workflow.py]
verify: mise exec -- pytest scripts/tests/test_ci_workflow.py -q
depends_on: [e2e-behind-slow-marker]
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/init-leaves-a-green-tree-ci-workflow-test-pins-e2e-jo
branch: init-leaves-a-green-tree-ci-workflow-test-pins-e2e-jo
verified_head: ""
run: ""
provides: []
---

# ci workflow test pins e2e job

## Requirement

scripts/tests/test_ci_workflow.py::test_has_check_and_secrets_jobs pins .github/workflows/ci.yml to exactly two jobs (asserts 2 == count of 'runs-on: ubuntu-latest'), so the e2e job added by e2e-behind-slow-marker fails the full suite (1 failed, 494 passed). Update the test to pin the three jobs check, secrets and e2e by name, with e2e running mise run e2e, without loosening the other assertions.

## Acceptance conditions

- AC1: the CI workflow test pins jobs check, secrets and e2e and passes [evidence: test:scripts/tests/test_ci_workflow.py::test_has_check_and_secrets_jobs]

## Files

- `scripts/tests/test_ci_workflow.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The full suite is green with the three CI jobs pinned.

What is true and observable when the task is done.

## Steps

- The test currently fails on HEAD (red already seen: assert 3 == 2).
- Update it to pin check, secrets and e2e by name; run green.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
