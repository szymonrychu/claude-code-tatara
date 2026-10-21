# Epic integration worktrees design

## Summary

The workbench flow owns every git worktree it uses with plain `git worktree` commands and gives each
epic one integration worktree. `ticket.py move <epic> in-progress` creates the integration tree
`<configdir>/worktrees/<epic>` on branch `<epic>` (component mode: `<configdir>/worktrees/<epic>/<repo>`
per repo). Task trees are `<epic>-<task>`, fork from `<epic>` and land back on it inside the
plan-execute run, so verifier and reviewer diffs are taken against `<epic>` and never carry a
dependency's text. When the epic passes review and the full suite, `<epic>` is rebased onto main and
main is fast-forwarded (meta mode) or merged through the MR (component mode), and `ticket.py move
<epic> done` removes every task and integration tree and branch. Template only.

## Intent and why

Requested by the user on 2026-10-21 (U1-U3 in the approval ledger): skills use git worktree commands,
never the harness built-in feature; an epic gets its own integration worktree named `<epic>`, task
branches `<epic>-<task>` start from it and merge back into it, and all agents on a task share its
tree; once the epic is delivered and fully tested its worktree merges back to main and every epic and
task worktree is cleaned.

Today (facts from the internal map, paths relative to the repo, SD = `plugins/workbench/skills/start-development`):
- Every task forks from main and lands straight on main: `ticket.py worktrees` defaults `--base main`
  (SD/scripts/ticket.py:1681-1688), `args.py:99` hard-codes `"baseRef": "main"`, `continue`
  (continue_cmd.py:177) and `move done` (ticket.py:1697) default `--base main`.
- The `<epic>` integration branch exists only in docs (phase-4-execute.md:7-10, tickets.md:62). Nothing
  creates it; in component mode a human runs `git-worktrees-create`, which makes
  `.worktrees/<epic>/<repo>` (skills/_lib/common.py:73-75, common.sh:93-96) off `origin/<tracked>`.
  Meta mode has no integration tree at all.
- Task trees are `<epic>--<task>` (ticket.py:63-67, cap `WORKTREE_MAX = 58` at :36); `--` is parsed
  back out at ticket.py:571 (check warning) and :1520 (reap-all), produced at :473, :1247,
  :1457-1463, continue_cmd.py:122 and validated in plan-execute.js:316-326.
- Dependents merge each dependency branch into their own tree (plan-execute.js dependencyLines
  :784-798, forwardMerge :2213-2272), so a dependent's merge-base diff (`$(git merge-base HEAD main)..HEAD`,
  :933) and the verifier `--base main` (:1016) include the dependency's text.
- Landing is outside the run: `continue` prints `MERGE` lines (exit 2) and the orchestrator dispatches
  `worktree-merger`, whose merge.py (skills/worktree-merge/scripts/merge.py:206-304) rebases onto local
  base, then `git checkout <base>` in the main checkout if needed (:263-267), `merge --ff-only`, and runs
  suites there. A fast-forward into a branch checked out in another worktree is impossible there.
- Nothing calls the built-in feature (`isolation: "worktree"`, EnterWorktree/ExitWorktree,
  `claude --worktree`, WorktreeCreate/WorktreeRemove). Only guard text mentions it
  (agents/implementer.md:28, skills/worktree-create/SKILL.md:51-53, SD/references/worktrees.md:19-21,
  plan-execute.js:1846-1849), pinned by start-research/tests/test_start_skills_structure.py:257-269,
  workflows/tests/plan-execute.test.mjs:349-356 and plan-execute-implementer.test.mjs:64.
  SD/tests/test_repo_hygiene.py:25 still allows `isolation` as an agent frontmatter key.

Claude Code built-in worktree facts this design relies on (docs as of v2.1.305):
- `WorktreeCreate` does not fire for `git worktree add` run through Bash; `WorktreeRemove` fires only
  for trees a WorktreeCreate hook made.
- The built-in sweep removes only CC-marked subagent and background trees older than
  `cleanupPeriodDays`; it keeps any tree made with `git worktree add` and any tree without the marker.
- `claude -w <name>` adopts a directory of that name under `.claude/worktrees/`, and EnterWorktree
  enters such a path without a prompt; isolated subagents skip the worktree-root CLAUDE.md there.
- A subagent starts in the main conversation's cwd and `cd` does not persist between its Bash calls,
  so every prompt carries absolute paths and uses `cd <wt> && cmd` or `git -C`.

## Goals

- No skill, agent, workflow, hook manifest or generated harness file uses or instructs the built-in
  worktree feature; a guard test fails on any new use.
- `ticket.py move <epic> in-progress` creates (or reuses) the integration tree on branch `<epic>`:
  meta mode `<configdir>/worktrees/<epic>` from main, component mode
  `<configdir>/worktrees/<epic>/<repo>` per repo in scope from the repo's tracked branch.
- Task trees and branches are `<epic>-<task>` (at most 57 characters), fork from `<epic>` and land on
  it; a slug whose branch would collide with another epic's branch is refused at creation.
- Every role on a task (implementer, fixers, verifier, reviewers, forward-merge, land) works in that
  task's one tree.
- Inside an epic run each clean, verified task lands on `<epic>` before its dependents start; the
  verifier and reviewer diff against `<epic>`.
- Epic close: integration tree verified with the full suite, merged to main (meta: rebase plus
  fast-forward; component: MR), full suite on main, then `move done` removes every tree and branch.
- Every doc and the off-Claude fallback describe this one lifecycle; every test that pinned the old
  naming, base or merge target is updated by the task that changes it.

## Non-goals

- The personal plugin at ~/Documents/claude-infra-plugin (template only).
- Moving worktrees out of `<configdir>/worktrees/`.
- Pushing to remotes or opening MRs differently from today's phase 6 in component mode.
- A permission deny rule for the built-in feature (the guard test pins absence instead).

## Anti-goals

- The human's main checkout is switched to another branch by any script.
- Work is lost: a tree or branch is removed before an explicit merged check passed.
- A dependent's diff, review or verification includes a dependency's text.
- Old `--` trees in existing workbenches become unreapable or are reaped while unmerged.
- Non-epic plan-execute runs (no `args.epic`) change behaviour.

## Constraints

- Test first per task (rules/tdd.md); `mise run test` and `mise run lint` green before anything lands.
- Plain `git worktree add/remove`, `git branch`, `git rebase`, `git merge --ff-only` only; no
  `--force` removal, no `reset --hard`, no force push.
- `ticket.py` mutates only from the main checkout and commits its own `docs/plans/` changes; task
  frontmatter stays inside the restricted format (scalars and inline lists).
- Slugs keep `slugify(title, 28)`; the name cap is recomputed as 28 + 1 + 28 = 57.
- The plugin loads from the main checkout via a versioned cache: plugin edits made in an epic are not
  live until they reach main (README.md:353-357, AGENTS.md template maintenance).

## Decisions

### D1: Plain git worktrees only, pinned by guard tests; trees stay under `<configdir>/worktrees/`

Every worktree is made and removed with `git worktree` through Bash. U1 is already true in code, so it
is delivered as a guard test over `plugins/workbench/{skills,agents,workflows,hooks,rules}`, the plugin
and marketplace manifests, every agent frontmatter (the `isolation` key is no longer allowed) and the
output of every harness emitter, plus wording ("per-task git worktrees" instead of "worktree
isolation"). Trees stay under `<configdir>/worktrees/`: the built-in only cleans trees it created and
marked, and plain `git worktree add` trees carry no marker. Alternatives: a distinct directory
(rejected: a migration with no safety gain), a deny rule (rejected: changes the user's permission
surface, not requested). (my call, D-a) Serves A1.

### D2: The integration tree lives at `<configdir>/worktrees/<epic>[/<repo>]` and is created at claim

Meta mode: a worktree of the superrepo at `<configdir>/worktrees/<epic>` on branch `<epic>`, forked
from local main. Component mode: `<configdir>/worktrees/<epic>/<repo>` for each repo in scope (the
README `repos` that name a `code/` submodule plus every task's repo that does), forked from
`origin/<tracked>` when that ref exists, else local `<tracked>`. `common.worktree_path` (Python and
shell) moves to the same layout, so `git-worktrees-create`, `-commit`, `-push` and the sweep address the
tree `move in-progress` made. `ticket.py move <epic> in-progress` creates the trees before it moves the
epic, reuses an existing tree, reuses an existing `<epic>` branch, and moves nothing when creation
fails. Alternatives: `.worktrees/<epic>` (rejected: two roots for one lifecycle), creation in
`ticket.py worktrees` (rejected: the lean path and the epic close need the tree without task trees).
(my call, D-b) Serves A2.

### D3: Names are `<epic>-<task>`; collisions are prevented at creation, never parsed around

`worktree_name(epic, task)` returns `<epic>-<task>`, at most 57 characters. Because slugs contain `-`,
a name cannot be split back into epic and task: every consumer reads the epic from the ticket's
location and frontmatter, and the one lookup `ticket_names(root)` maps every epic slug and every
`<epic>-<task>` of every epic to its ticket. `new-epic` refuses a slug equal to any existing
`<epic>-<task>`; `new-task` refuses a task whose `<epic>-<task>` equals any epic slug or another
epic's `<epic>-<task>`. Legacy `<x>--<y>` trees are still recognised by reap so existing workbenches
can clean them. Alternative: keep `--` (rejected: the user wrote single hyphen). (my call, D-c)
Serves A2.

### D4: plan-execute lands each task on `<epic>` inside the run; dependents merge `<epic>`

With `args.epic` and `args.mainCheckout`, a task that is released (clean and verified, or released by
an accept ruling) is landed before any dependent starts: one `workbench:worktree-merger` agent runs
`merge.py --name <epic>-<task> --base <epic> [--repo <repo>] --keep --no-suites --verify <task verify>`
from the main checkout, which rebases the task branch onto `<epic>`, fast-forwards `<epic>` inside the
integration tree and runs the task verify there. Landings are serialised (one at a time per run).
On success the task's verification head becomes the landed head and the return lists it under
`landed`; on failure the task ends with reason `land-failed` (escalated) and its dependents are
`dependency-failed`. A dependent starts by merging `<epic>` once in its own tree instead of each
dependency branch; a cross-repo dependency still "lands with the integration". `args.baseRef` is
the epic branch, so the verifier `--base` and the reviewer merge-base diff exclude dependency text.
Escalated tasks do not land; the orchestrator lands them after a ruling through `continue`'s MERGE
lines (`--base <epic>`), the same merger path. Alternative: keep landing outside the run (rejected:
dependents would still carry dependency text). (my call, D-d; gate question Q1) Serves A2.

### D5: Epic close merges `<epic>` to main, then `move done` removes every tree and branch

Meta mode: after the pass verdict and the full suite on the integration tree, a `worktree-merger`
runs `merge.py --name <epic> --base main --keep`, which rebases `<epic>` onto main (main may have moved
with `chore(ticket)` commits) and fast-forwards main in the main checkout, where main is checked out;
then the full suite runs on main; then `ticket.py move <epic> done` checks every task branch is merged
into `<epic>` and `<epic>` into main, and removes every task tree and branch and the integration tree
and branch. No `-landed` marker branches: tasks are ancestors of `<epic>`, `<epic>` of main. Meta
mode, with or without an `origin` remote, ends at the fast-forwarded local main and the record; this
replaces the meta-mode PR path, and pushing main stays with the user. Component
mode keeps today's MR path from the integration branch; `move done` runs after the MRs merge and
checks `<epic>` against `origin/<tracked>`. Alternative: merge commits into main (rejected: hides a
moved base). (my call, D-e; gate question Q2) Serves A3.

### D6: merge.py lands into whichever worktree has the base checked out

`merge_back` finds the worktree where `<base>` is checked out (`git worktree list --porcelain`): the
integration tree for `--base <epic>`, the main checkout for `--base main`. It rebases onto `<base>`,
fast-forwards there, prunes empty directories there, runs suites and the new `--verify <cmd>` there
(under `suite-lock.sh`), and deletes a cleaned branch from there. It never runs `git checkout` in the
main checkout; a base checked out in no worktree is refused with the command that fixes it. (my call,
D-f) Serves A3 and A2.

### D7: One lifecycle in every doc and the fallback; template only

The root README, AGENTS.md, plugin README, start-development SKILL.md and references, the worktree and
epic skills, the implementer agent and `scripts/harness/fallbacks/plan-execute/SKILL.md` describe
claim, fork, in-run landing, epic close and cleanup the same way; the doc needle tests move with them.
`~/Documents/claude-infra-plugin` is not touched. (my call, D-g) Serves A4.

### D8: An epic that mixes meta and component tasks is refused at claim

The meta integration tree `<configdir>/worktrees/<epic>` and a component tree
`<configdir>/worktrees/<epic>/<repo>` cannot share a directory, and SKILL.md already runs a task
spanning both as two passes. `move in-progress` refuses a mixed epic and says to split it. (my call)
Serves A2.

### D9: Landed trees stay until `move done`; branches are deleted only after an explicit merged check

In-run landing uses `--keep`, so remediation and the epic-close audit still read each task's tree and
branch. The sweep deletes a branch only after it verified that branch is contained in its target
(task branch in `<epic>`, `<epic>` in the trunk), using `git branch -D` so the source checkout's HEAD
does not matter; a failed check leaves tree and branch and lists the reason. (my call) Serves A3.

### D10: Non-epic runs, the legacy `.worktrees/` marker and the cross-epic overlap check stay as they are

A plan-execute run without `args.epic` keeps dependency-branch merges and no landing. The
`.worktrees/` hook marker and `.gitignore` entry stay so trees from older workbenches are still
guarded. `_counting_overlaps` keeps asking whether another epic's task reached main, which is still the
right question for cross-epic overlap. (my call) Serves A2.

## Research

| Lens | Ran or skipped | Adopted ideas | Rejected ideas |
|---|---|---|---|
| research-code-internal | ran: docs/research/epic-worktrees-map.md (local, facts copied above) | reuse create.fast_forward/merge_latest/validate_name, merge.merged_into/_rebase_with_union/cleanup/prune_empty_dirs, ticket._task_merged/_task_src/_linked_worktrees/Sweep, workbench.worktrees_dir, plan-execute repoDir/mergeCommand (map "Plan inputs") | a second worktree root (map E "Layout") |
| research-docs | ran: docs/research/builtin-worktrees.md (Claude Code docs v2.1.305, facts copied above) | plain `git worktree add` gets no hook and no marker (H, W); absolute paths in every prompt (SA, T) | moving trees out of `.claude/worktrees/` (W: the sweep keeps unmarked trees); deny rules (P); `git worktree lock` (W: the sweep never touches unmarked trees) |
| research-code-external | skipped: in-house git plumbing; the docs lens already covered the other harnesses (brief section 5) | none | none |
| research-papers | skipped: no algorithmic or scientific core | none | none |

## Research inputs

| Source | Entry | Lands in |
|---|---|---|
| map Plan inputs | Naming: ticket.py:36,63-67,1247,1457-1463 | single-hyphen-names |
| map Plan inputs | Naming parsers and fallbacks: ticket.py:473,571,1520 | name-lookup-parsers |
| map Plan inputs | Naming: continue_cmd.py:5,122 (MERGE line) | epic-base-wiring |
| map Plan inputs | Naming: plan-execute.js:76,316-326 | plan-execute-epic-names |
| map Plan inputs | Naming docs: worktrees.md:6-12, tickets.md:36,61, worktree-create/SKILL.md:22, plugin README.md:202,217 | docs-worktree-refs, docs-readmes-fallback |
| map Plan inputs | Integration lifecycle: `_move_in_progress` creates the integration tree | integration-tree-create |
| map Plan inputs | `cmd_worktrees --base <epic>`, args.py:99 baseRef, continue_cmd.py:109-123,177 | epic-base-wiring |
| map Plan inputs | `_move_done`/Sweep/cmd_reap (:1231-1264, 1396-1524) | epic-close-sweep |
| map Plan inputs | merge.py merge_back/run_suites/cleanup target worktree, worktree-merge/SKILL.md, worktree-merger.md | merge-target-worktree |
| map Plan inputs | git-worktrees-create superrepo support or a new helper | integration-tree-create (helper in worktree-create), common-worktree-path-py, common-worktree-path-sh |
| map Plan inputs | epic-worktrees-remove/SKILL.md | epic-close-sweep |
| map Plan inputs | Flow docs: SD/SKILL.md, phase-4-execute.md, phases-5-7.md, multi-epic.md | docs-flow-phases |
| map Plan inputs | Flow docs: hooks.md:6-7, implementer.md:26-36 | docs-worktree-refs |
| map Plan inputs | Flow docs: fallbacks/plan-execute/SKILL.md, README.md:198,353, AGENTS.md:201 | docs-readmes-fallback |
| map Plan inputs | Built-in removal and guards (section A), `isolation` in test_repo_hygiene.py:25 | builtin-worktree-guard |
| map Plan inputs | `.claude/worktrees/` co-location decision | rejected: kept by D1 (the built-in only cleans marked trees) |
| map Plan inputs | Tests to update (section C) and new tests for creation, task-to-epic merge, epic-to-main merge, cleanup | every task, per its Files list |
| map Plan inputs | Reuse list | every task's Notes |
| map E risk | `_counting_overlaps` hard-codes main (ticket.py:476) | rejected: kept by D10 |
| map E risk | ticket commits reach main independently of `<epic>` | merge-target-worktree (rebase onto main at close), docs-flow-phases |
| map E risk | hooks treat the integration tree as an agent tree | land-in-run (Notes: the merger reruns the verify after a conflict fix) |
| builtin brief 1 | create with plain `git worktree add` through Bash | builtin-worktree-guard |
| builtin brief 2 | keep plugin trees out of `.claude/worktrees/` | rejected: D1 |
| builtin brief 3 | gitignore the base dir; Glob explicit roots | rejected: already gitignored (.gitignore:42); prompts already pass absolute paths |
| builtin brief 4 | avoid `worktree-*` and `pr-*` branch names | rejected: create.validate_name already refuses an existing branch; a clash needs a user to run `claude -w` with that exact name |
| builtin brief 5 | deny `Agent(isolation:worktree)` and EnterWorktree | rejected: D1, permission surface not requested |
| builtin brief 6 | absolute worktree path in every prompt, `git -C` or same-call `cd` | land-in-run |
| builtin brief 7 | trust, settings, `${CLAUDE_PROJECT_DIR}` resolve to the main checkout | rejected: hooks already read the event cwd (hooks/worktree_lib.py:74-77); no change needed |
| builtin brief 8 | plugin owns cleanup; `git worktree lock` while agents run | epic-close-sweep (cleanup); lock rejected (unmarked trees are never swept) |

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 plain git worktrees, guard tests | builtin-worktree-guard, docs-worktree-refs |
| D2 integration tree path and creation at claim | integration-tree-create, common-worktree-path-py, common-worktree-path-sh, epic-base-wiring |
| D3 `<epic>-<task>` names and collision prevention | single-hyphen-names, name-lookup-parsers, slug-collision-guard, plan-execute-epic-names |
| D4 in-run landing, dependents merge `<epic>` | land-in-run, forward-merge-via-epic, epic-base-wiring |
| D5 epic close and full cleanup | epic-close-sweep, docs-flow-phases |
| D6 merge.py target-worktree mode | merge-target-worktree |
| D7 one lifecycle in every doc | docs-flow-phases, docs-worktree-refs, docs-readmes-fallback |
| D8 mixed epic refused at claim | integration-tree-create |
| D9 landed trees kept, guarded branch deletion | land-in-run, epic-close-sweep |
| D10 non-epic runs and legacy markers unchanged | land-in-run, name-lookup-parsers |

## Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| ticket-name-lookup | name-lookup-parsers | slug-collision-guard, epic-close-sweep | `plugins/workbench/skills/start-development/scripts/ticket.py` |
| integration-tree | integration-tree-create | epic-base-wiring, epic-close-sweep | `plugins/workbench/skills/worktree-create/scripts/create.py` |
| merge-target-worktree | merge-target-worktree | epic-close-sweep, land-in-run | `plugins/workbench/skills/worktree-merge/scripts/merge.py` |
| epic-run-args | epic-base-wiring | land-in-run | `plugins/workbench/skills/start-development/scripts/ticket_cmds/args.py` |
| land-step | land-in-run | forward-merge-via-epic | `plugins/workbench/workflows/plan-execute.js` |

No cross-epic contract: no related epic shares these files (`ticket.py contract list` is empty).

## Review focus

- merge.py: the target-tree lookup, that no path runs `git checkout` in the main checkout, and that a
  failed rebase, fast-forward or verify leaves both trees intact.
- The sweep: a branch is deleted only after its merged check; legacy `--` trees; component trees
  against `origin/<tracked>`.
- plan-execute.js: landings serialised; a dependent never starts before its dependencies landed; a
  ruling-released task lands first; non-epic runs unchanged (existing tests stay green untouched).
- Collision rules in `new-epic` and `new-task`, and that no code splits a name on `-` or `--`.

## Left to the builder

- Helper names and module layout inside ticket.py, create.py and merge.py, within the contracts above.
- The exact guard-test matching rule, as long as the forbidding sentences pass and a fixture line that
  instructs the built-in fails.
- Prompt wording of the land agent, within the AC (absolute paths, one merge.py call, relay its output).

## Assumptions and unknowns

- This epic itself runs on the current, pre-change flow: the installed plugin is the cached version,
  so its tasks are named `epic-integration-worktrees--<task>`, fork from main and land on main through
  `continue`'s MERGE lines. Confirmed by the plugin cache rule (MEMORY: workbench plugin cache version).
- `git worktree list --porcelain` reports `branch refs/heads/<b>` for every worktree with `<b>` checked
  out, so a target tree is found without parsing paths. Confirmed by merge-target-worktree's tests.
- `.mise.toml` trust in a new integration tree behaves as in task trees today; confirmed when the land
  verify runs in the integration tree in land-in-run's tests.
- Claude Code's own handling of `.claude/worktrees/` cleanup is documented, not probed: unmarked trees
  are kept (builtin brief section 2).

## Open questions
- Q1: (D4) inside an epic run, should plan-execute land each clean, verified task on the epic integration branch itself (a worktree-merger dispatch: rebase onto <epic>, fast-forward <epic> in the integration tree, run the task verify there), with dependents merging the updated <epic> and the verifier and reviewer diffing against <epic>, while escalated tasks land only after your ruling? [recommended: yes, land in the run as D4 describes]
- Q2: (D5) at meta-mode epic close, should the flow rebase <epic> onto main and fast-forward main in the main checkout (after the pass verdict and the full suite on the integration tree), run the full suite on main, then have move done remove every task and integration tree and branch, replacing the meta-mode PR path, while component mode keeps the MR path and cleans up after the MRs merge? [recommended: yes, local rebase plus fast-forward for meta mode, MR path unchanged for component mode]

## Irreversible operations in scope

- `git branch -D` of task branches and integration branches during `move done` and `reap`, only after
  the explicit merged check (D9); the commits stay reachable from `<epic>` and main.
- `git worktree remove` (never `--force`) of clean, merged trees during `move done` and `reap`.
- Rebase of task branches onto `<epic>` and of `<epic>` onto main: local, unpushed branches only.
- No force push, no history rewrite of a shared branch, no data deletion.
