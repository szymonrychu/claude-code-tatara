---
title: Docs readmes fallback
status: todo
repo: workbench
value: READMEs and the off-Claude fallback run the same epic lifecycle as Claude Code
files: [README.md, plugins/workbench/README.md, AGENTS.md, scripts/harness/fallbacks/plan-execute/SKILL.md, plugins/workbench/skills/start-development/tests/test_release.py, plugins/workbench/skills/start-development/tests/test_review_flow_docs.py, scripts/tests/harness/test_fallbacks.py]
verify: "mise run test && mise run lint"
depends_on: [epic-close-sweep, epic-close-command, forward-merge-via-epic]
owns: []
uses: []
model: sonnet
estimate: 55
actual: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Docs readmes fallback

## Requirement

Describe the same lifecycle in the READMEs, AGENTS.md and the off-Claude plan-execute fallback (design D7, D1, D5; user decisions U1-U3; interrogate verdict D).

- `plugins/workbench/README.md` (202, 217): task trees are `<epic>-<task>`; the claim creates the integration tree; the move to done checks that the epic reached main and removes every tree and branch.
- `README.md`:
  - line 98: "worktree isolation" becomes "per-task git worktrees with an epic integration worktree";
  - the worktree caveat (353-357): plugin edits made in a task or integration tree take effect only after the epic merges to main and `/reload-plugins` runs.
- `AGENTS.md` template-maintenance bullet: the same caveat.
- `scripts/harness/fallbacks/plan-execute/SKILL.md`:
  - the claim creates the integration tree;
  - `ticket.py worktrees <epic>` forks task trees from `<epic>`;
  - phase 1 merges `<epic>` into the task tree, not the dependency branches;
  - phase 6 lands with `python3 ${CLAUDE_PLUGIN_ROOT}/skills/worktree-merge/scripts/merge.py --name <epic>-<task> --base <epic> --keep --verify '<verify>'` from the main checkout;
  - a close section gives the epic close order: every done task on `<epic>` (no MERGE line from `ticket.py continue`); then, in meta mode, `ticket.py close <epic> --verify '<full suite and lint>'`, which rebases `<epic>` onto main in the integration tree, runs the full suite and lint on the rebased tip, fast-forwards main only when green, runs the full suite on main and records main's pre-fast-forward SHA; then `ticket.py move <epic> done`. The section says main never moves onto an untested tip;
  - an epic claimed before this change runs `ticket.py worktrees <epic> --integration` first;
  - one sentence: never the harness's built-in worktree feature.
- Needles updated in this task: `test_release.py:144` (`<epic>-<task>`), `test_review_flow_docs.py:266-267` (README reap line, no `<epic>--<task>` form), `scripts/tests/harness/test_fallbacks.py` (the fallback names `--base <epic>`, `merge.py` and `move <epic> done`).

## Acceptance conditions

- AC1: the plugin README names single-hyphen trees and the integration tree [evidence: test:plugins/workbench/skills/start-development/tests/test_release.py::test_readme_names_epic_task_trees_and_integration]
- AC2: the README reap line carries no double-hyphen form [evidence: test:plugins/workbench/skills/start-development/tests/test_review_flow_docs.py::test_readme_reap_task_needs_epic]
- AC3: the fallback describes forking from the epic, landing with merge.py on the epic base and the close order [evidence: test:scripts/tests/harness/test_fallbacks.py::test_plan_execute_fallback_epic_lifecycle]
- AC4: the root README and AGENTS.md say plugin edits are live only after the epic reaches main [evidence: command:grep -q 'integration' README.md && grep -q 'integration' AGENTS.md]
- AC5: no double-hyphen task name remains in the READMEs or the fallback [evidence: command:! grep -n '<epic>--<task>' README.md plugins/workbench/README.md scripts/harness/fallbacks/plan-execute/SKILL.md]
- AC6: the fallback close order verifies the rebased epic tip before main moves [evidence: test:scripts/tests/harness/test_fallbacks.py::test_plan_execute_fallback_close_order_verifies_before_main_moves]

## Files

- `README.md`
- `plugins/workbench/README.md`
- `AGENTS.md`
- `scripts/harness/fallbacks/plan-execute/SKILL.md`
- `plugins/workbench/skills/start-development/tests/test_release.py`
- `plugins/workbench/skills/start-development/tests/test_review_flow_docs.py`
- `scripts/tests/harness/test_fallbacks.py`

## Interfaces

- Documentation only; the fallback is hand-written source emitted by `scripts/harness/skills_emit.py:164-174`.

## Expected outcome

Every entry point a human or another harness reads describes claim, fork, in-run landing, close and cleanup the same way as SKILL.md.

## Steps

- Red: update the needles in the three test files; run `pytest scripts/tests/harness/test_fallbacks.py -q` and `cd plugins/workbench && pytest skills/start-development/tests/test_release.py -q`; expect failures.
- Green: edit the four docs.
- Run `mise run test && mise run lint` from the root (the root suite covers the harness emitter).

## Notes

- AGENTS.md outside the `workbench:rules` block is hand-written; never edit the block by hand (AGENTS.md template maintenance).
- `mise run harness-setup` regenerates emitted harness copies only when a target is enabled; nothing tracked is regenerated here.
