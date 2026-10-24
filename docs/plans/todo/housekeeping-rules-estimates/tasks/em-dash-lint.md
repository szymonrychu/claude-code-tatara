---
title: Em dash lint
status: todo
repo: workbench
value: mise run lint fails on any em dash anywhere in the tracked tree
files: [scripts/check_em_dash.py, mise-tasks/lint/em-dash, scripts/tests/test_check_em_dash.py, scripts/tests/test_agents_md.py]
verify: "mise run test:scripts && mise run lint"
depends_on: []
model: opus
review: ""
verified_head: ""
---

# Em dash lint

## Requirement

User requirement (U1, verbatim): "no em dash characters in any code, comment, commit, message, or content of any kind".

Design D3: a thin entry point `scripts/check_em_dash.py` over `scripts/check_personal.py`'s `_tracked` and `_text` helpers reports `path:line` for every U+2014 in any tracked text file of the repo, with no allow list and no exempt path, and exits 1 on any hit, else 0. `mise-tasks/lint/em-dash` (executable, `#MISE description=...`) runs it, so `mise run lint` picks it up through `lint:*`. The one tracked literal today, in `scripts/tests/test_agents_md.py` (`test_no_personal_or_stale_content`, the banned tuple), becomes the escape `"\u2014"` so the tree passes. Binary files and untracked files are skipped, exactly as check_personal does.

## Acceptance conditions

- AC1: a tracked file containing U+2014 is reported as `path:line` and the checker exits 1; a clean repo exits 0 [evidence: test:scripts/tests/test_check_em_dash.py::test_reports_tracked_em_dash]
- AC2: untracked files and binary files (a NUL in the first 8192 bytes) are not reported [evidence: test:scripts/tests/test_check_em_dash.py::test_ignores_untracked_and_binary]
- AC3: no path is exempt: a hit under `docs/plans/` and under `scripts/init_engine/` is reported [evidence: test:scripts/tests/test_check_em_dash.py::test_no_path_is_exempt]
- AC4: `mise-tasks/lint/em-dash` is executable and runs the checker against the repo root [evidence: test:scripts/tests/test_check_em_dash.py::test_lint_task_runs_checker]
- AC5: the tree is clean: `python3 scripts/check_em_dash.py` exits 0 [evidence: command:python3 scripts/check_em_dash.py]
- AC6: test_agents_md.py still bans the em dash in AGENTS.md, now written as an escape [evidence: test:scripts/tests/test_agents_md.py::test_no_personal_or_stale_content]
- AC7: `mise run lint` passes with the new task included [evidence: command:mise run lint]

## Files

- `scripts/check_em_dash.py`
- `mise-tasks/lint/em-dash`
- `scripts/tests/test_check_em_dash.py`
- `scripts/tests/test_agents_md.py`

## Interfaces

- `scripts/check_em_dash.py`: `scan(root: Path) -> list[str]` (hits as `path:line: em dash`), `main() -> int`, `--root DIR` like check_personal.
- Reuses `scripts/check_personal.py:_tracked` and `:_text`; no new walker.

## Expected outcome

`mise run lint` fails on any tracked U+2014 anywhere in the repo and passes on the current tree.

## Steps

1. List every file under Files, read them all in one pass (and check_personal.py), then write test_check_em_dash.py with a temp git repo fixture; run `pytest scripts/tests/test_check_em_dash.py -q` and watch it fail on the missing module.
2. Add check_em_dash.py and mise-tasks/lint/em-dash; replace the literal in test_agents_md.py with `"\u2014"`; run the verify once.
3. Commit; leave the tree clean.

## Notes

- Estimate: 2 points.
- Reuse (brief): check_personal.py `_tracked` (82), `_text` (89), `scan` (106) - import them, do not copy. Do-not-build: a new tracked-file walker.
- Rejected: a denylist entry in personal-denylist.json (its whole-file allows would exempt docs/plans/** and init_engine).
- Fix-as-ac: the literal em dash at scripts/tests/test_agents_md.py:107 is the only tracked hit (AC5, AC6).
- No allow list: tests that need the character write the escape `\u2014`.
