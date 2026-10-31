# Workbench

## What this repository is

This is a **workbench metarepository**: a thin superrepo whose real content lives in git
submodules under `code/`, plus shared skills, rules and documentation that support
development across the components. It is a working root, not a place for code.

- The submodules ARE the code. Every substantive change happens inside a `code/<component>`
  submodule, which is its own independent repo with its own tests, `MEMORY.md` and
  `ROADMAP.md`.
- This superrepo carries no build of its own for components. It pins submodule commits and
  hosts cross-cutting workbench material; the tooling lives under `plugins/`.

Bootstrap and refresh submodules:

    git submodule update --init --recursive     # first checkout
    git submodule update --remote               # advance each to its tracked branch

Each submodule tracks a branch (see `.gitmodules`). Work inside a submodule on its own
branch, land on that submodule's default branch, then commit the moved pointer here.

<!-- workbench:project:begin -->
## What this project is building

A Python reimplementation of tatara-new: a decentralised set of small microservices connected by a real queue, decoupled from Kubernetes APIs, replacing the monolithic Go codebase; it starts from claude-code-wrapper, with an orchestrator microservice next.

## Components (code/)

| Submodule | Lang | Role | Build |
|-----------|------|------|-------|
| claude-code-wrapper | python | HTTP microservice that runs long-lived interactive Claude Code sessions under PTYs and exposes turns, an SSE event stream and lifecycle hooks | `mise run --cd code/claude-code-wrapper test` |
| any-mcp | python | MCP server that exposes any API as MCP tools through a plugin system (stdio and streamable HTTP) | `mise run --cd code/any-mcp test` |
| agents-orchestrator | python | Web UI and headless API orchestrating Kubernetes pods of claude-code-wrapper agents: sessions, round-robin dispatch, chat history (Python backend, React frontend, helm chart) | `mise run --cd code/agents-orchestrator test` |
| agents-helmfile | generic | helmfile managing namespace agents: CNPG database and the agent-orchestrator release, applied with local mise tasks | `mise run --cd code/agents-helmfile test` |
| agents-web | typescript | Web UI of the agents system (React/MUI SPA served as static files by nginx-unprivileged), reaching each backend (agent-orchestrator first) through its documented HTTP API on one host | `mise run --cd code/agents-web test` |
| agents-common | python | Python library shared by the trigger services (agents-webhook, agents-schedule): settings, Postgres pool, migrator, guarded queue transitions, orchestrator client, run tracker | `mise run --cd code/agents-common test` |
| agents-webhook | python | Python microservice with its own Postgres database that receives GitHub/GitLab PR, issue and comment webhooks and Grafana alerts, queues them FIFO with dedup and limits, and starts agent clusters from presets through the orchestrator API | `mise run --cd code/agents-webhook test` |
| agents-schedule | python | Python microservice mapping cron schedules to presets; fires agent clusters through the orchestrator API; own database | `mise run --cd code/agents-schedule test` |
| agents-matrix-connector | python | Python microservice with its own Postgres database: connects to the Matrix homeserver as a bot user, auto-discovers Messenger chats bridged by mautrix-meta, applies allow/deny rules and routes allowed chats to agents-orchestrator sessions | `mise run --cd code/agents-matrix-connector test` |
| any-mcp-tatara-plugins | python | Bucket of platform-specific any-mcp plugins grouped into topic subdirectories, installed by any-mcp from a git repo, subdirectory and ref (terraform-module-like source notation) | `mise run --cd code/any-mcp-tatara-plugins test` |

## Component hard rules

- Python only, except web frontends (TypeScript).
- Services talk only through the queue or HTTP APIs; the only shared state is one service's own database, where each table has exactly one writer and queue tables change rows only through status-guarded updates.
- Deploy only semver-tagged images (X.Y.Z); never a sha tag; a component's main build releases the semver tag before helmfile pins it.

## Highest-risk surface

Running interactive Claude sessions: PTY control, hooks and credentials.

## Forge

Origins are on GitHub: changes land through pull requests (PRs), via `gh`.
<!-- workbench:project:end -->

## Ground rules

1. **Development flow.** The vanilla superpowers plugin governs all work
   (`superpowers:using-superpowers`); workbench skills and agents are helpers to it.
   Non-trivial work starts with `superpowers:brainstorming` (specs in
   `docs/superpowers/specs/`), `superpowers:writing-plans` writes the plan
   (`docs/superpowers/plans/`), and `superpowers:subagent-driven-development` or
   `superpowers:executing-plans` runs it. Reviews go through
   `superpowers:requesting-code-review` and `superpowers:receiving-code-review`, failures
   through `superpowers:systematic-debugging`, and the branch lands through
   `superpowers:finishing-a-development-branch`. In harnesses other than Claude Code, invoke
   the skills by their bare names.
2. **Always use subagents, with an explicit model.** Set the model on every dispatch:
   research opus; implementation sonnet, opus only for the hardest tasks; review sonnet;
   very complex architecture decisions fable; mechanical relays and classifiers: haiku;
   everything else (lookups, summaries, merges, monitoring) sonnet. Never use a stronger model when a weaker one
   suffices. On other harnesses use the harness's strongest or default equivalents of these
   tiers.
3. **Finish the whole scope and nothing outside it.** Implement everything asked, to the
   letter: never skip, "all" and "each" mean all and each. If it needs a missing subsystem,
   build the subsystem. Difficulty changes sequencing, never whether it gets done. The only
   acceptable non-delivery is a genuine blocker: name it and ask. Never cut corners or reduce
   scope (see "Housekeeping rules": full scope). Do not widen scope; a tangent gets exactly
   one line, "noted, not doing now: <thing>", and work continues.
4. **Never report waiting.** "Waiting", "holding", "blocked", "nothing to do yet" are a
   signal you have not found the work. Enumerate every open item (PR/MR, pipeline, branch,
   worktree, background task) and act on its state:

   | State | Action, now |
   |---|---|
   | green and mergeable, no unresolved review | merge it |
   | conflicted, `DIRTY`, `BEHIND` | rebase the branch |
   | changes requested, unresolved discussions | judge each finding, fix the real ones, drop the wrong ones |
   | `BLOCKED`, not approved, discussions unresolved | read the actual reason and act on it |
   | failing CI | read the log tail, fix the cause |
   | a dependency just merged | rebase and re-push what was waiting on it |

   Only when every item is genuinely pending on someone else may you say so, naming each
   item, its state and what it waits on. Act on the first item that transitions, never the
   batch: independent items get independent action. Bound every wait at 10 minutes, then
   re-enumerate and report concretely. Use a tested watcher script, never a hand-rolled
   polling loop. For agents running in the background, the Agent notification on exit is the
   wake signal: do not poll.
5. **Stay on the assignment and answer short.** Do the task given: no unrelated issues, no
   refactors beyond the task, no extra hardening. Keep answers to a few lines: what
   changed, what is next, anything needing a decision. Detail only when asked. If scope
   genuinely must grow, stop and ask in one sentence.
6. **Recurring corrections.**
   - Give estimates in agent wall-clock time, not human-days.
   - Main is always green: never merge or leave a red default branch.
   - Take the least destructive action first wherever actions have real side effects
     (deletes, force-pushes, applies, deploys); escalate only when it fails.
   - Record standing approvals in writing and honour them without re-asking.
   - Deferral sticks: what the user deferred stays deferred until they say otherwise.
   - Use the project's wrappers (`mise run ...`, helper scripts) instead of raw commands.
   - Do not run what the user said they will run themselves.
   - Boy-scout, reconciled: simplify the files the task already touches; for any other
     file, state the observation in one line and carry on.

## Writing and working conventions

- No em dashes, smart quotes, arrows or decorative Unicode, in code, comments, commits,
  messages or any other content (see "Housekeeping rules"). Plain hyphens and straight
  quotes. No preamble.
- Before working in a component, read its `AGENTS.md`, `MEMORY.md` and `ROADMAP.md`.
- Update `MEMORY.md` on every non-obvious decision, with the date and the why.
- `ROADMAP.md` is human-owned requirements; ask the user rather than inventing entries.
- Near context limits, use the `handoff` skill instead of pushing on.

<!-- workbench:rules:begin -->
_Generated from plugins/workbench/rules/; edit there, then run `mise run harness-setup`._

## Boy scout rule

Leave the tree better than you found it, and never let someone else's loose
end become a reason your own work is incomplete.

1. **Simplify what you touch.** If code you are already working in can be made
   simpler without changing behaviour, do it. Not a refactor tour - the files
   the task already puts in your hands.
2. **Functional but uncommitted work gets committed.** Uncommitted changes that
   work are not "someone else's problem" to route around. Review them, confirm
   they are green, and commit them.
3. **Uncommitted work that blocks full delivery must be cleared, not worked
   around.** Review it, adjust it until lint and tests pass, commit it as its
   own commit, then commit your work on top. Never leave your change sitting in
   a tree that was already broken, and never report a failure that belongs to
   pre-existing work as a reason your task is unfinished.

Commit boundaries stay honest: pre-existing work and your work are separate,
adjacent commits with their own messages. Fixing someone's lint does not make
their feature yours, and it does not get folded into your commit.

Do not commit work that is broken, half-finished, or that you cannot verify.
"Functional" means you ran the checks and they passed.

## Concise orchestrator output

The orchestrator's context is the most expensive thing in a session: every turn
re-reads all of it. After the initial discussion of a task, every update,
notification reply, poll reply and status is VERY short.

- Progress update: one line. `<what moved> - <next> - <decision needed, if any>`.
- Poll result with nothing actionable: no tool call, and no text
  beyond the line itself.
- Never restate what a notification already says. Never paste logs, tables,
  JSON or diffs unless asked; cite a path instead.
- A finished task: what landed, verified how (the one summary line of the real
  output), what is next. Three lines at most.
- Subagent prompts and reports follow the same rule: ask for capped reports
  (a word limit), and read their files rather than their full transcripts.
- Detail only when the user asks for it, or a decision needs it.

## Housekeeping rules

The user's standing rules for every agent, every harness and every task.

1. **No em dash characters** in any code, comment, commit, message or content of
   any kind. Use a plain hyphen.
2. **No backward compatibility** (shims, aliases, legacy fallbacks) unless the
   user explicitly asks for it.
3. **Tests are not negotiable.** Never edit, delete or xfail a test to make it
   pass, unless the test itself is no longer accurate; then say which test and
   why. Tests make the code repeatable and guard against regressions.
4. **One scratchpad.** Every scratchpad edit lands under `.scratchpad` in the
   workbench root (the main checkout, never a worktree); it is the only
   scratchpad dir (`workbench.py scratchpad` prints it).
5. **One log dir.** Every log lands in the gitignored `.logs` in the workbench
   root (`workbench.py logs` prints it).
<!-- workbench:rules:end -->
