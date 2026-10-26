---
title: matrix read receipts
blockers: []
stage: review
owner: Szymon Richert
repos: [agents-matrix-connector, agents-helmfile]
created: 2026-10-26
---

# matrix read receipts

## Project brief

What: the connector marks allowed Messenger messages as read when it hands them to the agent
How: a MatrixClient.send_receipt call in the worker's post-handoff step next to typing, then a connector re-pin and apply
Why: the user's messages stay unread in Messenger although the agent answers

## Description

User request 2026-10-26, verbatim: 'Add read receipts'. Context: after the agents-matrix-connector deploy the user noticed their Messenger messages stay unread even when the agent answers; the connector never sends a Matrix read receipt, so mautrix-meta never marks the Messenger message seen.

User decision 2026-10-26 (AskUserQuestion): "On handoff": mark read once the message is delivered to the agent session, in the same step that starts the typing indicator; only in allowed chats.

## Goals

- G1: when a batch of allowed inbound messages is handed to an agent session (first dispatch or delivery into a running session), the connector sends an `m.read` receipt for the newest event of that batch, best-effort like the typing indicator.
- G2: messages that are never handed off (denied, not_allowed, no_preset, ignored, failed before handoff) never get a receipt.
- G3: the change is live: the connector release is re-pinned and applied, and a real Messenger message in the owner DM shows as seen.

## Non-goals

- No `m.fully_read` read markers, no private receipts, no receipts for the bot's own outbound messages.
- No configuration switch for receipts (always on for handed-off messages).
- No change to typing, policy or the API.

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-26)

Epic review of matrix-read-receipts, 2026-10-26.
- Per-task reviews: mxc-read-receipts needed 1 fix round, to pin the id tiebreak. The other tasks were clean.
- Full suites: connector 192 passed, helmfile 184 passed.
- Live:
  - The apply was helm rev 2 (chart 0.1.0-main.98b0803) and post-apply diff showed no drift.
  - Smoke OK on the re-run. The first smoke run failed because the port-forward died; the leftovers were deleted with the user's OK.
  - Receipt POST answered 200, and the user confirmed the message shows as seen.
- Scope audit: clean.
- PRs: agents-matrix-connector #2 (98b0803) and agents-helmfile #27 (d0a1956).
