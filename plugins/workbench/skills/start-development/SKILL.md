---
name: start-development
description: >
  Mandatory entry point for non-trivial development here (code/ submodules and the workbench itself):
  discovery, a plan with a scope ladder, one human gate that picks the rung, an implementation plan for
  that rung, then unattended to merge through plan-run (one implementer, one whole-diff reviewer, a retro).
---

# start-development

Phases 1 to 4 in order, a todo each, and **one gate** between phase 2 and phase 3.

`ticket.py` is `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py`. It owns every file under
`docs/plans/`, runs in the main checkout and commits its own changes as `chore(ticket): <plan> <event>` (if the user
answers no at the gate, the orchestrator commits them). Details: `references/tickets.md`.

## Modes

- **Component mode** - code in `code/` submodules; the plan ends in an MR from its integration branch (phase 4).
- **Meta mode** - the workbench superrepo itself (`.claude/`, `docs/`, root configs, `CLAUDE.md`, `MEMORY.md`,
  `ROADMAP.md`), no submodule. Meta mode plans commit on the integration branch `<plan>`, and the plan closes by
  rebase plus fast-forward of the local main, with or without an `origin` remote (`ticket.py close`); pushing main
  stays with the user. Work spanning both is two plans, meta first unless a dependency says otherwise.

A plan is one directory: `plan.md` (what and why, the scope ladder, the agreed scope), `implementation-plan.md`
(the agreed rung only, in chunks of steps) and, when the review passes, `retro.md`.

## Phase 1 - Discovery

Component mode first runs `git-submodules-refresh` (`submodule-auditor` on a stale, detached or unpushed checkout) and
finishes it first. Then `start-discovery` lanes as subagents (LSP sweep, `codebase-cartographer` per repo,
`start-research`, the reuse hunt), each writing one brief; you keep the brief paths, never their contents. Never skip
the tree state: run each repo's lint and tests now and keep the commands verbatim. Choose the research lenses, each
recorded in plan.md's Research section as ran, or skipped with the reason (a lens nobody decided on is a gap). Run
when: `research-code-internal`, the plan adds a helper, reader, parser, schema field or subsystem, or a repo has >
~200 source files; `research-code-external`, the change has known analogues or an open fork; `research-papers`, a
scientific or algorithmic core; `research-docs`, a library or platform API used in a new way, upgraded, or touched in
>= 3 call sites. Every brief ends in `## Plan inputs`: four lists, "none" when empty, one line per entry: `reuse`
(name - file:symbol - which plan items need it), `do-not-build` (item - what provides it instead - source),
`fix-as-ac` (anti-pattern - where - the step's Verify or Test first that pins the fix), `ideas` (adopted / rejected,
one line each, with the source). The plan-writer places every entry.

## Phase 2 - Plan

`ticket.py check --title "<title>"` lists near duplicates; extend one rather than start a twin. Then
`ticket.py new --title "<title>" --repos <a,b>` creates plan.md from the template, and one `workbench:plan-writer`
(opus) with `{plan, briefs[]}` fills it and commits it as `docs(plan): <plan> plan`: What and why, a scope ladder,
Non-goals, Design, Decisions with unstated defaults marked `(my call)`, open questions each with a recommended answer,
Research and Irreversible operations. The scope ladder runs from the absolute MVP (rung 1) to the most complete
delivery, cumulative: each rung includes everything above it. Several viable approaches or a costly-to-reverse
choice: `architect-researcher` (`fable` only for one framed consulting question). A contested or high-risk plan
(authz, secrets, concurrency, a rules engine, a data migration) gets one `workbench:interrogate` before the gate. Ask
the user only what no probe can answer: a fact is settled by a read-only probe, a preference is theirs.

## The gate

One message with one section per plan, so one gate may batch several plans, a section and a worktree each:
1. The plan.md path, and what and why in two lines.
2. The rungs, one line each, with the recommended rung.
3. The open questions, numbered, each with a recommended answer, worded so that "yes" accepts it.
4. The research lenses that ran and the ones skipped, with the reason; the `workbench:interrogate` verdict when it ran.
5. Every irreversible operation in scope (destroy, data deletion, secret rotation, shared force-push), by name.
6. "Pick a rung per plan and answer, or tell me what to change."

The user's answer is the only approval; nothing else records it. On changes, the plan-writer revises plan.md and the
gate is presented again. **Everything after the gate runs unattended to merge.** An irreversible operation not listed
at the gate stops it.

## Phase 3 - Implementation plan

The same plan-writer, continued with `SendMessage` and the user's answer verbatim, records Agreed scope and the
answers in plan.md, sets `rung`, writes implementation-plan.md for the agreed rung only (chunks with a model each,
steps with Files, Covers, Test first, Change, Verify, then Files to delete, Final verify, After merge) and commits it
as `docs(plan): <plan> implementation plan` (path: `ticket.py path <plan> implementation`). There is no second gate: the plan is the contract the reviewer checks.

## Phase 4 - Run

Invoke the `plan-run` skill; it runs this loop, written once there, and every agent call runs in the background, so
the session stays free to plan other work.
1. `ticket.py move <plan> in-progress`, from the main checkout, claims the plan (refused unless `rung` is set and
   implementation-plan.md exists) and creates the integration tree on branch `<plan>` (`references/worktrees.md`).
2. Per chunk, one `workbench:implementer`: sequential chunks in one tree, each told the plan path and its chunk
   number.
3. One reviewer, `workbench:reviewer` (sonnet), on the whole diff `git diff <base>...HEAD`: under-delivery against
   every agreed item and step, over-delivery of any change no step covers, then quality, following the `start-review`
   checklist; a diff touching secrets, SOPS, RBAC, ingress, privilege, CI vars, image pins or hooks also gets
   `security-researcher` (Terraform or charts: `tf-planner` / `helmfile-differ` when the `workbench-infra` pack is
   enabled). Findings go back in at most two fix rounds by `SendMessage` to the same agents. On a pass the reviewer
   writes retro.md.
4. One `worktree-merger` lands the plan: **meta mode** runs `ticket.py close <plan> --verify '<final verify>'` (rebase
   onto main in the tree, verify, fast-forward only when green, verify main; a rebase conflict is resolved in the plan
   tree, then close runs again). **Component mode** runs `git-worktrees-commit`, `git-worktrees-push`,
   `pullrequests-update`, `pullrequests-watch` (host per repo, `references/merge-hosts.md`) and merges the MR the
   moment it is green, mergeable and review-clean. Deploy: `pullrequests-watch --deploy`, or `python3
   ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/deploy-hook.py` for a `deploy` config
   (`references/workbench-config.md`); a step only the user may run follows `references/user-run-steps.md`.
   Post-deploy health: `grafana-debugging-start` when the `workbench-observability` pack is enabled, else the repo's
   `deploy.verify` command; a failed check continues in `start-debugging`. Then `ticket.py move <plan> done` removes
   the tree and branch and `ticket.py reap --plan <plan>` sweeps any left over.
5. ONE closing message, three lines at most (`concise-orchestrator`): the plan and retro.md paths, what needs the
   user, and retro.md's recommendations relayed one line each.

You never implement and never merge a tree yourself. `undelivered` and `discovered` are data: the first is a finding,
the second is recommended, never built, and relayed from retro.md.

## Non-negotiables

Full text in `references/non-negotiables.md`, the hooks behind them in `references/hooks.md`: **Delivery is not
optional** (only a named genuine blocker stops it). **Orchestrate. Do not implement** (set every subagent's model; at
400k tokens or 75% context, hand off with `handoff`). **Test-driven and verified** (the reviewer that did not write
the code verified it on HEAD). **Scope is not negotiable** (the agreed rung is the scope; under- and over-delivery are
findings; files over summaries; no "later" parking).
