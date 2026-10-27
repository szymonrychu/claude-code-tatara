---
title: wrapper prompt command turn
status: todo
repo: claude-code-wrapper
value: skill and plugin commands sent from the chat run as real turns that complete at their Stop
files: [src/claude_code_wrapper/router.py, src/claude_code_wrapper/session.py, tests/fake_claude/fake_claude.py, README.md, tests/test_command_prompt_turn.py, tests/test_fake_claude_commands.py]
verify: "uv run pytest tests/test_command_prompt_turn.py tests/test_fake_claude_commands.py tests/test_command_runner.py tests/test_command_turn_resume.py tests/test_session_turns.py tests/test_stop_gate.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-dialog-commands]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1858483
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper prompt command turn

## Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."

Design D8, verbatim: "`_on_user_prompt_submit` publishes `prompt_submitted` on the SignalBus while a command runs. On that signal the runner calls `Session.adopt_turn(line, origin)` (origin client -> turn origin `client`, agent -> `agent`, idle -> `agent`): a running `TurnRecord` is created and persisted while the slot is already held, `router._last_marker` is set to its turn id (so its Stop is not dropped as stale), `turn_started` and `user_message` are emitted; the command record completes at once with result `turn` and `turn_id`. The turn then ends like any turn (Stop, interrupt, `turn_max_seconds`). Rulings (my call): after a promotion the runner stops; commands still queued stay queued for the promoted turn's Stop. In the agent same-turn path (commands run at a held turn's Stop, D9), a prompt command does not create a new record: the held turn continues as the prompt command's turn (`_commands_turn` cleared, `_last_marker` = the held turn id, result `turn` with that turn id) and no continue prompt is typed."

Scope (claude-code-wrapper): `router.py` (`_on_user_prompt_submit` publish; `_await_completion` promotion leg; the runner stops after a promotion; the held-turn branch), `session.py` (`adopt_turn(text, origin) -> TurnRecord`: create, persist, arm the turn watch, keep busy; `end_command` then leaves busy to the turn), `tests/fake_claude/fake_claude.py` (scenario `commands.<name>.prompt: true`: the `<command-message>` user echo, an isMeta user line with the expanded body, UserPromptSubmit, then a normal turn with its steps and Stop), `README.md` (`### Lifecycle`: prompt and skill commands run as real turns).

Real sample the fake must match: design Research, probed: "/hello world (.claude/commands/hello.md): user line `<command-message>hello</command-message><command-name>/hello</command-name><command-args>world`, then an isMeta user line with the expanded body, then a normal model turn. UserPromptSubmit fired". Stop at the end of that turn is inferred (no credentials in the probe): the fake pins it (design Assumptions).

## Acceptance conditions

- ac1: a prompt command (fake prompt true) becomes a turn: turn_started, user_message, the command completes result turn with its turn_id, the Stop completes that turn with its final_text and no "ignoring stale Stop" is logged (new) [evidence: test:tests/test_command_prompt_turn.py::test_prompt_command_promotes_to_turn]
- ac2: the promoted turn is interruptible: POST /interrupt ends it interrupted and the session returns to ready (new) [evidence: test:tests/test_command_prompt_turn.py::test_prompt_command_turn_is_interruptible]
- ac3: a command queued behind a promoted prompt command stays queued and runs only after the promoted turn's Stop; nothing is typed while that turn runs (new) [evidence: test:tests/test_command_prompt_turn.py::test_queued_commands_wait_for_promoted_turn]
- ac4: an agent-origin prompt command run at a held turn's Stop continues that turn: no new turn record, no continue prompt, result turn with the held turn_id (new) [evidence: test:tests/test_command_prompt_turn.py::test_agent_prompt_command_continues_held_turn]
- ac5: a promoted turn after an earlier completed turn is not dropped as stale (second-turn case of the discovery fix-as-ac) (new) [evidence: test:tests/test_command_prompt_turn.py::test_promoted_turn_after_earlier_turn_completes]
- ac6: the fake's prompt scenario writes the echo, the isMeta body, fires UserPromptSubmit, runs the turn and fires Stop (new) [evidence: test:tests/test_fake_claude_commands.py::test_prompt_command_scenario]
- ac7: targeted suites and lint pass [evidence: command:uv run pytest tests/test_command_prompt_turn.py tests/test_fake_claude_commands.py tests/test_command_runner.py tests/test_command_turn_resume.py tests/test_session_turns.py tests/test_stop_gate.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/router.py`
- `src/claude_code_wrapper/session.py`
- `tests/fake_claude/fake_claude.py`
- `README.md`
- `tests/test_command_prompt_turn.py`
- `tests/test_fake_claude_commands.py`

## Interfaces

- `Session.adopt_turn(text: str, *, origin: Origin) -> TurnRecord` (turns.Origin: client, initial, agent, peer).
- SignalBus kind `prompt_submitted`; command `result = "turn"`, `CommandRecord.turn_id` = the promoted (or held) turn id.

## Expected outcome

`/init`, a skill or a plugin command sent from the chat runs as a normal turn with assistant rows, turn accounting and the usual bounds, and the session is ready again at its Stop.

## Steps

- Red: add `tests/test_command_prompt_turn.py` (ac1-ac5) and the fake test (ac6); run them: they fail (the command times out; the Stop is dropped as stale).
- Green: router, session, fake, README; run the task's verify: passes. Quote the summary line.

## Notes

- Rulings pinned: queued commands stay queued after a promotion (ac3); the held-turn branch (ac4).
- The busy slot is already held by `begin_command` (idle runner) or `hold_for_commands` (held turn); `adopt_turn` must not set busy twice or emit a second `session_state`.
- If the logged-in contract check later shows no UserPromptSubmit for plugin commands, this task is amended to promote on the echo plus isMeta pair (design Assumptions).
- Depends on wrapper-dialog-commands (sequenced: router.py, session.py and the fake).
