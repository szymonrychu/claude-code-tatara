---
title: Flow docs update
status: todo
repo: workbench
value: The references tell the orchestrator how to relaunch in one step and show the epic estimate
files: [plugins/workbench/skills/start-development/references/task-fields.md, plugins/workbench/skills/start-development/references/tickets.md, plugins/workbench/skills/start-development/references/run-handback.md, plugins/workbench/skills/start-development/references/phase-4-execute.md, plugins/workbench/skills/start-development/SKILL.md, plugins/workbench/skills/start-development/templates/epic.md, plugins/workbench/skills/start-development/templates/record.md, plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py]
verify: "cd plugins/workbench && pytest skills/start-development/tests/test_ticket_flow_docs.py skills/start-development/tests/test_skill_size.py skills/start-development/tests/test_templates.py skills/start-development/tests/test_start_development_generic.py skills/start-development/tests/test_flow_references_remarks.py -q"
depends_on: [estimate-and-actuals, continue-launch, heartbeat-quiet, cascade-release, planner-sizing-rule]
owns: []
uses: [epic-time-line, continue-launch-lines]
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

# Flow docs update

## Requirement

Document the new estimates, actuals, relaunch and release rules in the flow references (design D3, D4, D5, D8, D9).

- `references/task-fields.md`: the `estimate` row (formula minutes from `scripts/lib/estimator.json` written by `ticket.py estimate`, `estimate_by: formula|override`, report only); the `actual` row (agent-minutes stamped from the run dir by `apply-run --run-dir` and `continue --run`, because the Workflow runtime gives scripts no clock; remove the `Date.now()` claim) and `actual_roles`; the `verify` row (targeted, a full-suite verify fails the lint on a todo task); the `review` row (doc-only and test-only skip, scoped re-review of light-tier fixes).
- `references/tickets.md`: the `estimate` subcommand, `continue --launch` (auto-accept, self-landing, `LAUNCH` and `ARM` lines) and the new Time line.
- `references/run-handback.md`: the heartbeat wakes on END and STALL; on END run `ticket.py continue <epic> --run <id> --out-dir <dir> --launch`, then the one Workflow call from the `LAUNCH` line and the one Monitor from the `ARM` line; auto-accepted processOnly and triageRejected tasks are not judged again; mediumOnly escalations are ruled like any escalation, their dependents already ran.
- `references/phase-4-execute.md`: the release rule (clean, processOnly, triageRejected, mediumOnly, ruled accept) and the relaunch scope (never a done task).
- `skills/start-development/SKILL.md`: gate item 3 shows the epic estimate line from `ticket.py estimate <epic>` and the three longest-path tasks; phase 4 relaunch names `continue --launch`. SKILL.md stays inside its size test.
- `templates/epic.md` Time section names the new line; `templates/record.md` puts `actual_roles` in the estimate-versus-actual table.
- `tests/test_ticket_flow_docs.py` pins each of the above.

## Acceptance conditions

- AC1: task-fields documents formula estimates and run-dir actuals and no longer claims Date.now [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_task_fields_document_formula_estimates_and_run_dir_actuals]
- AC2: tickets.md documents estimate and continue --launch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_tickets_reference_documents_estimate_and_continue_launch]
- AC3: run-handback covers END with continue --launch [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_run_handback_is_end_only_with_continue_launch]
- AC4: phase-4-execute documents the medium-only release and the relaunch scope [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_phase4_documents_medium_only_release_and_relaunch_scope]
- AC5: the gate shows the epic estimate line [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py::test_gate_shows_epic_estimate_line]
- AC6: the skill size, template and generic doc tests still pass [evidence: command:cd plugins/workbench && pytest skills/start-development/tests/test_skill_size.py skills/start-development/tests/test_templates.py skills/start-development/tests/test_start_development_generic.py skills/start-development/tests/test_flow_references_remarks.py -q]

## Files

- `plugins/workbench/skills/start-development/references/task-fields.md`
- `plugins/workbench/skills/start-development/references/tickets.md`
- `plugins/workbench/skills/start-development/references/run-handback.md`
- `plugins/workbench/skills/start-development/references/phase-4-execute.md`
- `plugins/workbench/skills/start-development/SKILL.md`
- `plugins/workbench/skills/start-development/templates/epic.md`
- `plugins/workbench/skills/start-development/templates/record.md`
- `plugins/workbench/skills/start-development/tests/test_ticket_flow_docs.py`

## Interfaces

- Uses `epic-time-line` (estimate-and-actuals) and `continue-launch-lines` (continue-launch): the docs quote their exact line formats.

## Expected outcome

An orchestrator reading the references runs the one-command relaunch, shows the epic estimate at the gate, and knows which escalations need a ruling.

## Steps

- Red: add AC1-AC5 to `skills/start-development/tests/test_ticket_flow_docs.py`; run `cd plugins/workbench && pytest skills/start-development/tests/test_ticket_flow_docs.py -q`; expect failures.
- Green: edit the seven docs.
- Run the task verify; expect all passed.

## Notes

- SKILL.md, run-handback.md, phase-4-execute.md and tickets.md were rewritten by epic integration worktrees (docs-flow-phases, docs-worktree-refs); edit the landed text.
- Quote the line formats from the landed estimate.py and continue_cmd.py, not from this task.
- Docs only plus a doc test: the red step is the doc test.
