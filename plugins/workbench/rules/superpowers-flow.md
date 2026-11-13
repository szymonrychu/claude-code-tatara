# Superpowers flow in this workbench

The development flow is the vanilla `superpowers` plugin. These amendments override its
defaults here (superpowers gives user instructions precedence over its skills). `<name>` is
the improvement's kebab-case name.

1. **Research first.** Every development workflow starts with a research step before
   `superpowers:brainstorming` proposes a design: (a) the docs of every tool, library and
   system the implementation plans to use (`workbench:research-docs`), (b) a sweep of the
   existing codebase aimed at the most reviewable update, meaning reuse and the smallest
   coherent diff (`workbench:research-code-internal`), (c) when the `orchestrator_mindmap_*` tools
   exist, search the project mind map first.
2. **One human gate.** The brainstorming plan (spec) plus its questions is the only gate.
   The plan is more detailed than the superpowers default: what, why, research findings,
   design, files and components touched, test approach, risks, and the scope from MVP to
   complete. Every question offers options and always marks one option "MVP" and one
   "Recommended" (one option may carry both). After the user answers,
   `superpowers:writing-plans` writes the implementation plan with no second human review,
   and execution (`superpowers:subagent-driven-development`) starts only once every decision on its open tasks is answered
   and, with the spec tools, the spec is approved. When the
   `orchestrator_task_*` tools are available, the questions are posted as taskboard
   decisions with `orchestrator_decision_ask` (recommended option marked; MVP in
   the option text), never as chat text. Answers arrive as a
   chat notice `Task T-<n> was updated: <link>`; then call `orchestrator_task_get`. The
   question text still goes in `docs/plans/<name>/plan.md`, so it survives a dead leader (item 7).
3. **Paths.** These override the superpowers locations, including the `using-git-worktrees`
   location choice:
   - worktrees: `<workbench root>/.worktrees/<name>/<repo>` for each repo involved
   - scratchpad: `<workbench root>/.scratchpad/<name>/`
   - logs of every tool the agents run: `<workbench root>/.logs/<name>/`
   - plan (spec): `docs/plans/<name>/plan.md`; implementation plan:
     `docs/plans/<name>/implementation.md` (instead of `docs/superpowers/specs` and
     `docs/superpowers/plans`); with the spec tools, item 7 places the plan, research and retro
4. **Final reviewer.** Besides correctness and completeness of the delivered work against
   the agreed scope (under- and over-delivery), the final reviewer writes
   `docs/plans/<name>/retro.md`: what came up in implementation and what discovery and
   planning overlooked. The orchestrator relays the retro recommendations in
   closing. With the spec tools, the retro is a spec document (item 7).
5. **The orchestrator never edits.** It never updates code (source, tests, skills, agents,
   hooks, rules, docs); where a skill would edit inline, it dispatches a subagent. It is accountable for its subagents' work. Its duties: dispatching, reading
   results, running test and lint, and git merge and push of reviewed work.
6. **Taskboard lifecycle.** Only when the `orchestrator_task_*` tools are available;
   otherwise skip this rule. When work starts, create or claim a task
   (`orchestrator_task_create`, or `orchestrator_task_update` with `assignee_self`). Keep its
   todo current (`orchestrator_todo_set` / `orchestrator_todo_update`). When the work lands,
   close the task (status `done` or `dropped`).
7. **Specs on the server.** Only when the `orchestrator_spec_*` tools are available;
   otherwise the `docs/plans/<name>/` paths of items 2-4 apply, with the implementation plan in
   `docs/plans/<name>/implementation.md`. Every brainstormed task gets a spec; small fixes only a task. The spec is spec `<name>` in the
   session's project. Its documents: `plan.md` (the brainstorming plan, with the question
   text), `research/<topic>.md` (each research step's final brief; lens briefs stay
   in `.scratchpad/<name>/`), `retro.md` (the final reviewer's retro). The task
   (rule 6) is linked to the spec (`orchestrator_task_update` with `spec`) and holds the gate
   questions as decisions; with the plan pushed and `orchestrator_plan_gate` saying `approvable`
   (without plan tools: `orchestrator_task_get` shows none open), the orchestrating agent
   approves the spec (`orchestrator_spec_update` status `approved`; the server refuses
   409 `decisions_open` while any is open). Subagents write documents as
   files in the working copy `.scratchpad/<name>/spec/` (`orchestrator_spec_pull` creates
   it); the orchestrating agent pushes with `orchestrator_spec_push` after each edit (pushing is not editing).
   With mind map tools, record each final brief as a node linked to the task. A document stays under 192 KiB: split a larger one. With
   `orchestrator_plan_*` too, the implementation plan is the spec's plan, not a file:
   `superpowers:writing-plans` writes the header with `orchestrator_plan_set` and the steps
   with `orchestrator_plan_steps_push`,
   and writes no `implementation.md`; the gate questions go out with
   `orchestrator_plan_questions_ask`; `superpowers:subagent-driven-development` takes work with
   `orchestrator_plan_step_next` (`claim: true`) and records branches and PRs with
   `orchestrator_plan_step_update`; the orchestrating agent first runs `orchestrator_spec_pull` and
   `orchestrator_plan_export` into `.scratchpad/<name>/spec/` for the final reviewer; the orchestrating agent pushes `retro.md` and archives the spec (`orchestrator_spec_update` status `archived`). Work already executing from an imported
   `implementation.md` finishes from it.
