---
title: mxc e2e image send
status: todo
repo: agents-matrix-connector
value: the whole connector picture path is proven end to end against the fake homeserver
files: [tests/e2e/test_e2e_agent.py, tests/e2e/conftest.py]
verify: "uv run --frozen pytest tests/e2e/test_e2e_agent.py && mise run lint"
depends_on: [mxc-images-route, mxc-bot-image-upload, mxc-bridge-error-notices]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 8
expected_tokens: 1003544
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# mxc e2e image send

## Requirement

README Goal G1, verbatim: "an agent sends a picture (jpeg, png, gif or webp, judged by content, at most 8,000,000 bytes) from a file in its session workspace to its chat room through a new tool orchestrator_chat_send_image {path, caption?, room?, reply_to?}; the owner sees it in Messenger through the bridge."

README Goal G2, verbatim: "the Matrix token stays in the bot pod: the bot uploads the bytes and sends m.image; the caption goes as its own text message after the picture; reply_to anchors the picture."

README Goal G4, verbatim: "limits and failures are explicit: unsupported type, too large, missing file and rate (5 pictures a minute per session inside the 20 sends a minute) refuse synchronously with a named error; upload failures and bridge error notices mark the send failed, visible in orchestrator_chat_status."

Design D5, verbatim: "Fake homeserver grows the upload and media-config routes."

Scope (agents-matrix-connector): end-to-end tests through the real console script (migrate, api, bot) against the fake homeserver, as `tests/e2e/test_e2e_agent.py` does for messages: an image send with a caption and a reply, a bridge notice failing it, and an upload the homeserver rejects. Test code only.

## Acceptance conditions

- ac1: POST /chat/v1/images with a png, a caption and reply_to leads to one upload on the fake homeserver with the exact bytes, then one m.image (url the uploaded mxc, info mimetype and size, m.in_reply_to) and then the caption as m.text, and the send ends sent [evidence: test:tests/e2e/test_e2e_agent.py::test_e2e_image_send]
- ac2: a bridge-bot m.notice replying to the m.image turns that send failed with reason "bridge: <body>" [evidence: test:tests/e2e/test_e2e_agent.py::test_e2e_bridge_notice_fails_send]
- ac3: an upload the fake rejects with 413 M_TOO_LARGE ends the send failed upload_rejected:M_TOO_LARGE and no m.image is sent [evidence: test:tests/e2e/test_e2e_agent.py::test_e2e_image_upload_rejected]
- ac4: the e2e agent tests and lint pass (CI: needs Docker) [evidence: command:uv run --frozen pytest tests/e2e/test_e2e_agent.py && mise run lint]

## Files

- `tests/e2e/test_e2e_agent.py`
- `tests/e2e/conftest.py`

## Interfaces

- None new: the agent listener `POST /chat/v1/images`, `GET /chat/v1/messages/{id}` and the fake homeserver's recorded uploads and sent events.

## Expected outcome

The whole connector path for pictures (api, queue, upload, send, bridge notice) is proven together, not only per unit.

## Steps

- Red/green: these are integration tests over code the dependencies built; write them, run `uv run --frozen pytest tests/e2e/test_e2e_agent.py`, and if one fails for a product reason, report it as a discovered gap rather than editing product code here.
- Quote the CI run of the pushed head (the e2e suite needs Postgres).

## Notes

- DB-backed tests (testcontainers Postgres) need Docker; agent pods have none, so they error here (baseline 2026-10-29: 182 Docker errors) and CI on the PR is the gate for them (recurring retro). Run the verify, quote the local summary line and the CI run of the pushed head. Keep each pure helper covered by a non-DB test so the local run has signal.
- Reuse the fixtures in `tests/e2e/conftest.py` (the real console script and the fake homeserver); add an upload-limit or `fail_next` setter only through the fake's existing API from mxc-matrix-media-upload.
