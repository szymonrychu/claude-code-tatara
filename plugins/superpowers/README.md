# superpowers

The development flow of this workbench: a vendored, adapted fork of superpowers 7.0.0
(MIT, see `LICENSE` and `NOTICE`). The `workbench` plugin keeps the tooling the flow
dispatches (implementer, reviewer and worktree-merger agents, research skills, worktree and
pull request skills, hooks).

## The flow

`brainstorming` -> one gate -> `writing-plans` -> `subagent-driven-development` ->
`finishing-a-development-branch`.

- `brainstorming`: discovery by subagents, then plan.md with a scope ladder from MVP to
  complete and open questions with recommended answers, then one gate where the user picks a
  rung and answers. Nothing is built before that.
- `writing-plans`: implementation-plan.md for the agreed rung only, chunks with a pinned
  model, steps with Files, Covers, Test first, Change and Verify.
- `subagent-driven-development`: one implementer per chunk in one plan tree, one reviewer on
  the whole diff for under- and over-delivery, at most two fix rounds, retro.md on a pass.
- `using-git-worktrees`: the plan tree comes from `ticket.py move <plan> in-progress`.
- `requesting-code-review`: the whole-diff review brief (`code-reviewer.md`).
- `finishing-a-development-branch`: lands the plan without a menu.

Disciplines the flow leans on: `test-driven-development`, `verification-before-completion`,
`systematic-debugging`, `receiving-code-review`, `dispatching-parallel-agents`.
`using-superpowers` and its SessionStart hook (`hooks/session-start`) route a fresh Claude
Code session to the flow; other harnesses read AGENTS.md ground rule 1.

## Plans

`scripts/ticket.py` keeps the plan lifecycle in `docs/plans/{todo,in-progress,done}/<slug>/`
(`new`, `check`, `path`, `rename`, `move`, `worktrees`, `close`, `migrate`, `reap`), with the templates in `templates/`
(plan.md, implementation-plan.md, retro.md).

## Upstream

`UPSTREAM.md` records the upstream URL, the tag pattern, the base version and the per-skill
adaptations. `mise run superpowers-diff <version>` prints the vendored skill files a newer
upstream release changed, added or removed. It reports only; porting a change is a deliberate
edit.

## Tests

`mise run test:superpowers` (`pytest plugins/superpowers/tests`) and
`mise run lint:superpowers`.
