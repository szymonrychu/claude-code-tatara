---
title: mxc matrix media upload
status: todo
repo: agents-matrix-connector
value: the bot can upload a picture to Synapse and read its upload limit
files: [src/agents_matrix_connector/matrix.py, src/agents_matrix_connector/fake_homeserver.py, tests/test_matrix_client.py]
verify: "uv run --frozen pytest tests/test_matrix_client.py && mise run lint"
depends_on: []
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

# mxc matrix media upload

## Requirement

README Goal G2, verbatim: "the Matrix token stays in the bot pod: the bot uploads the bytes and sends m.image; the caption goes as its own text message after the picture; reply_to anchors the picture."

Design D5, verbatim: "`MatrixClient.upload_media(data, mime, filename) -> mxc` on `/_matrix/media/v3`, raw content, the same error, 429 and redaction handling as `_request`; `media_config()` on `/_matrix/client/v1/media/config`." and "Fake homeserver grows the upload and media-config routes."

Constraint, verbatim: "Synapse v1.163.1, authenticated media: upload `POST /_matrix/media/v3/upload`, limit from `GET /_matrix/client/v1/media/config`."

brief-docs fix-as-ac, verbatim: "Upload sends `Content-Type` and `filename`, and the Matrix access token never appears in a URL or log (existing redaction extended to the new calls)."

brief-reuse fix-as-ac, verbatim: "`MatrixClient._request` sends JSON only and is bound to `/_matrix/client/v3` (`matrix.py:14`, `:190`). AC: an upload takes raw bytes with a content type through the same error and 429 handling, against the media prefix." and "The fake homeserver only answers the `/_matrix/client/v3` prefix (`fake_homeserver.py:65`, `:310`). AC: the fake answers the media upload, so tests do not hit a real server."

Scope (agents-matrix-connector):
- `matrix.py`: one request core for JSON and raw bodies (no second client): `upload_media(data, mime, filename) -> str` posts the raw bytes to `/_matrix/media/v3/upload?filename=<filename>` with `Content-Type: <mime>` and returns `content_uri`; `media_config() -> int | None` reads `m.upload.size` from `/_matrix/client/v1/media/config` (None when absent).
- `fake_homeserver.py`: the upload route (stores bytes, mime and filename, answers `mxc://<server>/<id>`, 413 `M_TOO_LARGE` over a configurable limit, `fail_next` covers it) and the media config route (configurable `m.upload.size`, or absent); an accessor for the recorded uploads.

## Acceptance conditions

- ac1: upload_media posts the raw bytes to /_matrix/media/v3/upload with the Content-Type and filename given and returns the content_uri [evidence: test:tests/test_matrix_client.py::test_upload_media]
- ac2: media_config returns m.upload.size from /_matrix/client/v1/media/config, and None when the server omits it [evidence: test:tests/test_matrix_client.py::test_media_config]
- ac3: upload errors map like every other call: 413 to MatrixError with errcode M_TOO_LARGE, 403 to MatrixForbidden, 401 and token errcodes to MatrixAuthError, 429 retried once then MatrixUnavailable, 5xx and transport errors to MatrixUnavailable [evidence: test:tests/test_matrix_client.py::test_upload_media_errors]
- ac4: the access token appears in no URL, log line or error text of either call [evidence: test:tests/test_matrix_client.py::test_media_token_redacted]
- ac5: the fake homeserver answers upload and media config, records each upload's bytes, mime and filename, and refuses an upload over its configured limit with 413 M_TOO_LARGE [evidence: test:tests/test_matrix_client.py::test_fake_media_routes]
- ac6: existing client tests pass unedited and lint passes (runs locally, no database) [evidence: command:uv run --frozen pytest tests/test_matrix_client.py && mise run lint]

## Files

- `src/agents_matrix_connector/matrix.py`
- `src/agents_matrix_connector/fake_homeserver.py`
- `tests/test_matrix_client.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
