---
title: claude-code-wrapper orchestrator support
blockers: []
stage: build
owner: ""
repos: [claude-code-wrapper]
created: 2026-10-22
---

# claude-code-wrapper orchestrator support

## Project brief

What: 
How: 
Why: 

## Description

claude-code-wrapper gains the API surface agent-orchestrator needs: context-window usage, idle-since, backward history paging, a user_message event and a peer mesh view. All changes are additive and documented in README.md. Design: section 4 of /private/tmp/claude-501/-Users-szymonri-Documents-claude-code-tatara/21d1a847-8d6b-4ee4-a271-ba52ec27cf3b/scratchpad/orch/design-orchestrator.md.

## Goals

- Snapshot and SSE expose context usage (used_tokens, window_tokens, used_percentage) from the statusline relay.
- Snapshot exposes idle_since; session_state carries since.
- History pages backwards (before_seq, types filter).
- A user_message event is emitted for every pasted prompt (user, peer, hook, restart, command origin).
- GET /v1/peers returns the peer mesh view.

## Non-goals

- No breaking change to existing routes or events.
- No orchestrator logic inside the wrapper.

## Time

Derived by `ticket.py estimate`, `tasks` and `apply-run` from the task `estimate` and `actual` fields into one line (`Estimate | Critical path | Expected wall at P= | Actual | Remaining estimate`); never edit by hand. Report only, never a budget.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
