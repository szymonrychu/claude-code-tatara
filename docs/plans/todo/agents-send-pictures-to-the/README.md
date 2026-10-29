---
title: Agents send pictures to the chat
blockers: [slash commands from chat, hive decoupling, immediate message delivery]
stage: build
owner: ""
repos: [any-mcp-tatara-plugins, agents-matrix-connector, agents-orchestrator, agents-web, agents-helmfile]
created: 2026-10-29
---

# Agents send pictures to the chat

## Project brief

What: Agents send a picture file from their session workspace to their chat room (Matrix/Messenger) and see it in the session web chat.
How: New plugin tool orchestrator_chat_send_image; the orchestrator reads the file from the caller's wrapper and relays base64 JSON to the connector, which queues an image send; the bot uploads to Synapse and sends m.image; the web chat renders the tool result from the session download route.
Why: User, 2026-10-27 20:13Z: 'Allow agents to send pictures over the chat.' (cct2 queue item 5, last in the user's order).

## Description

User brief, verbatim (chat 2026-10-27 20:13Z): "Another epic. Allow agents to send pictures over the chat. Eg skill would search for a meme, or a mtg card when someone would write something matching contextually (it's just an example, not a part of the epic)." And at 20:52Z: "Pictures at the end of the queue."

Today agents can only send text and reactions to a chat (orchestrator_chat_send, orchestrator_chat_react from matrix-connector-agent-initi). This epic adds one tool, orchestrator_chat_send_image, that takes a picture file from the session workspace. The orchestrator reads the bytes from the calling agent's own wrapper and relays them to the connector, which validates and queues them; the bot (the only Matrix token holder) uploads them to Synapse and sends m.image, with an optional caption as a separate text message. The session web chat shows the picture inside the tool-call box from the session download route; the Chats page shows a "picture: <name>" line. A bridge error notice replying to one of our events marks that agent send failed. Discovery: .scratchpad/pictures/ (architecture.md, briefs, probes, baselines, delta-2026-10-29.md). Design: design.md.

It builds last in the cct2 queue, on top of slash-commands-from-chat (plugins v0.3.0), hive-decoupling (plugins v0.4.0) and immediate-message-delivery-w (plugins v0.5.0, possibly connector migration 0003); its release and migration numbers are placeholders resolved at build time.

## Goals

- G1: an agent sends a picture (jpeg, png, gif or webp, judged by content, at most 8,000,000 bytes) from a file in its session workspace to its chat room through a new tool orchestrator_chat_send_image {path, caption?, room?, reply_to?}; the owner sees it in Messenger through the bridge.
- G2: the Matrix token stays in the bot pod: the bot uploads the bytes and sends m.image; the caption goes as its own text message after the picture; reply_to anchors the picture.
- G3: the session web chat shows the sent picture inside the tool-call box from the same-origin session download route; message text still never renders images; the Chats page shows "picture: <name>".
- G4: limits and failures are explicit: unsupported type, too large, missing file and rate (5 pictures a minute per session inside the 20 sends a minute) refuse synchronously with a named error; upload failures and bridge error notices mark the send failed, visible in orchestrator_chat_status.
- G5: released and deployed in order (plugins, connector, orchestrator, web, helmfile) and proven by a live smoke that posts one real picture with a caption to the owner's Messenger DM.

## Non-goals

- URL sources: no service of ours fetches a picture from the internet; agents fetch with their own tools and pass a workspace path.
- Skills that pick pictures contextually (meme or MTG card search): the user's example, not part of the epic.
- Pictures in chat-started final answers (the tracker's reply path) and inbound pictures from the chat to agents.
- Image bytes on the Chats page, thumbnails, width/height, or keeping pictures after the session or file is deleted.
- Changes to claude-code-wrapper, any-mcp or agents-common.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
