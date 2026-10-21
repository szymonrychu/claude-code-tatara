# Epic integration worktrees design

## Summary

The workbench flow owns every git worktree it uses with plain `git worktree` commands and gives each
epic one integration worktree. `ticket.py move <epic> in-progress` creates the integration tree
`<configdir>/worktrees/<epic>` on branch `<epic>` (component mode: `<configdir>/worktrees/<epic>/<repo>`
per repo). Task trees are `<epic>-<task>`, fork from `<epic>` and land back on it inside the
plan-execute run, so verifier and reviewer diffs are taken against `<epic>` and never carry a
dependency's text. When the epic passes review and every done task is on `<epic>`, `ticket.py close` rebases
`<epic>` onto main, runs the full suite on the rebased tip and only then fast-forwards main (meta mode;
component mode merges through the MR), and `ticket.py move <epic> done` removes every task and
integration tree and branch, with merged checks that survive the rebase. Template only.

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
epic's `<epic>-<task>`. Names on disk count too (interrogate verdict I): every local branch and every
directory under `<configdir>/worktrees/`, legacy `<epic>--<task>` trees and branches included, so a new
ticket never inherits a stale tree or branch. Legacy `<x>--<y>` trees are still recognised by reap so
existing workbenches can clean them. Alternative: keep `--` (rejected: the user wrote single hyphen).
(my call, D-c) Serves A2, V-I.

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
lines (`--base <epic>`), the same merger path. The continue gate lists EVERY done task not yet on
`<epic>`, not only dependencies of open tasks, so an accepted task with no dependents still lands
before the close (verdict E). The land step treats a task already contained in `<epic>` with a passing
verify as landed, never `land-failed` (verdict C); it tells the merger that a rebase drops a
dependent's merge-of-`<epic>` commit, so it resolves unambiguous re-conflicts and otherwise fails with
the files named (verdict H); and it lands a recorded legacy tree under its recorded name (D13). Diff
bases after landing come from the fork point (D14). Alternative: keep landing outside the run
(rejected: dependents would still carry dependency text). (my call, D-d; gate question Q1) Serves A2,
V-C, V-E, V-H.

### D5: Epic close merges `<epic>` to main, then `move done` removes every tree and branch

Meta mode, in this order (interrogate verdict D, E), main never moving onto an untested tip:
1. Every done task is landed on `<epic>`. `ticket.py continue` prints a MERGE line for each one that is
   not, and `ticket.py close` refuses while any is not.
2. `ticket.py close <epic> --verify '<full suite and lint>'` (new `ticket_cmds/close_cmd.py`) calls
   merge.py's close mode. It rebases `<epic>` onto main inside the integration tree (main always moved
   through `chore(ticket)` commits) and runs the full suite and lint on the rebased tip there.
3. Only when that passes does it fast-forward main in the main checkout, where main is checked out.
4. It runs the full suite on main.
5. It records `close.json` with main's pre-fast-forward SHA.
6. `ticket.py move <epic> done` checks that every task branch is contained in `<epic>` and `<epic>` in
   main (ancestry, else patch equivalence, D9), then removes every task tree and branch and the
   integration tree and branch.
A rebase conflict goes to a `worktree-merger` in the integration tree, then close runs again. No
`-landed` marker branches: tasks are contained in `<epic>`, `<epic>` in main. The close is a ticket.py
command rather than a merger agent alone, because the refusal in step 1 and the summary in step 5 need
the tickets. Meta mode, with or without an `origin` remote, ends at the fast-forwarded local main and the record; this
replaces the meta-mode PR path, and pushing main stays with the user. Component
mode keeps today's MR path from the integration branch; `move done` runs after the MRs merge and
checks `<epic>` against `origin/<tracked>`. Alternative: merge commits into main (rejected: hides a
moved base). (my call, D-e; gate question Q2) Serves A3, V-D, V-E.

### D6: merge.py lands into whichever worktree has the base checked out

`merge_back` finds the worktree where `<base>` is checked out (`git worktree list --porcelain`): the
integration tree for `--base <epic>`, the main checkout for `--base main`. It rebases onto `<base>`,
runs the new `--verify <cmd>` in the rebased tree under `suite-lock.sh` BEFORE anything moves, and only
on a green verify fast-forwards the target, prunes empty directories and runs suites there; a failed
verify never advances the base, and a base that moved in between is rebased onto again and reverified
(at most 3 attempts) (interrogate verdict B). A tree already contained in `<base>` (ancestor or
patch-equivalent) merges nothing but still runs `--verify` in the target tree and reports it (verdict
C). The summary carries `baseBefore`, the base's pre-fast-forward SHA (verdict D). A cleaned branch is
deleted from the target tree. It never runs `git checkout` in the main checkout; a base checked out in
no worktree is refused with the command that fixes it. (my call, D-f) Serves A3, A2, V-B, V-C, V-D.

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
does not matter; a failed check leaves tree and branch and lists the reason. Every merged check (the
continue gate, the move done gate, `Sweep.tree`, merge.py's post-merge check) goes through one
`merge.contained`: ancestry first, then patch equivalence (`git cherry <target> <head>` all `-`),
because after the close rebases `<epic>` onto a moved main no task branch or task-tree HEAD is an
ancestor of `<epic>` (interrogate verdict A). Anything still not equivalent is listed as left with the
reason. (my call) Serves A3, V-A.

### D10: Non-epic runs, the legacy `.worktrees/` marker and the cross-epic overlap check stay as they are

A plan-execute run without `args.epic` keeps dependency-branch merges and no landing. The
`.worktrees/` hook marker and `.gitignore` entry stay so trees from older workbenches are still
guarded. `_counting_overlaps` keeps asking whether another epic's task reached main, which is still the
right question for cross-epic overlap. (my call) Serves A2.

### D11: Gate answer Q1 (user, 2026-10-21: yes): inside an epic run p
Gate answer Q1 (user, 2026-10-21: yes): inside an epic run plan-execute lands each clean, verified task on the epic integration branch (rebase onto <epic>, fast-forward in the integration tree, task verify there); dependents merge the updated <epic>; verifier and reviewer diff against <epic>; escalated tasks land only after a ruling. (user decision)

### D12: Gate answer Q2 (user, 2026-10-21: yes): meta-mode epic close
Gate answer Q2 (user, 2026-10-21: yes): meta-mode epic close rebases <epic> onto main and fast-forwards main in the main checkout after the pass verdict and the full suite on the integration tree, runs the full suite on main, then move done removes every task and integration tree and branch; component mode keeps the MR path and cleans up after the MRs merge. (user decision)

### D13: Epics already in progress upgrade in place

An epic claimed before this change has legacy `<epic>--<task>` trees and no `<epic>` branch.
`ticket.py worktrees <epic> --integration` creates its integration tree through the same
`ensure_integration_trees` step the claim uses. `cmd_worktrees` keeps the recorded worktree and branch
of a live tree whatever its name. plan-execute accepts a recorded legacy `<epic>--<id>` tree, and the
land step and the MERGE lines use the recorded name. The legacy trees then land on `<epic>` like any
other. Alternative: require such epics to finish on the old flow (rejected: a plugin update would strand
them, and this epic itself is one). (interrogate verdict F) Serves A2, V-F.

### D14: Diffs after landing are taken from the recorded fork point

Once a task has landed, `merge-base(HEAD, <epic>)` is the task's own HEAD and the diff is empty. The
land step records the `<epic>` SHA the task was rebased onto (merge.py `baseBefore`) as its fork
point. plan-execute uses it for every later reviewer, verifier and TDD diff of that task (remediation,
audit re-review, forward-merge re-verify). `apply-run` persists it as `fork_point` and `ticket.py args`
passes it back as `forkPoint`. Before landing, the diff stays `merge-base(HEAD, <baseRef>)`.
Alternative: recompute it from git (rejected: not recoverable once `<epic>` moves on). (interrogate
verdict G) Serves A2, V-G.

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
| D3 `<epic>-<task>` names and collision prevention | single-hyphen-names, name-lookup-parsers, slug-collision-guard, plan-execute-epic-names, docs-worktree-refs |
| D4 in-run landing, dependents merge `<epic>` | land-in-run, land-outcomes, forward-merge-via-epic, epic-base-wiring, epic-close-command, merge-target-worktree |
| D5 epic close and full cleanup | epic-close-command, epic-close-sweep, merge-target-worktree, docs-flow-phases, docs-readmes-fallback |
| D6 merge.py target-worktree mode | merge-target-worktree, merge-contained-check |
| D7 one lifecycle in every doc | docs-flow-phases, docs-worktree-refs, docs-readmes-fallback |
| D8 mixed epic refused at claim | integration-tree-create |
| D9 landed trees kept, guarded branch deletion | land-in-run, merge-contained-check, epic-base-wiring, epic-close-sweep, epic-close-command |
| D10 non-epic runs and legacy markers unchanged | land-in-run, name-lookup-parsers |
| D11 Gate answer Q1 (user, 2026-10-21: yes): inside an epic run p | land-in-run, forward-merge-via-epic, epic-base-wiring |
| D12 Gate answer Q2 (user, 2026-10-21: yes): meta-mode epic close | epic-close-sweep, docs-flow-phases |
| D13 epics already in progress upgrade in place | epic-base-wiring, integration-tree-create, single-hyphen-names, plan-execute-epic-names, land-outcomes, docs-flow-phases, docs-readmes-fallback, docs-worktree-refs |
| D14 diffs after landing from the recorded fork point | fork-point-diffs, fork-point-record, forward-merge-via-epic, docs-flow-phases, docs-worktree-refs |

## Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| ticket-name-lookup | name-lookup-parsers | slug-collision-guard, epic-close-sweep | `plugins/workbench/skills/start-development/scripts/ticket.py` |
| integration-tree | integration-tree-create | epic-base-wiring, epic-close-sweep, epic-close-command | `plugins/workbench/skills/worktree-create/scripts/create.py` |
| merge-target-worktree | merge-target-worktree | merge-contained-check, epic-close-sweep, epic-close-command, land-in-run | `plugins/workbench/skills/worktree-merge/scripts/merge.py` |
| epic-run-args | epic-base-wiring | land-in-run | `plugins/workbench/skills/start-development/scripts/ticket_cmds/args.py` |
| land-step | land-in-run | land-outcomes, fork-point-diffs, forward-merge-via-epic | `plugins/workbench/workflows/plan-execute.js` |
| contained-check | merge-contained-check | epic-base-wiring, epic-close-sweep, epic-close-command, land-outcomes | `plugins/workbench/skills/worktree-merge/scripts/merge.py` |
| fork-point | fork-point-diffs | fork-point-record, forward-merge-via-epic | `plugins/workbench/workflows/plan-execute.js` |

No cross-epic contract: no related epic shares these files (`ticket.py contract list` is empty).

## Review focus

- merge.py: the target-tree lookup, that no path runs `git checkout` in the main checkout, and that a
  failed rebase, fast-forward or verify leaves both trees intact.
- The sweep: a branch is deleted only after its merged check; legacy `--` trees; component trees
  against `origin/<tracked>`.
- plan-execute.js: landings serialised; a dependent never starts before its dependencies landed; a
  ruling-released task lands first; non-epic runs unchanged (existing tests stay green untouched).
- Collision rules in `new-epic` and `new-task`, and that no code splits a name on `-` or `--`.
- merge.py: `--verify` runs before every fast-forward, the re-rebase loop is bounded, and no path advances a base on a red or stale verify.
- `ticket.py close`: the refusal while a done task is off `<epic>`, the order rebase, verify, fast-forward, verify on main, and `close.json` carrying main's pre-fast-forward SHA.
- `merge.contained`: patch equivalence is used only after ancestry fails, merge commits are ignored, and a non-equivalent commit is always listed with its reason.
- Fork points: every diff site in plan-execute.js goes through `diffBase(t)`.

## Left to the builder

- The re-rebase cap in merge.py is 3 attempts and `close.json` holds at least the listed keys (my call).
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
- Q1: (D4) inside an epic run, should plan-execute land each clean, verified task on the epic integration branch itself (a worktree-merger dispatch: rebase onto <epic>, fast-forward <epic> in the integration tree, run the task verify there), with dependents merging the updated <epic> and the verifier and reviewer diffing against <epic>, while escalated tasks land only after your ruling? [recommended: yes, land in the run as D4 describes] ANSWERED by the user 2026-10-21: yes.
- Q2: (D5) at meta-mode epic close, should the flow rebase <epic> onto main and fast-forward main in the main checkout (after the pass verdict and the full suite on the integration tree), run the full suite on main, then have move done remove every task and integration tree and branch, replacing the meta-mode PR path, while component mode keeps the MR path and cleans up after the MRs merge? [recommended: yes, local rebase plus fast-forward for meta mode, MR path unchanged for component mode] ANSWERED by the user 2026-10-21: yes.

## Irreversible operations in scope

- `git branch -D` of task branches and integration branches during `move done` and `reap`, only after
  the explicit merged check (D9); the commits stay reachable from `<epic>` and main.
- `git worktree remove` (never `--force`) of clean, merged trees during `move done` and `reap`.
- Rebase of task branches onto `<epic>` and of `<epic>` onto main: local, unpushed branches only.
- The fast-forward of local main by `ticket.py close`: only after the full suite passed on the rebased `<epic>` tip (interrogate verdict D); main's pre-fast-forward SHA is recorded in `close.json`, so the previous main stays named and reachable.
- No force push, no history rewrite of a shared branch, no data deletion.

## Builder check answers

- Main not checked out in any worktree at meta-mode close (detached main checkout): merge.py refuses and prints the exact fix, `git -C <workbench root> switch main`, then the close is re-run; it never checks a branch out on its own. (my call)
- Component-mode close runs a read-only `git fetch origin <tracked>` (fetching is not pushing). With no `origin` or no network it falls back to the local tracked branch and says so in the summary. (my call)
- Mixed meta and component tasks in one epic are refused at claim only; epics already in progress are not re-checked by `continue`. (my call)
- The collision guard checks new names against existing epic slugs, every `<epic>-<task>` name, and legacy `<epic>--<task>` trees and branches still on disk. (my call)
- Landing always runs the task's own `verify` in the integration tree, whatever its review path (process-only or triage-rejected included). (answered by D4)
- `land-failed` escalates the task and its dependents end `dependency-failed` for that run. Recovery: the orchestrator resolves the conflict through `worktree-merger` (or rules on it), and the relaunch from `ticket.py continue` lands the task through the same merger path before its dependents run. (my call)

## Interrogate verdict

Interrogate panel (fable, opus, sonnet), 2026-10-21. Every Act-on item is delivered as requirement
text and at least one acceptance condition in the task that owns the behaviour; ledger items V-A to
V-I track them. No existing acceptance condition was dropped. merge-target-worktree AC4 and AC5 were
reworded by item B: before B, the verify ran after the fast-forward and a failure kept the merge.

| Item | Raised by | Verdict | Delivered by |
|---|---|---|---|
| A | fable, opus, sonnet (fable reproduced it) | After the close rebases `<epic>` onto a moved main, task branches and task-tree HEADs are no longer ancestors, so every merged check falls back to patch equivalence (`git cherry` all `-`); anything not equivalent is left with the reason | D9; merge-contained-check AC1-AC4; epic-base-wiring AC8; epic-close-sweep AC8, AC9; epic-close-command AC6 |
| B | fable, opus, sonnet | merge.py verifies the rebased task tree before fast-forwarding `<epic>`, fast-forwards only on green, re-rebases and re-verifies if `<epic>` moved; a failed verify never advances `<epic>` | D6; merge-target-worktree AC4, AC5, AC9 |
| C | fable, opus, sonnet | The nothing-to-merge path still runs `--verify` in the integration tree and reports it; forward-merge never reports `land-failed` for a dependent already in `<epic>` | D6, D4; merge-contained-check AC5, AC6; land-outcomes AC1; forward-merge-via-epic AC5 |
| D | sonnet, opus | Close order: land every done task, rebase `<epic>` onto main in the integration tree, full suite and lint on the rebased tip, only then fast-forward main, then the full suite on main; the summary records main's pre-ff SHA; docs carry the order | D5; merge-target-worktree AC10; epic-close-command AC4, AC5; docs-flow-phases AC7; docs-readmes-fallback AC6 |
| E | opus | In landing mode the continue gate emits a MERGE line for every done task not in `<epic>`, and the close refuses while one is not | D4, D5; epic-close-command AC1, AC2, AC3; docs-flow-phases AC7 |
| F | opus | Upgrade path for in-progress epics with legacy `<epic>--<task>` trees and no `<epic>` branch: `worktrees --integration`, legacy records kept, plan-execute accepts the legacy tree | D13; integration-tree-create AC10; epic-base-wiring AC2, AC9, AC10; single-hyphen-names AC5; plan-execute-epic-names AC1, AC6; land-outcomes AC4; docs-worktree-refs AC7 |
| G | sonnet | Reviewer and verifier diffs after landing come from the recorded fork point, not `merge-base(HEAD, <epic>)` | D14; fork-point-diffs AC1-AC5; fork-point-record AC1-AC3; forward-merge-via-epic AC6; docs-worktree-refs AC7 |
| H | sonnet | The land step tells the merger to resolve re-conflicts from a dropped merge-of-`<epic>` commit when unambiguous, else `land-failed` naming the files | D4; land-outcomes AC2, AC3; merge-target-worktree AC11 |
| I | sonnet | slug-collision-guard gets an explicit AC for legacy `<epic>--<task>` trees and branches on disk | D3; slug-collision-guard AC7 |
