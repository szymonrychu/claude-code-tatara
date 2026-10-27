---
title: orch e2e slash command
status: todo
repo: agents-orchestrator
value: "CI proves end to end, on the real agent image, that /reload-plugins from chat keeps the session responsive"
files: [tests/e2e/test_e2e_kind.py]
verify: "uv run --frozen python -m py_compile tests/e2e/test_e2e_kind.py && mise run lint"
depends_on: [orch-render-client-commands]
model: sonnet
review: ""
verified_head: ""
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch e2e slash command

## Requirement

User decision, verbatim: "A regression test must pin the reported case: sending '/reload-plugins' from chat never leaves the session busy (wrapper and orchestrator level)." This kind e2e case proves it against the real agent image.

Interrogate item 12 (interrogate.md), verbatim: "Kind e2e case placed before the render change (A). The e2e job runs on every PR and agents get `client: ["*"]` only in orch-render-client-commands, so the pin PR would be red with 403. Move the e2e case and its AC to orch-render-client-commands."

Design D14, verbatim (the placement part): "Kind e2e placement (my call, interrogate item 12): the e2e job runs on every PR and agents get `client: ["*"]` only from the render change (D11), so an e2e case in the pin PR would be red with 403. The case is its own task orch-e2e-slash-command, right after orch-render-client-commands (a separate task keeps orch-render-client-commands at 8 files); orch-wrapper-pin-0-4-0 no longer touches `tests/e2e/test_e2e_kind.py`."

Scope (agents-orchestrator), moved verbatim from task orch-wrapper-pin-0-4-0: "`tests/e2e/test_e2e_kind.py`: new `test_slash_command_from_chat_keeps_session_responsive`: POST a chat message "/reload-plugins" through the API; the session's events show `command_completed` for reload-plugins; the agent returns idle; a following prose message completes its turn; POST "/exit" fails with error `command_denied`."

Retro proposal (cross-session-messaging-and), verbatim from design Research inputs: "kind e2e allow-list assertions should derive from the shared constant": the case asserts on the wrapper's error code `command_denied`, never on a hard-coded deny list.

Depends on orch-render-client-commands (agents render `client: ["*"]`) and, through it, orch-wrapper-pin-0-4-0 (the agent image runs wrapper 0.4.0).

## Acceptance conditions

- ac1: (CI only, kind) test_slash_command_from_chat_keeps_session_responsive passes against the real agent image: "/reload-plugins" ends command_completed, the agent returns idle, a following prose message completes its turn, "/exit" fails command_denied (new) [evidence: command:mise run test:e2e]
- ac2: the case asserts on the wrapper error code command_denied and names no deny list [evidence: command:grep -q "def test_slash_command_from_chat_keeps_session_responsive" tests/e2e/test_e2e_kind.py && grep -q "command_denied" tests/e2e/test_e2e_kind.py && ! grep -q "DEFAULT_COMMAND_DENY" tests/e2e/test_e2e_kind.py]
- ac3: the module compiles and lint passes [evidence: command:uv run --frozen python -m py_compile tests/e2e/test_e2e_kind.py && mise run lint]

## Files

- `tests/e2e/test_e2e_kind.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
