---
title: Start-development rewrite
status: in-progress
repo: workbench
value: "The flow document is what every orchestrator session reads; it must describe only the lean loop"
files: [plugins/workbench/skills/start-development/SKILL.md, plugins/workbench/skills/start-development/references/, plugins/workbench/skills/start-development/templates/record.md, plugins/workbench/skills/start-development/tests/, plugins/workbench/agents/record-writer.md, plugins/workbench/README.md, plugins/workbench/.claude-plugin/plugin.json]
verify: "bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run lint"
depends_on: [ticket-lean-tasks, agents-lean-roles]
owns: []
uses: []
model: opus
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Start-development rewrite

## Requirement

Rewrite `start-development` for the lean flow. `SKILL.md` is at most 150 lines and the references directory holds at most seven files; the phase list is: 0 size (lean or full), 1 discovery (optional lenses, each recorded as ran or skipped), 2 design doc, 3 tasks via the planner plus `ticket.py lint` and the builder check (one general-purpose agent on sonnet reads README, design.md and tasks and returns only the questions it still needs answered), THE GATE, 4 execute (invoke `epic-run`, see below; that skill is added by the next task and no test here checks the skill exists), 5 epic review (whole-diff `start-review`, one `scope-auditor`, the one full-suite run, security check when the diff touches that surface), 6 close or merge (`ticket.py close` in meta mode, the MR path in component mode), 7 record.

The gate message: epic README and design.md paths, the project brief, the task table (id, title, value, files, depends_on, model), the lenses that ran or were skipped, the builder check's remaining questions as one numbered batch with a recommended answer each, every irreversible operation, and "Approve, or tell me what to change". Approving the message approves the README goals and every task's acceptance conditions; there is no approval ledger. Everything after the gate runs unattended to merge.

Phase 4 text: the loop that `epic-run` runs, written once here and referenced from that skill: claim the epic (`ticket.py move <epic> in-progress`, which creates the integration tree), then for each task in `ticket.py tasks <epic>` order: dispatch one `workbench:implementer` (model from the task, in the background) with the task file verbatim and the tree path; on return dispatch one `workbench:reviewer`; while it reports unmet ACs or findings, continue the same implementer with SendMessage, then the same reviewer, at most two fix rounds; then `ticket.py task <epic> <task> --status done --verified-head <head>`, or `--status escalated` after the cap with the open findings as the note, and go on with tasks that do not depend on it. The orchestrator plans other epics while dispatches run; it never implements a task itself and never merges a tree itself. After the last task: phases 5 to 7. Rules: a task's `undelivered` entry is a finding, `discovered` becomes a new task in the same epic via `new-task`, `escalated` tasks are judged by the orchestrator (fix with a sharper requirement, or `interrogate` once), and the epic cannot close while a task is not `done`.

References: keep and update `tickets.md` (the lean layout, subcommands, frontmatter, state machines, writer rule; fold `task-fields.md` in), `worktrees.md` (one integration tree per epic), `non-negotiables.md` (half its length; drop plan-execute return fields), `hooks.md` (what the hooks enforce), `merge-hosts.md`, `user-run-steps.md`, `workbench-config.md`. Delete `phase-4-execute.md`, `phases-1-3.md`, `phases-5-7.md`, `run-handback.md`, `approvals.md`, `agents.md`, `builder-check.md`, `mode-flags.md`, `multi-epic.md`, `plan-inputs.md`, `task-fields.md`. `templates/record.md` becomes a short record (what was asked, what shipped, per task: status, verified head, review rounds, verification tail; rulings; what is not pushed) and `agents/record-writer.md` fills it from the task files, git log and the orchestrator's notes with no plan-execute return. Update the plugin `README.md` (flow, agents, scripts, verification sections) and `plugin.json` description. Update `tests/` here (including `test_skill_size.py`, which reads `references/phase-4-execute.md` today) so every doc test pins the lean wording and no test mentions a removed file, command or return field; add a test pinning the deleted references.

## Acceptance conditions

- AC1: SKILL.md has at most 150 lines and `references/` at most seven files, with the eleven named references absent from `git ls-files` [evidence: test:plugins/workbench/skills/start-development/tests/test_lean_flow_docs.py::test_skill_is_lean]
- AC2: SKILL.md names the phases 0 to 7, the gate items, `epic-run`, `ticket.py task`, `SendMessage`, the two-round cap and the sequential dependency order, and contains no `plan-execute`, `Workflow(`, `heartbeat`, `approvals.json`, `verifier`, `forward-merge`, `land`, `rulings` or `apply-run` [evidence: test:plugins/workbench/skills/start-development/tests/test_lean_flow_docs.py::test_skill_describes_lean_loop]
- AC3: outside `tests/` directories (the retirement tests name the retired words on purpose), `grep -rn "plan-execute\|heartbeat\|approvals.json\|apply-run\|forwardMerged\|verify-task" plugins/workbench/skills/start-development plugins/workbench/agents/record-writer.md plugins/workbench/README.md plugins/workbench/.claude-plugin/plugin.json` prints nothing [evidence: command:! grep -rn --exclude-dir=tests "plan-execute\|heartbeat\|approvals.json\|apply-run\|forwardMerged\|verify-task" plugins/workbench/skills/start-development plugins/workbench/agents/record-writer.md plugins/workbench/README.md plugins/workbench/.claude-plugin/plugin.json]
- AC4: `templates/record.md` and record-writer.md mention no plan-execute return (`return value`, `forwardMerged`, `plan-execute`), and record-writer.md names task files and git log as its inputs [evidence: command:! grep -n "return value\|forwardMerged\|plan-execute" plugins/workbench/skills/start-development/templates/record.md plugins/workbench/agents/record-writer.md]
- AC5: `bash plugins/workbench/scripts/run-tests.sh --only start-development` passes [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only start-development]

## Files

- `plugins/workbench/skills/start-development/SKILL.md`
- `plugins/workbench/skills/start-development/references/`
- `plugins/workbench/skills/start-development/templates/record.md`
- `plugins/workbench/skills/start-development/tests/`
- `plugins/workbench/agents/record-writer.md`
- `plugins/workbench/README.md`
- `plugins/workbench/.claude-plugin/plugin.json`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

1. Read the files named under Files and the tests the ACs name; write the new or changed tests first and run them: they must fail for the expected reason.
2. Implement until the targeted verify command passes; keep every existing test green or update it where it pinned removed behaviour.
3. Run the verify command, paste its real tail in the report, commit on the epic branch, leave the tree clean.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
