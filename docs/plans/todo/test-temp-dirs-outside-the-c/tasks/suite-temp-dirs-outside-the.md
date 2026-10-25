---
title: Suite temp dirs outside the checkout
status: todo
repo: workbench
value: "Plugin suites stay green inside initialised workbenches, so template updates can land"
files: [plugins/workbench/scripts/run-tests.sh, plugins/workbench/scripts/flake-hunt.sh, plugins/workbench/hooks/bash-output-filter.py, plugins/workbench/scripts/tests/test_run_tests.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint"
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 23
expected_tokens: 723362
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# Suite temp dirs outside the checkout

## Requirement

Epic README G1-G4 (verbatim): "G1: `run-tests.sh` gives each component's pytest a `--basetemp` and a `TMPDIR` under a fresh mktemp dir outside any git checkout; the dir is removed when every component passes and is kept and printed (next to `full output:`) when one fails. G2: a regression test runs the fake suite from a fabricated initialised workbench and asserts the suite's temp dir is not under that tree (nor under any dir with `.gitmodules`), while the log still lands in the tree's `.logs/run-tests/`. G3: the `GIT_CEILING_DIRECTORIES` export and the comments that justify nesting are removed; run-tests.sh, flake-hunt.sh and the bash-output-filter docstring describe the new layout. G4: the plugin's own `_lib` suite passes when the plugin is copied into a fabricated initialised workbench (the exact failure seen in claude-code-tatara), proven by a command acceptance condition."

Observed failure (2026-10-25, claude-code-tatara after merging template 5bd67d1): `plugins/workbench/skills/_lib/tests/test_common.py::test_repo_root_found_via_script_location_fallback` asserts `common.repo_root() == workbench` and got `/Users/szymonri/Documents/claude-code-tatara`, because the test's cwd `tmp_path/unrelated` lived under `<checkout>/.logs/run-tests/<stamp>/tmp/_lib/...` and the cwd walk found the enclosing workbench (`code/` plus `.gitmodules`) first. The same nesting broke 3 tests in scripts/tests/test_workbench_root.py and 13 in worktree-create. Before the merge (plugin 1.0.0, basetemp under /tmp) `_lib` passed 251.

Design (my call, lean): `run-tests.sh` keeps `LOG_DIR` as is (`RUN_TESTS_LOG_DIR` override, else `<main>/.logs/run-tests/<stamp>-<pid>`, else mktemp), but creates `TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/run-tests-tmp.XXXXXX")"` and passes `--basetemp "$TMP_DIR/<component>"` with `TMPDIR="$TMP_DIR"` exported to every suite (pytest and bats alike). On an all-green run both LOG_DIR and TMP_DIR are removed; on a red run both are kept and the summary prints `temp dirs: <TMP_DIR>` after the `full output:` lines. `GIT_CEILING_DIRECTORIES` is no longer set by run-tests.sh (no shim, no fallback). The header comments of run-tests.sh and flake-hunt.sh and the docstring of hooks/bash-output-filter.py state that logs go to `.logs/run-tests` and temp dirs to a mktemp dir outside any checkout. No other file changes; root finders stay as they are.

## Acceptance conditions

- AC1: run from a fabricated initialised workbench (a git repo with `code/` and `.gitmodules`, WORKBENCH_ROOT pointing at it), the fake component's pytest basetemp and its `TMPDIR` are outside that tree and under no directory holding `.gitmodules`, while `<tree>/.logs/run-tests/<stamp>/fake.log` holds the log [evidence: test:plugins/workbench/scripts/tests/test_run_tests.py::test_suite_temp_dirs_are_outside_any_checkout]
- AC2: a green run removes both the log dir and the temp dir; a red run keeps both and prints `temp dirs: <path>` after the `full output:` line [evidence: test:plugins/workbench/scripts/tests/test_run_tests.py::test_temp_dir_kept_on_failure_removed_on_green]
- AC3: run-tests.sh no longer sets `GIT_CEILING_DIRECTORIES` and no comment in it or in flake-hunt.sh or hooks/bash-output-filter.py claims the basetemps live under the log dir [evidence: command:! grep -q GIT_CEILING_DIRECTORIES plugins/workbench/scripts/run-tests.sh && ! grep -qi "basetemps live under the log dir" plugins/workbench/scripts/run-tests.sh && grep -q "outside any" plugins/workbench/scripts/run-tests.sh && grep -q "outside any" plugins/workbench/scripts/flake-hunt.sh && grep -q "outside any" plugins/workbench/hooks/bash-output-filter.py]
- AC4: the plugin's `_lib` suite passes when the plugin is copied into a fabricated initialised workbench, reproducing the claude-code-tatara failure [evidence: command:W="$(mktemp -d "${TMPDIR:-/tmp}/wb-init.XXXXXX")" && git -C "$W" init -q && mkdir -p "$W/code" && : > "$W/.gitmodules" && cp -R plugins "$W/plugins" && (cd "$W" && git add -A && git -c user.name=t -c user.email=t@t commit -qm init && WORKBENCH_ROOT="$W" bash plugins/workbench/scripts/run-tests.sh --only _lib) && rm -rf "$W"]
- AC5: the existing run-tests tests (log dir override and fallback, green run leaves nothing, flake-hunt) still pass and the scripts suite and lint are green [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only scripts && mise run lint]

## Files

- `plugins/workbench/scripts/run-tests.sh`
- `plugins/workbench/scripts/flake-hunt.sh`
- `plugins/workbench/hooks/bash-output-filter.py`
- `plugins/workbench/scripts/tests/test_run_tests.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

1. Red: in scripts/tests/test_run_tests.py add `test_suite_temp_dirs_are_outside_any_checkout` (make the fixture tree an initialised workbench: `git init`, `code/`, `.gitmodules`; have the fake component record its basetemp and TMPDIR into its output) and `test_temp_dir_kept_on_failure_removed_on_green`; run `bash plugins/workbench/scripts/run-tests.sh --only scripts` and see exactly those two fail.
2. Green: in run-tests.sh create the mktemp temp dir, pass `--basetemp "$TMP_DIR/<component>"` and export `TMPDIR` for every suite, remove it on green, keep and print `temp dirs:` on red, drop the GIT_CEILING_DIRECTORIES block; update the header comments of run-tests.sh and flake-hunt.sh and the docstring of hooks/bash-output-filter.py; run the same command once and see it green.
3. Run AC3 and AC4 as written, then the verify on the committed HEAD.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
