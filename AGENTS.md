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
| agents-mindmap | python | Python microservice with its own Postgres (pgvector) that stores research mind maps per project: nodes, versioned growth, edges, links to tasks and specs, directions, full-text and semantic search, an outbox notifier and an embedder; three listeners (web, delegate, service) behind the orchestrator relay | `mise run --cd code/agents-mindmap test` |

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
   `superpowers:executing-plans` runs it. Reviews run native
   `/code-review` plus `workbench:spec-reviewer` (item 13), findings through
   `superpowers:receiving-code-review`, failures
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
   simpler without changing behaviour, do it. No refactor tour: only the files
   the task already touches.
2. **Functional but uncommitted work gets committed.** Review them, confirm
   they are green, and commit them; do not route around them.
3. **Uncommitted work that blocks full delivery must be cleared, not worked
   around.** Review it, adjust it until lint and tests pass, commit it as its
   own commit, then commit your work on top. Never leave your change in
   a broken tree, and never cite a pre-existing failure as a reason your task is unfinished.

Commit boundaries stay honest: pre-existing work and your work are separate,
adjacent commits with their own messages. Fixing someone's lint does not make
their feature yours or fold it into your commit.

Do not commit work that is broken, half-finished, or that you cannot verify.
"Functional" means you ran the checks and they passed.

## Concise orchestrator output

The orchestrator's context is the costliest thing in a session: every turn
re-reads it. After the initial discussion of a task, every update, reply and status
is VERY short.

- Progress update: one line. `<what moved> - <next> - <decision needed, if any>`.
- Poll result with nothing actionable: no tool call, no text beyond the line itself.
- Never restate what a notification already says. Never paste logs, tables,
  JSON or diffs unless asked; cite a path instead.
- A finished task: what landed, verified how (the one summary line of the real
  output), what is next. Three lines at most.
- Subagent prompts and reports follow the same rule: ask for capped reports
  (a word limit), and read their files rather than their full transcripts.
- Detail only when the user asks for it, or a decision needs it.

## Housekeeping rules

The user's standing rules for every agent, harness and task.

1. **No em dash characters** in any code, comment, commit, message or other
   content. Use a plain hyphen.
2. **No backward compatibility** (shims, aliases, legacy fallbacks) unless the
   user explicitly asks for it.
3. **Tests are not negotiable.** Never edit, delete or xfail a test to make it
   pass, unless the test itself is no longer accurate; then say which test and
   why. Tests guard against regressions (tests guarding no behaviour may go: flow item 12).
4. **One scratchpad per improvement.** Every scratchpad edit lands under
   `.scratchpad/<name>/` in the workbench root (the main checkout, never a
   worktree), `<name>` being the improvement's kebab-case name
   (`workbench.py scratchpad <name>` prints it).
5. **One log dir per improvement.** Every agent tool log lands
   in the gitignored `.logs/<name>/` in the workbench root
   (`workbench.py logs <name>` prints it).
6. **The orchestrator never edits.** It dispatches, verifies with the repo's test and lint
   commands, and merges and pushes reviewed work; it is accountable for its subagents
   (full rule: "Superpowers flow", item 5).
7. **Secrets.** Before changing anything that handles secret values, env, tokens,
   logging, errors, transcripts or RBAC in any component, read
   `plugins/workbench/rules/secrets-model.md`.

## Superpowers flow in this workbench

The flow is the vanilla `superpowers` plugin; these amendments override its defaults here (user instructions take precedence over its skills). `<name>` is the improvement's kebab-case name.

1. **Research first.** (Scaled by task class, item 10.) Every development workflow starts with a research step before `superpowers:brainstorming` designs: (a) the docs of every tool, library and system the plan uses (`workbench:research-docs`), (b) a sweep of the codebase for reuse and the smallest coherent diff (`workbench:research-code-internal`), (c) when the `orchestrator_mindmap_*` tools exist, search the project mind map first, (d) list every tool the plan calls and which role may call it.
2. **One human gate.** The plan (spec) plus its questions is the only gate. It covers what, why, research findings, design, files and components touched, test approach, risks, scope: the MVP (smallest literal delivery of the request) plus every option the user chose at the gate, each with its LOC; above-MVP is a question; prefer deleting code. Every question offers options, one marked "MVP", one "Recommended" (may coincide). After answers, `superpowers:writing-plans` writes the implementation plan without a second human review; execution (`superpowers:subagent-driven-development`) starts only once every decision on its open tasks is answered and, with the spec tools, the spec approved. With `orchestrator_task_*` tools, questions are posted as taskboard decisions via `orchestrator_decision_ask` (recommended marked; MVP in the option text), never as chat text. Answers arrive as notice `Task T-<n> was updated: <link>`; then `orchestrator_task_get`. Question text also goes in `docs/plans/<name>/plan.md`, to survive a dead leader (item 7). A design-changing answer regenerates the plan summary.
3. **Paths.** (Spikes use none of them, item 10.) These override the superpowers locations (also for `using-git-worktrees`):
   - worktrees: `<workbench root>/.worktrees/<name>/<repo>` for each repo involved
   - scratchpad: `<workbench root>/.scratchpad/<name>/`
   - logs of every tool the agents run: `<workbench root>/.logs/<name>/`
   - plan (spec): `docs/plans/<name>/plan.md`; implementation plan: `docs/plans/<name>/implementation.md` (instead of `docs/superpowers/*`); with the spec tools, item 7 places the plan, research and retro
4. **Final reviewer.** `workbench:spec-reviewer` (item 13): completeness against the agreed scope; correctness is `/code-review` at `high`. It writes only the retro (`docs/plans/<name>/retro.md`, a spec document with the spec tools, item 7): what implementation hit and planning missed. The orchestrator relays them.
5. **The orchestrator never edits.** It never updates code (source, tests, skills, agents, hooks, rules, docs); where a skill would edit inline, it dispatches a subagent, and answers for them. Duties: dispatching, reading results, test and lint, and git merge and push of reviewed work.
6. **Taskboard lifecycle.** Only with the `orchestrator_task_*` tools. When work starts, create or claim a task (`orchestrator_task_create`, or `orchestrator_task_update` with `assignee_self`). Keep its todo current (`orchestrator_todo_set` / `orchestrator_todo_update`). On landing, close it (`done` or `dropped`).
7. **Specs on the server.** Only when the `orchestrator_spec_*` tools are available (else items 2-4 paths apply). Every brainstormed task gets a spec `<name>` in the session's project; small fixes only a task. Its documents: `plan.md` (the brainstorming plan with its questions), `research/<topic>.md` (each research step's final brief; lens briefs stay in `.scratchpad/<name>/`), `retro.md` (the final reviewer's retro). The task (rule 6) is linked to the spec (`orchestrator_task_update` with `spec`) and holds the gate questions as decisions; with the plan pushed and `orchestrator_plan_gate` saying `approvable` (without plan tools: `orchestrator_task_get` shows none open), the orchestrating agent approves the spec (`orchestrator_spec_update` status `approved`; the server refuses 409 `decisions_open` while any is open). Subagents write documents as files in the copy `.scratchpad/<name>/spec/` (`orchestrator_spec_pull` creates it); the orchestrating agent pushes with `orchestrator_spec_push` after each edit (pushing is not editing). With mind map tools, record each final brief as a node linked to the task. A document stays under 192 KiB: split a larger one. With `orchestrator_plan_*` too, the implementation plan is the spec's plan, not a file: `superpowers:writing-plans` writes the header with `orchestrator_plan_set` and the steps with `orchestrator_plan_steps_push`, and writes no `implementation.md`; the gate questions go out with `orchestrator_plan_questions_ask`; `superpowers:subagent-driven-development` takes work with `orchestrator_plan_step_next` (`claim: true`) and records branches and PRs with `orchestrator_plan_step_update`; the orchestrating agent runs `orchestrator_spec_pull` and `orchestrator_plan_export` into `.scratchpad/<name>/spec/` for the final reviewer, then pushes `retro.md` and archives the spec (`orchestrator_spec_update` status `archived`). Work already executing from an imported `implementation.md` finishes from it.
8. **Approved spec starts implementation.** A hive receiving "Spec S-<n> approved - take it into implementation now: <url>", or started by taskboard autostart with a prompt naming an approved spec, proceeds without re-asking: it claims the gate task, runs `superpowers:writing-plans` from the spec (unless the plan exists), then `superpowers:subagent-driven-development`, review, release, deploy, retro, archive.
9. **Approvals.** With `orchestrator_approval_*` tools: `plugins/workbench/rules/approvals.md`.
10. **Task classes.** Label the task `class:spike`, `class:bounded` or `class:architectural` on creating or claiming; when unsure, the higher class. Items 1 and 3 apply in full only to `architectural`:
    - `spike`: throwaway or one-file exploration, no production merge. No research, spec or subagent-driven development; one subagent inline (item 5).
    - `bounded`: a change inside one component. Research: only `workbench:research-code-internal` (plus `workbench:research-docs` for a library used in a new way); one implementer per task; one review round (item 13), more only if findings need a fix.
    - `architectural`: cross-component, new subsystem or hard to reverse. Everything in full.
11. **Native mechanics over superpowers mechanics.**
    - `superpowers:dispatching-parallel-agents`: native parallel subagents (several Agent calls per message).
    - `superpowers:using-git-worktrees`: served by `workbench:git-worktrees-*` (item 3); harness worktree isolation is unused: in a metarepo it isolates the superrepo, not the submodule.
    - `superpowers:writing-plans`: lean plans; steps carry decisions, not code, and a LOC estimate; over ~400 changed LOC lands as separate PRs.
    - `superpowers:finishing-a-development-branch`: before merging, `git status --porcelain` is empty in every repo (commit or clear, boy-scout).
    - `superpowers:verification-before-completion`: keep the skill text; mechanics move to the opt-in Stop hook `verify-on-stop.py` (`WORKBENCH_VERIFY_ON_STOP=1`).
12. **Tests earn their place.** `superpowers:test-driven-development` stays. Test only observable behaviour named in the plan step or spec (inputs to outputs, boundary side effects), never helpers, constants or framework behaviour. One test per behaviour; parametrise variants. No test that could not signal a real defect; the reviewer (item 13) rejects them. Each report states the net test count delta. Deleting them does not breach housekeeping rule 3.
    - Marked levels: unit, `integration`, `e2e` (`tests/e2e`), `live` (`tests/live`); agents-web vitest, playwright; boox JVM, androidTest, roborazzi.
    - B1 `critical` (`mise run test:critical`), B2 default, B3 deleted: config/structure tests (settings, chart/values/helmfile render, CI/mise/Dockerfile/README shape), duplicates.
13. **Review.** Per task, run native `/code-review` (the `code-review` skill at effort `medium` for bounded, `high` for architectural; never `max` or `ultra` unless the user asks) for correctness, then dispatch `workbench:spec-reviewer` for scope and test value; spikes skip review. Findings go through `superpowers:receiving-code-review` (judge each, fix the real ones); reviewable: lint clean (no new complexity `noqa`), diff within its LOC estimate or explained. This item replaces `superpowers:requesting-code-review`. Final branch review: `workbench:spec-reviewer` over the whole branch plus native `/code-review` at `high`.
<!-- workbench:rules:end -->
