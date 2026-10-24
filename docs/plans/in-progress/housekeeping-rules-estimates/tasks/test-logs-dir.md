---
title: Test logs dir
status: in-progress
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

- `run-tests.sh [--only <component>]`, env `RUN_TESTS_LOG_DIR` - unchanged contract, new default.
- `flake-hunt.sh <component> <runs> [parallel]` - unchanged contract, new log location.

## Expected outcome

Test and flake-hunt logs an agent reads after a failure sit in the gitignored `.logs` of the main checkout.

## Steps

1. List the files under Files, read them in one pass; adjust the existing log-location tests and add AC2; run `pytest scripts/tests/test_run_tests.py -q` from plugins/workbench: they fail.
2. Implement in both scripts; run the verify once.
3. Commit; leave the tree clean.

## Notes

- Estimate: 2 points.
- The test fixture `tree` copies the scripts into a temp tree; give it a temp main checkout (git init) or set WORKBENCH_ROOT, and clear CLAUDE_PROJECT_DIR.
- Keep the per-pytest `--basetemp` under the log dir.
- Depends on workbench-dirs for `workbench.py logs`.
