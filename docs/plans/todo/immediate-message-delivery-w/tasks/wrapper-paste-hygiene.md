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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
