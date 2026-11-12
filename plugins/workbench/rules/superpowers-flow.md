# Superpowers flow in this workbench

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
   `orchestrator_task_*` tools are available, the questions are posted as taskboard
   decisions with `orchestrator_decision_ask` (one option marked recommended; MVP marked in
   the option text), never as chat text; a chat line may link the task. Answers arrive as a
   chat notice `Task T-<n> was updated: <link>`; then call `orchestrator_task_get`. The
   question text still goes in `docs/plans/<name>/plan.md`, so it survives a dead leader (see item 7 for the server spec).
3. **Paths.** These override the superpowers locations, including the worktree location
   choice of `using-git-worktrees`:
   - worktrees: `<workbench root>/.worktrees/<name>/<repo>` for each repo involved
   - scratchpad: `<workbench root>/.scratchpad/<name>/`
   - logs of every tool the agents run: `<workbench root>/.logs/<name>/`
   - plan (spec): `docs/plans/<name>/plan.md`; implementation plan:
     `docs/plans/<name>/implementation.md` (instead of `docs/superpowers/specs` and
     `docs/superpowers/plans`); with the spec tools, item 7 places the plan, research and retro
4. **Final reviewer.** Besides correctness and completeness of the delivered work against
   the agreed scope (under- and over-delivery), the final reviewer writes
   `docs/plans/<name>/retro.md`: what came up during implementation and what was overlooked
   during discovery and planning. The orchestrator relays the retro recommendations in its
   closing message. With the spec tools, the retro is a document of the spec (item 7).
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
7. **Specs on the server.** Only when the `orchestrator_spec_*` tools are available;
   otherwise the `docs/plans/<name>/` paths of items 2-4 apply, with the implementation plan in
   `docs/plans/<name>/implementation.md`. Every task that goes through
   brainstorming gets a spec; small fixes keep only a task. The spec is spec `<name>` in the
   session's project. Its documents: `plan.md` (the brainstorming plan, with the question
   text), `research/<topic>.md` (the final brief of each research step only; lens briefs stay
   in `.scratchpad/<name>/`), `retro.md` (the final reviewer's retro). The improvement's own
   task (rule 6) is linked to the spec (`orchestrator_task_update` with `spec`) and holds the
   gate questions as decisions; when all are answered the gate is open (pressing Approve in
   the web is optional and records the approved versions). Subagents write the documents as
   files in the working copy `.scratchpad/<name>/spec/` (`orchestrator_spec_pull` creates
   it); the orchestrating agent pushes with `orchestrator_spec_push` after each edit (pushing
   is not editing). A document stays under 192 KiB: split a larger one. When the
   `orchestrator_plan_*` tools are available too, the implementation plan is the spec's plan,
   not a file: `superpowers:writing-plans` writes the header with `orchestrator_plan_set` and
   the steps with `orchestrator_plan_steps_push` (a JSON file a subagent writes in the working
   copy), and writes no `implementation.md`; the gate questions go out with
   `orchestrator_plan_questions_ask`; `superpowers:subagent-driven-development` takes work with
   `orchestrator_plan_step_next` (`claim: true`) and records branches and PRs with
   `orchestrator_plan_step_update`; the final reviewer reads the step history and the
   orchestrating agent pushes `retro.md`. Work already executing from an imported
   `implementation.md` finish from it.
