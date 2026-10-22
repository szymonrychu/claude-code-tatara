---
title: e2e behind slow marker
status: todo
repo: workbench
value: "the template's default suite stays fast while the full green-tree proof still runs in CI"
files: [pyproject.toml, scripts/tests/e2e/test_instantiate.py, .mise.toml, mise-tasks/test/scripts, .github/workflows/ci.yml, scripts/tests/test_root_config.py, scripts/tests/test_root_tooling.py, AGENTS.md]
verify: "mise exec -- pytest scripts/tests/test_root_config.py scripts/tests/test_root_tooling.py -q && mise exec -- pytest scripts/tests/e2e/test_instantiate.py -q -m 'not slow'"
depends_on: [refresh-writes-allow-entries]
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

# e2e behind slow marker

## Requirement

The template's default `mise run test` must not grow by the ~48 minutes the e2e green-tree tests take (review finding). Register a `slow` pytest marker in pyproject.toml; mark the heavy e2e tests in scripts/tests/e2e/test_instantiate.py `slow` (at least test_suite_green_on_initialised_copy and any test that runs the full `mise run test` inside a copy); the default test:scripts run deselects them (`-m "not slow"`); a new mise task `e2e` (NOT under the `test:` namespace, since root `test` depends on `test:*`) runs `pytest -m slow`; .github/workflows/ci.yml runs `mise run e2e` as its own job. The fast checks (new init, adopt, second component add asserting lint green and clean status) stay in the default suite, using lint plus a reduced, fast test target instead of the full suite. AGENTS.md Template maintenance and README "Maintaining the template" mention `mise run e2e`.

## Acceptance conditions

- AC1: the default test:scripts run deselects slow tests and the slow marker is registered [evidence: test:scripts/tests/test_root_config.py::test_slow_marker_registered_and_deselected_by_default]
- AC2: `mise run e2e` exists outside the test: namespace and runs only slow tests [evidence: test:scripts/tests/test_root_tooling.py::test_e2e_task_runs_slow_tests]
- AC3: CI runs mise run e2e as its own job [evidence: test:scripts/tests/test_root_tooling.py::test_ci_runs_e2e_job]
- AC4: the fast green-tree e2e tests still run by default and pass [evidence: command:mise exec -- pytest scripts/tests/e2e/test_instantiate.py -q -m "not slow"]

## Files

- `pyproject.toml`
- `scripts/tests/e2e/test_instantiate.py`
- `.mise.toml`
- `mise-tasks/test/scripts`
- `.github/workflows/ci.yml`
- `scripts/tests/test_root_config.py`
- `scripts/tests/test_root_tooling.py`
- `AGENTS.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The requirement above holds, pinned by the acceptance tests.

What is true and observable when the task is done.

## Steps

- Write the failing acceptance tests; run red.
- Implement; run green with the verify command.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
