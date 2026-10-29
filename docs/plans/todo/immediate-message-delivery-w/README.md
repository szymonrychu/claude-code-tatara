---
title: Immediate message delivery with per-message priority
blockers: [slash commands from chat, hive decoupling]
stage: build
owner: ""
repos: [claude-code-wrapper, agents-orchestrator, any-mcp-tatara-plugins, agents-web, agents-common, agents-matrix-connector]
created: 2026-10-29
---

# Immediate message delivery with per-message priority

## Project brief

What: Messages to a session reach its leader through the PTY at once, even mid-turn, and Claude Code (or the agent) queues them internally; each message carries a priority: immediate by default, or wait until the leader is idle (today's behaviour).
How: Planned when reached (cct2 queue: after slash-commands-from-chat and the paste-.env fix).
Why: User, verbatim (2026-10-28 21:02Z via mx-34 #262): 'currently the messages wait for too long ... message should get through PTY immediately and let either Claude Code or even agent queue them internally'; 21:04Z (#266): 'maybe worth adding priority meta to messages (by default reaching instantly, option to wait until idle)'.

## Description

User request (2026-10-28 21:02Z via mx-34 #262), verbatim: "Improvement idea to messaging system- currently the messages wait for too long. Ask agents to queue another epic- message should get through PTY immediately and let either Claude Code or even agent queue them internally."

User scope addition (21:04Z via mx-34 #266), verbatim: "A: maybe worth adding priority meta to messages (by default reaching instantly, option to wait until idle)".

Today every message waits for an idle leader: the orchestrator picks only an idle agent, holds later messages behind a busy leader, and the wrapper answers 409 busy to a second turn. Claude Code itself queues input typed while it works and hands it to the model at the next tool boundary, or right after the turn. This epic sends a message to a busy leader at once: the wrapper pastes it into the running turn with that turn's marker, so it joins the running turn and shares its final answer, and a message can ask to wait for idle instead. It is planned on top of slash-commands-from-chat (wrapper command queue, transcript parser, orchestrator message kind) and hive-decoupling (orchestrator migration 0011, plugins 0.4.0), both blockers. It lands after session-orchestration-mcp too (migration 0013 on top of slash's 0012, plugins v0.6.0), so it takes migration 0014 and plugins v0.7.0 (negotiated 2026-10-29, mx-34 #469/#470). Design: design.md.

## Goals

- G1: a message sent to a busy session reaches its leader through the PTY at once, mid-turn, and Claude Code queues it internally; by default no message waits for the leader to go idle.
- G2: each message carries a priority, immediate (the default) or idle (wait until the leader is idle, today's behaviour), settable from the web composer, the orchestrator messages API, the superleader's session_send tool and the ccw peer send_message tool.
- G3: a message delivered mid-turn never wedges the session: the running turn still ends on its Stop, and the message is linked to the turn that answered it (hop guard and delivery verifier included).
- G4: Matrix chat messages in a room whose run is in progress are delivered at once, and an answer shared by merged messages is relayed to the room once.
- G5: slash commands keep running at the turn's Stop whatever the priority, and nothing is pasted while a command runs or a dialog is open.
- G6: how Claude Code 2.1.304 treats input pasted mid-turn is probed on the real binary and recorded before the wrapper relies on it.

## Non-goals

- No new message status for "answered": it stays derived from the linked turn.
- No delivery through the notes channel, Claude Code's native cross-session messaging or queue keystrokes (Ctrl+Enter, Up take-back).
- No slash command typed mid-turn; Claude Code's own immediate commands (slash epic Q2) stay out.
- No orchestrator stale-busy detector and no wrapper turn watchdog (debug record follow-up, noted, not doing now).
- No agents-helmfile pin, apply or smoke task: deploy is decided at the gate.
- No priority control in Matrix: connector, webhook and schedule messages take the server default.
- No change to turn_max_seconds: it keeps counting from the turn's first submit.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
