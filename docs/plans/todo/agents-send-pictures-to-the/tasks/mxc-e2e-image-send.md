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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
