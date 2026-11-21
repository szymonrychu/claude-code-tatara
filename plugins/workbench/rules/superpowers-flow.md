# Superpowers flow in this workbench

The development flow is the vanilla `superpowers` plugin; these amendments override its defaults
here (user instructions take precedence over its skills). `<name>` is the improvement's
kebab-case name.

1. **Research first.** (Scaled by task class, item 10.) Every development workflow starts with a research step before `superpowers:brainstorming`
   designs: (a) the docs of every tool, library and system the plan uses (`workbench:research-docs`), (b) a sweep of the
   codebase for reuse and the smallest coherent diff (`workbench:research-code-internal`), (c) when the
   `orchestrator_mindmap_*` tools exist, search the project mind map first, (d) list every tool the plan calls and which role may call it.
2. **One human gate.** The brainstorming plan (spec) plus its questions is the only gate. The plan covers what, why,
   research findings, design, files and components touched, test approach, risks, and the scope from MVP to complete.
   Every question offers options, one marked "MVP" and one "Recommended" (one may carry both). After the
   user answers, `superpowers:writing-plans` writes the implementation plan without a second human review, and execution
   (`superpowers:subagent-driven-development`) starts only once every decision on its open tasks is answered and, with
   the spec tools, the spec is approved. When the `orchestrator_task_*` tools are available, the questions are posted as
   taskboard decisions with `orchestrator_decision_ask` (recommended option marked; MVP in the option text), never as
   chat text. Answers arrive as a chat notice `Task T-<n> was updated: <link>`; then call `orchestrator_task_get`. The
   question text still goes in `docs/plans/<name>/plan.md`, to survive a dead leader (item 7). When an answer changes the design, regenerate the plan summary.
3. **Paths.** (Spikes use none of them, item 10.) These override the superpowers locations (also for `using-git-worktrees`):
   - worktrees: `<workbench root>/.worktrees/<name>/<repo>` for each repo involved
   - scratchpad: `<workbench root>/.scratchpad/<name>/`
   - logs of every tool the agents run: `<workbench root>/.logs/<name>/`
   - plan (spec): `docs/plans/<name>/plan.md`; implementation plan: `docs/plans/<name>/implementation.md` (instead of
     `docs/superpowers/*`); with the spec tools, item 7 places the plan, research and retro
4. **Final reviewer.** The final reviewer is `workbench:spec-reviewer` (item 13): correctness and completeness
   against the agreed scope (under- and over-delivery). It writes only the retro (`docs/plans/<name>/retro.md`): what came up in
   implementation and what discovery and planning overlooked. The orchestrator relays its recommendations in closing. With the spec tools, the retro is a spec document
   (item 7).
5. **The orchestrator never edits.** It never updates code (source, tests, skills, agents, hooks, rules, docs); where a
   skill would edit inline, it dispatches a subagent, and answers for them. Duties: dispatching, reading results,
   test and lint, and git merge and push of reviewed work.
6. **Taskboard lifecycle.** Only when the `orchestrator_task_*` tools are available. When work
   starts, create or claim a task (`orchestrator_task_create`, or `orchestrator_task_update` with `assignee_self`). Keep
   its todo current (`orchestrator_todo_set` / `orchestrator_todo_update`). When the work lands, close the task (status
   `done` or `dropped`).
7. **Specs on the server.** Only when the `orchestrator_spec_*` tools are available (else items 2-4 paths apply). Every brainstormed task gets a spec `<name>` in the session's project; small fixes only a
   task. Its documents: `plan.md` (the brainstorming plan with its questions), `research/<topic>.md` (each research
   step's final brief; lens briefs stay in `.scratchpad/<name>/`), `retro.md` (the final reviewer's retro). The task
   (rule 6) is linked to the spec (`orchestrator_task_update` with `spec`) and holds the gate questions as decisions;
   with the plan pushed and `orchestrator_plan_gate` saying `approvable` (without plan tools: `orchestrator_task_get`
   shows none open), the orchestrating agent approves the spec (`orchestrator_spec_update` status `approved`; the server
   refuses 409 `decisions_open` while any is open). Subagents write documents as files in the copy
   `.scratchpad/<name>/spec/` (`orchestrator_spec_pull` creates it); the orchestrating agent pushes with
   `orchestrator_spec_push` after each edit (pushing is not editing). With mind map tools, record each final brief as a
   node linked to the task. A document stays under 192 KiB: split a larger one. With `orchestrator_plan_*` too, the
   implementation plan is the spec's plan, not a file: `superpowers:writing-plans` writes the header with
   `orchestrator_plan_set` and the steps with `orchestrator_plan_steps_push`, and writes no `implementation.md`; the
   gate questions go out with `orchestrator_plan_questions_ask`; `superpowers:subagent-driven-development` takes work
   with `orchestrator_plan_step_next` (`claim: true`) and records branches and PRs with `orchestrator_plan_step_update`;
   the orchestrating agent runs `orchestrator_spec_pull` and `orchestrator_plan_export` into `.scratchpad/<name>/spec/`
   for the final reviewer, then pushes `retro.md` and archives the spec (`orchestrator_spec_update` status `archived`).
   Work already executing from an imported `implementation.md` finishes from it.
8. **Approved spec starts implementation.** A hive that receives "Spec S-<n> approved - take it into implementation now:
   <url>", or is started by the taskboard autostart with a prompt naming an approved spec, proceeds without re-asking:
   it claims the gate task, runs `superpowers:writing-plans` from the approved spec (unless the plan exists),
   then `superpowers:subagent-driven-development`, review, release and deploy, retro and archive.
9. **Approvals.** With `orchestrator_approval_*` tools: `plugins/workbench/rules/approvals.md`.
10. **Task classes.** Label the task `class:spike`, `class:bounded` or `class:architectural` when creating or
    claiming it; when unsure, the higher class. Items 1 and 3 apply in full only to `architectural`:
    - `spike`: throwaway or one-file exploration, no production merge. No research, spec or subagent-driven
      development; inline work (the orchestrator never edits in code/).
    - `bounded`: a change inside one component. Research is only `workbench:research-code-internal` (plus
      `workbench:research-docs` for a library used in a new way); one implementer and one reviewer per task.
    - `architectural`: cross-component, a new subsystem or hard to reverse. Everything in full.
11. **Native mechanics over superpowers mechanics.**
    - `superpowers:dispatching-parallel-agents`: use native parallel subagents (several Agent calls in one message).
    - `superpowers:using-git-worktrees`: served here by `workbench:git-worktrees-*` under `.worktrees/<name>/<repo>`
      (item 3); the harness built-in worktree isolation is not used: in a metarepo it isolates the superrepo, not
      the submodule.
    - `superpowers:writing-plans`: lean plans; steps carry decisions, not code.
    - `superpowers:finishing-a-development-branch`: before merging, `git status --porcelain` is empty in every repo; uncommitted work is committed or cleared (boy-scout rule).
    - `superpowers:verification-before-completion`: keep the skill text; its mechanics move to the opt-in Stop hook
      `verify-on-stop.py` (`WORKBENCH_VERIFY_ON_STOP=1`).
12. **Tests earn their place.** `superpowers:test-driven-development` stays. Test only observable behaviour named in
    the plan step or spec (inputs to outputs, side effects at a boundary), never helpers, constants or framework
    behaviour. One test per behaviour; parametrise variants. No test whose
    failure would not signal a real defect. The per-task reviewer (item 13) rejects such tests; every task
    report states the net test count delta. Deleting them does not breach housekeeping rule 3.
13. **Review.** Per task, run native `/code-review` (the `code-review` skill at effort `medium` for bounded, `high`
    for architectural; never `max` or `ultra` unless the user asks) for correctness, then dispatch
    `workbench:spec-reviewer` for scope and test value; spikes skip review. Findings go through
    `superpowers:receiving-code-review` (judge each, fix the real ones). This item replaces
    `superpowers:requesting-code-review`. Final branch review: `workbench:spec-reviewer` over the whole branch plus
    native `/code-review` at `high`.
