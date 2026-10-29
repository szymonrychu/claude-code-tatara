---
title: wrapper midturn probe
status: todo
repo: claude-code-wrapper
value: "the wrapper's mid-turn delivery rests on what Claude Code 2.1.304 really does, not on guesses"
files: [docs/claude-midturn-input.md, tests/fixtures/transcripts/midturn-probe.jsonl, tests/fixtures/transcripts/midturn-probe-hooks.jsonl, tests/fixtures/screens/midturn-dialogs.txt, tests/test_transcript_midturn.py, MEMORY.md]
verify: "uv run pytest tests/test_transcript_midturn.py tests/test_transcript.py && uv run ruff check . && uv run ruff format --check ."
depends_on: []
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 10
expected_tokens: 1875101
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

Design D11 (gate), verbatim: "Gate (interrogate 6, builder Q4, my call): every other task depends on the probe, directly or through its chain; epic-run stops after it, the orchestrator reads the consequences table (rows D2-D7, D9, D10, D13, D14, D17, D18) and amends before any other task starts. P1, P2, P4 and P5 must be observed, never `not run`; P4 also records input combined across a turn end and across an Esc; P6 captures the real dialog footers, their dismissal output and a key that safely clears unsent input with a dialog open; P7 records how long an end-of-turn auto-compaction with queued input takes; the Stop and UserPromptSubmit payloads are captured beside the transcript lines, so wrapper-merge-stop-gate replays both through the Router."

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

Scope (claude-code-wrapper): `docs/claude-midturn-input.md` (new: the probe record), `tests/fixtures/transcripts/midturn-probe.jsonl` (new: the captured real transcript lines), `tests/fixtures/transcripts/midturn-probe-hooks.jsonl` (new: the captured Stop and UserPromptSubmit payloads), `tests/fixtures/screens/midturn-dialogs.txt` (new: the captured dialog screens and their dismissal), `tests/test_transcript_midturn.py` (new: pins over the captured lines), `MEMORY.md` (dated entry).

## Acceptance conditions

- ac1: the probe record names claude 2.1.304 and has one `### P<n>` section for each of P1 to P12, each with an `Observed:` and a `Consequence:` line (new) [evidence: command:grep -q '2.1.304' docs/claude-midturn-input.md && for p in P1 P2 P3 P4 P5 P6 P7 P8 P9 P10 P11 P12; do grep -qE "^### $p( |:|$)" docs/claude-midturn-input.md || exit 1; done && test "$(grep -c '^Observed:' docs/claude-midturn-input.md)" -ge 12 && test "$(grep -c '^Consequence:' docs/claude-midturn-input.md)" -ge 12]
- ac2: P1, P2, P4 and P5 were observed on the binary: none of their Observed lines says not run (new) [evidence: command:for p in P1 P2 P4 P5; do awk -v p="$p" '$0 ~ "^### "p"([ :]|$)" {f=1; next} /^##/ {f=0} f' docs/claude-midturn-input.md | grep '^Observed:' | grep -qv 'not run' || exit 1; done]
- ac3: the P4 section records input queued across a turn end and across an Esc combined with the next paste; the P6 section records the dismissal output and a clear key (or none found); the P7 section records the duration of an end-of-turn auto-compaction (new) [evidence: command:sec() { awk -v p="$1" '$0 ~ "^### "p"([ :]|$)" {f=1; next} /^##/ {f=0} f' docs/claude-midturn-input.md; }; sec P4 | grep -qi 'turn end' && sec P4 | grep -qi 'esc' && sec P6 | grep -qi 'dismiss' && sec P6 | grep -qi 'clear' && sec P7 | grep -qi 'auto-compact']
- ac4: the record ends with a `## Design consequences` table with a row for each of D2, D3, D4, D5, D6, D7, D9, D10, D13, D14, D17 and D18, each saying `confirmed` or `contradicted` (new) [evidence: command:grep -q '^## Design consequences' docs/claude-midturn-input.md && for d in D2 D3 D4 D5 D6 D7 D9 D10 D13 D14 D17 D18; do grep -qE "^\| $d .*(confirmed|contradicted)" docs/claude-midturn-input.md || exit 1; done]
- ac5: the fixture holds the real transcript lines captured for P1, P2, P4 and P5, one JSON object per line, with no credential, token or home path in it (new) [evidence: test:tests/test_transcript_midturn.py::test_fixture_lines_are_real_transcript_lines]
- ac6: the hook fixture holds the real Stop payloads of P1, P2, P4 and P5 (with stop_hook_active and last_assistant_message) and the UserPromptSubmit payloads seen, in arrival order, redacted (new) [evidence: test:tests/test_transcript_midturn.py::test_hook_fixture_holds_real_stop_payloads]
- ac7: the dialog screen fixture has a block and a dismissed block for each dialog kind P6 opened, or P6 is recorded unsettled and the fixture is empty (new) [evidence: test:tests/test_transcript_midturn.py::test_dialog_fixture_matches_the_p6_record]
- ac8: every captured line whose prompt carries a pasted `<!-- ccw turn: ... -->` marker yields, through `parse_line`, a `UserPrompt` with that turn marker (new) [evidence: test:tests/test_transcript_midturn.py::test_captured_midturn_prompts_carry_the_turn_marker]
- ac9: MEMORY.md has a dated entry with the headline results and the record's path [evidence: command:grep -q 'docs/claude-midturn-input.md' MEMORY.md]
- ac10: the new and the transcript tests and lint pass [evidence: command:uv run pytest tests/test_transcript_midturn.py tests/test_transcript.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `docs/claude-midturn-input.md`
- `tests/fixtures/transcripts/midturn-probe.jsonl`
- `tests/fixtures/transcripts/midturn-probe-hooks.jsonl`
- `tests/fixtures/screens/midturn-dialogs.txt`
- `tests/test_transcript_midturn.py`
- `MEMORY.md`

## Interfaces

- `docs/claude-midturn-input.md`: `# Claude Code mid-turn input (probed on 2.1.304, <date>)`, one `### P1` .. `### P12` section each with `Observed:` (what the screen, transcript and hooks showed, with the captured line ids) and `Consequence:` (what the wrapper must do), then `## Design consequences`: a table `| D<n> | confirmed or contradicted | evidence | task to amend |` for D2, D3, D4, D5, D6, D7, D9, D10, D13, D14, D17 and D18 of design.md (D13, D14, D17, D18 rest on the wrapper's 202 shape and refusal codes).
- `### P4` also records input queued across a turn end (settle bound case) and across an Esc combined with the next paste, with the captured line. `### P6` records the real footers, the screen output when each dialog is dismissed, and a key that clears pasted but unsubmitted input while a dialog is open without answering it (or `none found`). `### P7` records how long an end-of-turn auto-compaction with queued input takes.
- `tests/fixtures/transcripts/midturn-probe-hooks.jsonl`: the Stop and UserPromptSubmit hook payloads of P1, P2, P4 and P5, one JSON object per line with `hook_event_name`, in arrival order, redacted like the transcript fixture.
- `tests/fixtures/screens/midturn-dialogs.txt`: the ANSI-stripped screen text of each dialog P6 opened (permission, AskUserQuestion, MCP elicitation), one block per dialog headed `== <kind> ==`, followed by a `== <kind> dismissed ==` block with the screen after dismissal; empty only when P6 is recorded unsettled.
- Every probe paste uses the design D3 format exactly: `<text>\n\n<!-- ccw turn: <turn id> -->\n<!-- ccw merge: <merge id> -->` (ids such as `turn-probe1`, `m-probe1`), written as one bracketed paste, then CR after the wrapper's `boot.submit_delay_seconds` default, so the fixture carries both markers for task wrapper-merge-marker-parse.
- `tests/fixtures/transcripts/midturn-probe.jsonl`: raw transcript lines copied verbatim from the probe session's JSONL (only redaction of credentials and absolute home paths), at least the prompt-bearing lines of P1, P2, P4 and P5 plus the neighbouring tool_result and assistant lines that show the position.

## Expected outcome

The facts the docs cannot settle (Stop count at a turn end with queued input, injection line shape, UserPromptSubmit, Esc with queued input, dialogs, compaction, collapsed pastes, invisible characters, Enter interrupting) are written down from the real binary, with real transcript lines pinned by tests; the orchestrator can amend wrapper-merge-marker-parse, wrapper-fake-claude-queue, wrapper-paste-hygiene, wrapper-immediate-turn-merge and wrapper-merge-stop-gate from the consequences table before they start.

## Steps

- Read `src/claude_code_wrapper/pty_proc.py` (`paste_bytes`, `send_prompt`), `src/claude_code_wrapper/transcript.py` (`parse_line`, `_attachment_events`), `tests/test_transcript.py`, the docs brief and the slash epic's probe layout (`/workdir/workdir/.scratchpad/probe-slash`) in one pass.
- Set up a throwaway session under `/workdir/workdir/.scratchpad/probe-midturn` (own `CLAUDE_CONFIG_DIR` copy with the existing login, a work dir, a hooks log for UserPromptSubmit and Stop payloads); drive `claude` 2.1.304 through a PTY with the wrapper's paste format. Run P1 to P12; save raw screens and the transcript per probe there.
- Red: write `tests/test_transcript_midturn.py` (every test named in the acceptance conditions) and run `uv run pytest tests/test_transcript_midturn.py`; expect a failure on the missing fixture.
- Copy the captured lines, hook payloads and dialog screens into the fixtures, write the record and the MEMORY entry; rerun the task's verify; expect all passed. Quote the summary line.
- A probe the environment cannot run (for example no MCP elicitation available) is recorded as `Observed: not run (<reason>)` with the consequence `unsettled`, never guessed; report it back as a question. P1, P2, P4 and P5 may not be `not run`: if one cannot run, stop and report it as a blocker.
- After this task epic-run stops: the orchestrator reads the consequences table and amends every contradicted task before any other task starts (design D11).

## Notes

- Never copy a credential, token or `/home/...` path into the repo; redact them in the fixture.
- The tests are characterisation pins over real data: the red step is the missing fixture, the green step is the captured lines; the parser itself is not changed here (0.3.3 already reads `queued_command`).
- A contradiction of the design goes into the consequences table and the report; do not change other tasks' code here.
- `docs/claude-midturn-input.md` is new; the wrapper's `docs/` holds `source-analysis.md` for style.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)

- 2026-10-29 amended: interrogate (panel fable, opus, sonnet; lead verdict .scratchpad/immediate-delivery/interrogate.md): Requirement and acceptance conditions follow the amended design
