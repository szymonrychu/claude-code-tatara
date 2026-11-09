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
| agents-usage | python | Python microservice with its own Postgres that collects Claude plan usage windows (5-hour, weekly) pushed by the agents' claude-code-wrapper statusLine relay, with a lazy CLI probe as fallback, and records session start/end marks; serves current, history and marks for the orchestrator's usage gate and the web UI | `mise run --cd code/agents-usage test` |
| agents-history | python | Python microservice with its own Postgres that stores and searches historical agent session logs (transcripts) exported by agents-orchestrator, with retention cleanup and user-only delete; serves read and search to superleaders | `mise run --cd code/agents-history test` |
| agents-taskboard | python | Python microservice with its own Postgres: tasks, decisions answered once, todo, comments and history for users and agents; agents reach it through an orchestrator relay, user answers notify the asking session | `mise run --cd code/agents-taskboard test` |
| agents-app-connector | python | Python microservice with its own Postgres and a PVC: client-plugin connector for user devices; plugin sketch pairs Boox devices, takes sketch uploads, translates them into versioned markdown specs through a sketch-translator agent session, streams progress and hands specs off to sessions | `mise run --cd code/agents-app-connector test` |
| agents-boox-sketch | kotlin | Kotlin Android app for BOOX e-ink tablets: pen board with pages, multi-page sketch upload to agents-app-connector, spec panel, hand-off; signed APKs on GitHub Releases | `mise run --cd code/agents-boox-sketch test` |
| agents-vault | python | Python microservice with its own Postgres that owns secret values: write-only versioned entries stored as immutable Kubernetes Secrets, entry labels, per-session pins and garbage collection; users manage entries on the web listener, the orchestrator resolves and pins references on the service listener | `mise run --cd code/agents-vault test` |

## Component hard rules

- Python only, except web frontends (TypeScript) and the Android app agents-boox-sketch (Kotlin).
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
   Non-trivial work starts with `superpowers:brainstorming`, `superpowers:writing-plans`
   writes the plan, and `superpowers:subagent-driven-development` or
   `superpowers:executing-plans` runs it. Reviews go through
   `superpowers:requesting-code-review` and `superpowers:receiving-code-review`, failures
   through `superpowers:systematic-debugging`, and the branch lands through
   `superpowers:finishing-a-development-branch`. In harnesses other than Claude Code, invoke
   the skills by their bare names. The workbench amendments (research step first, one human
   gate, paths under `.worktrees/`, `.scratchpad/`, `.logs/` and `docs/plans/<name>/`,
   final-review retro, the orchestrator never edits) are in the "Superpowers flow in this
   workbench" rule below and override the superpowers defaults.
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
4. **One scratchpad per improvement.** Every scratchpad edit lands under
   `.scratchpad/<name>/` in the workbench root (the main checkout, never a
   worktree), `<name>` being the improvement's kebab-case name
   (`workbench.py scratchpad <name>` prints it).
5. **One log dir per improvement.** Every log of every tool the agents run lands
   in the gitignored `.logs/<name>/` in the workbench root
   (`workbench.py logs <name>` prints it).
6. **The orchestrator never edits.** The orchestrating agent never updates code
   (source, tests, skills, agents, hooks, rules, docs) and is responsible and
   accountable for all work its subagents do. Its own duties: dispatching, reading
   results, running the repo's test and lint commands to verify, and git merge and
   push of reviewed work.

## Secrets model

How secret values move through the agents system, and what every change must preserve.

### Who sees what
- **Protected value**: exists only in the user's browser input, the vault web request body
  (SecretStr), an immutable Kubernetes Secret `vault-<entry>-v<n>`, and the env of the claude
  child in a session pod pinned to it. Never in Postgres, events, logs, error bodies, views,
  tool output or transcripts.
- **Readable value**: stored in the vault database and shown in views and to the orchestrator.
  It is configuration, not a secret. Anything that must stay secret is protected; never store a
  secret as readable for convenience.
- Users (SSO) manage entries on the vault web listener. The orchestrator (service token)
  resolves, pins and releases. Agents never talk to the vault: they see entry names, ids, env
  names and pin metadata through orchestrator tools, and values only as env of their own pod.
- `project:` labels on an entry restrict where it may attach; only the vault evaluates the match,
  from labels the orchestrator derives from the preset's project. A session gets exactly the
  versions pinned at create.
- Anything that can read Secrets in the namespace (cluster-admin sessions, node root) is outside the model; rotation is the response.

### Invariants
1. Write-only Kubernetes: no code, test fake or Role grants get/list/watch on secrets. Secrets
   are written and deleted by deterministic name only.
2. A value is a SecretStr from parse to Secret write and becomes plain text only inside the
   function that builds stringData.
3. No value, hash, length or prefix of a protected value in Postgres, events, metrics, logs,
   error messages, exception chains, HTTP bodies, OpenAPI examples, fixtures or test names.
4. Error texts are fixed strings plus env names, entry ids and versions. Never echo a
   caller-chosen key or an upstream body; drop Kubernetes error bodies and log only the
   exception type name.
5. Pins are immutable per session: a retry returns the first pins, rotate never moves a running
   session, readable values are not versioned.
6. Render only what the spec references. Secret names and keys are validated against the vault
   grammar before they reach a pod spec.
7. The orchestrator sends exactly one `project:` label (its preset's project). User or agent
   supplied labels never carry the `project:` prefix.
8. Wrapper redaction never depends on the env name: every env the orchestrator marks secret is
   redacted by value in events, tails, hook output and transcript-derived records, and kept out
   of shell terminals and of children that run repository code.
9. Service tokens: raw tokens live in Kubernetes Secrets applied from SOPS files. A service
   holds the sha256 of tokens it verifies and the raw token only of the upstream it calls. A
   token that opens service X is never accepted by X's own listener. Constant-time compare;
   never logged, never in a URL.
10. A superleader is an agent with admin reach. Every admin route and tool it gets assumes
    prompt injection: names and ids only, no values, scoped to the caller's project, audited.

### When changing code
- New route or tool: list its statuses in the OpenAPI ROUTE_ERRORS, add it to the canary test
  (a known marker value appears nowhere in responses, logs, rows or events), pick its listener
  (web = humans, service = orchestrator, agent = pods) and the actor identity it records.
- New field on an entry, pin, event or view: ask whether it could hold or derive a value.
  Readable yes, protected never.
- New env name grammar or passthrough: update the orchestrator render golden, the wrapper
  secret-env list and the vault validation together; a mismatch leaks by name.
- New process that handles a value (CLI, migration, backup, export, archive): give it the same
  canary coverage. Exports and archives rely on the wrapper having redacted first.
- Logging: type names, ids, env names, counts. Never request bodies, upstream bodies, env dumps
  or settings reprs. Settings fields holding tokens use repr=False and SecretStr.
- Tests: fake CANARY-... markers only; never a real token in tests, README or OpenAPI examples.
- RBAC and charts: Secret verbs stay create/patch/delete; name restrictions belong in an
  admission policy; mount a ServiceAccount token only into the container that calls the API;
  external Secrets for tokens, never values.yaml literals; semver image pins.
- Transcripts and history: treat every tool result as possibly holding a secret the model
  echoed. Redact in the wrapper before storage; history is searchable by superleaders, so what
  reaches it must already be clean.
- Rotation and GC: delete a retired version only when no live pin references it. Release is by
  reconciliation (pull), late rather than early. After a leak rotate and restart pinned sessions.
- Privileged sessions (cluster access, docker, exec tiers): document and gate what they can
  read, prefer project-scoped entries, never attach broad credentials to presets that trigger
  services (webhooks, schedules) can start.
- Prompt injection: any text an agent reads (webhooks, chats, repos, tool output) may tell it to
  exfiltrate. Controls: value-level redaction, scoped tools, no values in tool answers, audit of
  every admin call.

### Avoid
- Deriving "is secret" from a variable name pattern alone.
- Returning upstream error bodies, pydantic input values or dict keys in 422 messages.

## Superpowers flow in this workbench

The development flow is the vanilla `superpowers` plugin. These amendments override its
defaults here (superpowers gives user instructions precedence over its skills). `<name>` is
the improvement's kebab-case name.

1. **Research first.** Every development workflow starts with a research step before
   `superpowers:brainstorming` proposes a design: (a) the docs of every tool, library and
   system the implementation plans to use (`workbench:research-docs`), (b) a sweep of the
   existing codebase aimed at the most reviewable update, meaning reuse and the smallest
   coherent diff (`workbench:research-code-internal`).
2. **One human gate.** The brainstorming plan (spec) plus its questions is the only gate.
   The plan is more detailed than the superpowers default: what and why, research findings,
   design, files and components touched, test approach, risks, and the scope from MVP to
   complete. Every question offers options and always marks one option "MVP" and one
   "Recommended" (the same option may carry both). After the user answers,
   `superpowers:writing-plans` writes the implementation plan with no second human review,
   and execution (`superpowers:subagent-driven-development`) starts immediately. When the
   `orchestrator_task_*` tools are available, the questions are also posted as taskboard
   decisions with `orchestrator_decision_ask` (one option marked recommended; MVP marked in
   the option text). Answers arrive as a chat
   notice `Task T-<n> was updated: <link>`; then call `orchestrator_task_get`. The question
   text still goes in `docs/plans/<name>/plan.md`, so it survives a dead leader.
3. **Paths.** These override the superpowers locations, including the worktree location
   choice of `using-git-worktrees`:
   - worktrees: `<workbench root>/.worktrees/<name>/<repo>` for each repo involved
   - scratchpad: `<workbench root>/.scratchpad/<name>/`
   - logs of every tool the agents run: `<workbench root>/.logs/<name>/`
   - plan (spec): `docs/plans/<name>/plan.md`; implementation plan:
     `docs/plans/<name>/implementation.md` (instead of `docs/superpowers/specs` and
     `docs/superpowers/plans`)
4. **Final reviewer.** Besides correctness and completeness of the delivered work against
   the agreed scope (under- and over-delivery), the final reviewer writes
   `docs/plans/<name>/retro.md`: what came up during implementation and what was overlooked
   during discovery and planning. The orchestrator relays the retro recommendations in its
   closing message.
5. **The orchestrator never edits.** The orchestrating agent never updates code (source,
   tests, skills, agents, hooks, rules, docs); where a superpowers skill would have it edit
   inline, it dispatches a subagent instead. It is responsible and accountable for all work
   its subagents do. Its own duties: dispatching, reading results, running the repo's test
   and lint commands to verify, and git merge and push of reviewed work.
6. **Taskboard lifecycle.** Only when the `orchestrator_task_*` tools are available in the
   session; otherwise skip this rule. When work starts, create or claim a task
   (`orchestrator_task_create`, or `orchestrator_task_update` with `assignee_self`). Keep its
   todo current (`orchestrator_todo_set` / `orchestrator_todo_update`). When the work lands,
   close the task (status `done` or `dropped`).
<!-- workbench:rules:end -->
