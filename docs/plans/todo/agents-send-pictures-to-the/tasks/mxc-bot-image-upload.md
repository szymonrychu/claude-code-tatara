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
- `sender.py`: `Sender` takes the `MatrixClient` (built in `bot.py`); each tick, before the claim: for every `sends.queued_images` row, the read-only pre-check ((a) `agent_room_decision`, (b) binding rules, as the claim); a refusal goes into `ready` as None (no upload; handled as the review fix for interrogate item 1 below says); else the size against `m.upload.size` (cached 1 h; None means `MATRIX_IMAGE_MAX_BYTES`), over it: `fail_queued` `upload_rejected:M_TOO_LARGE` without uploading (my call: the code Synapse would answer); else `upload_media` outside any transaction, its mxc into `ready`. 413 or 403 `M_FORBIDDEN`: `fail_queued` `upload_rejected:<errcode>`; any other non-auth Matrix 4xx: `fail_queued` `upload_rejected:<errcode or status>` (my call: not retryable); `MatrixUnavailable` (429 after the retry, 5xx, transport): stays queued until `created_at + 600 s`, then `fail_queued` `upload_failed`; `MatrixAuthError` propagates. Then `claim_queued(conn, now, ready)`; `_place` for an image stores the `mxa-<send>-i` row (kind `image`, body the picture name, `content` the m.image content with the reply relation when reply_to was given) and, with a caption, its `m.text` chunk rows `mxa-<send>-1..n` without a relation; never `empty_text` for an image.
- `tracker.py`: `_send_pending` sends a row's stored `content` as is when set, else `event_content` as today.
- `bot.py`: builds the `Sender` with the Matrix client.
- README: the reasons `upload_rejected:<errcode>` and `upload_failed`; `tests/test_readme_api.py::test_readme_lists_every_reason` gains the new reason constants. MEMORY.md: the upload-before-claim decision, bytes cleared at claim or failure, orphan media accepted.

Review fix, interrogate 2026-10-29 Act on 1 (pre-check refusal becomes a placed image with no mxc), verbatim: "a claimed image without a successful upload this tick is never placed: a None entry fails (guarded) with the pre-check's reason and clears the bytes; an image is placed only with its `mxc_uri`; an authoritative re-check that refuses after upload refuses as today (orphan media accepted). AC: "policy flips between pre-check and claim" and "no outbound m.image row without url"." For this task: the sender keeps the pre-check's reason per send for the tick; a send claimed from a None entry goes through the guarded `sending -> refused` (`sends.mark_refused`) with that reason, its bytes already cleared by the claim, and `_place` is never called for it (my call: `refused`, the status a claim-time policy or binding refusal has today, so orchestrator_chat_status reads the same); `_place` stores an `m.image` row only from a non-empty `mxc_uri`, so no path stores an `m.image` without `url`.

Review fix, interrogate 2026-10-29 Consider (folded into Act on 1), verbatim: "the pre-check calls one pure decision function shared with the claim (my call; extracting it from `may_post` too is boy-scout only if the task already touches it)." For this task: the room (a) and binding (b) rules are one pure function over the room policy answer, the active binding and the room settings, called by the read-only pre-check and by the claim (`_place`/`_authorise`, which then binds); `api/agent.py:may_post` is not in this task's files and stays as is.

Review fix, interrogate 2026-10-29 Act on 3 (upload outage stalls text sends and reactions), verbatim: "the upload pass stops at the first MatrixUnavailable or transport error (as the tracker does, tracker.py:207-212), and text/reaction claims in the same tick are not delayed by it; AC: during an upload outage a queued text send is still claimed in that tick." For this task: on the first `MatrixUnavailable` (429 after the retry, 5xx, transport) the pass attempts no further upload in that tick; the images not attempted stay queued with their bytes and are not in `ready`, except that each one past `created_at + 600 s` fails `upload_failed` without an upload (my call: D4's retry window holds for every image, attempted or not); the claim of the same tick then runs as today for message and reaction sends.

## Acceptance conditions

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

- `Sender(matrix: MatrixClient, pool, settings, *, now=utcnow)`; `Sender.tick()` = upload step, claim, settle.
- Outbound image row: kind `image`, `event_type` `m.room.message`, body the picture name, `content` the full m.image content (relation merged in), txn `mxa-<send>-i`.
- Reasons: `upload_rejected:<errcode>`, `upload_failed` (constants in `sender.py`).

## Expected outcome

The bot turns a queued picture into one uploaded file and one m.image (plus its caption), with the bytes gone from Postgres at claim, and every upload failure ends as a named failed status.

## Steps

- Red: the sender tests (ac1, ac2, ac4-ac10) with the fake homeserver from mxc-matrix-media-upload, the tracker test (ac3), the reason constants in `test_readme_lists_every_reason`; run `uv run --frozen pytest tests/test_readme_api.py`: fails (reasons missing); the DB tests error locally.
- Green: the upload step, the claim with `ready`, `_place` for images, the tracker content path, `bot.py`, README and MEMORY.md; run the task's verify; quote the local summary line and the CI run.

## Notes

- DB-backed tests (testcontainers Postgres) need Docker; agent pods have none, so they error here (baseline 2026-10-29: 182 Docker errors) and CI on the PR is the gate for them (recurring retro). Run the verify, quote the local summary line and the CI run of the pushed head. Keep each pure helper covered by a non-DB test so the local run has signal.
- Keep the m.image content builder a pure function with a non-DB test in `tests/test_sender.py` so the local run has signal.
- The upload happens outside the claim transaction and holds no pool connection while it waits on Synapse (retro: `Sender._claim` connection hold).
- Settle is unchanged: the first row by id is the picture, so the send's `event_id` is the picture's and `reply_to: s<n>` quotes it.
- Shared file with immediate-message-delivery-w (`tracker.py`): read it as merged on main first.

- 2026-10-29 amended: interrogate 2026-10-29 act on 1 and 3 (and Consider folded into 1)
