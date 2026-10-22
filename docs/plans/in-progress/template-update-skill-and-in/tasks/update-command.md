---
title: Update command
status: in-progress
repo: workbench
value: "One mise command pulls template tooling into a project without the template's own docs"
files: [scripts/init_engine/update.py, scripts/init_engine/cli.py, scripts/init_engine/gitops.py, mise-tasks/init/update, scripts/tests/init_engine/test_update.py, scripts/tests/init_engine/conftest.py]
verify: "pytest scripts/tests/init_engine/test_update.py scripts/tests/init_engine/test_refresh.py -q && ruff check scripts && shellcheck mise-tasks/init/update"
depends_on: [instance-owned-paths]
owns: [init-update-command]
uses: [instance-owned-paths]
model: sonnet
estimate: 10
actual: ""
review: full
worktree: /Users/szymonri/Documents/workbench/.claude/worktrees/template-update-skill-and-in--update-command
branch: template-update-skill-and-in--update-command
verified_head: ""
run: ""
provides: []
---

# Update command

## Requirement

Add the engine command `update` and the mise task `init:update` for the clean, shared-history path (design D3, D6).

- `scripts/init_engine/update.py` holds the logic; `cli.py` adds subcommand `update` with `--url` (used only when the `template` remote is missing; default `gitops.DEFAULT_TEMPLATE_URL = "https://github.com/szymonrychu/workbench"`, defined next to `TEMPLATE_URL_RE`) and `--branch` (default `main`). New `mise-tasks/init/update` mirrors `mise-tasks/init/refresh` and execs `python3 scripts/init_engine/cli.py update "$@"`.
- Preflight, before any change: refuse (exit 1, `refused: ...` on stderr) when AGENTS.md still has the uninitialised block (same check as `cmd_refresh`, `project_files.UNINIT_RE`), when `git status --porcelain` is non-empty (tracked changes or untracked files; list the paths), or when a merge is in progress.
- Remote: an existing `template` remote is used as is; a missing one is added with `--url` or the default. Fetch `template <branch>` and resolve the commit sha.
- When the template commit is already an ancestor of HEAD: print `up to date with template/<branch> <12-char sha>`, exit 0, no commit.
- Otherwise `git merge --no-commit --no-ff <sha>`; then for every `owned.INSTANCE_OWNED` path: remove it from index and worktree, and restore the HEAD version when HEAD tracks it (template-added files under owned dirs are dropped, modify/delete conflicts resolve to the project side). Then run the merged tree's `python3 scripts/init_engine/cli.py refresh` as a subprocess, passing the MEMORY.md event `template update <12-char sha>` (add a hidden `--event` to `refresh` that reaches `project_files.write_all(event=...)`).
- Commit with `git add -A` and `git commit`: subject `chore(workbench): template update <12-char sha>`, body trailer `Template-Commit: <full sha>`; HEAD^2 is the template commit; `git status --porcelain` is empty afterwards. Print the commit line.
- Lint gate (design D7): after the refresh and before the commit, run the lint command (default `mise run lint`; hidden `--lint-command <cmd>` on `update`, help suppressed like `--user-settings`, run through the shell from the workbench root); commit only on exit 0. Conflict handling beyond owned paths and the failure-abort paths are update-conflicts-and-abort's; this task refuses (exit 1) on a non-zero lint or refresh after `git merge --abort`.

## Acceptance conditions

- AC1: update refuses an uninitialised workbench with exit 1 and changes nothing [evidence: test:scripts/tests/init_engine/test_update.py::test_update_refuses_uninitialised]
- AC2: update refuses a dirty tree (a modified tracked file, and an untracked file) with exit 1, lists the paths and changes nothing [evidence: test:scripts/tests/init_engine/test_update.py::test_update_refuses_dirty_tree]
- AC3: a missing template remote is added with the default URL, and with --url when given [evidence: test:scripts/tests/init_engine/test_update.py::test_update_adds_default_template_remote]
- AC4: an existing template remote keeps its URL [evidence: test:scripts/tests/init_engine/test_update.py::test_update_keeps_existing_template_remote]
- AC5: after update the template plugin change is present, and git ls-files shows no template epic, research file or contracts.json, MEMORY.md has no template entry, the project's own epic is unchanged [evidence: test:scripts/tests/init_engine/test_update.py::test_update_takes_tooling_drops_owned_paths]
- AC6: update ends in one merge commit with subject chore(workbench): template update <sha>, HEAD^2 the template commit, the Template-Commit trailer, a MEMORY.md template update line, and a clean status [evidence: test:scripts/tests/init_engine/test_update.py::test_update_one_commit_records_template_commit]
- AC7: an update with nothing new prints up to date, exits 0 and makes no commit [evidence: test:scripts/tests/init_engine/test_update.py::test_update_up_to_date_is_noop]
- AC8: mise-tasks/init/update execs the engine update subcommand [evidence: test:scripts/tests/init_engine/test_update.py::test_mise_task_runs_engine_update]
- AC9: the update tests, root lint and shellcheck pass [evidence: command:pytest scripts/tests/init_engine/test_update.py scripts/tests/init_engine/test_refresh.py -q && ruff check scripts && shellcheck mise-tasks/init/update]

## Files

- `scripts/init_engine/update.py`
- `scripts/init_engine/cli.py`
- `scripts/init_engine/gitops.py`
- `mise-tasks/init/update`
- `scripts/tests/init_engine/test_update.py`
- `scripts/tests/init_engine/conftest.py`

## Interfaces

`update.update(root: Path, url: str | None, branch: str) -> int`; exit codes 0 ok or up to date, 1 refusal, 2 usage. `gitops.DEFAULT_TEMPLATE_URL`. These are the `init-update-command` contract consumed by later tasks.

## Expected outcome

`mise run init:update` in a clean, initialised project with shared template history ends in one merge commit `chore(workbench): template update <sha>` that carries the template's tooling and none of its owned docs; refusals change nothing.

## Steps

Write `scripts/tests/init_engine/test_update.py` first. Fixture: add `upstream_pair` to `scripts/tests/init_engine/conftest.py` (later update tests reuse it): take the `workbench` fixture, `git init` and commit it as the template, clone it to `<tmp>/upstream`, run `new` in the workbench, then change upstream (a plugin file, a new epic under `docs/plans/done/x/README.md`, a MEMORY.md line, a modified `docs/plans/contracts.json`, a force-added `docs/research/b.md`) and commit. Run `pytest scripts/tests/init_engine/test_update.py -q`; expect failures on the missing subcommand. Implement until green.

## Notes

The default-URL test maps the default URL to the local upstream with `GIT_CONFIG_COUNT`/`url.<upstream>.insteadOf=https://github.com/szymonrychu/workbench`, so no network is used. The unit fixture stubs `scripts/harness/setup.py`, so refresh runs offline. Unit tests pass `--lint-command true`; the e2e test exercises the real `mise run lint`. Retirement assertions use `git ls-files`.
