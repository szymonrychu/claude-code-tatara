# Lean development flow record

## Asked

Simplify the workbench plugin: the plan-execute Workflow, its verifier scripts, the approval
ledger and the per-task worktrees cost about six agent sessions per task and hours per epic.
Keep what works: planning decoupled from execution, epics and tasks as files, and the reviews
that stop agents from silently narrowing scope. Target: about 2N+3 sessions for N tasks.

## Shipped

The lean loop: one integration tree per epic, one implementer plus one reviewer per task, fix
rounds by continuing the same agents (cap 2), status recorded with `ticket.py task`, one scope
audit per epic, `ticket.py close` then `move done`. Removed: the Workflow runtime, heartbeat,
hook-evidence, verify-task.py, triage.py, claude_json.py, the estimator, nine ticket.py
subcommands, spec-reviewer and quality-reviewer. 37 commits, 212 files, +2583/-26929.
Epic review verdict: pass (one whole-diff reviewer, 7 findings fixed; scope audit: every goal
and AC delivered). Meta mode: no PR; main fast-forwarded to 908e141.

## Tasks

| Task | Status | Verified head | Rounds | Verification tail |
|---|---|---|---|---|
| remove-workflows | done | 6f72ab7 | 0 | root 485 passed; lint ok; plugin 25 components 2172 assertions all green |
| retire-verifier-scripts | done | 9423065 | 0 (+1 follow-up: root test_codex.py pinned verifier.toml, fixed fa914ac) | scripts 146 passed; test_release 12 passed; lint ok |
| ticket-drop-run-commands | done | 31559e5 | 0 | start-development 376 passed; scripts 129 passed; lint ok |
| ticket-lean-tasks | done | 1b76c81 | 0 | start-development 361 passed; lint ok; six named AC tests pass |
| agents-lean-roles | done | b79edfd | 1 (start-review still dispatched deleted split reviewers) | start-review 28, start-research 71 passed; lint ok; plugin 1813 assertions all green |
| start-development-rewrite | done | 06d6a93 | 1 (D3 verify-first order and D8 background dispatch not stated) | start-development 343 passed; root 485 passed; lint ok |
| epic-run-skill | done | de33424 | 1 (prompt shapes, reviewer order, weak structure test) | epic-run 2, start-research 66 assertions all green; lint ok |
| skills-wording | done | 606b059 | 1 (epic-move, worktree-create, worktree-merge still described per-task trees) | plugin 26 components 1794 assertions all green |
| root-docs-and-rules | done | 8990c8e | 0 | root 486 passed; lint ok; harness-setup leaves the tree unchanged |

Epic-level fixes after the whole-diff review and scope audit: 3370476..8a2c289 (stale
new-task flags in epic-task-create, stale refRunners entry, epic-run skips done tasks, one
report cap per role, dangling acEvidence field, dead per-task branch checks in ticket.py,
retired wording in reviewer.md and templates/task.md). Final: plugin 1797 assertions, root 486
passed, lint ok.

## Rulings

- retire-verifier-scripts verify command did not include the root suite, so a root test
  pinned to verifier.toml stayed red for two tasks. Fixed as a follow-up on the same
  implementer; cost if wrong: none, one-line test change.
- ticket-drop-run-commands deleted `test_verifier_table_row_names_haiku`, already red since
  the verifier retirement; the reviewer confirmed it hid no regression.
- start-review full/panel tier dropped (one sonnet reviewer for every tier, second opinion
  via interrogate), because an existing test forbids naming opus in start-review. Cost if
  wrong: a high-risk diff gets one reviewer; interrogate remains available.
- lint content rules skip done epics (an old done epic has a task without `verify`). Cost if
  wrong: none for live epics.
- The old `ticket.py close` on main needed `stage review` and a `review --verdict` first;
  both recorded. Its post-fast-forward verify failed on main only because the main checkout
  kept ignored pycache files under the deleted heartbeat skill, which a README test
  enumerates; removed, main re-verified.

## Discovered and blocked

- `references/workbench-config.md` does not document the `harness` config key that
  `workbench.py` accepts (not acted on).
- The `tatara` venv on PATH shadows `python` without pytest; every agent had to drop it from
  PATH for subprocess tests (environment, not code).

## Not pushed

main (37 epic commits plus the ticket commits) is committed locally and not pushed; the user
pushes. No branches remain after `move done`.

## Lessons routed to

- A task's `verify` must include every suite its files can break: root `scripts/tests` when a
  plugin agent or script is deleted. Mechanical: `ticket.py lint` could require the root
  suite in `verify` when `files` lists `plugins/workbench/agents/` or `scripts/` deletions.
- Deleting a directory leaves ignored pycache behind in other checkouts and a directory
  enumeration test then sees a ghost skill. Mechanical: the README test should enumerate
  `git ls-files`, not the filesystem.
