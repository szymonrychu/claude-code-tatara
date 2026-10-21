# Tickets: epics and tasks as files

One tool, `skills/start-development/scripts/ticket.py`, creates and moves every ticket. An epic is one
short human page (`README.md`) plus one agent-facing file per task.

## Layout

```
docs/plans/<phase>/<epic>/README.md      human page: brief, description, goals, non-goals, review
docs/plans/<phase>/<epic>/design.md      full path only
docs/plans/<phase>/<epic>/approvals.json the approvals ledger
docs/plans/<phase>/<epic>/tasks/<task>.md agent-facing task files
docs/plans/<phase>/<epic>/rulings.json   orchestrator rulings (ticket.py rule), read by the run
docs/plans/<phase>/<epic>/record.md      written at done
docs/plans/contracts.json                shared contracts across epics (ticket.py contract)
docs/plans/facts.md                      repo facts pack (ticket.py facts), generated, gitignored
docs/plans/index.json                    generated, gitignored
```

- `<phase>` is `todo`, `in-progress` or `done`. The epic directory is the coarse status and moves
  only three times in an epic's life.
- `--root <dir>` overrides `<docs_root>/docs/plans` (tests).
- Legacy `docs/plans/<date>-*` files were removed; only the three phase folders live under `docs/plans/`.
- `ticket.py path <epic> readme|design|approvals|record|tasks` prints the absolute path inside the
  epic's current phase. Every subcommand that takes an epic accepts its slug or its directory.
- Time is report-only: the planner writes `estimate` (minutes, about an hour per task) in each task, `apply-run` writes `actual` from `durationMs`, and `ticket.py tasks` regenerates the README `## Time` section. See `task-fields.md`.

## Subcommands added for the run loop and planning

Each lives in its own module under `skills/start-development/scripts/ticket_cmds/` (`ticket_cmds`):

- `rule`: `rule <epic> --accept|--reject <ids> --reason ...` records rulings in the task files and `rulings.json`.
- `args`: `args <epic> --out-dir <dir>` writes the plan-execute args JSON and its named copy.
- `continue`: `continue <epic> --out-dir <dir>` applies the last return, records rulings, refreshes trees, writes the next args.
  The merge gate exits 2 (exit 2): an accepted task that a still-open task depends on has no merge in the base yet.
  `continue` then prints one line per task, `MERGE <task> --name <epic>-<task> --base <epic> --repo <repo>`, and writes no args file.
  The orchestrator dispatches `workbench:worktree-merger` with those `--name` and `--repo` values, then reruns `continue`
  (the earlier steps are idempotent).
- `contract`: `contract add|use|list` keeps `docs/plans/contracts.json`.
- `graph --todo` checks todo and in-progress epics for blocker cycles and contract order.
- `roadmap`: `roadmap [--json]` lists the epics by phase.
- `facts`: writes `docs/plans/facts.md`.
- `decide`: `decide <epic> <approval_id> <text> --tasks ...` records a user decision (see `approvals.md`).
- `questions`: `questions [--add|--answer]` lists, adds or answers open questions in todo epics.
- `amend`: `amend <epic> <task> --requirement-file ... --reason ...` replaces a task's Requirement and AC.
- `worktrees --refresh` (`worktrees <epic> --refresh`) fast-forwards live, clean trees with nothing ahead of the base.
- `close`: `close <epic> --verify <cmd>` lands `<epic>` on main in a fixed order (every done task contained in `<epic>`,
  rebase, `--verify` on the rebased tip in the integration tree, fast-forward main, `--verify` on main) and writes
  `close.json` (`epic`, `base`, `baseBefore`, `baseAfter`, `epicTip`, `integrationVerify`, `mainVerify`, `at`).
  Exit 2 means a task is not yet contained (MERGE lines), exit 4 a failed verify.
- `worktrees --integration` (`worktrees <epic> --integration`) creates or reuses the integration trees of an epic
  claimed before this change; it makes no task tree.
- `reap --task` (`reap --epic <epic> --task <task>`) reaps one task's merged, clean worktree.

`apply-run` resets a dependency-failed task to the initial status (`todo`) and appends a dated note line
naming the failed dependency, so the next run picks it up; a discovered task carries the finding as its AC.

## Naming

| Thing | Value |
|---|---|
| Epic slug | `slugify(title, 28)`, trailing `-` trimmed; unique across all three phases |
| Task slug | the same rule; unique within its epic |
| Run name and named copy | `<epic>`, giving `plan-execute-<epic>.js` |
| Task `id` and `short` | `<task>` |
| Agent labels | `<epic>:impl:<task>`, `<epic>:verify:<task>#n` |
| Per-task worktree and branch | `<epic>-<task>`, at most 57 characters (28 + 1 + 28) |
| Integration branch and tree | branch `<epic>`; tree `<configdir>/worktrees/<epic>[/<repo>]` |

`ticket.py slug "<title>"` prints a slug. `worktree_name(epic, task)` raises past 57 characters.
Collision rule: `new-epic`, `new-task` and `rename` refuse a slug whose worktree or branch name is taken,
including a name whose tree or branch is still on disk (a legacy double-hyphen tree included), even when no ticket file
carries it; the stop names what is occupying it.
Slug freeze: a slug never changes once the epic leaves `todo/`; `ticket.py` refuses a rename after that.

## Creating an epic: near duplicates

`ticket.py new-epic` runs the dedup check first. A near-duplicate epic (similarity >= 0.6) in `todo/` or
`in-progress/` stops creation: it prints `new-epic: near duplicate <slug> (<score>); pass --force to create anyway`
on stderr, writes and commits nothing, and exits 3 (exit 3 is reserved for this stop). `--force` creates the
epic anyway and still prints the near-duplicate note on stdout. A near duplicate in `done/` is only a note
(a new epic on a finished subject is legitimate). `--force` never overrides a real failure such as a slug clash.
`ticket.py check --title` only lists near duplicates (exit 0), and `new-task` keeps near-duplicate tasks as notes.

## State machines

Epic: `todo` -> `in-progress` -> `done`. Under `in-progress/` the README `stage` is `build`, then
`review`. There is no fourth directory. `ticket.py move <epic> in-progress` sets every todo task to in-progress
(other statuses are left alone), in the same commit.

Task `status` is exactly one of `todo`, `in-progress`, `done`, `blocked`, `escalated`. There is no
parked, deferred or wontfix state: a task is delivered, blocked on a named external blocker, or
escalated.

## Frontmatter

Restricted, parsed by `ticket.py` with no YAML dependency: scalars, single- and double-quoted
strings, and inline lists `[a, b]`. A nested mapping or block list fails with
`<path>:<line>: unsupported frontmatter`. `dump(load(x)) == x` for every file `ticket.py` wrote.

Epic README: `title`, `blockers` (epic titles), `stage`, `owner`, `repos`, `created`. Sections:
Project brief (What/How/Why), Description, Goals, Non-goals, Review.

Task file: `title`, `status`, `repo`, `value`, `files`, `verify`, `depends_on`, `owns`, `uses`,
`model`, `review`, `worktree`, `branch`, `fork_point` (the commit the task forked from, recorded when the task lands: apply-run stores the merge's `baseBefore`),
`verified_head`, `run`, `provides`. Sections: Requirement,
Acceptance conditions (`- <AC-id>: <text> [evidence: <kind>:<ref>]`), Files, Interfaces, Expected
outcome, Steps, Notes.

## Writer rule

Only the orchestrator writes tickets, only through `ticket.py`, only in the main checkout, never on
a task branch. Every mutating subcommand calls `require_main_checkout(root)`, which exits 1 with
`ticket.py: run in the main checkout, not a linked worktree` inside a linked worktree. After a
mutating subcommand succeeds, `commit_ticket_change(epic, event, paths)` commits exactly the
`docs/plans/` paths it wrote as `chore(ticket): <epic> <event>`; unrelated dirty files stay
uncommitted. Outside git both are no-ops.

## Ownership split

- `ticket.py` writes: README frontmatter and the sections it creates, task files, moves and stage
  changes. `decide`, `questions` and `amend` write design.md, approvals.json and task files;
  `rule` writes rulings.json.
- Written directly by the orchestrator or the record-writer, always in the main checkout:
  `record.md`, and `approvals.json` and `design.md` outside those subcommands.

## The `discovered` entry

Work found during a task that is outside its ownership is recorded as `{what, where, why}`: what the
gap is, where it sits (file or repo), and why the task could not fix it. It is never a way to leave
agreed scope undone.
