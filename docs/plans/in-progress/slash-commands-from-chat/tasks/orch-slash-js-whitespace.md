---
title: orch slash js whitespace
status: done
repo: agents-orchestrator
value: "the orchestrator classifies every text claude would run as a command as a command, so none reaches an agent as a turn"
files: [src/agents_orchestrator/slash.py, tests/test_slash.py, README.md]
verify: "uv run --frozen pytest tests/test_slash.py tests/test_readme_api.py && mise run lint"
depends_on: [orch-slash-parser]
model: sonnet
review: ""
verified_head: f681026b0629bfa12e2f80862d3669aba6059f34
points: 2
expected_minutes: 5
expected_tokens: 546295
points_actual: 2
actual_minutes: 3
actual_tokens: 411765
actual_roles: "impl 2, review 2"
actual_role_tokens: "impl 302025, review 109740"
---

# orch slash js whitespace

## Requirement

User decision F1 (2026-10-29), verbatim: "F1 (security): both slash parsers adopt claude's JS whitespace set and skip invisible Cc/Cf characters as the architect specifies, including the ESC hole and the Session.probe guard; wrapper release v0.4.1 (tag approved by the user and mx-34 #432; the orchestrator session pushes it after merge) and an orchestrator pin to it; amend D2."

Architect brief (`/workdir/workdir/.scratchpad/slash-fix-design.md`), verbatim:

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

"2. `orch-slash-js-whitespace` (agents-orchestrator): `slash.py` and `tests/test_slash.py`, with the same case table. Can run in parallel with task 1.
   - New cases: `"/exit x"`, `"/clear\x0bx"`, `"/login\rx"`, `"﻿/login"`, `"/exit　"`, `"\x1b/exit"`, `"/ex\x1bit"`, `"/ex​it"`, `"\x1c/exit"`, `"/exit\x1cx"` giving `("exitx","")`.
   - Prose stays prose: `"x /exit"`, `"/etc/hosts x"`."

Design D2 (amended 2026-10-29) names the set; the orchestrator keeps one case table with the wrapper's (task wrapper-slash-js-whitespace).

Scope (agents-orchestrator, epic branch in `/workdir/workdir/.claude/worktrees/slash-commands-from-chat/agents-orchestrator`): `src/agents_orchestrator/slash.py` (`parse` per the parse steps; the dispatcher already sends `parse`'s name and args, so the cleaned name reaches the wrapper), `tests/test_slash.py`, README.md (the two places that describe slash text, `POST /api/v1/sessions/{id}/messages` and `orchestrator_session_send`, say leading whitespace and invisible characters are skipped and the name ends at the first whitespace character).

## Acceptance conditions

- ac1: parse keeps the existing command table and adds: "/exit x" -> ("exit", "x"), "/clear\x0bx" -> ("clear", "x"), "/login\rx" -> ("login", "x"), "﻿/login" -> ("login", ""), "/exit　" -> ("exit", ""), "\x1b/exit" -> ("exit", ""), "/ex\x1bit" -> ("exit", ""), "/ex​it" -> ("exit", ""), "\x1c/exit" -> ("exit", ""), "/exit\x1cx" -> ("exitx", "") (updated) [evidence: test:tests/test_slash.py::test_parse_slash_commands]
- ac2: "x /exit" and "/etc/hosts x" join the prose cases and return None (updated) [evidence: test:tests/test_slash.py::test_parse_leaves_prose]
- ac3: exactly U+0009-000D, 0020, 00A0, 1680, 2000-200A, 2028, 2029, 202F, 205F, 3000 and FEFF end the name and are stripped from the args; U+001C-001F and U+0085 do not (new) [evidence: test:tests/test_slash.py::test_parse_whitespace_set_is_js_whitespace]
- ac4: for every code point of category Zs, Zl, Zp, Cc and Cf, "<c>/exit" and "/exit<c>x" parse as a command (never None) (new) [evidence: test:tests/test_slash.py::test_no_whitespace_or_invisible_char_hides_a_slash_command]
- ac5: the trailing run marker rule still holds [evidence: test:tests/test_slash.py::test_parse_strips_trailing_run_marker]
- ac6: README's slash text descriptions name the skipped invisible characters [evidence: command:grep -q "invisible" README.md]
- ac7: the Docker-free checks and lint pass [evidence: command:uv run --frozen pytest tests/test_slash.py tests/test_readme_api.py && mise run lint]

## Files

- `src/agents_orchestrator/slash.py`
- `tests/test_slash.py`
- `README.md`

## Interfaces

- `agents_orchestrator.slash.parse(text: str) -> tuple[str, str] | None`: unchanged signature; the name cleaned of Cc/Cf characters, the args stripped of JS whitespace only. The dispatcher sends this name and these args to the wrapper.

## Expected outcome

The orchestrator stores every text claude would run as a command as `kind = 'command'`, with the cleaned name, so none is dispatched as a turn.

## Steps

- Red: add the shared cases and the two new tests to `tests/test_slash.py`; run `uv run --frozen pytest tests/test_slash.py`: the new cases fail.
- Green: rewrite `parse` per the parse steps (explicit JS whitespace set, `unicodedata.category` in Cc/Cf); update README; run the task's verify. Quote the summary line.

## Notes

- Same code shape and the same case table as wrapper-slash-js-whitespace, so the two parsers cannot drift (retro proposal: one shared parity table).
- No `str.strip()`, `str.lstrip()`, `str.isspace` or regex `\s` in the parser, the `_RUN_MARKER` regex included.
- Docker-free: runs in this container. Can run in parallel with the wrapper tasks.

- 2026-10-29 done
