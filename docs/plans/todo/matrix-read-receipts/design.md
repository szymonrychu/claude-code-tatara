# matrix read receipts - design

## Size

Full by rule (two repos, a live deploy), but small: one behaviour in the connector plus a re-pin and apply. 3 tasks.

## Decisions

- D1 (user 2026-10-26, "On handoff"): the receipt is sent in `Worker._delivered`, the step that runs after both a first dispatch and a delivery into a running session and that already starts the typing indicator. So "seen" means "the agent has it".
- D2 (my call): one `m.read` receipt per batch, for the newest event (greatest `origin_ts`, then greatest row `id`). A receipt on the newest event implies all earlier ones, as the Matrix spec defines receipts, so one call per batch is enough.
- D3 (my call): best-effort, like typing. A `MatrixError` is a warning and never fails the run, so a homeserver hiccup cannot cost an agent reply.
- D4 (my call): only handed-off rows get receipts, which means only allowed chats with a preset. A denied stranger never sees "seen" from the bot's Facebook account.
- D5 (my call): public `m.read` receipt, not `m.read.private`, because mautrix-meta bridges the logged-in user's public read receipts to Messenger as "seen". This is checked live in apply-receipts-live, AC3.

## Research

- Lenses: all skipped. research-docs: the receipt endpoint `POST /_matrix/client/v3/rooms/{roomId}/receipt/{receiptType}/{eventId}` is a stable client-server API, the call is the same shape as the existing typing call, and the live AC3 proves the bridge behaviour. research-code-internal: the hook point (`Worker._delivered`) and the client pattern (`MatrixClient.typing`, `_path`, `_request`) were read directly. research-code-external and research-papers: no fork, no algorithmic core.

## Deploy

- The connector PR merges first, then its main CI publishes chart and image `0.1.0-main.<sha7>`, then the helmfile re-pin is made, and the apply goes through the main session (APPLY REQUEST), as in agents-matrix-connector-depl.
- Irreversible operations: none. The apply rolls the connector Deployments only.

## Builder check answers (my call)

- Newest event: a NULL `origin_ts` sorts lowest, and the greatest row `id` breaks ties.
- A batch can hold several senders, as in group chats. One receipt on the newest event covers them all, which is the intent.
- The fake homeserver only records `(room_id, receipt_type, event_id)` and answers unknown rooms as the other routes do. It does not check who the caller is.
- The orchestrator puts the merge `<sha7>` into the dispatch prompt of connector-repin-receipts and apply-receipts-live.
- For apply-receipts-live AC3, the orchestrator asks the user to send one message and to confirm "seen". The implementer reads the log and API evidence.
