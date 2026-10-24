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

- `workbench.main_checkout(start: Path | None = None) -> Path | None`
- `workbench.scratchpad_dir(start: Path | None = None) -> Path | None`, `workbench.logs_dir(start: Path | None = None) -> Path | None` (mkdir parents, exist_ok)
- CLI: `python3 plugins/workbench/scripts/lib/workbench.py scratchpad|logs [--from DIR]`

## Expected outcome

Every caller (hooks, ticket.py, scripts, skills) resolves the one `.scratchpad` and `.logs` of the main checkout from anywhere, including an integration tree.

## Steps

1. List the files under Files, read them in one pass; write AC1-AC4 tests (clear WORKBENCH_ROOT and CLAUDE_PROJECT_DIR with monkeypatch in every test, the suite may run inside a Claude session) and run them: they fail.
2. Implement; add `.scratchpad/` to .gitignore; run the verify once.
3. Commit; leave the tree clean.

## Notes

- Estimate: 3 points.
- Reuse (brief): workbench.py:find_root (65) honours WORKBENCH_ROOT and CLAUDE_PROJECT_DIR first; hooks import workbench through hooks/worktree_lib.py:16. Do-not-build: a new root resolver in hooks.
- Fix-as-ac (brief): an integration tree is a superrepo checkout, so it can pass `_is_metarepo` (workbench.py:45) and find_root(cwd) would return the tree; `main_checkout` uses the git common dir instead (AC1).
- Do-not-build: a new `.logs/` ignore entry; .gitignore:18 already has it, pinned by test_root_config.py:40. Only `.scratchpad/` is new.
- This template repo is uninitialised (`workbench.py root` prints "kind: none"), so `main_checkout` must not depend on detect_kind.
