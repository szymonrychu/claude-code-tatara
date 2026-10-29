---
title: wrapper slash js whitespace
status: todo
repo: claude-code-wrapper
value: "slash text claude would run as a command (JS whitespace, invisible characters, ESC, probe) can never be typed into the session as a turn or probe"
files: [src/claude_code_wrapper/session.py, README.md, MEMORY.md, tests/test_session_turns.py, tests/test_api_turns.py]
verify: "uv run pytest tests/test_session_turns.py tests/test_api_turns.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check ."
depends_on: [wrapper-release-0-4-0]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 8
expected_tokens: 996161
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# wrapper slash js whitespace

## Requirement

User decision F1 (2026-10-29), verbatim: "F1 (security): both slash parsers adopt claude's JS whitespace set and skip invisible Cc/Cf characters as the architect specifies, including the ESC hole and the Session.probe guard; wrapper release v0.4.1 (tag approved by the user and mx-34 #432; the orchestrator session pushes it after merge) and an orchestrator pin to it; amend D2."

Architect brief (`/workdir/workdir/.scratchpad/slash-fix-design.md`), verbatim:

"F1: claude 2.1.304 (binary `/usr/local/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe`) parses slash text like this:
- `Kb`: `t.trim()`, then checks the text starts with `/`.
- `hIe`: the name ends at the first `search(/\s/)` and the args are `.trim()`'d.
- Command lookup is an exact, case-sensitive match on name or alias.

Our two parsers split only at space, tab and newline, so claude runs `/exit` and `/login` texts that we class as prose. A second hole: `pty_proc.paste_bytes` deletes ESC before typing, so `"/ex\x1bit"` and `"\x1b/exit"` also reach claude as `/exit`. A third: `Session.probe` pastes client text with no guard at all, so a probe text of `/exit` runs."

"**F1: exact character rules (identical code in both repos)**
- **Whitespace (W):** exactly JS `\s`, which is the same set as JS `trim`. Checked under node v24: U+0009-000D, 0020, 00A0, 1680, 2000-200A, 2028, 2029, 202F, 205F, 3000, FEFF. Python's `isspace` differs: it adds U+001C-001F and U+0085, and it lacks U+FEFF.
- **Ignorable (D):** every other character in Unicode categories Cc or Cf. This includes ESC, NUL, DEL, C1, U+001C-001F, U+0085, zero-width and bidi characters. In the leading run and inside the name these are deleted before classifying.
- **Parse steps:**
  1. Remove the run marker.
  2. Skip leading W and D characters.
  3. Require `/`.
  4. The name runs to the first W character, with D characters dropped from it.
  5. The args are the rest, stripped of W only.
  6. The existing name regex applies unchanged.
- **Python's extra stripping must change:** stop using `lstrip()`, `strip()` and `\s` everywhere in the parser. U+001C-001F are still skipped when leading, but they no longer split the name.
- This leans toward calling more text a command, which design D2 already treats as the safe direction. The orchestrator then sends the cleaned name.
- Normalising in the orchestrator alone is not enough: direct wrapper clients, the initial prompt and the probe all bypass it."

"1. `wrapper-slash-js-whitespace` (claude-code-wrapper)
   - Files: `session.py` (`slash_command`, plus the same guard in `probe`), `tests/test_session_turns.py`, `tests/test_api_turns.py`.
   - Tests: extend `test_slash_rule_matches_claude_parser` and `test_slash_rule_leaves_paths_and_prose`. Add `test_slash_whitespace_set_is_js_whitespace`, `test_no_whitespace_or_invisible_char_hides_a_slash_command` (loops over every Zs/Zl/Zp/Cc/Cf code point as a leading character and as the separator), and `test_probe_refuses_slash_text` (422 `slash_command`)."

The case table, verbatim from the architect's orchestrator task (both repos share it): "New cases: `"/exit x"`, `"/clear\x0bx"`, `"/login\rx"`, `"﻿/login"`, `"/exit　"`, `"\x1b/exit"`, `"/ex\x1bit"`, `"/ex​it"`, `"\x1c/exit"`, `"/exit\x1cx"` giving `("exitx","")`. Prose stays prose: `"x /exit"`, `"/etc/hosts x"`."

Design D2 (amended 2026-10-29) names the JS whitespace set and the ignorable characters; design D3 keeps every origin refused.

Scope (claude-code-wrapper, branch from origin `main` e946288, which carries v0.4.0): `src/claude_code_wrapper/session.py` (`slash_command` per the parse steps; `Session.probe` raises `TurnRejected("slash_command")` for slash text before anything is pasted, so `POST /v1/sessions/{id}/probe` answers 422 `slash_command` and counts the probe `rejected`), `tests/test_session_turns.py`, `tests/test_api_turns.py`, README.md (the slash rule at "Slash commands" names the JS whitespace set and the skipped invisible characters; the probe endpoint documents 422 `slash_command`), MEMORY.md (the rule and why). `router.py` and `manager.py` already call `slash_command` and need no change.

## Acceptance conditions

- ac1: slash_command keeps the existing table and adds the shared cases: "/exit x" -> ("exit", "x"), "/clear\x0bx" -> ("clear", "x"), "/login\rx" -> ("login", "x"), "﻿/login" -> ("login", ""), "/exit　" -> ("exit", ""), "\x1b/exit" -> ("exit", ""), "/ex\x1bit" -> ("exit", ""), "/ex​it" -> ("exit", ""), "\x1c/exit" -> ("exit", ""), "/exit\x1cx" -> ("exitx", ""); Session.submit refuses each with slash_command and writes nothing (updated) [evidence: test:tests/test_session_turns.py::test_slash_rule_matches_claude_parser]
- ac2: "x /exit" and "/etc/hosts x" join the prose cases: slash_command returns None and each is typed as a turn (updated) [evidence: test:tests/test_session_turns.py::test_slash_rule_leaves_paths_and_prose]
- ac3: exactly U+0009-000D, 0020, 00A0, 1680, 2000-200A, 2028, 2029, 202F, 205F, 3000 and FEFF end the name and are stripped from the args; U+001C-001F and U+0085 neither end the name nor are stripped from the args (new) [evidence: test:tests/test_session_turns.py::test_slash_whitespace_set_is_js_whitespace]
- ac4: for every code point of category Zs, Zl, Zp, Cc and Cf, "<c>/exit" and "/exit<c>x" are classified as a command (never None), with the name the parse steps give (new) [evidence: test:tests/test_session_turns.py::test_no_whitespace_or_invisible_char_hides_a_slash_command]
- ac5: POST /v1/sessions/{id}/probe with text "/exit", "\x1b/exit" or "/exit now" answers 422 slash_command and pastes nothing; a prose probe text is still accepted (new) [evidence: test:tests/test_api_turns.py::test_probe_refuses_slash_text]
- ac6: README names the JS whitespace set and the skipped Cc/Cf characters in the slash rule [evidence: command:grep -q "U+3000" README.md && grep -q "U+FEFF" README.md && grep -qE "\bCf\b" README.md]
- ac7: MEMORY.md records the rule under this epic's tag [evidence: command:grep -E "^- 2026-[0-9-]+ \(slash-commands-from-chat\)" MEMORY.md | grep -q "JS"]
- ac8: the named tests and lint pass [evidence: command:uv run pytest tests/test_session_turns.py tests/test_api_turns.py tests/test_readme_api.py && uv run ruff check . && uv run ruff format --check .]

## Files

- `src/claude_code_wrapper/session.py`
- `README.md`
- `MEMORY.md`
- `tests/test_session_turns.py`
- `tests/test_api_turns.py`

## Interfaces

- `claude_code_wrapper.session.slash_command(text: str) -> tuple[str, str] | None`: unchanged signature; `(name, args)` with the name cleaned of Cc/Cf characters and the args stripped of JS whitespace only.
- `Session.probe(text)`: raises `TurnRejected("slash_command")` when `slash_command(text)` is not None, before anything is pasted; `POST /v1/sessions/{id}/probe` maps it to 422 `slash_command` (the existing `_REJECT_STATUS` entry) and counts the probe `rejected`.
- One case table, identical to orch-slash-js-whitespace's `tests/test_slash.py`.

## Expected outcome

No text that claude 2.1.304 would run as a slash command (JS whitespace separators, a leading BOM, an ESC or zero-width character inside or before the name) can reach the PTY as a turn, an initial prompt or a probe.

## Steps

- Branch from origin `main` (e946288, v0.4.0) in the wrapper tree.
- Red: extend `SLASH_COMMANDS`/`SLASH_PROSE` and add the three new tests in `tests/test_session_turns.py` and `test_probe_refuses_slash_text` in `tests/test_api_turns.py`; run `uv run pytest tests/test_session_turns.py tests/test_api_turns.py`: the new cases fail (for example "/exit x" returns None).
- Green: rewrite `slash_command` per the parse steps with an explicit whitespace set (a frozenset of the JS code points) and `unicodedata.category(c) in ("Cc", "Cf")` for ignorable characters; guard `probe`; update README and MEMORY.md; run the task's verify. Quote the summary line.

## Notes

- Parse steps, in order: remove the run marker; skip leading W and D; require `/`; name to the first W with D dropped; args = rest stripped of W only; `COMMAND_NAME.fullmatch` unchanged.
- Do not use `str.isspace`, `str.strip()`, `str.lstrip()` or regex `\s` in the parser: Python's set differs from JS (`U+001C-001F`, `U+0085` added, `U+FEFF` missing). The `_RUN_MARKER` regex is part of the parser: spell its whitespace explicitly.
- `pty_proc.paste_bytes` keeps deleting ESC (the todo epic immediate-message-delivery-w owns `pty_proc.py` in wrapper-paste-hygiene); the parser closes the hole by dropping ESC from the name.
- `router.py` (`submit_turn`) and `manager.py` (`_initial_turn`) call `slash_command` already; no change there.
- Do not run `tests/test_manager.py` (`test_shutdown_stops_all` fails locally, a known pre-existing failure).
- Claude's parser evidence: `.scratchpad/slash-fix-design.md` sources (binary offsets 254536412, 267231000, 243756307).
