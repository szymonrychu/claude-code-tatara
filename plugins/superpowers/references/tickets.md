# Tickets: plans as files

One tool, `${CLAUDE_PLUGIN_ROOT}/scripts/ticket.py`, creates and moves every plan. A plan is one
directory: what and why with a scope ladder, the implementation plan for the agreed rung, and a retro.

## Layout

```
docs/plans/<phase>/<plan>/plan.md                 what and why, scope ladder, agreed scope, decisions
docs/plans/<phase>/<plan>/implementation-plan.md  agreed rung only, chunks of steps, final verify
docs/plans/<phase>/<plan>/retro.md                written by the reviewer when the review passes
docs/plans/<phase>/<plan>/close.json              written by `ticket.py close` (meta mode)
```

- `<phase>` is `todo`, `in-progress` or `done`. The plan directory is the coarse status and moves
  only twice in a plan's life.
- `--root <dir>` overrides `<docs_root>/docs/plans` (tests).
- `ticket.py path <plan> plan|implementation|retro|close` prints the absolute path inside the plan's
  current phase. Every subcommand that takes a plan accepts its slug or its directory.
- A directory that holds an old-format README.md and no plan.md is refused by every command except
  `migrate`, with a pointer to `ticket.py migrate --all`; no command reads the old format.

## Subcommands

Core in `ticket.py`, the rest one module each under `${CLAUDE_PLUGIN_ROOT}/scripts/ticket_cmds/`
(`ticket_cmds`):

- `slug`: `slug "<title>"` prints the slug.
- `new`: `new --title <t> [--repos a,b] [--force]` runs the near-duplicate check, then writes plan.md
  from templates/plan.md into `todo/` with `rung` empty.
- `check`: `check --title <t>` only lists near duplicates.
- `path`: prints the path of plan.md, implementation-plan.md, retro.md or close.json.
- `rename`: `rename <plan> <title>` renames a plan in `todo/` only.
- `move`: `move <plan> in-progress` is refused unless plan.md `rung` is set and implementation-plan.md
  exists (the gate passed); it creates the integration tree, moves the dir and sets the owner.
  `move <plan> done` is refused unless the plan is in-progress, retro.md exists and the branch is
  contained in its trunk; it removes the tree and branch.
- `worktrees`: `worktrees <plan>` creates or reuses the plan's trees; `worktrees <plan> --refresh`
  fast-forwards each clean tree with nothing ahead of the base.
- `close`: `close <plan> --verify <cmd>` (meta mode) needs retro.md, rebases `<plan>` onto main in the
  plan tree, runs `--verify` on the rebased tip there, fast-forwards main only when it passed, runs
  `--verify` on main, writes `close.json` (`plan`, `base`, `baseBefore`, `baseAfter`, `planTip`,
  `integrationVerify`, `mainVerify`, `at`), moves the plan to done and sweeps its tree. A failed verify
  is exit 4; main does not move. Component mode closes through the MR, then `move <plan> done`.
- `reap`: `reap --plan <plan> [--dry-run]` removes a done plan's merged, clean trees; without `--plan`
  it sweeps every done plan.
- `migrate`: `migrate <epic-dir> | --all [--dry-run]` converts old-format directories to plan.md,
  implementation-plan.md and retro.md, keeping the phase folder. In-progress and done plans get `rung`
  "1"; todo plans get `rung` empty and Agreed scope "not agreed yet", so each passes the gate before it
  is claimed. The goals become one rung, `Rung 1: agreed scope (migrated)`; every section without a home
  is kept under `## Migrated notes`. Every directory is parsed before anything is written; a real run
  commits each plan alone as `chore(ticket): <plan> migrate`.

Retired with the task flow: task creation, status, amendment, lint, stage, review, roadmap, questions,
actuals, deltas, retro tables, the index. Questions live in plan.md and are answered at the gate.

## Naming

| Thing | Value |
|---|---|
| Plan slug | `slugify(title, 28)`, trailing `-` trimmed; unique across all three phases |
| Integration branch and tree | branch `<plan>`; tree `<configdir>/worktrees/<plan>[/<repo>]` |

Collision rule: `new` and `rename` refuse a slug whose branch or worktree name is taken, including a
name still on disk with no plan file carrying it; the stop names what holds it. Slug freeze: a slug
never changes once the plan leaves `todo/`.

`new` runs the near-duplicate check first: a near duplicate (similarity >= 0.6) in `todo/` or
`in-progress/` stops creation with exit 3 (reserved for this stop) and writes nothing; `--force`
creates anyway. One in `done/` is only a note.

## State machine

`todo` -> `in-progress` -> `done`. The gate is mechanical: `move in-progress` needs an agreed rung and
an implementation plan; `close` and `move done` need retro.md, which the reviewer writes only when the
review passes.

## Frontmatter

Restricted, parsed by `ticket.py` with no YAML dependency: scalars, single- and double-quoted strings,
and inline lists `[a, b]`. A nested mapping or block list fails with `<path>:<line>: unsupported
frontmatter`. plan.md keys: title, repos, created, owner, rung (the agreed rung number, empty before the
gate). Sections: What and why, Scope ladder, Agreed scope, Non-goals, Design, Decisions, Open
questions, Research, Irreversible operations. implementation-plan.md and retro.md have their own
templates under `templates/`.

A retirement test (one that pins a removal) asserts on `git ls-files <path>`, never on the filesystem,
because an untracked empty directory can survive a merge. The TDD exception for a deletion is narrow:
the diff's non-test changes are deletions only and a test pins the removal; the implementer names it
as "deletion pinned by a retirement test".

An implementation-plan step's `Test first` and `Verify` refs: a test is named by file and test name and
runs with its package's runner from the package root (the nearest `pyproject.toml`, `package.json` or
`package.xml`) or a `refRunners` entry (`workbench-config.md`); with no runner, use a command.

## Writer rule

Only the orchestrator and the plan-writer write under `docs/plans/`: ticket.py for creation and moves,
only in the main checkout, never on the plan branch. Every mutating subcommand refuses inside a linked
worktree (`ticket.py: run in the main checkout, not a linked worktree`). After it succeeds it commits
exactly the `docs/plans/` paths it wrote as `chore(ticket): <plan> <event>`; unrelated dirty files stay
uncommitted. The plan-writer commits plan.md and implementation-plan.md as `docs(plan): <plan> <event>`;
the reviewer writes retro.md, which ticket.py commits with the move to done.

## The `discovered` entry

Work an implementer finds outside its plan's steps is returned as `{what, where, why}`: what the gap
is, where it sits (file or repo), and why the steps could not fix it. It is never built in the same
plan; the reviewer relays it in retro.md's Recommendations.
