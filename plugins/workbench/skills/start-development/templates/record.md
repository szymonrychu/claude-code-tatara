# <Topic> record

## Summary

What was asked, what shipped, and the verdict in 3-6 lines.

## Planned vs built

Table: task, status, review rounds, continuations, files, verifier head SHA, verification tail. Filled from the files and test output, not from agent summaries. Then an approvals table: id, text, decisions, tasks, status (delivered, blocked: who can clear it, escalated), from the run's approvals return value.

A `tdd-revert` result is never quoted as TDD red evidence: `verify-task.py:343-366` restores every non-test file to base at once, so any new test importing new code fails trivially. The red evidence quoted is the implementer's own `tests.red` run.

## Deviations and rulings

One entry per deviation or orchestrator ruling: what, why, and the cost if the call was wrong.

## Duplicates reconciled

Parts built twice or overlapping across tasks, and which one was kept; "none" if none.

## Discovered and blocked

Each item named, with the blocker and who can clear it.

## Research that changed the plan

Findings that altered a decision or a task, with the citation and the change it caused.

## Cost

Agents by role, continuations, audits, and wall-clock. Then a table of estimate vs actual minutes per task (`estimate` and `actual` from the task files) with the README `Time` totals; report only, never a budget.

## MRs and deploy

MR or PR URLs, pipeline state, merge state, and deploy confirmation.

## Lessons routed to

Each lesson names the check to add (a test, hook or lint rule) when the violation is mechanical, and the skill or rule to edit only when it is a judgement call.
