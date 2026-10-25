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

- AC1: same path in different repos does not refuse a claim or new-task [evidence: command:cd plugins/workbench && python3 -m pytest -q -k overlap]
- AC2: the workbench lint and plugin tests pass [evidence: command:mise run lint]

## Files

- `plugins/workbench/skills/start-development/scripts/ticket.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
