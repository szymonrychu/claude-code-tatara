# Lean development flow retro

## Review

Migrated from the epic format.

## What went well

- 5 of 9 tasks passed review in round 0 (remove-workflows, retire-verifier-scripts, ticket-drop-run-commands, ticket-lean-tasks, root-docs-and-rules), each with a quoted tail (e.g. "root 485 passed; lint ok").
- Whole-diff review and scope audit closed with pass: 7 findings fixed in 3370476..8a2c289, every goal and AC delivered; net +2583/-26929 over 37 commits.
- Rulings were explicit with cost-if-wrong: start-review tier dropped to one sonnet reviewer (second opinion via interrogate), lint skips done epics, verifier-table test deletion confirmed to hide no regression.
- epic-run-skill landed in 4 min (est 5, ratio 0.80) and 703360 tokens (ratio 0.94); root-docs-and-rules came in under the token estimate (ratio 0.81).
- Discovered work was recorded, not dropped: the `harness` config key gap is listed in record.md.

## What went wrong or could improve

- 4 of 9 tasks needed one fix round: agents-lean-roles (start-review still dispatched deleted split reviewers), start-development-rewrite (D3 verify-first order and D8 background dispatch missing), epic-run-skill (prompt shapes, reviewer order, weak structure test), skills-wording (epic-move, worktree-create, worktree-merge still described per-task trees). No task hit the 2-round cap or escalated.
- Four of the fix rounds and most epic-level fixes were stale references to retired concepts (per-task trees, split reviewers, new-task flags, refRunners entry, acEvidence); a grep for retired names was not part of the per-task verify.
- retire-verifier-scripts: its verify omitted the root suite, so root test_codex.py stayed pinned to verifier.toml and red for two tasks (fixed fa914ac).
- Estimates were a flat placeholder (1 point, 5-6 min, 750000 tokens per task): MdAPE minutes 81.2%, tokens 74.0%, points not recorded. Worst: remove-workflows 129 min vs 6 (21.50x), retire-verifier-scripts 102 vs 6 (17.00x), start-development-rewrite 25492559 tokens vs 750000 (33.99x), ticket-lean-tasks 12635715 (16.85x).
- Environment friction: the `tatara` venv on PATH shadowed `python` without pytest, so every agent had to drop it from PATH for subprocess tests.
- Old `ticket.py close` on main needed `stage review` and a `review --verdict` first, and its post-fast-forward verify failed on stale ignored pycache under the deleted heartbeat skill that a README test enumerated.

## Recommendations

- Code:
  - plugins/workbench/skills/start-development/scripts/ticket.py: the lint rule skipping done epics is a workaround for old tasks without `verify`; a migrated-epic schema allowance would be cleaner.
  - README skill-enumeration test (root scripts/tests): walks the filesystem, so ignored pycache in another checkout shows a ghost skill; enumerate `git ls-files` instead.
  - plugins/workbench/skills/start-development/references/workbench-config.md: does not document the `harness` config key that `workbench.py` accepts.
- Delivered differently:
  - start-review: design implied tiers (full/panel); delivered one sonnet reviewer for every tier because an existing test forbids naming opus in start-review. Second opinion moved to interrogate.
  - Net deletion of 26929 lines (Workflow runtime, heartbeat, hook-evidence, verify-task.py, triage.py, claude_json.py, estimator, nine ticket.py subcommands, spec-reviewer, quality-reviewer) is far larger than a typical epic; planned estimates (1 point each) did not reflect it.
  - Epic-level fixes (3370476..8a2c289) were needed after the whole-diff review for items no task owned (stale flags, dead branch checks in ticket.py, retired wording).
- Tech debt:
  - Not pushed: main holds the 37 epic commits locally; the user pushes (record.md).
  - `harness` config key undocumented (see Code): remove by documenting it in workbench-config.md.
  - Task Notes sections of all 9 tasks are still template text: the migrated epic carries no per-task decisions; remove by recording rulings with `ticket.py task --note` during future epics.
- Workflow:
  - recurring: unmeasurable estimates (housekeeping-rules-estimates: tasks lacked points and expected minutes/tokens; this epic: flat 1 point, 6 min, 750000 tokens on all 9 tasks, MdAPE 81.2% minutes and 74.0% tokens). Change: `ticket.py lint` should reject identical placeholder estimates across all tasks of an epic, and the planner should size minutes and tokens per task from the retro history deltas.
  - recurring: verification scope not trusted to the implementer's report (housekeeping-rules-estimates: lint tails read before `git add`; this epic: retire-verifier-scripts verify omitted the root suite, two tasks red). Change: `ticket.py lint` requires the root suite in `verify` when `files` lists plugins/workbench/agents/ or scripts/ deletions, and epic-run reviewers rerun the full lint and suites rather than the report.
  - Add a retired-names grep (per-task banned wording from design.md) to each task's verify, so stale references are caught in round 0 instead of fix rounds and the epic-level sweep.

## Delivery record (migrated)

### Asked

Simplify the workbench plugin: the plan-execute Workflow, its verifier scripts, the approval
ledger and the per-task worktrees cost about six agent sessions per task and hours per epic.
Keep what works: planning decoupled from execution, epics and tasks as files, and the reviews
that stop agents from silently narrowing scope. Target: about 2N+3 sessions for N tasks.

### Shipped

The lean loop: one integration tree per epic, one implementer plus one reviewer per task, fix
rounds by continuing the same agents (cap 2), status recorded with `ticket.py task`, one scope
audit per epic, `ticket.py close` then `move done`. Removed: the Workflow runtime, heartbeat,
hook-evidence, verify-task.py, triage.py, claude_json.py, the estimator, nine ticket.py
subcommands, spec-reviewer and quality-reviewer. 37 commits, 212 files, +2583/-26929.
Epic review verdict: pass (one whole-diff reviewer, 7 findings fixed; scope audit: every goal
and AC delivered). Meta mode: no PR; main fast-forwarded to 908e141.

### Tasks

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

### Rulings

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

### Discovered and blocked

- `references/workbench-config.md` does not document the `harness` config key that
  `workbench.py` accepts (not acted on).
- The `tatara` venv on PATH shadows `python` without pytest; every agent had to drop it from
  PATH for subprocess tests (environment, not code).

### Not pushed

main (37 epic commits plus the ticket commits) is committed locally and not pushed; the user
pushes. No branches remain after `move done`.

### Lessons routed to

- A task's `verify` must include every suite its files can break: root `scripts/tests` when a
  plugin agent or script is deleted. Mechanical: `ticket.py lint` could require the root
  suite in `verify` when `files` lists `plugins/workbench/agents/` or `scripts/` deletions.
- Deleting a directory leaves ignored pycache behind in other checkouts and a directory
  enumeration test then sees a ghost skill. Mechanical: the README test should enumerate
  `git ls-files`, not the filesystem.
