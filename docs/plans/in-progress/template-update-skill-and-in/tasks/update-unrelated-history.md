---
title: Update unrelated history
status: in-progress
repo: workbench
value: "Projects copied from the template, with no shared history, can still take updates"
files: [scripts/init_engine/update.py, scripts/init_engine/cli.py, scripts/tests/init_engine/test_update_unrelated.py]
verify: "pytest scripts/tests/init_engine/test_update.py scripts/tests/init_engine/test_update_conflicts.py scripts/tests/init_engine/test_update_unrelated.py -q && ruff check scripts"
depends_on: [update-conflicts-and-abort]
owns: []
uses: [init-update-command]
model: opus
estimate: 8
actual: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# Update unrelated history

## Requirement

Support projects with no shared history with the template (design D5).

- When `git merge-base HEAD <template sha>` finds nothing and no `--base` is given: change nothing, exit 1, print on stderr `refused: no shared history with template/<branch>`, the candidate base (the newest commit on the fetched `template/<branch>` whose committer date is not newer than the project's oldest root commit; `none` when there is none) and the rerun line `mise run init:update -- --base <candidate>`.
- `--base <sha>` on `update`: refuse (exit 1, nothing changed) unless `<sha>` is a commit and an ancestor of the fetched template commit. Otherwise create `git replace --graft <project root commit> <sha>` (the oldest root when there are several), run the normal update (merge, owned-path restore, generated conflicts, refresh, lint, commit), and delete the replace ref in every outcome (success, refusal, exception), so `git replace -l` is empty afterwards.
- The resulting commit's second parent is the real template commit, so the next update with a newer template commit needs no `--base`.
- `--base` given when a merge base already exists: ignore it with one stdout note `--base ignored: history is shared`.

## Acceptance conditions

- AC1: with no shared history and no --base, update exits 1, changes nothing and prints the candidate base and the --base rerun line [evidence: test:scripts/tests/init_engine/test_update_unrelated.py::test_unrelated_history_refused_with_candidate]
- AC2: with --base the update merges, drops owned paths, HEAD^2 is the template commit and git replace -l is empty [evidence: test:scripts/tests/init_engine/test_update_unrelated.py::test_base_flag_merges_unrelated_history]
- AC3: a --base that is not an ancestor of the template commit is refused with nothing changed and no replace ref left [evidence: test:scripts/tests/init_engine/test_update_unrelated.py::test_base_not_in_template_refused]
- AC4: a later update after a --base update needs no --base [evidence: test:scripts/tests/init_engine/test_update_unrelated.py::test_next_update_needs_no_base]
- AC5: all update test files and root lint pass [evidence: command:pytest scripts/tests/init_engine/test_update.py scripts/tests/init_engine/test_update_conflicts.py scripts/tests/init_engine/test_update_unrelated.py -q && ruff check scripts]

## Files

- `scripts/init_engine/update.py`
- `scripts/init_engine/cli.py`
- `scripts/tests/init_engine/test_update_unrelated.py`

## Interfaces

Adds `--base` to the `init-update-command` contract (`cli.py update --base <sha>`).

## Expected outcome

A project copied from the template without history gets a refusal naming the candidate base; with `--base` it takes the update in one merge commit, no replace ref remains, and later updates need no flag.

## Steps

Write `scripts/tests/init_engine/test_update_unrelated.py` first. Fixture: build the upstream as `upstream_pair` does, then make the project by copying the upstream tree without `.git` (the README "copy it into a new directory" route) and running `new`. Run `pytest scripts/tests/init_engine/test_update_unrelated.py -q`; expect red. Implement until green.

## Notes

`git replace --graft` is honoured by `git merge-base` and `git merge` by default; never set `GIT_NO_REPLACE_OBJECTS`. Clean-state assertions use `git rev-parse HEAD`, `git status --porcelain`, `git replace -l`.
