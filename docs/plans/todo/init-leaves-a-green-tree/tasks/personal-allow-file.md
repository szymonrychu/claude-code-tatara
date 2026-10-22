---
title: personal allow file
status: todo
repo: workbench
value: "lint:personal accepts a project's own vocabulary without weakening the template"
files: [scripts/check_personal.py, scripts/tests/test_check_personal.py, scripts/tests/init_engine/test_update.py]
verify: "pytest scripts/tests/test_check_personal.py scripts/tests/init_engine/test_update.py -q && mise run lint:personal"
depends_on: []
owns: [personal-allow-local]
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# personal allow file

## Requirement

scripts/check_personal.py also reads scripts/personal-allow.local.json (shape {"allow": [...]}, same entry shape as the shipped denylist allow) when present and appends its entries to the allow list; a missing file changes nothing. The file only ever adds allow entries; it cannot remove patterns or hashes. The template ships no such file and scripts/personal-denylist.json stays byte-identical. template-update never brings or overwrites the file (a test pins this). In the template tree lint:personal still fails on any denylisted term.

## Acceptance conditions

- AC1: a term whose digest is denylisted passes once an allow entry for its path and digest is in personal-allow.local.json [evidence: test:scripts/tests/test_check_personal.py::test_local_allow_file_accepts_project_vocabulary]
- AC2: without the local file the same term still fails, and the local file cannot remove a denylist pattern [evidence: test:scripts/tests/test_check_personal.py::test_local_allow_file_only_adds]
- AC3: the shipped denylist stays hashed-only and the template tree stays clean [evidence: test:scripts/tests/test_check_personal.py::test_shipped_denylist_is_hashed_only]
- AC4: a template update leaves a project's personal-allow.local.json untouched [evidence: test:scripts/tests/init_engine/test_update.py::test_update_keeps_personal_allow_local]

## Files

- `scripts/check_personal.py`
- `scripts/tests/test_check_personal.py`
- `scripts/tests/init_engine/test_update.py`

## Interfaces

check_personal.py: scan() also loads scripts/personal-allow.local.json (`{"allow": [{"path", "pattern"}]}`) when it exists; contract personal-allow-local.

## Expected outcome

With a matching local allow entry lint:personal passes; without it the same term fails; the template tree is unchanged.

## Steps

- Write the failing tests in test_check_personal.py and test_update.py; run them red.
- Extend scan() in scripts/check_personal.py to append local allow entries; run green, then `mise run lint:personal`.

## Notes

Design D1. Reuse the existing allow-entry shape. template-update never brings the file because the template does not ship it; pin that.
