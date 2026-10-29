---
title: plugin chat send image
status: todo
repo: any-mcp-tatara-plugins
value: agents get a tool that sends a picture from their workspace to their chat room
files: [orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py, orchestration/orchestrator/README.md, orchestration/orchestrator/tests/test_orchestrator_plugin.py]
verify: "uv run --frozen pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py tests/test_nomenclature.py && mise run lint"
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 545296
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# plugin chat send image

## Requirement

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

## Acceptance conditions

- ac1: the plugin lists orchestrator_chat_send_image beside every existing tool, with hive true and false [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_send_image_listed]
- ac2: calling it sends POST /agent/v1/chat/images with exactly the arguments given as the JSON body ({path}, plus caption, room and reply_to when given), the bearer token and X-Orch-Session, and returns the server JSON [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_send_image_calls_agent_route]
- ac3: an error answer becomes a tool error carrying the code and HTTP status, token redacted, for 400 invalid_path, 404 not_found, 413 image_too_large, 422 unsupported_image, 429 rate_limited, 403 trigger_session, 403 not_leader and 503 chat_unavailable [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_send_image_errors_surface_code]
- ac4: the description says Leader only; a file path in the session workspace (absolute under the workdir or relative); no URLs (fetch the picture with your own tools and save it first); jpeg, png, gif or webp judged by content; at most 8,000,000 bytes; at most 5 pictures a minute; the caption goes as its own message after the picture; reply_to anchors the picture and takes m<n> or s<n>; asynchronous, answers s<n>, read the outcome with orchestrator_chat_status [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_send_image_description]
- ac5: the chat_status description names the kinds message, reaction and image [evidence: test:orchestration/orchestrator/tests/test_orchestrator_plugin.py::test_chat_descriptions]
- ac6: the plugin README lists the tool and its route [evidence: command:grep -qF '`orchestrator_chat_send_image(path, caption?, room?, reply_to?)` | `POST /agent/v1/chat/images`' orchestration/orchestrator/README.md]
- ac7: the plugin tests, repo tests and lint pass [evidence: command:uv run --frozen pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py tests/test_repo.py tests/test_nomenclature.py && mise run lint]

## Files

- `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`
- `orchestration/orchestrator/README.md`
- `orchestration/orchestrator/tests/test_orchestrator_plugin.py`

## Interfaces

- `any_mcp_tatara_orchestrator.OrchestratorPlugin.load_tools`: `spec("chat_send_image", "POST", "/chat/images", _schema({"path": ..., "caption": ..., "room": ..., "reply_to": ...}, ["path"]), "*")`.
- Contract with agents-orchestrator `POST /agent/v1/chat/images` (task orch-chat-images-route): body `{path, caption?, room?, reply_to?}`, 202 `{id: "s<n>", status, path}` passed through from the connector.

## Expected outcome

The orchestrator plugin offers `orchestrator_chat_send_image`; an agent that sees it knows what it accepts and refuses before calling it.

## Steps

- Read `__init__.py`, the plugin README and `test_orchestrator_plugin.py` as merged on main (three epics touched them before this one).
- Red: add `test_chat_send_image_listed`, `test_chat_send_image_calls_agent_route`, `test_chat_send_image_errors_surface_code`, `test_chat_send_image_description`, the image kind assertion in `test_chat_descriptions`, and the new name in the tool-count set; run `uv run --frozen pytest orchestration/orchestrator/tests/test_orchestrator_plugin.py`: the new tests fail (unknown tool).
- Green: the tool spec, its description, the chat_status wording, the README row and count; run the task's verify: passes. Quote the summary line.

## Notes

- Copy the shape of `chat_send` (HttpBinding, `body="*"`, `_schema`); the tool stays declarative (design D2 rejected an agent-side handler).
- The description text lives in `_descriptions()`; keep the hive prefix rule (`test_descriptions_from_config`, `test_handover_threshold_hint`) intact.
- Shared file with slash-commands-from-chat, hive-decoupling and immediate-message-delivery-w: build on their merged tools.
