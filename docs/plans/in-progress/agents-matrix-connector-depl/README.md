---
title: agents matrix connector deploy
blockers: [orchestrator-rename-sessions, agents-matrix-connector]
stage: review
owner: Szymon Richert
repos: [agents-helmfile, agents-web]
created: 2026-10-25
---

# agents matrix connector deploy

## Project brief

What: New microservice agents-matrix-connector that connects to the existing Matrix deployment and lets people talk to agents through Facebook Messenger via the existing mautrix-meta bridge, with user/chat/room auto discovery and allowlist/denylist.
How: A Python service (own repo `code/agents-matrix-connector`, own CNPG database) logs in to the live Synapse (`http://matrix-synapse.messaging.svc.cluster.local:8008`) as a plain bot user with an access token, the way Hermes does; that user is logged in to mautrix-meta with a Facebook account, so every Messenger chat with that account becomes a Matrix portal room the bot is invited to. A sync loop auto-joins invites and records rooms, users and members; a default-deny allow/deny policy decides which messages reach an agent; allowed messages are batched per room and sent through agents-common's orchestrator client to one agents-orchestrator session per room (reused while it runs), and each turn's final text is posted back to the room. A UI API under `/matrix/api/v1` and a Chats page in agents-web list discovered rooms and users, edit the rules and room settings and show recent messages. Deployed through agents-helmfile into namespace `agents`.
Why: User request 2026-10-25: 'agents-matrix-connector New microservice- is meant to connect with existing matrix deployment and allow for talking to agents through facebook. Must support user/chat/room auto discovery and white/blacklosting. Hermes already uses working bridge.'

## Description

The connector has one image and two long-running processes: `api` (UI API, SSO) and `bot` (singleton: Matrix sync, dispatch worker, reply tracker), plus `migrate` as an initContainer. Discovery: every invite is joined; each room is classified from its `m.bridge` state (`dm`, `group`, `infrastructure`) or as a plain `matrix` room, encrypted rooms are marked and never served; members are recorded with their Facebook id parsed from the bridge ghost id. Policy: deny rules win, then allow rules on the room or the sender, else the default policy (deny). Conversation: one session per room from the room's preset (or the default preset), messages arriving while the agent works are queued and sent as the next batch into the same running session; replies are plain text, split at 4000 characters, with a typing indicator while the agent works. Bot user creation, its token and the bridge login are user-run steps outside namespace `agents`. Design: `design.md`.


Split from epic agents-matrix-connector on 2026-10-25 (user decision): this epic holds its agents-helmfile and agents-web tasks, unchanged in scope; the design is docs/plans/{todo,in-progress,done}/agents-matrix-connector/design.md.

## Goals

- G1: the connector runs in namespace `agents` as Matrix user `@agents:szymonrichert.pl` against the live Synapse, and a Messenger message to the connected Facebook account in an allowed chat gets the agent's reply in the same chat.
- G5: the agents-web Chats page lists discovered rooms and users with their access decision, edits the allow and deny rules, a room's preset and trigger and the default preset, and shows each room's recent inbound and outbound messages.
- G6: every capability is reachable headless (README `## API`, committed `openapi.json`, API e2e), and the live namespace runs the connector with a green smoke.

## Non-goals

- End-to-end encrypted rooms (marked `encrypted`, never read or answered).
- Media, reactions, edits, redactions and voice: only `m.text` messages are processed.
- Token streaming of agent output; one message per agent turn.
- Changing Hermes, its Facebook account or its rooms.
- Synapse or mautrix-meta configuration managed from agents-helmfile (they stay in namespace `messaging`, applied by the user).
- Regex or expression rules; rule matching is exact identifiers.
- Other bridges (WhatsApp, Signal, Telegram); they would work as plain Matrix rooms but are not targeted.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
