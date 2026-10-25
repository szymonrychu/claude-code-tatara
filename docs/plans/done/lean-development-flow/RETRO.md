# Lean development flow retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| Remove workflows | 1 | not recorded | 6 | 129 | 750000 | 4103204 |
| Retire verifier scripts | 1 | not recorded | 6 | 102 | 750000 | 749173 |
| Ticket drop run commands | 1 | not recorded | 6 | 20 | 750000 | 2889785 |
| Ticket lean tasks | 1 | not recorded | 6 | 32 | 750000 | 12635715 |
| Agents lean roles | 1 | not recorded | 6 | 40 | 750000 | 6075082 |
| Start-development rewrite | 1 | not recorded | 6 | 58 | 750000 | 25492559 |
| Epic-run skill | 1 | not recorded | 5 | 4 | 750000 | 703360 |
| Skills wording | 1 | not recorded | 6 | 31 | 750000 | 860510 |
| Root docs and rules | 1 | not recorded | 6 | 16 | 750000 | 608440 |
| Total | 9 | not recorded | 53 | 432 | 6750000 | 54117828 |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| Remove workflows | not recorded | 21.50 | 5.47 |
| Retire verifier scripts | not recorded | 17.00 | 1.00 |
| Ticket drop run commands | not recorded | 3.33 | 3.85 |
| Ticket lean tasks | not recorded | 5.33 | 16.85 |
| Agents lean roles | not recorded | 6.67 | 8.10 |
| Start-development rewrite | not recorded | 9.67 | 33.99 |
| Epic-run skill | not recorded | 0.80 | 0.94 |
| Skills wording | not recorded | 5.17 | 1.15 |
| Root docs and rules | not recorded | 2.67 | 0.81 |

- MdAPE points: not recorded
- MdAPE minutes: 81.2%
- MdAPE tokens: 74.0%
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| 5 of 9 tasks passed review in round 0 (remove-workflows, retire-verifier-scripts, ticket-drop-run-commands, ticket-lean-tasks, root-docs-and-rules), each with a quoted tail (e.g. "root 485 passed; lint ok"). | 4 of 9 tasks needed one fix round: agents-lean-roles (start-review still dispatched deleted split reviewers), start-development-rewrite (D3 verify-first order and D8 background dispatch missing), epic-run-skill (prompt shapes, reviewer order, weak structure test), skills-wording (epic-move, worktree-create, worktree-merge still described per-task trees). No task hit the 2-round cap or escalated. |
| Whole-diff review and scope audit closed with pass: 7 findings fixed in 3370476..8a2c289, every goal and AC delivered; net +2583/-26929 over 37 commits. | Four of the fix rounds and most epic-level fixes were stale references to retired concepts (per-task trees, split reviewers, new-task flags, refRunners entry, acEvidence); a grep for retired names was not part of the per-task verify. |
| Rulings were explicit with cost-if-wrong: start-review tier dropped to one sonnet reviewer (second opinion via interrogate), lint skips done epics, verifier-table test deletion confirmed to hide no regression. | retire-verifier-scripts: its verify omitted the root suite, so root test_codex.py stayed pinned to verifier.toml and red for two tasks (fixed fa914ac). |
| epic-run-skill landed in 4 min (est 5, ratio 0.80) and 703360 tokens (ratio 0.94); root-docs-and-rules came in under the token estimate (ratio 0.81). | Estimates were a flat placeholder (1 point, 5-6 min, 750000 tokens per task): MdAPE minutes 81.2%, tokens 74.0%, points not recorded. Worst: remove-workflows 129 min vs 6 (21.50x), retire-verifier-scripts 102 vs 6 (17.00x), start-development-rewrite 25492559 tokens vs 750000 (33.99x), ticket-lean-tasks 12635715 (16.85x). |
| Discovered work was recorded, not dropped: the `harness` config key gap is listed in record.md. | Environment friction: the `tatara` venv on PATH shadowed `python` without pytest, so every agent had to drop it from PATH for subprocess tests. |
| | Old `ticket.py close` on main needed `stage review` and a `review --verdict` first, and its post-fast-forward verify failed on stale ignored pycache under the deleted heartbeat skill that a README test enumerated. |

## Improvements

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
