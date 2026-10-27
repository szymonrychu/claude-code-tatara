---
title: hive decoupling
blockers: [slash-commands-from-chat, matrix-connector-agent-initi]
stage: build
owner: ""
repos: [agents-orchestrator, any-mcp-tatara-plugins, agents-helmfile]
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

- G1: Members receive no streamed activity: the dispatcher sends no appended feed note, `hive_state` is re-pushed only when the leader, epoch, membership or readiness changes, and `session_leaders.feed_cursor` is dropped.
- G2: Any hive agent pulls recent activity on demand: `GET /agent/v1/activity` (optional `agent`, `limit` 1..200) and the plugin tool `orchestrator_activity`.
- G3: A leader at or above the effective handover threshold (its compaction percentage minus 15) gets one keyed `handover_due` note with ranked successor candidates, their ccw addresses and the handoff protocol; the `hive_state` hint and the plugin advice always use the effective threshold.
- G4: The leader briefs a chosen successor directly over ccw peer messaging, then hands over with `orchestrator_leadership_handover(to=..., epoch=...)`; the requester learns every handover request outcome (applied, or rejected with its reason) as a keyed `leadership_request` note.
- G5: Released and deployed: any-mcp-tatara-plugins next minor tag, orchestrator pins, agents-helmfile bump, apply, a smoke covering the activity route and tool, and a live handoff proof.

## Non-goals

- Any claude-code-wrapper change or release; any agents-web change.
- A digest or summarised stream to members, or a shared journal file.
- An automatic threshold handover by the orchestrator, or any new automatic pick rule.
- An orchestrator-mediated handoff protocol, or a new table or writer for the brief.
- A new `session_leaders.reason` value or stream frame; a per-session switch for the signal or the pull tool.
- Pushing the compact summary to the successor.
- Changing any leader-auto-handover backstop (compaction and scale-down handover, claim hold, reconciler pod hold).
- Rate limiting `activity`; dropping `events.created_at` (the session export reads it).

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
