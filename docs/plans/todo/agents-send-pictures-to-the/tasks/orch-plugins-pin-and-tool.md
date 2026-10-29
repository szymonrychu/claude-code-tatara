---
title: orch plugins pin and tool
status: todo
repo: agents-orchestrator
value: agent pods install the plugins release with the picture tool and may call it
files: [src/agents_orchestrator/settings.py, pyproject.toml, uv.lock, README.md, src/agents_orchestrator/k8s/on_start.py, tests/test_settings.py, tests/test_on_start.py, tests/test_agent_chat.py]
verify: "uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py tests/test_agent_chat.py && mise run lint"
depends_on: [plugins-release-images, orch-chat-images-route]
model: opus
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

# orch plugins pin and tool

## Requirement

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

## Acceptance conditions

- ac1: the settings default is <TAG> (updated, named) [evidence: test:tests/test_settings.py::test_defaults]
- ac2: the dev dependency and uv.lock pin the same plugins tag as the settings default [evidence: test:tests/test_images.py::test_plugins_dev_pin_matches_settings_ref]
- ac3: the README documents the <TAG> default and names no older plugins tag [evidence: command:grep -qF '| `ORCH_ANY_MCP_PLUGINS_REF` | `<TAG>` |' README.md && test "$(grep -oE 'plugins release tag \(`v[0-9.]+`\)' README.md | grep -vc '<TAG>')" = 0]
- ac4: every non-trigger session's allow list carries chat_send_image after the other chat tools (CHAT_TOOLS constant updated, named) [evidence: test:tests/test_on_start.py::test_alone_session_tools_entry]
- ac5: sessions started by a trigger service get none of the five chat tools [evidence: test:tests/test_on_start.py::test_trigger_service_sessions_get_no_chat_tools]
- ac6: every allowed tool name is offered by the pinned plugin [evidence: test:tests/test_on_start.py::test_allowed_tools_exist_in_plugin]
- ac7: the released plugin's chat_send_image drives the real image route against the fake wrapper and FakeChat with the same result as a direct call, and a member's call is refused not_leader [evidence: test:tests/test_agent_chat.py::test_chat_send_image_parity]
- ac8: the README names orchestrator_chat_send_image in the Chat section [evidence: command:grep -q 'orchestrator_chat_send_image' README.md]
- ac9: settings, images, on-start and chat suites and lint pass (no database) [evidence: command:uv run --frozen pytest tests/test_settings.py tests/test_images.py tests/test_on_start.py tests/test_agent_chat.py && mise run lint]

## Files

- `src/agents_orchestrator/settings.py`
- `pyproject.toml`
- `uv.lock`
- `README.md`
- `src/agents_orchestrator/k8s/on_start.py`
- `tests/test_settings.py`
- `tests/test_on_start.py`
- `tests/test_agent_chat.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
