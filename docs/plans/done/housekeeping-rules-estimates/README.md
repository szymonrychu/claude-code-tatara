---
title: "Housekeeping rules, estimates and retrospectives"
blockers: []
stage: review
owner: Szymon Richert
repos: [workbench]
created: 2026-10-24
---

# Housekeeping rules, estimates and retrospectives

## Project brief

What: Housekeeping rules for every agent, storypoint, time and token estimates per task, a RETRO.md at epic close, and a deltas script that calibrates future estimates from actuals
How: Rule files in the plugin rules block plus hooks and a lint for the mechanical ones; ticket.py gains estimate fields, a SubagentStop usage recorder under .logs, a retro subcommand and a deltas report; epic-run and start-development gain the retro step
Why: Agents guess at scope, tamper with tests and estimate from reasoning alone; measured actuals per task make estimates and the flow itself improve with every epic

## Description

Four improvements to the workbench development flow, requested together as one epic:

1. Housekeeping rules, binding on every agent in every harness: the agent the user interacts with never writes code or builds anything (supervisor only, responsible and accountable for all work done by subagents); never edit, delete or xfail a test to make it pass unless the test itself is no longer accurate; implementing and reviewing subagents list all files, read them in one pass, only then make all edits, then run tests once; no backward compatibility unless the user explicitly asks; no em dash characters in any code, comment, commit, message or content of any kind; do not guess at any level, ask the user or the fable architect when unsure; always aim for the full scope, never cut corners or reduce scope; all scratchpad edits land under `.scratchpad` in the workbench root, the only scratchpad dir; all logs land in gitignored `.logs` in the workbench root.
2. Planner improvements: each task also carries a complexity estimate in storypoints, an expected time and expected tokens.
3. Retrospective at epic close: RETRO.md with a tasks table (task title in delivery order, post-delivery complexity in storypoints, delivery time start to finish in minutes, tokens used per task including implementation and review), a retro table (what went well; what went bad, could be improved) and a list of potential improvements in the code or things delivered differently than expected, including tech debt introduced anyway.
4. Scripting support for deltas between complexity, delivery time and token usage per task, so estimates get more precise over time: the tasks table feeds future estimates, the retro table feeds improvement proposals for future work including workflow improvements; seamless for the agent, taking over most of the estimation from the agent's reasoning.

## Goals

- G1: A housekeeping rule set exists in the plugin rules, reaches AGENTS.md through the generated rules block, and states every rule of the request: supervisor-only orchestrator accountable for subagent work; no test editing, deletion or xfail to make a test pass unless the test is no longer accurate; list all files, read in one pass, edit all, run tests once; no backward compatibility unless asked; no em dash in any content; no guessing, ask the user or the fable architect; full scope always; `.scratchpad` as the only scratchpad dir; logs under gitignored `.logs`.
- G2: The em dash rule and the scratchpad and logs locations are enforced mechanically where that is possible: a lint over tracked content and a hook that refuses an em dash in a written file or a commit message; `.scratchpad` and `.logs` are gitignored and every skill, agent and script that names a scratch or log location names those two directories.
- G3: The implementer, reviewer and planner agent instructions carry the list, read once, edit all, test once discipline and the no test tampering rule.
- G4: Every task file carries a complexity estimate in storypoints, an expected time in minutes and expected tokens, written at planning time; the planner gives storypoints and the tool fills time and tokens from history, so the estimate costs the planner one number.
- G5: Actual delivery time (start to finish, minutes) and tokens (implementation plus review, all rounds) are captured per task without the orchestrator doing arithmetic or copying numbers, and a post-delivery storypoint measure is recorded per task.
- G6: Epic close produces RETRO.md with the tasks table (title in delivery order, post-delivery storypoints, delivery minutes, tokens), the retro table (went well; went bad or could be improved) and the list of improvements and things delivered differently than expected, tech debt included.
- G7: A script reports the deltas between estimated and actual storypoints, minutes and tokens per task and across done epics, and `new-task` defaults draw on those actuals, so estimates improve with every closed epic.

## Non-goals

- Changing the user's private global CLAUDE.md or any file outside this repository.
- Cost in currency: tokens are counted, never priced.
- Backward compatibility with task files of epics already in `done/`: they are read as they are, and the new fields are simply absent there.
- A new orchestration loop: epic-run stays as it is except for the retro step and the prompt marker the capture needs.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-25)

Whole-diff review (one sonnet reviewer, checklist): no critical or high findings; no missing, extra or wrong spec item against G1-G7 and D1-D16. Two medium quality findings, both confirmed and placed as task review-seams: (1) the records-or-backfill sequence written twice (task_cmd._actuals, retro._fill_from_records) plus deltas._logs rebuilding the logs path by hand; (2) the run marker defined in epic-run prose and in agent_usage.MARKER with no test tying them. Seams checked consistent: recorder fields vs aggregate/backfill, stamped keys vs retro/deltas, template H2s vs retro, commit guard probes (-m, -C, cd &&, --amend, -c, -F -), edit guard allows removals, recorder fail-open and idempotent, calibration fallbacks, rule texts vs tdd.md.
Scope audit (sonnet): every goal G1-G7 built, no non-goal crossed, no duplicate helpers. Goals met only in text, as designed (rules 1, 3, 6, 7 are prose; the marker is a prompt convention with actuals --backfill as the fallback).
Dropped: none. Cannot verify until /reload-plugins on main: live SubagentStart/Stop payload shapes.
