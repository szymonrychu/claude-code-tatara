# Test temp dirs outside the checkout retro

## Review

Migrated from the epic format.

## What went well

- suite-temp-dirs-outside-the passed its own task review in round 0 (6f40f47) with a quoted tail: scripts 175 passed, lint clean, AC4 `_lib` 212 passed in a fabricated initialised workbench.
- The whole-diff review found the critical, the orchestrator verified it, and one fix round (bd22020: mktemp guard, exit 2, temp dir created before log dir) was re-reviewed clean with a live reproduction; scope audit then found no gaps.
- Verification was independent and real: full suite and lint in the integration tree on bd22020 both exit 0, and both verifies on main (fd524cc -> db1ad54) green.
- Points estimate held (3 vs 3, MdAPE 0.0%).
- Rulings were explicit: `unset WORKBENCH_ROOT CLAUDE_PROJECT_DIR` judged correct and documented as part of the fix; security lens skipped with a reason (no hooks, secrets, RBAC or pins touched).

## What went wrong or could improve

- The task review passed code with a critical: a failed `mktemp` left TMP_DIR empty, `cd ""` resolved to plugins/workbench and the green-run `rm -rf` would have deleted the plugin dir (run-tests.sh:70-72,172; `set -uo pipefail` without `set -e`). Only the whole-diff review caught it.
- Root cause came from the previous epic's output-spill-to-logs task, which was only ever exercised in the template (no .gitmodules); the instance shape was never tested until now.
- Minutes came in under estimate (14 vs 23, ratio 0.61, MdAPE 64.3%) but tokens ran at 1421756 vs 723362 (ratio 1.97, MdAPE 49.1%); the fix round and whole-diff review were not in the estimate.
- Summary prints `temp dirs:` after `failure logs:` rather than per component (accepted at scope audit).

## Recommendations

- Code:
  - plugins/workbench/skills/start-development/scripts (run-tests.sh, lines 70-72 and 172): the script runs `set -uo pipefail` without `set -e`, so any other unchecked command that feeds a `cd` or `rm -rf` target is the same class of bug; audit the remaining `cd`/`rm -rf` targets for empty-variable use.
  - Instance-shaped fixture (a tree with .gitmodules) is now the reproduction for the temp-dir path; keep it in the scripts suite so the template-only blind spot does not return.
- Delivered differently:
  - Added beyond the first design: the `mktemp` failure guard (exit 2, temp dir created before the log dir), because the whole-diff review showed the green-run cleanup could delete plugins/workbench.
  - `unset WORKBENCH_ROOT CLAUDE_PROJECT_DIR` is part of the fix, documented and judged correct by the reviewer.
- Tech debt:
  - `temp dirs:` is printed once in the summary after `failure logs:`, not per component; remove by printing it where each component's result is reported, if the user wants it.
- Workflow:
  - recurring (epic-and-task-migration-skil, lean-development-flow): defects that no per-task review saw surfaced only at the whole-diff review (there: a done epic with no RETRO.md skipped by migrate, stale references to retired concepts; here: the mktemp critical). Change: add to the per-task reviewer checklist, for any task that deletes or cleans up (`rm -rf`, `cd` into a computed path), "what runs if the producing command fails or the variable is empty", and keep the whole-diff review mandatory for every epic including one-task lean epics.
  - Estimates: for a lean epic the tokens estimate should include one whole-diff review plus a possible fix round; here the actual was 1.97x. One data point, not recurring.
  - Template-only exercise: a task whose behaviour depends on instance-only structure (.gitmodules, submodules) needs an instance-shaped fixture in its verify; one occurrence, not recurring.

## Delivery record (migrated)

### Asked

run-tests.sh (and flake-hunt.sh through it) must give the suites their pytest basetemp and TMPDIR outside any git checkout, with component logs still in the main checkout's `.logs/run-tests/<stamp>/`. Motivation: claude-code-tatara went red after merging template 5bd67d1, because plugin suites discovered the enclosing initialised workbench from temp repos nested under `.logs` (`_lib` test_repo_root_found_via_script_location_fallback plus 16 more failing; `_lib` was 251 passed before). Gate approved 2026-10-25 ("Go").

### Shipped

Meta mode, lean epic, one task. Closed by `ticket.py close`: main fast-forwarded fd524cc -> db1ad54 (commits a28332f, 0eb3907, db1ad54), integration and main verifies (`mise run test && mise run lint`) both green per close.json. No MR. Epic review verdict: pass (2026-10-25); whole-diff review found one critical, fixed in one fix round; scope audit no gaps. Security lens skipped (no hooks, secrets, RBAC or pins touched; the bash-output-filter.py change is a docstring).

### Tasks

| Task | Status | Verified head | Review rounds | Verification tail |
|---|---|---|---|---|
| suite-temp-dirs-outside-the | done (task file) | bd22020 (task file `verified_head`; pre-close SHA, main carries a28332f..db1ad54) | task review clean in round 0 at 6f40f47 (pointsActual 3); epic-level review: 1 fix round (bd22020), re-reviewed clean | at 6f40f47: PASS scripts 175; lint clean; AC4 `_lib` 212 passed in a fabricated initialised workbench; worktree-create 27 passed there too. At bd22020: full suite and lint exit 0 (.logs/tempdirs-review-test2.log, tempdirs-review-lint2.log). Red evidence: implementer's own run, not read by me beyond the notes. |

Actuals from the task file: 3 points, 14 min, 1421756 tokens (impl 1127922, review 293834).

### Rulings

- Builder check answers (orchestrator, 2026-10-25): (1) `${TMPDIR:-/tmp}` trusted as given. Cost if wrong: a TMPDIR set inside a checkout reintroduces nesting. (2) bats suites get exported `TMPDIR` only; `--basetemp` is pytest's. (3) With `RUN_TESTS_LOG_DIR` overridden the temp dir is still its own mktemp dir, kept and printed on red. (4) The temp dir is removed whenever run-tests.sh exits 0, kept otherwise. Cost if wrong on (3)/(4): a leaked temp dir or a lost one on a failure.
- Accepted at scope audit: `temp dirs:` printed once in the summary after `failure logs:` instead of per component. Cost if wrong: slightly harder to map a temp dir to a component.
- Accepted: `unset WORKBENCH_ROOT CLAUDE_PROJECT_DIR` is part of the fix, judged correct by the reviewer. Cost if wrong: suites lose an inherited root override they relied on.
- Critical finding acted on: a failed mktemp left TMP_DIR empty, `cd ""` resolved to plugins/workbench, and the green-run cleanup `rm -rf` would delete it (run-tests.sh:70-72,172, no `set -e`). Verified by the orchestrator, fixed in bd22020 (mktemp guard, exit 2, temp dir created before log dir).

### Discovered and blocked

- claude-code-tatara still needs the template update re-run (parked on branch template-merge-3d1d1cb, its main reset to 9ca4f87). Non-goal of this epic; follows by hand after the user pushes main. Cleared by: the user.
- 38 fixture worktrees and branches that the nested suites had created in the real tatara repo were found and have since been cleaned (per orchestrator).

### Not pushed

Local main (db1ad54) is committed and not pushed. The user pushes.

### Lessons routed to

- The earlier epic housekeeping-rules-estimates (task output-spill-to-logs) was only tested in the template, which has no `.gitmodules`, so the nesting bug was invisible. Mechanical check added: an instance-shaped fixture (fabricated initialised workbench with `.git`, `code/`, `.gitmodules`) is now the AC4 reproduction, plus `test_suite_temp_dirs_are_outside_any_checkout` in plugins/workbench/scripts/tests/test_run_tests.py. No skill or rule edit.
- Cleanup commands built from a variable (`rm -rf` after `cd "$VAR"`) need a guard when the variable can be empty: covered by the mktemp-failure exit 2 in run-tests.sh; no wider lint rule added.
