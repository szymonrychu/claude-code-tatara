---
title: wrapper midturn probe
status: todo
repo: claude-code-wrapper
value: "the wrapper's mid-turn delivery rests on what Claude Code 2.1.304 really does, not on guesses"
files: [docs/claude-midturn-input.md, tests/fixtures/transcripts/midturn-probe.jsonl, tests/test_transcript_midturn.py, MEMORY.md]
verify: "uv run pytest tests/test_transcript_midturn.py tests/test_transcript.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 996161
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper midturn probe

## Requirement

User request (2026-10-28 21:02Z via mx-34 #262), verbatim: "message should get through PTY immediately and let either Claude Code or even agent queue them internally."

Goal G6 (README), verbatim: "how Claude Code 2.1.304 treats input pasted mid-turn is probed on the real binary and recorded before the wrapper relies on it."

Design D11, verbatim: "Task wrapper-midturn-probe runs claude 2.1.304 under a PTY in `/workdir/workdir/.scratchpad/probe-midturn` (existing login, as the slash epic's probes did) and records P1-P12 of the docs brief in `docs/claude-midturn-input.md` of the wrapper, with captured transcript lines as a fixture and a consequences table naming each design decision it confirms or contradicts. A contradiction is a `ticket.py amend` of the named task by the orchestrator before that task starts; nothing downstream guesses."

Docs brief (`/workdir/workdir/.scratchpad/immediate-delivery/brief-docs.md`, "Probes only the real binary (2.1.304) can settle"), verbatim:
"P1. Tool-boundary injection: paste plus CR during a long Bash call. Record the transcript line type (`attachment/queued_command` vs `user` with `promptSource`), its position relative to the tool_result, and whether the marker survives verbatim.
P2. Text-only turn: paste while Claude streams with no tool calls. Check whether it waits for the turn end and whether Stop fires for the first turn before the queued one starts, giving two Stops or one. Check `stop_hook_active` and `last_assistant_message` on each.
P3. UserPromptSubmit for P1 and P2: whether it fires, when (at paste or at injection), with which `prompt` and `prompt_id`.
P4. Multiple pastes queued before a boundary: one combined injection or several? Order? One `queued_command` per paste? Do markers interleave?
P5. Esc with queued input: the transcript interrupt line, then the auto-sent queued prompt. Does the wrapper's second ESC (settle) clear or affect it? Does a bare Esc with empty input plus a second Esc open rewind?
P6. Paste plus CR while a permission dialog is visible (default mode, a tool needing approval): does the CR approve? Does the 2.1.299 hold-back apply to pasted text? Does the paste land in the input box or the dialog? Also test an AskUserQuestion dialog and an MCP elicitation.
P7. Paste during auto-compaction and during a queued or running `/compact`: is the message kept, delivered after, or dropped? Does it go before or after `compact_boundary`? Repeat P1 with a running `/compact` from the commands queue.
P8. Paste while a queued slash command is pending (the wrapper's own command queue): which runs first at the turn end, the queued message or the command?
P9. Paste plus CR when the prompt is collapsed (over 800 characters or over 3 lines): CR timing versus collapse rendering, mid-turn. Does `submit_delay` still suffice?
P10. Invisible-character prompt mid-turn: confirm the CR is swallowed and the text stays in the input, which would then corrupt the next paste.
P11. Background-task wake (the MEMORY.md case): a paste while the wrapper thinks it is ready but Claude was woken. Confirm it is the same mechanism as P1.
P12. The `chat:submit` interrupt case implied by `chat:queueSubmit` wording: find any state where plain Enter interrupts instead of queueing (for example just after submit, before the response starts; compare the 2.1.309 send-now bullet)."

Scope (claude-code-wrapper): `docs/claude-midturn-input.md` (new: the probe record), `tests/fixtures/transcripts/midturn-probe.jsonl` (new: the captured real transcript lines), `tests/test_transcript_midturn.py` (new: pins over the captured lines), `MEMORY.md` (dated entry).

## Acceptance conditions

- ac1: the probe record names claude 2.1.304 and has one `### P<n>` section for each of P1 to P12, each with an `Observed:` and a `Consequence:` line (new) [evidence: command:grep -q '2.1.304' docs/claude-midturn-input.md && for p in P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12; do grep -qE "^### $p( |:|$)" docs/claude-midturn-input.md || exit 1; done && test "$(grep -c '^Observed:' docs/claude-midturn-input.md)" -ge 12 && test "$(grep -c '^Consequence:' docs/claude-midturn-input.md)" -ge 12]
- ac2: the record ends with a `## Design consequences` table with a row for each of D2, D3, D4, D5, D6, D7, D9 and D10, each saying `confirmed` or `contradicted` (new) [evidence: command:grep -q '^## Design consequences' docs/claude-midturn-input.md && for d in D2 D3 D4 D5 D6 D7 D9 D10; do grep -qE "^\| $d .*(confirmed|contradicted)" docs/claude-midturn-input.md || exit 1; done]
- ac3: the fixture holds the real transcript lines captured for P1, P2, P4 and P5, one JSON object per line, with no credential, token or home path in it (new) [evidence: test:tests/test_transcript_midturn.py::test_fixture_lines_are_real_transcript_lines]
- ac4: every captured line whose prompt carries a pasted `<!-- ccw turn: ... -->` marker yields, through `parse_line`, a `UserPrompt` with that turn marker (new) [evidence: test:tests/test_transcript_midturn.py::test_captured_midturn_prompts_carry_the_turn_marker]
- ac5: MEMORY.md has a dated entry with the headline results and the record's path [evidence: command:grep -q 'docs/claude-midturn-input.md' MEMORY.md]
- ac6: the new and the transcript tests and lint pass [evidence: command:uv run pytest tests/test_transcript_midturn.py tests/test_transcript.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `docs/claude-midturn-input.md`
- `tests/fixtures/transcripts/midturn-probe.jsonl`
- `tests/test_transcript_midturn.py`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
