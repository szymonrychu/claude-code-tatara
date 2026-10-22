---
title: Audit context and models
status: in-progress
repo: workbench
value: The audit reads task files instead of inlined text and mechanical roles run on haiku
files: [plugins/workbench/workflows/plan-execute.js, plugins/workbench/skills/start-development/scripts/ticket_cmds/args.py, plugins/workbench/skills/start-development/tests/test_ticket_args.py, plugins/workbench/agents/scope-auditor.md, plugins/workbench/workflows/tests/plan-execute-audit-context.test.mjs, plugins/workbench/workflows/tests/plan-execute-epic-audit.test.mjs]
verify: "cd plugins/workbench && pytest skills/start-development/tests/test_ticket_args.py -q && ruff check skills && bash scripts/run-tests.sh --only workflows"
depends_on: [cascade-release]
owns: []
uses: [ac-evidence, land-step, epic-run-args]
model: sonnet
estimate: 6
actual: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/flow-speed-and-token-optimiz--audit-context-and-models
branch: flow-speed-and-token-optimiz--audit-context-and-models
verified_head: ""
run: ""
provides: []
---

# Audit context and models

## Requirement

Give the audit task files instead of inlined requirements and move mechanical roles to haiku (design D11, D12).

- `ticket_cmds/args.py`: every task entry gets `taskFile`, the absolute path of its task file.
- `auditPrompt` and `epicAuditPrompt` in plan-execute.js: when every task has `taskFile`, list per task `- <id>: <title> | tree <worktree> | task file <taskFile>` with the instruction to read each task file's `## Requirement` and `## Acceptance conditions` sections, and inline no requirement text (PLAN_TEXT and the ledger stay). Without `taskFile` the prompts are unchanged. For a 21-task fixture with 900-character requirements the sonnet epic audit prompt is under 10,000 characters.
- Audit split: AC table rows the verifier settled (every AC of the task met with test, symbol, command or doc-section evidence, none with `matchedBy: substring`, the task not in `acsForAudit`) go to one haiku scope-auditor call (`model: 'haiku'`, label `<name>:audit:settled`) that only confirms each row's evidence exists at the landed head. Every other row, the ledger, the ancestry pairs and the duplicate sweep go to the sonnet call. Both results merge (missing lists concatenated, `complete` true only when both are) before `splitAudit`. With no settled rows no haiku call is made.
- `forwardMerge`'s merge agent runs on `model: 'haiku'`.
- The land agent runs on `model: 'haiku'`; a land result that reports a conflict is re-dispatched once on `model: 'sonnet'` before the task ends `land-failed`.
- `plugins/workbench/agents/scope-auditor.md`: a `## Reading task files` section (read the named sections of each task file, never the whole tree of docs) and the settled-rows mode.
- Existing audit tests are updated where they pinned the inlined requirement.

## Acceptance conditions

- AC1: args task entries carry their absolute taskFile path [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_args.py::test_args_tasks_carry_task_file]
- AC2: the epic audit prompt for a 21-task fixture is under 10000 characters [evidence: test:plugins/workbench/workflows/tests/plan-execute-audit-context.test.mjs::epic-audit-prompt-under-10k-for-21-tasks]
- AC3: with task files the audit prompts name the files and inline no requirement [evidence: test:plugins/workbench/workflows/tests/plan-execute-audit-context.test.mjs::audit-reads-task-files-not-inlined-requirements]
- AC4: verifier-settled rows go to one haiku audit call and the rest to sonnet, merged before splitAudit [evidence: test:plugins/workbench/workflows/tests/plan-execute-audit-context.test.mjs::settled-rows-go-to-one-haiku-audit]
- AC5: the forward-merge agent runs on haiku [evidence: test:plugins/workbench/workflows/tests/plan-execute-audit-context.test.mjs::forward-merge-runs-on-haiku]
- AC6: the land agent runs on haiku and a conflict is retried once on sonnet [evidence: test:plugins/workbench/workflows/tests/plan-execute-audit-context.test.mjs::land-runs-on-haiku-and-retries-conflict-on-sonnet]
- AC7: the scope auditor documents reading task files [evidence: doc-section:plugins/workbench/agents/scope-auditor.md#Reading task files]

## Files

- `plugins/workbench/workflows/plan-execute.js`
- `plugins/workbench/skills/start-development/scripts/ticket_cmds/args.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_args.py`
- `plugins/workbench/agents/scope-auditor.md`
- `plugins/workbench/workflows/tests/plan-execute-audit-context.test.mjs`
- `plugins/workbench/workflows/tests/plan-execute-epic-audit.test.mjs`

## Interfaces

- Uses `ac-evidence` (ac-evidence-map): `matchedBy` per AC decides a settled row.
- Uses `land-step` (epic integration worktrees): the land agent dispatch whose model changes.
- Uses `epic-run-args` (epic integration worktrees): `build_args` in `ticket_cmds/args.py`, which gains `taskFile`.

## Expected outcome

The epic audit reads a short prompt and the task files it needs, the mechanical checks run on haiku, and review and judgement rows stay on sonnet.

## Steps

- Red: write `workflows/tests/plan-execute-audit-context.test.mjs` (AC2-AC6) and add AC1 to `skills/start-development/tests/test_ticket_args.py`; run both; expect failures.
- Green: `taskFile` in args.py, the audit prompts and split, the two model changes, the scope-auditor section; update `plan-execute-epic-audit.test.mjs`.
- Run the task verify; expect all green.

## Notes

- Measured: one epic audit was 7.5M raw tokens with every requirement inlined (brief item 10).
- `acTable()` already marks rows `verifier settled` or `open: judge it`; reuse that split.
- args.py and the land step were changed by epic integration worktrees; read the landed code first.
