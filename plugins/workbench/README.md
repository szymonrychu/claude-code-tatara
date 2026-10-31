# workbench - core plugin

The tooling for any workbench tree, whether the tree is a metarepo or a flat set of sibling
repos: the agents the development flow dispatches, research skills, worktrees, submodules, pull
requests, releases, and hooks that guard destructive commands and tie every test run to the
committed HEAD. The development flow itself (discovery, a plan with a scope ladder behind one
approval gate that picks the rung, unattended execution with one implementer per chunk and one
reviewer on the whole diff, who writes the retro) is the `superpowers` plugin:
`brainstorming`, `writing-plans`, `subagent-driven-development`,
`finishing-a-development-branch`, `requesting-code-review`, `receiving-code-review` and
`systematic-debugging`.

## Install

The plugin ships inside the workbench template (`plugins/workbench/`) and is listed in
the template's root marketplace (`.claude-plugin/marketplace.json`). Project settings
enable it, so in Claude Code there is nothing to install: open the clone, accept the
trust dialog once, and the root marketplace loads the plugin. After editing the plugin,
run `/reload-plugins`.

Other harnesses use the same files after `mise run harness-setup -- <target>` (or `all`); the hook adapter
(`hooks/adapter.py`) runs the same guard logic for them.

## Packs

Anything specific to one kind of work lives in an optional pack behind the same root
marketplace. A pack needs this core and is enabled in `.claude/settings.json`.

| Pack | Adds |
|---|---|
| `workbench-infra` | Terraform and Helm agents that plan and diff without applying |
| `workbench-observability` | cluster health agent and log and metrics investigation skills |
| `workbench-secrets` | encrypted-secret and environment loading skills |

Each pack has its own README. The agents and skills in the packs are not part of this
core, and the tables below list only what the core ships.

## The trees it targets

| shape | marks | components |
|---|---|---|
| metarepo | `.gitmodules` plus `code/` | one submodule per component at `code/<component>` |
| flat | an instruction file plus sibling repos | repos named `<project>-<component>` next to each other |

The forge (GitHub or GitLab) is picked per repo from its `origin` remote; a component
with no remote is reported, never assumed.

## Python floor for hooks

The Claude Code hooks run under whatever bare `python3` is on PATH, so they import and work
on python 3.9+ (no `match`, no runtime `X | Y` unions, `tomllib` is imported lazily and only
where `pyproject.toml` is read). The deny hooks (`guard-bash`, `protect_files`) exit 2 with a
one-line reason on an interpreter older than 3.9 instead of crashing, because exit 1 does not
block. `hooks/tests/test_py39_safe.py` pins this.

## Nothing hardcodes a path

`scripts/lib/workbench.py` finds the tree and resolves components inside it:

```bash
python3 scripts/lib/workbench.py root          # walk up from cwd
python3 scripts/lib/workbench.py kind          # metarepo | flat
python3 scripts/lib/workbench.py components    # name<TAB>path
python3 scripts/lib/workbench.py resolve api
python3 scripts/lib/workbench.py doctor        # branches + NO REMOTE warnings
```

Resolution order: `$WORKBENCH_ROOT`, then `$CLAUDE_PROJECT_DIR`, then walking up from
the cwd. `resolve` also matches by suffix, so one name works in both shapes:

| shape | `resolve api` |
|---|---|
| metarepo | `code/api` |
| flat | `<project>-api` |

Every agent and script goes through this, so a new tree needs no code change.

## Agents

Read-only, except `reviewer` (one file, retro.md, when the review passes), `implementer` (code in the plan tree),
`worktree-merger` (a conflicted rebase and the landing) and the `research-*` agents (a brief at their output path).
Mechanical ones on sonnet (they exist to keep large output out of the main context);
research ones on opus (they exist for judgement). The reviewers carry no model of their own:
the caller sets it per call.

| Agent | Model | Does |
|---|---|---|
| `scm-shepherd` | sonnet | MR/PR + pipeline status; picks `glab` or `gh` from the remote |
| `submodule-auditor` | sonnet | which submodule pins are stale, unpushed, detached, or remote-less |
| `codebase-cartographer` | opus | maps an unfamiliar repo before design: entrypoints, boundaries, where a change lands |
| `security-researcher` | opus | secrets, RBAC, container privilege, supply chain, CVE surface |
| `architect-researcher` | opus | design research that ends in a decision, not a table |
| `reuse-hunter` | sonnet | finds parts a plan would rebuild, near-duplicate helpers and hot spots; returns a shared-parts map |
| `implementer` | sonnet | implements one chunk of an implementation plan test-first in the plan tree and returns `complete`, `undelivered`, `discovered`; fix rounds continue it |
| `reviewer` | per call | one reviewer on the whole diff: verify on HEAD, under- and over-delivery, debt markers, quality; writes retro.md on a pass |
| `panel-reviewer` | per call | one member of a multi-model review panel, such as brainstorming's builder review, one per model |
| `worktree-merger` | sonnet | lands a plan: `ticket.py close` (resolving a rebase conflict in the plan tree) or the MR |
| `research-docs-purist` | sonnet | official docs at the installed version, anti-patterns in our usage |
| `research-practitioner` | sonnet | field experience and known failure modes |
| `research-prior-art-scout` | sonnet | similar open-source projects, shapes and dead ends |
| `research-paper-scout` | sonnet | literature for the algorithmic core, cited by DOI or arXiv id |
| `research-reviewer` | sonnet | adversarial check of research briefs |

`scm-shepherd` decides per repo from `remote get-url`, so one agent serves GitHub and GitLab trees.

`submodule-auditor` is the one capability with no analogue elsewhere. Metarepo pins never
advance on their own - `git submodule update --remote` is manual - so a workbench
can sit weeks behind while looking clean, and every tool run against it reports
stale reality as fact.

### Where the skills dispatch them

Agents are wired in as **conditional** steps - each fires on a trigger, not on
every pass, so routine work doesn't pay for them:

| Caller | Agent | Trigger |
|---|---|---|
| `superpowers:brainstorming` | `codebase-cartographer` | mapping a repo in scope (a discovery lane) |
| `research-code-internal` | `reuse-hunter` | the reuse hunt |
| `superpowers:brainstorming` | `architect-researcher` | >1 viable approach, or an expensive-to-reverse choice |
| `research-docs` | `research-docs-purist` | official docs of every library in scope |
| `start-research` | `research-practitioner` | field experience, known failure modes |
| `research-code-external` | `research-prior-art-scout` | similar open-source projects |
| `research-papers` | `research-paper-scout` | literature for an algorithmic core |
| `start-research` | `research-reviewer` | adversarial check of every research brief |
| `superpowers:subagent-driven-development` | `implementer` | every chunk, in the background |
| `superpowers:subagent-driven-development` | `reviewer` | the whole diff, after the last chunk and after each fix round |
| `superpowers:subagent-driven-development` | `security-researcher` | diff touches secrets, RBAC, exposure, privilege, CI, or hooks |
| `superpowers:finishing-a-development-branch` | `worktree-merger` | landing the plan: `ticket.py close` or the MR |
| `references/merge-hosts.md` | `scm-shepherd` | a pipeline failed and the cause is not in the log tail |
| a multi-model review | `panel-reviewer` | a review panel, one agent per model |
| `git-submodules-refresh` | `submodule-auditor` | checkout state unknown before refreshing |

Two rules hold throughout: no agent replaces an approval gate
(`architect-researcher` informs a design the user still approves;
`security-researcher` produces findings you still judge), and none of them can
merge, push, or apply - those stay in the calling thread. The pack agents
(see Packs) add their own rows to the same phases when the pack is enabled.

## Skills

```
_lib                            shared python/bash helpers
init                            turn the template into a new project or adopt existing repos, through the tested engine
template-update                 update an initialised workbench from the template, keeping its own docs, in one local commit
component-add, component-remove add a component as a submodule with its origin / remove one only when nothing is lost
handoff                         write a handoff file so multi-day work resumes in a fresh session
git-submodules-add, git-submodules-refresh   submodule lifecycle
git-worktrees-create, git-worktrees-commit, git-worktrees-push
pullrequests-update, pullrequests-watch, pullrequests-list, pullrequests-review-loop   host-agnostic: GitHub (gh) or GitLab (glab) per repo from origin
start-research                  several research lenses at once, briefs ending in Plan inputs
worktree-create, worktree-merge
release                         judge major/minor/patch from commits, write CHANGELOG, bump plugin.json and marketplace.json, commit and tag locally (never pushes)
research-code-internal          plan adds a helper/reader/parser/schema field/subsystem, or a repo has > ~200 source files
research-code-external          the change has known analogues (protocol, parser, scheduler, cache, auth flow, rules engine) or an open design fork
research-papers                 the problem has a scientific or algorithmic core, or the user names a paper
research-docs                   a library, framework, provider or platform API is used in a new way, upgraded, or touched in >= 3 call sites
```

`init` is the entry point of a fresh clone: it asks the questions, confirms any forge
creation, runs the engine through `mise run init:new` or `mise run init:adopt`, generates the
harness files and fills the project block of `AGENTS.md`. `component-add` and
`component-remove` wrap `mise run component`. `template-update` wraps `mise run init:update`:
it fetches the template, merges its tooling, keeps the instance-owned docs and pushes nothing.

The flow (`superpowers:brainstorming`) has one gate, up front, after plan.md and its scope ladder
are written; it may batch several plans, a section and a worktree each. The answer picks the rung;
`writing-plans` then writes implementation-plan.md for that rung only, and everything after runs
unattended through `subagent-driven-development` and ends with retro.md. The four `research-*`
skills are optional inputs to that gate; their briefs go to the plan writer brainstorming
dispatches with `plan-writer-prompt.md`.

One flow serves both tree shapes; the host (GitLab or GitHub) is picked per repo in references/merge-hosts.md.

## Documents

Every plan is a file-based ticket under `docs/plans/{todo,in-progress,done}/<plan>/`:

```
docs/plans/{todo,in-progress,done}/<plan>/plan.md                 what and why, scope ladder, agreed scope
                                          implementation-plan.md  the agreed rung only, chunks of steps
                                          retro.md                written by the reviewer when the review passes
                                          close.json
docs/research/                               research briefs
```

`plugins/superpowers/scripts/ticket.py` creates and moves plans between the three folders. `ticket.py new` writes plan.md from the template after the near-duplicate check, `ticket.py check` lists near duplicates, `ticket.py path` prints a plan file's path, `ticket.py rename` renames a plan in todo, `ticket.py move <plan> in-progress` is refused until plan.md has an agreed `rung` and implementation-plan.md exists (the gate is mechanical) and then creates the plan tree on branch `<plan>`, and `ticket.py move <plan> done` needs retro.md and a merged branch, then removes the tree and branch. Every step commits in the plan tree in order, and the plan merges to main once at close (`ticket.py close <plan>`: rebase onto main, full suite and lint on the rebased tip, fast-forward only when green). Plain `git worktree` is used throughout, never the harness's built-in worktree feature. Further commands (sibling modules in `scripts/ticket_cmds/`): `ticket.py worktrees --refresh` brings a plan tree up to date, `ticket.py reap --plan <plan>` reaps a done plan's leftover worktrees, and `ticket.py migrate <old-dir> | --all [--dry-run]` converts old-format directories to plans with one `chore(ticket): <plan> migrate` commit each (`ticket.py migrate --all` converts every one), and `ticket.py slug` prints a title's slug. Research paths come from `skills/start-research/scripts/doc_path.sh <kind> "<topic>"`.
Plans follow `plugins/superpowers/templates/`.

### Per-repo config

`.claude/workbench.json` holds the per-repo settings read by `scripts/lib/workbench.py`: `refRunners` (glob to command for a test ref in a step), `suites`, `deploy` (hook run after merge) and `overlapIgnore` (paths ignored by the overlap rule). Keys and defaults: `references/workbench-config.md`.

### Background dispatches and user steps

`subagent-driven-development` dispatches each implementer and reviewer in the background; the completion notification is the wake signal, so the session stays free to plan another plan. A command only the user can run (reboots, firmware) becomes a user-run step: `scripts/user-run-step.py` checks state before and after and parses the pasted result (`references/user-run-steps.md`).

Releases go through the `release` skill: `skills/release/scripts/release.py --dry-run` previews the judged bump and changelog section; a real run bumps `plugin.json` and the `workbench` entry of the root `.claude-plugin/marketplace.json`, prepends `plugins/workbench/CHANGELOG.md`, commits `chore(release): vX.Y.Z` and tags it locally.

## The plan loop

- **Plans**: file-based plans (above), `ticket.py`, one plan tree per plan, retro.md before done, the tree and branch removed on done.
- **Execution**: `subagent-driven-development` runs the chunks in order in the plan tree, one implementer per chunk; one reviewer reads the whole diff for under-delivery and over-delivery, at most two fix rounds that continue the same agents, then writes retro.md; `undelivered` is a finding and `discovered` is recommended, never built; the worktree-merger lands it.
- **Discovery**: discovery uses LSP and grep, with no graph probe; LSP first for symbols and references, then grep.

Both SCM families ship deliberately. They are parallel implementations, not drift.

## Hooks

| Hook | Event | Does |
|---|---|---|
| `guard-bash.py` | PreToolUse/Bash | denies destructive commands with an actionable reason (advisory guardrail, not a sandbox) |
| `bash-output-filter.py` | PreToolUse/Bash | caps noisy test/log output before it reaches context |
| `protect_files.py` | PreToolUse/Edit,Write | blocks edits to secrets, state files, `.git`, encrypted-secret files |
| `format-file.sh` | PostToolUse/Edit,Write | formats the edited file with the formatter for its language when one is installed |
| `verify-recorder.py` | PostToolUse and PostToolUseFailure/Bash | records the HEAD and tree state of every test or lint run in an agent worktree |
| `subagent-commit-guard.py` | SubagentStop | blocks a turn that leaves uncommitted work, and also blocks a turn whose last verification did not run on HEAD |
| `agent-usage-recorder.py` | SubagentStart and SubagentStop | records each subagent's time, model and tokens to `.logs/agents/<agentId>.json` in the main checkout; Claude-only, never blocks |

`guard-bash.py` is an advisory guardrail against agent mistakes, not a security sandbox.
Enterprises that need enforcement should use managed permissions (deny rules) or a
sandbox. It tolerates git global options (`-C`, `-c`, `--git-dir`, `--work-tree`) and
`terraform -chdir`, and applies the same rules inside `bash -c`/`sh -c`/`zsh -c`/`eval`
strings and `$(...)` or backtick substitutions.

`guard-bash.py` splits compound commands, so a destructive command chained after a
harmless one is caught like a bare one. The deny list covers infrastructure applies and
state surgery, raw secret-tool edits, bulk or cluster-scoped deletes, force-push without
`--force-with-lease` and hard resets to a remote ref; the exact rules are in
`hooks/lib/core.py`, shared by every harness. Claude Code runs the scripts above
directly; every other harness runs `hooks/adapter.py --harness <h> --event <e> --hook <name>`
over the same logic.

What each hook enforces and why: references/hooks.md.

## Verification

The reviewer runs every step's Verify and the Final verify on the committed HEAD, checks every agreed item and step against the files and maps every changed hunk to a step. Implementers return red evidence (`tests.red`) or name the TDD exception that applied, and commit per step, so the verified head is the plan tree's HEAD. The freshness guard (`verify-recorder.py` plus `subagent-commit-guard.py`) refuses to let a subagent stop while its last test or lint run was not on the current HEAD.

The user's answer at the gate is the only approval: it picks the rung and answers the open questions; the reviewer checks the whole diff against that agreed scope.

Every implementer prompt carries the plan path and its chunk number, never file contents.

systematic-debugging supersedes engineering:debug and requesting-code-review supersedes /code-review for work in these trees.

## Scripts

| Script | Does |
|---|---|
| `lib/workbench.py` | tree discovery and component resolution |
| `../../superpowers/scripts/ticket.py` | plan ticket lifecycle (see Documents) |
| `run-tests.sh` | every skill suite, one process per skill |
| `flake-hunt.sh` | repeats one component under load to hunt flakes |

All plain CLI tools; none of them need Claude.

## Tests

```bash
mise install
mise run test     # or: bash scripts/run-tests.sh
```

The suites are pytest and bats. `run-tests.sh` prints the component and assertion counts and ends with `all green`.

`bash scripts/run-tests.sh --only <component>` runs one component (a skill name, `hooks` or `scripts`). A failing component's full output is kept on disk and its path is printed after the tail as `full output: <path>`. `scripts/flake-hunt.sh <component> <runs> [parallel]` repeats one component under parallel load to hunt order, timing or environment flakes (the hooks hunt, 30 runs x 4 parallel, found 0 failures).

One pytest process **per skill**, deliberately: the GitLab and GitHub skills each
ship `scripts/watch.py` and `scripts/update.py`, and their tests sys.path-insert
their own directory then `import watch`. In one shared process the first loaded
wins and the other family silently tests the wrong module. Per-skill processes are
both correct and honest about the skills being independent.

## Rules

`rules/` carries the working rules as plain files: the cross-cutting ones (`concise-orchestrator`, `boy-scout`, `tdd`, `housekeeping`) and per-language ones. A plugin does not auto-load them in Claude Code; the template embeds the load-bearing rules in `AGENTS.md`, and `mise run harness-setup -- <target>` generates the per-harness copies.

- `rules/concise-orchestrator.md` - one line per update, no pasted logs
- `rules/boy-scout.md`
- `rules/tdd.md`
- `rules/housekeeping.md` - the user's standing rules for every agent, every harness and every task

## Research briefs

Research skills write their briefs under `docs/research/`; `skills/start-research/scripts/doc_path.sh <kind> "<topic>"` returns the path.

## Known limitations

- `rules/` is not auto-loaded by a plugin (see Rules above).
- Skills that need a tool you do not have (`gh`, `glab`, `mise`) say so and stop; they do not fall back silently.
