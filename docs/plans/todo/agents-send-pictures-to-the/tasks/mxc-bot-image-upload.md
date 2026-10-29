---
title: mxc bot image upload
status: todo
repo: agents-matrix-connector
value: "a queued picture reaches the chat as one m.image plus its caption, with every upload failure named"
files: [src/agents_matrix_connector/sender.py, src/agents_matrix_connector/tracker.py, src/agents_matrix_connector/bot.py, README.md, MEMORY.md, tests/test_sender.py, tests/test_tracker.py, tests/test_readme_api.py]
verify: "uv run --frozen pytest tests/test_sender.py tests/test_tracker.py tests/test_readme_api.py && mise run lint"
depends_on: [mxc-send-images-schema, mxc-matrix-media-upload, mxc-images-route]
model: opus
review: ""
verified_head: ""
points: 8
expected_minutes: 27
expected_tokens: 4757438
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc bot image upload

## Requirement

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
- `sender.py`: `Sender` takes the `MatrixClient` (built in `bot.py`); each tick, before the claim: for every `sends.queued_images` row, the read-only pre-check ((a) `agent_room_decision`, (b) binding rules, as the claim); a refusal goes into `ready` as None so the claim refuses it as today (no upload, bytes cleared by the claim); else the size against `m.upload.size` (cached 1 h; None means `MATRIX_IMAGE_MAX_BYTES`), over it: `fail_queued` `upload_rejected:M_TOO_LARGE` without uploading (my call: the code Synapse would answer); else `upload_media` outside any transaction, its mxc into `ready`. 413 or 403 `M_FORBIDDEN`: `fail_queued` `upload_rejected:<errcode>`; any other non-auth Matrix 4xx: `fail_queued` `upload_rejected:<errcode or status>` (my call: not retryable); `MatrixUnavailable` (429 after the retry, 5xx, transport): stays queued until `created_at + 600 s`, then `fail_queued` `upload_failed`; `MatrixAuthError` propagates. Then `claim_queued(conn, now, ready)`; `_place` for an image stores the `mxa-<send>-i` row (kind `image`, body the picture name, `content` the m.image content with the reply relation when reply_to was given) and, with a caption, its `m.text` chunk rows `mxa-<send>-1..n` without a relation; never `empty_text` for an image.
- `tracker.py`: `_send_pending` sends a row's stored `content` as is when set, else `event_content` as today.
- `bot.py`: builds the `Sender` with the Matrix client.
- README: the reasons `upload_rejected:<errcode>` and `upload_failed`; `tests/test_readme_api.py::test_readme_lists_every_reason` gains the new reason constants. MEMORY.md: the upload-before-claim decision, bytes cleared at claim or failure, orphan media accepted.

## Acceptance conditions

- ac1: a queued png send is uploaded (filename the picture name, Content-Type its mime) before the claim; the claim sets mxc_uri, clears the bytes and stores row mxa-<send>-i whose content is {msgtype m.image, body name, filename name, url mxc, info {mimetype, size}} [evidence: test:tests/test_sender.py::test_image_send_uploaded_then_claimed]
- ac2: with a caption the m.image row comes first and the caption follows as m.text row(s) mxa-<send>-1..n; reply_to puts m.in_reply_to on the m.image only; without a caption there is one row and the send is never failed empty_text [evidence: test:tests/test_sender.py::test_image_caption_and_reply_rows]
- ac3: the tracker sends a row's stored content unchanged; once all rows are sent the send is sent with the picture's event id [evidence: test:tests/test_tracker.py::test_image_content_sent_as_stored]
- ac4: an image whose upload did not succeed this tick stays queued while the tick's message and reaction sends are claimed as before [evidence: test:tests/test_sender.py::test_unuploaded_image_stays_queued]
- ac5: an image the pre-check refuses is never uploaded and is refused at claim with the policy or binding reason, its bytes cleared [evidence: test:tests/test_sender.py::test_image_refused_without_upload]
- ac6: a 413 or 403 M_FORBIDDEN upload fails the send upload_rejected:<errcode> with its bytes cleared; a picture over m.upload.size fails upload_rejected:M_TOO_LARGE without an upload; an unknown media config falls back to MATRIX_IMAGE_MAX_BYTES [evidence: test:tests/test_sender.py::test_image_upload_rejected]
- ac7: 429, 5xx and transport failures leave the send queued and retry next tick; after created_at + 600 s it fails upload_failed; a lost token propagates [evidence: test:tests/test_sender.py::test_image_upload_retry_window]
- ac8: the media config is read at most once an hour [evidence: test:tests/test_sender.py::test_media_config_cached]
- ac9: a crash between upload and claim re-uploads on the next tick and exactly one m.image is sent (txn mxa-<send>-i) [evidence: test:tests/test_sender.py::test_image_restart_exactly_once]
- ac10: no log line carries the bytes or their base64 [evidence: test:tests/test_sender.py::test_image_bytes_never_logged]
- ac11: text sends and reactions behave as before: the existing sender and tracker assertions are unchanged, only Sender construction lines change [evidence: judgement:reviewer reads the diff of tests/test_sender.py and tests/test_tracker.py]
- ac12: README names upload_rejected:<errcode> and upload_failed and the reason test lists them; MEMORY.md records upload before claim and the accepted orphan media [evidence: command:uv run --frozen pytest tests/test_readme_api.py::test_readme_lists_every_reason && grep -qi 'orphan' MEMORY.md]
- ac13: the targeted tests and lint pass (DB tests in CI) [evidence: command:uv run --frozen pytest tests/test_sender.py tests/test_tracker.py tests/test_readme_api.py && mise run lint]

## Files

- `src/agents_matrix_connector/sender.py`
- `src/agents_matrix_connector/tracker.py`
- `src/agents_matrix_connector/bot.py`
- `README.md`
- `MEMORY.md`
- `tests/test_sender.py`
- `tests/test_tracker.py`
- `tests/test_readme_api.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
