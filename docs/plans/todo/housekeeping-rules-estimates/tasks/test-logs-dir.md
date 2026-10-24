---
title: Test logs dir
status: todo
repo: workbench
value: Failing test and flake-hunt logs land in the gitignored .logs of the workbench root
files: [plugins/workbench/scripts/run-tests.sh, plugins/workbench/scripts/flake-hunt.sh, plugins/workbench/scripts/tests/test_run_tests.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint"
depends_on: [workbench-dirs]
model: sonnet
review: ""
verified_head: ""
---

# Test logs dir

## Requirement

User requirement (U1, verbatim): "all logs land in gitignored `.logs` in workbench root".

Design D6: `plugins/workbench/scripts/run-tests.sh` keeps a failing component's full output in `<main checkout>/.logs/run-tests/<UTC timestamp>-<pid>/` by default (resolved with `python3 <plugin>/scripts/lib/workbench.py logs`), falling back to a mktemp dir under TMPDIR only when no main checkout is found; `RUN_TESTS_LOG_DIR` still overrides, and the directory is still removed when everything passes. `flake-hunt.sh` keeps its run logs in `<main checkout>/.logs/flake-hunt/<UTC timestamp>-<pid>/` with the same fallback. Script headers name the new locations.

## Acceptance conditions

- AC1: a failing run keeps its logs under `<main checkout>/.logs/run-tests/` and prints that path [evidence: test:plugins/workbench/scripts/tests/test_run_tests.py::test_failing_component_keeps_full_output]
- AC2: RUN_TESTS_LOG_DIR still overrides the default, and with no main checkout the logs fall back to TMPDIR [evidence: test:plugins/workbench/scripts/tests/test_run_tests.py::test_log_dir_override_and_fallback]
- AC3: a green run leaves nothing behind [evidence: test:plugins/workbench/scripts/tests/test_run_tests.py::test_green_run_leaves_nothing]
- AC4: flake-hunt keeps its logs under `<main checkout>/.logs/flake-hunt/` [evidence: test:plugins/workbench/scripts/tests/test_run_tests.py::test_flake_hunt_reports_failures_and_keeps_logs]
- AC5: the scripts suite and lint (shellcheck) pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint]

## Files

- `plugins/workbench/scripts/run-tests.sh`
- `plugins/workbench/scripts/flake-hunt.sh`
- `plugins/workbench/scripts/tests/test_run_tests.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
