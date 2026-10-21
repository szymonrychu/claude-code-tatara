---
title: Integration tree create
status: in-progress
repo: workbench
value: "Claiming an epic gives it its own integration worktree, the base every task forks from"
files: [plugins/workbench/skills/worktree-create/scripts/create.py, plugins/workbench/skills/worktree-create/tests/test_create.py, plugins/workbench/skills/worktree-create/tests/test_fast_forward.py, plugins/workbench/skills/start-development/scripts/ticket.py, plugins/workbench/skills/start-development/tests/test_ticket_integration.py, plugins/workbench/skills/start-development/tests/test_ticket_move.py, plugins/workbench/skills/worktree-create/SKILL.md, plugins/workbench/skills/epic-move/SKILL.md]
verify: "mise run test && mise run lint"
depends_on: [name-lookup-parsers]
owns: [integration-tree]
uses: []
model: sonnet
estimate: 75
actual: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/epic-integration-worktrees--integration-tree-create
branch: epic-integration-worktrees--integration-tree-create
verified_head: ""
run: ""
provides: []
---

# Integration tree create

## Requirement

Create the epic integration worktree when the epic is claimed (user decision U2, design D2, D8).

- `plugins/workbench/skills/worktree-create/scripts/create.py` gains `integration(epic, base="main", repo=None, start=None) -> dict` returning `{name, path, branch, base, verb, notes}` with `verb` `created` or `reused`. Destination: `worktrees_dir(root) / epic`, plus `/ repo` in component mode. When the destination is already a linked worktree of the source checkout on branch `<epic>` it is reused unchanged. When it exists as anything else the call raises `WorktreeError` naming the path. When branch `<epic>` exists, `git worktree add <dest> <epic>` reuses it. Otherwise `git worktree add -b <epic> <dest> <start>`, where `<start>` is `base` in meta mode, and in component mode `origin/<base>` when that ref resolves, else `base`. Never `--force`. CLI: `create.py --integration --name <epic> [--base main] [--repo <repo>]` prints the path, branch, base and verb.
- `ticket.py` gains `integration_trees(root, epic_dir) -> dict[str, Path]` (key `""` for the superrepo, else the repo name) and `integration_branch(epic) -> str` (the epic slug); the only place integration paths are computed.
- The claim step is one function, `ensure_integration_trees(root, epic_dir) -> list[dict]`, which returns one `integration()` result per tree. `move in-progress` calls it, and epic-base-wiring's `ticket.py worktrees <epic> --integration` reuses it for epics claimed before this change (interrogate verdict F, design D13).
- `ticket.py move <epic> in-progress`, after the blocker and check gates and before the move: the repos in scope are the README `repos` that name a `code/<repo>` submodule plus every task repo that does (`_task_repo`). With no such repo it is meta mode: one superrepo tree forked from `main`. With such repos and no task outside them it is component mode: one tree per repo, forked from that submodule's tracked branch (`.gitmodules` `submodule.<repo>.branch`, default `main`). An epic with tasks in both refuses: `epic <epic> mixes meta and component tasks; split it into two epics`. Each tree prints one line `integration <path> (<verb>)`. A creation failure exits 1, the epic stays in todo, and nothing is committed. Running the claim again reuses whatever was already created. Outside a git checkout no tree is made and the move proceeds as today.
- `plugins/workbench/skills/worktree-create/SKILL.md` documents `--integration`; `plugins/workbench/skills/epic-move/SKILL.md` says the claim creates the integration tree.
- Existing move tests in test_ticket_move.py are adapted only where the new tree changes what they observe.
- `create.fast_forward` is pinned against a non-main base (the epic branch) in `worktree-create/tests/test_fast_forward.py:37-74`.

## Acceptance conditions

- AC1: integration() creates the meta tree on branch epic from main [evidence: test:plugins/workbench/skills/worktree-create/tests/test_create.py::test_integration_creates_meta_tree]
- AC2: integration() reuses an existing tree and an existing branch without -b [evidence: test:plugins/workbench/skills/worktree-create/tests/test_create.py::test_integration_reuses_tree_and_branch]
- AC3: integration() in component mode forks from origin of the tracked branch when it exists, else the local branch [evidence: test:plugins/workbench/skills/worktree-create/tests/test_create.py::test_integration_component_forks_tracked_branch]
- AC4: move in-progress creates the meta integration tree and prints its line [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_integration.py::test_claim_creates_meta_integration_tree]
- AC5: move in-progress creates one tree per component repo under the epic directory [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_integration.py::test_claim_creates_component_trees]
- AC6: move in-progress refuses an epic mixing meta and component tasks [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_integration.py::test_claim_refuses_mixed_epic]
- AC7: a creation failure leaves the epic in todo with nothing committed, and a second claim reuses the tree [evidence: test:plugins/workbench/skills/start-development/tests/test_ticket_integration.py::test_claim_failure_moves_nothing_and_retry_reuses]
- AC8: the worktree-create skill documents the integration flag [evidence: command:grep -q -- '--integration' plugins/workbench/skills/worktree-create/SKILL.md]
- AC9: fast_forward updates a tree behind a non-main base such as the epic branch [evidence: test:plugins/workbench/skills/worktree-create/tests/test_fast_forward.py::test_fast_forward_against_epic_base]
- AC10: the claim step is the one reusable function ensure_integration_trees [evidence: symbol:plugins/workbench/skills/start-development/scripts/ticket.py::ensure_integration_trees]

## Files

- `plugins/workbench/skills/worktree-create/scripts/create.py`
- `plugins/workbench/skills/worktree-create/tests/test_create.py`
- `plugins/workbench/skills/worktree-create/tests/test_fast_forward.py`
- `plugins/workbench/skills/start-development/scripts/ticket.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_integration.py`
- `plugins/workbench/skills/start-development/tests/test_ticket_move.py`
- `plugins/workbench/skills/worktree-create/SKILL.md`
- `plugins/workbench/skills/epic-move/SKILL.md`

## Interfaces

- `create.integration(epic: str, base: str = "main", repo: str | None = None, start: Path | None = None) -> dict` (new; the `integration-tree` part).
- `ticket.integration_trees(root: Path, epic_dir: Path) -> dict[str, Path]` and `ticket.integration_branch(epic: str) -> str` (new; consumed by epic-base-wiring and epic-close-sweep).
- `ticket.ensure_integration_trees(root: Path, epic_dir: Path) -> list[dict]` (new; the claim step, consumed by epic-base-wiring's `worktrees --integration`).

## Expected outcome

After `ticket.py move <epic> in-progress`, `git worktree list` shows `<configdir>/worktrees/<epic>` on `[<epic>]` (meta) or `<configdir>/worktrees/<epic>/<repo>` per repo (component), and a rerun of the claim on a half-created epic is safe.

## Steps

- Red: add the three integration tests to `plugins/workbench/skills/worktree-create/tests/test_create.py` and write `plugins/workbench/skills/start-development/tests/test_ticket_integration.py`; run `cd plugins/workbench && pytest skills/worktree-create/tests/test_create.py skills/start-development/tests/test_ticket_integration.py -q` (separately if the module names clash); expect failures.
- Green: implement `integration()` and the CLI flag, then the claim step in `_move_in_progress`.
- Run `cd plugins/workbench && bash scripts/run-tests.sh --only worktree-create && bash scripts/run-tests.sh --only start-development`, then `mise run test && mise run lint` from the root.

## Notes

- Reuse `create.branch_exists`, `create.workbench_root`, `ticket._task_repo`, `ticket._linked_worktrees`.
- Create the trees before `_git_mv` so a failure moves nothing; the claim stays idempotent because existing trees and branches are reused.
- The integration tree sits beside task trees `<epic>-<task>` under `<configdir>/worktrees/`; `create.validate_name` already refuses a duplicate name.
- Plain `git worktree add` gets no Claude Code marker, so the built-in sweep never removes it (design D1).
