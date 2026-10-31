# Agents send pictures to the chat implementation plan

## Agreed rung

Not agreed yet: a draft migrated from the epic's tasks; the plan-writer revises it after the gate.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: mxc matrix media upload

- Status: todo
- Files: `src/agents_matrix_connector/matrix.py`, `src/agents_matrix_connector/fake_homeserver.py`, `tests/test_matrix_client.py`
- Verify: `uv run --frozen pytest tests/test_matrix_client.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G2, verbatim: "the Matrix token stays in the bot pod: the bot uploads the bytes and sends m.image; the caption goes as its own text message after the picture; reply_to anchors the picture."

Design D5, verbatim: "`MatrixClient.upload_media(data, mime, filename) -> mxc` on `/_matrix/media/v3`, raw content, the same error, 429 and redaction handling as `_request`; `media_config()` on `/_matrix/client/v1/media/config`." and "Fake homeserver grows the upload and media-config routes."

Constraint, verbatim: "Synapse v1.163.1, authenticated media: upload `POST /_matrix/media/v3/upload`, limit from `GET /_matrix/client/v1/media/config`."

brief-docs fix-as-ac, verbatim: "Upload sends `Content-Type` and `filename`, and the Matrix access token never appears in a URL or log (existing redaction extended to the new calls)."

brief-reuse fix-as-ac, verbatim: "`MatrixClient._request` sends JSON only and is bound to `/_matrix/client/v3` (`matrix.py:14`, `:190`). AC: an upload takes raw bytes with a content type through the same error and 429 handling, against the media prefix." and "The fake homeserver only answers the `/_matrix/client/v3` prefix (`fake_homeserver.py:65`, `:310`). AC: the fake answers the media upload, so tests do not hit a real server."

Scope (agents-matrix-connector):
- `matrix.py`: one request core for JSON and raw bodies (no second client): `upload_media(data, mime, filename) -> str` posts the raw bytes to `/_matrix/media/v3/upload?filename=<filename>` with `Content-Type: <mime>` and returns `content_uri`; `media_config() -> int | None` reads `m.upload.size` from `/_matrix/client/v1/media/config` (None when absent).
- `fake_homeserver.py`: the upload route (stores bytes, mime and filename, answers `mxc://<server>/<id>`, 413 `M_TOO_LARGE` over a configurable limit, `fail_next` covers it) and the media config route (configurable `m.upload.size`, or absent); an accessor for the recorded uploads.

#### Acceptance conditions

- ac1: upload_media posts the raw bytes to /_matrix/media/v3/upload with the Content-Type and filename given and returns the content_uri [evidence: test:tests/test_matrix_client.py::test_upload_media]
- ac2: media_config returns m.upload.size from /_matrix/client/v1/media/config, and None when the server omits it [evidence: test:tests/test_matrix_client.py::test_media_config]
- ac3: upload errors map like every other call: 413 to MatrixError with errcode M_TOO_LARGE, 403 to MatrixForbidden, 401 and token errcodes to MatrixAuthError, 429 retried once then MatrixUnavailable, 5xx and transport errors to MatrixUnavailable [evidence: test:tests/test_matrix_client.py::test_upload_media_errors]
- ac4: the access token appears in no URL, log line or error text of either call [evidence: test:tests/test_matrix_client.py::test_media_token_redacted]
- ac5: the fake homeserver answers upload and media config, records each upload's bytes, mime and filename, and refuses an upload over its configured limit with 413 M_TOO_LARGE [evidence: test:tests/test_matrix_client.py::test_fake_media_routes]
- ac6: existing client tests pass unedited and lint passes (runs locally, no database) [evidence: command:uv run --frozen pytest tests/test_matrix_client.py && mise run lint]

#### Files

- `src/agents_matrix_connector/matrix.py`
- `src/agents_matrix_connector/fake_homeserver.py`
- `tests/test_matrix_client.py`

#### Interfaces

- `MatrixClient.upload_media(data: bytes, mime: str, filename: str) -> str` (an `mxc://` URI); `MatrixClient.media_config() -> int | None`.
- Fake homeserver: `POST /_matrix/media/v3/upload`, `GET /_matrix/client/v1/media/config`; an accessor returning the recorded uploads; a setter for the upload limit.

#### Expected outcome

The bot can upload a picture to Synapse and read its upload limit through the one thin client, and tests run both against the fake homeserver.

#### Steps

- Red: write the five tests (ac1-ac5); run `uv run --frozen pytest tests/test_matrix_client.py`: they fail (no such methods or routes).
- Green: generalise the request core to a raw body with headers on any prefix, add the two calls and the two fake routes; run the task's verify: passes. Quote the summary line.

#### Notes

- Reuse `_request`'s 429 retry, `_error` mapping and `_redact`; the module docstring counts the client's calls, update the count.
- `tests/test_matrix_client.py` needs no database, so this task's verify runs fully in agent pods.
- The token goes in the `Authorization` header only, never a query parameter (authenticated media).

### S2: mxc send images schema

- Status: todo
- Files: `src/agents_matrix_connector/migrations/<MIGRATION>_send_images.sql`, `src/agents_matrix_connector/db/sends.py`, `src/agents_matrix_connector/db/runs.py`, `tests/test_schema.py`, `tests/test_sends_repo.py`, `tests/test_runs_repo.py`
- Verify: `uv run --frozen pytest tests/test_schema.py tests/test_sends_repo.py tests/test_runs_repo.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G2, verbatim: "the Matrix token stays in the bot pod: the bot uploads the bytes and sends m.image; the caption goes as its own text message after the picture; reply_to anchors the picture."

Design D3, verbatim:
"- Inserts `sends(kind='image', status='queued')` with `image` bytea, `image_mime`, `image_size`, `image_sha256`, `image_name` (basename of path), `image_path`; caption in `text`. Answers 202 `{id: "s<n>", status, path}`.
- Migration `<MIGRATION>_send_images.sql` (the next free connector number at build time; 0003 is claimed): widens the sends.kind CHECK to message|reaction|image, adds the image columns, adds `outbound.content` jsonb NULL (full event content when set) and widens the outbound kind CHECK as needed. 0002 is not edited.
- `_COLUMNS`/`SendRow` never select the `image` bytea; only the upload step reads it by id.
- `sends.insert` kind check and `_txn_ids` accept image rows."

Design D4, verbatim: "4. One claim transaction as today (queued->sending, authoritative re-check and binding), which also sets `mxc_uri`, sets `image = NULL`, and inserts outbound rows `mxa-<send>-i` (m.image, reply relation) and, with a caption, `mxa-<send>-1` (m.text)." and "`claim_queued` skips image rows whose upload has not succeeded in this tick." and "Upload failures: 413 or 403 M_FORBIDDEN -> guarded queued->failed `upload_rejected:<errcode>`; 429, 5xx, transport -> retry next tick until created_at + 600 s, then failed `upload_failed`."

Design D7, verbatim: "Duplicate: same session, room, kind image, image_sha256, caption and reply_to within 60 s returns the existing send." and "D10 duplicate-final (`message_sends_since`): an image send's caption counts as its text."

Delta fix-as-ac, verbatim: "Migration and plugins tag take the next free number (0003 and v0.4.0/v0.5.0 are claimed)." "`claim_queued` skips image rows whose upload has not succeeded this tick." "`_COLUMNS`/SendRow never load the image bytea." "`sends.insert` kind check, `_txn_ids` and the outbound kind CHECK accept the image row." "`message_sends_since` includes image captions (D10)."

User decision (binding), verbatim: "Release numbers are placeholders resolved at build time, exactly as /workdir/workdir/docs/plans/in-progress/hive-decoupling does (read its design.md 'Build-time settlements' and tasks orch-activity-route, plugins-release-0-4-0, orch-plugins-pin-0-4-0, helmfile-deploy-pin for the pattern): <MIGRATION> for the connector migration (0003 is claimed by immediate-message-delivery-w), <TAG>/<VERSION> for the plugins release (v0.3.0-v0.5.0 claimed). The first task needing each reads it from main and amends dependents."

This is the first (and only) task that needs `<MIGRATION>`. Before the first implementer is dispatched the orchestrator session reads the highest `NNNN_*.sql` in `src/agents_matrix_connector/migrations/` on agents-matrix-connector `main` (after immediate-message-delivery-w merged), adds one, and replaces `<MIGRATION>` (four digits) in this task by `ticket.py amend` (Requirement and acceptance conditions) and in its frontmatter `files` and body. The migration test is named `test_send_images_migration` without the number.

Scope (agents-matrix-connector):
- `migrations/<MIGRATION>_send_images.sql`: `sends.kind` CHECK `message|reaction|image`; columns `image bytea NULL`, `image_mime text NULL`, `image_size integer NULL`, `image_sha256 text NULL`, `image_name text NULL`, `image_path text NULL`, `mxc_uri text NULL`; a CHECK that an image row has mime, size, sha256, name and path (my call: the bot cannot build m.image without them); `outbound.content jsonb NULL`; the outbound kind CHECK gains `image`. The table comments stay (tests/test_schema.py::test_writer_comments).
- `db/sends.py`: `SendRow` gains `image_mime`, `image_size`, `image_sha256`, `image_name`, `image_path`, `mxc_uri` and never `image`; an image insert (kind check accepts `image`) storing bytes, mime, size, sha256, name, path and the caption in `text`; `image_bytes(conn, send_id)`, the only read of the bytea; `queued_images(conn)` (queued image rows with bytes present, oldest first, read-only, for the upload step); `claim_queued(conn, now, ready)` where `ready` maps an image send id to its mxc uri, or to None when the pre-check refused it: message and reaction rows are claimed as today, an image row only when its id is in `ready`, and its `queued -> sending` transition sets `image = NULL` and `mxc_uri`; `fail_queued(conn, send_id, reason)`, the guarded `queued -> failed` that also sets `image = NULL`; `count_recent_kind(conn, session_id, kind, seconds)`; `find_duplicate` for images on session, room, kind image, `image_sha256`, caption (`text`) and `reply_to`; `message_sends_since` includes image sends that have a caption.
- `db/runs.py`: `_txn_ids("image", ...)` is exactly `[f"mxa-{send_id}-i"]`, one chunk, a send and no run; `OutboundRow.content`; `add_outbound(..., content=...)` stores the content on the first row only (like `relates_to`); `pending` and `list_outbound` return it.

Review fix, interrogate 2026-10-29 Act on 1 (pre-check refusal becomes a placed image with no mxc; supersedes builder-check Q4), verbatim: "a claimed image without a successful upload this tick is never placed: a None entry fails (guarded) with the pre-check's reason and clears the bytes; an image is placed only with its `mxc_uri`; an authoritative re-check that refuses after upload refuses as today (orphan media accepted)." For this task: `claim_queued(conn, now, ready)` claims an image row mapped to None `queued -> sending` with `image = NULL` and `mxc_uri` NULL, and returns it so the sender refuses it with the pre-check's reason without placing it (task mxc-bot-image-upload); an image row mapped to an mxc uri is claimed with `image = NULL` and that `mxc_uri`; an image row absent from `ready` stays queued with its bytes.

#### Acceptance conditions

- ac1: the migration widens sends.kind to message, reaction and image, adds the image columns, mxc_uri and outbound.content, widens the outbound kind check with image, refuses an image row without mime, size, sha256, name or path, and re-running the migrator is a no-op [evidence: test:tests/test_schema.py::test_send_images_migration]
- ac2: 0001 and 0002 are not edited [evidence: command:git diff --quiet origin/main -- src/agents_matrix_connector/migrations/0001_init.sql src/agents_matrix_connector/migrations/0002_agent_sends.sql]
- ac3: SendRow has no image field and _COLUMNS names no image bytea column (pure test, runs without a database) [evidence: test:tests/test_sends_repo.py::test_send_row_never_loads_image_bytes]
- ac4: an image insert stores kind image, the bytes, mime, size, sha256, name, path and the caption as text; get returns the metadata without bytes; image_bytes returns the exact bytes [evidence: test:tests/test_sends_repo.py::test_image_send_insert_and_bytes]
- ac5: claim_queued claims message and reaction rows as before and an image row only when ready names it; an image mapped to an mxc uri is claimed with that mxc_uri and its bytes cleared; an image mapped to None is claimed with its bytes cleared and mxc_uri NULL; an image row not in ready stays queued with its bytes [evidence: test:tests/test_sends_repo.py::test_claim_skips_unready_images]
- ac6: fail_queued moves a queued send to failed with its reason and clears the bytes, and changes nothing on a send that is not queued [evidence: test:tests/test_sends_repo.py::test_fail_queued_clears_image]
- ac7: an image duplicate matches session, room, kind image, sha256, caption and reply_to within the window; another sha256, caption or reply_to is not a duplicate [evidence: test:tests/test_sends_repo.py::test_image_duplicate]
- ac8: count_recent_kind counts only the session's sends of that kind in the window [evidence: test:tests/test_sends_repo.py::test_count_recent_kind]
- ac9: message_sends_since returns an image send's caption as its text and skips caption-less images and failed or refused sends [evidence: test:tests/test_sends_repo.py::test_message_sends_since_includes_image_captions]
- ac10: _txn_ids gives mxa-<send>-i for an image (one chunk, a send and no run; anything else raises) (pure test) [evidence: test:tests/test_runs_repo.py::test_image_txn_ids]
- ac11: add_outbound stores content on the first row only and pending and list_outbound return it [evidence: test:tests/test_runs_repo.py::test_outbound_content_stored]
- ac12: (orchestrator session, before dispatch) the real next migration number read from connector main replaces <MIGRATION> in this task [evidence: judgement:orchestrator quotes the migrations listed on main and a grep of this task file showing no placeholder left]
- ac13: the schema, sends and runs repo tests and lint pass (DB tests in CI) [evidence: command:uv run --frozen pytest tests/test_schema.py tests/test_sends_repo.py tests/test_runs_repo.py && mise run lint]

#### Files

- `src/agents_matrix_connector/migrations/<MIGRATION>_send_images.sql`
- `src/agents_matrix_connector/db/sends.py`
- `src/agents_matrix_connector/db/runs.py`
- `tests/test_schema.py`
- `tests/test_sends_repo.py`
- `tests/test_runs_repo.py`

#### Interfaces

- `migrations/<MIGRATION>_send_images.sql` (additive).
- `db/sends.py`: `SendRow` (+ `image_mime`, `image_size`, `image_sha256`, `image_name`, `image_path`, `mxc_uri`); the image insert; `image_bytes(conn, send_id) -> bytes | None`; `queued_images(conn) -> list[SendRow]`; `claim_queued(conn, now=None, ready: Mapping[int, str | None] = ...) -> list[SendRow]`; `fail_queued(conn, send_id, reason) -> bool`; `count_recent_kind(conn, session_id, kind, seconds) -> int`; `find_duplicate(...)` for images; `message_sends_since` with image captions.
- `db/runs.py`: `_txn_ids("image", None, send_id, 1) == [f"mxa-{send_id}-i"]`; `OutboundRow.content: dict | None`; `add_outbound(..., content: dict | None = None)`.

#### Expected outcome

The queue can hold an image send whose bytes live on the row only until the bot claims or fails it; every existing reader still gets a `SendRow` without bytes.

#### Steps

- Orchestrator session, before dispatch: read the migrations on connector main and amend `<MIGRATION>` (ac12).
- Red: write `test_send_images_migration`, the sends repo tests (ac3-ac9) and the runs repo tests (ac10, ac11); run `uv run --frozen pytest tests/test_sends_repo.py::test_send_row_never_loads_image_bytes tests/test_runs_repo.py::test_image_txn_ids`: fail locally (the DB tests error without Docker).
- Green: migration, sends and runs repository changes; run the task's verify; quote the local summary line, then the CI run of the pushed head for the DB tests.

#### Notes

- DB-backed tests (testcontainers Postgres) need Docker; agent pods have none, so they error here (baseline 2026-10-29: 182 Docker errors) and CI on the PR is the gate for them (recurring retro). Run the verify, quote the local summary line and the CI run of the pushed head. Keep each pure helper covered by a non-DB test so the local run has signal.
- Every status move goes through `agents_common.db.queue.transition` (status-guarded); the api inserts, the bot moves (one writer per table, design D4).
- Shared files with immediate-message-delivery-w (`db/runs.py`, `runs.relayed_turn_id`): read them as merged on main first.
- `claim_queued` keeps `FOR UPDATE SKIP LOCKED` and oldest-first order; the sender's use of `ready` is task mxc-bot-image-upload.

- 2026-10-29 amended: interrogate 2026-10-29 act on 1

### S3: plugin chat send image

- Status: todo
- Files: `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`, `orchestration/orchestrator/README.md`, `orchestration/orchestrator/tests/test_orchestrator_plugin.py`
- Verify: `uv run --frozen pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py tests/test_nomenclature.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G1, verbatim: "an agent sends a picture (jpeg, png, gif or webp, judged by content, at most 8,000,000 bytes) from a file in its session workspace to its chat room through a new tool orchestrator_chat_send_image {path, caption?, room?, reply_to?}; the owner sees it in Messenger through the bridge."

Design D2, first bullet, verbatim: "Plugin: a plain declarative HttpBinding tool `orchestrator_chat_send_image {path, caption?, room?, reply_to?}` -> `POST /agent/v1/chat/images`, separate from chat_send so chat_send stays a pass-through."

Design D1, verbatim: "The tool takes `path`, absolute under the session workdir or relative, normalised by `api/agent.py:_normalise` (:261); invalid is 400 `invalid_path`. No URL argument. Agents fetch pictures with their own tools (open egress, WebFetch, curl) and pass the saved path."

Design D7 (limits the description names), verbatim: "Types by magic bytes only: jpeg `FF D8 FF`, png `89 50 4E 47 0D 0A 1A 0A`, gif `GIF87a`/`GIF89a`, webp `RIFF....WEBP`; anything else (SVG included) 422 `unsupported_image`." and "Images count toward `MATRIX_AGENT_RATE_PER_MINUTE` (20); sub-limit `MATRIX_AGENT_IMAGE_RATE_PER_MINUTE` (default 5) per session on kind image -> 429 `rate_limited`."

Design D5, verbatim: "Caption always a separate `m.text` after the picture (Messenger E2EE drops image captions)."

Scope (any-mcp-tatara-plugins, orchestrator plugin):
- `__init__.py`: tool `chat_send_image` (rendered `orchestrator_chat_send_image`), `POST /chat/images` under `_BASE`, body `*`, input schema `{path: string (required), caption: string, room: string, reply_to: string}`; its description (below); the `chat_status` description names kind `image` beside message and reaction.
- The tool-count test is no longer accurate (named): on today's main it is `test_lists_fifteen_tools` with the set `FIFTEEN`; the epics before this one (slash-commands-from-chat, hive-decoupling, immediate-message-delivery-w) may have renamed it. It gains `orchestrator_chat_send_image`; read it as merged on main first.
- `orchestration/orchestrator/README.md`: the tool table row and the "always lists all <n> tools" sentence.
- No version bump here (plugins-release-images).

#### Acceptance conditions

- ac1: the plugin lists orchestrator_chat_send_image beside every existing tool, with hive true and false [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_send_image_listed]
- ac2: calling it sends POST /agent/v1/chat/images with exactly the arguments given as the JSON body ({path}, plus caption, room and reply_to when given), the bearer token and X-Orch-Session, and returns the server JSON [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_send_image_calls_agent_route]
- ac3: an error answer becomes a tool error carrying the code and HTTP status, token redacted, for 400 invalid_path, 404 not_found, 413 image_too_large, 422 unsupported_image, 429 rate_limited, 403 trigger_session, 403 not_leader and 503 chat_unavailable [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_send_image_errors_surface_code]
- ac4: the description says Leader only; a file path in the session workspace (absolute under the workdir or relative); no URLs (fetch the picture with your own tools and save it first); jpeg, png, gif or webp judged by content; at most 8,000,000 bytes; at most 5 pictures a minute; the caption goes as its own message after the picture; reply_to anchors the picture and takes m<n> or s<n>; asynchronous, answers s<n>, read the outcome with orchestrator_chat_status [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_send_image_description]
- ac5: the chat_status description names the kinds message, reaction and image [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_descriptions]
- ac6: the plugin README lists the tool and its route [evidence: command:grep -qF '`orchestrator_chat_send_image(path, caption?, room?, reply_to?)` | `POST /agent/v1/chat/images`' orchestration/orchestrator/README.md]
- ac7: the plugin tests, repo tests and lint pass [evidence: command:uv run --frozen pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py tests/test_nomenclature.py && mise run lint]

#### Files

- `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`
- `orchestration/orchestrator/README.md`
- `orchestration/orchestrator/tests/test_orchestrator_plugin.py`

#### Interfaces

- `any_mcp_tatara_orchestrator.OrchestratorPlugin.load_tools`: `spec("chat_send_image", "POST", "/chat/images", _schema({"path": ..., "caption": ..., "room": ..., "reply_to": ...}, ["path"]), "*")`.
- Contract with agents-orchestrator `POST /agent/v1/chat/images` (task orch-chat-images-route): body `{path, caption?, room?, reply_to?}`, 202 `{id: "s<n>", status, path}` passed through from the connector.

#### Expected outcome

The orchestrator plugin offers `orchestrator_chat_send_image`; an agent that sees it knows what it accepts and refuses before calling it.

#### Steps

- Read `__init__.py`, the plugin README and `test_orchestrator_plugin.py` as merged on main (three epics touched them before this one).
- Red: add `test_chat_send_image_listed`, `test_chat_send_image_calls_agent_route`, `test_chat_send_image_errors_surface_code`, `test_chat_send_image_description`, the image kind assertion in `test_chat_descriptions`, and the new name in the tool-count set; run `uv run --frozen pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py`: the new tests fail (unknown tool).
- Green: the tool spec, its description, the chat_status wording, the README row and count; run the task's verify: passes. Quote the summary line.

#### Notes

- Copy the shape of `chat_send` (HttpBinding, `body="*"`, `_schema`); the tool stays declarative (design D2 rejected an agent-side handler).
- The description text lives in `_descriptions()`; keep the hive prefix rule (`test_descriptions_from_config`, `test_handover_threshold_hint`) intact.
- Shared file with slash-commands-from-chat, hive-decoupling and immediate-message-delivery-w: build on their merged tools.

### S4: web chat image tool

- Status: todo
- Files: `src/chat/ChatImage.tsx`, `src/chat/ChatImage.test.tsx`, `src/chat/entries.tsx`, `src/chat/ChatLog.tsx`, `src/chat/ChatLog.test.tsx`, `src/chat/ChatView.tsx`, `MEMORY.md`
- Verify: `npx vitest run src/chat/ChatImage.test.tsx src/chat/ChatView.test.tsx src/chat/ChatLog.test.tsx && npm run lint`
- Verified head: none

#### Requirement

README Goal G3, verbatim: "the session web chat shows the sent picture inside the tool-call box from the same-origin session download route; message text still never renders images; the Chats page shows "picture: <name>"."

Design D8, verbatim:
"- Session ChatView: a renderer for tool items named `*orchestrator_chat_send_image*` with status ok and a JSON result containing `path` draws `<img src={fileDownloadUrl(sessionId, path)} loading="lazy">` at most 320 px wide, opening the full file on click, with "picture no longer in the workspace" on error; the tool JSON box stays below. Session-level download (all agents of a session share one workdir, probes.md). User Q1.
- Markdown.tsx unchanged; agents-web MEMORY.md records "the only `<img>` is the chat-image tool renderer, same-origin download route only, never markdown or remote URLs"."

Anti-goal, verbatim: "Any service of ours fetches remote content (SSRF surface), or the web renders an `<img>` from message text or a remote URL."

Open question Q1 (planned on its recommended answer): "Show pictures in the session web chat too? [recommended: yes]"

Scope (agents-web):
- `src/chat/ChatImage.tsx` (new; its own module so its test runs without react-markdown): `ChatImage({sessionId, item})` renders for a tool item whose name contains `orchestrator_chat_send_image`, status `ok` and an output that parses as a JSON object with a string `path`: an anchor to `fileDownloadUrl(sessionId, path)` opening in a new tab (`rel="noopener noreferrer"`, my call for "opening the full file on click") around `<img src={fileDownloadUrl(sessionId, path)} loading="lazy">` with `max-width: 320px` and the picture name as alt; on the image's error it shows "picture no longer in the workspace". Anything else renders nothing.
- `src/chat/entries.tsx`: the tool row shows `ChatImage` under its summary, visible without expanding (my call), with the expandable Input/Output box below as today; `ChatEntry` takes `sessionId`.
- `src/chat/ChatLog.tsx`, `src/chat/ChatView.tsx`: pass `sessionId` down.
- `src/chat/Markdown.tsx` unchanged. `MEMORY.md` records the rule above, dated.

#### Acceptance conditions

- ac1: an ok orchestrator_chat_send_image tool item whose output is JSON with a path renders an img whose src is the relative session download URL of that path, lazy, at most 320 px wide, inside a link to the same URL [evidence: command:npx vitest run src/chat/ChatImage.test.tsx -t "renders the picture from the session download route"]
- ac2: nothing renders for a running or error item, another tool name, output that is not JSON or has no string path; any path only ever yields the same-origin download route [evidence: command:npx vitest run src/chat/ChatImage.test.tsx -t "renders nothing"]
- ac3: an image load error shows "picture no longer in the workspace" [evidence: command:npx vitest run src/chat/ChatImage.test.tsx -t "placeholder when the file is gone"]
- ac4: the tool row shows the picture without expanding and keeps the expandable Input and Output box below it [evidence: command:npx vitest run src/chat/ChatLog.test.tsx -t "image tool row"]
- ac5: Markdown.tsx is unchanged [evidence: command:git diff --quiet origin/main -- src/chat/Markdown.tsx]
- ac6: MEMORY.md records that the only img is the chat-image tool renderer [evidence: command:grep -qF 'the only `<img>` is the chat-image tool renderer' MEMORY.md]
- ac7: the chat tests and lint pass [evidence: command:npx vitest run src/chat/ChatImage.test.tsx src/chat/ChatView.test.tsx src/chat/ChatLog.test.tsx && npm run lint]

#### Files

- `src/chat/ChatImage.tsx`
- `src/chat/ChatImage.test.tsx`
- `src/chat/entries.tsx`
- `src/chat/ChatLog.tsx`
- `src/chat/ChatLog.test.tsx`
- `src/chat/ChatView.tsx`
- `MEMORY.md`

#### Interfaces

- `ChatImage({ sessionId: string, item: ChatItem }): JSX.Element | null` (`src/chat/ChatImage.tsx`).
- `ChatEntry({ item, sessionId })`; `ChatLog` gains a `sessionId` prop.
- Tool result contract: the connector's 202 body `{id, status, path}` relayed unchanged by the orchestrator and the plugin (orch-chat-images-route, mxc-images-route); `path` is workdir-relative.

#### Expected outcome

The session web chat shows a picture the agent sent, from the session's own download route, and nothing else in the chat can render an image.

#### Steps

- Read `entries.tsx`, `ChatLog.tsx`, `ChatView.tsx`, `chatModel.ts` (`toolItem`), `src/api/files.ts` and their tests as merged on main (slash-commands-from-chat edits `entries.tsx` and `chatModel.ts`).
- Red: `src/chat/ChatImage.test.tsx` (ac1-ac3) and the image tool row case in `ChatLog.test.tsx` (ac4); run `npx vitest run src/chat/ChatImage.test.tsx`: fails (no module).
- Green: `ChatImage.tsx`, the row, the prop threading, MEMORY.md; run the task's verify: passes. Quote the summary line.

#### Notes

- `ChatLog.test.tsx` imports `entries.tsx`, which imports `react-markdown`; in agent pods `node_modules` lacks it (baseline 2026-10-29). Run `npm ci` first; when the install is not possible here, say so and let the PR CI be the gate for `ChatLog.test.tsx`, quoting both.
- `fileDownloadUrl` (`src/api/files.ts`) builds the relative URL from `base()`; no `agent_id` (session-level download, D8).
- The download route answers `X-Content-Type-Options: nosniff` and `Cache-Control: no-store` (orchestrator `_DownloadRelay`).

### S5: mxc images route

- Status: todo
- Files: `src/agents_matrix_connector/images.py`, `src/agents_matrix_connector/api/agent.py`, `src/agents_matrix_connector/settings.py`, `README.md`, `openapi-agent.json`, `tests/test_images.py`, `tests/test_api_agent.py`, `tests/test_settings.py`
- Verify: `uv run --frozen pytest tests/test_images.py tests/test_api_agent.py tests/test_settings.py tests/test_readme_api.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G1, verbatim: "an agent sends a picture (jpeg, png, gif or webp, judged by content, at most 8,000,000 bytes) from a file in its session workspace to its chat room through a new tool orchestrator_chat_send_image {path, caption?, room?, reply_to?}; the owner sees it in Messenger through the bridge."

README Goal G4, verbatim: "limits and failures are explicit: unsupported type, too large, missing file and rate (5 pictures a minute per session inside the 20 sends a minute) refuse synchronously with a named error; upload failures and bridge error notices mark the send failed, visible in orchestrator_chat_status."

Design D3, verbatim:
"- `POST /chat/v1/images` in the agent listener, body cap 12 MiB on this route only (new code: the connector has no body cap today).
- Order: body cap, decode base64, refs/room/slug checks as `queue` does, sniff magic bytes, size, caption 0-4000; then under the existing advisory locks: duplicate first, then rate, image sub-rate and room cap (D5 order, delta fix-as-ac).
- Inserts `sends(kind='image', status='queued')` with `image` bytea, `image_mime`, `image_size`, `image_sha256`, `image_name` (basename of path), `image_path`; caption in `text`. Answers 202 `{id: "s<n>", status, path}`."

Design D7, verbatim:
"- Types by magic bytes only: jpeg `FF D8 FF`, png `89 50 4E 47 0D 0A 1A 0A`, gif `GIF87a`/`GIF89a`, webp `RIFF....WEBP`; anything else (SVG included) 422 `unsupported_image`.
- Size 1..`MATRIX_IMAGE_MAX_BYTES` (default and maximum 8,000,000). Orchestrator read cap fixed 8,000,000. The bot also enforces `m.upload.size`.
- Images count toward `MATRIX_AGENT_RATE_PER_MINUTE` (20); sub-limit `MATRIX_AGENT_IMAGE_RATE_PER_MINUTE` (default 5) per session on kind image -> 429 `rate_limited`.
- Room hourly cap (`MATRIX_AGENT_ROOM_CHUNKS_PER_HOUR`, `_chunk_count`): an image counts as 1 event plus its caption chunks.
- Duplicate: same session, room, kind image, image_sha256, caption and reply_to within 60 s returns the existing send."

Delta fix-as-ac, verbatim: "`_chunk_count` counts an image as 1 event plus caption chunks under the room hourly cap." "Image rate and duplicate run inside the advisory locks, duplicate before rate (D5 order)." "Connector body cap is new code (none exists)."

Retro proposal (matrix-connector-agent-initi, recurring), verbatim: "add to the reviewer brief the security checklist for tools that send on a user's behalf (rate and size limits, session trust) per task, not only at the epic review."

Scope (agents-matrix-connector):
- `images.py` (new, my call per Left to the builder): `sniff(data) -> str | None`, the MIME type from the four signatures only.
- `settings.py`: `image_max_bytes` (`MATRIX_IMAGE_MAX_BYTES`, default 8000000, 1..8000000) and `agent_image_rate_per_minute` (`MATRIX_AGENT_IMAGE_RATE_PER_MINUTE`, default 5, at least 1); README Configuration rows.
- `api/agent.py`: `POST /chat/v1/images`, body `{data (base64), path, caption?, room?, reply_to?}` with unknown fields refused like the other bodies; the 12 MiB cap applies to this route only, before parsing, from Content-Length and while streaming: 413 `payload_too_large` (my call: the orchestrator's code for the same refusal); data that is not strict base64 is 422 `invalid_image` (my call); 422 `unsupported_image`; over `MATRIX_IMAGE_MAX_BYTES` 413 `image_too_large`; caption over 4000 characters refused as a validation error; an empty caption means none. Room choice, references and their masked refusals exactly as `send_message` (room, else reply_to's room, else the bound room, else 422 `room_required`). Under the advisory locks, in this order: duplicate (returns the existing send), the 20-a-minute rate, the image sub-rate (429 `rate_limited`, message naming the picture limit), the room hourly cap with `_chunk_count` image = 1 + caption chunks. 202 `{id: "s<n>", status, path}`. `SendStatus.kind` accepts `image`.
- `openapi-agent.json` regenerated; README `## Agent API` gains the route, its codes and limits.
- Text sends and reactions keep their behaviour (anti-goal: no regression in the merged outbound path).

#### Acceptance conditions

- ac1: sniff returns image/jpeg, image/png, image/gif and image/webp for their signatures whatever the file name, and None for SVG, text, empty, truncated headers and RIFF that is not WEBP (pure test) [evidence: test:tests/test_images.py::test_sniff_magic_bytes]
- ac2: a png from a session queues one send of kind image with the bytes, mime, size, sha256, name (basename of path), path and the caption as text, and answers 202 {id, status queued, path} [evidence: test:tests/test_api_agent.py::test_image_queued]
- ac3: a body over 12 MiB is refused 413 payload_too_large before parsing, by Content-Length and by streamed size; the message and reaction routes are unchanged [evidence: test:tests/test_api_agent.py::test_image_body_cap]
- ac4: data that is not base64 is 422 invalid_image, an unsupported type 422 unsupported_image, more than MATRIX_IMAGE_MAX_BYTES 413 image_too_large, a caption over 4000 characters a 422 validation error; each queues nothing [evidence: test:tests/test_api_agent.py::test_image_refusals_queue_nothing]
- ac5: room choice, references and refusals match messages: room, reply_to's room, bound room, room_required, masked bad_reference, room_not_allowed, room_bound, room_not_authorised and session_bound, each queuing nothing [evidence: test:tests/test_api_agent.py::test_image_room_choice_and_refusals]
- ac6: a repeat within 60 s (same session, room, sha256, caption and reply_to) returns the existing send even when the rate is exhausted; another caption is a new send [evidence: test:tests/test_api_agent.py::test_image_duplicate_before_rate]
- ac7: images count toward the 20 sends a minute, and the sixth picture of a session within 60 s is 429 rate_limited at the default 5; parallel requests never exceed either limit [evidence: test:tests/test_api_agent.py::test_image_rate_limits]
- ac8: the room hourly cap counts an image as 1 event plus its caption chunks [evidence: test:tests/test_api_agent.py::test_image_room_chunk_cap]
- ac9: GET /chat/v1/messages/s<n> answers an image send with kind image [evidence: test:tests/test_api_agent.py::test_image_status_kind]
- ac10: the settings default to 8000000 and 5, 8000001 and 0 are refused with the variable named, and the README lists both [evidence: test:tests/test_settings.py::test_image_settings]
- ac11: the committed agent OpenAPI matches the app and the README lists every agent route [evidence: test:tests/test_readme_api.py::test_agent_openapi_committed_matches]
- ac12: the existing agent route tests pass unedited [evidence: command:git diff origin/main -- tests/test_api_agent.py | grep -c '^-[^-]' | grep -qx 0]
- ac13: the targeted tests and lint pass (DB tests in CI) [evidence: command:uv run --frozen pytest tests/test_images.py tests/test_api_agent.py tests/test_settings.py tests/test_readme_api.py && mise run lint]

#### Files

- `src/agents_matrix_connector/images.py`
- `src/agents_matrix_connector/api/agent.py`
- `src/agents_matrix_connector/settings.py`
- `README.md`
- `openapi-agent.json`
- `tests/test_images.py`
- `tests/test_api_agent.py`
- `tests/test_settings.py`

#### Interfaces

- `images.sniff(data: bytes) -> str | None`.
- `POST /chat/v1/images` (agent listener): request `{data: str, path: str, caption?: str, room?: str, reply_to?: str}`; 202 `{id: "s<n>", status: "queued"|"sending"|"sent", path: str}`; errors 400, 401, 403, 409, 413, 422, 429, 503 in the existing `{error: {code, message}}` body.
- `ConnectorSettings.image_max_bytes`, `ConnectorSettings.agent_image_rate_per_minute`.
- `SendStatus.kind: Literal["message", "reaction", "image"]`.

#### Expected outcome

The connector accepts a picture from the orchestrator, refuses what the bridge would refuse (type, size) and what would flood a room (rate, room cap), and queues it for the bot.

#### Steps

- Red: `tests/test_images.py` (ac1), the image tests in `tests/test_api_agent.py` (ac2-ac9), `test_image_settings`; run `uv run --frozen pytest tests/test_images.py tests/test_settings.py`: fail (no module, no settings); the API tests error locally without Docker.
- Green: `images.py`, settings, the route with its cap, the shared `queue` path extended for images, `_chunk_count`, `SendStatus`; regenerate `openapi-agent.json` (README Development names the command); README; run the task's verify. Quote the local summary line and the CI run.

#### Notes

- DB-backed tests (testcontainers Postgres) need Docker; agent pods have none, so they error here (baseline 2026-10-29: 182 Docker errors) and CI on the PR is the gate for them (recurring retro). Run the verify, quote the local summary line and the CI run of the pushed head. Keep each pure helper covered by a non-DB test so the local run has signal.
- Reuse `queue` (advisory locks: session lock before room lock), `_resolve`, `may_post` and the masked refusal; do not copy them. The duplicate check runs before the rate checks inside the locks.
- The body cap is new code for this route only (an ASGI-level or request-stream check); the message and reaction routes keep their behaviour.
- Never log the bytes or the base64; log the send id, size and mime only.
- Size checks count the decoded bytes, not the base64 length.

### S6: plugins release images

- Status: todo
- Files: `orchestration/orchestrator/pyproject.toml`, `uv.lock`, `orchestration/orchestrator/README.md`, `tests/test_source_install.py`
- Verify: `uv run --frozen pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G5, verbatim: "released and deployed in order (plugins, connector, orchestrator, web, helmfile) and proven by a live smoke that posts one real picture with a caption to the owner's Messenger DM."

Design D9, verbatim: "Placeholders, as hive-decoupling does: `<MIGRATION>` (next free connector migration), `<TAG>`/`<VERSION>` (next free plugins minor, expected v0.6.0). The first task that needs one reads the real number from main at build time and amends the dependent tasks (`ticket.py amend`); no number is assumed."

User decision (binding), verbatim: "Release numbers are placeholders resolved at build time, exactly as /workdir/workdir/docs/plans/in-progress/hive-decoupling does (read its design.md 'Build-time settlements' and tasks orch-activity-route, plugins-release-0-4-0, orch-plugins-pin-0-4-0, helmfile-deploy-pin for the pattern): <MIGRATION> for the connector migration (0003 is claimed by immediate-message-delivery-w), <TAG>/<VERSION> for the plugins release (v0.3.0-v0.5.0 claimed). The first task needing each reads it from main and amends dependents."

Repo README `## Releases`: releases are `vX.Y.Z` tags on `main`; pins use `?ref=` to a release tag; nothing is published beyond the tag.

This is the first task that needs `<TAG>` and `<VERSION>`. Before the first implementer is dispatched the orchestrator session (not a subagent: `ticket.py amend` and `git ls-remote` are its tools) reads the newest `vX.Y.Z` tag on the any-mcp-tatara-plugins origin (`git ls-remote --tags https://github.com/szymonrychu/any-mcp-tatara-plugins 'v*'`), takes the next minor, and replaces `<TAG>` (with the `v`) and `<VERSION>` (without it) by `ticket.py amend` in this task, orch-plugins-pin-and-tool and helmfile-pictures-pin (Requirement and acceptance conditions), and edits the same placeholders in their bodies. The task slug keeps its name.

Scope (any-mcp-tatara-plugins):
- `orchestration/orchestrator/pyproject.toml`: version `<VERSION>`; `uv lock` updates `uv.lock`.
- `orchestration/orchestrator/README.md`: the example source pins `?ref=<TAG>`.
- `tests/test_source_install.py::test_orchestrator_distribution_metadata` is no longer accurate (named): it pins the previous release version; it asserts `<VERSION>`.
- Release step, run by the orchestrator session (never a subagent) once this repo's PR is merged to `main` with green CI: `git tag <TAG> <merge sha> && git push origin <TAG>` (irreversible, listed in design.md). ac3 and ac4 are checked after that push; the task is not done before the tag exists.

#### Acceptance conditions

- ac1: the plugin's pyproject and installed metadata say <VERSION> (updated, named) [evidence: test:tests/test_source_install.py::test_orchestrator_distribution_metadata]
- ac2: the plugin README example pins the new release and no older one [evidence: command:test "$(grep -oE "ref=v[0-9.]+" orchestration/orchestrator/README.md | sort -u)" = "ref=<TAG>"]
- ac3: (orchestrator session, after the push) tag <TAG> exists on origin at the main merge commit, whose CI is green [evidence: command:test -n "$(git ls-remote --tags origin <TAG>)"]
- ac4: (orchestrator session, after the push) the tagged tree carries the image tool [evidence: command:git fetch origin tag <TAG> && git show <TAG>:orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py | grep -q chat_send_image]
- ac5: (orchestrator session, before dispatch) the real next plugins minor read from origin replaces <TAG> and <VERSION> in this task, orch-plugins-pin-and-tool and helmfile-pictures-pin [evidence: judgement:orchestrator quotes the tag list read and a grep of the three task files showing no placeholder left]
- ac6: the targeted tests and lint pass [evidence: command:uv run --frozen pytest tests/test_source_install.py::test_orchestrator_distribution_metadata tests/test_repo.py && mise run lint]

#### Files

- `orchestration/orchestrator/pyproject.toml`
- `uv.lock`
- `orchestration/orchestrator/README.md`
- `tests/test_source_install.py`

#### Interfaces

- Distribution `any-mcp-tatara-orchestrator` version `<VERSION>`; git tag `<TAG>` on the `main` merge commit.

#### Expected outcome

The orchestrator plugin with `orchestrator_chat_send_image` is released as tag `<TAG>`, so the orchestrator and agents-helmfile can pin it.

#### Steps

- Orchestrator session, before dispatch: read the tags (`git ls-remote --tags https://github.com/szymonrychu/any-mcp-tatara-plugins 'v*'`), take the next minor, amend the three tasks (ac5).
- Confirm `<TAG>` does not exist on origin and that `main` carries the newest tag; stop and report otherwise.
- Red: change `test_orchestrator_distribution_metadata` to `<VERSION>`; run `uv run --frozen pytest tests/test_source_install.py::test_orchestrator_distribution_metadata`: fails.
- Green: bump the plugin pyproject, `uv lock`, the README example; run the task's verify: passes. Quote the summary line.
- After the merge (orchestrator session): wait for CI green on the merge commit, `git tag <TAG> <merge sha> && git push origin <TAG>`, then check ac3 and ac4; only then mark done.

#### Notes

- Dependency-bump TDD exception for the version values; the metadata test is the guard.
- `tests/test_source_install.py::test_orchestrator_plugin_installs_from_sources` fails in agent pods with git 2.39 (`--end-of-options`, baseline 2026-10-29); CI is the gate for it.
- Retro (deploy-safe-agent-sessions): a release once was marked done before its artifact existed; ac3 and ac4 prevent that here.

### S7: mxc bot image upload

- Status: todo
- Files: `src/agents_matrix_connector/sender.py`, `src/agents_matrix_connector/tracker.py`, `src/agents_matrix_connector/bot.py`, `README.md`, `MEMORY.md`, `tests/test_sender.py`, `tests/test_tracker.py`, `tests/test_readme_api.py`
- Verify: `uv run --frozen pytest tests/test_sender.py tests/test_tracker.py tests/test_readme_api.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G2, verbatim: "the Matrix token stays in the bot pod: the bot uploads the bytes and sends m.image; the caption goes as its own text message after the picture; reply_to anchors the picture."

README Goal G4, verbatim: "limits and failures are explicit: unsupported type, too large, missing file and rate (5 pictures a minute per session inside the 20 sends a minute) refuse synchronously with a named error; upload failures and bridge error notices mark the send failed, visible in orchestrator_chat_status."

Design D4, verbatim:
"1. For each queued image send whose bytes are present, a read-only authorisation pre-check (same rules as the claim); on failure the claim step refuses it as today.
2. Check size <= `m.upload.size` (media config cached 1 h; unknown means our cap).
3. Upload (filename = image_name, Content-Type = image_mime) outside any transaction.
4. One claim transaction as today (queued->sending, authoritative re-check and binding), which also sets `mxc_uri`, sets `image = NULL`, and inserts outbound rows `mxa-<send>-i` (m.image, reply relation) and, with a caption, `mxa-<send>-1` (m.text).
- `claim_queued` skips image rows whose upload has not succeeded in this tick.
- `_place` does not fail a caption-less image as `empty_text`.
- Upload failures: 413 or 403 M_FORBIDDEN -> guarded queued->failed `upload_rejected:<errcode>`; 429, 5xx, transport -> retry next tick until created_at + 600 s, then failed `upload_failed`.
- A crash between upload and claim re-uploads next tick; the orphan media on our own Synapse is accepted.
- One writer holds: the api inserts sends; the bot transitions them, clears bytes and prunes; outbound stays bot-only."

Design D5, verbatim: "`m.image`: `{msgtype: m.image, body: name, filename: name, url: mxc, info: {mimetype, size}}` plus `m.relates_to.m.in_reply_to` when reply_to is given. No width/height (my call: optional, the bridge checks only mimetype and size; avoids Pillow or a header parser)." and "Caption always a separate `m.text` after the picture (Messenger E2EE drops image captions). User Q4."

brief-docs fix-as-ac, verbatim: "Every `m.image` sent sets `info.mimetype` (sniffed, not trusted) and `info.size` (exact byte count), so bridgev2's pre-send caps check (2.11) runs and rejects early with a clear reason."

Anti-goals, verbatim: "The Matrix token leaves the bot pod, or the api pod uploads media." "Image bytes are loaded into every `SendRow` read, or stay in Postgres after the upload." "A text send or reaction behaves differently than before (regression in the merged outbound path)."

Scope (agents-matrix-connector):
- `sender.py`: `Sender` takes the `MatrixClient` (built in `bot.py`); each tick, before the claim: for every `sends.queued_images` row, the read-only pre-check ((a) `agent_room_decision`, (b) binding rules, as the claim); a refusal goes into `ready` as None (no upload; handled as the review fix for interrogate item 1 below says); else the size against `m.upload.size` (cached 1 h; None means `MATRIX_IMAGE_MAX_BYTES`), over it: `fail_queued` `upload_rejected:M_TOO_LARGE` without uploading (my call: the code Synapse would answer); else `upload_media` outside any transaction, its mxc into `ready`. 413 or 403 `M_FORBIDDEN`: `fail_queued` `upload_rejected:<errcode>`; any other non-auth Matrix 4xx: `fail_queued` `upload_rejected:<errcode or status>` (my call: not retryable); `MatrixUnavailable` (429 after the retry, 5xx, transport): stays queued until `created_at + 600 s`, then `fail_queued` `upload_failed`; `MatrixAuthError` propagates. Then `claim_queued(conn, now, ready)`; `_place` for an image stores the `mxa-<send>-i` row (kind `image`, body the picture name, `content` the m.image content with the reply relation when reply_to was given) and, with a caption, its `m.text` chunk rows `mxa-<send>-1..n` without a relation; never `empty_text` for an image.
- `tracker.py`: `_send_pending` sends a row's stored `content` as is when set, else `event_content` as today.
- `bot.py`: builds the `Sender` with the Matrix client.
- README: the reasons `upload_rejected:<errcode>` and `upload_failed`; `tests/test_readme_api.py::test_readme_lists_every_reason` gains the new reason constants. MEMORY.md: the upload-before-claim decision, bytes cleared at claim or failure, orphan media accepted.

Review fix, interrogate 2026-10-29 Act on 1 (pre-check refusal becomes a placed image with no mxc), verbatim: "a claimed image without a successful upload this tick is never placed: a None entry fails (guarded) with the pre-check's reason and clears the bytes; an image is placed only with its `mxc_uri`; an authoritative re-check that refuses after upload refuses as today (orphan media accepted). AC: "policy flips between pre-check and claim" and "no outbound m.image row without url"." For this task: the sender keeps the pre-check's reason per send for the tick; a send claimed from a None entry goes through the guarded `sending -> refused` (`sends.mark_refused`) with that reason, its bytes already cleared by the claim, and `_place` is never called for it (my call: `refused`, the status a claim-time policy or binding refusal has today, so orchestrator_chat_status reads the same); `_place` stores an `m.image` row only from a non-empty `mxc_uri`, so no path stores an `m.image` without `url`.

Review fix, interrogate 2026-10-29 Consider (folded into Act on 1), verbatim: "the pre-check calls one pure decision function shared with the claim (my call; extracting it from `may_post` too is boy-scout only if the task already touches it)." For this task: the room (a) and binding (b) rules are one pure function over the room policy answer, the active binding and the room settings, called by the read-only pre-check and by the claim (`_place`/`_authorise`, which then binds); `api/agent.py:may_post` is not in this task's files and stays as is.

Review fix, interrogate 2026-10-29 Act on 3 (upload outage stalls text sends and reactions), verbatim: "the upload pass stops at the first MatrixUnavailable or transport error (as the tracker does, tracker.py:207-212), and text/reaction claims in the same tick are not delayed by it; AC: during an upload outage a queued text send is still claimed in that tick." For this task: on the first `MatrixUnavailable` (429 after the retry, 5xx, transport) the pass attempts no further upload in that tick; the images not attempted stay queued with their bytes and are not in `ready`, except that each one past `created_at + 600 s` fails `upload_failed` without an upload (my call: D4's retry window holds for every image, attempted or not); the claim of the same tick then runs as today for message and reaction sends.

#### Acceptance conditions

- ac1: a queued png send is uploaded (filename the picture name, Content-Type its mime) before the claim; the claim sets mxc_uri, clears the bytes and stores row mxa-<send>-i whose content is {msgtype m.image, body name, filename name, url mxc, info {mimetype, size}} [evidence: test:tests/test_sender.py::test_image_send_uploaded_then_claimed]
- ac2: with a caption the m.image row comes first and the caption follows as m.text row(s) mxa-<send>-1..n; reply_to puts m.in_reply_to on the m.image only; without a caption there is one row and the send is never failed empty_text [evidence: test:tests/test_sender.py::test_image_caption_and_reply_rows]
- ac3: the tracker sends a row's stored content unchanged; once all rows are sent the send is sent with the picture's event id [evidence: test:tests/test_tracker.py::test_image_content_sent_as_stored]
- ac4: an image whose upload did not succeed this tick stays queued while the tick's message and reaction sends are claimed as before [evidence: test:tests/test_sender.py::test_unuploaded_image_stays_queued]
- ac5: an image the pre-check refuses is never uploaded and never placed: claimed from its None entry it ends refused with the pre-check's policy or binding reason, its bytes cleared and no outbound row stored [evidence: test:tests/test_sender.py::test_image_refused_without_upload]
- ac6: a 413 or 403 M_FORBIDDEN upload fails the send upload_rejected:<errcode> with its bytes cleared; a picture over m.upload.size fails upload_rejected:M_TOO_LARGE without an upload; an unknown media config falls back to MATRIX_IMAGE_MAX_BYTES [evidence: test:tests/test_sender.py::test_image_upload_rejected]
- ac7: 429, 5xx and transport failures leave the send queued and retry next tick; after created_at + 600 s it fails upload_failed; a lost token propagates [evidence: test:tests/test_sender.py::test_image_upload_retry_window]
- ac8: the media config is read at most once an hour [evidence: test:tests/test_sender.py::test_media_config_cached]
- ac9: a crash between upload and claim re-uploads on the next tick and exactly one m.image is sent (txn mxa-<send>-i) [evidence: test:tests/test_sender.py::test_image_restart_exactly_once]
- ac10: no log line carries the bytes or their base64 [evidence: test:tests/test_sender.py::test_image_bytes_never_logged]
- ac11: text sends and reactions behave as before: the existing sender and tracker assertions are unchanged, only Sender construction lines change [evidence: judgement:reviewer reads the diff of tests/test_sender.py and tests/test_tracker.py]
- ac12: README names upload_rejected:<errcode> and upload_failed and the reason test lists them; MEMORY.md records upload before claim and the accepted orphan media [evidence: command:uv run --frozen pytest tests/test_readme_api.py::test_readme_lists_every_reason && grep -qi 'orphan' MEMORY.md]
- ac13: the targeted tests and lint pass (DB tests in CI) [evidence: command:uv run --frozen pytest tests/test_sender.py tests/test_tracker.py tests/test_readme_api.py && mise run lint]
- ac14: policy flips between pre-check and claim: a send the pre-check refused stays refused with the pre-check's reason after the policy or binding flips to allow, with no upload and no outbound row; a send uploaded after an allowing pre-check whose policy or binding flips to refuse before the claim is refused at claim as today, its bytes cleared (the uploaded media is orphaned) [evidence: test:tests/test_sender.py::test_image_policy_flips_between_precheck_and_claim]
- ac15: no outbound m.image row without url: across the upload, refusal, flip and retry cases every outbound row of kind image has a content url equal to the send's mxc_uri, and the m.image content builder refuses an empty mxc (pure test) [evidence: test:tests/test_sender.py::test_no_image_row_without_url]
- ac16: during an upload outage (MatrixUnavailable on the first upload) a tick with two queued images and a queued text send makes exactly one upload attempt, claims the text send in that tick, and leaves both images queued with their bytes; an image past created_at + 600 s fails upload_failed even when not attempted [evidence: test:tests/test_sender.py::test_upload_outage_does_not_stall_text_sends]
- ac17: the pre-check and the claim call the same pure room and binding decision function, and sender.py holds no second copy of those rules [evidence: judgement:reviewer reads sender.py and names the shared function and its two callers]

#### Files

- `src/agents_matrix_connector/sender.py`
- `src/agents_matrix_connector/tracker.py`
- `src/agents_matrix_connector/bot.py`
- `README.md`
- `MEMORY.md`
- `tests/test_sender.py`
- `tests/test_tracker.py`
- `tests/test_readme_api.py`

#### Interfaces

- `Sender(matrix: MatrixClient, pool, settings, *, now=utcnow)`; `Sender.tick()` = upload step, claim, settle.
- Outbound image row: kind `image`, `event_type` `m.room.message`, body the picture name, `content` the full m.image content (relation merged in), txn `mxa-<send>-i`.
- Reasons: `upload_rejected:<errcode>`, `upload_failed` (constants in `sender.py`).

#### Expected outcome

The bot turns a queued picture into one uploaded file and one m.image (plus its caption), with the bytes gone from Postgres at claim, and every upload failure ends as a named failed status.

#### Steps

- Red: the sender tests (ac1, ac2, ac4-ac10) with the fake homeserver from mxc-matrix-media-upload, the tracker test (ac3), the reason constants in `test_readme_lists_every_reason`; run `uv run --frozen pytest tests/test_readme_api.py`: fails (reasons missing); the DB tests error locally.
- Green: the upload step, the claim with `ready`, `_place` for images, the tracker content path, `bot.py`, README and MEMORY.md; run the task's verify; quote the local summary line and the CI run.

#### Notes

- DB-backed tests (testcontainers Postgres) need Docker; agent pods have none, so they error here (baseline 2026-10-29: 182 Docker errors) and CI on the PR is the gate for them (recurring retro). Run the verify, quote the local summary line and the CI run of the pushed head. Keep each pure helper covered by a non-DB test so the local run has signal.
- Keep the m.image content builder a pure function with a non-DB test in `tests/test_sender.py` so the local run has signal.
- The upload happens outside the claim transaction and holds no pool connection while it waits on Synapse (retro: `Sender._claim` connection hold).
- Settle is unchanged: the first row by id is the picture, so the send's `event_id` is the picture's and `reply_to: s<n>` quotes it.
- Shared file with immediate-message-delivery-w (`tracker.py`): read it as merged on main first.

- 2026-10-29 amended: interrogate 2026-10-29 act on 1 and 3 (and Consider folded into 1)
- (my call, builder-check Q3) Caption rows keep outbound kind `agent`, as text sends have today (`mxa-<send>-1..n`), stored by a second `add_outbound` call in the same claim transaction after the picture row, so the picture row is first by id; only `image` is added to the outbound kind CHECK.
- (review fix) Red also covers ac14-ac16; ac17 is the reviewer's read of the shared decision function.

### S8: orch chat contract refresh

- Status: todo
- Files: `tests/fakes/chat_openapi.json`, `tests/fakes/chat_openapi.source`, `tests/fakes/fake_chat.py`, `tests/test_chat_contract.py`
- Verify: `uv run --frozen pytest tests/test_chat_contract.py tests/test_agent_chat.py && mise run lint`
- Verified head: none

#### Requirement

Design D9, verbatim: "Refresh the vendored contract `tests/fakes/chat_openapi.*` from connector main (already stale) with the new route."

Delta fix-as-ac, verbatim: "Refresh tests/fakes/chat_openapi.json from connector main (already stale)."

Design D2, verbatim: "Then POST JSON `{data: base64, path, caption?, room?, reply_to?}` to `{ORCH_CHAT_URL}/chat/v1/images`; status and body pass through unchanged (D2 of the merged epic)."

Scope (agents-orchestrator, tests only):
- `tests/fakes/chat_openapi.json`: byte for byte the connector's `openapi-agent.json` at the commit `tests/fakes/chat_openapi.source` names; that commit carries `POST /chat/v1/images` (mxc-images-route): connector `main` once the connector PR merged, else the connector epic-branch commit, kept reachable by a merge commit (my call, the matrix epic's precedent: web `openapi/matrix.source` pinned 23f0424).
- `tests/fakes/chat_openapi.source`: `agents-matrix-connector <full sha>`.
- `tests/fakes/fake_chat.py`: `FakeChat` answers `POST /chat/v1/images` per the vendored schema (202 `{id, status, path}`, the documented refusals through `refuse`) and records the call.
- `tests/test_chat_contract.py`: a test for the new fake route; the existing contract tests keep passing against the refreshed document. The relay still serves four routes in this task (orch-chat-images-route adds the fifth).

#### Acceptance conditions

- ac1: the source line names the full sha of a connector commit that serves POST /chat/v1/images, and the vendored document equals that commit's openapi-agent.json byte for byte [evidence: command:sha=$(awk '{print $2}' tests/fakes/chat_openapi.source) && git -C ../agents-matrix-connector cat-file -e "$sha" && git -C ../agents-matrix-connector show "$sha:openapi-agent.json" | cmp -s - tests/fakes/chat_openapi.json && grep -q '"/chat/v1/images"' tests/fakes/chat_openapi.json]
- ac2: FakeChat answers POST /chat/v1/images with a 202 body valid under the vendored schema, refuses on request with a documented status, and records the call [evidence: test:tests/test_chat_contract.py::test_fake_chat_images_route]
- ac3: the existing contract tests pass against the refreshed document [evidence: test:tests/test_chat_contract.py::test_fake_chat_matches_vendored_schema]
- ac4: the contract and chat tests and lint pass (no database) [evidence: command:uv run --frozen pytest tests/test_chat_contract.py tests/test_agent_chat.py && mise run lint]

#### Files

- `tests/fakes/chat_openapi.json`
- `tests/fakes/chat_openapi.source`
- `tests/fakes/fake_chat.py`
- `tests/test_chat_contract.py`

#### Interfaces

- `tests/fakes/fake_chat.FakeChat`: route `("POST", "/chat/v1/images")`, answers `{id: "s<n>", status: "queued", path}`; `refuse("/images", status, code)` as for the other routes.

#### Expected outcome

The orchestrator's contract fake of the chat upstream matches the connector that serves pictures, so the relay tests of orch-chat-images-route test against the real contract (design D16 of the matrix epic).

#### Steps

- Read `tests/fakes/fake_chat.py`, `tests/test_chat_contract.py` and the connector's `openapi-agent.json` at the commit carrying mxc-images-route.
- Red: `test_fake_chat_images_route`; run `uv run --frozen pytest tests/test_chat_contract.py`: fails (no route in the document or fake).
- Green: copy the document, update the source line, teach FakeChat the route; run the task's verify: passes. Quote the summary line.

#### Notes

- The vendored document has been stale since 0380120 (connector openapi-agent.json gained 400 responses); the refresh may surface such differences in `test_fake_chat_matches_vendored_schema` and the fake's refusals: fix the fake, never the document.
- In the integration worktree layout the connector tree is the sibling `../agents-matrix-connector`; fetch the pinned commit there first.
- (my call, builder-check Q1) The connector tasks merge to connector `main` first; this task starts after that and pins the connector `main` sha, so the epic-branch fallback in Scope is not used.

### S9: mxc bridge error notices

- Status: todo
- Files: `src/agents_matrix_connector/discovery.py`, `src/agents_matrix_connector/sync.py`, `src/agents_matrix_connector/sender.py`, `src/agents_matrix_connector/db/runs.py`, `src/agents_matrix_connector/db/sends.py`, `README.md`, `MEMORY.md`, `tests/test_discovery.py`, `tests/test_sync.py`
- Verify: `uv run --frozen pytest tests/test_discovery.py tests/test_sync.py tests/test_readme_api.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G4, verbatim: "limits and failures are explicit: unsupported type, too large, missing file and rate (5 pictures a minute per session inside the 20 sends a minute) refuse synchronously with a named error; upload failures and bridge error notices mark the send failed, visible in orchestrator_chat_status."

Design D6, verbatim: "Before the bridge-bot skip in the sync loop (discovery.py:132, sync.py:470), the bot checks one thing: a bridge-bot `m.notice` whose `m.relates_to.m.in_reply_to.event_id` equals a sent outbound row of an agent send. On a match the outbound row goes sent->failed and the send sent->failed with reason `bridge: <notice body>`, both guarded; orchestrator_chat_status shows it. Applies to all agent sends, not only images. parse_message stays unchanged. User Q6."

Open question Q6 (planned on its recommended answer): "A bridge error notice marks any agent send failed, text included? [recommended: yes]"

brief-docs fix-as-ac, verbatim: "The connector stops ignoring the bridge bot's error `m.notice` for its own outbound images (at least logs/records the failure for that run); today `discovery.py:132` drops it, so a failed bridge is silent."

brief-cartographer fix-as-ac, verbatim: "Inbound non-text messages are dropped silently (`discovery.py:141`, `sync.py:515` `unsupported_content`): if pictures add an image event kind, keep inbound images classified explicitly (not a regression of the ignore path)."

Scope (agents-matrix-connector):
- `discovery.py`: a pure `bridge_notice_reply(event, bridge_bots) -> tuple[str, str] | None`: the replied event id and the body of an `m.room.message` from a bridge bot with msgtype `m.notice` and a string `m.relates_to.m.in_reply_to.event_id`. `parse_message` unchanged.
- `sync.py`: in the room timeline pass, before `parse_message` skips the event, a match fails the outbound row carrying that `event_id` when it is `sent` and belongs to a send (guarded `sent -> failed`), and, when that send is `sent`, the send too (guarded `sent -> failed`), reason `bridge: <body>` truncated to 500 characters (my call: bounded status text), in the sync transaction. A send still `sending` is failed by the sender's settle from the failed row, keeping its binding (review fix below). A notice replying to a run's reply or notice, an unknown event or an already failed row changes nothing. No binding changes (my call: the event reached the room). No inbound row is stored for the notice (as today).
- `db/runs.py`: the guarded outbound `sent -> failed` by event id for send rows. `db/sends.py`: the guarded send `sent -> failed`.
- README: the reason `bridge: <notice body>` and the behaviour; MEMORY.md: the sync loop writes these two transitions inside the one bot process under the singleton lock (bot.py), so the bot stays the one writer of `outbound` and `sends` transitions; the table comments stay.

Review fix, interrogate 2026-10-29 Act on 2 (bridge notice vs settle binding release is timing-dependent), verbatim: "a row failed by a bridge notice counts as having reached the room for the binding: settle releases the initiation only when no row reached the room; AC covers both orders." For this task: a row reached the room when it carries an `event_id` (sent, or failed by a bridge notice); `sends.ended` reports that count and `Sender._settle` (sender.py, today `done.sent == 0`) calls `release_initiation` only when it is 0, so a notice that fails the only row keeps the binding whether it lands while the send is still `sending` or after settle marked it `sent`. `refuse_sending`'s count and `release_initiation`'s later-send check use the same reached rule (my call: one rule for every release decision, so no order of notice and tracker changes the binding).

#### Acceptance conditions

- ac1: bridge_notice_reply returns the replied event id and body for a bridge-bot m.notice with m.in_reply_to, and None for another sender, m.text, no relation or a non-string id (pure test) [evidence: test:tests/test_discovery.py::test_bridge_notice_reply]
- ac2: parse_message is unchanged: bridge-bot events stay Skip and an inbound m.image stays Unsupported, the existing test passing unedited [evidence: test:tests/test_discovery.py::test_parse_message]
- ac3: a bridge notice replying to a sent row of a sent agent send fails the row and the send with reason "bridge: <body>", for a message send and an image send, and GET /chat/v1/messages/s<n> shows failed with that reason [evidence: test:tests/test_sync.py::test_bridge_notice_fails_agent_send]
- ac4: a notice replying to a row of a send still sending fails the row, and the sender's settle then fails the send with that reason without releasing its binding [evidence: test:tests/test_sync.py::test_bridge_notice_during_sending]
- ac5: a notice replying to a run reply, an unknown event or an already failed row changes nothing, stores no inbound row and changes no binding [evidence: test:tests/test_sync.py::test_bridge_notice_ignored_otherwise]
- ac6: README names the reason and MEMORY.md records the writer ruling [evidence: command:grep -qF '`bridge: ' README.md && grep -q 'bridge notice' MEMORY.md]
- ac7: the targeted tests and lint pass (DB tests in CI) [evidence: command:uv run --frozen pytest tests/test_discovery.py tests/test_sync.py tests/test_readme_api.py && mise run lint]
- ac8: both orders keep the binding: an agent-initiated send whose only row is failed by a bridge notice keeps the room bound to its session when the notice lands before settle (send sending) and when it lands after settle (send sent); a send whose only row failed without an event id still releases its binding as today [evidence: test:tests/test_sync.py::test_bridge_notice_keeps_binding_either_order]

#### Files

- `src/agents_matrix_connector/discovery.py`
- `src/agents_matrix_connector/sync.py`
- `src/agents_matrix_connector/sender.py`
- `src/agents_matrix_connector/db/runs.py`
- `src/agents_matrix_connector/db/sends.py`
- `README.md`
- `MEMORY.md`
- `tests/test_discovery.py`
- `tests/test_sync.py`

#### Interfaces

- `discovery.bridge_notice_reply(event: dict, bridge_bots: Sequence[str]) -> tuple[str, str] | None`.
- `db/runs.py`: guarded outbound `sent -> failed` by event id for send rows; `db/sends.py`: guarded `sent -> failed`.
- Reason text `bridge: <notice body>` (at most 500 characters of body).

#### Expected outcome

A picture or message the bridge could not deliver to Messenger shows as failed with the bridge's words in `orchestrator_chat_status`, instead of a silent `sent`.

#### Steps

- Red: `test_bridge_notice_reply` (pure) and the three sync tests (the fake homeserver's `post` injects the bridge notice into the timeline); run `uv run --frozen pytest tests/test_discovery.py`: fails (no function); the sync tests error locally.
- Green: the helper, the sync-loop check, the two guarded transitions, README and MEMORY.md; run the task's verify; quote the local summary line and the CI run.

#### Notes

- DB-backed tests (testcontainers Postgres) need Docker; agent pods have none, so they error here (baseline 2026-10-29: 182 Docker errors) and CI on the PR is the gate for them (recurring retro). Run the verify, quote the local summary line and the CI run of the pushed head. Keep each pure helper covered by a non-DB test so the local run has signal.
- The notice shape is mautrix/go bridgev2 `messagestatus.go` `ToNoticeEvent` (`SetReplyTo(SourceEventID)`), per brief-docs; the bridge bot ids come from `MATRIX_BRIDGE_BOTS`.
- The check runs before the bridge-bot skip and does not change what `parse_message` returns (D6).
- Shared files with mxc-send-images-schema and mxc-bot-image-upload (`db/runs.py`, `db/sends.py`, README, MEMORY.md): build on their commits.

- 2026-10-29 amended: interrogate 2026-10-29 act on 2
- (review fix) `sender.py` joins the files for the settle, `refuse_sending` and `release_initiation` reached rule (interrogate Act on 2); nine files, one over the sizing guide, kept in one task because the both-orders test drives sync and settle together. Shared file with mxc-bot-image-upload (`sender.py`): build on its commit.

### S10: orch chat images route

- Status: todo
- Files: `src/agents_orchestrator/api/chat.py`, `src/agents_orchestrator/api/workspace.py`, `tests/test_agent_chat.py`, `tests/test_chat_contract.py`, `openapi.json`, `README.md`, `MEMORY.md`
- Verify: `uv run --frozen pytest tests/test_agent_chat.py tests/test_chat_contract.py tests/test_readme_api.py tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper && mise run lint`
- Verified head: none

#### Requirement

README Goal G1, verbatim: "an agent sends a picture (jpeg, png, gif or webp, judged by content, at most 8,000,000 bytes) from a file in its session workspace to its chat room through a new tool orchestrator_chat_send_image {path, caption?, room?, reply_to?}; the owner sees it in Messenger through the bridge."

README Goal G4, verbatim: "limits and failures are explicit: unsupported type, too large, missing file and rate (5 pictures a minute per session inside the 20 sends a minute) refuse synchronously with a named error; upload failures and bridge error notices mark the send failed, visible in orchestrator_chat_status."

Design D1, verbatim: "The tool takes `path`, absolute under the session workdir or relative, normalised by `api/agent.py:_normalise` (:261); invalid is 400 `invalid_path`. No URL argument."

Design D2, verbatim:
"- Route in api/chat.py runs exactly the checks of `_relay` (require_agent, 403 `trigger_session`, `_leads`, chat_available, `_capped_body`) by sharing them, not copying them; it parses only `path`.
- Seam `read_file_bytes(conn, settings, http, session_id, agent_id, path, max_bytes)` in api/workspace.py over `resolve_agent` and `WrapperClient.open_download`; reads at most max+1 bytes (413 `image_too_large`) inside `asyncio.timeout(10)`, maps errors with `_wrapper_errors` (404 `not_found` etc.). chat.py imports workspace, not wrapper, so the layering test stays unchanged.
- Then POST JSON `{data: base64, path, caption?, room?, reply_to?}` to `{ORCH_CHAT_URL}/chat/v1/images`; status and body pass through unchanged (D2 of the merged epic). Worst case 10 s + 10 s, under 30 s."

Design D7, verbatim: "Orchestrator read cap fixed 8,000,000."

Delta fix-as-ac, verbatim: "Image route runs the same checks as `_relay`, including 403 `trigger_session`."

Constraint, verbatim: "Orchestrator chat relay is JSON, 256 KiB body cap (`_capped_body`, api/chat.py:97), 10 s timeout, stores nothing. Only api/workspace.py may import wrapper (tests/test_api_sessions.py:237)."

Anti-goal, verbatim: "A tool reads an arbitrary file outside the session workdir, or bytes of a non-image (a credentials file) reach the chat."

Scope (agents-orchestrator):
- `api/chat.py`: the checks of `_relay` move into one helper that `_relay` and the new route share; `POST /agent/v1/chat/images` (202 pass-through, OpenAPI body `{path, caption?, room?, reply_to?}`): the capped body (256 KiB) must be a JSON object (else 422 `invalid_request`, my call: the api's existing code), `path` a string that `_normalise` accepts against the caller's session workdir (else 400 `invalid_path`); `read_file_bytes` for the caller's own agent; then the upstream body `{data: <base64>, path: <the normalised workdir-relative path>, ...}` with `caption`, `room` and `reply_to` passed through as the agent sent them (my call: the relative path is what the wrapper download route and the web renderer resolve); forwarded with the same `forward` (10 s, same headers, pass-through, 503 `chat_unavailable`).
- `api/workspace.py`: `read_file_bytes(pool, settings, http, session_id, agent_id, path, max_bytes) -> bytes` (signature per the review fix below): `resolve_agent(session_id=..., agent_id=...)` under `pool.connection()`, released before the read, `WrapperClient.open_download`, reads raw chunks until more than `max_bytes` (413 `image_too_large`) inside `asyncio.timeout(10)`; wrapper errors through `_wrapper_errors`; the deadline is 502 `wrapper_unreachable` (my call: an existing code); the stream is always closed.
- Tests no longer accurate (named): `tests/test_agent_chat.py::test_readme_documents_chat_routes` (its served-route set gains `POST /agent/v1/chat/images`) and `tests/test_chat_contract.py::test_relay_routes_exist_upstream` (four relayed routes become five).
- `openapi.json` regenerated; README `### Chat` documents five routes and the image route's checks, read cap and codes; MEMORY.md: the image route parses `path` and is the only chat route that reads a body; it reads the caller's own pod.

Review fix, interrogate 2026-10-29 Act on 4 (seam holds a pool connection across the read), verbatim: "orch-chat-images-route's `read_file_bytes(conn, ...)` contradicts its own note "Hold no pool connection across the wrapper read or the upstream call"; `download_file` resolves under `pool.connection()` then releases (workspace.py:496-503). Fix: the seam takes the pool (or a resolved target) and releases the connection before the read and the upstream POST; AC." For this task: the seam takes the pool (my call between the two options: it keeps `resolve_agent` inside workspace.py exactly as `download_file` does), resolves the caller's agent inside `async with pool.connection()` and leaves that block before `open_download`; the shared checks (`_session`, `_leads`, under `pool.connection()` as in `_relay`, api/chat.py:153) release their connection before the seam is called, and no connection is checked out during the upstream POST.

#### Acceptance conditions

- ac1: the leader of a user session gets the file read through its own agent's wrapper and forwarded to /chat/v1/images as {data: base64 of the exact bytes, path: normalised workdir-relative, caption, room, reply_to} with only the chat bearer, X-Orch-Session, X-Orch-Slug and Content-Type; the upstream 202 body comes back unchanged [evidence: test:tests/test_agent_chat.py::test_image_read_and_forwarded]
- ac2: an absolute path under the workdir is normalised; an empty, escaping, outside, NUL, missing or non-string path is 400 invalid_path and a body that is not a JSON object 422 invalid_request, with no wrapper or upstream call [evidence: test:tests/test_agent_chat.py::test_image_invalid_path]
- ac3: the route runs the relay's checks in the relay's order: 401 and 403 identity, 403 trigger_session, 403 not_leader, 503 chat_unconfigured, 413 payload_too_large over 256 KiB; a refusal calls neither the wrapper nor the upstream [evidence: test:tests/test_agent_chat.py::test_image_route_shares_relay_checks]
- ac4: a file of 8,000,000 bytes is forwarded whole; one of 8,000,001 bytes or more is 413 image_too_large after reading at most 8,000,001 bytes [evidence: test:tests/test_agent_chat.py::test_image_read_cap]
- ac5: a wrapper 404 is 404 not_found, a wrapper 5xx 502 wrapper_error, an unreachable wrapper or the 10 s read deadline 502 wrapper_unreachable, an upstream failure 503 chat_unavailable [evidence: test:tests/test_agent_chat.py::test_image_wrapper_and_upstream_errors]
- ac6: the file is read from the calling agent's own pod, never another agent's of the session [evidence: test:tests/test_agent_chat.py::test_image_read_from_caller_pod]
- ac7: only api/workspace.py imports the wrapper client (unchanged test) [evidence: test:tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper]
- ac8: the five relayed routes exist in the vendored upstream contract (updated, named) [evidence: test:tests/test_chat_contract.py::test_relay_routes_exist_upstream]
- ac9: the README documents the five chat routes and their codes (updated, named) [evidence: test:tests/test_agent_chat.py::test_readme_documents_chat_routes]
- ac10: the committed openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- ac11: MEMORY.md records the image route ruling [evidence: command:grep -q 'chat/images' MEMORY.md]
- ac12: the targeted tests and lint pass (no database) [evidence: command:uv run --frozen pytest tests/test_agent_chat.py tests/test_chat_contract.py tests/test_readme_api.py tests/test_api_sessions.py::test_api_never_imports_k8s_or_wrapper && mise run lint]
- ac13: no pool connection is checked out while the wrapper download is read or while the upstream POST runs; read_file_bytes takes the pool, not a connection [evidence: test:tests/test_agent_chat.py::test_image_route_holds_no_connection_during_io]

#### Files

- `src/agents_orchestrator/api/chat.py`
- `src/agents_orchestrator/api/workspace.py`
- `tests/test_agent_chat.py`
- `tests/test_chat_contract.py`
- `openapi.json`
- `README.md`
- `MEMORY.md`

#### Interfaces

- `POST /agent/v1/chat/images` (agent port): body `{path, caption?, room?, reply_to?}`; 202 and refusals passed through from `{ORCH_CHAT_URL}/chat/v1/images`; own refusals 400 `invalid_path`, 401, 403 `forbidden`/`trigger_session`/`not_leader`, 404 `not_found`, 409 `agent_not_ready`, 413 `payload_too_large`/`image_too_large`, 422 `invalid_request`, 502 `wrapper_error`/`wrapper_unreachable`, 503 `chat_unconfigured`/`chat_unavailable`.
- `api/workspace.read_file_bytes(pool, settings, http, session_id: uuid.UUID, agent_id: uuid.UUID, path: str, max_bytes: int) -> bytes`.
- Upstream body (contract, orch-chat-contract-refresh): `{data: str (base64), path: str, caption?: str, room?: str, reply_to?: str}`.

#### Expected outcome

An agent's picture path becomes one connector call carrying the picture's bytes, read only from the caller's own workspace and only by a leader allowed to use the chat.

#### Steps

- Read `api/chat.py`, `api/workspace.py`, `api/agent.py:_normalise`, `tests/test_agent_chat.py`, `tests/fakes/fake_wrapper.py` (its download route) and `tests/test_chat_contract.py`.
- Red: the image tests (ac1-ac6) using the in-memory rig, the fake wrapper download and `FakeChat`; update the two named tests; run `uv run --frozen pytest tests/test_agent_chat.py tests/test_chat_contract.py`: fail (404 route).
- Green: the shared checks, the route, `read_file_bytes`; `uv run python -m agents_orchestrator.api.openapi > openapi.json`; README, MEMORY.md; run the task's verify: passes. Quote the summary line.

#### Notes

- Non-DB tests fake the repository reads of `require_agent` and `_leads` (MEMORY 2026-10-28), so this verify runs in agent pods; keep any DB variant marked like `test_leader_only_and_identity_db`.
- Hold no pool connection across the wrapper read or the upstream call.
- The 8,000,000 literal mirrors the connector's `MATRIX_IMAGE_MAX_BYTES` maximum; ac4 pins it (retro file-editor-with-tabs-and-hi).
- Shared files with the epics before (`api/chat.py`, `openapi.json`, README): read them as merged on main.

- 2026-10-29 amended: interrogate 2026-10-29 act on 4
- (review fix) The design D2 quote above still reads `read_file_bytes(conn, ...)`; the review fix for interrogate Act on 4 replaces it by the pool (Interfaces and Scope follow it).

### S11: mxc e2e image send

- Status: todo
- Files: `tests/e2e/test_e2e_agent.py`, `tests/e2e/conftest.py`
- Verify: `uv run --frozen pytest tests/e2e/test_e2e_agent.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G1, verbatim: "an agent sends a picture (jpeg, png, gif or webp, judged by content, at most 8,000,000 bytes) from a file in its session workspace to its chat room through a new tool orchestrator_chat_send_image {path, caption?, room?, reply_to?}; the owner sees it in Messenger through the bridge."

README Goal G2, verbatim: "the Matrix token stays in the bot pod: the bot uploads the bytes and sends m.image; the caption goes as its own text message after the picture; reply_to anchors the picture."

README Goal G4, verbatim: "limits and failures are explicit: unsupported type, too large, missing file and rate (5 pictures a minute per session inside the 20 sends a minute) refuse synchronously with a named error; upload failures and bridge error notices mark the send failed, visible in orchestrator_chat_status."

Design D5, verbatim: "Fake homeserver grows the upload and media-config routes."

Scope (agents-matrix-connector): end-to-end tests through the real console script (migrate, api, bot) against the fake homeserver, as `tests/e2e/test_e2e_agent.py` does for messages: an image send with a caption and a reply, a bridge notice failing it, and an upload the homeserver rejects. Test code only.

#### Acceptance conditions

- ac1: POST /chat/v1/images with a png, a caption and reply_to leads to one upload on the fake homeserver with the exact bytes, then one m.image (url the uploaded mxc, info mimetype and size, m.in_reply_to) and then the caption as m.text, and the send ends sent [evidence: test:tests/e2e/test_e2e_agent.py::test_e2e_image_send]
- ac2: a bridge-bot m.notice replying to the m.image turns that send failed with reason "bridge: <body>" [evidence: test:tests/e2e/test_e2e_agent.py::test_e2e_bridge_notice_fails_send]
- ac3: an upload the fake rejects with 413 M_TOO_LARGE ends the send failed upload_rejected:M_TOO_LARGE and no m.image is sent [evidence: test:tests/e2e/test_e2e_agent.py::test_e2e_image_upload_rejected]
- ac4: the e2e agent tests and lint pass (CI: needs Docker) [evidence: command:uv run --frozen pytest tests/e2e/test_e2e_agent.py && mise run lint]

#### Files

- `tests/e2e/test_e2e_agent.py`
- `tests/e2e/conftest.py`

#### Interfaces

- None new: the agent listener `POST /chat/v1/images`, `GET /chat/v1/messages/{id}` and the fake homeserver's recorded uploads and sent events.

#### Expected outcome

The whole connector path for pictures (api, queue, upload, send, bridge notice) is proven together, not only per unit.

#### Steps

- Red/green: these are integration tests over code the dependencies built; write them, run `uv run --frozen pytest tests/e2e/test_e2e_agent.py`, and if one fails for a product reason, report it as a discovered gap rather than editing product code here.
- Quote the CI run of the pushed head (the e2e suite needs Postgres).

#### Notes

- DB-backed tests (testcontainers Postgres) need Docker; agent pods have none, so they error here (baseline 2026-10-29: 182 Docker errors) and CI on the PR is the gate for them (recurring retro). Run the verify, quote the local summary line and the CI run of the pushed head. Keep each pure helper covered by a non-DB test so the local run has signal.
- Reuse the fixtures in `tests/e2e/conftest.py` (the real console script and the fake homeserver); add an upload-limit or `fail_next` setter only through the fake's existing API from mxc-matrix-media-upload.

### S12: mxc room messages msgtype

- Status: todo
- Files: `src/agents_matrix_connector/api/schemas.py`, `src/agents_matrix_connector/api/rooms.py`, `openapi.json`, `README.md`, `tests/test_api_rooms.py`
- Verify: `uv run --frozen pytest tests/test_api_rooms.py tests/test_readme_api.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G3, verbatim: "the session web chat shows the sent picture inside the tool-call box from the same-origin session download route; message text still never renders images; the Chats page shows "picture: <name>"."

Design D8, verbatim: "Chats page: MessageView grows `msgtype` (from outbound.content); RoomMessages shows "picture: <name>" for m.image. No bytes served by the connector, no mxc proxy. User Q3."

brief-cartographer fix-as-ac, verbatim: "`_out_view` / `MessageView` (`api/schemas.py:69`) expose only `body`: an image row must not render as an empty or misleading line on the Chats page."

Scope (agents-matrix-connector, UI API):
- `api/schemas.py`: `MessageView.msgtype: str | None`.
- `api/rooms.py`: `_out_view` sets `msgtype` from `outbound.content["msgtype"]` when the row has content, else null; inbound rows null. The image row's `body` is the picture name (stored by mxc-bot-image-upload).
- `openapi.json` regenerated; README documents the field on `GET /matrix/api/v1/rooms/{room_id}/messages`.
- No image bytes and no mxc URL in the view (non-goal).

#### Acceptance conditions

- ac1: an outbound image row lists msgtype m.image with the picture name as body and no mxc URL; rows without content and inbound rows list msgtype null [evidence: test:tests/test_api_rooms.py::test_room_messages_msgtype]
- ac2: the committed UI OpenAPI matches the app [evidence: test:tests/test_readme_api.py::test_openapi_committed_matches]
- ac3: the README documents msgtype on the messages route [evidence: command:grep -q 'msgtype' README.md]
- ac4: the targeted tests and lint pass (DB tests in CI) [evidence: command:uv run --frozen pytest tests/test_api_rooms.py tests/test_readme_api.py && mise run lint]

#### Files

- `src/agents_matrix_connector/api/schemas.py`
- `src/agents_matrix_connector/api/rooms.py`
- `openapi.json`
- `README.md`
- `tests/test_api_rooms.py`

#### Interfaces

- `MessageView.msgtype: str | None` on `GET /matrix/api/v1/rooms/{room_id}/messages` (consumed by agents-web, task web-room-messages-picture).

#### Expected outcome

The Chats page API tells a picture row apart from a text row without serving any image data.

#### Steps

- Red: `test_room_messages_msgtype` (insert an outbound row with m.image content through `runs.add_outbound`); run `uv run --frozen pytest tests/test_api_rooms.py::test_room_messages_msgtype`: errors locally (no Docker), fails in CI.
- Green: schema field, `_out_view`, regenerate `openapi.json`, README; run the task's verify; quote the local summary line and the CI run.

#### Notes

- DB-backed tests (testcontainers Postgres) need Docker; agent pods have none, so they error here (baseline 2026-10-29: 182 Docker errors) and CI on the PR is the gate for them (recurring retro). Run the verify, quote the local summary line and the CI run of the pushed head. Keep each pure helper covered by a non-DB test so the local run has signal.
- `OutboundRow.content` and `list_outbound` returning it come from mxc-send-images-schema.

### S13: orch plugins pin and tool

- Status: todo
- Files: `src/agents_orchestrator/settings.py`, `pyproject.toml`, `uv.lock`, `README.md`, `src/agents_orchestrator/k8s/on_start.py`, `tests/test_settings.py`, `tests/test_images.py`, `tests/test_on_start.py`, `tests/test_agent_chat.py`
- Verify: `uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py tests/test_agent_chat.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G5, verbatim: "released and deployed in order (plugins, connector, orchestrator, web, helmfile) and proven by a live smoke that posts one real picture with a caption to the owner's Messenger DM."

Design D9, verbatim: "Orchestrator: pin `<TAG>` and add the tool to `CHAT_TOOLS` (k8s/on_start.py:31) in one change (D13 probe); trigger sessions keep losing every chat tool (:43)."

Anti-goal, verbatim: "A second chat-tool allow list, or trigger sessions gaining the image tool."

User decision (binding), verbatim: "Release numbers are placeholders resolved at build time, exactly as /workdir/workdir/docs/plans/in-progress/hive-decoupling does (read its design.md 'Build-time settlements' and tasks orch-activity-route, plugins-release-0-4-0, orch-plugins-pin-0-4-0, helmfile-deploy-pin for the pattern): <MIGRATION> for the connector migration (0003 is claimed by immediate-message-delivery-w), <TAG>/<VERSION> for the plugins release (v0.3.0-v0.5.0 claimed). The first task needing each reads it from main and amends dependents."

`<TAG>` (the plugins release tag, `vX.Y.Z`) is filled by `ticket.py amend` from plugins-release-images before this task starts. Needs a merged upstream: any-mcp-tatara-plugins tag `<TAG>` on origin.

Scope (agents-orchestrator):
- `src/agents_orchestrator/settings.py`: `any_mcp_plugins_ref` default `<TAG>`.
- `pyproject.toml`: dev dependency `any-mcp-tatara-orchestrator @ git+https://github.com/szymonrychu/any-mcp-tatara-plugins@<TAG>#subdirectory=orchestration/orchestrator`; `uv lock` updates `uv.lock`.
- `README.md`: the `ORCH_ANY_MCP_PLUGINS_REF` row default `<TAG>`, the `## Images` plugins release tag, and `orchestrator_chat_send_image` among the chat tools of `### Chat`.
- `src/agents_orchestrator/k8s/on_start.py`: `CHAT_TOOLS` gains `chat_send_image`; `chat=False` still drops every chat tool.
- Tests no longer accurate (named): `tests/test_settings.py::test_defaults` (pins the previous plugins tag) and the `CHAT_TOOLS` constant of `tests/test_on_start.py` (pins the four chat tools).
- `tests/test_agent_chat.py`: the released plugin's `chat_send_image` against the real image route (parity, like `test_chat_tools_parity`).

#### Acceptance conditions

- ac1: the settings default is <TAG> (updated, named) [evidence: test:tests/test_settings.py::test_defaults]
- ac2: the dev dependency and uv.lock pin the same plugins tag as the settings default [evidence: test:tests/test_images.py::test_plugins_dev_pin_matches_settings_ref]
- ac3: the README documents the <TAG> default and names no older plugins tag [evidence: command:grep -qF '| `ORCH_ANY_MCP_PLUGINS_REF` | `<TAG>` |' README.md && test "$(grep -oE 'plugins release tag \(`v[0-9.]+`\)' README.md | grep -vc '<TAG>')" = 0]
- ac4: every non-trigger session's allow list carries chat_send_image after the other chat tools (CHAT_TOOLS constant updated, named) [evidence: test:tests/test_on_start.py::test_alone_session_tools_entry]
- ac5: sessions started by a trigger service get none of the five chat tools [evidence: test:tests/test_on_start.py::test_trigger_service_sessions_get_no_chat_tools]
- ac6: every allowed tool name is offered by the pinned plugin [evidence: test:tests/test_on_start.py::test_allowed_tools_exist_in_plugin]
- ac7: the released plugin's chat_send_image drives the real image route against the fake wrapper and FakeChat with the same result as a direct call, and a member's call is refused not_leader [evidence: test:tests/test_agent_chat.py::test_chat_send_image_parity]
- ac8: the README names orchestrator_chat_send_image in the Chat section [evidence: command:grep -q 'orchestrator_chat_send_image' README.md]
- ac9: settings, images, on-start and chat suites and lint pass (no database) [evidence: command:uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py tests/test_agent_chat.py && mise run lint]

#### Files

- `src/agents_orchestrator/settings.py`
- `pyproject.toml`
- `uv.lock`
- `README.md`
- `src/agents_orchestrator/k8s/on_start.py`
- `tests/test_settings.py`
- `tests/test_images.py`
- `tests/test_on_start.py`
- `tests/test_agent_chat.py`

#### Interfaces

- `Settings.any_mcp_plugins_ref` default `<TAG>` (`ORCH_ANY_MCP_PLUGINS_REF`); `k8s/on_start.CHAT_TOOLS == ["chat_rooms", "chat_send", "chat_react", "chat_status", "chat_send_image"]` (order within the list is the builder's).

#### Expected outcome

Agent pods rendered by this orchestrator install the plugins release with the picture tool and may call it; trigger sessions still see no chat tool.

#### Steps

- Confirm tag `<TAG>` on any-mcp-tatara-plugins origin (`git ls-remote --tags https://github.com/szymonrychu/any-mcp-tatara-plugins <TAG>`); stop and report if absent.
- Red: update `test_defaults` and the test `CHAT_TOOLS` constant, add `test_chat_send_image_parity`; run `uv run --frozen pytest tests/test_settings.py tests/test_on_start.py tests/test_agent_chat.py`: fail.
- Green: settings default, pyproject pin, `uv lock`, `CHAT_TOOLS`, README; run the task's verify: passes. Quote the summary line.

#### Notes

- Dependency-bump TDD exception for the version values; `test_plugins_dev_pin_matches_settings_ref` ties the three to one tag.
- The pin and the allow list land in one change: `test_allowed_tools_exist_in_plugin` fails when the allow list names a tool the pinned plugin lacks (D13 probe).
- Changing the default changes the rendered config hash and rolls agent pods on deploy (README `## Images`); the deploy is pictures-live-smoke.
- (my call, builder-check Q5) `tests/test_images.py` may be edited only for the plugins pin literals the tag bump changes; no other edit to it.

### S14: web room messages picture

- Status: todo
- Files: `openapi/matrix.json`, `openapi/matrix.source`, `src/api/matrix-schema.d.ts`, `src/matrix/RoomMessages.tsx`, `src/matrix/RoomMessages.test.tsx`
- Verify: `npx vitest run src/matrix && npm run check:api && npm run lint`
- Verified head: none

#### Requirement

README Goal G3, verbatim: "the session web chat shows the sent picture inside the tool-call box from the same-origin session download route; message text still never renders images; the Chats page shows "picture: <name>"."

Design D8, verbatim: "Chats page: MessageView grows `msgtype` (from outbound.content); RoomMessages shows "picture: <name>" for m.image. No bytes served by the connector, no mxc proxy. User Q3."

Open question Q3 (planned on its recommended answer): "The Chats page shows a "picture: <name>" line, not the image? [recommended: yes]"

Scope (agents-web):
- `openapi/matrix.json` synced (`npm run sync:api -- matrix`) from the connector commit that carries `MessageView.msgtype` (mxc-room-messages-msgtype): connector `main` once merged, else the connector epic-branch commit kept reachable by a merge commit (my call, the matrix epic's precedent 23f0424); `openapi/matrix.source` names it; `src/api/matrix-schema.d.ts` regenerated.
- `src/matrix/RoomMessages.tsx`: an outbound row with `msgtype` `m.image` shows `picture: <body>` in the Body cell; every other row as today; no `<img>`.
- `src/matrix/RoomMessages.test.tsx` (new test file).

#### Acceptance conditions

- ac1: an outbound message with msgtype m.image shows "picture: <name>" in the Body cell, and text rows and inbound rows show their body as before [evidence: command:npx vitest run src/matrix/RoomMessages.test.tsx]
- ac2: the matrix OpenAPI copy and its types agree, and the source names the connector commit carrying msgtype [evidence: command:npm run check:api && grep -q 'msgtype' openapi/matrix.json && grep -qE '^agents-matrix-connector [0-9a-f]{40}$' openapi/matrix.source]
- ac3: RoomMessages renders no img [evidence: command:test "$(grep -c '<img' src/matrix/RoomMessages.tsx)" = 0]
- ac4: the matrix tests, API check and lint pass [evidence: command:npx vitest run src/matrix && npm run check:api && npm run lint]

#### Files

- `openapi/matrix.json`
- `openapi/matrix.source`
- `src/api/matrix-schema.d.ts`
- `src/matrix/RoomMessages.tsx`
- `src/matrix/RoomMessages.test.tsx`

#### Interfaces

- `MessageView.msgtype: string | null` (connector UI API, `src/api/matrix-schema.d.ts`, re-exported by `src/matrix/api.ts`).

#### Expected outcome

The Chats page lists a picture the agent sent as "picture: <name>" instead of a bare file name.

#### Steps

- Red: `src/matrix/RoomMessages.test.tsx` (mock `listRoomMessages` as `ChatsPage.test.tsx` does); run `npx vitest run src/matrix/RoomMessages.test.tsx`: fails.
- Green: sync the matrix API from the connector commit, regenerate the types, the Body cell; run the task's verify: passes. Quote the summary line.

#### Notes

- `npm run sync:api -- matrix [--from <checkout>]` reads the sibling `../agents-matrix-connector`; check out the pinned commit there first.
- No bytes and no mxc URL reach the browser (non-goal: image bytes on the Chats page).
- (my call, builder-check Q1) The connector tasks merge to connector `main` first; this task starts after that and pins the connector `main` sha, so the epic-branch fallback in Scope is not used.

### S15: helmfile pictures pin

- Status: todo
- Files: `helmfile.yaml.gotmpl`, `values/agents-matrix-connector/common.yaml`, `values/agents-orchestrator/common.yaml`, `values/agents-web/common.yaml`, `tests/test_matrix_connector_release.py`, `tests/test_orchestrator_release.py`, `tests/test_web_release.py`
- Verify: `uv run --frozen pytest -q -p no:cacheprovider tests/test_matrix_connector_release.py tests/test_orchestrator_release.py tests/test_web_release.py && mise run lint`
- Verified head: none

#### Requirement

README Goal G5, verbatim: "released and deployed in order (plugins, connector, orchestrator, web, helmfile) and proven by a live smoke that posts one real picture with a caption to the owner's Messenger DM."

Design D9, verbatim: "Release and deploy order: plugins, connector, orchestrator, web, helmfile (image tags, chart versions, `ORCH_ANY_MCP_PLUGINS_REF: <TAG>`, connector image settings)."

User decision (binding), verbatim: "Release numbers are placeholders resolved at build time, exactly as /workdir/workdir/docs/plans/in-progress/hive-decoupling does (read its design.md 'Build-time settlements' and tasks orch-activity-route, plugins-release-0-4-0, orch-plugins-pin-0-4-0, helmfile-deploy-pin for the pattern): <MIGRATION> for the connector migration (0003 is claimed by immediate-message-delivery-w), <TAG>/<VERSION> for the plugins release (v0.3.0-v0.5.0 claimed). The first task needing each reads it from main and amends dependents."

`<TAG>` is filled by `ticket.py amend` from plugins-release-images; each `<sha7>` below is filled by `ticket.py amend` when that repo's PR merges to `main` and CI publishes the image and chart.

Scope (agents-helmfile):
- `helmfile.yaml.gotmpl` and `values/agents-matrix-connector/common.yaml`: connector chart `0.1.0-main.<connector sha7>` and `image.tag` `<connector sha7>`, the connector `main` commit carrying every connector task of this epic.
- `helmfile.yaml.gotmpl` and `values/agents-orchestrator/common.yaml`: orchestrator chart and `image.tag` `<orchestrator sha7>`; `env.ORCH_ANY_MCP_PLUGINS_REF: <TAG>`.
- `helmfile.yaml.gotmpl` and `values/agents-web/common.yaml`: web chart and `image.tag` `<web sha7>`.
- "connector image settings" is read as the connector image pins above: the picture limits keep their connector defaults (`MATRIX_IMAGE_MAX_BYTES` 8000000, `MATRIX_AGENT_IMAGE_RATE_PER_MINUTE` 5) and no connector value is added (my call: the connector chart has no generic env map and the defaults are the decided limits).
- `tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions` is no longer accurate (named): it asserts the previous plugins ref; it asserts `<TAG>`.
- Before changing a value, confirm that image tag and chart version exist in Harbor (retro: Harbor prunes tags). No apply here (pictures-live-smoke).

#### Acceptance conditions

- ac1: the connector chart version and image tag agree on the connector merge sha7 and the release still needs its database [evidence: test:tests/test_matrix_connector_release.py::test_matrix_connector_pin_and_needs]
- ac2: the orchestrator chart version and image tag agree on the orchestrator merge sha7 [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- ac3: the web chart version and image tag agree on the web merge sha7 [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- ac4: new sessions get the <TAG> plugins ref (updated, named) [evidence: test:tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions]
- ac5: each pinned sha7 is a main commit of its repo containing every task of this epic in that repo, with green CI [evidence: judgement:reviewer checks git merge-base --is-ancestor of each task's verified_head against the pinned sha and the CI run of that sha]
- ac6: every pin's main CI is green [evidence: command:mise run check-pins]
- ac7: (orchestrator session) Harbor holds each pinned image tag and chart version [evidence: judgement:orchestrator records the registry check of each tag and chart in the task Notes]
- ac8: the release tests and lint pass [evidence: command:uv run --frozen pytest -q -p no:cacheprovider tests/test_matrix_connector_release.py tests/test_orchestrator_release.py tests/test_web_release.py && mise run lint]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-matrix-connector/common.yaml`
- `values/agents-orchestrator/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_matrix_connector_release.py`
- `tests/test_orchestrator_release.py`
- `tests/test_web_release.py`

#### Interfaces

- `values/agents-matrix-connector/common.yaml` `image.tag`; `values/agents-orchestrator/common.yaml` `image.tag`, `env.ORCH_ANY_MCP_PLUGINS_REF`; `values/agents-web/common.yaml` `image.tag`; the three chart `version`s in `helmfile.yaml.gotmpl`.

#### Expected outcome

agents-helmfile pins the picture-capable connector, orchestrator and web and the `<TAG>` plugins release, ready to apply in order.

#### Steps

- Red: point `test_any_mcp_configured_for_new_sessions` at `<TAG>`; run `uv run --frozen pytest -q -p no:cacheprovider tests/test_orchestrator_release.py`: fails.
- Green: the three pins (the sha7s from the amendments, each checked in Harbor first) and the plugins ref; run the task's verify and `mise run check-pins`. Quote the summary lines.

#### Notes

- Dependency-bump TDD exception (pin changes); the release tests are the guard.
- `test_release_chart_version_and_needs` and `test_db_secret_matches_rendered_cnpg_cluster_helmfile_build` run `helmfile build` and need network and a helm version in the mise shim (absent in agent pods, baseline 2026-10-29); run them before the apply in pictures-live-smoke.
- The epics before (hive-decoupling, immediate-message-delivery-w) also edit these values: build on their merged pins.

### S16: pictures live smoke

- Status: todo
- Files: `MEMORY.md`
- Verify: `mise run lint && grep -q 'pictures live smoke' MEMORY.md`
- Verified head: none

#### Requirement

User decision (binding), verbatim: "Live smoke posts one real picture with a caption to the owner's Messenger DM after the helmfile apply under the deploy lease (Lease agents/agents-helmfile-apply)."

README Goal G5, verbatim: "released and deployed in order (plugins, connector, orchestrator, web, helmfile) and proven by a live smoke that posts one real picture with a caption to the owner's Messenger DM."

Design D10, verbatim: "After the helmfile apply (deploy lease taken), the session posts one real picture with a caption to the owner's Messenger DM through the tool; the owner confirms in Messenger; the web chat shows the picture; orchestrator_chat_status shows the send `sent`. User Q7."

Open question Q7 (planned on its recommended answer): "The live smoke posts one real picture with a caption to your Messenger DM? [recommended: yes]"

Steps, run by the orchestrator session (never a subagent: subagent `kubectl exec` and applies are denied), in `code/agents-helmfile` on `main` after the helmfile-pictures-pin PR merged, least destructive first:
1. Claim the deploy lease, Lease `agents/agents-helmfile-apply`, before the first diff; hold it through the applies and the smoke; release it at the end. Procedure (workbench practice, cct2 2026-10-28): `kubectl create -f` a `coordination.k8s.io/v1` Lease `agents/agents-helmfile-apply` with `holderIdentity` (this session), `acquireTime` and `leaseDurationSeconds: 3600`; `create` fails when the lease exists, then wait for it; a lease older than 60 minutes is stale, and the holder is messaged via the superleader before anyone deletes it; delete only your own lease at the end. Kubeconfig from the pod service account (context `in-cluster-sa`, `EXPECTED_KUBE_CONTEXT=in-cluster-sa`). It never applies without the lease.
2. Check each pinned image tag and chart version exists in Harbor; run the release tests that need `helmfile build` (helmfile-pictures-pin Notes).
3. Per release in the order connector, orchestrator, web (`--selector name=agents-matrix-connector`, then `name=agents-orchestrator`, then `name=agents-web`): `mise run diff -- --selector name=<release>` and read it: the change is the chart version, the image tag and, for the orchestrator, `ORCH_ANY_MCP_PLUGINS_REF`; anything else stops the task. Before the orchestrator apply (it rolls agent pods, the session running this task included) write a handoff checkpoint (`workbench:handoff`) naming the remaining steps, the pins and the Notes so far. Then `mise run apply -- --selector name=<release>`. The connector applies its send-images migration on start.
4. After the applies (by the resumed leader if the session was rolled): `mise run diff` shows no pending change; `mise run smoke` green.
5. Live picture (my call: "the session" of D10 is this orchestrator session, an agent session with the orchestrator plugin): save one small picture (a png) in its own workspace and call `orchestrator_chat_send_image` with that path, a caption naming the smoke and the date, and `room` the owner DM (`!iLWrAwaTMYnINJsyNv:szymonrichert.pl`, the chat-smoke default). The DM must be bound to this session, or unbound, flagged `agents_may_initiate` and this session bound to no room; a `room_bound` or `session_bound` refusal stops the task and asks the user, with no binding changed. Poll `orchestrator_chat_status` to `sent`. Open this session's chat in the web UI and confirm the picture shows in the tool-call box. Ask the user to confirm the picture and the caption in Messenger.
6. MEMORY.md entry containing the words `pictures live smoke`, dated, with the applied pins, the plugins ref, the send id, its status, the web check and the user's confirmation, and the Synapse `m.upload.size` the bot read (design: "Synapse `max_upload_size` is unknown ... the smoke confirms it").

Notes: never put `mise run apply` in AC evidence (agents-helmfile MEMORY 2026-10-25).

#### Acceptance conditions

- ac1: (orchestrator session) the deploy lease Lease agents/agents-helmfile-apply was held from the first diff to the end of the smoke [evidence: judgement:orchestrator records the claim and release times in the task Notes]
- ac2: (orchestrator session) each pinned image tag and chart version existed in Harbor before its apply, and each release's diff showed only its pins before its apply, applied in the order connector, orchestrator, web [evidence: judgement:orchestrator records the registry checks and the three diff summaries in the task Notes]
- ac3: after the applies helmfile reports no pending change [evidence: command:mise run diff]
- ac4: the regular smoke passes against the applied releases [evidence: command:mise run smoke]
- ac5: (orchestrator session) orchestrator_chat_send_image sent one real picture with a caption to the owner DM and orchestrator_chat_status reports it sent [evidence: judgement:orchestrator quotes the tool result (s<n>, path) and the final status in the task Notes]
- ac6: (orchestrator session) the session's web chat shows the picture in the tool-call box [evidence: judgement:orchestrator records what the web chat showed, with the session id, in the task Notes]
- ac7: (user) Messenger shows the picture followed by its caption [evidence: judgement:the user's one-line confirmation, quoted in the task Notes]
- ac8: (orchestrator session) a handoff checkpoint naming the remaining steps was written before the orchestrator apply, and the steps after the roll ran from it [evidence: judgement:orchestrator quotes the checkpoint path in the task Notes]
- ac9: agents-helmfile MEMORY.md records the live picture smoke and the applied versions [evidence: command:grep -q "pictures live smoke" MEMORY.md]

#### Files

- `MEMORY.md`

#### Interfaces

- None new; uses `mise run diff`, `mise run apply`, `mise run smoke`, the orchestrator plugin tools of the running session, the web UI and the Lease `agents/agents-helmfile-apply`.

#### Expected outcome

The deployed system sends a real picture with a caption from an agent session to the owner's Messenger DM, and the session web chat shows it.

#### Steps

- Orchestrator session only: steps 1-6 of the Requirement, in order; stop at step 3 if a diff shows more than the pins, and at step 5 on a binding refusal.
- Record each result in the task Notes as it happens (lease, registry checks, diffs, smoke tail, send id and status, web check, user confirmation), then the MEMORY.md entry; commit it through the agents-helmfile PR flow.

#### Notes

- Retro (recurring): live apply tasks run several times their seed and a live apply has surfaced defects tests missed; read every diff before its apply and keep helm's rollback as the last guard only.
- The orchestrator apply rolls the agent pods of every running session (new plugins ref, README `## Images`); write the Notes and the handoff checkpoint first.
- Captions are dropped by Messenger in E2EE chats only when inline; this epic sends the caption as its own m.text (D5), so the user should see both messages.
- Irreversible: one real Messenger message to the owner's DM (design.md Irreversible operations, Q7).

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
