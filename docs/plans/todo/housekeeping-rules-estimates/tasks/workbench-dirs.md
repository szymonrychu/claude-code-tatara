---
title: Workbench dirs
status: todo
repo: workbench
value: "One resolver gives every tool the main checkout's .scratchpad and .logs, even from an integration tree"
files: [plugins/workbench/scripts/lib/workbench.py, plugins/workbench/scripts/tests/test_workbench_root.py, .gitignore, scripts/tests/test_root_config.py]
verify: "bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only hooks && mise run test:scripts && mise run lint"
depends_on: []
model: sonnet
review: ""
verified_head: ""
---

# Workbench dirs

## Requirement

User requirement (U1, verbatim):

- all scratchpads edits land under `.scratchpad` in workbench root, use it as the only scratchpad dir
- all logs land in gitignored `.logs` in workbench root

Design D6: `plugins/workbench/scripts/lib/workbench.py` gains `main_checkout(start)`: the `WORKBENCH_ROOT` env dir, then `CLAUDE_PROJECT_DIR`, else the parent of the absolute `git rev-parse --git-common-dir` of `start` (for a submodule checkout, the superproject's main checkout); never an integration tree or other linked worktree; None outside git. `scratchpad_dir(start)` and `logs_dir(start)` return `<main checkout>/.scratchpad` and `<main checkout>/.logs`, created on demand. CLI actions `workbench.py scratchpad` and `workbench.py logs` print (and create) the directory, work in an uninitialised template tree (they do not need `find_root`), and exit 1 with a message when no main checkout is found. `.gitignore` gains `.scratchpad/` beside `.logs/`, pinned in scripts/tests/test_root_config.py.

## Acceptance conditions

- AC1: from a linked worktree of a repo (an integration tree), `main_checkout` returns the main checkout, never the worktree [evidence: test:plugins/workbench/scripts/tests/test_workbench_root.py::test_main_checkout_from_linked_worktree]
- AC2: WORKBENCH_ROOT wins over CLAUDE_PROJECT_DIR, which wins over git; a subdirectory resolves to the toplevel; outside git it is None [evidence: test:plugins/workbench/scripts/tests/test_workbench_root.py::test_main_checkout_precedence]
- AC3: `workbench.py scratchpad` and `workbench.py logs` print `<main>/.scratchpad` and `<main>/.logs`, create them, work from a linked worktree and in a tree with no .gitmodules, and exit 1 outside git [evidence: test:plugins/workbench/scripts/tests/test_workbench_root.py::test_scratchpad_and_logs_cli]
- AC4: `.gitignore` lists `.scratchpad/` and `.logs/`, pinned [evidence: test:scripts/tests/test_root_config.py::test_gitignore_base_entries]
- AC5: scripts, hooks and root scripts suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only scripts && bash plugins/workbench/scripts/run-tests.sh --only hooks && mise run test:scripts && mise run lint]

## Files

- `plugins/workbench/scripts/lib/workbench.py`
- `plugins/workbench/scripts/tests/test_workbench_root.py`
- `.gitignore`
- `scripts/tests/test_root_config.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
