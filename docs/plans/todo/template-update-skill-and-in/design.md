# Template update skill and init docs cleanup design

## Summary

The template repo keeps its own development docs tracked (plans, records, contracts, research,
MEMORY.md and ROADMAP.md entries). Projects made from it must never carry them. Two changes:

- One instance-owned path list (`scripts/init_engine/owned.py`) drives init's template-history
  cleanup, which now also drops `docs/plans/contracts.json`, `docs/plans/index.json` and
  `docs/handoffs`.
- A new engine command `mise run init:update` merges the template (`git merge --no-commit`),
  restores every instance-owned path to the project's HEAD, keeps the project side of known
  generated files, re-runs the merged tree's refresh writers, runs lint and ends in one merge commit
  `chore(workbench): template update <sha>`. A new `template-update` skill runs it and reports.

## Intent and why

User decisions (2026-10-22, verbatim): "don't add to gitignore. During initial setup, cleanup the
docs. Add a skill, that will refresh future instances of workbenches without workbench specific
docs." Workbench-specific docs are the template repo's own development docs: docs/plans epics and
records (todo, in-progress, done), docs/plans/contracts.json, index.json, facts.md, docs/research,
and the template's MEMORY.md and ROADMAP.md entries. User docs that ship with the template
(README.md, docs/enterprise.md, docs/harnesses.md, plugin docs) are not template-specific.

Today init clears the plan phases, docs/research and facts.md (`scripts/init_engine/finalize.py:128`
`clear_template_history`, first init only, `finalize.py:210`) but leaves the tracked
`docs/plans/contracts.json`. Pulling template updates is a manual `git merge template/main`, hand
conflict resolution and `mise run init:refresh` (README.md:319), and that merge brings every new
template epic, research file and MEMORY.md entry into the project.

## Goals

- After `init:new` or `init:adopt`, `git ls-files docs/plans` lists only the three phase
  `.gitkeep` files, `git ls-files docs/research docs/handoffs` is empty, and MEMORY.md and
  ROADMAP.md are the fresh init versions.
- `mise run init:update` in an initialised, clean workbench brings template tooling, plugins, rules
  and generated blocks; brings no template plan, record, research, contracts, MEMORY.md or
  ROADMAP.md entry; leaves the project's own docs and AGENTS.md answers intact; ends in exactly one
  commit with `mise run lint` green.
- It refuses a dirty tree and an uninitialised workbench, and aborts with no half-applied state on
  conflicts outside the known paths, naming them.
- The `template-update` skill runs it, asking nothing except in the unrelated-history case.
- README "Pulling template updates" points at the skill.

## Non-goals

- Gitignoring docs/plans in the template (user decision).
- Changes to the personal plugin at ~/Documents/claude-infra-plugin.
- Pushing anything; the update commits locally only.
- Updating components under `code/`; only the workbench superrepo is updated.

## Anti-goals

- A template doc reappearing in a project after any update.
- A refused or failed update that leaves conflict markers, a MERGE_HEAD, a replace ref, staged
  changes or new untracked files behind.
- The owned-path list duplicated between init and update so the two drift.
- An update that loses the project's AGENTS.md answers, its own epics or its MEMORY.md history.

## Constraints

- The init engine is stdlib python run with `python3` through mise tasks only
  (`.claude/rules/python.md`); skills call `mise run`, never a script path
  (`plugins/workbench/skills/init/tests/test_init_skills.py::test_engine_only_through_mise_tasks`).
- Root scripts tests run as `pytest scripts/tests/...` from the repo root (`mise-tasks/test/scripts`);
  plugin skill tests run per skill (`cd plugins/workbench && bash scripts/run-tests.sh --only <skill>`).
  Lint for the engine is `ruff check scripts` plus shellcheck on `mise-tasks/*` (`mise-tasks/lint/root`).
- Git: only commands available on the git shipped with macOS (no `git merge-tree --merge-base`);
  `git replace --graft` is allowed.
- Epic flow-speed-and-token-optimiz is running and owns plugins/workbench/workflows,
  plugins/workbench/scripts, start-development references, plugins/workbench/rules and AGENTS.md.
  This epic touches none of them. It touches root `MEMORY.md`, which that epic's
  cache-prefix-change task also edits; MEMORY.md is a doc file under the default `overlapIgnore`,
  so the two only append separate entries.
- The plugin README must name every skill
  (`plugins/workbench/skills/start-development/tests/test_release.py::test_readme_documents_the_template`).

## Decisions

### D1: The template keeps its docs tracked; nothing is gitignored

The template's plans, records, contracts.json, MEMORY.md and ROADMAP.md stay tracked in the template
repo. Instances drop them at init (D2) and never take them on update (D3). Alternative: gitignore
docs/plans in the template; rejected by the user. Serves A1.

### D2: One instance-owned path list, shared by init cleanup and update

`scripts/init_engine/owned.py` defines `INSTANCE_OWNED`, an ordered tuple of `(path, kind)`:
`docs/plans/todo`, `docs/plans/in-progress`, `docs/plans/done` (kind `phase`: reset to an empty dir
with `.gitkeep` at init), `docs/plans/contracts.json`, `docs/plans/index.json`, `docs/plans/facts.md`,
`docs/research`, `docs/handoffs` (kind `delete`), `MEMORY.md`, `ROADMAP.md` (kind `rewritten`:
written fresh by `project_files.memory_and_roadmap` on first init, so cleanup leaves them).
`finalize.clear_template_history` iterates this tuple, and `update` restores every entry to HEAD.
Nothing else in the engine names these paths. `docs/handoffs` is on the list (my call): it is
gitignored in the template but a copied template would carry the template's session handoffs.
Alternatives: keep the paths in finalize.py and import them (rejected: the list is also the
update contract, so it gets its own module); a JSON manifest (rejected: a second format for a
python-only consumer). Serves A2, A4.

### D3: Update mechanism is git merge with owned-path restore (my call)

`update` fetches `template/<branch>`, runs `git merge --no-commit --no-ff <sha>`, then for every
`INSTANCE_OWNED` path removes it from index and worktree and restores the HEAD version where HEAD
has one (so template-added files under owned dirs are dropped and modify/delete conflicts resolve to
the project side). It then runs the merged tree's own `python3 scripts/init_engine/cli.py refresh`
as a subprocess (so the template's new writers and harness generators run, not the pre-merge
code), stages everything and commits the merge. Why: init keeps the template history (a clone
renames origin to `template`, `gitops.py:48`), so a real three-way merge exists for free and keeps
user edits to tooling files; the merge commit itself records the synced commit, and the next
update's merge base is that commit. Alternative (b): a copier/cruft-style sync from a recorded
last-synced commit and an ownership manifest; rejected because it needs its own three-way file
merge (or overwrites user edits to tooling), a manifest of every template file, and a state file,
while git already provides all three. Serves A3.

### D4: Conflict policy: project side for generated files, clean abort for anything else

Conflicts under `INSTANCE_OWNED` resolve by D3's restore. Conflicts in the generated-file set
`GENERATED_ON_CONFLICT` in owned.py (`AGENTS.md`, `.mise.toml`, `docs/architecture.md`, `LICENSE`,
`.claude-plugin/marketplace.json`, and `settings.json` and `workbench.json` in the config dir
resolved through `workbench.config_dir`) resolve to the project side (`git checkout --ours`), and
the refresh in D3 regenerates their generated blocks from the merged sources; the output lists
each file kept this way. `enabledPlugins` and `extraKnownMarketplaces` keys suffixed
`@workbench-template` that arrive from the template are renamed to the project's marketplace name.
Any other conflicted path aborts: `git merge --abort`, remove files the run created, print every
conflicted path on stderr, exit 1. The same clean abort applies when refresh or lint fails (D7).
The abort is safe because the preflight refuses any dirty or untracked state, so every untracked
file after the merge is the run's own. Alternatives: per-file JSON resolvers that take the
template side of marketplace.json and settings.json (rejected: larger, and the rename covers the
only key the template can add); take the template side of AGENTS.md and splice the project block
back (rejected: drops a user's own prose edits; the caller asked for the project side). Serves A3.

### D5: Unrelated histories: refuse with a candidate, merge through a temporary graft (my call)

A project made by copying the template (README Quick start "copy it into a new directory") or by
GitHub "Use this template" shares no history with the template. When `git merge-base HEAD <sha>`
finds nothing, `update` refuses (exit 1) without touching anything and prints the candidate base,
the newest `template/<branch>` commit not newer than the project's root commit, and the rerun line
`mise run init:update -- --base <candidate>`. With `--base <sha>` (which must be an ancestor of
the fetched template commit, else refuse) it grafts the project's root commit onto `<sha>` with
`git replace --graft`, runs the D3 merge, and deletes the replace ref in every outcome. The merge
commit's second parent is the real template commit, so every later update has a native merge
base and needs no `--base`. Alternatives: `--allow-unrelated-histories` (rejected: with an empty
base every differing file conflicts); guessing the base silently (rejected: a wrong base produces a
wrong merge without any signal). Serves A3.

### D6: The synced template commit is recorded by the merge commit (my call)

The one commit is a merge with the template commit as second parent, subject
`chore(workbench): template update <12-char sha>`, body trailer `Template-Commit: <full sha>`.
The refresh writer appends the dated MEMORY.md line `template update <12-char sha>` (passed as
`event`). No separate state file. Alternative: a `template.commit` key in workbench.json (rejected:
a second record that can disagree with history). An update with nothing new (the template commit
is already an ancestor of HEAD) prints `up to date` and makes no commit. Serves A3.

### D7: Lint runs inside the engine before the commit (my call)

After the refresh, `update` runs the lint command (default `mise run lint`, hidden
`--lint-command` for tests) and commits only when it exits 0; otherwise it aborts per D4 and prints
the lint output tail. This keeps "one commit, lint green" an engine guarantee rather than a skill
instruction. Alternative: the skill runs lint after the commit (rejected: a red lint then needs a
second commit). Serves A3.

### D8: The `template-update` skill

`plugins/workbench/skills/template-update/SKILL.md` runs `mise run init:update` (optionally
`-- --url <url> --branch <branch>` only when the user named them), asks the user nothing on the
normal path, and reports the one commit, the template sha and the files kept on the project side.
On a dirty tree it lists the paths and stops; on an unknown conflict it reports the paths and the
manual route; on unrelated histories it shows the candidate base, asks the user to confirm it, and
reruns with `--base`. It never pushes. Listed in plugins/workbench/README.md. Serves A3.

### D9: Docs point at the skill

README.md "Pulling template updates" describes the skill and `mise run init:update`, what arrives
and what never does, and the refusal cases; "What init does" states that template docs are
removed at init. Root MEMORY.md gets a dated entry for D3 to D7. Serves A2, A3.

## Research

| Lens | Ran or skipped | Adopted ideas | Rejected ideas |
|---|---|---|---|
| code internal (caller recon, re-read here) | ran | reuse `clear_template_history` (finalize.py:128), `cmd_refresh` (cli.py:156), `UNINIT_RE` (project_files.py:16), `memory_and_roadmap` event lines (project_files.py:266), e2e fixtures (scripts/tests/e2e/conftest.py) | none |
| code external (copier, cruft) | skipped: the caller laid out the copier/cruft option; D3 weighs it | none | manifest-based sync (D3 alternative b) |
| docs, papers | skipped: git plumbing only | none | none |

## Research inputs

| Source | Entry | Lands in |
|---|---|---|
| finalize.py:128 | `clear_template_history` misses contracts.json and index.json | instance-owned-paths |
| project_files.py:266 | MEMORY.md and ROADMAP.md rewritten on first init | instance-owned-paths |
| cli.py:156 | `cmd_refresh` refuses an uninitialised tree; reuse its check | update-command |
| gitops.py:48 | origin renamed to `template` on clone | update-command |
| README.md:319 | manual merge flow to replace | docs-update-flow |
| scripts/tests/e2e/test_template_update.py | manual-merge e2e to replace | e2e-template-update |
| plugins/workbench/skills/init/tests/test_init_skills.py | skill test shape (frontmatter, mise only, flags in cli help) | template-update-skill |
| test_release.py::test_readme_documents_the_template | plugin README names every skill | template-update-skill |

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 template keeps its docs tracked | instance-owned-paths |
| D2 one instance-owned path list | instance-owned-paths, update-command, e2e-template-update |
| D3 git merge with owned-path restore | update-command, e2e-template-update |
| D4 conflict policy and clean abort | update-conflicts-and-abort, e2e-template-update |
| D5 unrelated histories through a graft | update-unrelated-history, template-update-skill |
| D6 merge commit records the template commit | update-command |
| D7 lint inside the engine | update-command, update-conflicts-and-abort |
| D8 template-update skill | template-update-skill |
| D9 docs point at the skill | docs-update-flow |

## Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| `instance-owned-paths` | instance-owned-paths | update-command, update-conflicts-and-abort | `scripts/init_engine/owned.py` |
| `init-update-command` | update-command | update-conflicts-and-abort, update-unrelated-history, e2e-template-update, template-update-skill, docs-update-flow | `scripts/init_engine/cli.py` (subcommand `update`) and `mise-tasks/init/update` |

No cross-epic contracts: no other todo or in-progress epic reads or writes these parts.

## Review focus

- Every failure path after `git merge` starts: tree, index, HEAD, MERGE_HEAD and `refs/replace`
  exactly as before. Tests assert on `git status --porcelain`, `git rev-parse HEAD` and
  `git replace -l`.
- Owned-path restore drops template-added files under owned dirs and resolves modify/delete
  conflicts; assertions use `git ls-files`, never the filesystem.
- The refresh runs the merged tree's cli, not the imported pre-merge module.
- `clear_template_history` and `update` both read `INSTANCE_OWNED`; no path literal elsewhere.

## Left to the builder

- Internal structure of `scripts/init_engine/update.py` and the exact wording of messages, within
  the refusal and output lines named in the tasks.
- How `GENERATED_ON_CONFLICT` represents config-dir files (relative names resolved through
  `workbench.config_dir`, or a function).
- Which root commit is grafted when the project history has several roots (the oldest by default).

## Assumptions and unknowns

- Assumed: a cloned instance keeps the template history. Confirmed by `gitops.rename_template_origin`
  and the e2e fixture (upstream cloned from the pre-init commit).
- Assumed: `git replace --graft` is honoured by `git merge-base` and `git merge`; confirmed by the
  update-unrelated-history tests, not by guess.
- The default template URL `https://github.com/szymonrychu/workbench` matches `TEMPLATE_URL_RE`
  (gitops.py:7); tests map it to a local upstream with `url.<local>.insteadOf` so no network is used.

## Open questions

none
- Q1: Should init cleanup and update also own docs/handoffs (gitignored in the template, but carried by a copied template)? [recommended: yes, keep it on the instance-owned list]

## Irreversible operations in scope

- `git merge --abort` and removal of untracked files on a failed update: safe because the preflight
  refuses any dirty or untracked state, so only files the run created are removed.
- init cleanup deletes template docs on first init only (existing behaviour, extended to
  contracts.json, index.json and docs/handoffs).
- No push, no force operation, no remote change except adding a missing `template` remote.
