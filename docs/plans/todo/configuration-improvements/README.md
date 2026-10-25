---
title: configuration improvements
blockers: []
stage: build
owner: ""
repos: [agent-orchestrator, claude-code-wrapper, agents-helmfile]
created: 2026-10-25
---

# configuration improvements

## Project brief

What: Expose more claude-code-wrapper settings (hooks, idle_auto_compact), optional leader lease timeout, optional cluster autoclose after a time, Clusters entry in the hamburger menu above Presets
How: ClusterSpec and preset fields rendered into the wrapper config, a lease timeout in the leadership tables, an autoclose deadline enforced by the reconciler, a menu entry
Why: Get more of tatara-new's configurability into the Python platform

## Description

User request (2026-10-25), verbatim. Overall target: "Target getting more and more from tatara system (/Users/szymonri/Documents/tatara-new)"

"## configuration improvements
  * expose more claude-code-wrapper settings (including hooks, idle_auto_compact)
  * add optional timeout to leader lease
  * add autoclose after time (optional parameter- closing agent cluster after specified time)
  * clusters gets it's own place in \"hamburger\" menu, above \"presets\""

## Goals



## Non-goals



## Time

Derived by `ticket.py estimate`, `tasks` and `apply-run` from the task `estimate` and `actual` fields into one line (`Estimate | Critical path | Expected wall at P= | Actual | Remaining estimate`); never edit by hand. Report only, never a budget.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
