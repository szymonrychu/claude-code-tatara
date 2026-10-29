# Agents send pictures to the chat design

## Summary

Agents send a picture from their session workspace to their chat room. A new plugin tool
`orchestrator_chat_send_image {path, caption?, room?, reply_to?}` calls a new orchestrator route that
reads the file from the calling agent's own wrapper (at most 8,000,000 bytes) and relays it as base64
JSON to the connector. The connector checks the type from the file's first bytes and queues a `sends`
row of kind `image`. The bot uploads the bytes to Synapse before claiming the send, clears them, and
sends `m.image`; a caption follows as a separate `m.text`. The session web chat draws the picture in the
tool-call box from the session download route; the Chats page shows "picture: <name>". A bridge error
notice replying to one of our events marks that agent send failed. Source decision:
`.scratchpad/pictures/architecture.md` (architect-researcher, opus, 2026-10-28), rechecked against main in
`.scratchpad/pictures/delta-2026-10-29.md`.

## Intent and why

User, verbatim (chat 2026-10-27 20:13Z): "Another epic. Allow agents to send pictures over the chat. Eg
skill would search for a meme, or a mtg card when someone would write something matching contextually
(it's just an example, not a part of the epic)." 20:52Z: "Pictures at the end of the queue." Agents can
only send text and reactions today (matrix-connector-agent-initi, merged). The picking skill is the
user's example and not part of this epic; the epic provides the capability any skill would call.

## Goals

As in README.md G1-G5.

## Non-goals

As in README.md. In short: no URL fetching by our services, no picture-picking skill, no pictures in
chat-started final answers or inbound, no image bytes on the Chats page, no wrapper/any-mcp/common change.

## Anti-goals

- The Matrix token leaves the bot pod, or the api pod uploads media.
- Any service of ours fetches remote content (SSRF surface), or the web renders an `<img>` from message
  text or a remote URL.
- A tool reads an arbitrary file outside the session workdir, or bytes of a non-image (a credentials file)
  reach the chat.
- Image bytes are loaded into every `SendRow` read, or stay in Postgres after the upload.
- A text send or reaction behaves differently than before (regression in the merged outbound path).
- A second chat-tool allow list, or trigger sessions gaining the image tool.

## Constraints

- AGENTS.md: services talk only over HTTP or a queue; one writer per table; queue rows change only through
  status-guarded updates; Python, plus TypeScript for the web; no backward-compat shims.
- The Matrix token lives only in the connector bot pod (connector AGENTS.md).
- Orchestrator chat relay is JSON, 256 KiB body cap (`_capped_body`, api/chat.py:97), 10 s timeout, stores
  nothing. Only api/workspace.py may import wrapper (tests/test_api_sessions.py:237).
- any-mcp HTTP timeout 30 s (any-mcp http.py:31).
- mautrix-meta v26.09: jpeg/png/gif/webp up to 8,000,000 bytes; captions dropped in Meta-E2EE chats; pre-send
  checks need `info.mimetype` and `info.size` (probes.md, brief-docs.md).
- Synapse v1.163.1, authenticated media: upload `POST /_matrix/media/v3/upload`, limit from
  `GET /_matrix/client/v1/media/config`.
- Release numbers are claimed by earlier epics: plugins v0.3.0 (slash-commands-from-chat), v0.4.0
  (hive-decoupling), v0.5.0 (immediate-message-delivery-w); connector migration 0003
  (immediate-message-delivery-w, `0003_run_relayed_turn.sql`). This epic builds last in the cct2 queue.

## Decisions

### D1: Picture source is a workspace path

The tool takes `path`, absolute under the session workdir or relative, normalised by
`api/agent.py:_normalise` (:261); invalid is 400 `invalid_path`. No URL argument. Agents fetch pictures with
their own tools (open egress, WebFetch, curl) and pass the saved path. Alternatives: URL fetch by our
services (full SSRF handling, fetch next to the owner's Messenger identity), both (two paths), base64 in the
tool input (blows the 256 KiB cap; tool input is stored untruncated in events and SSE). User question Q2.

### D2: The orchestrator reads the bytes from the caller's own pod

- Plugin: a plain declarative HttpBinding tool `orchestrator_chat_send_image {path, caption?, room?,
  reply_to?}` -> `POST /agent/v1/chat/images`, separate from chat_send so chat_send stays a pass-through.
- Route in api/chat.py runs exactly the checks of `_relay` (require_agent, 403 `trigger_session`, `_leads`,
  chat_available, `_capped_body`) by sharing them, not copying them; it parses only `path`.
- Seam `read_file_bytes(conn, settings, http, session_id, agent_id, path, max_bytes)` in api/workspace.py
  over `resolve_agent` and `WrapperClient.open_download`; reads at most max+1 bytes (413 `image_too_large`)
  inside `asyncio.timeout(10)`, maps errors with `_wrapper_errors` (404 `not_found` etc.). chat.py imports
  workspace, not wrapper, so the layering test stays unchanged.
- (review fix) The seam takes the pool, not a connection: it resolves the agent under `pool.connection()` and releases it before the read, and no connection is held during the upstream POST (interrogate Act on 4; orch-chat-images-route).
- Then POST JSON `{data: base64, path, caption?, room?, reply_to?}` to `{ORCH_CHAT_URL}/chat/v1/images`;
  status and body pass through unchanged (D2 of the merged epic). Worst case 10 s + 10 s, under 30 s.
- Alternatives rejected: agent-side handler reading the file (first non-declarative tool, re-implements
  auth, reads any file in the pod, two byte hops); connector fetching from the workspace download
  (widens service auth to every session's files, token holder fetches, TOCTOU); upload at queue time (api has
  no token); connector storage (no shared volume); separate blob table (two writers).

### D3: Connector image route and storage on the sends row

- `POST /chat/v1/images` in the agent listener, body cap 12 MiB on this route only (new code: the connector
  has no body cap today).
- Order: body cap, decode base64, refs/room/slug checks as `queue` does, sniff magic bytes, size, caption
  0-4000; then under the existing advisory locks: duplicate first, then rate, image sub-rate and room cap
  (D5 order, delta fix-as-ac).
- Inserts `sends(kind='image', status='queued')` with `image` bytea, `image_mime`, `image_size`,
  `image_sha256`, `image_name` (basename of path), `image_path`; caption in `text`. Answers 202
  `{id: "s<n>", status, path}`.
- Migration `<MIGRATION>_send_images.sql` (the next free connector number at build time; 0003 is claimed):
  widens the sends.kind CHECK to message|reaction|image, adds the image columns, adds `outbound.content`
  jsonb NULL (full event content when set) and widens the outbound kind CHECK as needed. 0002 is not edited.
- `_COLUMNS`/`SendRow` never select the `image` bytea; only the upload step reads it by id.
- `sends.insert` kind check and `_txn_ids` accept image rows.

### D4: Bot uploads before claiming

1. For each queued image send whose bytes are present, a read-only authorisation pre-check (same rules as
   the claim); on failure the claim step refuses it as today.
2. Check size <= `m.upload.size` (media config cached 1 h; unknown means our cap).
3. Upload (filename = image_name, Content-Type = image_mime) outside any transaction.
4. One claim transaction as today (queued->sending, authoritative re-check and binding), which also sets
   `mxc_uri`, sets `image = NULL`, and inserts outbound rows `mxa-<send>-i` (m.image, reply relation) and,
   with a caption, `mxa-<send>-1` (m.text).
- `claim_queued` skips image rows whose upload has not succeeded in this tick.
- `_place` does not fail a caption-less image as `empty_text`.
- Upload failures: 413 or 403 M_FORBIDDEN -> guarded queued->failed `upload_rejected:<errcode>`; 429, 5xx,
  transport -> retry next tick until created_at + 600 s, then failed `upload_failed`.
- A crash between upload and claim re-uploads next tick; the orphan media on our own Synapse is accepted.
- One writer holds: the api inserts sends; the bot transitions them, clears bytes and prunes; outbound stays
  bot-only.
- (review fix) An image is placed only with its `mxc_uri`: a pre-check refusal (None in `ready`) ends refused with that reason, bytes cleared, never placed; the pre-check and the claim share one pure room/binding decision; the upload pass stops at the first MatrixUnavailable so text and reaction claims of the tick still run (interrogate Act on 1, 3 and Consider; mxc-send-images-schema, mxc-bot-image-upload).

### D5: Matrix content

- `MatrixClient.upload_media(data, mime, filename) -> mxc` on `/_matrix/media/v3`, raw content, the same
  error, 429 and redaction handling as `_request`; `media_config()` on `/_matrix/client/v1/media/config`.
- `m.image`: `{msgtype: m.image, body: name, filename: name, url: mxc, info: {mimetype, size}}` plus
  `m.relates_to.m.in_reply_to` when reply_to is given. No width/height (my call: optional, the bridge checks
  only mimetype and size; avoids Pillow or a header parser).
- Caption always a separate `m.text` after the picture (Messenger E2EE drops image captions). User Q4.
- Fake homeserver grows the upload and media-config routes.

### D6: Bridge error notices fail agent sends

Before the bridge-bot skip in the sync loop (discovery.py:132, sync.py:470), the bot checks one thing: a
bridge-bot `m.notice` whose `m.relates_to.m.in_reply_to.event_id` equals a sent outbound row of an agent
send. On a match the outbound row goes sent->failed and the send sent->failed with reason
`bridge: <notice body>`, both guarded; orchestrator_chat_status shows it. Applies to all agent sends, not
only images. parse_message stays unchanged. User Q6.

(review fix) A row failed by a bridge notice counts as reached the room (it has an `event_id`): settle releases the initiation only when no row reached the room, so the binding is the same whichever lands first, notice or settle (interrogate Act on 2; mxc-bridge-error-notices).

### D7: Limits

- Types by magic bytes only: jpeg `FF D8 FF`, png `89 50 4E 47 0D 0A 1A 0A`, gif `GIF87a`/`GIF89a`, webp
  `RIFF....WEBP`; anything else (SVG included) 422 `unsupported_image`.
- Size 1..`MATRIX_IMAGE_MAX_BYTES` (default and maximum 8,000,000). Orchestrator read cap fixed 8,000,000.
  The bot also enforces `m.upload.size`.
- Images count toward `MATRIX_AGENT_RATE_PER_MINUTE` (20); sub-limit `MATRIX_AGENT_IMAGE_RATE_PER_MINUTE`
  (default 5) per session on kind image -> 429 `rate_limited`. User Q5.
- Room hourly cap (`MATRIX_AGENT_ROOM_CHUNKS_PER_HOUR`, `_chunk_count`): an image counts as 1 event plus its
  caption chunks.
- Duplicate: same session, room, kind image, image_sha256, caption and reply_to within 60 s returns the
  existing send.
- D10 duplicate-final (`message_sends_since`): an image send's caption counts as its text.

### D8: Web UI

- Session ChatView: a renderer for tool items named `*orchestrator_chat_send_image*` with status ok and a JSON
  result containing `path` draws `<img src={fileDownloadUrl(sessionId, path)} loading="lazy">` at most 320 px
  wide, opening the full file on click, with "picture no longer in the workspace" on error; the tool JSON
  box stays below. Session-level download (all agents of a session share one workdir, probes.md). User Q1.
- Markdown.tsx unchanged; agents-web MEMORY.md records "the only `<img>` is the chat-image tool renderer,
  same-origin download route only, never markdown or remote URLs".
- Chats page: MessageView grows `msgtype` (from outbound.content); RoomMessages shows "picture: <name>" for
  m.image. No bytes served by the connector, no mxc proxy. User Q3.

### D9: Releases, pins and contracts with build-time numbers

- Placeholders, as hive-decoupling does: `<MIGRATION>` (next free connector migration), `<TAG>`/`<VERSION>`
  (next free plugins minor, expected v0.6.0). The first task that needs one reads the real number from main
  at build time and amends the dependent tasks (`ticket.py amend`); no number is assumed. The connector
  migration test is named `test_send_images_migration` without the number.
- Orchestrator: pin `<TAG>` and add the tool to `CHAT_TOOLS` (k8s/on_start.py:31) in one change (D13 probe);
  trigger sessions keep losing every chat tool (:43). Refresh the vendored contract
  `tests/fakes/chat_openapi.*` from connector main (already stale) with the new route.
- Release and deploy order: plugins, connector, orchestrator, web, helmfile (image tags, chart versions,
  `ORCH_ANY_MCP_PLUGINS_REF: <TAG>`, connector image settings).

### D10: Live smoke

After the helmfile apply (deploy lease taken), the session posts one real picture with a caption to the
owner's Messenger DM through the tool; the owner confirms in Messenger; the web chat shows the picture;
orchestrator_chat_status shows the send `sent`. User Q7.

## Research

| Lens | Ran / skipped | Adopted | Rejected |
|---|---|---|---|
| start-discovery (cartographer) | ran 2026-10-28, `.scratchpad/pictures/brief-cartographer.md`; delta 2026-10-29 `delta-2026-10-29.md` | chat path map, mount render.py:43 | - |
| research-code-internal (reuse-hunter) | ran, `brief-reuse.md`; delta refreshed reuse list | `_relay` checks, `resolve_agent`, `open_download`, advisory locks, `send_event`, `release_initiation` | agent_id on the web download (session-level instead, D8) |
| research-docs | ran, `brief-docs.md` | Synapse v3 upload + v1 media config; m.image fields (Matrix spec v1.19 content-repo.yaml); bridgev2 notice shape (mautrix/go bridgev2/messagestatus.go ToNoticeEvent); meta caps (mautrix/meta pkg/connector/capabilities.go) | thumbnails, width/height |
| research-code-external | skipped: the analogue (Matrix bots posting media) is covered by the spec and bridge source read in research-docs; no open fork left after the architecture decision | - | - |
| research-papers | skipped: no scientific core | - | - |
| architect-researcher | ran (opus), `architecture.md` | D1-D9 | URL source, agent-side handler, connector fetch, blob table |

## Research inputs

- `_relay` now 403s trigger sessions; image route shares its checks (delta, chat.py:155) - orch-chat-images-route.
- `claim_queued` claims every queued row (db/sends.py:116) - mxc-send-images-schema, mxc-bot-image-upload.
- `_place` fails empty text as `empty_text` (sender.py:167) - mxc-bot-image-upload.
- No connector body cap exists - mxc-images-route.
- Advisory-lock block and room cap in `queue` (api/agent.py:306, :257) - mxc-images-route.
- Vendored chat contract stale (tests/fakes/chat_openapi.source pins 0380120) - orch-chat-contract-refresh.
- CHAT_TOOLS excludes trigger sessions (on_start.py:43) - orch-plugins-pin-and-tool.
- Migration 0003 and plugins v0.3.0-v0.5.0 claimed - mxc-send-images-schema (`<MIGRATION>`), plugins-release-images (`<TAG>`/`<VERSION>`), amending orch-plugins-pin-and-tool and helmfile-pictures-pin (D9).
- Inbound `m.image` stays Unsupported and bridge-bot events stay skipped by `parse_message` (brief-cartographer fix-as-ac, discovery.py:141) - mxc-bridge-error-notices.
- `outbound.body NOT NULL` (0001_init.sql:110): the image row's body is the picture name, its content in `outbound.content` (brief-cartographer fix-as-ac) - mxc-send-images-schema, mxc-room-messages-msgtype.

Retro proposals (`ticket.py retro --history`, 2026-10-29), recurring workflow ones first:

- recurring, matrix-connector-agent-initi (also deploy-safe-agent-sessions, parked-epic-stage): task files with empty Steps; the planner writes Steps before the gate - every task of this epic carries Steps.
- recurring, matrix-connector-agent-initi (also deploy-safe-agent-sessions, file-editor-with-tabs-and-hi): defects that passed per-task review surfaced only in the epic review; check per task the security list for tools that send on a user's behalf (rate and size limits, session trust) and a size cap on every route that accepts a body - mxc-images-route, orch-chat-images-route, mxc-bot-image-upload (their acceptance conditions name each limit, cap and trust check).
- recurring, matrix-connector-agent-initi (also deploy-safe-agent-sessions, file-editor-with-tabs-and-hi, file-download-in-file-browse): no Docker in agent pods makes DB tests CI-only - every agents-matrix-connector task names its DB-backed tests as CI-gated and keeps a pure test for local signal; orchestrator tasks use the non-DB fakes.
- recurring, matrix-connector-agent-initi (also deploy-safe-agent-sessions): a live apply surfaced a defect tests did not; read `mise run diff` before every apply and render the releases first - pictures-live-smoke.
- recurring, file-editor-with-tabs-and-hi: the deploy depends on Harbor holding the pinned tags; check each tag before pinning and before applying - helmfile-pictures-pin, pictures-live-smoke.
- recurring, matrix-connector-agent-initi (also deploy-safe-agent-sessions, file-editor-with-tabs-and-hi): leadership handovers lose state; the pod-rolling apply is preceded by a handoff checkpoint and results go to the task Notes as they happen - pictures-live-smoke.
- recurring, matrix-connector-agent-initi (seeds by task kind, epic-run writing actuals at every close): orchestrator tooling, no task in this epic.
- deploy-safe-agent-sessions, Delivered differently: a release task was marked done before its artifact existed - plugins-release-images (the tag must exist on origin and carry the tool before done).
- deploy-safe-agent-sessions, Tech debt: web must deploy after the orchestrator - pictures-live-smoke applies connector, orchestrator, web in that order.
- matrix-connector-agent-initi, Delivered differently: web `openapi/matrix.source` pinned a connector epic-branch commit, kept reachable by a merge commit - orch-chat-contract-refresh, web-room-messages-picture.
- file-editor-with-tabs-and-hi, Code: a byte cap literal that mirrors another component's limit should be pinned by a test - orch-chat-images-route (8,000,000 read cap) and mxc-images-route (`MATRIX_IMAGE_MAX_BYTES` maximum 8,000,000).

## Decision coverage

Every design decision (`### D<n>` above) maps to the task(s) that deliver it, by task slug.

| Decision | Tasks |
|---|---|
| D1 Picture source is a workspace path | plugin-chat-send-image, orch-chat-images-route |
| D2 The orchestrator reads the bytes from the caller's own pod | plugin-chat-send-image, orch-chat-contract-refresh, orch-chat-images-route |
| D3 Connector image route and storage on the sends row | mxc-send-images-schema, mxc-images-route |
| D4 Bot uploads before claiming | mxc-send-images-schema, mxc-bot-image-upload, mxc-e2e-image-send |
| D5 Matrix content | mxc-matrix-media-upload, mxc-bot-image-upload, mxc-e2e-image-send |
| D6 Bridge error notices fail agent sends | mxc-bridge-error-notices, mxc-e2e-image-send |
| D7 Limits | mxc-send-images-schema, mxc-images-route, orch-chat-images-route, mxc-bot-image-upload |
| D8 Web UI | web-chat-image-tool, mxc-room-messages-msgtype, web-room-messages-picture |
| D9 Releases, pins and contracts with build-time numbers | mxc-send-images-schema, plugins-release-images, orch-chat-contract-refresh, orch-plugins-pin-and-tool, helmfile-pictures-pin |
| D10 Live smoke | pictures-live-smoke |

## Review focus

- Image bytes never loaded by `SendRow` reads; cleared on claim; never logged.
- Status-guarded transitions for upload failures and bridge-notice failures; one writer per table.
- The image route shares `_relay`'s checks, including trigger_session, and reads only inside the session
  workdir via the wrapper.
- Magic-byte sniffing is the only type authority; SVG refused.
- No regression in text sends, reactions, D10 duplicate-final or the room cap.

## Left to the builder

- Module layout inside each repo (e.g. a connector `images.py` for sniffing), helper names, test file split,
  within the D-decisions above.
- How the media config cache is held (in-process, 1 h).
- Q1 (my call, builder-check): the connector tasks merge to connector `main` first; orch-chat-contract-refresh and web-room-messages-picture pin the connector `main` sha, not an epic-branch commit.
- Q3 (my call, builder-check): caption rows keep outbound kind `agent`, a second `add_outbound` call in the same claim transaction, the picture row first by id (mxc-bot-image-upload Notes).
- Q4 (my call, builder-check): superseded by interrogate Act on 1 (D4 review fix; mxc-send-images-schema ac5, mxc-bot-image-upload ac5 and ac14).
- Q5 (my call, builder-check): orch-plugins-pin-and-tool may edit `tests/test_images.py` only for the pin literals; it is in that task's files.
- Q6 (my call, builder-check): the builder builds the code tasks only; the `ticket.py amend` calls (placeholders, sha7s), the `<TAG>` push, the Harbor checks, the helmfile apply and the smoke (plugins-release-images ac3-ac5, helmfile-pictures-pin ac5-ac7, pictures-live-smoke) are orchestrator-session work, as those tasks already mark.

## Assumptions and unknown facts

- Synapse `max_upload_size` is unknown (needs a user token); the bot reads it at runtime via media config
  and the smoke confirms it.
- mautrix-meta limits were read from main, not the deployed tag; the smoke and D6 cover a mismatch.
- RGW/Synapse orphan media after a crash: accepted.
- Q2 (my call, builder-check): the build starts only after slash-commands-from-chat, hive-decoupling and immediate-message-delivery-w are merged, with plugins v0.5.0 tagged and connector migration 0003 on main, so `<MIGRATION>`, `<TAG>` and `<VERSION>` are read from main; otherwise the orchestrator session stops and reports.
- Q7 (my call, builder-check): pod memory limits are out of scope; the connector limit is 384Mi (agents-helmfile chart values.yaml:88,94), above the 30-40 MB per-request peak under the 5/min image rate.

## Open questions

- Q1: Show pictures in the session web chat too? [answer: yes (user approved the gate 2026-10-29 10:06Z via mx-34 #375, verbatim: "Images: all yes")]
- Q2: Workspace paths only, no URL argument? [answer: yes (user approved the gate 2026-10-29 10:06Z via mx-34 #375, verbatim: "Images: all yes")]
- Q3: The Chats page shows a "picture: <name>" line, not the image? [answer: yes (user approved the gate 2026-10-29 10:06Z via mx-34 #375, verbatim: "Images: all yes")]
- Q4: Send the caption as its own message after the picture? [answer: yes (user approved the gate 2026-10-29 10:06Z via mx-34 #375, verbatim: "Images: all yes")]
- Q5: Limit pictures to 5 a minute per session (inside the 20 sends a minute)? [answer: yes (user approved the gate 2026-10-29 10:06Z via mx-34 #375, verbatim: "Images: all yes")]
- Q6: A bridge error notice marks any agent send failed, text included? [answer: yes (user approved the gate 2026-10-29 10:06Z via mx-34 #375, verbatim: "Images: all yes")]
- Q7: The live smoke posts one real picture with a caption to your Messenger DM? [answer: yes (user approved the gate 2026-10-29 10:06Z via mx-34 #375, verbatim: "Images: all yes")]
- Q8: No pictures inside chat-started final answers in this epic? [recommended: yes]

## Irreversible operations in scope

- Connector migration `<MIGRATION>_send_images.sql` (additive: columns, widened CHECKs) applied on deploy;
  covered by the gate.
- Releases: plugins tag `<TAG>`, connector, orchestrator and web image tags; covered by the gate.
- helmfile apply under the deploy lease.
- One real Messenger message (the smoke picture) to the owner's DM (Q7).
