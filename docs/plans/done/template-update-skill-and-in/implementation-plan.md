# Template update skill and init docs cleanup implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: Instance owned paths

- Status: done
- Files: `scripts/init_engine/owned.py`, `scripts/init_engine/finalize.py`, `scripts/tests/init_engine/test_finalize.py`
- Verify: `pytest scripts/tests/init_engine/test_finalize.py -q && ruff check scripts`
- Verified head: e0fb748de0937120b442903737d78c5904383dc9

#### Requirement

Move the instance-owned path list into one module and make init's template-history cleanup derive from it (design D1, D2).

- New `scripts/init_engine/owned.py` defines `INSTANCE_OWNED`: an ordered tuple of `(path, kind)` entries, exactly `docs/plans/todo`, `docs/plans/in-progress`, `docs/plans/done` (kind `phase`), `docs/plans/contracts.json`, `docs/plans/index.json`, `docs/plans/facts.md`, `docs/research`, `docs/handoffs` (kind `delete`), `MEMORY.md`, `ROADMAP.md` (kind `rewritten`). It also defines `GENERATED_ON_CONFLICT` for update-conflicts-and-abort (design D4): `AGENTS.md`, `.mise.toml`, `docs/architecture.md`, `LICENSE`, `.claude-plugin/marketplace.json`, and the config-dir `settings.json` and `workbench.json` (resolved through `workbench.config_dir` by the caller). A module docstring says this is the one place these paths are named.
- `finalize.clear_template_history(root)` iterates `INSTANCE_OWNED`: `phase` entries are removed and recreated as an empty dir with `.gitkeep`; `delete` entries are removed (file or dir, missing is fine); `rewritten` entries are left for `project_files.memory_and_roadmap`. No path literal for these entries remains in finalize.py (`PHASES` goes away or is derived from the list).
- Behaviour stays first-init only (`finalize.py` `if first:`); a rerun keeps the project's epics and research (existing `test_rerun_keeps_epics_and_research` stays green).
- `.gitignore` gets no new docs/plans entry (user decision A1).

#### Acceptance conditions

- AC1: after init, git ls-files docs/plans lists only the three phase .gitkeep files and docs/research and docs/handoffs track nothing, with contracts.json and index.json seeded beforehand [evidence: test:scripts/tests/init_engine/test_finalize.py::test_owned_paths_retired_from_tracked_files]
- AC2: clear_template_history follows INSTANCE_OWNED: an extra monkeypatched delete entry is removed and a rewritten entry is left in place [evidence: test:scripts/tests/init_engine/test_finalize.py::test_clear_template_history_derives_from_owned_list]
- AC3: after init MEMORY.md and ROADMAP.md hold no template entry and are the fresh init versions [evidence: test:scripts/tests/init_engine/test_project_files.py::test_docs_reset]
- AC4: owned.py defines INSTANCE_OWNED and GENERATED_ON_CONFLICT [evidence: symbol:scripts/init_engine/owned.py::INSTANCE_OWNED]
- AC5: no new docs/plans entry in .gitignore [evidence: command:! grep -E '^/?docs/plans/(todo|in-progress|done|contracts)' .gitignore]
- AC6: the finalize tests and root lint pass [evidence: command:pytest scripts/tests/init_engine/test_finalize.py -q && ruff check scripts]

#### Files

- `scripts/init_engine/owned.py`
- `scripts/init_engine/finalize.py`
- `scripts/tests/init_engine/test_finalize.py`

#### Interfaces

`owned.INSTANCE_OWNED: tuple[tuple[str, str], ...]`, `owned.GENERATED_ON_CONFLICT: tuple[str, ...]` (config-dir entries marked so the caller can resolve them; builder's choice of representation). `finalize.clear_template_history(root: Path) -> None` keeps its signature.

#### Expected outcome

A freshly initialised workbench tracks no template doc under docs/plans, docs/research or docs/handoffs, and `scripts/init_engine/owned.py` is the only place those paths are named.

#### Steps

Test first in `scripts/tests/init_engine/test_finalize.py`: seed tracked `docs/plans/contracts.json`, `docs/plans/index.json`, an epic under each phase, `docs/research/brief.md`, `docs/handoffs/h.md` and a template MEMORY.md entry, commit them, run `new`, then assert `git ls-files docs/plans` is exactly the three `.gitkeep` files and `git ls-files docs/research docs/handoffs` is empty. Run `pytest scripts/tests/init_engine/test_finalize.py -q`; expect the contracts.json assertion to fail first. Then implement.

#### Notes

The unit `workbench` fixture (`scripts/tests/init_engine/conftest.py`) has no git history; `init(run_cli, ...)` in test_finalize.py creates it. Retirement assertions use `git ls-files`, never the filesystem. The single-source test monkeypatches `owned.INSTANCE_OWNED` (import `owned` and `finalize` with `scripts/init_engine` on sys.path, as cli.py does) and calls `clear_template_history` directly on a temp dir.

### S2: Update command

- Status: done
- Files: `scripts/init_engine/update.py`, `scripts/init_engine/cli.py`, `scripts/init_engine/gitops.py`, `mise-tasks/init/update`, `scripts/tests/init_engine/test_update.py`, `scripts/tests/init_engine/conftest.py`
- Verify: `pytest scripts/tests/init_engine/test_update.py scripts/tests/init_engine/test_refresh.py -q && ruff check scripts && shellcheck mise-tasks/init/update`
- Verified head: ae39c750d22c36d70bd89e245dc4bd00b2d68e13

#### Requirement

Add the engine command `update` and the mise task `init:update` for the clean, shared-history path (design D3, D6).

- `scripts/init_engine/update.py` holds the logic; `cli.py` adds subcommand `update` with `--url` (used only when the `template` remote is missing; default `gitops.DEFAULT_TEMPLATE_URL = "https://github.com/szymonrychu/workbench"`, defined next to `TEMPLATE_URL_RE`) and `--branch` (default `main`). New `mise-tasks/init/update` mirrors `mise-tasks/init/refresh` and execs `python3 scripts/init_engine/cli.py update "$@"`.
- Preflight, before any change: refuse (exit 1, `refused: ...` on stderr) when AGENTS.md still has the uninitialised block (same check as `cmd_refresh`, `project_files.UNINIT_RE`), when `git status --porcelain` is non-empty (tracked changes or untracked files; list the paths), or when a merge is in progress.
- Remote: an existing `template` remote is used as is; a missing one is added with `--url` or the default. Fetch `template <branch>` and resolve the commit sha.
- When the template commit is already an ancestor of HEAD: print `up to date with template/<branch> <12-char sha>`, exit 0, no commit.
- Otherwise `git merge --no-commit --no-ff <sha>`; then for every `owned.INSTANCE_OWNED` path: remove it from index and worktree, and restore the HEAD version when HEAD tracks it (template-added files under owned dirs are dropped, modify/delete conflicts resolve to the project side). Then run the merged tree's `python3 scripts/init_engine/cli.py refresh` as a subprocess, passing the MEMORY.md event `template update <12-char sha>` (add a hidden `--event` to `refresh` that reaches `project_files.write_all(event=...)`).
- Commit with `git add -A` and `git commit`: subject `chore(workbench): template update <12-char sha>`, body trailer `Template-Commit: <full sha>`; HEAD^2 is the template commit; `git status --porcelain` is empty afterwards. Print the commit line.
- Lint gate (design D7): after the refresh and before the commit, run the lint command (default `mise run lint`; hidden `--lint-command <cmd>` on `update`, help suppressed like `--user-settings`, run through the shell from the workbench root); commit only on exit 0. Conflict handling beyond owned paths and the failure-abort paths are update-conflicts-and-abort's; this task refuses (exit 1) on a non-zero lint or refresh after `git merge --abort`.

#### Acceptance conditions

- AC1: update refuses an uninitialised workbench with exit 1 and changes nothing [evidence: test:scripts/tests/init_engine/test_update.py::test_update_refuses_uninitialised]
- AC2: update refuses a dirty tree (a modified tracked file, and an untracked file) with exit 1, lists the paths and changes nothing [evidence: test:scripts/tests/init_engine/test_update.py::test_update_refuses_dirty_tree]
- AC3: a missing template remote is added with the default URL, and with --url when given [evidence: test:scripts/tests/init_engine/test_update.py::test_update_adds_default_template_remote]
- AC4: an existing template remote keeps its URL [evidence: test:scripts/tests/init_engine/test_update.py::test_update_keeps_existing_template_remote]
- AC5: after update the template plugin change is present, and git ls-files shows no template epic, research file or contracts.json, MEMORY.md has no template entry, the project's own epic is unchanged [evidence: test:scripts/tests/init_engine/test_update.py::test_update_takes_tooling_drops_owned_paths]
- AC6: update ends in one merge commit with subject chore(workbench): template update <sha>, HEAD^2 the template commit, the Template-Commit trailer, a MEMORY.md template update line, and a clean status [evidence: test:scripts/tests/init_engine/test_update.py::test_update_one_commit_records_template_commit]
- AC7: an update with nothing new prints up to date, exits 0 and makes no commit [evidence: test:scripts/tests/init_engine/test_update.py::test_update_up_to_date_is_noop]
- AC8: mise-tasks/init/update execs the engine update subcommand [evidence: test:scripts/tests/init_engine/test_update.py::test_mise_task_runs_engine_update]
- AC9: the update tests, root lint and shellcheck pass [evidence: command:pytest scripts/tests/init_engine/test_update.py scripts/tests/init_engine/test_refresh.py -q && ruff check scripts && shellcheck mise-tasks/init/update]

#### Files

- `scripts/init_engine/update.py`
- `scripts/init_engine/cli.py`
- `scripts/init_engine/gitops.py`
- `mise-tasks/init/update`
- `scripts/tests/init_engine/test_update.py`
- `scripts/tests/init_engine/conftest.py`

#### Interfaces

`update.update(root: Path, url: str | None, branch: str) -> int`; exit codes 0 ok or up to date, 1 refusal, 2 usage. `gitops.DEFAULT_TEMPLATE_URL`. These are the `init-update-command` contract consumed by later tasks.

#### Expected outcome

`mise run init:update` in a clean, initialised project with shared template history ends in one merge commit `chore(workbench): template update <sha>` that carries the template's tooling and none of its owned docs; refusals change nothing.

#### Steps

Write `scripts/tests/init_engine/test_update.py` first. Fixture: add `upstream_pair` to `scripts/tests/init_engine/conftest.py` (later update tests reuse it): take the `workbench` fixture, `git init` and commit it as the template, clone it to `<tmp>/upstream`, run `new` in the workbench, then change upstream (a plugin file, a new epic under `docs/plans/done/x/README.md`, a MEMORY.md line, a modified `docs/plans/contracts.json`, a force-added `docs/research/b.md`) and commit. Run `pytest scripts/tests/init_engine/test_update.py -q`; expect failures on the missing subcommand. Implement until green.

#### Notes

The default-URL test maps the default URL to the local upstream with `GIT_CONFIG_COUNT`/`url.<upstream>.insteadOf=https://github.com/szymonrychu/workbench`, so no network is used. The unit fixture stubs `scripts/harness/setup.py`, so refresh runs offline. Unit tests pass `--lint-command true`; the e2e test exercises the real `mise run lint`. Retirement assertions use `git ls-files`.

### S3: Update conflicts and abort

- Status: done
- Files: `scripts/init_engine/update.py`, `scripts/tests/init_engine/test_update_conflicts.py`, `scripts/tests/init_engine/conftest.py`
- Verify: `pytest scripts/tests/init_engine/test_update.py scripts/tests/init_engine/test_update_conflicts.py -q && ruff check scripts`
- Verified head: 7221ebf9b4dcb4a30667bf585ae705bda7a1b83a

#### Requirement

Handle conflicts, the lint gate and every abort path of `update` (design D4, D7).

- Conflicts under `owned.INSTANCE_OWNED` are already resolved by update-command's restore.
- Conflicted paths in `owned.GENERATED_ON_CONFLICT` (config-dir entries resolved through `workbench.config_dir`) resolve to the project side (`git checkout --ours -- <path>` then `git add`); the refresh then regenerates their generated blocks. The output names each such file on one line `kept project side: <path>`.
- After the merge, keys in the config-dir `settings.json` `enabledPlugins` and `extraKnownMarketplaces` that end in `@workbench-template` (from `finalize.TEMPLATE_MARKET`) are renamed to the project's marketplace name read from `.claude-plugin/marketplace.json`; existing project keys and their values win.
- Any other conflicted path: `git merge --abort`, remove every untracked file the run created, print `refused: template update conflicts outside the known paths:` and one path per line on stderr, exit 1. HEAD, index, worktree and `git status --porcelain` equal the pre-run state; no MERGE_HEAD.
- Lint failure (gate added by update-command): abort exactly as above, print the last 20 lines of lint output, exit 1.
- A failing refresh subprocess aborts the same way.

#### Acceptance conditions

- AC1: a conflict in AGENTS.md resolves to the project side, the project answers survive, and the output names kept project side: AGENTS.md [evidence: test:scripts/tests/init_engine/test_update_conflicts.py::test_generated_conflict_keeps_project_side]
- AC2: a template-added enabledPlugins key suffixed @workbench-template is renamed to the project marketplace [evidence: test:scripts/tests/init_engine/test_update_conflicts.py::test_template_market_keys_renamed]
- AC3: a conflict outside the known paths aborts with exit 1, lists the path, and leaves HEAD, status and MERGE_HEAD as before [evidence: test:scripts/tests/init_engine/test_update_conflicts.py::test_unknown_conflict_aborts_cleanly]
- AC4: a failing lint command aborts with exit 1 and the same clean state, printing the lint tail [evidence: test:scripts/tests/init_engine/test_update_conflicts.py::test_lint_failure_aborts_cleanly]
- AC5: a failing refresh aborts with exit 1 and the same clean state [evidence: test:scripts/tests/init_engine/test_update_conflicts.py::test_refresh_failure_aborts_cleanly]
- AC6: the update test files and root lint pass [evidence: command:pytest scripts/tests/init_engine/test_update.py scripts/tests/init_engine/test_update_conflicts.py -q && ruff check scripts]

#### Files

- `scripts/init_engine/update.py`
- `scripts/tests/init_engine/test_update_conflicts.py`
- `scripts/tests/init_engine/conftest.py`

#### Interfaces

Uses `owned.GENERATED_ON_CONFLICT` and the `init-update-command` contract (including the hidden `--lint-command`).

#### Expected outcome

Conflicts in generated files resolve to the project side and are named in the output; any other conflict, a red lint or a failed refresh leaves HEAD, index, worktree and MERGE_HEAD exactly as before the run.

#### Steps

Write `scripts/tests/init_engine/test_update_conflicts.py` first, reusing the `upstream_pair` fixture from `scripts/tests/init_engine/conftest.py`. Conflict cases: upstream and project edit the same line of AGENTS.md's project block region; upstream adds `enabledPlugins["workbench-new@workbench-template"]`; upstream and project edit the same line of a plain tracked file (for example `docs/enterprise.md`). Run `pytest scripts/tests/init_engine/test_update_conflicts.py -q`; expect red. Implement until green, then rerun test_update.py.

#### Notes

The abort may remove untracked files safely only because the preflight refused any untracked state; keep that invariant explicit in a comment. Assert state with `git rev-parse HEAD`, `git status --porcelain` and `git rev-parse -q --verify MERGE_HEAD`.

### S4: Update unrelated history

- Status: done
- Files: `scripts/init_engine/update.py`, `scripts/init_engine/cli.py`, `scripts/tests/init_engine/test_update_unrelated.py`
- Verify: `pytest scripts/tests/init_engine/test_update.py scripts/tests/init_engine/test_update_conflicts.py scripts/tests/init_engine/test_update_unrelated.py -q && ruff check scripts`
- Verified head: a9f002008b61a02e9994fcdc9fc927e539eb704c

#### Requirement

Support projects with no shared history with the template (design D5).

- When `git merge-base HEAD <template sha>` finds nothing and no `--base` is given: change nothing, exit 1, print on stderr `refused: no shared history with template/<branch>`, the candidate base (the newest commit on the fetched `template/<branch>` whose committer date is not newer than the project's oldest root commit; `none` when there is none) and the rerun line `mise run init:update -- --base <candidate>`.
- `--base <sha>` on `update`: refuse (exit 1, nothing changed) unless `<sha>` is a commit and an ancestor of the fetched template commit. Otherwise create `git replace --graft <project root commit> <sha>` (the oldest root when there are several), run the normal update (merge, owned-path restore, generated conflicts, refresh, lint, commit), and delete the replace ref in every outcome (success, refusal, exception), so `git replace -l` is empty afterwards.
- The resulting commit's second parent is the real template commit, so the next update with a newer template commit needs no `--base`.
- `--base` given when a merge base already exists: ignore it with one stdout note `--base ignored: history is shared`.

#### Acceptance conditions

- AC1: with no shared history and no --base, update exits 1, changes nothing and prints the candidate base and the --base rerun line [evidence: test:scripts/tests/init_engine/test_update_unrelated.py::test_unrelated_history_refused_with_candidate]
- AC2: with --base the update merges, drops owned paths, HEAD^2 is the template commit and git replace -l is empty [evidence: test:scripts/tests/init_engine/test_update_unrelated.py::test_base_flag_merges_unrelated_history]
- AC3: a --base that is not an ancestor of the template commit is refused with nothing changed and no replace ref left [evidence: test:scripts/tests/init_engine/test_update_unrelated.py::test_base_not_in_template_refused]
- AC4: a later update after a --base update needs no --base [evidence: test:scripts/tests/init_engine/test_update_unrelated.py::test_next_update_needs_no_base]
- AC5: all update test files and root lint pass [evidence: command:pytest scripts/tests/init_engine/test_update.py scripts/tests/init_engine/test_update_conflicts.py scripts/tests/init_engine/test_update_unrelated.py -q && ruff check scripts]

#### Files

- `scripts/init_engine/update.py`
- `scripts/init_engine/cli.py`
- `scripts/tests/init_engine/test_update_unrelated.py`

#### Interfaces

Adds `--base` to the `init-update-command` contract (`cli.py update --base <sha>`).

#### Expected outcome

A project copied from the template without history gets a refusal naming the candidate base; with `--base` it takes the update in one merge commit, no replace ref remains, and later updates need no flag.

#### Steps

Write `scripts/tests/init_engine/test_update_unrelated.py` first. Fixture: build the upstream as `upstream_pair` does, then make the project by copying the upstream tree without `.git` (the README "copy it into a new directory" route) and running `new`. Run `pytest scripts/tests/init_engine/test_update_unrelated.py -q`; expect red. Implement until green.

#### Notes

`git replace --graft` is honoured by `git merge-base` and `git merge` by default; never set `GIT_NO_REPLACE_OBJECTS`. Clean-state assertions use `git rev-parse HEAD`, `git status --porcelain`, `git replace -l`.

### S5: E2e template update

- Status: done
- Files: `scripts/tests/e2e/test_template_update.py`, `scripts/init_engine/update.py`
- Verify: `pytest scripts/tests/e2e/test_template_update.py -q && ruff check scripts`
- Verified head: 1be9a6d434dd1cda928369c68cfede426be62d33

#### Requirement

Replace the manual-merge e2e with an end-to-end run of `mise run init:update` on a real template copy (design D2, D3, D4).

- `scripts/tests/e2e/test_template_update.py` drops the manual `git merge` plus `git checkout --ours` flow.
- `test_init_leaves_no_template_docs`: run `init new` in the `template` fixture (which carries this repo's real tracked docs/plans, including contracts.json); assert `git ls-files docs/plans` is exactly the three phase `.gitkeep` files, `git ls-files docs/research docs/handoffs` is empty, and MEMORY.md holds only the init header and the `project initialised` line.
- `test_template_update_roundtrip`: clone the template fixture to `upstream` before init (as today), run `init new` with purpose, hard rule, risk and `--harness cursor`; in the project add and commit its own epic `docs/plans/todo/my-epic/README.md`. In upstream: append a rule line to `plugins/workbench/rules/tdd.md` and rebuild with `scripts/harness/setup.py`, change a plugin file (for example `plugins/workbench/skills/handoff/SKILL.md`), add `docs/plans/done/template-epic/README.md`, append a dated MEMORY.md entry, force-add `docs/research/template-brief.md`, modify `docs/plans/contracts.json`; commit. Then `mise run init:update -- --url <upstream>` exits 0, and:
  - the rule line is in AGENTS.md and the plugin change is in the file;
  - `git ls-files docs/plans/done/template-epic docs/research docs/plans/contracts.json` is empty and the template MEMORY.md entry text is absent;
  - the project's purpose, hard rule and risk are in AGENTS.md, `docs/plans/todo/my-epic/README.md` is unchanged, no `<<<<<<<` in AGENTS.md;
  - exactly one new commit, subject `chore(workbench): template update <sha>`, `git status --porcelain` empty;
  - `scripts/doctor.py` reports `metarepo` and `components: 1`, and `mise run lint` exits 0.

#### Acceptance conditions

- AC1: after init on the real template copy, git ls-files shows only the three plan .gitkeep files and no research or handoffs, and MEMORY.md is fresh [evidence: test:scripts/tests/e2e/test_template_update.py::test_init_leaves_no_template_docs]
- AC2: init:update brings the rule and plugin changes, keeps the template epic, research, contracts and MEMORY entry out, keeps the project's answers and own epic, ends in one commit with lint green [evidence: test:scripts/tests/e2e/test_template_update.py::test_template_update_roundtrip]
- AC3: the manual git merge flow is gone from the e2e test [evidence: command:! grep -q 'checkout", "--ours' scripts/tests/e2e/test_template_update.py]
- AC4: the e2e file and root lint pass [evidence: command:pytest scripts/tests/e2e/test_template_update.py -q && ruff check scripts]

#### Files

- `scripts/tests/e2e/test_template_update.py`
- `scripts/init_engine/update.py`

#### Interfaces

Uses the `init-update-command` contract through `mise run init:update` only.

#### Expected outcome

The e2e suite proves init cleanup on the real template tree and a full `mise run init:update` round trip with real lint, replacing the manual-merge test.

#### Steps

Write the two tests; run `pytest scripts/tests/e2e/test_template_update.py -q`. The engine tasks have landed, so the tests may pass at once: say so in `tests.note` (they pin delivered behaviour end to end); if they fail, the failure is a real gap in the engine and gets fixed in update.py within this task.

#### Notes

Fixtures `template`, `engine`, `mise` in `scripts/tests/e2e/conftest.py` and `helpers.git/run`. The engine's lint gate runs the real `mise run lint` inside the project here, which is the "lint green" proof. Retirement assertions use `git ls-files`.

### S6: Template update skill

- Status: done
- Files: `plugins/workbench/skills/template-update/SKILL.md`, `plugins/workbench/skills/template-update/tests/test_template_update_skill.py`, `plugins/workbench/README.md`
- Verify: `cd plugins/workbench && bash scripts/run-tests.sh --only template-update && pytest skills/start-development/tests/test_release.py -q -k readme`
- Verified head: efddaf2cc90f64aeeab3532c577861fb6808608d

#### Requirement

Add the `template-update` skill (design D8, D5).

- `plugins/workbench/skills/template-update/SKILL.md` with frontmatter `name: template-update` and a folded `description: >` (over 80 characters) naming the triggers ("update from the template", "pull template updates", "refresh the workbench from the template").
- Body: run `mise run init:update` from the workbench root; add `-- --url <url>` or `--branch <branch>` only when the user named them. Ask the user nothing on the normal path. Report: the one commit (subject and sha), the template sha, every `kept project side:` file, and that nothing was pushed. Never call a script path, never push.
- Refusals: uninitialised workbench, say to run `init` first; dirty tree, list the paths and stop (do not stash or commit them for the user); conflicts outside the known paths, list them and name the manual route (merge `template/<branch>` by hand, resolve, `mise run init:refresh`); lint failure, show the tail and stop; up to date, say so.
- Unrelated history: show the candidate base the engine printed, ask the user to confirm it (the only question), then rerun `mise run init:update -- --base <sha>`.
- `plugins/workbench/README.md` Skills list gains a `template-update` line, and the paragraph after it mentions that it wraps `mise run init:update`.

#### Acceptance conditions

- AC1: SKILL.md frontmatter is name template-update with a folded description [evidence: test:plugins/workbench/skills/template-update/tests/test_template_update_skill.py::test_frontmatter]
- AC2: the skill reaches the engine only through mise run init:update [evidence: test:plugins/workbench/skills/template-update/tests/test_template_update_skill.py::test_engine_only_through_mise_task]
- AC3: every flag the skill passes exists in cli.py update --help [evidence: test:plugins/workbench/skills/template-update/tests/test_template_update_skill.py::test_flags_exist_in_cli_help]
- AC4: the only question is the unrelated-history base confirmation [evidence: test:plugins/workbench/skills/template-update/tests/test_template_update_skill.py::test_asks_only_for_unrelated_history_base]
- AC5: the skill reports commit, template sha, kept project side files and the refusals, and never pushes [evidence: test:plugins/workbench/skills/template-update/tests/test_template_update_skill.py::test_reports_commit_and_refusals]
- AC6: the plugin README names the skill [evidence: test:plugins/workbench/skills/start-development/tests/test_release.py::test_readme_documents_the_template]
- AC7: the skill suite, the README test, frontmatter parsing and plugin lint pass [evidence: command:cd plugins/workbench && bash scripts/run-tests.sh --only template-update && pytest skills/start-development/tests/test_release.py -q -k readme && cd ../.. && pytest scripts/tests/harness/test_sources.py -q -k frontmatter && ruff check plugins/workbench/skills/template-update]

#### Files

- `plugins/workbench/skills/template-update/SKILL.md`
- `plugins/workbench/skills/template-update/tests/test_template_update_skill.py`
- `plugins/workbench/README.md`

#### Interfaces

Uses the `init-update-command` contract: `update` flags `--url`, `--branch`, `--base`.

#### Expected outcome

`workbench:template-update` exists, is listed in the plugin README, runs only `mise run init:update`, asks at most the unrelated-history base question and reports the commit.

#### Steps

Write `plugins/workbench/skills/template-update/tests/test_template_update_skill.py` first, mirroring `plugins/workbench/skills/init/tests/test_init_skills.py`: frontmatter shape, no `cli.py`/`init_engine`/`CLAUDE_PLUGIN_ROOT` in the body, every `--flag` on a `mise run init:update -- ...` line exists in `cli.py update --help`, the base question is the only question, the report names commit, sha and `kept project side`, and the body says it never pushes. Run `cd plugins/workbench && bash scripts/run-tests.sh --only template-update`; expect red (no SKILL.md). Write the skill and the README line until green.

#### Notes

Resolve the CLI path as init's test does: `SKILLS = Path(__file__).resolve().parents[2]`, `ROOT = SKILLS.parents[2]`, `CLI = ROOT / "scripts" / "init_engine" / "cli.py"`. The plugin README test is `plugins/workbench/skills/start-development/tests/test_release.py::test_readme_documents_the_template`.

### S7: Docs update flow

- Status: done
- Files: `README.md`, `MEMORY.md`
- Verify: `python3 scripts/check_personal.py && grep -q init:update README.md`
- Verified head: cb97b45f8415de6adf8a35e2bea84a4a7736b989

#### Requirement

Point the docs at the new flow (design D9).

- README.md `## Pulling template updates`: replace the manual `git remote add` / `git merge template/main` steps with the `template-update` skill and `mise run init:update` (optional `--url`, `--branch`, `--base`); state what arrives (tooling, plugins, rules, generated blocks) and what never does (template plans and records, contracts.json, index.json, facts.md, research, handoffs, MEMORY.md and ROADMAP.md entries); the refusals (uninitialised, dirty tree, conflicts outside the known paths with the manual route, lint failure) and the unrelated-history `--base` case; that it ends in one local commit and never pushes; `mise run doctor` afterwards.
- README.md `## What init does`: one bullet saying init removes the template's own docs (plans, records, contracts, research, handoffs) and starts MEMORY.md and ROADMAP.md fresh.
- Root MEMORY.md: one dated entry (2026-10-22 or the landing date) headed `template update` recording D3 (git merge with owned-path restore over a copier-style sync, and why), D5 (graft for unrelated histories), D6 (merge commit as the record), D7 (lint inside the engine), and that `scripts/init_engine/owned.py` is the one owned-path list.

#### Acceptance conditions

- AC1: README.md has the Pulling template updates section [evidence: doc-section:README.md#Pulling template updates]
- AC2: the section names the skill and init:update and no longer documents the manual merge [evidence: command:grep -q 'template-update' README.md && grep -q 'init:update' README.md && ! grep -q 'git merge template/main' README.md]
- AC3: README What init does states that template docs are removed at init [evidence: judgement:]
- AC4: MEMORY.md records the update mechanism decision [evidence: command:grep -qi 'template update' MEMORY.md && grep -q 'owned.py' MEMORY.md]
- AC5: the personal-reference lint passes [evidence: command:python3 scripts/check_personal.py]

#### Files

- `README.md`
- `MEMORY.md`

#### Interfaces

None beyond the files listed; no public signature changes.

#### Expected outcome

README.md tells users to run the template-update skill (or `mise run init:update`) and what it keeps out; MEMORY.md records the mechanism decision.

#### Steps

- Doc edit only (TDD exception: a comment or doc edit); say so in `tests.note`.
- Rewrite README.md `## Pulling template updates` and add the `## What init does` bullet.
- Append the MEMORY.md entry.
- Run `python3 scripts/check_personal.py && grep -q init:update README.md`; expect exit 0.

#### Ruling

- 2026-10-22 accepted: run 1: all 7 tasks landed on main at d87b383 (plus README -- separator fix and init_helpers rename); docs-update-flow escalated only on an empty verifier evidence field, hand-verified (check_personal rc 0, README grep rc 0). Phase 5 remediation: update-safety.

#### Notes

README.md must keep passing the personal-reference lint (`python3 scripts/check_personal.py`); the template URL is already allowed there. MEMORY.md is also edited by flow-speed-and-token-optimiz/cache-prefix-change; append a separate entry, never rewrite others.

### S8: Update safety

- Status: done
- Files: `scripts/init_engine/update.py`, `scripts/tests/init_engine/test_update_safety.py`, `plugins/workbench/skills/template-update/SKILL.md`, `plugins/workbench/skills/template-update/tests/test_template_update_skill.py`
- Verify: `pytest scripts/tests/init_engine/test_update_safety.py plugins/workbench/skills/template-update/tests/test_template_update_skill.py -q && ruff check scripts plugins/workbench/skills/template-update`
- Verified head: 322a9eed6457410b23d312f78c2f8fc4db7d0b91

#### Requirement

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

#### Acceptance conditions

- AC1: a gitignored file under docs/research and one under docs/handoffs survive a successful update and an aborted one [evidence: test:scripts/tests/init_engine/test_update_safety.py::test_update_keeps_ignored_owned_files]
- AC2: an explicit --url differing from an existing template remote is refused with nothing changed [evidence: test:scripts/tests/init_engine/test_update_safety.py::test_update_refuses_url_mismatch_with_template_remote]
- AC3: --branch -x and --base -x are refused with nothing changed [evidence: test:scripts/tests/init_engine/test_update_safety.py::test_update_refuses_option_like_branch_and_base]
- AC4: the output names the template url, branch and commit [evidence: test:scripts/tests/init_engine/test_update_safety.py::test_update_prints_source]
- AC5: SKILL.md tells the agent to confirm a non-default --url with the user before running [evidence: test:plugins/workbench/skills/template-update/tests/test_template_update_skill.py::test_skill_confirms_non_default_url]

#### Files

- `scripts/init_engine/update.py`
- `scripts/tests/init_engine/test_update_safety.py`
- `plugins/workbench/skills/template-update/SKILL.md`
- `plugins/workbench/skills/template-update/tests/test_template_update_skill.py`

#### Interfaces

- `update.restore_owned(root)` keeps its signature.
- CLI flags unchanged; new refusals exit 1 like the existing ones.

#### Expected outcome

Updating from the template cannot delete local untracked or ignored notes, cannot silently fetch from a different source than requested, and asks before running code from a non-default template.

#### Steps

1. Write test_update_safety.py (reuse init_helpers fixtures) and the skill test; see them fail.
2. Restrict restore_owned to staged paths; add the url, branch and base checks and the source line; update SKILL.md.
3. Run the verify command.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S9: Existing remote kept

- Status: done
- Files: `scripts/tests/init_engine/test_update.py`
- Verify: `pytest scripts/tests/init_engine/test_update.py -q && ruff check scripts`
- Verified head: a8d952468624aa0afef9b2865629c635253cc411

#### Requirement

Scope audit gap (2026-10-22): update-command AC4 says an existing template remote keeps its URL, citing scripts/tests/init_engine/test_update.py::test_update_keeps_existing_template_remote, but no such test exists on main and nothing asserts it.

Deliver: the test `test_update_keeps_existing_template_remote` in scripts/tests/init_engine/test_update.py. A workbench whose `template` remote points at a local upstream (a URL other than the default) runs `update` with no `--url`. The update succeeds from that remote, and afterwards `git remote get-url template` still prints the original URL. If the behaviour is missing, fix update.py so it holds. Reuse the init_helpers fixtures.

#### Acceptance conditions

- AC1: with an existing template remote and no --url, update succeeds and the remote URL is unchanged [evidence: test:scripts/tests/init_engine/test_update.py::test_update_keeps_existing_template_remote]

#### Files

- `scripts/tests/init_engine/test_update.py`

#### Interfaces

- No interface change; test only unless the behaviour is missing.

#### Expected outcome

update-command AC4 is pinned by a real test.

#### Steps

1. Write the test and run it; if it passes at once, this is a pinning test of existing behaviour (say so in tests.note).
2. If it fails, fix update.py.
3. Run the verify command.

#### Ruling

- 2026-10-22 accepted: Accepted 2026-10-22: pin test of existing behaviour, red shown by mutation; TDD-skipped exception (no non-test change). Landed on main.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none

## Rulings (migrated)

- docs-update-flow: accept true, at 2026-10-22T07:00:18Z: run 1: all 7 tasks landed on main at d87b383 (plus README -- separator fix and init_helpers rename); docs-update-flow escalated only on an empty verifier evidence field, hand-verified (check_personal rc 0, README grep rc 0). Phase 5 remediation: update-safety.
- existing-remote-kept: accept true, at 2026-10-22T07:56:27Z: Accepted 2026-10-22: pin test of existing behaviour, red shown by mutation; TDD-skipped exception (no non-test change). Landed on main.
