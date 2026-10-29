---
title: session orchestration mcp
blockers: [slash-commands-from-chat]
stage: build
owner: ""
repos: [agents-orchestrator, any-mcp-tatara-plugins, agents-schedule, agents-web, agents-helmfile]
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

Queued right after slash-commands-from-chat, its only blocker (accepted queue, 2026-10-29); hive-decoupling and matrix-connector-agent-initi are done. immediate-message-delivery-w builds on this epic. Numbers (negotiated 2026-10-29, mx-34 #469/#470): orchestrator migration 0013, agents-schedule migration 0002, any-mcp-tatara-plugins v0.6.0, agents-schedule release v0.2.0 (negotiated, user answer pending). Every release tag is proposed via mx-34 and confirmed before tagging. Refreshed 2026-10-29 after a staleness audit (design.md, "Staleness refresh").

## Goals

- G1: A session the user flagged `session_orchestration` (a per-preset or per-spec switch, off by default, set only by the user through agents-web or the public API) has orchestrator MCP tools to list, create, edit and delete presets, list, create, scale and delete sessions, and list, create, edit, delete and run cron schedules, on the user's request; only its leader may call them, and no unflagged session gets the tools.
- G2: "On user request" is checked by the server: a write is allowed only in a turn delivered by a message from the user (agents-web) or the Matrix connector by default; turns started by session messages, webhooks, schedules or no message are refused `not_user_turn`.
- G3: A flagged session changes only the sessions, presets and schedules it created; it reads all of them, with preset secrets masked except on its own; it cannot grant more privilege than it holds (`session_orchestration` is never grantable), cannot delete itself, and cannot delete a superleader or orchestrating session.
- G4: Every write call, refusals included, is recorded in an orchestrator audit table readable on the main API and by the caller through a tool; writes and owned objects are rate- and count-limited.
- G5: Schedule calls go through the orchestrator, which relays them to a token-protected listener on agents-schedule that records each schedule's owner; the agent token never leaves the orchestrator.
- G6: agents-web has the "Session orchestration" switch on the preset form (sessions take the flag from their preset), and shows "created by <slug>" on sessions, presets and schedules.
- G7: The plugin release, orchestrator pin, agents-helmfile values and live applies ship it, and a live smoke from a flagged throwaway session proves create, edit and delete of a preset, a session and a schedule, the refusals and the audit rows, leaving nothing behind.

## Non-goals

- Agents calling agents-schedule directly, an admin or service token in agent pods, or orchestrator-side schedule storage.
- Scope lists, slug globs or per-target grants (option C); ownership is the target scope.
- A two-step confirmation token before a delete.
- A preset copy tool.
- Any agents-common or agents-matrix-connector change.
- Making `session_orchestration` editable in place on a running session (the spec stays immutable).
- Noted, not doing now: a UI page for the audit trail, a shared bearer listener gate in agents-common, owner-sender marking on connector messages, schedules passing owner provenance to the sessions they fire.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
