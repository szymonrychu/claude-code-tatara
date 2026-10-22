---
title: Update safety
status: in-progress
repo: workbench
value: "A template update never deletes a user's local notes and only merges from the source the user named"
files: [scripts/init_engine/update.py, scripts/tests/init_engine/test_update_safety.py, plugins/workbench/skills/template-update/SKILL.md, plugins/workbench/skills/template-update/tests/test_template_update_skill.py]
verify: "pytest scripts/tests/init_engine/test_update_safety.py plugins/workbench/skills/template-update/tests/test_template_update_skill.py -q && ruff check scripts plugins/workbench/skills/template-update"
depends_on: [e2e-template-update, template-update-skill, docs-update-flow]
owns: []
uses: []
model: opus
estimate: ""
actual: ""
review: ""
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/template-update-skill-and-in--update-safety
branch: template-update-skill-and-in--update-safety
verified_head: ""
run: ""
provides: []
---

# Update safety

## Requirement

Security review findings (2026-10-22), confirmed by the orchestrator:
1. HIGH: update.py:34-44 restore_owned runs shutil.rmtree / unlink on every INSTANCE_OWNED path, including docs/research and docs/handoffs, which the template gitignores; preflight uses `git status --porcelain`, which hides ignored files, so a user's local research and handoff notes are deleted by an update and cannot be restored by the abort path.
2. MEDIUM: update.py:28-30 fetch_template ignores --url when a `template` remote already exists.
3. LOW: --branch and --base reach git as arguments with no check for a leading `-`.
4. MEDIUM: the update runs the merged template's refresh and lint scripts before commit, so a non-default --url runs that source's code.

Deliver:
- restore_owned only removes what the merge staged: for each owned path, the paths tracked in the index after the merge are removed from the index and the worktree and HEAD's version is restored; any file on disk under an owned path that HEAD does not track and the merge did not stage (for example a gitignored note in docs/research or docs/handoffs) is left untouched. init's clear_template_history is unchanged.
- When a `template` remote exists and --url is given explicitly with a different URL, the update refuses (exit 1, nothing changed) and prints both URLs and `git remote set-url template <url>`. Every run prints `template: <url> <branch> <commit>` before merging.
- A --branch or --base value starting with `-` is refused (exit 1, nothing changed).
- template-update SKILL.md: before running with a --url other than the default template URL, the skill shows the URL and asks the user to confirm, because the update runs that template's refresh and lint scripts.

## Acceptance conditions

- AC1: a gitignored file under docs/research and one under docs/handoffs survive a successful update and an aborted one [evidence: test:scripts/tests/init_engine/test_update_safety.py::test_update_keeps_ignored_owned_files]
- AC2: an explicit --url differing from an existing template remote is refused with nothing changed [evidence: test:scripts/tests/init_engine/test_update_safety.py::test_update_refuses_url_mismatch_with_template_remote]
- AC3: --branch -x and --base -x are refused with nothing changed [evidence: test:scripts/tests/init_engine/test_update_safety.py::test_update_refuses_option_like_branch_and_base]
- AC4: the output names the template url, branch and commit [evidence: test:scripts/tests/init_engine/test_update_safety.py::test_update_prints_source]
- AC5: SKILL.md tells the agent to confirm a non-default --url with the user before running [evidence: test:plugins/workbench/skills/template-update/tests/test_template_update_skill.py::test_skill_confirms_non_default_url]

## Files

- `scripts/init_engine/update.py`
- `scripts/tests/init_engine/test_update_safety.py`
- `plugins/workbench/skills/template-update/SKILL.md`
- `plugins/workbench/skills/template-update/tests/test_template_update_skill.py`

## Interfaces

- `update.restore_owned(root)` keeps its signature.
- CLI flags unchanged; new refusals exit 1 like the existing ones.

## Expected outcome

Updating from the template cannot delete local untracked or ignored notes, cannot silently fetch from a different source than requested, and asks before running code from a non-default template.

## Steps

1. Write test_update_safety.py (reuse init_helpers fixtures) and the skill test; see them fail.
2. Restrict restore_owned to staged paths; add the url, branch and base checks and the source line; update SKILL.md.
3. Run the verify command.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
