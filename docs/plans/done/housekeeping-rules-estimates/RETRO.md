# Housekeeping rules, estimates and retrospectives retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| Calibration lib | 5 | 5 | not recorded | 11 | not recorded | 388955 |
| Em dash lint | 2 | 2 | not recorded | 18 | not recorded | 426098 |
| Workbench dirs | 3 | 3 | not recorded | 16 | not recorded | 451351 |
| Em dash edit guard | 5 | 5 | not recorded | 34 | not recorded | 1414237 |
| Estimate fields | 5 | 5 | not recorded | 15 | not recorded | 2032100 |
| Housekeeping rules | 3 | 3 | not recorded | 23 | not recorded | 1105466 |
| Test logs dir | 2 | 2 | not recorded | 4 | not recorded | 538938 |
| Agent discipline | 2 | 2 | not recorded | 14 | not recorded | 691774 |
| Em dash commit guard | 3 | 3 | not recorded | 28 | not recorded | 631476 |
| Plugin readme rules | 1 | 1 | not recorded | 14 | not recorded | 353749 |
| Points required | 3 | 3 | not recorded | 14 | not recorded | 1108799 |
| Output spill to logs | 3 | 3 | not recorded | 24 | not recorded | 1148960 |
| Agent usage lib | 5 | 5 | not recorded | 15 | not recorded | 1204508 |
| Scratch locations | 3 | 3 | not recorded | 45 | not recorded | 723362 |
| Agent usage hook | 5 | 5 | not recorded | 29 | not recorded | 1836811 |
| Planner points gate | 2 | 2 | not recorded | 15 | not recorded | 559738 |
| Run marker points | 2 | 2 | not recorded | 5 | not recorded | 299770 |
| Stamp actuals | 5 | 5 | not recorded | 12 | not recorded | 2552072 |
| Actuals backfill | 2 | 2 | not recorded | 21 | not recorded | 2632742 |
| Retro command | 8 | 8 | not recorded | 16 | not recorded | 3112607 |
| Deltas command | 5 | 5 | not recorded | 16 | not recorded | 2043374 |
| Retro writer | 5 | 3 | not recorded | 16 | not recorded | 1883475 |
| Plugin readme commands | 1 | 1 | not recorded | 11 | not recorded | 452093 |
| Review seams | 2 | 2 | not recorded | 7 | not recorded | 531208 |
| Total | 82 | 80 | not recorded | 423 | not recorded | 28123663 |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| Calibration lib | 0 | not recorded | not recorded |
| Em dash lint | 0 | not recorded | not recorded |
| Workbench dirs | 0 | not recorded | not recorded |
| Em dash edit guard | 0 | not recorded | not recorded |
| Estimate fields | 0 | not recorded | not recorded |
| Housekeeping rules | 0 | not recorded | not recorded |
| Test logs dir | 0 | not recorded | not recorded |
| Agent discipline | 0 | not recorded | not recorded |
| Em dash commit guard | 0 | not recorded | not recorded |
| Plugin readme rules | 0 | not recorded | not recorded |
| Points required | 0 | not recorded | not recorded |
| Output spill to logs | 0 | not recorded | not recorded |
| Agent usage lib | 0 | not recorded | not recorded |
| Scratch locations | 0 | not recorded | not recorded |
| Agent usage hook | 0 | not recorded | not recorded |
| Planner points gate | 0 | not recorded | not recorded |
| Run marker points | 0 | not recorded | not recorded |
| Stamp actuals | 0 | not recorded | not recorded |
| Actuals backfill | 0 | not recorded | not recorded |
| Retro command | 0 | not recorded | not recorded |
| Deltas command | 0 | not recorded | not recorded |
| Retro writer | -2 | not recorded | not recorded |
| Plugin readme commands | 0 | not recorded | not recorded |
| Review seams | 0 | not recorded | not recorded |

- MdAPE points: 0.0%
- MdAPE minutes: not recorded
- MdAPE tokens: not recorded
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| 17 of 24 tasks passed review in round 0, with a verification tail quoted per task (e.g. calibration-lib, em-dash-lint, retro-command). | 7 of 24 tasks needed one fix round per the notes (em-dash-commit-guard, output-spill-to-logs, agent-usage-lib, planner-points-gate, actuals-backfill, retro-writer, plugin-readme-commands); three were false greens from a tail read or a pre-`git add` run. |
| Real-run checks by reviewers caught bugs tests missed: actuals-backfill (default transcripts dir derived from the plans root, 0 records; real run then found 38) and plugin-readme-commands (README span was not a real invocation). | agent-usage-lib: implementer reported lint green from a tail read; lint:config-dir was red on a literal path (fixed f34227b). |
| No task ended with a points delta except retro-writer (-2, est 5 vs 3); MdAPE points 0.0%, so point sizing was sound for this epic. | retro-writer: implementer verified before `git add`, so the retro.md cap pin in test_lean_flow_docs.py went red once tracked (fixed 7f31a5a). |
| Rulings were explicit with cost-if-wrong: points-required finding deferred to planner-points-gate, scratch-locations `op inject -o <tmp>` kept as the caller's choice, estimate-fields LEAN_KEYS split judged not a weakening. | em-dash-edit-guard: f4b2fb9 alone was red on the new em-dash lint (literal in a test constant), fixed in f45010f; the commit was not green on its own. |
| Whole-diff review and scope audit found no critical, high or scope gaps against G1-G7 and D1-D16; the two medium findings became task review-seams (2 pt, 0 rounds). | Expected minutes and tokens read "not recorded" for all 24 tasks, so MdAPE minutes and tokens are unmeasured; the epic delivered the fields but could not use them (tasks predate them). |
| Discovered work was placed as tasks, not dropped: plugin-readme-rules, plugin-readme-commands, review-seams. | The agent-usage hook has not run live: `.logs/agents` records came from the backfill, and live SubagentStart/Stop payload shapes are unverified until /reload-plugins on main. |
| | Tasks lack a `points` frontmatter key (created before the field); the queued epic epic-and-task-migration-skill fills it. |

## Improvements

- Code:
  - plugins/workbench/skills/start-development/scripts (task_cmd._actuals and retro._fill_from_records): the records-or-backfill sequence is written twice; deltas._logs rebuilds the logs path by hand. Tracked in review-seams.
  - epic-run prose and agent_usage.MARKER: the run marker is defined in both places; review-seams adds a test tying them.
  - test_ticket_files.py: needed a ruff format commit (879c672) after retro-command; formatting drifted across tasks.
- Delivered differently:
  - retro-writer re-pointed from 5 to 3 post-delivery points: smaller than planned because the agent is a prompt file plus a doc, not a subsystem.
  - Rules 1, 3, 6 and 7 are prose only and the run marker is a prompt convention, as designed; `actuals --backfill` is the fallback when the live hook does not fire. The backfill, not the hook, produced this epic's `.logs/agents` records because the hook loads only after merge and /reload-plugins.
  - Three tasks (points-required, scratch-locations, em-dash-commit-guard) changed or declined adjacent items by ruling: only the first commit segment's -F is read by the commit guard (declined).
- Tech debt:
  - retro backfills per empty task (up to N transcript walks): lives in retro command; remove by a single transcript pass shared across tasks. Accepted at review.
  - No `points` key and no expected minutes/tokens on this epic's 24 tasks: remove by running epic-and-task-migration-skill.
  - Live hook payload shapes unverified: remove by one real subagent run after /reload-plugins and checking `.logs/agents`.
- Workflow:
  - No history yet (first epic with a RETRO.md), so nothing is marked recurring.
  - Implementer reports must quote each `[lint:*]` and suite summary line, run after `git add` and commit, not from a tail read or before staging (agent-usage-lib, retro-writer, em-dash-commit-guard); have the reviewer rerun the full lint and `git ls-files` checks instead of trusting the report.
  - A feature with a default path needs one test without the override flag (actuals-backfill); add it to the implementer checklist.
  - Reviewers should run the documented command for any README or skill snippet that shows an invocation (plugin-readme-commands).
  - Create tasks with `--points` and expected minutes/tokens from the start so the next epic's Deltas are measurable.
