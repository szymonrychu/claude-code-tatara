---
title: slash commands from chat
blockers: []
stage: review
owner: Szymon Richert
repos: [claude-code-wrapper, agents-orchestrator, agents-web, any-mcp-tatara-plugins]
created: 2026-10-27
---

# slash commands from chat

## Project brief

What: Any slash command sent from chat, by the user or a superleader, runs as a Claude Code command at any moment without hanging the session
How: route slash text to a generic command path in wrapper and orchestrator with completion detection and a bound, design settled by architect-researcher
Why: /reload-plugins from chat made the session unresponsive

## Description

User request (2026-10-27), verbatim:

"## Allow / commands from chat

I tried to send `/reload-plugins` from chat window and it made session unresponsive. Allow these commands to be run from chat window at any moment. Both user and superleader can send them. Any / comand."

Discovery (2026-10-27): chat text is typed into the PTY as a turn with a ccw turn marker; a local command such as /reload-plugins never calls the model, so no Stop hook fires, turn_max_seconds defaults to 0 and the session stays busy (every later turn gets 409). The wrapper command queue (POST /v1/sessions/{id}/commands) accepts only five built-ins. "Superleader" = a session with spec.session_messaging whose leader sends to other sessions via orchestrator_session_send; those messages are framed as <session-message>, so a "/cmd" never runs as a command today.

## Goals

- Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards.
- A superleader can send a slash command to a target session and it runs as a command, not as framed prompt text.
- Sending /reload-plugins (the reported case) no longer hangs the session; a regression test pins it.
- The chat shows the command and its outcome.

## Non-goals

- No slash-command autocomplete or picker in the composer.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
