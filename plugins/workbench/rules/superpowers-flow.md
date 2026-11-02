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
