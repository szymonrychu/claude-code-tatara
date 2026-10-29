---
title: mxc images route
status: todo
repo: agents-matrix-connector
value: "the connector accepts a picture send, refusing bad types, oversize files and floods with named errors"
files: [src/agents_matrix_connector/images.py, src/agents_matrix_connector/api/agent.py, src/agents_matrix_connector/settings.py, README.md, openapi-agent.json, tests/test_images.py, tests/test_api_agent.py, tests/test_settings.py]
verify: "uv run --frozen pytest tests/test_images.py tests/test_api_agent.py tests/test_settings.py tests/test_readme_api.py && mise run lint"
depends_on: [mxc-send-images-schema]
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

# mxc images route

## Requirement

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

## Acceptance conditions

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

## Files

- `src/agents_matrix_connector/images.py`
- `src/agents_matrix_connector/api/agent.py`
- `src/agents_matrix_connector/settings.py`
- `README.md`
- `openapi-agent.json`
- `tests/test_images.py`
- `tests/test_api_agent.py`
- `tests/test_settings.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
