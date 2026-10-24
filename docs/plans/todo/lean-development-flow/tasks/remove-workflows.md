---
title: Remove workflows
status: todo
repo: workbench
value: Deletes the 12k-line Workflow runtime that every other simplification depends on
files: [plugins/workbench/workflows/, plugins/workbench/skills/heartbeat/, plugins/workbench/scripts/hook-evidence.py, plugins/workbench/scripts/tests/, scripts/harness/fallbacks/, scripts/harness/skills_emit.py, scripts/tests/, plugins/workbench/scripts/run-tests.sh]
verify: "pytest scripts/tests -m \"not slow\" -q && mise run lint && bash plugins/workbench/scripts/run-tests.sh"
depends_on: []
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

# Remove workflows

## Requirement

Remove the Workflow runtime and everything that exists only to drive or watch it. Delete `plugins/workbench/workflows/` entirely (plan-execute.js, named-copy.mjs, hook-probe.js, validate-tasks.mjs, ac-lint.mjs, tests/ including harness.mjs), the `heartbeat` skill (`plugins/workbench/skills/heartbeat/`), `plugins/workbench/scripts/hook-evidence.py` and its tests, and the `plan-execute` harness fallback (`scripts/harness/fallbacks/plan-execute/`). In `scripts/harness/skills_emit.py` remove the `CLAUDE_ONLY` set and every rewrite rule that exists for Workflow, plan-execute, heartbeat or Monitor wording; the emitter keeps working for the remaining skills. Update the root tests that enumerate the removed paths (`scripts/tests/test_config_dir_literals.py`, `test_root_config.py`, `test_builtin_worktree_guard.py`, `scripts/tests/harness/`) and remove the workflows branch from `plugins/workbench/scripts/run-tests.sh`. Add a retirement test that pins the removal with `git ls-files`. Do not reword docs or skills and do not touch ticket.py: later tasks own those.

## Acceptance conditions

- AC1: `git ls-files plugins/workbench/workflows plugins/workbench/skills/heartbeat plugins/workbench/scripts/hook-evidence.py scripts/harness/fallbacks/plan-execute` prints nothing [evidence: command:git ls-files plugins/workbench/workflows plugins/workbench/skills/heartbeat plugins/workbench/scripts/hook-evidence.py scripts/harness/fallbacks/plan-execute]
- AC2: a retirement test asserts AC1 with git ls-files, never the filesystem [evidence: test:scripts/tests/test_retired_workflow.py::test_workflow_runtime_retired]
- AC3: `scripts/harness/skills_emit.py` has no CLAUDE_ONLY set and no rewrite rule mentioning Workflow, plan-execute, heartbeat or Monitor; `grep -n "plan-execute\|heartbeat\|CLAUDE_ONLY\|Workflow" scripts/harness/skills_emit.py` prints nothing [evidence: command:grep -c "plan-execute\|heartbeat\|CLAUDE_ONLY\|Workflow" scripts/harness/skills_emit.py]
- AC4: `bash plugins/workbench/scripts/run-tests.sh` runs every remaining component and ends with `all green` [evidence: command:bash plugins/workbench/scripts/run-tests.sh]
- AC5: `pytest scripts/tests -m "not slow" -q` and `mise run lint` pass [evidence: command:pytest scripts/tests -m "not slow" -q]

## Files

- `plugins/workbench/workflows/`
- `plugins/workbench/skills/heartbeat/`
- `plugins/workbench/scripts/hook-evidence.py`
- `plugins/workbench/scripts/tests/`
- `scripts/harness/fallbacks/`
- `scripts/harness/skills_emit.py`
- `scripts/tests/`
- `plugins/workbench/scripts/run-tests.sh`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
