---
title: session orchestration mcp
blockers: [hive-decoupling]
stage: build
owner: ""
repos: []
created: 2026-10-27
---

# session orchestration mcp

## Project brief

What: MCP tools for a session to manage other sessions on the user's request: presets, sessions, cron schedules
How: orchestrator-side tools behind a permission model naming who may orchestrate and which sessions
Why: The user wants the Matrix-connected agent (mx-5) to set up presets, sessions and schedules from chat

## Description

User request (2026-10-27, relayed by the mx-5 leader, msg 124), verbatim:

"Allow for session to orchestrate other sessions through appropriate mcp tooling. Eg you (matrix connected agent) would be allowed to define presets, sessions, cronjobs, etc on user request."

Relayer's reading: MCP tools that let a session (for example mx-5, the Matrix-connected one) manage other sessions on the user's request: create and edit presets, create and delete sessions, set up cron jobs and so on, scoped by permissions (who may do this, and to which sessions).

Queued after hive-decoupling.

## Goals



## Non-goals



## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
