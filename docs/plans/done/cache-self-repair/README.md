---
title: cache-self-repair
blockers: []
stage: review
owner: Szymon Richert
repos: [agents-orchestrator]
created: 2026-10-26
---

# cache-self-repair

## Project brief

What: Unreadable workspace cache archive resets the workdir and is overwritten by the next save
How: restore wipes the workdir on ExtractError and emits reset; reset joins the save allow-list
Why: User decision 2026-10-26: cache repair - start empty

## Description



## Goals



## Non-goals



## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-26)

Single-task epic; reviewer pass at 6ec2d89, 940 passed, lint clean, AC1-AC5 verified, agents-web has no hard-coded cache states.
