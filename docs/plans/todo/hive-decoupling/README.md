---
title: hive decoupling
blockers: [matrix-connector-agent-initi]
stage: build
owner: ""
repos: []
created: 2026-10-27
---

# hive decoupling

## Project brief

What: Members stop receiving a truncated stream of the leader's activity; context moves on demand, and a leader near its limit hands over directly to a chosen successor
How: fable-architected design on top of leader-auto-handover: on-demand handoff instead of streamed peer-notes, a limit signal to the leader, a direct leader-successor conversation
Why: Streamed peer-notes consume every member's context on every turn

## Description

User request (2026-10-27, relayed by the mx-5 leader, msg 124), verbatim:

"Decouple agents in session more. Right now non-leaders get truncated stream of what's leader is doing. Ask fable architect to decouple or use handoff or something to consume non-leaders less.
Maybe leader could get a signal to pass on its session details to another agent when it hits a limit and both could talk to each other about details for handoff?"

Relayer's reading: non-leader members get a truncated stream of the leader's activity (seen as peer-notes on every turn), which uses up their context. A fable architect designs a better approach (on-demand handoff instead of streaming, or similar), including a leader-initiated handoff: near its limit the leader gets a signal, picks a successor, and the two talk directly to transfer details. Build on the done epic leader-auto-handover; do not duplicate it.

Queued after matrix-connector-agent-initi.

## Goals



## Non-goals



## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
