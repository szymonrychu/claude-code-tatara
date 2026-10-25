# Test temp dirs outside the checkout retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| Suite temp dirs outside the checkout | 3 | 3 | 23 | 14 | 723362 | 1421756 |
| Total | 3 | 3 | 23 | 14 | 723362 | 1421756 |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| Suite temp dirs outside the checkout | 0 | 0.61 | 1.97 |

- MdAPE points: 0.0%
- MdAPE minutes: 64.3%
- MdAPE tokens: 49.1%
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| suite-temp-dirs-outside-the passed its own task review in round 0 (6f40f47) with a quoted tail: scripts 175 passed, lint clean, AC4 `_lib` 212 passed in a fabricated initialised workbench. | The task review passed code with a critical: a failed `mktemp` left TMP_DIR empty, `cd ""` resolved to plugins/workbench and the green-run `rm -rf` would have deleted the plugin dir (run-tests.sh:70-72,172; `set -uo pipefail` without `set -e`). Only the whole-diff review caught it. |
| The whole-diff review found the critical, the orchestrator verified it, and one fix round (bd22020: mktemp guard, exit 2, temp dir created before log dir) was re-reviewed clean with a live reproduction; scope audit then found no gaps. | Root cause came from the previous epic's output-spill-to-logs task, which was only ever exercised in the template (no .gitmodules); the instance shape was never tested until now. |
| Verification was independent and real: full suite and lint in the integration tree on bd22020 both exit 0, and both verifies on main (fd524cc -> db1ad54) green. | Minutes came in under estimate (14 vs 23, ratio 0.61, MdAPE 64.3%) but tokens ran at 1421756 vs 723362 (ratio 1.97, MdAPE 49.1%); the fix round and whole-diff review were not in the estimate. |
| Points estimate held (3 vs 3, MdAPE 0.0%). | Summary prints `temp dirs:` after `failure logs:` rather than per component (accepted at scope audit). |
| Rulings were explicit: `unset WORKBENCH_ROOT CLAUDE_PROJECT_DIR` judged correct and documented as part of the fix; security lens skipped with a reason (no hooks, secrets, RBAC or pins touched). | |

## Improvements

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
