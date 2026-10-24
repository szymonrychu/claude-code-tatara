---
title: Em dash edit guard
status: todo
repo: workbench
value: No agent in any harness can write an em dash into a file
files: [plugins/workbench/hooks/lib/core.py, plugins/workbench/hooks/lib/harness_io.py, plugins/workbench/hooks/lib/apply_patch.py, plugins/workbench/hooks/tests/test_protect_files.py, plugins/workbench/hooks/tests/test_adapter.py, plugins/workbench/skills/start-development/references/hooks.md]
verify: "bash plugins/workbench/scripts/run-tests.sh --only hooks && bash plugins/workbench/scripts/run-tests.sh --only start-development && mise run test:scripts && mise run lint"
depends_on: [em-dash-lint]
model: opus
review: ""
verified_head: ""
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
