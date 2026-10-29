---
title: wrapper paste hygiene
status: todo
repo: claude-code-wrapper
value: a message with a stray invisible character is submitted at once instead of corrupting the next one
files: [src/claude_code_wrapper/pty_proc.py, tests/test_pty_proc.py, README.md]
verify: "uv run pytest tests/test_pty_proc.py --deselect tests/test_pty_proc.py::test_exit_without_eof_still_fires --deselect tests/test_pty_proc.py::test_close_terminates_group_then_kill && uv run ruff check . && uv run ruff format --check ."
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

# wrapper paste hygiene

## Requirement

Design D9, verbatim: "`paste_bytes` removes Unicode tag characters (U+E0000-U+E007F), bidi controls (U+202A-U+202E, U+2066-U+2069) and zero-width spaces (U+200B, U+FEFF) besides ESC, keeping ZWJ and ZWNJ (U+200C, U+200D) and variation selectors. Claude Code removes them itself on Enter, and then "that Enter sends nothing" and the cleaned prompt stays in the input box (docs G3); mid-turn, the next merged paste would be concatenated onto it. Applies to every paste, idle turns included."

Docs brief (Fix-as-AC), verbatim: "Strip invisible Unicode (tag chars, bidi controls, zero-width spaces; keep ZWJ/ZWNJ for Persian/Indic and emoji selectors) before pasting. Otherwise the CR submits nothing and text is left in the input (G3). This applies to idle turns too."

Scope (claude-code-wrapper): `src/claude_code_wrapper/pty_proc.py` (`paste_bytes`), `tests/test_pty_proc.py`, `README.md` (one sentence where turns and pastes are described).

## Acceptance conditions

- ac1: paste_bytes removes every tag character U+E0000-U+E007F, the bidi controls U+202A-U+202E and U+2066-U+2069, U+200B and U+FEFF, and ESC, inside the bracketed paste (new) [evidence: test:tests/test_pty_proc.py::test_paste_bytes_strips_invisible_characters]
- ac2: paste_bytes keeps U+200C, U+200D, variation selectors U+FE00-U+FE0F, an emoji ZWJ sequence, Persian text with ZWNJ and plain text byte for byte (new) [evidence: test:tests/test_pty_proc.py::test_paste_bytes_keeps_joiners_and_variation_selectors]
- ac3: the README says which invisible characters are removed from every pasted prompt and why [evidence: command:grep -q 'U+200B' README.md && grep -q 'U+E0000' README.md]
- ac4: the PTY suite (minus the two PID-1 tests that fail in this container) and lint pass [evidence: command:uv run pytest tests/test_pty_proc.py --deselect tests/test_pty_proc.py::test_exit_without_eof_still_fires --deselect tests/test_pty_proc.py::test_close_terminates_group_then_kill && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/pty_proc.py`
- `tests/test_pty_proc.py`
- `README.md`

## Interfaces

- `pty_proc.paste_bytes(text: str) -> bytes`: unchanged signature; the removed set is a module constant (for example `INVISIBLE = re.compile("[​﻿‪-‮⁦-⁩\U000e0000-\U000e007f]")`) applied with the ESC removal before encoding.
- Every writer that pastes (`send_prompt`, `paste`, probes, continue prompts, merges) goes through `paste_bytes`, so no caller changes.

## Expected outcome

A prompt or message carrying a stray invisible character is submitted by the first CR instead of being left in Claude Code's input box, where it would corrupt the next pasted message.

## Steps

- Read `src/claude_code_wrapper/pty_proc.py`, `tests/test_pty_proc.py`, the README section on turns and `docs/claude-midturn-input.md` (P10) in one pass.
- Red: add the two tests named in the acceptance conditions; run `uv run pytest tests/test_pty_proc.py -k paste_bytes`; expect ac1 to fail.
- Green: extend `paste_bytes` and add the README sentence; run the task's verify; expect all passed. Quote the summary line.

## Notes

- If the probe's P10 recorded that 2.1.304 does not swallow the CR, the stripping still stands (harmless, design D9); say so in the report.
- Keep U+200C and U+200D: they are needed by Persian and Indic text and emoji sequences.
- Before working read the repo's AGENTS.md, MEMORY.md and ROADMAP.md. No em dashes. No backward-compatibility shims. If a verify run fails, save the failing test name and the output tail before any rerun.

- 2026-10-29 amended: planner filled Interfaces, Expected outcome, Steps and Notes before the gate (retro: no empty Steps)
