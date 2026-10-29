---
title: decision board
blockers: [session-orchestration-mcp]
stage: build
owner: ""
repos: [agents-web, any-mcp-tatara-plugins, agents-orchestrator, agents-helmfile]
created: 2026-10-29
---

# decision board

## Project brief

What: A web Tasks/Decision board where agents post questions with options and a recommendation, and the user answers, reviews history and requests amendments
How: A new microservice with its own database, agents-web pages and an any-mcp tool, built on the session-orchestration-mcp tools
Why: The user wants visibility and better UX for decisions agents need from them, complementing the skills

## Description

User request (chat 2026-10-28 21:02Z, relayed by mx-34 msg 263), verbatim:

"General idea (another epic, maybe microservice):
Tasks/Decision board- idea here is simple- if there is a question/decision that I should take, it will land on a webUI- I will get to choose, or propose something myself from options provided by an agent (with its recommendation).

I will also be able to see past decisions and ask to amend them (through properly planned changes ).

It's not meant to be an epic replacement- agents are still mean to follow the skills as is. It's meant to complement them and help me out with visibility and UX of the system"

Ownership and queue spot agreed between tatara and cct2 (tatara msg 282, cct2 msg 315, confirmed by mx-34 msg 316): tatara owns this epic, after session-orchestration-mcp and before semver-image-tags-at-the-end. The sibling epic A (immediate PTY delivery with per-message priority) belongs to cct2.

Shape proposed in msg 282, to be confirmed at planning: a new microservice with its own Postgres database (decisions with options, the agent's recommendation, the user's choice or own proposal, history, and amend requests that become planned changes), agents-web pages, and an any-mcp tool so agents can post questions and read answers. The workbench skills' gate questions would post there too. It builds on the session-orchestration-mcp tools for the agent-facing MCP surface and for routing the user's choice back into the session.

Open at planning: the new component's name and repo (added with component-add), and how an answer reaches the asking session (orchestrator message or polled tool).

User requirement (chat 2026-10-29 04:59Z, relayed by mx-34 msg 347), verbatim: "Decision board should belong to session". Relayer's reading: each session has its own board, the web UI shows it under that session, and the agent tools post to and read from the caller's session board.

Planning note (tatara, 2026-10-29): session scoping weakens the case for a separate microservice. The orchestrator already owns sessions, caller identity on the agent port, the session pages in the web UI and delivery of messages into a session, so orchestrator tables keyed by session (with their single writer) look simpler than a new service that must resolve sessions over HTTP. Decide between the two at planning (architect-researcher).

README-only shell; plan it when it is reached.

## Goals

- G1: A question or decision an agent needs from the user lands on a web UI page with the agent's options and its recommendation.
- G2: The user picks an option or proposes their own, and the answer reaches the asking agent.
- G3: The user sees past decisions with their history.
- G4: The user can ask to amend a past decision, and the request becomes a properly planned change.
- G5: Agents post questions and read answers through an MCP tool; the workbench skills' gate questions post there too.
- G6: The decision board belongs to a session: each session has its own board, shown under that session in the web UI, and the agent tools post to and read from the caller's session board.

## Non-goals

- Replacing epics or the skills flow: agents still follow the skills as they are; the board complements them.
- Immediate PTY message delivery and per-message priority (epic A, owned by cct2).

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
