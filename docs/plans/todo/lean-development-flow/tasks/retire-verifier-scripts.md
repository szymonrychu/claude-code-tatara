---
title: Retire verifier scripts
status: todo
repo: workbench
value: "Removes 2500 lines of verifier, triage and claude -p plumbing the lean reviewer replaces"
files: [plugins/workbench/scripts/verify-task.py, plugins/workbench/scripts/triage.py, plugins/workbench/scripts/lib/claude_json.py, plugins/workbench/scripts/tests/, plugins/workbench/agents/verifier.md, plugins/workbench/README.md, docs/enterprise.md, plugins/workbench/skills/start-development/tests/test_release.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only scripts && pytest plugins/workbench/skills/start-development/tests/test_release.py -q && mise run lint"
depends_on: [remove-workflows]
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

# Retire verifier scripts

## Requirement

Retire the independent-verifier tooling that only the plan-execute run called. Delete `plugins/workbench/scripts/verify-task.py`, `plugins/workbench/scripts/triage.py`, `plugins/workbench/scripts/lib/claude_json.py` and their tests and fixtures (`test_verify_task.py`, `test_verify_bounded.py`, `test_triage.py`, `test_claude_json.py`, `fixtures/`), and `plugins/workbench/agents/verifier.md`. Remove the `claude_json` and `verify-task`/`triage` rows from the plugin README script table and from `docs/enterprise.md`, and fix `plugins/workbench/skills/start-development/tests/test_release.py` where it pins those names. The reviewer agent (rewritten in a later task) takes over running the verify command on HEAD and checking acceptance conditions; nothing here replaces the scripts with new code. Add a retirement test with `git ls-files`. Leave estimator.py alone: the ticket task removes it.

## Acceptance conditions

- AC1: `git ls-files plugins/workbench/scripts/verify-task.py plugins/workbench/scripts/triage.py plugins/workbench/scripts/lib/claude_json.py plugins/workbench/agents/verifier.md plugins/workbench/scripts/tests/fixtures` prints nothing [evidence: command:git ls-files plugins/workbench/scripts/verify-task.py plugins/workbench/scripts/triage.py plugins/workbench/scripts/lib/claude_json.py plugins/workbench/agents/verifier.md plugins/workbench/scripts/tests/fixtures]
- AC2: a retirement test asserts AC1 with git ls-files [evidence: test:plugins/workbench/scripts/tests/test_retired_verifier.py::test_verifier_tooling_retired]
- AC3: `grep -rn "claude_json\|verify-task\|triage.py" plugins/workbench/README.md docs/enterprise.md` prints nothing [evidence: command:grep -rc "claude_json\|verify-task\|triage.py" plugins/workbench/README.md docs/enterprise.md]
- AC4: `bash plugins/workbench/scripts/run-tests.sh --only scripts` and `pytest plugins/workbench/skills/start-development/tests/test_release.py -q` pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only scripts]

## Files

- `plugins/workbench/scripts/verify-task.py`
- `plugins/workbench/scripts/triage.py`
- `plugins/workbench/scripts/lib/claude_json.py`
- `plugins/workbench/scripts/tests/`
- `plugins/workbench/agents/verifier.md`
- `plugins/workbench/README.md`
- `docs/enterprise.md`
- `plugins/workbench/skills/start-development/tests/test_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
