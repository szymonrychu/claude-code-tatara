# workbench - core plugin

The tooling for any workbench tree, whether the tree is a metarepo or a flat set of sibling
repos: read-only diagnostic and research agents, research skills, worktrees, submodules, pull
requests, releases, and hooks that guard destructive commands. The development flow itself is
the vanilla superpowers plugin (`superpowers@claude-plugins-official`, governed by
`superpowers:using-superpowers`): `superpowers:brainstorming` (plan in
`docs/plans/<name>/plan.md`), `superpowers:writing-plans` (plan in `docs/plans/<name>/implementation.md`),
`superpowers:subagent-driven-development` or `superpowers:executing-plans`,
`superpowers:requesting-code-review`, `superpowers:receiving-code-review`,
`superpowers:systematic-debugging` and `superpowers:finishing-a-development-branch`. Every
workbench skill and agent is a helper to one of those skills.

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

Read-only, except the `research-*` agents (a brief at their output path).
Mechanical ones on sonnet (they exist to keep large output out of the main context);
research ones on opus (they exist for judgement).

| Agent | Model | Does |
|---|---|---|
| `scm-shepherd` | sonnet | MR/PR + pipeline status; picks `glab` or `gh` from the remote |
| `submodule-auditor` | sonnet | which submodule pins are stale, unpushed, detached, or remote-less |
| `codebase-cartographer` | opus | maps an unfamiliar repo before design: entrypoints, boundaries, where a change lands |
| `security-researcher` | opus | secrets, RBAC, container privilege, supply chain, CVE surface |
| `architect-researcher` | opus | design research that ends in a decision, not a table |
| `reuse-hunter` | sonnet | finds parts a plan would rebuild, near-duplicate helpers and hot spots; returns a shared-parts map |
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
| `superpowers:requesting-code-review` | `security-researcher` | diff touches secrets, RBAC, exposure, privilege, CI, or hooks |
| `references/merge-hosts.md` | `scm-shepherd` | a pipeline failed and the cause is not in the log tail |
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
git-worktrees-create, git-worktrees-commit, git-worktrees-push   the multi-submodule path for superpowers:using-git-worktrees
pullrequests-update, pullrequests-watch, pullrequests-list   the PR path of superpowers:finishing-a-development-branch; GitHub (gh) or GitLab (glab) per repo from origin
pullrequests-review-loop        judges an automated PR reviewer's findings through superpowers:receiving-code-review
start-research                  several research lenses at once, briefs ending in Plan inputs
release                         judge major/minor/patch from commits, write CHANGELOG, bump plugin.json and marketplace.json, commit and tag locally (never pushes)
research-code-internal          plan adds a helper/reader/parser/schema field/subsystem, or a repo has > ~200 source files
research-code-external          the change has known analogues (protocol, parser, scheduler, cache, auth flow, rules engine) or an open design fork
research-papers                 the problem has a scientific or algorithmic core, or the user names a paper
research-docs                   a library, framework, provider or platform API is used in a new way, upgraded, or touched in >= 3 call sites
pill                            a cited study PDF on a topic: research agents, optional pod measurements, SVG figures, pure-pip render, kubectl cp into a pod mounting the books dir
```

`init` is the entry point of a fresh clone: it asks the questions, confirms any forge
creation, runs the engine through `mise run init:new` or `mise run init:adopt`, generates the
harness files and fills the project block of `AGENTS.md`. `component-add` and
`component-remove` wrap `mise run component`. `template-update` wraps `mise run init:update`:
it fetches the template, merges its tooling, keeps the instance-owned docs and pushes nothing.

The `research-*` skills and `start-research` run during `superpowers:brainstorming`; their
briefs end in the Plan inputs lists (`references/plan-inputs.md`) that the design and the plan
place.

One flow serves both tree shapes; the host (GitLab or GitHub) is picked per repo in references/merge-hosts.md.

## Documents

```
docs/plans/<name>/plan.md            written by superpowers:brainstorming
docs/plans/<name>/implementation.md written by superpowers:writing-plans
docs/research/             research briefs
```

Research paths come from `skills/start-research/scripts/doc_path.sh research "<topic>"`.

### Per-repo config

`.claude/workbench.json` holds the per-repo settings read by `scripts/lib/workbench.py`: `refRunners` (glob to command for a test ref) and `deploy` (run after merge by `scripts/deploy-hook.py`). Keys: `references/workbench-config.md`.

### Background dispatches and user steps

A command only the user can run (reboots, firmware) becomes a user-run step: `scripts/user-run-step.py` checks state before and after and parses the pasted result (`references/user-run-steps.md`).

Releases go through the `release` skill: `skills/release/scripts/release.py --dry-run` previews the judged bump and changelog section; a real run bumps `plugin.json` and the `workbench` entry of the root `.claude-plugin/marketplace.json`, prepends `plugins/workbench/CHANGELOG.md`, commits `chore(release): vX.Y.Z` and tags it locally.

## Discovery

Discovery uses LSP and grep, with no graph probe; LSP first for symbols and references, then grep.

Both SCM families ship deliberately. They are parallel implementations, not drift.

## Hooks

| Hook | Event | Does |
|---|---|---|
| `guard-bash.py` | PreToolUse/Bash | denies destructive commands with an actionable reason (advisory guardrail, not a sandbox) |
| `bash-output-filter.py` | PreToolUse/Bash | caps noisy test/log output before it reaches context |
| `protect_files.py` | PreToolUse/Edit,Write | blocks edits to secrets, state files, `.git`, encrypted-secret files |
| `format-file.sh` | PostToolUse/Edit,Write | formats the edited file with the formatter for its language when one is installed |
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

## Review and debugging

systematic-debugging supersedes engineering:debug and requesting-code-review supersedes /code-review for work in these trees.

## Scripts

| Script | Does |
|---|---|
| `lib/workbench.py` | tree discovery and component resolution |
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

`rules/` carries the working rules as plain files: the cross-cutting ones (`concise-orchestrator`, `boy-scout`, `housekeeping`, `secrets-model`, `superpowers-flow`) and per-language ones. A plugin does not auto-load them in Claude Code; the template embeds the load-bearing rules in `AGENTS.md`, and `mise run harness-setup -- <target>` generates the per-harness copies.

- `rules/concise-orchestrator.md` - one line per update, no pasted logs
- `rules/boy-scout.md`
- `rules/housekeeping.md` - the user's standing rules for every agent, every harness and every task
- `rules/secrets-model.md` - how secret values move through the agents system and the invariants every change must keep
- `rules/superpowers-flow.md` - workbench amendments to the vanilla superpowers flow: research step, single human approval, per-improvement paths, retro, orchestrator never edits

## Research briefs

Research skills write their briefs under `docs/research/`; `skills/start-research/scripts/doc_path.sh research "<topic>"` returns the path.

## Known limitations

- `rules/` is not auto-loaded by a plugin (see Rules above).
- Skills that need a tool you do not have (`gh`, `glab`, `mise`) say so and stop; they do not fall back silently.
