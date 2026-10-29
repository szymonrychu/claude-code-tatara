---
title: Immediate message delivery with per-message priority
blockers: []
stage: build
owner: ""
repos: [claude-code-wrapper, agents-orchestrator, any-mcp-tatara-plugins, agents-web]
created: 2026-10-29
---

# Immediate message delivery with per-message priority

## Project brief

What: Messages to a session reach its leader through the PTY at once, even mid-turn, and Claude Code (or the agent) queues them internally; each message carries a priority: immediate by default, or wait until the leader is idle (today's behaviour).
How: Planned when reached (cct2 queue: after slash-commands-from-chat and the paste-.env fix).
Why: User, verbatim (2026-10-28 21:02Z via mx-34 #262): 'currently the messages wait for too long ... message should get through PTY immediately and let either Claude Code or even agent queue them internally'; 21:04Z (#266): 'maybe worth adding priority meta to messages (by default reaching instantly, option to wait until idle)'.

## Description



## Goals



## Non-goals



## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
