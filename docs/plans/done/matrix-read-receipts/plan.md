---
title: matrix read receipts
repos: [agents-matrix-connector, agents-helmfile]
created: 2026-10-26
owner: Szymon Richert
rung: 1
---

# matrix read receipts

## What and why

What: the connector marks allowed Messenger messages as read when it hands them to the agent
How: a MatrixClient.send_receipt call in the worker's post-handoff step next to typing, then a connector re-pin and apply
Why: the user's messages stay unread in Messenger although the agent answers

User request 2026-10-26, verbatim: 'Add read receipts'. Context: after the agents-matrix-connector deploy the user noticed their Messenger messages stay unread even when the agent answers; the connector never sends a Matrix read receipt, so mautrix-meta never marks the Messenger message seen.

User decision 2026-10-26 (AskUserQuestion): "On handoff": mark read once the message is delivered to the agent session, in the same step that starts the typing indicator; only in allowed chats.

## Scope ladder

### Rung 1: agreed scope (migrated)

- 1.1: G1: when a batch of allowed inbound messages is handed to an agent session (first dispatch or delivery into a running session), the connector sends an `m.read` receipt for the newest event of that batch, best-effort like the typing indicator.
- 1.2: G2: messages that are never handed off (denied, not_allowed, no_preset, ignored, failed before handoff) never get a receipt.
- 1.3: G3: the change is live: the connector release is re-pinned and applied, and a real Messenger message in the owner DM shows as seen.

## Agreed scope

Rung 1, migrated from the epic format: the epic's goals were its agreed scope.

## Non-goals

- No `m.fully_read` read markers, no private receipts, no receipts for the bot's own outbound messages.
- No configuration switch for receipts (always on for handed-off messages).
- No change to typing, policy or the API.

## Design

Migrated from the epic format; the design sections without a plan.md heading are under Migrated notes.

## Decisions

- D1 (user 2026-10-26, "On handoff"): the receipt is sent in `Worker._delivered`, the step that runs after both a first dispatch and a delivery into a running session and that already starts the typing indicator. So "seen" means "the agent has it".
- D2 (my call): one `m.read` receipt per batch, for the newest event (greatest `origin_ts`, then greatest row `id`). A receipt on the newest event implies all earlier ones, as the Matrix spec defines receipts, so one call per batch is enough.
- D3 (my call): best-effort, like typing. A `MatrixError` is a warning and never fails the run, so a homeserver hiccup cannot cost an agent reply.
- D4 (my call): only handed-off rows get receipts, which means only allowed chats with a preset. A denied stranger never sees "seen" from the bot's Facebook account.
- D5 (my call): public `m.read` receipt, not `m.read.private`, because mautrix-meta bridges the logged-in user's public read receipts to Messenger as "seen". This is checked live in apply-receipts-live, AC3.

## Open questions

none

## Research

- Lenses: all skipped. research-docs: the receipt endpoint `POST /_matrix/client/v3/rooms/{roomId}/receipt/{receiptType}/{eventId}` is a stable client-server API, the call is the same shape as the existing typing call, and the live AC3 proves the bridge behaviour. research-code-internal: the hook point (`Worker._delivered`) and the client pattern (`MatrixClient.typing`, `_path`, `_request`) were read directly. research-code-external and research-papers: no fork, no algorithmic core.

## Irreversible operations

none

## Migrated notes

### README.md: Review

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

### design.md: Size

Full by rule (two repos, a live deploy), but small: one behaviour in the connector plus a re-pin and apply. 3 tasks.

### design.md: Deploy

- The connector PR merges first, then its main CI publishes chart and image `0.1.0-main.<sha7>`, then the helmfile re-pin is made, and the apply goes through the main session (APPLY REQUEST), as in agents-matrix-connector-depl.
- Irreversible operations: none. The apply rolls the connector Deployments only.

### design.md: Builder check answers (my call)

- Newest event: a NULL `origin_ts` sorts lowest, and the greatest row `id` breaks ties.
- A batch can hold several senders, as in group chats. One receipt on the newest event covers them all, which is the intent.
- The fake homeserver only records `(room_id, receipt_type, event_id)` and answers unknown rooms as the other routes do. It does not check who the caller is.
- The orchestrator puts the merge `<sha7>` into the dispatch prompt of connector-repin-receipts and apply-receipts-live.
- For apply-receipts-live AC3, the orchestrator asks the user to send one message and to confirm "seen". The implementer reads the log and API evidence.
