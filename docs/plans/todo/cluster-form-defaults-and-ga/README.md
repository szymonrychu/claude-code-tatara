---
title: cluster form defaults and gauge tick
blockers: []
stage: build
owner: ""
repos: [agent-orchestrator, agents-helmfile]
created: 2026-10-23
---

# cluster form defaults and gauge tick

## Project brief

What: Dropdowns for model and effort, defaults prefilled for every cluster field, a correct auto-compact tick
How: Settings and /meta carry model, effort and resource defaults; the form reads them like max attempts; the renderer applies resource defaults; the gauge tick is a radial mark
Why: The form shows empty fields with no hint of what the cluster will get, and the gauge tick is drawn off the ring

## Description

User request (2026-10-23): in the cluster form, Model and Effort must be dropdowns, and every other field must show its default when not provided, the way Max attempts is prefilled from /meta defaults (e.g. CPU request). Also the ribbon context gauge's auto-compact tick renders as a skewed rectangle outside the circle (screenshot: grey ring at 3%, white bar top-right); it must be a small radial mark on the ring.

## Goals

- Model and Effort are dropdowns fed by /meta (models: claude-opus-5-5 default, claude-sonnet-5-5, claude-haiku-5-5, claude-fable-5-1; efforts: low, medium, high, xhigh, max).
- Every form field is prefilled from /meta defaults; cpu request 500m / limit 4 and memory request 1Gi / limit 8Gi are real defaults applied to agent pods when a cluster leaves them empty, all configurable via ORCH_* settings.
- The gauge's auto-compact tick sits on the ring at the auto-compact percentage.
- Deployed: chart and image bumped in agents-helmfile, applied, smoke OK.

## Non-goals

- No change to clusters already running until they are edited (existing specs keep their values).

## Time

Derived by `ticket.py estimate`, `tasks` and `apply-run` from the task `estimate` and `actual` fields into one line (`Estimate | Critical path | Expected wall at P= | Actual | Remaining estimate`); never edit by hand. Report only, never a budget.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
