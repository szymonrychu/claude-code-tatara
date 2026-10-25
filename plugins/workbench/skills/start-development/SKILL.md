---
name: start-development
description: >
  Mandatory entry point for non-trivial development here (code/ submodules and the workbench itself):
  size, discovery, design doc and task files, then one approval gate; after it, unattended to merge through
  epic-run (one implementer and one reviewer per task, one scope audit per epic) and a record.
---

# start-development

Phases 0 to 7 in order, a todo each, and **one approval gate** between phase 3 and phase 4.

`ticket.py` is `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/ticket.py`. It owns every file under
`docs/plans/`, runs in the main checkout and commits its own changes as `chore(ticket): <epic> <event>` (if the user
answers no at the gate, the orchestrator commits them). Details: `references/tickets.md`.

## Modes

- **Component mode** - code in `code/` submodules; the epic ends in an MR from its integration branch (phase 6).
- **Meta mode** - the workbench superrepo itself (`.claude/`, `docs/`, root configs, `CLAUDE.md`, `MEMORY.md`,
  `ROADMAP.md`), no submodule. Meta mode tasks commit on the integration branch `<epic>`, and the epic closes by
  rebase plus fast-forward of the local main, with or without an `origin` remote (`ticket.py close`); pushing main
  stays with the user. Work spanning both is two epics, meta first unless a dependency says otherwise.

## Phase 0 - Size the work

Say the size and why in one line; borderline starts lean. Both are one epic with task files, one gate, one loop.
- **Lean** when all hold: one repo, about ten files you can name, no new cross-repo interface, schema or
  deployment-topology change, nothing expensive to reverse, no design fork. Lean skips the lenses and design.md: phase
  1 is your own recon, you write the tasks with `epic-task-create` (`ticket.py new-task --points <n>`).
- **Full** when any holds: more than one `code/` submodule, a cross-repo contract, a genuine fork worth a human
  decision, authz, secrets, cluster exposure or container privilege, or files you cannot name yet.

## Phase 1 - Discovery

Component mode first runs `git-submodules-refresh` (`submodule-auditor` on a stale, detached or unpushed checkout) and
finishes it first. Then `start-discovery` (LSP sweep, `codebase-cartographer` per repo, `start-research`, the reuse
hunt), one brief. Never skip the tree state: run each repo's lint and tests now and keep the commands verbatim.
Optional lenses, each recorded in design.md's Research section as ran, or skipped with the reason (a lens nobody
decided on is a gap). Run when: `research-code-internal`, the plan adds a helper, reader, parser, schema field or
subsystem, or a repo has > ~200 source files; `research-code-external`, the change has known analogues or an open
fork; `research-papers`, a scientific or algorithmic core; `research-docs`, a library or platform API used in a new
way, upgraded, or touched in >= 3 call sites. Every brief ends in `## Plan inputs`: four lists, "none" when empty, one
line per entry: `reuse` (name - file:symbol - which plan items need it), `do-not-build` (item - what provides it
instead - source), `fix-as-ac` (anti-pattern - where - the acceptance condition), `ideas` (adopted / rejected, one
line each, with the source). The planner places every entry (task Notes, a removed item, an AC, Research).

## Phase 2 - Design doc

`ticket.py check --title "<title>"` lists near duplicates; extend one rather than start a twin. Then `epic-create`
(`ticket.py new-epic --title "<title>"`) writes the README: project brief (what, how, why), description, goals,
non-goals. Several viable approaches or a costly-to-reverse choice: `architect-researcher` (`fable` only for one
framed consulting question). Ask the user only what no probe can answer: a fact is settled by a read-only probe, a
preference is theirs. Full size: design.md from `templates/design.md` at `ticket.py path <epic> design`, unstated
defaults marked `(my call)`.

## Phase 3 - Tasks

Dispatch one `workbench:planner` (opus) with `{epic, briefs[], userDecisions[]}`. Through `epic-task-create` it writes
each task: a verbatim requirement, acceptance conditions with `test:` or `command:` evidence, `files`, a targeted
`verify`, `depends_on`, and `model` (opus when it adds a module or touches more than five files, else sonnet); one
test file's worth of behaviour, at most 8 files. `ticket.py lint <epic>` must print `lint: ok`. Then the **builder
check**: one general-purpose agent on sonnet, no prior context, prompted "You are a talented engineer in this domain,
handed the epic at <epic-dir>: its README.md, its design.md (absent when lean) and the task files under tasks/. Report
only the questions you would still need answered before building, one numbered line each, or 'no questions'."  Settle
the answered and minor ones in the docs, marked `(my call)`; probe facts, never ask them; preference calls go to the
gate. A contested or high-risk design (authz, secrets, concurrency, a rules engine, a data migration) gets one
`workbench:interrogate` before the gate.

## The gate

One message, in this order:
1. The epic README and design.md paths, and the project brief (what, how, why).
2. The task table: id, title, value, files, depends_on, model, points, expected_minutes, expected_tokens.
3. The research lenses that ran and the ones skipped, with the reason.
4. The builder check's remaining questions as one batch, numbered, each with a recommended answer, worded so that
   "yes" accepts it (`ticket.py questions` gathers the open ones of every todo epic).
5. The `workbench:interrogate` verdict, when it ran.
6. Every irreversible operation in scope (destroy, data deletion, secret rotation, shared force-push), by name.
7. "Approve, or tell me what to change."

Approving the message approves the README goals and every task's acceptance conditions; nothing else records approval.
On changes: revise the docs and tasks (`ticket.py amend`), re-lint, re-present. One gate may cover several epics, each
under its own heading. **Everything after the gate runs unattended to merge.** An irreversible operation not listed at
the gate stops it.

## Phase 4 - Execute

Invoke the `epic-run` skill; it runs this loop, written once here, and every agent call (implementer, reviewer, each
continued in a fix round) runs in the background, so the session stays free to plan other epics.
1. Claim the epic: `ticket.py move <epic> in-progress` creates the integration tree on branch `<epic>`
   (`references/worktrees.md`). Every `ticket.py` call stays in the main checkout.
2. For each task in `ticket.py tasks <epic>` order, sequential, every dependency before its dependents: note the
   tree's HEAD, then one `workbench:implementer` (model from the task) with the task file verbatim and the tree path.
3. On its return, one `workbench:reviewer` (sonnet) with the task file, the tree path and the commit the task started
   from: the reviewer checks a clean tree at HEAD, runs the task's `verify` on HEAD, checks every acceptance
   condition against the files, greps for debt markers, then reviews quality. While it reports unmet conditions or
   findings, continue the same implementer with `SendMessage`, then the same reviewer: at most two fix rounds.
4. Clean: `ticket.py task <epic> <task> --status done --verified-head <head> --points-actual <reviewer's pointsActual>`.
   Open after the cap: `--status escalated --note "<open findings>"`; skip its dependents. After the last: phases 5-7.

Rules: `undelivered` is a finding; `discovered` becomes a new task in the same epic (`ticket.py new-task --points <n>`); an
escalated task is yours to judge: a sharper requirement (`ticket.py amend`) or `workbench:interrogate` once. The epic
cannot close while a task is not `done`; never implement a task yourself, never merge a tree yourself.

## Phase 5 - Epic review

1. `ticket.py stage <epic> review` (refuses while a task is open).
2. Whole-diff `start-review` on `git diff <base>...<epic>`; `workbench:interrogate` for a high-risk diff.
3. One `scope-auditor` (sonnet) with the README, the task files, the tree and the base: goals, non-goals and every
   acceptance condition against the integrated diff, plus the duplicate sweep.
4. The one full-suite run: the repo's `suites` from `.claude/workbench.json`, else
   `"${CLAUDE_PLUGIN_ROOT}/skills/worktree-merge/scripts/suite-lock.sh" -- mise run test`, and `mise run lint`.
5. Security: a diff touching secrets, SOPS, RBAC, ingress, privilege, CI vars, image pins or hooks gets
   `security-researcher`; Terraform or charts: `tf-planner` / `helmfile-differ` when the `workbench-infra` pack is
   enabled.
6. Each real gap or finding becomes a new task (`ticket.py new-task --points <n>`), then `ticket.py stage <epic> build` and phase
   4; a wrong one is dropped with the reason in your notes. Clean: `ticket.py review <epic> --verdict pass
   --notes-file <notes>` (`--verdict fail` goes back to build).

## Phase 6 - Close or merge

- **Meta mode:** `ticket.py close <epic> --verify '<full suite and lint>'` rebases `<epic>` onto main in the
  integration tree, verifies the rebased tip, fast-forwards main only when green, then verifies main. A rebase
  conflict: `worktree-merger` in that tree, then close again.
- **Component mode:** `git-worktrees-commit`, `git-worktrees-push`, `pullrequests-update` for the MR from the
  integration branch; `pullrequests-watch`, acting on each `RESOLVED` line as it arrives (host per repo,
  `references/merge-hosts.md`); merge each MR the moment it is green, mergeable and review-clean. Deploy:
  `pullrequests-watch --deploy`, or `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/deploy-hook.py`
  for a `deploy` config (`references/workbench-config.md`); a step only the user may run follows
  `references/user-run-steps.md`. Post-deploy health: `grafana-debugging-start` when the `workbench-observability`
  pack is enabled, else the repo's `deploy.verify` command; a failed check continues in `start-debugging`.
- **Then** `ticket.py move <epic> done` (`epic-move`) removes the integration tree and branch, and
  `epic-worktrees-remove` (`ticket.py reap --epic <epic>`) removes every remaining worktree of the epic.

## Phase 7 - Record

Dispatch `record-writer` (sonnet) with the epic slug, base and branch per repo, MR URLs and your notes (per task:
review rounds, the reviewer's verification tail; escalations judged, findings dropped); it fills `templates/record.md`
at `ticket.py path <epic> record`. Then `ticket.py retro <epic>` and `retro-writer` (sonnet): `references/retro.md`.
ONE closing message, three lines at most (`concise-orchestrator`): both paths, what needs the user, what is blocked.

## Non-negotiables

Full text in `references/non-negotiables.md`, the hooks behind them in `references/hooks.md`: **Delivery is not
optional** (only a named genuine blocker stops it). **Orchestrate. Do not implement** (set every subagent's model; at
400k tokens or 75% context, hand off with `handoff`). **Test-driven and verified** (a task is done when a reviewer
that did not write it verified it on HEAD). **Scope is not negotiable** (requirements verbatim, `undelivered` and
`discovered` as data, files over summaries; no "later" parking).
