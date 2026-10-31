# Upstream

This plugin is a vendored, adapted fork of superpowers. `mise run superpowers-diff <version>`
reads this file, clones the base and the given upstream release and prints, one per line, the
files under the vendored skill dirs that changed, were added or were removed. It reports only;
merging a change into the vendored copy stays a deliberate edit.

- Upstream URL: https://github.com/obra/superpowers
- Tag pattern: `v{version}`
- Base version: `7.0.0`

## Vendored skills

- `brainstorming`: discovery by subagents, questions batched at one gate, output is plan.md
  from `templates/plan.md` with a scope ladder and a recommended rung, written by one opus
  subagent briefed by `plan-writer-prompt.md`; the HARD-GATE is "nothing is built until the
  user picks a rung and answers the open questions"; no Visual Companion, no
  `docs/superpowers/specs`, no second approval.
- `writing-plans`: writes implementation-plan.md for the agreed rung only from
  `templates/implementation-plan.md` (chunks with a pinned model, steps with Files, Covers,
  Test first, Change, Verify); no second gate, no Native or Subagent-driven execution choice,
  no `docs/superpowers/plans`.
- `subagent-driven-development`: one `workbench:implementer` per chunk sequentially in one
  tree, one `workbench:reviewer` on the whole diff checking under- and over-delivery, at most
  two fix rounds by continuing the same agents, retro.md on a pass; no per-task reviewer, no
  5-round model escalation; `task-brief` splits on `## Chunk <k>:` headers and
  `re-review-prompt.md` is the fix-round prompt.
- `using-git-worktrees`: `ticket.py move <plan> in-progress` is the one way a plan tree is
  made; `ticket.py worktrees <plan> --refresh` reuses it.
- `requesting-code-review`: dispatches `workbench:reviewer` (sonnet) with `code-reviewer.md`,
  which holds the under- and over-delivery checklist and ends with retro.md on a pass.
- `finishing-a-development-branch`: no options menu; one `workbench:worktree-merger` lands
  the plan (meta mode `ticket.py close`, component mode merges the PR the moment it is green,
  mergeable and review-clean), then `ticket.py move <plan> done` and `ticket.py reap`.
- `systematic-debugging`: em dashes dropped, `find-polluter.sh` made shellcheck-clean, a
  post-deploy failure continues from `grafana-debugging-start`; no CREATION-LOG or test-*.md.
- `test-driven-development`: em dashes dropped, cross references limited to vendored skills.
- `verification-before-completion`: em dashes dropped, cross references limited to vendored
  skills.
- `receiving-code-review`: names `pullrequests-review-loop` for PR threads and the two-round
  cap.
- `dispatching-parallel-agents`: every dispatch sets the model per AGENTS.md ground rule 2.
- `using-superpowers`: names `brainstorming` as the entry for non-trivial work, one gate, the
  scope ladder and two fix rounds; tool references only for Claude Code, Codex, Gemini and
  Antigravity; its SessionStart hook runs `hooks/session-start`, no `run-hook.cmd`.

Every vendored file has its em dashes (U+2014) replaced by " - "; LICENSE is kept byte for byte.
