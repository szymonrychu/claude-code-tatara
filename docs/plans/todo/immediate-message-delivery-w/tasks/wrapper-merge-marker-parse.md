---
title: wrapper merge marker parse
status: todo
repo: claude-code-wrapper
value: the wrapper sees which mid-turn message Claude Code actually took
files: [src/claude_code_wrapper/transcript.py, tests/test_transcript.py, tests/test_transcript_midturn.py]
verify: "uv run pytest tests/test_transcript.py tests/test_transcript_midturn.py tests/test_transcript_commands.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-midturn-probe]
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

# wrapper merge marker parse

## Requirement

Goal G3 (README), verbatim: "a message delivered mid-turn never wedges the session: the running turn still ends on its Stop, and the message is linked to the turn that answered it (hop guard and delivery verifier included)."

Design D5 (the parser part), verbatim: "The transcript parser reads `<!-- ccw merge: <id> -->` into `UserPrompt.merge_marker` from every prompt-bearing line: a `user` line, a `queued_command` attachment (wrapper 0.3.3) and a `user` line with `promptSource: "queued"` (docs A10, issue 92478); the probe records which ones 2.1.304 writes. [...] A merge marker never moves `_last_marker` by itself: the turn marker on the same line names the running turn."

Design D3 (the paste format), verbatim: "`<text>\n\n<!-- ccw turn: <running turn id> -->\n<!-- ccw merge: <merge id> -->`"

Scope (claude-code-wrapper): `src/claude_code_wrapper/transcript.py` (`_MERGE_MARKER`, `UserPrompt.merge_marker`, read in `_prompt_events` for every prompt-bearing line), `tests/test_transcript.py`, `tests/test_transcript_midturn.py` (assertions over the probe's captured lines).

## Acceptance conditions

- ac1: a user line whose text ends with the D3 turn and merge markers yields one UserPrompt with turn_marker and merge_marker set (new) [evidence: test:tests/test_transcript.py::test_merge_marker_read_from_user_line]
- ac2: a queued_command attachment whose prompt carries both markers yields both (new) [evidence: test:tests/test_transcript.py::test_merge_marker_read_from_queued_command_attachment]
- ac3: a user line with promptSource queued carrying both markers yields both (new) [evidence: test:tests/test_transcript.py::test_merge_marker_read_from_queued_user_line]
- ac4: a prompt with a turn marker and no merge marker yields merge_marker None; the 0.3.3 attachment pin is unchanged [evidence: test:tests/test_transcript.py::test_queued_command_attachment_yields_the_user_prompt_event]
- ac5: every captured probe line that carries a merge marker yields it, with the turn marker of the same line (new) [evidence: test:tests/test_transcript_midturn.py::test_captured_midturn_prompts_carry_the_merge_marker]
- ac6: the transcript suites and lint pass [evidence: command:uv run pytest tests/test_transcript.py tests/test_transcript_midturn.py tests/test_transcript_commands.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/transcript.py`
- `tests/test_transcript.py`
- `tests/test_transcript_midturn.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
