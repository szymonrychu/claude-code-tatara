# Housekeeping rules, estimates and retrospectives record

## Asked

Four things in one epic (meta mode, repo workbench): housekeeping rules for every agent (G1-G3, G2 enforced by lint and hooks where mechanical); per-task storypoint, time and token estimates (G4); measured per-task actuals and a RETRO.md at epic close (G5, G6); a deltas report so estimates calibrate from history (G7).

## Shipped

Closed by `ticket.py close`: main 01d2701 -> e46b3fa; integration verify and main verify both passed (`mise run test && mise run lint`). 24 of 24 task files done (21 planned + plugin-readme-rules, plugin-readme-commands, review-seams discovered). Epic review: no critical or high findings, no spec gap against G1-G7 and D1-D16; 2 medium became task review-seams. Scope audit: no gaps. No MR or PR; nothing pushed. Before the epic main was red on scripts/tests/test_marketplace.py (pinned 1.0.0 vs released 2.0.0), fixed as its own commit 3187a99.

## Tasks

Status and verified head from the task files. Rounds and tail from the orchestrator's notes. Points: estimate = actual except retro-writer (est 5, actual 3). Minutes/tokens per task are in RETRO.md (totals 423 min, 28123663 tokens; expected minutes/tokens "not recorded" for all tasks).

| Task | Status | Verified head | Rounds | Verification tail |
|---|---|---|---|---|
| calibration-lib | done | 297bdf4 | 0 | scripts 130 + start-development 346 assertions green, lint passed |
| em-dash-lint | done | a2950c7 | 0 | scripts 490 passed, lint:em-dash green |
| workbench-dirs | done | 35f1ce0 | 0 | scripts 134, hooks 437, test:scripts 490 passed, lint green |
| em-dash-edit-guard | done | f45010f | 0 | hooks 453, start-development 346, test:scripts 490 passed, lint green |
| estimate-fields | done | fb13db0 | 0 | start-development 352 passed, lint green |
| housekeeping-rules | done | bb010ff | 0 | scripts 492, start-development 352 passed, lint green, setup --check no drift |
| test-logs-dir | done | 11f9442 | 0 | scripts 135 passed, lint green |
| agent-discipline | done | b9ee9ba | 0 | start-review 32, start-development 353, start-research 66, scripts 135 passed, lint green |
| em-dash-commit-guard | done | cea87f1 | 1 (EM_DASH defined twice) | hooks 462, start-development 353 passed, lint green |
| plugin-readme-rules | done | 1dc8d46 | 0 | start-development 354 passed, lint green |
| points-required | done | e73b57b | 0 | start-development 356 passed, lint green |
| output-spill-to-logs | done | 303f638 | 1 (spill_dir not fail-open) | hooks 466, start-development 356 passed, lint green |
| agent-usage-lib | done | f34227b | 1 (lint:config-dir red, misreported green) | scripts 140, hooks 466 passed, lint green incl config-dir |
| scratch-locations | done | fd6600a | 0 | test:scripts 493, start-development 356, start-debugging 14, pack-observability 22 passed, lint green |
| agent-usage-hook | done | cec85a7 | 0 | hooks 476, start-development 356, test:scripts 494 passed, lint green |
| planner-points-gate | done | 3c983ec | 1 (scope-auditor.md and two new-task lines lacked --points) | start-development 359, start-review 32 passed, lint green |
| run-marker-points | done | f597bdd | 0 | epic-run 3, start-review 33, start-development 359 passed, lint green |
| stamp-actuals | done | fb1bd5b | 0 | start-development 363, scripts 141, epic-run 4 passed, lint green |
| actuals-backfill | done | ab86c4b | 1 (HIGH: 0 records by default) | scripts 145, start-development 366 passed, lint green |
| retro-command | done | d257ca1 | 0 | start-development 374 passed, lint green; dry run on a clone: 20 of 23 tasks with real minutes |
| deltas-command | done | 2ddf0d0 | 0 | start-development 379, scripts 145 passed, lint green |
| retro-writer | done | 7f31a5a | 1 (cap pin red once retro.md tracked) | start-development 382, start-review 33, start-research 66, scripts 147 passed, lint green |
| plugin-readme-commands | done | e68d094 | 1 (README span not a real invocation) | start-development 384 passed, lint green |
| review-seams | done | f0bdea7 | 0 | start-development 384, epic-run 5, scripts 150 passed, lint green (targeted suites only; full suite ran at e68d094, exit 0, and at close) |

TDD red evidence (`tests.red`) and `verification.head` are plan-execute fields; this epic ran through epic-run (no plan-execute return), so none was available and none is quoted. The verified head above is the task file's `verified_head`.

## Rulings

- points-required medium finding ("epic-task-create and planner.md show new-task without --points") dropped there: task planner-points-gate owns those lines. Cost if wrong: a stale doc for the span of two tasks. Three existing-test edits in points-required accepted (old premise impossible, new assertions stronger).
- scratch-locations low-confidence finding (secrets-env SKILL.md `op inject -o <tmp>`) dropped: a decrypted secrets file must not be written under the repo tree. Cost if wrong: one skill names a generic temp path.
- estimate-fields: LEAN_KEYS split into BASE_KEYS + NUMBER_KEYS judged not a weakening. Cost if wrong: a new key could go unasserted; new keys are asserted on new-task output and the template.
- test-logs-dir: GIT_CEILING_DIRECTORIES export in run-tests.sh judged sound (reviewer checked suites that git init under basetemp). Cost if wrong: a suite resolving a parent repo.
- agent-discipline: reworded pin in test_implementer_is_lean accepted (stricter phrase, appears twice in implementer.md). Cost if wrong: a weaker pin.
- review-seams: retro backfills once per empty task (up to N transcript walks), accepted. Cost if wrong: slow retro on large epics.
- Declined (em-dash-commit-guard): only the first commit segment's -F is read. Cost if wrong: an em dash in a later segment's -F file passes the guard.
- Extra commits: ruff format fix in hooks/lib/core.py (in output-spill-to-logs) and ruff format of test_ticket_files.py (879c672, in retro-command), each its own commit.
- Epic review and scope audit: no findings dropped.

## Discovered and blocked

- Plugin README rules list: became task plugin-readme-rules (done). README `task --status done` line: became plugin-readme-commands (done). Whole-diff medium findings: became review-seams (done).
- Queued follow-up epic `epic-and-task-migration-skill`, blocked on this one: migrates old task files (no `points` key, no expected minutes/tokens) to the new scheme. Cleared by the user starting it.
- Cannot verify: live SubagentStart/Stop payload shapes for the agent-usage hook until `/reload-plugins` on main; the user clears it. Records so far came from the backfill.
- Expected minutes and tokens are "not recorded" for all tasks (they predate the fields), so MdAPE minutes and tokens are unmeasured; cleared by the next epic's tasks.
- Goals 1, 3, 6, 7 (rules) and the run marker are prompt/text conventions by design; actuals --backfill is the fallback.

## Not pushed

Main is committed locally (e46b3fa) and not pushed; the user pushes it. Local main is also 4 commits behind origin/main (merged cloud-session PR #1 and related); the user reconciles before pushing.

## Lessons routed to

- Implementer reports must quote each `[lint:*]` line, not a tail read (agent-usage-lib false green): edit the implementer/reviewer skill text (judgement call); the reviewer's own lint run is the backstop.
- Verify after `git add`/commit, not before (retro-writer: tracked-files tests went red): add a check in the verify step that runs tests on the committed tree; until then edit the implementer.md instruction.
- A default-path feature needs one test without its override flag (actuals-backfill): reviewer checklist edit (judgement call).
- Each commit must be green on its own (em-dash-edit-guard f4b2fb9 red on the new em-dash lint): mechanical, add the em-dash lint to the per-task verify and to the commit-time check; already enforced going forward by the lint:em-dash task and commit guard.
- Duplicate definitions (EM_DASH twice; run marker in prose and in code; records-or-backfill twice): add a test tying the prose marker to agent_usage.MARKER (done in review-seams); duplicate-helper detection stays a reviewer judgement.
