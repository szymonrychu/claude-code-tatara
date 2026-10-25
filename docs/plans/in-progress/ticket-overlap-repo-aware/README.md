---
title: ticket overlap repo aware
blockers: []
stage: review
owner: Szymon Richert
repos: [workbench]
created: 2026-10-25
---

# ticket overlap repo aware

## Project brief

What: Make ticket.py's in-progress file-overlap check compare (repo, path) instead of bare paths, so epics touching same-named files in different repos (pyproject.toml, uv.lock, openapi.json, AGENTS.md) can be in progress together; genuine same-repo overlaps still refuse.
How: 
Why: User 2026-10-25: run agents-matrix-connector and agents-schedule-microservice in separate orchestrator sessions alongside orchestrator-rename-sessions; the repo-agnostic check blocks that with false collisions.

## Description



## Goals



## Non-goals



## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-25)

Lean meta change, one task. Reviewer PASS: AC1 15 passed, mise run test:plugin 2015 assertions all green, lint clean; dry run shows only same-repo agents-helmfile and agents-web overlaps remain.
