---
title: frontend decoupling
blockers: []
stage: build
owner: ""
repos: [agent-orchestrator, agents-helmfile]
created: 2026-10-25
---

# frontend decoupling

## Project brief

What: Decouple the web frontend from the orchestrator microservice
How: The frontend ships and runs on its own, talking to the orchestrator only through its documented HTTP API
Why: Services talk only through the queue or HTTP; new microservices (webhook, schedule) need UI entries without living in the orchestrator

## Description

User request (2026-10-25), verbatim. Overall target: "Target getting more and more from tatara system (/Users/szymonri/Documents/tatara-new)"

"## frontend decoupling
  * decouple frontend from orchestrator microservice"

## Goals



## Non-goals



## Time

Derived by `ticket.py estimate`, `tasks` and `apply-run` from the task `estimate` and `actual` fields into one line (`Estimate | Critical path | Expected wall at P= | Actual | Remaining estimate`); never edit by hand. Report only, never a budget.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
