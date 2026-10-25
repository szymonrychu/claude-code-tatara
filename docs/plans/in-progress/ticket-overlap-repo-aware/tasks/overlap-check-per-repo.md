---
title: overlap check per repo
status: in-progress
repo: workbench
value: independent epics in different repos can run in parallel sessions
files: [plugins/workbench/skills/start-development/scripts/ticket.py]
verify: mise run lint
depends_on: []
model: ""
review: ""
verified_head: ""
points: 2
expected_minutes: 6
expected_tokens: 535073
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# overlap check per repo

## Requirement

In plugins/workbench/skills/start-development/scripts/ticket.py, the in-progress file-overlap check (around line 700: `shared = sorted(set(tfiles) & set(t.meta.get("files", [])))`, and `_counting_overlaps`) compares bare file paths across tasks of different epics, ignoring each task's `repo` field. Two tasks only overlap when they share a repo AND a path. Compare `(repo, path)` pairs: a task's repo is its `repo` frontmatter, and a task without a repo (meta) counts as the superrepo. Keep every other behaviour of the check (own epic and own blockers skipped, only in-progress epics, the `_counting_overlaps` filter) and the message format, with the repo added to it (`file 'x' in repo 'r' is also in task ...`). Add tests in the plugin's existing ticket.py test suite: same path in different repos does not refuse; same repo and path refuses; meta tasks compare against meta tasks only. Update the plugin's docs or reference that describe the overlap rule, if any. Keep the change minimal; this is the user's plugin, follow its conventions and CHANGELOG practice if one exists.

## Acceptance conditions

- AC1: same path in different repos does not refuse a claim or new-task [evidence: command:cd plugins/workbench && python3 -m pytest -q skills/start-development/tests -k overlap]
- AC2: the workbench lint and plugin tests pass [evidence: command:mise run lint && mise run test:plugin]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`

## Interfaces

- ticket.py `run_check(..., repo="")`, `candidates()` yielding `(repo, files, label)`, `check --repo`; overlap message `file 'x' in repo 'r' is also in task ...`.

## Expected outcome

Epics touching same-named files in different repos can be in progress together; same repo and path still refuses.

## Steps

- Red: add the overlap-by-repo tests under plugins/workbench/skills/start-development/tests; `cd plugins/workbench && python3 -m pytest -q skills/start-development/tests -k overlap` fails.
- Green: compare (repo, path) pairs in ticket.py; rerun: passes.
- Run `mise run test:plugin` and `mise run lint`: green.

## Notes

- The ticket.py tests live in plugins/workbench/skills/start-development/tests; `mise run test:plugin` runs one pytest process per skill.

- 2026-10-25 amended: AC1 evidence path corrected to the real test location; template sections filled
