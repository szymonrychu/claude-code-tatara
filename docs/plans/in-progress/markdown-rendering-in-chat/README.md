---
title: markdown rendering in chat
blockers: [file-download-in-file-browse]
stage: build
owner: Szymon Richert
repos: [agents-web]
created: 2026-10-27
---

# markdown rendering in chat

## Project brief

What: Chat messages, the user's and the agents', render as markdown
How: safe markdown renderer (GFM, raw HTML off) in the chat entry components
Why: Agent answers and user input are readable: code blocks, lists, tables

## Description

User request (2026-10-27), verbatim:

"## markdown rendering in the chat

as title implies, render markdown in chat window (both for my input and agent's responses)"

## Goals

- Chat messages render as markdown (GFM: headings, lists, emphasis, links, inline code, fenced code blocks, tables), for the user's own messages and the agents' responses.
- Raw HTML in message text is not rendered (shown as text), so message content cannot inject markup.

## Non-goals

- No change to how messages are stored or sent by the backend.
- No markdown editing toolbar or live preview in the composer.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
