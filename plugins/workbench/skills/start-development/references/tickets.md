# Tickets: epics and tasks as files

One tool, `skills/start-development/scripts/ticket.py`, creates and moves every ticket. An epic is one
short human page (`README.md`) plus one agent-facing file per task.

## Layout

```
docs/plans/<phase>/<epic>/README.md        human page: brief, description, goals, non-goals, review
docs/plans/<phase>/<epic>/design.md        full size only
docs/plans/<phase>/<epic>/tasks/<task>.md  agent-facing task files
docs/plans/<phase>/<epic>/close.json       written by `ticket.py close`
docs/plans/<phase>/<epic>/record.md        written by record-writer at phase 7
docs/plans/<phase>/<epic>/RETRO.md         `ticket.py retro` (Tasks, Deltas) and retro-writer, phase 7
docs/plans/index.json                      generated, gitignored
```

- `<phase>` is `todo`, `in-progress` or `done`. The epic directory is the coarse status and moves only
  twice in an epic's life.
- `--root <dir>` overrides `<docs_root>/docs/plans` (tests).
- Legacy `docs/plans/<date>-*` files were removed; only the three phase folders live under `docs/plans/`.
- `ticket.py path <epic> readme|design|record|retro|tasks` prints the absolute path inside the epic's current
  phase. Every subcommand that takes an epic accepts its slug or its directory.

## Subcommands

Core in `ticket.py`, the rest one module each under `skills/start-development/scripts/ticket_cmds/`
(`ticket_cmds`):

- `slug`, `new-epic`, `new-task`, `rename`, `path`: create and name tickets (`new-task` takes
  `--requirement-file`, `--ac-file` and `--points N`).
- `check`, `index`, `existing`: near-duplicate check, the generated index, the files done tasks built.
- `tasks`: `tasks <epic>` prints the tasks as JSON in dependency order (every dependency before its
  dependents; a cycle exits 1); each carries `points`, `expected_minutes` and `expected_tokens` (numbers,
  or null when unset).
- `task`: `task <epic> <task> --status <s> [--verified-head <sha>] [--note <text>] [--points-actual N]
  [--logs DIR]` records a task's outcome; the note is appended under `## Notes` as a dated line.
  `--status done` needs `--points-actual N` (Fibonacci, the reviewer's `pointsActual`; refused with any
  other status) and stamps `points_actual` plus the actuals measured from the task's `.logs/agents`
  records (`--logs` overrides the main checkout's `.logs`): `actual_minutes` (first start to last end
  across its agents, ceiling minutes), `actual_tokens` (every agent, every round), and per role
  `actual_roles` and `actual_role_tokens` (`impl N, review N`; a role's minutes sum its agents' spans).
  With no records it first backfills the epic's records from the harness transcripts (`--transcripts DIR`,
  default the project's dir under the harness home), and only then stamps `points_actual` alone and notes
  `actuals: no agent records`, never a guess.
- `actuals`: `actuals <epic> --backfill [--transcripts DIR] [--refresh] [--logs DIR]` writes the
  `.logs/agents` records the recorder hook missed, from the marked (`[wb <epic>/<task>/<role>]`) subagent
  transcripts still on disk (the harness deletes them after about 30 days), with the hook's summariser and
  record format. It keeps existing records unless `--refresh`, skips unmarked transcripts, and prints one
  line per record written: `<agentId> <epic>/<task>/<role> <minutes> <tokens>`.
- `move`: `move <epic> in-progress` claims the epic, sets every todo task to in-progress and creates the
  integration tree; `move <epic> done` needs the pass verdict, every task done and the epic on main, then
  removes the integration tree and branch.
- `stage`: `stage <epic> review|build` (`review` refuses while a task is not done).
- `review`: `review <epic> --verdict pass|fail --notes-file <f>` writes the README Review section.
- `lint`: `lint [<epic>]` checks statuses, dependencies, cycles, every task's Requirement, acceptance
  conditions, `verify` and `files`, its points, minutes, tokens and roles fields (todo and in-progress
  epics), and design.md's Decision coverage; prints `lint: ok`.
- `amend`: `amend <epic> <task> --requirement-file ... [--ac-file ...] --reason ...` replaces a task's
  Requirement and acceptance conditions and notes why.
- `questions`: `questions [--add <epic> <q> --recommended <a>|--answer <epic> <qid> <text>]` lists, adds
  or answers open questions in todo epics (design.md's Open questions).
- `roadmap`: `roadmap [--json]` lists the epics by phase with what blocks each.
- `worktrees`: `worktrees <epic>` creates or reuses the integration trees of an epic claimed earlier;
  `worktrees <epic> --refresh` fast-forwards each clean tree with nothing ahead of the base.
- `close`: `close <epic> --verify <cmd>` rebases `<epic>` onto main in the integration tree, runs
  `--verify` on the rebased tip there, fast-forwards main only when it passed, then runs `--verify` on
  main, and writes `close.json` (`epic`, `base`, `baseBefore`, `baseAfter`, `epicTip`,
  `integrationVerify`, `mainVerify`, `at`). A failed verify is exit 4; main does not move. Component mode
  closes through the MR instead.
- `reap`: `reap --epic <epic> [--dry-run]` removes a done epic's merged, clean trees.
- `retro`: `retro <epic> [--logs DIR] [--transcripts DIR]` (epic in-progress or done) writes RETRO.md
  from templates/retro.md: the Tasks table in delivery order (the `chore(ticket): <epic> task <slug> done`
  commits, oldest first; tasks never marked done follow by the committer date of their `verified_head`,
  oldest first, and a `verified_head` that is empty, unknown or not a sha leaves its task with the rest, in dependency order) with task title, points
  (planned), points (post-delivery), minutes (expected), minutes (actual), tokens (expected), tokens
  (actual) and a totals line, and the Deltas section (per task the points difference and the minutes and
  tokens ratios, actual over expected, then the MdAPE per metric). Empty actual minutes and tokens come from
  the task's `.logs/agents` records (read once per epic and backfilled from the harness transcripts at most once, when a task has none), a
  missing `points` from a Notes line `Estimate: <n> points`; anything else missing reads `not recorded`.
  Both sections sit between `<!-- retro:generated:begin -->` and `<!-- retro:generated:end -->`; a rerun
  regenerates only that block, keeps the Retro and Improvements sections retro-writer fills, refuses a
  file without exactly one block, and commits exactly RETRO.md as `chore(ticket): <epic> retro`. Task
  files are never written. `retro --history [--limit N]` prints, as JSON (`epic`, `retro`,
  `improvements`), the Retro and Improvements sections of the N (default 5) most recently done epics
  (by their `move done` commit) that have a RETRO.md.
- `deltas`: `deltas <epic> | --all [--buckets] [--json] [--logs DIR]` is read-only (writes no file,
  makes no commit). `deltas <epic>` prints per task, in retro's delivery order and with retro's values
  (existing `.logs/agents` records are read, never backfilled), planned, actual, difference (actual -
  planned) and ratio (actual / planned) for points (`points` vs `points_actual`), minutes
  (`expected_minutes` vs `actual_minutes`) and tokens (`expected_tokens` vs `actual_tokens`), then the
  MdAPE per metric; a missing value reads `not recorded`. `--all` does that for every done epic and
  adds the MdAPE over all of them. A task without `points` whose two legacy minutes keys (planned and
  `actual`, from before points) are whole numbers is a minutes-only row marked `(legacy)`: it counts
  toward the minutes MdAPE, is never bucketed by points and is never written. `--buckets` prints the
  per-points table the next `new-task` uses (`calibration.bucket_table` over the done tasks with points
  and both actuals: points, minutes, tokens, n, source). `--json` prints any mode as JSON (`epic`,
  `rows`, `mdape`; `--all`: `epics`, `mdape`; `--buckets` alone: the table keyed by points, else under
  `buckets`).

## Naming

| Thing | Value |
|---|---|
| Epic slug | `slugify(title, 28)`, trailing `-` trimmed; unique across all three phases |
| Task slug | the same rule; unique within its epic; the task's id everywhere |
| Integration branch and tree | branch `<epic>`; tree `<configdir>/worktrees/<epic>[/<repo>]` |

`ticket.py slug "<title>"` prints a slug. Collision rule: `new-epic`, `new-task` and `rename` refuse a
slug whose branch or worktree name (epic plus task, at most 57 characters) is taken, including a name
still on disk with no ticket file carrying it; the stop names what holds it. Slug freeze: a slug never
changes once the epic leaves `todo/`.

`new-epic` runs the near-duplicate check first: a near duplicate (similarity >= 0.6) in `todo/` or
`in-progress/` stops creation with exit 3 (reserved for this stop) and writes nothing; `--force` creates
anyway. One in `done/` is only a note. `check --title` only lists near duplicates (exit 0).

## State machines

Epic: `todo` -> `in-progress` -> `done`. Under `in-progress/` the README `stage` is `build`, then
`review`; `stage build` sends it back.

Task `status` is exactly one of `todo`, `in-progress`, `done`, `blocked`, `escalated`. There is no parked,
deferred or wontfix state: a task is delivered, blocked on a named external blocker, or escalated after
two fix rounds for the orchestrator's judgement. The epic cannot close while a task is not `done`.

## Frontmatter

Restricted, parsed by `ticket.py` with no YAML dependency: scalars, single- and double-quoted strings, and
inline lists `[a, b]`. A nested mapping or block list fails with `<path>:<line>: unsupported frontmatter`.
`dump(load(x)) == x` for every file `ticket.py` wrote. Older done epics keep their extra keys; the loader
reads them and nothing writes them.

Epic README: `title`, `blockers` (epic titles), `stage`, `owner`, `repos`, `created`. Sections: Project
brief (What/How/Why), Description, Goals, Non-goals, Review.

Task file, eighteen keys: title, status, repo, value, files, verify, depends_on, model, review, verified_head,
points, expected_minutes, expected_tokens, points_actual, actual_minutes, actual_tokens, actual_roles,
actual_role_tokens.
- `value`: one line, what this task is worth to the user; required.
- `files`: every file the task may touch. `verify`: the targeted test and lint command (named test
  files or a component suite plus lint, never the full suite); the reviewer runs it on HEAD.
- `depends_on`: the tasks whose commits it builds on. `model`: opus when the task adds a module or
  touches more than five files, else sonnet; the reviewer and scope auditor run on sonnet.
- `verified_head`: the commit the reviewer verified, written by `ticket.py task --verified-head`.
- `points`: Fibonacci storypoints (1, 2, 3, 5, 8, 13), the planner's one number, from
  `new-task --points N`; any other value exits 1 and writes nothing.
- `expected_minutes`, `expected_tokens`: filled by `new-task` from `calibration.expected(points, rows)`
  (`scripts/lib/calibration.py`). The rows are every done task with integer `points`, `actual_minutes`
  and `actual_tokens`: the median of that points bucket at 3 rows, a least-squares line over points at 5
  rows overall, else the seed table.
- `points_actual`, `actual_minutes`, `actual_tokens`: what the task really took, written when it is done;
  they start empty. `actual_roles` and `actual_role_tokens`: minutes and tokens per role, `impl N,
  review N`.
- `lint` checks these fields when set: `points` and `points_actual` Fibonacci, the minutes and tokens
  whole numbers >= 0, the roles `impl N, review N`. Values load as strings. Done epics are not checked.

Sections: Requirement (verbatim, every acceptance condition, never a summary), Acceptance conditions,
Files, Interfaces, Expected outcome, Steps, Notes. An acceptance condition is `- <AC-id>: <text>
[evidence: <kind>:<ref>]` with kind one of `test`, `symbol`, `command`, `doc-section`, `judgement`. A
`test:<file>::<name>` ref runs with its package's runner from the package root (the nearest
`pyproject.toml`, `package.json` or `package.xml`) or a `refRunners` entry (`workbench-config.md`); with
no runner, use a `command:` ref.

A retirement test (one that pins a removal) asserts on `git ls-files <path>`, never on the filesystem,
because an untracked empty directory can survive a merge. The TDD exception for a deletion is narrow: the
diff's non-test changes are deletions only and a test pins the removal; the implementer names it as
"deletion pinned by a retirement test".

## Writer rule

Only the orchestrator writes tickets, only through `ticket.py`, only in the main checkout, never on the
epic branch. Every mutating subcommand calls `require_main_checkout(root)`, which exits 1 with `ticket.py:
run in the main checkout, not a linked worktree` inside a linked worktree. After it succeeds,
`commit_ticket_change(epic, event, paths)` commits exactly the `docs/plans/` paths it wrote as
`chore(ticket): <epic> <event>`; unrelated dirty files stay uncommitted. Outside git both are no-ops.
`design.md`, `record.md` (record-writer) and RETRO.md's Retro and Improvements (retro-writer) are written
directly, in the main checkout.

## The `discovered` entry

Work an implementer finds outside its task's files is returned as `{what, where, why}`: what the gap is,
where it sits (file or repo), and why the task could not fix it. The orchestrator adds it as a new task in
the same epic with `ticket.py new-task --points <n>`. It is never a way to leave agreed scope undone.
