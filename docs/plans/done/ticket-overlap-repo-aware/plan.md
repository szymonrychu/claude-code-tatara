---
title: ticket overlap repo aware
repos: [workbench]
created: 2026-10-25
owner: Szymon Richert
rung: 1
---

# ticket overlap repo aware

## What and why

What: Make ticket.py's in-progress file-overlap check compare (repo, path) instead of bare paths, so epics touching same-named files in different repos (pyproject.toml, uv.lock, openapi.json, AGENTS.md) can be in progress together; genuine same-repo overlaps still refuse.
How: 
Why: User 2026-10-25: run agents-matrix-connector and agents-schedule-microservice in separate orchestrator sessions alongside orchestrator-rename-sessions; the repo-agnostic check blocks that with false collisions.

## Scope ladder

### Rung 1: agreed scope (migrated)

none recorded in the epic format

## Agreed scope

Rung 1, migrated from the epic format: the epic's goals were its agreed scope.

## Non-goals

none recorded in the epic format

## Design

none recorded in the epic format

## Decisions

none recorded in the epic format

## Open questions

none

## Research

none recorded in the epic format

## Irreversible operations

none

## Migrated notes

### README.md: Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-25)

Lean meta change, one task. Reviewer PASS: AC1 15 passed, mise run test:plugin 2015 assertions all green, lint clean; dry run shows only same-repo agents-helmfile and agents-web overlaps remain.
