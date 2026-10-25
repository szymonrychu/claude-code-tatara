---
title: Docs flow phases
status: done
repo: workbench
value: "The orchestrator's flow docs describe exactly the lifecycle the tools now run"
files: [plugins/workbench/skills/start-development/SKILL.md, plugins/workbench/skills/start-development/references/phase-4-execute.md, plugins/workbench/skills/start-development/references/phases-5-7.md, plugins/workbench/skills/start-development/references/multi-epic.md, plugins/workbench/skills/start-development/references/run-handback.md, plugins/workbench/skills/start-research/tests/test_start_skills_structure.py, plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py, plugins/workbench/skills/start-development/tests/test_start_development_generic.py]
verify: "cd plugins/workbench && bash scripts/run-tests.sh --only start-development && bash scripts/run-tests.sh --only start-research && cd ../.. && mise run lint"
depends_on: [epic-close-sweep, epic-close-command, forward-merge-via-epic, common-worktree-path-py, common-worktree-path-sh]
model: sonnet
review: ""
verified_head: e5270eb1649c3fd84ff6b321455fb8ba1986ae98
points: 5
expected_minutes: 70
expected_tokens: 3750000
points_actual: ""
actual_minutes: 74
actual_tokens: 1997602
actual_roles: "impl 21, review 53"
actual_role_tokens: "impl 1062916, review 934686"
---

# Docs flow phases

## Requirement

Describe the epic worktree lifecycle in the start-development flow docs (design D5, D7, D13, D14; user decisions U2, U3; interrogate verdict D, E).

- `plugins/workbench/skills/start-development/SKILL.md`. Modes: meta mode tasks land on the integration branch `<epic>`, and the epic closes by rebase plus fast-forward of the local main, with or without an `origin` remote; that replaces the meta-mode PR path, and pushing main stays with the user. Component mode keeps the MR from the integration branch. Lean path: "work in the integration worktree" names the tree `move in-progress` creates. Phase 4: the claim creates the integration tree, task trees fork from `<epic>`, and the run lands each task. Phases 5-7: the close order below. `test_skill_size.py` stays green.
- `references/phase-4-execute.md`:
  - lines 7-18: the hand-run `git-worktrees-create` step is replaced by "`move in-progress` creates it";
  - `baseRef` is the epic branch and `mainCheckout` is the main checkout;
  - landing happens in the run, `land-failed` is an escalation reason;
  - escalated tasks land after a ruling through `continue`'s `MERGE ... --base <epic>` lines and a `worktree-merger`.
  - an epic claimed before this change gets its integration tree from `ticket.py worktrees <epic> --integration`, and its live legacy double-hyphen trees keep running.
- `references/phases-5-7.md` (25-41, 59), the close order (interrogate verdict D, E); main is never moved onto an untested tip:
  1. the pass verdict;
  2. every done task is on `<epic>`: `ticket.py continue` prints no MERGE line, and that includes a task released by an accept ruling that has no dependents;
  3. meta mode: `ticket.py close <epic> --verify '<full suite and lint>'`, which does three things in order:
     - it rebases `<epic>` onto main inside the integration tree and runs the full suite and lint on the rebased tip there;
     - only when they pass, it fast-forwards main;
     - it then runs the full suite on main and records main's pre-fast-forward SHA in `close.json`.
     A rebase conflict goes to a `worktree-merger` in the integration tree, then close runs again;
  4. `ticket.py move <epic> done`, which removes every task and integration tree and branch.
  Component mode: the phase 6 MR from the integration branch, then `move done` once the MRs merge.
- `references/multi-epic.md`: each epic has its own integration tree and branch; concurrent epics never share one; each closes into main on its own, rebasing onto whatever main has become.
- `references/run-handback.md`: the `landed` return field (with each task's `forkPoint`) and the `land-failed` reason, and what the orchestrator does with each.
- Doc needle tests updated in this task: `start-research/tests/test_start_skills_structure.py:518` (Phase 4 names `baseRef`, the epic branch and `mainCheckout`), `test_ticket_flow_docs.py:81` (needles for the integration tree created by the claim and the landing in the run), and `test_start_development_generic.py:24` (the meta-mode sentences now pin the local fast-forward close, and the old "never commits" sentence is gone).

## Acceptance conditions

- AC1: Phase 4 names baseRef as the epic branch and mainCheckout [evidence: test:plugins/workbench/skills/start-research/tests/test_start_skills_structure.py::test_phase4_names_epic_base_ref_and_main_checkout]
- AC2: the flow docs say the claim creates the integration tree and the run lands each task [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_flow_docs_integration_tree_and_landing]
- AC3: the meta-mode rule describes the local rebase and fast-forward close [evidence: test:plugins/workbench/skills/start-development/tests/test_start_development_generic.py::test_meta_mode_closes_by_local_fast_forward]
- AC4: phases-5-7 gives the close order ending in move done removing every tree and branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_close_order_documented]
- AC5: run-handback names landed and land-failed [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_run_handback_names_landing]
- AC6: SKILL.md stays within its size budget [evidence: command:cd plugins/workbench && pytest skills/start-development/tests/test_skill_size.py -q]
- AC7: phases-5-7 says close verifies the rebased epic tip before main moves, refuses while a done task is not on the epic branch, and records main's pre-fast-forward SHA [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_close_order_verifies_rebased_tip_before_main_moves]

## Files

- `plugins/workbench/skills/start-development/SKILL.md`
- `plugins/workbench/skills/start-development/references/phase-4-execute.md`
- `plugins/workbench/skills/start-development/references/phases-5-7.md`
- `plugins/workbench/skills/start-development/references/multi-epic.md`
- `plugins/workbench/skills/start-development/references/run-handback.md`
- `plugins/workbench/skills/start-research/tests/test_start_skills_structure.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py`
- `plugins/workbench/skills/start-development/tests/test_start_development_generic.py`

## Interfaces

- Documentation only; the needles in the three test files pin the wording.

## Expected outcome

An orchestrator reading SKILL.md and its references runs claim, worktrees, run with in-run landing, close and cleanup in that order, in either mode, without consulting the code.

## Steps

- Red: update the needles in the three test files to the new lifecycle and add the AC tests; run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development`; expect the needle tests to fail.
- Green: edit SKILL.md and the four references.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only start-development && bash scripts/run-tests.sh --only start-research && cd ../.. && mise run lint`.

## Notes

- Q2's recommended answer is the written rule; if the gate answers otherwise the orchestrator amends this task before the run.
- Keep SKILL.md short: details belong in the references (test_skill_size.py).

- 2026-10-21 run epic-integration-worktrees: dependency-failed on epic-close-sweep, epic-close-command, forward-merge-via-epic

- 2026-10-21 run epic-integration-worktrees: dependency-failed on forward-merge-via-epic
