# workbench - core plugin

The development flow for any workbench tree, whether the tree is a metarepo or a flat
set of sibling repos: discovery, design and plan behind one approval gate, unattended
execution with a verifier, tiered review, gated debugging, file-based epic tickets,
and hooks that guard destructive commands and tie every test run to the committed HEAD.

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

Read-only, except `record-writer` (one file, the run record), `implementer` (code in its worktree)
and the `research-*` agents (a brief at their output path).
Mechanical ones on sonnet (they exist to keep large output out of the main context);
research ones on opus (they exist for judgement). The reviewers carry no model of their own:
the caller sets it per call.

| Agent | Model | Does |
|---|---|---|
| `scm-shepherd` | sonnet | MR/PR + pipeline status; picks `glab` or `gh` from the remote |
| `submodule-auditor` | sonnet | which submodule pins are stale, unpushed, detached, or remote-less |
| `codebase-cartographer` | opus | maps an unfamiliar repo before design: entrypoints, boundaries, where a change lands |
| `planner` | opus | plans an epic from `{epic, briefs[], userDecisions[]}`: design.md and linted tasks |
| `security-researcher` | opus | secrets, RBAC, container privilege, supply chain, CVE surface |
| `architect-researcher` | opus | design research that ends in a decision, not a table |
| `reuse-hunter` | sonnet | finds parts a plan would rebuild, near-duplicate helpers and hot spots; returns a shared-parts map |
| `record-writer` | sonnet | the one agent that writes: fills the record template for a finished run, one file |
| `implementer` | sonnet | implements one task or the lean path's change test-first and returns `complete`, `undelivered`, `discovered` |
| `reviewer` | per call | one reviewer per task: verify on HEAD, every acceptance condition, then quality |
| `panel-reviewer` | per call | one member of an `interrogate` review panel, one per model |
| `worktree-merger` | sonnet | merges one task worktree back: rebase, fast-forward, verify every commit landed, clean up |
| `research-docs-purist` | sonnet | official docs at the installed version, anti-patterns in our usage |
| `research-practitioner` | sonnet | field experience and known failure modes |
| `research-prior-art-scout` | sonnet | similar open-source projects, shapes and dead ends |
| `research-paper-scout` | sonnet | literature for the algorithmic core, cited by DOI or arXiv id |
| `research-reviewer` | sonnet | adversarial check of research briefs |
| `scope-auditor` | sonnet | checks delivered work against the agreed scope; dispatched by plan-execute as an agent type |

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
| `start-development` phase 1 | `submodule-auditor` | a checkout may be stale, detached, or unpushed |
| `start-development` phase 1 | `codebase-cartographer` | mapping a repo in scope (via `start-discovery`) |
| `start-development` phase 1 | `reuse-hunter` | the reuse hunt (via `research-code-internal`) |
| `start-development` phase 2 | `architect-researcher` | >1 viable approach, or an expensive-to-reverse choice |
| `start-development` phase 3 | `planner` | planning an epic from `{epic, briefs[], userDecisions[]}` |
| `start-development` phase 1 | `research-docs-purist` | official docs of every library in scope (via `research-docs`) |
| `start-development` phase 1 | `research-practitioner` | field experience, known failure modes (via `start-research`) |
| `start-development` phase 1 | `research-prior-art-scout` | similar open-source projects (via `research-code-external`) |
| `start-development` phase 1 | `research-paper-scout` | literature for an algorithmic core (via `research-papers`) |
| `start-development` phase 1 | `research-reviewer` | adversarial check of every research brief |
| `start-development` phase 4 | `implementer` | every task's implementation, via plan-execute and the lean path |
| `start-development` phase 5 | `reviewer` | one reviewer for spec and quality (via `start-review --single`) |
| `start-development` phase 4 | `scope-auditor` | after implementation, audit of delivered vs planned |
| `start-development` phase 4 | `worktree-merger` | every worktree merge, sized by `--assess` |
| `start-development` phase 5 | `scope-auditor` | before sign-off |
| `start-development` phase 5 | `security-researcher` | diff touches secrets, RBAC, exposure, privilege, CI, or hooks |
| `start-development` phase 6 | `worktree-merger` | the final merge |
| `start-development` phase 6 | `scm-shepherd` | a pipeline failed and the cause is not in the log tail |
| `start-development` phase 7 | `record-writer` | always on a plan-execute run: writes the record |
| `interrogate` | `panel-reviewer` | a review panel, one agent per model |
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
start-research, start-discovery, start-development, interrogate
epic-create, epic-task-create   create an epic / a task file through ticket.py
epic-move, epic-worktrees-remove  move an epic between stages / remove its merged worktrees
heartbeat                       progress line every 10 minutes while waiting on a run; keepalive opt-in
start-review                    review a branch, diff, MR or PR against its intent: pinned ref, independent suite run, spec and quality reviewers, validated findings
review                          alias of start-review (invoked as /workbench:review)
start-debugging                 gated: reproduce with a red-capable command, minimise, hypothesise, root cause, proven regression test, fix through the lean path
debug                           alias of start-debugging (invoked as /workbench:debug)
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

`start-development` has one approval gate, up front, after design and plan are
written; everything after it runs unattended through `workbench:plan-execute` and ends
with a record. The four `research-*` skills are optional inputs to that gate.

One flow serves both tree shapes; the host (GitLab or GitHub) is picked per repo in references/merge-hosts.md.

## Documents

Every epic is a file-based ticket under `docs/plans/{todo,in-progress,done}/<epic>/`:

```
docs/plans/{todo,in-progress,done}/<epic>/README.md      epic ticket (status, Time section)
                                          design.md
                                          approvals.json
                                          tasks/<task>.md  one file per task (acceptance criteria, estimate, actual)
                                          record.md
docs/research/                               research briefs
```

Older runs wrote `docs/plans/<date>-<slug>-{design,plan,tasks,record}.md` (tasks is .json); those legacy dated files were removed and live only in git history.

`skills/start-development/scripts/ticket.py` moves tickets between the three folders (epic review before done is required, and the move to done checks that the epic reached main, then removes every tree and branch), derives the task JSON, applies a run's results and dedups discovered tasks. The claim creates the epic integration worktree and branch `<epic>`; each task runs in its own `<epic>-<task>` worktree forked from it and landing back on it, and the epic merges to main once at close (`ticket.py close <epic>`: rebase onto main, full suite and lint on the rebased tip, fast-forward only when green). Plain `git worktree` is used throughout, never the harness's built-in worktree feature. Further commands (sibling modules in `scripts/ticket_cmds/`): `ticket.py rule` records a ruling, `ticket.py args` builds and copies the run args, `ticket.py continue` relaunches an escalated run, `ticket.py contract` lists the design contracts, `ticket.py graph --todo` shows the epic dependency graph and open work, `ticket.py roadmap` lists epics in order, `ticket.py facts` builds the facts pack for planners, `ticket.py decide` records a user decision, `ticket.py questions` lists open questions, `ticket.py amend` edits a task in place, `ticket.py worktrees --refresh` brings task worktrees up to date, and `ticket.py reap --epic <epic> --task <task-id>` reaps one merged task worktree (<task-id> is the bare task name, without the epic prefix). Research paths come from `skills/start-research/scripts/doc_path.sh <kind> "<topic>"`.
The design, plan and record follow `skills/start-development/templates/`.

### Per-repo config

`.claude/workbench.json` holds the per-repo settings read by `scripts/lib/workbench.py`: `refRunners` (glob to command for an acceptance-condition test ref), `suites`, `deploy` (hook run after merge) and `overlapIgnore` (paths ignored by the overlap rule). Keys and defaults: `skills/start-development/references/workbench-config.md`.

### Waiting and user steps

`skills/heartbeat/scripts/heartbeat.py --run <id>` waits for the run's journal and ends with the run. A command only the user can run (reboots, firmware) becomes a user-run step: `skills/start-development/scripts/user-run-step.py` checks state before and after and parses the pasted result (`skills/start-development/references/user-run-steps.md`).

Releases go through the `release` skill: `skills/release/scripts/release.py --dry-run` previews the judged bump and changelog section; a real run bumps `plugin.json` and the `workbench` entry of the root `.claude-plugin/marketplace.json`, prepends `plugins/workbench/CHANGELOG.md`, commits `chore(release): vX.Y.Z` and tags it locally.

## What 1.0.0 adds

- **Tickets**: file-based epics and tasks (above), `ticket.py`, `<epic>-<task>` task worktrees on a per-epic integration worktree, epic review before done, every tree and branch removed on done, dedup of discovered tasks.
- **Cheaper review flow**: the script+haiku verifier replaces a model re-run; risk tiers pick how much review a task gets; gate-only fix rounds re-review through the work gate; findings split into undelivered and discovered; an AC evidence gate requires each acceptance criterion to carry command, file or test evidence; an epic-close audit checks the whole epic; time estimates and actuals are report-only, never a budget.
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

Which hooks fire inside Workflow subagents is measured, not assumed: see skills/start-development/references/hooks.md (hook-probe.js and scripts/hook-evidence.py).

## Verification

The independent verifier in `plan-execute` runs the task's own command on the committed HEAD after every implementer and fixer, and records the SHA it ran on. Implementers return red evidence (`tests.red`), and a behaviour change without it becomes a `No red evidence` finding (`TDD skipped` is for a task that reports `wroteTestFirst` false with no listed exception). The freshness guard (`verify-recorder.py` plus `subagent-commit-guard.py`) refuses to let a subagent stop while its last test or lint run was not on the current HEAD. After remediation, each remediated task's branch is forward-merged into every finished same-repo dependent's worktree and re-verified there.

The approval ledger (docs/plans/<date>-<slug>-approvals.json) gives every approved item an id; validate-tasks --approvals checks it against the design and the tasks, plan-execute refuses to defer an approved item (a named external blocker escalates instead), the scope audit checks it by id, and the record shows a status per item.

Every implementer, reviewer, fixer, verifier, merge and audit prompt carries the project brief (what, how, why) and the task's value.

start-debugging supersedes engineering:debug and start-review supersedes /code-review for work in these trees.

## Scripts

| Script | Does |
|---|---|
| `lib/workbench.py` | tree discovery and component resolution |
| `../skills/start-development/scripts/ticket.py` | epic ticket lifecycle (see Documents) |
| `run-tests.sh` | every skill suite, one process per skill |
| `flake-hunt.sh` | repeats one component under load to hunt flakes |

All plain CLI tools; none of them need Claude.

## Tests

```bash
mise install
mise run test     # or: bash scripts/run-tests.sh
```

The suites are pytest, bats and node. `run-tests.sh` prints the component and assertion counts and ends with `all green`.

`bash scripts/run-tests.sh --only <component>` runs one component (a skill name, `hooks`, `scripts` or `workflows`). A failing component's full output is kept on disk and its path is printed after the tail as `full output: <path>`. `scripts/flake-hunt.sh <component> <runs> [parallel]` repeats one component under parallel load to hunt order, timing or environment flakes (the hooks hunt, 30 runs x 4 parallel, found 0 failures).

One pytest process **per skill**, deliberately: the GitLab and GitHub skills each
ship `scripts/watch.py` and `scripts/update.py`, and their tests sys.path-insert
their own directory then `import watch`. In one shared process the first loaded
wins and the other family silently tests the wrong module. Per-skill processes are
both correct and honest about the skills being independent.

## Rules

`rules/` carries the working rules as plain files: the cross-cutting ones (`concise-orchestrator`, `boy-scout`, `tdd`) and per-language ones. A plugin does not auto-load them in Claude Code; the template embeds the load-bearing rules in `AGENTS.md`, and `mise run harness-setup -- <target>` generates the per-harness copies.

- `rules/concise-orchestrator.md` - one line per update, no pasted logs
- `rules/boy-scout.md`
- `rules/tdd.md`

## Research briefs

Research skills write their briefs under `docs/research/`; `skills/start-research/scripts/doc_path.sh <kind> "<topic>"` returns the path.

## Known limitations

- `rules/` is not auto-loaded by a plugin (see Rules above).
- Skills that need a tool you do not have (`gh`, `glab`, `mise`) say so and stop; they do not fall back silently.
