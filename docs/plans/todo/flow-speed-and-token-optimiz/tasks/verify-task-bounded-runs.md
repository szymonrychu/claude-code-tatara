---
title: Verify task bounded runs
status: todo
repo: workbench
value: "No verifier dies at the Bash cap and TDD-revert costs one short run, not two suites"
files: [plugins/workbench/scripts/verify-task.py, plugins/workbench/scripts/tests/test_verify_bounded.py, plugins/workbench/scripts/tests/test_verify_tdd_revert_dirs.py, plugins/workbench/scripts/tests/test_verify_task.py, plugins/workbench/agents/verifier.md]
verify: "cd plugins/workbench && pytest scripts/tests/test_verify_bounded.py scripts/tests/test_verify_tdd_revert_dirs.py scripts/tests/test_verify_task.py scripts/tests/test_verify_ref_runner.py scripts/tests/test_verify_command_tail.py -q && ruff check scripts"
depends_on: []
owns: [verify-task-cli]
uses: []
model: sonnet
estimate: 6
actual: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Verify task bounded runs

## Requirement

Bound every run verify-task makes and stop the third suite run (design D1). `plugins/workbench/scripts/verify-task.py` only, plus the verifier agent's Bash timeout.

- `run_shell` and `run_argv` take a timeout. New `--timeout` seconds per command (default 480, so two runs plus triage fit the verifier's 600 s Bash call). On expiry the process group is killed and the result carries `timeout: {command, seconds}`, `exit: 124`, `passed: false` and the output tail captured so far as `evidence`. The limit applies to the main command, each `command:` AC, each `test:` ref re-run, each install step and the TDD-revert base run.
- `--prev-head` that does not match `^[0-9a-f]{7,40}$` yields one JSON result with `passed: false` and `error: "prev-head is not a sha: <first 40 chars>"` and exit 2, never an argparse usage error. A valid sha keeps `changedSincePrevious`.
- `--tdd-revert`: on the reverted base, run only the runner commands of the AC `test:` refs (one per ref file, built with the runner resolution check_ac already uses) when the task has any, else the command. `passedOnHead` reuses the main run's exit code instead of running again, so one verify-task call runs the command at most twice. `tdd.baseCommand` records what ran on base.
- `--cmd` becomes optional. `--targeted`, or no `--cmd`, builds the command from the runner of each AC `test:` ref file and of each changed test file (matched by `--test-re`), deduplicated, joined with ` && `. The result's `command` is the built command and `commandScope` is `"targeted"`; with no refs and no changed test files the result is `passed: false` with `error: "no targeted tests"`.
- `plugins/workbench/agents/verifier.md`: the one Bash call that runs verify-task sets `timeout: 600000`.

## Acceptance conditions

- AC1: a command that outlives --timeout yields a timeout field, exit 124 and passed false in one JSON result [evidence: test:plugins/workbench/scripts/tests/test_verify_bounded.py::test_command_timeout_reports_timeout_field]
- AC2: a non-sha --prev-head yields a JSON error result, not an argparse failure [evidence: test:plugins/workbench/scripts/tests/test_verify_bounded.py::test_non_sha_prev_head_is_a_json_error]
- AC3: --tdd-revert runs the command at most twice and only the AC-referenced tests on base [evidence: test:plugins/workbench/scripts/tests/test_verify_bounded.py::test_tdd_revert_runs_at_most_twice]
- AC4: --targeted builds the command from the AC test refs and the changed test files [evidence: test:plugins/workbench/scripts/tests/test_verify_bounded.py::test_targeted_builds_command_from_refs_and_changed_tests]
- AC5: --targeted with no tests to run fails with error no targeted tests [evidence: test:plugins/workbench/scripts/tests/test_verify_bounded.py::test_targeted_without_tests_fails_with_error]
- AC6: the existing verify-task tests still pass [evidence: command:cd plugins/workbench && pytest scripts/tests/test_verify_tdd_revert_dirs.py scripts/tests/test_verify_task.py scripts/tests/test_verify_ref_runner.py scripts/tests/test_verify_command_tail.py -q]
- AC7: the verifier agent sets the 600000 ms Bash timeout [evidence: command:grep -q 'timeout: 600000' plugins/workbench/agents/verifier.md]

## Files

- `plugins/workbench/scripts/verify-task.py`
- `plugins/workbench/scripts/tests/test_verify_bounded.py`
- `plugins/workbench/scripts/tests/test_verify_tdd_revert_dirs.py`
- `plugins/workbench/scripts/tests/test_verify_task.py`
- `plugins/workbench/agents/verifier.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
