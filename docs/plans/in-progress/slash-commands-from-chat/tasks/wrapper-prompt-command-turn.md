---
title: wrapper prompt command turn
status: done
repo: claude-code-wrapper
value: skill and plugin commands sent from the chat run as real turns that complete at their Stop
files: [src/claude_code_wrapper/router.py, src/claude_code_wrapper/session.py, tests/fake_claude/fake_claude.py, README.md, tests/test_command_prompt_turn.py, tests/test_fake_claude_commands.py, MEMORY.md]
verify: "uv run pytest tests/test_command_prompt_turn.py tests/test_fake_claude_commands.py tests/test_command_runner.py tests/test_command_turn_resume.py tests/test_session_turns.py tests/test_stop_gate.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-dialog-commands]
model: opus
review: ""
verified_head: 2fe4eb72ad2f48d3196e5e0acaefd3ec428a3393
points: 5
expected_minutes: 11
expected_tokens: 1858483
points_actual: 5
actual_minutes: 54
actual_tokens: 13233007
actual_roles: "impl 46, review 9"
actual_role_tokens: "impl 12825518, review 407489"
---

# wrapper prompt command turn

## Requirement

Goal G1 (README), verbatim: "Any slash command typed in the chat runs as a Claude Code slash command on the session, at any moment, and the session stays responsive afterwards."

Design D8, verbatim: "`_on_user_prompt_submit` publishes `prompt_submitted` on the SignalBus while a command runs. On that signal the runner calls `Session.adopt_turn(line, origin)` (origin client -> turn origin `client`, agent -> `agent`, idle -> `agent`): a running `TurnRecord` is created and persisted while the slot is already held, `router._last_marker` is set to its turn id (so its Stop is not dropped as stale), `turn_started` and `user_message` are emitted; the command record completes at once with result `turn` and `turn_id`. The turn then ends like any turn (Stop, interrupt, `turn_max_seconds`). Rulings (my call): after a promotion the runner stops; commands still queued stay queued for the promoted turn's Stop. In the agent same-turn path (commands run at a held turn's Stop, D9), a prompt command does not create a new record: the held turn continues as the prompt command's turn (`_commands_turn` cleared, `_last_marker` = the held turn id, result `turn` with that turn id) and no continue prompt is typed. The hold is released through a session API (my call, interrogate item 10; for example `Session.release_commands_hold(record)`), which clears the session's own `_commands_turn` (session.py `continue_turn`, `interrupt`), so an interrupt on the continued turn sends ESC like any running turn instead of ending the record with no ESC. Real-binary probe (user decision): task wrapper-prompt-command-turn settles, in a throwaway dir under `/workdir/workdir/.scratchpad/probe-slash` and recorded in the wrapper's `MEMORY.md`, whether Stop fires after a promoted prompt-command turn and whether plugin commands fire UserPromptSubmit; a result that contradicts the design (or a fact the probe cannot settle, for example with no credentials for a model call) is reported back, not worked around."

Interrogate item 10 (interrogate.md), verbatim: "Held-turn interrupt (B). When the held turn continues as a prompt-command turn, `_commands_turn` is not cleared (session.py:702-703, 1128-1131), so an interrupt ends the record without ESC. Release the hold through a session API; AC that an interrupt on that turn sends ESC."

User decision (probes), verbatim: "the owning tasks (prompt-command turn, command signals) get a requirement to settle by a real-binary probe in a throwaway dir under /workdir/workdir/.scratchpad/probe-slash, recorded in the component MEMORY.md, whether Stop fires after a promoted prompt-command turn, whether plugin commands fire UserPromptSubmit, whether local commands never fire it, and how claude treats path-like prose such as '/workdir/foo is broken'; a probe result that contradicts the design is reported back, not worked around."
This task's probe facts (design D8): whether Stop fires after a promoted prompt-command turn (a project command such as `.claude/commands/hello.md`, as in the first probe) and whether a plugin-namespaced command (for example `/<plugin>:<command>` from a plugin installed in the throwaway config) fires UserPromptSubmit. The probe runs the real binary in a new throwaway directory under `/workdir/workdir/.scratchpad/probe-slash` (never a session workdir, never a test), and each fact is recorded as a dated entry tagged `(slash-commands-from-chat) probe` in the wrapper's `MEMORY.md` (created by wrapper-command-signals), with the observed result and the raw evidence path. A fact the probe cannot settle (the Stop needs a model call; with no credentials it cannot run) is recorded as "not settled: <why>" and returned to the orchestrator as a question. A result that contradicts design D8 is reported back and not worked around (design Assumptions: no UserPromptSubmit for plugin commands means an amend of this task to promote on the echo plus isMeta pair).

Scope (claude-code-wrapper): `router.py` (`_on_user_prompt_submit` publish; `_await_completion` promotion leg; the runner stops after a promotion; the held-turn branch releases the hold through the session API), `session.py` (`adopt_turn(text, origin) -> TurnRecord`: create, persist, arm the turn watch, keep busy; `end_command` then leaves busy to the turn; the hold-release API that clears `_commands_turn` for the continued held turn), `tests/fake_claude/fake_claude.py` (scenario `commands.<name>.prompt: true`: the `<command-message>` user echo, an isMeta user line with the expanded body, UserPromptSubmit, then a normal turn with its steps and Stop), `README.md` (`### Lifecycle`: prompt and skill commands run as real turns), `MEMORY.md` (the probe entries).

Real sample the fake must match: design Research, probed: "/hello world (.claude/commands/hello.md): user line `<command-message>hello</command-message><command-name>/hello</command-name><command-args>world`, then an isMeta user line with the expanded body, then a normal model turn. UserPromptSubmit fired". Stop at the end of that turn is inferred (no credentials in the first probe): the fake pins it (design Assumptions) until this task's probe settles it.

## Acceptance conditions

- ac1: a prompt command (fake prompt true) becomes a turn: turn_started, user_message, the command completes result turn with its turn_id, the Stop completes that turn with its final_text and no "ignoring stale Stop" is logged (new) [evidence: test:tests/test_command_prompt_turn.py::test_prompt_command_promotes_to_turn]
- ac2: the promoted turn is interruptible: POST /interrupt ends it interrupted and the session returns to ready (new) [evidence: test:tests/test_command_prompt_turn.py::test_prompt_command_turn_is_interruptible]
- ac3: a command queued behind a promoted prompt command stays queued and runs only after the promoted turn's Stop; nothing is typed while that turn runs (new) [evidence: test:tests/test_command_prompt_turn.py::test_queued_commands_wait_for_promoted_turn]
- ac4: an agent-origin prompt command run at a held turn's Stop continues that turn: no new turn record, no continue prompt, result turn with the held turn_id (new) [evidence: test:tests/test_command_prompt_turn.py::test_agent_prompt_command_continues_held_turn]
- ac5: an interrupt on that continued held turn sends one ESC (fake-keys.jsonl), ends the turn interrupted and returns the session to ready; the session's commands hold is cleared (new) [evidence: test:tests/test_command_prompt_turn.py::test_interrupt_on_continued_held_turn_sends_escape]
- ac6: a promoted turn after an earlier completed turn is not dropped as stale (second-turn case of the discovery fix-as-ac) (new) [evidence: test:tests/test_command_prompt_turn.py::test_promoted_turn_after_earlier_turn_completes]
- ac7: the fake's prompt scenario writes the echo, the isMeta body, fires UserPromptSubmit, runs the turn and fires Stop (new) [evidence: test:tests/test_fake_claude_commands.py::test_prompt_command_scenario]
- ac8: MEMORY.md records the real-binary probe of this task: whether Stop fires after a promoted prompt-command turn and whether a plugin command fires UserPromptSubmit, each with its observed result or "not settled" [evidence: command:grep -E "^- 2026-[0-9-]+ \(slash-commands-from-chat\) probe" MEMORY.md | grep -qi "promoted" && grep -E "^- 2026-[0-9-]+ \(slash-commands-from-chat\) probe" MEMORY.md | grep -qi "plugin"]
- ac9: targeted suites and lint pass [evidence: command:uv run pytest tests/test_command_prompt_turn.py tests/test_fake_claude_commands.py tests/test_command_runner.py tests/test_command_turn_resume.py tests/test_session_turns.py tests/test_stop_gate.py && uv run ruff check . && uv run ruff format --check .]
- ac10: a command whose name claude sends to the model with no command echo (fake scenario `commands.<name>.prose: true`: a plain user prompt line, UserPromptSubmit, a turn, Stop; the real case `/tmp`, probe 2026-10-29) is promoted on `prompt_submitted` alone, completes result `turn` with its turn_id, the Stop completes the turn, and the session is ready within the fake turn, never at `timeout_seconds` (new) [evidence: test:tests/test_command_prompt_turn.py::test_prose_dispatched_command_promotes_to_turn]

## Files

- `src/claude_code_wrapper/router.py`
- `src/claude_code_wrapper/session.py`
- `tests/fake_claude/fake_claude.py`
- `README.md`
- `tests/test_command_prompt_turn.py`
- `tests/test_fake_claude_commands.py`
- `MEMORY.md`

## Interfaces

- `Session.adopt_turn(text: str, *, origin: Origin) -> TurnRecord` (turns.Origin: client, initial, agent, peer).
- A session API that releases the commands hold of a held turn that continues as a prompt-command turn (for example `Session.release_commands_hold(record: TurnRecord) -> None`), clearing `Session._commands_turn`.
- SignalBus kind `prompt_submitted`; command `result = "turn"`, `CommandRecord.turn_id` = the promoted (or held) turn id.

## Expected outcome

`/init`, a skill or a plugin command sent from the chat runs as a normal turn with assistant rows, turn accounting and the usual bounds, and the session is ready again at its Stop.

## Steps

- Probe first (real binary, throwaway dir under `/workdir/workdir/.scratchpad/probe-slash`, never a test): Stop after a promoted project command, UserPromptSubmit for a plugin command; append the dated `(slash-commands-from-chat) probe` entries to `MEMORY.md` (ac8). A contradiction, or a fact the probe cannot settle (no credentials for the model call), is returned to the orchestrator as a question before going on.
- Red: add `tests/test_command_prompt_turn.py` (ac1-ac6) and the fake test (ac7); run them: they fail (the command times out; the Stop is dropped as stale).
- Green: router, session, fake, README; run the task's verify: passes. Quote the summary line.

## Notes

- Rulings pinned: queued commands stay queued after a promotion (ac3); the held-turn branch (ac4); the hold release and its ESC on interrupt (ac5).
- The busy slot is already held by `begin_command` (idle runner) or `hold_for_commands` (held turn); `adopt_turn` must not set busy twice or emit a second `session_state`.
- If the logged-in contract check later shows no UserPromptSubmit for plugin commands, this task is amended to promote on the echo plus isMeta pair (design Assumptions).
- Depends on wrapper-dialog-commands (sequenced: router.py, session.py and the fake).

- 2026-10-27 amended: interrogate item 10 (release the held-turn hold through a session API so an interrupt sends ESC), user decision on the Noted items (real-binary probe of Stop after a promoted turn and of plugin commands and UserPromptSubmit, recorded in MEMORY.md, contradictions reported back), design D8 revised

- 2026-10-29 amended: fable ruling 2026-10-29 on the wrapper-command-signals probe: claude sends a bare name that exists on disk (/tmp) to the model; D2 rule unchanged, ac8 uses nonexistent, D8 promotion pins the prose case

- 2026-10-29 done
