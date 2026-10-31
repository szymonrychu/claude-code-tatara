---
name: finishing-a-development-branch
description: "Use when a plan's review passed and retro.md exists: one workbench:worktree-merger lands it (meta mode ticket.py close, component mode the pull request merged the moment it is green, mergeable and review-clean), the plan moves to done, and one closing message relays retro.md's recommendations. No options menu."
---

# Finishing a Development Branch

## Overview

**Core principle:** Verify -> land -> clean up -> one closing message. The integration decision was made at the brainstorming gate: the user's answer approved the run to merge, so there is no menu here and nothing to ask.

`ticket.py` is `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/ticket.py`, run from the main checkout. You never merge a tree yourself: one agent does.

## Step 1: Entry Conditions

- The whole-diff review passed and retro.md exists at `ticket.py path <plan> retro` (superpowers:requesting-code-review). Without it `ticket.py close` and `ticket.py move <plan> done` refuse.
- The Final verify of implementation-plan.md is the command every landing verifies with.
- The mode is the plan's: meta mode (the workbench superrepo, no submodule) or component mode (code in `code/` submodules).

## Step 2: Land

Dispatch one `workbench:worktree-merger` (sonnet), opus only when the workbench plugin's `skills/worktree-merge/scripts/merge.py --name <plan> --assess` predicts a conflict, in the background, with the model set explicitly:

```
[wb <plan>/merge]
Plan: <plan>. Mode: <meta|component>. Final verify: <final verify>.
ticket.py: <absolute ticket.py path> (run it from the main checkout).
Tree: <tree>, branch <plan>.
Report in at most 150 words.
```

The merger gets the absolute ticket.py path because its own plugin root is another plugin's.

**Meta mode.** The merger runs `ticket.py close <plan> --verify '<final verify>'`: it rebases `<plan>` onto main in the plan tree, runs the verify on the rebased tip there, fast-forwards main only when that verify is green, runs the verify on main, writes `close.json`, moves the plan to done and sweeps its tree. A failed verify is exit 4 and main does not move. A rebase conflict is resolved in the plan tree, then close runs again. Pushing main stays with the user.

**Component mode.** The merger runs `git-worktrees-commit`, `git-worktrees-push`, `pullrequests-update` and `pullrequests-watch` (host per repo, the workbench plugin's `references/merge-hosts.md`) and merges the pull request the moment it is green, mergeable and review-clean. Review threads go through `pullrequests-review-loop`. Deploy: `pullrequests-watch --deploy`, or the workbench plugin's `scripts/deploy-hook.py` for a `deploy` config; a step only the user may run follows the workbench plugin's `references/user-run-steps.md`. Post-deploy health: `grafana-debugging-start` when the `workbench-observability` pack is enabled, else the repo's `deploy.verify` command; a failed check continues in superpowers:systematic-debugging.

## Step 3: Clean Up

`ticket.py move <plan> done` (meta mode: close already did it) removes the tree and branch, and `ticket.py reap --plan <plan>` sweeps any tree left over. If a tree cannot be removed, leave it and name it in the closing message: named and stranded beats silently dropped.

## Step 4: One Closing Message

ONE closing message, three lines at most:

1. The plan landed and how it was verified (the Final verify summary line), the plan.md and retro.md paths.
2. What needs the user, if anything (a push of main in meta mode, a user-run step, a stranded tree), and the rulings the run took on their behalf, from the ledger.
3. retro.md's Recommendations relayed one line each.

## Quick Reference

| Mode | Lands by | Verify | Then |
|------|----------|--------|------|
| meta | `ticket.py close` (rebase, verify, fast-forward) | Final verify on the rebased tip and on main | close moved it to done; `ticket.py reap --plan <plan>` |
| component | the pull request, merged when green, mergeable, review-clean | CI and `pullrequests-watch` | `ticket.py move <plan> done`; `ticket.py reap --plan <plan>` |

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "Tests passed earlier this session" | The merger verifies on the tree it is about to land, and on main after. A green run only proves the tree it ran on. |
| "I'll ask which way to integrate" | The gate approved the run to merge. Land it. |
| "I'll merge it myself, it's one command" | One `workbench:worktree-merger` lands every plan; you never merge a tree yourself. |
| "The PR is green, I'll wait for the others" | Merge it the moment it is green, mergeable and review-clean. |
| "Removal refused - `--force` is just finishing the cleanup" | The refusal means files exist only in that tree. Name it and leave it. |
| "The push was rejected - force-push will fix it" | A rejected push means the remote moved. Rebase and verify again; never force-push a shared branch. |
| "The merged-result failure is probably flaky" | A failing verify stops the landing. Main does not move while you investigate. |
