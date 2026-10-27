---
title: matrix connector agent-initiated and follow-up messages
blockers: [slash-commands-from-chat]
stage: build
owner: ""
repos: [agents-matrix-connector, agents-orchestrator, any-mcp-tatara-plugins, agents-helmfile, agents-web]
created: 2026-10-27
---

# matrix connector agent-initiated and follow-up messages

## Project brief

What: Agents send, follow up, reply and react in the user's Matrix (Messenger) chat at any time, not only as the answer to a chat-started turn
How: orchestrator-relayed orchestrator_chat_* MCP tools, a token-protected agent port and sends queue on the connector, room authorisation by session binding or a per-room agents_may_initiate flag
Why: Replies to turns not started from the chat (session messages, background completions) never reach the user, and agents cannot start a chat

## Description

User request (2026-10-27, relayed by the mx-5 leader), verbatim:

"Bug: agents talking to the user over the Matrix connector (bridged to Facebook Messenger) can only answer the turn that came from a chat message. Turns arriving from a chat message carry a marker like `<!-- agents-matrix:12 -->`; the reply text to those reaches Facebook. Replies to turns started any other way (e.g. a <session-message> from another session's leader, background task completions, member agents reporting) show only in the web UI and never reach the chat. Repro: user sends a chat message, agent replies (delivered); another session messages the agent before the user writes again; the agent's reply to that turn is never delivered. Observed 2026-10-27 ~16:38Z in hive mx-5 (session-message #87 reply was dropped). The agent has no Matrix MCP tool, only plain-text replies.

Requirements from the user:
1. Must: an agent can initiate a chat with the user over the connector (no prior inbound message needed).
2. Must: an agent can send follow-ups (multiple messages without a user reply in between).
3. Ideally: an agent can reply to a specific message (threaded/quoted reply) and react to messages with emoji (reactions may be enough for acknowledgements)."

Queued after the four epics in flight (file-download, markdown, file-editor, slash-commands).

Discovery (2026-10-27): .scratchpad/discovery/matrix-outbound.md. Architecture decision: .scratchpad/design/matrix-outbound-arch.md (orchestrator-relayed orchestrator_chat_* tools, connector agent port, `sends` queue, room authorisation by binding or an agents_may_initiate flag, short m<n>/s<n> message references).

## Goals

- An agent (session leader) can send a message to the user's Matrix chat at any time, including a chat it never received a message from (initiate), through MCP tools, not only as the final answer of a chat-started turn.
- An agent can send several messages in a row without a user reply in between (follow-ups), including while a chat-started turn is still running.
- An agent can reply to a specific chat message (quoted reply) and react to a message with an emoji.
- An agent can list the rooms it may post to and read the delivery status of what it sent.
- Agents may post only to policy-allowed rooms that are bound to their session or flagged agents_may_initiate (off by default, set per room by the user); the agent token never leaves the orchestrator.
- The user's next chat message after an agent-initiated or follow-up message reaches the session that last spoke in the room while it runs.
- Docs, tests (unit, contract, e2e) and a live smoke in the owner DM covering send without inbound, quoted reply and reaction.

## Non-goals

- No automatic forwarding of every final reply of every turn to the chat (agents use the send tool).
- No posting to arbitrary allowed rooms; no raw Matrix event ids from agents.
- No member-agent (non-leader) chat tools; members report through their leader.
- No other chat channels (Slack, Telegram); one upstream only.
- No change to the inbound allow/deny policy model.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
