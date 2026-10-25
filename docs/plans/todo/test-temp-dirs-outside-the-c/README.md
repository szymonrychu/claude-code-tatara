---
title: Test temp dirs outside the checkout
blockers: []
stage: build
owner: ""
repos: [workbench]
created: 2026-10-25
---

# Test temp dirs outside the checkout

## Project brief

What: run-tests.sh (and through it flake-hunt.sh) must give the suites their pytest basetemp and TMPDIR outside any git checkout, while the component logs keep landing in the main checkout's `.logs/run-tests/<stamp>/`.
How: a fresh `mktemp -d` under the system TMPDIR for the suites' temp dirs, removed on a green run and kept and named on a red one; the `GIT_CEILING_DIRECTORIES` workaround goes away with the nesting; a regression test runs the fake suite from a fabricated initialised workbench (`.git`, `code/`, `.gitmodules`) and proves the temp dirs are outside it.
Why: since housekeeping-rules-estimates (task output-spill-to-logs) the basetemps live under `<checkout>/.logs/run-tests/.../tmp`. In an initialised workbench (which has `code/` and `.gitmodules`) the plugin's own root finders (`_lib/common.repo_root` cwd walk, `workbench.py` walk-up, worktree tests) then discover the enclosing real workbench from inside their temp repos, and the plugin test families go red: observed 2026-10-25 in /Users/szymonri/Documents/claude-code-tatara after merging template 5bd67d1 (`_lib` 251 passed before the merge, `test_repo_root_found_via_script_location_fallback` and 16 more failing after it). The template never shows it because it has no `.gitmodules`.

## Description

Reported 2026-10-25 while installing plugin 2.0.0 into the claude-code-tatara workbench (the merge is parked there on branch template-merge-3d1d1cb; its main was reset to 9ca4f87 to stay green). The logs rule (housekeeping rule 9: every log lands in `.logs`) is kept: component logs stay in `.logs/run-tests/`; only the suites' scratch temp dirs move out of the checkout, because a fake workbench nested inside a real one cannot be told apart by walk-up root finders.

## Goals

- G1: `run-tests.sh` gives each component's pytest a `--basetemp` and a `TMPDIR` under a fresh mktemp dir outside any git checkout; the dir is removed when every component passes and is kept and printed (next to `full output:`) when one fails.
- G2: a regression test runs the fake suite from a fabricated initialised workbench and asserts the suite's temp dir is not under that tree (nor under any dir with `.gitmodules`), while the log still lands in the tree's `.logs/run-tests/`.
- G3: the `GIT_CEILING_DIRECTORIES` export and the comments that justify nesting are removed; run-tests.sh, flake-hunt.sh and the bash-output-filter docstring describe the new layout.
- G4: the plugin's own `_lib` suite passes when the plugin is copied into a fabricated initialised workbench (the exact failure seen in claude-code-tatara), proven by a command acceptance condition.

## Non-goals

- Moving the logs out of `.logs` (rule 9 stands).
- Changing `common.repo_root` or `workbench.py` root detection.
- Re-running the claude-code-tatara template update (follows this epic, by hand, after the fix lands on main).

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
