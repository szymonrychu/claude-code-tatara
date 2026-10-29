---
title: wrapper merge marker parse
status: todo
repo: claude-code-wrapper
value: the wrapper sees which mid-turn message Claude Code actually took
files: [src/claude_code_wrapper/transcript.py, src/claude_code_wrapper/turns.py, tests/test_transcript.py, tests/test_transcript_midturn.py, tests/test_turns.py]
verify: "uv run pytest tests/test_transcript.py tests/test_transcript_midturn.py tests/test_transcript_commands.py tests/test_turns.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-midturn-probe]
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

# wrapper merge marker parse

## Requirement

Goal G3 (README), verbatim: "a message delivered mid-turn never wedges the session: the running turn still ends on its Stop, and the message is linked to the turn that answered it (hop guard and delivery verifier included)."

Design D5 (the record model and the parser part), verbatim: "`TurnRecord.merged: list[MergedPrompt]`, `MergedPrompt {merge_id, origin, metadata, callback_url, pasted_at, absorbed_at}` (persisted with the record, served by `GET /turns/{id}`). The transcript parser reads every `<!-- ccw merge: <id> -->` into `UserPrompt.merge_markers: list[str]` from every prompt-bearing line: a `user` line, a `queued_command` attachment (wrapper 0.3.3) and a `user` line with `promptSource: "queued"` (docs A10, issue 92478); the probe records which ones 2.1.304 writes. `UserPrompt.turn_marker` is the last turn marker of the text, not the first (interrogate 4): a merge left queued after the settle bound or an interrupt and combined with the next turn's paste must not name the old turn, or the new turn's Stop is dropped as stale (the 0.3.3 wedge). The router sets `absorbed_at` once (first sighting) for each listed merge of the running turn, ignores merge ids of any other turn, and emits `turn_merge_absorbed`. A merge marker never moves `_last_marker` by itself: the turn marker on the same line names the running turn."

Design D3 (the paste format), verbatim: "`<text>\n\n<!-- ccw turn: <running turn id> -->\n<!-- ccw merge: <merge id> -->`"

Scope (claude-code-wrapper): `src/claude_code_wrapper/transcript.py` (`_MERGE_MARKER`, `UserPrompt.merge_markers`, the last-turn-marker rule, read in `_prompt_events` for every prompt-bearing line), `src/claude_code_wrapper/turns.py` (`MergedPrompt`, `TurnRecord.merged`, persisted and reloaded), `tests/test_transcript.py`, `tests/test_transcript_midturn.py` (assertions over the probe's captured lines), `tests/test_turns.py`. Test no longer accurate (named): `tests/test_turns.py::test_turn_record_serializes_callback_url_camel_case` asserts the exact dumped field set of `TurnRecord`; it gains `merged`, and this file is changed only for that and the new model test. The router is not touched here (task wrapper-immediate-turn-merge).

## Acceptance conditions

- ac1: a user line whose text ends with the D3 turn and merge markers yields one UserPrompt with turn_marker and merge_markers set (new) [evidence: test:tests/test_transcript.py::test_merge_marker_read_from_user_line]
- ac2: a queued_command attachment whose prompt carries both markers yields both (new) [evidence: test:tests/test_transcript.py::test_merge_marker_read_from_queued_command_attachment]
- ac3: a user line with promptSource queued carrying both markers yields both (new) [evidence: test:tests/test_transcript.py::test_merge_marker_read_from_queued_user_line]
- ac4: a combined prompt holding an older turn's merge (turn marker T1, merge marker m1) followed by a new turn's paste (turn marker T2) yields turn_marker T2 and merge_markers [m1]; two merges of one turn in one prompt yield both ids in text order (new) [evidence: test:tests/test_transcript.py::test_combined_prompt_takes_the_last_turn_marker_and_every_merge_marker]
- ac5: a prompt with a turn marker and no merge marker yields merge_markers empty; the 0.3.3 attachment pin is unchanged [evidence: test:tests/test_transcript.py::test_queued_command_attachment_yields_the_user_prompt_event]
- ac6: every captured probe line that carries merge markers yields all of them, with the last turn marker of the same line (new) [evidence: test:tests/test_transcript_midturn.py::test_captured_midturn_prompts_carry_the_merge_marker]
- ac7: TurnRecord.merged defaults to an empty list, MergedPrompt serialises callbackUrl in camelCase, and a record with merges survives TurnStore put and reload (new) [evidence: test:tests/test_turns.py::test_turn_record_merged_persists_and_reloads]
- ac8: the TurnRecord field-set pin lists merged (no longer accurate: it pins the exact field set) [evidence: test:tests/test_turns.py::test_turn_record_serializes_callback_url_camel_case]
- ac9: the transcript and turn suites and lint pass [evidence: command:uv run pytest tests/test_transcript.py tests/test_transcript_midturn.py tests/test_transcript_commands.py tests/test_turns.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/transcript.py`
- `src/claude_code_wrapper/turns.py`
- `tests/test_transcript.py`
- `tests/test_transcript_midturn.py`
- `tests/test_turns.py`

## Interfaces

- `transcript.py`: `_MERGE_MARKER = re.compile(r"<!--\s*ccw merge:\s*(\S+?)\s*-->")`; `UserPrompt.merge_markers: list[str] = []` (every merge marker, in text order, via `findall`), filled wherever `turn_marker` is filled today (`_prompt_events`), so user lines, `queued_command` attachments and queued user lines all carry it. `UserPrompt.turn_marker` becomes the last `_TURN_MARKER` match of the text instead of the first.
- `turns.py`: `MergedPrompt(BaseModel)`: `merge_id: str`, `origin: Origin`, `metadata: dict`, `callback_url: str | None` (alias `callbackUrl`, serialised camelCase like `TurnRecord.callback_url`), `pasted_at: str`, `absorbed_at: str | None = None`; `TurnRecord.merged: list[MergedPrompt] = []`, persisted by `TurnStore` and reloaded.
- Consumer (task wrapper-immediate-turn-merge): `Router._on_transcript_events` reads `ev.merge_markers`; this task does not touch the router.

## Expected outcome

The wrapper can tell which merged pastes Claude Code took, from any line shape 2.1.304 writes for it, a combined prompt never names a stale turn, and the turn record can carry its merges.

## Steps

- Read `src/claude_code_wrapper/transcript.py`, `src/claude_code_wrapper/turns.py`, `tests/test_transcript.py`, `tests/test_transcript_midturn.py`, `tests/test_turns.py`, `tests/fixtures/transcripts/midturn-probe.jsonl` and `docs/claude-midturn-input.md` (P1, P2, P4) in one pass.
- Red: add the new tests named in the acceptance conditions and add `"merged"` to the field set of `tests/test_turns.py::test_turn_record_serializes_callback_url_camel_case`; run `uv run pytest tests/test_transcript.py tests/test_transcript_midturn.py tests/test_turns.py`; expect the new tests and the field-set pin to fail.
- Green: add the regex, the list field, the last-marker rule and the model; run the task's verify; expect all passed. Quote the summary line.

## Notes

- The `promptSource: "queued"` user line already reaches `_user_events`; check that its prompt text path reaches `_prompt_events` (issue 92478 shape: `{"type": "user", "promptSource": "queued", "message": {"content": ...}}`), and use the probe's captured shape where it differs.
- Redaction keeps applying to the text as today; markers are read from the unredacted text as `turn_marker` is.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: interrogate (panel fable, opus, sonnet; lead verdict .scratchpad/immediate-delivery/interrogate.md): Requirement and acceptance conditions follow the amended design
