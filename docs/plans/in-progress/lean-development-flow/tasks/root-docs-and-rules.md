---
title: Root docs and rules
status: in-progress
repo: workbench
value: "AGENTS.md is loaded into every session; a stale rule 1 would send agents back to a deleted workflow"
files: [AGENTS.md, CLAUDE.md, README.md, docs/architecture.md, docs/harnesses.md, docs/enterprise.md, scripts/tests/]
verify: "pytest scripts/tests -m \"not slow\" -q && mise run lint"
depends_on: [skills-wording]
owns: []
uses: []
model: sonnet
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

# Root docs and rules

## Requirement

Bring the root documents and their tests to the lean flow. `AGENTS.md`: ground rule 1 says implementation goes through `epic-run` (one implementer and one reviewer per task, two fix rounds, one scope audit per epic) and never hand-rolled beyond that; ground rule 4 drops the heartbeat sentence and keeps the 10-minute bound with the background Agent notification as the wake signal; the Claude-only block in `CLAUDE.md` drops the plan-execute and heartbeat lines and says `epic-run` dispatches agents in the background. Root `README.md`: "The autonomous run to merge" describes epic-run, "Parallel epics, background runs, heartbeats" becomes "Parallel epics and background runs" without the heartbeat skill, "Resume after an escalation" names `ticket.py task` and `epic-run`. `docs/architecture.md` and `docs/harnesses.md`: remove the Workflow row and the plan-execute fallback paragraphs; other harnesses run the same loop with their own subagent facility. `docs/enterprise.md` only if a reference remains after retire-verifier-scripts. Regenerate the rules block with `mise run harness-setup` after `concise-orchestrator.md` changed (skills-wording task) and commit the regenerated output. Update `scripts/tests/test_agents_md.py`, `scripts/tests/init_engine/test_project_files.py` and `scripts/tests/harness/fixtures/tree/AGENTS.md` so they pin the new wording; the init engine must still produce an AGENTS.md whose ground rules match this one. No other root file changes.

## Acceptance conditions

- AC1: `grep -rniE "plan-execute|heartbeat|Workflow tool|Workflow scripts|approval ledger" AGENTS.md CLAUDE.md README.md docs/architecture.md docs/harnesses.md docs/enterprise.md` prints nothing [evidence: command:! grep -rniE "plan-execute|heartbeat|Workflow tool|Workflow scripts|approval ledger" AGENTS.md CLAUDE.md README.md docs/architecture.md docs/harnesses.md docs/enterprise.md]
- AC2: AGENTS.md ground rule 1 names `epic-run`, one implementer and one reviewer per task, two fix rounds and one scope audit per epic [evidence: test:scripts/tests/test_agents_md.py::test_ground_rule_one_names_epic_run]
- AC3: after the task's commit, `mise run harness-setup` leaves the tree unchanged (the generated block is committed) [evidence: command:mise run harness-setup && git status --porcelain]
- AC4: `pytest scripts/tests -m "not slow" -q` and `mise run lint` pass [evidence: command:pytest scripts/tests -m "not slow" -q]

## Files

- `AGENTS.md`
- `CLAUDE.md`
- `README.md`
- `docs/architecture.md`
- `docs/harnesses.md`
- `docs/enterprise.md`
- `scripts/tests/`

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
