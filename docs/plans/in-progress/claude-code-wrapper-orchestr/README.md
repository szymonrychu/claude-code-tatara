---
title: claude-code-wrapper orchestrator support
blockers: []
stage: build
owner: Szymon Richert
repos: [claude-code-wrapper]
created: 2026-10-22
---

# claude-code-wrapper orchestrator support

## Project brief

What: seven additive claude-code-wrapper changes (idle_since, user_message event, backward history, GET /v1/peers, statusline relay, context surface, onStart instance hook), each documented in README.md.
How: one task per test file in code/claude-code-wrapper, chained where they share events.py/router.py, verified by targeted pytest plus mise run lint (never the full 11-minute suite).
Why: agent-orchestrator needs idle-longest routing, a context gauge, lazy chat history and a peer view that the wrapper does not expose today.

## Description

claude-code-wrapper gains the API surface agent-orchestrator needs: context-window usage, idle-since, backward history paging, a user_message event and a peer mesh view. All changes are additive and documented in README.md. Design: section 4 of /private/tmp/claude-501/-Users-szymonri-Documents-claude-code-tatara/21d1a847-8d6b-4ee4-a271-ba52ec27cf3b/scratchpad/orch/design-orchestrator.md.

## Goals

- Snapshot and SSE expose context usage (used_tokens, window_tokens, used_percentage) from the statusline relay.
- Snapshot exposes idle_since; session_state carries since.
- History pages backwards (before_seq, types filter).
- A user_message event is emitted for every pasted prompt (user, peer, hook, restart, command origin).
- GET /v1/peers returns the peer mesh view.
- hooks.onStart runs once per process start, before peers, resume or any session (agent-orchestrator installs any-mcp with it).

## Non-goals

- No breaking change to existing routes or events.
- No orchestrator logic inside the wrapper.

## Time

Estimate: 42 agent-min | Critical path: 30 min | Expected wall at P=1.5: 1.0 h (k=2.0) | Actual: 0 min | Remaining estimate: 30 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

## Delivery notes

Another Claude session (claude-code-wrapper-58) actively develops code/claude-code-wrapper from a different clone. Before the PR, rebase this branch onto origin/main and re-run the six targeted verifies; README.md and events.py/router.py are the likely conflict points.
