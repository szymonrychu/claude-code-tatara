---
title: parked epic stage
blockers: []
stage: review
owner: Szymon Richert
repos: []
created: 2026-10-27
---

# parked epic stage

## Project brief

What: ticket.py can park an in-progress epic so its unbuilt tasks stop reserving files
How: A parked README stage, set and cleared by ticket.py stage; run_check skips parked epics' tasks; lint and docs updated
Why: 2026-10-27 reprioritisation puts the incident and Matrix epics ahead of the parked slash-commands epic, whose unbuilt tasks block their task creation

## Description



## Goals



## Non-goals



## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-27)

Single-task lean meta epic. Task review clean (verify 41 passed; mise run test:plugin all green 2023 assertions; mise run lint clean) at 610c3b55. Scope audit: all landed. Whole-diff review = the task review (one task, whole diff). README goals left empty (lean); audited against brief and ACs.
