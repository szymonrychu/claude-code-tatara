---
title: Docs flow phases
status: todo
repo: workbench
value: "The orchestrator's flow docs describe exactly the lifecycle the tools now run"
files: [plugins/workbench/skills/start-development/SKILL.md, plugins/workbench/skills/start-development/references/phase-4-execute.md, plugins/workbench/skills/start-development/references/phases-5-7.md, plugins/workbench/skills/start-development/references/multi-epic.md, plugins/workbench/skills/start-development/references/run-handback.md, plugins/workbench/skills/start-research/tests/test_start_skills_structure.py, plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py, plugins/workbench/skills/start-development/tests/test_start_development_generic.py]
verify: "cd plugins/workbench && bash scripts/run-tests.sh --only start-development && bash scripts/run-tests.sh --only start-research && cd ../.. && mise run lint"
depends_on: [epic-close-sweep, forward-merge-via-epic, common-worktree-path-py, common-worktree-path-sh]
owns: []
uses: []
model: sonnet
estimate: 60
actual: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Docs flow phases

## Requirement

Describe the epic worktree lifecycle in the start-development flow docs (design D5, D7; user decisions U2, U3).

- `plugins/workbench/skills/start-development/SKILL.md`. Modes: meta mode tasks land on the integration branch `<epic>`, and the epic closes by rebase plus fast-forward of the local main, with or without an `origin` remote; that replaces the meta-mode PR path, and pushing main stays with the user. Component mode keeps the MR from the integration branch. Lean path: "work in the integration worktree" names the tree `move in-progress` creates. Phase 4: the claim creates the integration tree, task trees fork from `<epic>`, and the run lands each task. Phases 5-7: the close order below. `test_skill_size.py` stays green.
- `references/phase-4-execute.md`:
  - lines 7-18: the hand-run `git-worktrees-create` step is replaced by "`move in-progress` creates it";
  - `baseRef` is the epic branch and `mainCheckout` is the main checkout;
  - landing happens in the run, `land-failed` is an escalation reason;
  - escalated tasks land after a ruling through `continue`'s `MERGE ... --base <epic>` lines and a `worktree-merger`.
- `references/phases-5-7.md` (25-41, 59), the close order:
  1. the pass verdict;
  2. the full suite on the integration tree;
  3. meta mode: a `worktree-merger` runs `merge.py --name <epic> --base main --keep`;
  4. the full suite on main;
  5. `ticket.py move <epic> done`, which removes every task and integration tree and branch.
  Component mode: the phase 6 MR from the integration branch, then `move done` once the MRs merge.
- `references/multi-epic.md`: each epic has its own integration tree and branch; concurrent epics never share one; each closes into main on its own, rebasing onto whatever main has become.
- `references/run-handback.md`: the `landed` return field and the `land-failed` reason, and what the orchestrator does with each.
- Doc needle tests updated in this task: `start-research/tests/test_start_skills_structure.py:518` (Phase 4 names `baseRef`, the epic branch and `mainCheckout`), `test_ticket_flow_docs.py:81` (needles for the integration tree created by the claim and the landing in the run), and `test_start_development_generic.py:24` (the meta-mode sentences now pin the local fast-forward close, and the old "never commits" sentence is gone).

## Acceptance conditions

- AC1: Phase 4 names baseRef as the epic branch and mainCheckout [evidence: test:plugins/workbench/skills/start-research/tests/test_start_skills_structure.py::test_phase4_names_epic_base_ref_and_main_checkout]
- AC2: the flow docs say the claim creates the integration tree and the run lands each task [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_flow_docs_integration_tree_and_landing]
- AC3: the meta-mode rule describes the local rebase and fast-forward close [evidence: test:plugins/workbench/skills/start-development/tests/test_start_development_generic.py::test_meta_mode_closes_by_local_fast_forward]
- AC4: phases-5-7 gives the close order ending in move done removing every tree and branch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_close_order_documented]
- AC5: run-handback names landed and land-failed [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_run_handback_names_landing]
- AC6: SKILL.md stays within its size budget [evidence: command:cd plugins/workbench && pytest skills/start-development/tests/test_skill_size.py -q]

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
