# Test temp dirs outside the checkout record

## Asked

run-tests.sh (and flake-hunt.sh through it) must give the suites their pytest basetemp and TMPDIR outside any git checkout, with component logs still in the main checkout's `.logs/run-tests/<stamp>/`. Motivation: claude-code-tatara went red after merging template 5bd67d1, because plugin suites discovered the enclosing initialised workbench from temp repos nested under `.logs` (`_lib` test_repo_root_found_via_script_location_fallback plus 16 more failing; `_lib` was 251 passed before). Gate approved 2026-10-25 ("Go").

## Shipped

Meta mode, lean epic, one task. Closed by `ticket.py close`: main fast-forwarded fd524cc -> db1ad54 (commits a28332f, 0eb3907, db1ad54), integration and main verifies (`mise run test && mise run lint`) both green per close.json. No MR. Epic review verdict: pass (2026-10-25); whole-diff review found one critical, fixed in one fix round; scope audit no gaps. Security lens skipped (no hooks, secrets, RBAC or pins touched; the bash-output-filter.py change is a docstring).

## Tasks

| Task | Status | Verified head | Review rounds | Verification tail |
|---|---|---|---|---|
| suite-temp-dirs-outside-the | done (task file) | bd22020 (task file `verified_head`; pre-close SHA, main carries a28332f..db1ad54) | task review clean in round 0 at 6f40f47 (pointsActual 3); epic-level review: 1 fix round (bd22020), re-reviewed clean | at 6f40f47: PASS scripts 175; lint clean; AC4 `_lib` 212 passed in a fabricated initialised workbench; worktree-create 27 passed there too. At bd22020: full suite and lint exit 0 (.logs/tempdirs-review-test2.log, tempdirs-review-lint2.log). Red evidence: implementer's own run, not read by me beyond the notes. |

Actuals from the task file: 3 points, 14 min, 1421756 tokens (impl 1127922, review 293834).

## Rulings

- Builder check answers (orchestrator, 2026-10-25): (1) `${TMPDIR:-/tmp}` trusted as given. Cost if wrong: a TMPDIR set inside a checkout reintroduces nesting. (2) bats suites get exported `TMPDIR` only; `--basetemp` is pytest's. (3) With `RUN_TESTS_LOG_DIR` overridden the temp dir is still its own mktemp dir, kept and printed on red. (4) The temp dir is removed whenever run-tests.sh exits 0, kept otherwise. Cost if wrong on (3)/(4): a leaked temp dir or a lost one on a failure.
- Accepted at scope audit: `temp dirs:` printed once in the summary after `failure logs:` instead of per component. Cost if wrong: slightly harder to map a temp dir to a component.
- Accepted: `unset WORKBENCH_ROOT CLAUDE_PROJECT_DIR` is part of the fix, judged correct by the reviewer. Cost if wrong: suites lose an inherited root override they relied on.
- Critical finding acted on: a failed mktemp left TMP_DIR empty, `cd ""` resolved to plugins/workbench, and the green-run cleanup `rm -rf` would delete it (run-tests.sh:70-72,172, no `set -e`). Verified by the orchestrator, fixed in bd22020 (mktemp guard, exit 2, temp dir created before log dir).

## Discovered and blocked

- claude-code-tatara still needs the template update re-run (parked on branch template-merge-3d1d1cb, its main reset to 9ca4f87). Non-goal of this epic; follows by hand after the user pushes main. Cleared by: the user.
- 38 fixture worktrees and branches that the nested suites had created in the real tatara repo were found and have since been cleaned (per orchestrator).

## Not pushed

Local main (db1ad54) is committed and not pushed. The user pushes.

## Lessons routed to

- The earlier epic housekeeping-rules-estimates (task output-spill-to-logs) was only tested in the template, which has no `.gitmodules`, so the nesting bug was invisible. Mechanical check added: an instance-shaped fixture (fabricated initialised workbench with `.git`, `code/`, `.gitmodules`) is now the AC4 reproduction, plus `test_suite_temp_dirs_are_outside_any_checkout` in plugins/workbench/scripts/tests/test_run_tests.py. No skill or rule edit.
- Cleanup commands built from a variable (`rm -rf` after `cd "$VAR"`) need a guard when the variable can be empty: covered by the mktemp-failure exit 2 in run-tests.sh; no wider lint rule added.
