# Superpowers flow in this workbench

The flow is the vanilla `superpowers` plugin; these amendments override its defaults here
(user instructions win). `<name>` is the improvement's kebab-case name.

1. **Research first.** (Item 10 scales it.) Every development workflow starts with research before `superpowers:brainstorming`
   designs: (a) docs of every tool, library and system the plan uses (`workbench:research-docs`), (b) a codebase sweep
   for reuse and the smallest coherent diff (`workbench:research-code-internal`), (c) with `orchestrator_mindmap_*` tools,
   search the project mind map first, (d) list every tool the plan calls and which role may call it.
2. **One human gate.** The brainstorming plan (spec) plus its questions is the only gate. The plan covers what, why,
   research findings, design, files touched, test approach, risks, and scope.
   MVP is the smallest delivery meeting the request literally; the plan holds only the MVP, each option states its LOC
   added/removed, anything above MVP is a question; prefer deleting code.
   Every question offers options, one marked "MVP" and one "Recommended" (may be the same). After the
   answers, `superpowers:writing-plans` writes the implementation plan without a second human review; execution
   (`superpowers:subagent-driven-development`) starts only once every decision on its open tasks is answered and, with
   the spec tools, the spec approved. When the `orchestrator_task_*` tools are available, the questions are posted as
   taskboard decisions with `orchestrator_decision_ask` (recommended option marked; MVP in the option text), never as
   chat text. Answers arrive as a chat notice `Task T-<n> was updated: <link>`; then call `orchestrator_task_get`. The
   question text also goes in `docs/plans/<name>/plan.md`, to survive a dead leader (item 7). An answer that changes the design regenerates the plan summary.
3. **Paths.** (Spikes use none, item 10.) These override the superpowers locations (also for `using-git-worktrees`):
   - worktrees: `<workbench root>/.worktrees/<name>/<repo>` per repo involved
   - scratchpad: `<workbench root>/.scratchpad/<name>/`
   - tool logs: `<workbench root>/.logs/<name>/`
   - plan: `docs/plans/<name>/plan.md`; implementation plan: `docs/plans/<name>/implementation.md` (not
     `docs/superpowers/*`); with the spec tools, item 7 places plan, research and retro
4. **Final reviewer.** The final reviewer is `workbench:spec-reviewer` (item 13): completeness
   against the agreed scope; correctness is `/code-review` at `high`. It writes only the retro (`docs/plans/<name>/retro.md`, a spec document with the spec tools, item 7): what implementation hit and planning missed. The orchestrator relays it.
5. **The orchestrator never edits.** It never updates code (source, tests, skills, agents, hooks, rules, docs); where a
   skill would edit inline, it dispatches a subagent. Duties: dispatching, reading results, test, lint,
   merging and pushing reviewed work.
6. **Taskboard lifecycle.** Only when the `orchestrator_task_*` tools are available. When work
   starts, create or claim a task (`orchestrator_task_create`, or `orchestrator_task_update` with `assignee_self`). Keep
   its todo current (`orchestrator_todo_set` / `orchestrator_todo_update`). On landing, close it (`done` or `dropped`).
7. **Specs on the server.** Only when the `orchestrator_spec_*` tools are available (else items 2-4 paths apply). Every brainstormed task gets a spec `<name>` in the session's project; small fixes only a
   task. Documents: `plan.md` (the plan with its questions), `research/<topic>.md` (each research
   step's final brief; lens briefs stay in `.scratchpad/<name>/`), `retro.md` (the final reviewer's retro). The task
   (item 6) is linked to the spec (`orchestrator_task_update` with `spec`) and holds the gate questions as decisions;
   with the plan pushed and `orchestrator_plan_gate` saying `approvable` (without plan tools: `orchestrator_task_get`
   shows none open), the orchestrator approves the spec (`orchestrator_spec_update` status `approved`; the server
   refuses 409 `decisions_open` while any is open). Subagents write documents in the copy
   `.scratchpad/<name>/spec/` (`orchestrator_spec_pull` creates it); the orchestrator runs
   `orchestrator_spec_push` after each edit. With mind map tools, record each final brief as a
   node linked to the task. Documents stay under 192 KiB. With `orchestrator_plan_*` too, the
   implementation plan is the spec's plan, not a file: `superpowers:writing-plans` writes the header with
   `orchestrator_plan_set` and the steps with `orchestrator_plan_steps_push`, and writes no `implementation.md`; the
   gate questions go out with `orchestrator_plan_questions_ask`; `superpowers:subagent-driven-development` takes work
   with `orchestrator_plan_step_next` (`claim: true`) and records branches and PRs with `orchestrator_plan_step_update`;
   the orchestrator runs `orchestrator_spec_pull` and `orchestrator_plan_export` into `.scratchpad/<name>/spec/`
   for the final reviewer, then pushes `retro.md` and archives the spec (`orchestrator_spec_update` status `archived`).
   Work running from an imported `implementation.md` finishes from it.
8. **Approved spec starts implementation.** A hive that receives "Spec S-<n> approved - take it into implementation now:
   <url>", or is started by the taskboard autostart with a prompt naming an approved spec, proceeds without re-asking:
   it claims the gate task, runs `superpowers:writing-plans` from the spec (unless the plan exists), then `superpowers:subagent-driven-development`, review, release, deploy, retro, archive.
9. **Approvals.** With `orchestrator_approval_*` tools: `plugins/workbench/rules/approvals.md`.
10. **Task classes.** Label the task `class:spike`, `class:bounded` or `class:architectural` when creating or
    claiming it; when unsure, the higher class. Items 1 and 3 apply in full only to `architectural`:
    - `spike`: throwaway or one-file exploration, no production merge. No research, spec or subagent-driven
      development; inline work by one subagent (item 5).
    - `bounded`: a change inside one component. Research is only `workbench:research-code-internal` (plus
      `workbench:research-docs` for a library used in a new way); one implementer per task; one review round (item 13), more only if findings need a fix.
    - `architectural`: cross-component, new subsystem or hard to reverse. Everything in full.
11. **Native mechanics over superpowers mechanics.**
    - `superpowers:dispatching-parallel-agents`: use native parallel subagents (several Agent calls per message).
    - `superpowers:using-git-worktrees`: served by `workbench:git-worktrees-*` under `.worktrees/<name>/<repo>`
      (item 3); the harness built-in worktree isolation is unused: in a metarepo it isolates the superrepo, not the submodule.
    - `superpowers:writing-plans`: lean plans; steps carry decisions, not code, and a LOC estimate; each is the
      smallest reviewable diff; over ~400 changed LOC lands as separate PRs.
    - `superpowers:finishing-a-development-branch`: before merging, `git status --porcelain` is empty in every repo (boy-scout rule).
    - `superpowers:verification-before-completion`: keep the skill text; mechanics move to the opt-in Stop hook
      `verify-on-stop.py` (`WORKBENCH_VERIFY_ON_STOP=1`).
12. **Tests earn their place.** `superpowers:test-driven-development` stays. Test only observable behaviour named in
    the plan step or spec (inputs to outputs, side effects at a boundary), never helpers, constants or framework
    behaviour. One test per behaviour; parametrise variants. No test whose
    failure would not signal a real defect; the reviewer (item 13) rejects them. Every task
    report states the net test count delta. Deleting them does not breach housekeeping rule 3.
    - Levels: unit, `integration`, `e2e` (`tests/e2e`), `live` (`tests/live`), marked.
    - Buckets: B1 `critical` (user flow, data integrity, security; `mise run test:critical` fast lane), B2 default,
      B3 deleted: config and structure tests (settings defaults and validation, chart/values/helmfile render,
      CI/mise/Dockerfile/README shape; chart check is `helm lint`) and duplicates (parametrise or delete).
    - agents-web: vitest, playwright e2e; boox: JVM unit, androidTest integration, roborazzi.
13. **Review.** Per task, run native `/code-review` (the `code-review` skill at effort `medium` for bounded, `high`
    for architectural; never `max` or `ultra` unless the user asks) for correctness, then
    `workbench:spec-reviewer` for scope and test value; spikes skip review. Findings go through
    `superpowers:receiving-code-review` (fix the real ones). Reviewable: lint clean, no new
    complexity `noqa`, diff within its LOC estimate or explained. This item replaces
    `superpowers:requesting-code-review`. Final branch review: `workbench:spec-reviewer` over the branch plus
    `/code-review` at `high`.
