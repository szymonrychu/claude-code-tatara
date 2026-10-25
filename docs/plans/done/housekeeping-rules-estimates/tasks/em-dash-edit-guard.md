---
title: Em dash edit guard
status: done
repo: workbench
value: No agent in any harness can write an em dash into a file
files: [plugins/workbench/hooks/lib/core.py, plugins/workbench/hooks/lib/harness_io.py, plugins/workbench/hooks/lib/apply_patch.py, plugins/workbench/hooks/tests/test_protect_files.py, plugins/workbench/hooks/tests/test_adapter.py, plugins/workbench/skills/start-development/references/hooks.md]
verify: "bash plugins/workbench/scripts/run-tests.sh --only hooks && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run test:scripts && mise run lint"
depends_on: [em-dash-lint]
model: opus
review: ""
verified_head: f45010f
points: 5
expected_minutes: 57
expected_tokens: 3750000
points_actual: 5
actual_minutes: 34
actual_tokens: 1414237
actual_roles: "impl 24, review 11"
actual_role_tokens: "impl 1329221, review 85016"
---

# Em dash edit guard

## Requirement

User requirement (U1, verbatim): "no em dash characters in any code, comment, commit, message, or content of any kind".

Design D4: `core.protect_files` also denies an edit or write whose new content contains U+2014: Write `content`, Edit `new_string`, MultiEdit `edits[].new_string`, NotebookEdit `new_source`, and the added lines (`+` lines and Add File bodies) of a Codex `apply_patch` envelope. The content is read from `event.raw["tool_input"]`; `harness_io.normalize` stores the normalised tool input under that Claude-named key so every harness that already emits protect-files (copilot, codex, gemini, cursor, antigravity) gets the guard with no new allowlist entry. Removing an em dash (it appears only in `old_string` or a `-` patch line) is allowed. The deny reason names U+2014 and tells the agent to use a plain hyphen. protect_files.py stays fail-closed. Design D14: the guard applies in every harness through protect-files.

## Acceptance conditions

- AC1: a Write whose `content` holds U+2014 is denied with exit 2 and a reason naming U+2014 and a plain hyphen [evidence: test:plugins/workbench/hooks/tests/test_protect_files.py::test_em_dash_in_write_content_denied]
- AC2: an Edit whose `new_string` holds U+2014 is denied [evidence: test:plugins/workbench/hooks/tests/test_protect_files.py::test_em_dash_in_edit_new_string_denied]
- AC3: a MultiEdit with U+2014 in any `edits[].new_string` is denied [evidence: test:plugins/workbench/hooks/tests/test_protect_files.py::test_em_dash_in_multiedit_denied]
- AC4: a NotebookEdit whose `new_source` holds U+2014 is denied [evidence: test:plugins/workbench/hooks/tests/test_protect_files.py::test_em_dash_in_notebook_edit_denied]
- AC5: an Edit that removes an em dash (only `old_string` holds it) is allowed [evidence: test:plugins/workbench/hooks/tests/test_protect_files.py::test_removing_an_em_dash_is_allowed]
- AC6: a Codex `apply_patch` adding a line with U+2014 is denied and one removing it is allowed, through the adapter [evidence: test:plugins/workbench/hooks/tests/test_adapter.py::test_apply_patch_em_dash_added_line_denied]
- AC7: a Copilot `toolArgs` JSON string Write with U+2014 is denied through the adapter [evidence: test:plugins/workbench/hooks/tests/test_adapter.py::test_copilot_write_em_dash_denied]
- AC8: references/hooks.md documents the em dash check under protect-files [evidence: command:grep -n "U+2014" plugins/workbench/skills/start-development/references/hooks.md]
- AC9: hooks, start-development and root scripts suites and lint pass [evidence: command:bash plugins/workbench/scripts/run-tests.sh --only hooks && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run test:scripts && mise run lint]

## Files

- `plugins/workbench/hooks/lib/core.py`
- `plugins/workbench/hooks/lib/harness_io.py`
- `plugins/workbench/hooks/lib/apply_patch.py`
- `plugins/workbench/hooks/tests/test_protect_files.py`
- `plugins/workbench/hooks/tests/test_adapter.py`
- `plugins/workbench/skills/start-development/references/hooks.md`

## Interfaces

- `hooks/lib/core.py:protect_files(event) -> Decision` - path check first, then content check.
- `hooks/lib/core.py` new helper: the new content strings of an edit or write from `event.raw["tool_input"]` (Write, Edit, MultiEdit, NotebookEdit, apply_patch).
- `hooks/lib/apply_patch.py` new helper: the added lines of a patch envelope (header recognition as `patch_paths`).
- `hooks/lib/harness_io.py:normalize` - sets `raw["tool_input"]` to the normalised dict from `_tool_input` when the payload has no Claude `tool_input`.

## Expected outcome

No agent in any harness can write an em dash into a file through an edit tool.

## Steps

1. List the files under Files, read them in one pass with hooks/protect_files.py and hooks/tests/harness_payloads.py; write the AC1-AC7 tests and run `pytest hooks/tests/test_protect_files.py hooks/tests/test_adapter.py -q` from plugins/workbench: they fail.
2. Implement the content check, the apply_patch added-lines helper and the normalize key; run the verify once.
3. Commit; leave the tree clean.

## Notes

- Estimate: 5 points.
- Fix-as-ac (brief): NormalizedEvent (core.py:38) carries only paths and command, not content; read `event.raw` tool_input, with a test per tool shape (AC1-AC4, AC6, AC7).
- Fix-as-ac (brief, other harnesses): targets keep explicit hook allowlists (copilot.py:36-40, codex.py:20-21, gemini.py:20-23, cursor.py:17-18, antigravity.py:23-27); riding protect-files means no target change (D14).
- Reuse: harness_io._tool_input / _TOOL_INPUT_KEYS (Copilot sends toolArgs as a JSON string), apply_patch.patch_paths header rules.
- protect_files.py denies on any internal error (exit 2); keep the content check inside `decide` so that holds.
- Test data writes the character as the escape `"\u2014"` (the em dash lint scans tests too).

- 2026-10-24 done

- 2026-10-25 done
