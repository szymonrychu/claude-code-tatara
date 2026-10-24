# Lean development flow design

## Summary

Replace the plan-execute Workflow (2952 lines plus 44 test files), the independent verifier, the split spec and quality reviewers, review tiers, triage and false-finding classifiers, the approval ledger, per-task worktrees with in-run landing and forward merges, and the heartbeat watcher with an instruction-driven loop the orchestrator runs over the existing epic and task files: one implementer and one reviewer per task, fix rounds that continue the same agents, one scope audit per epic, one integration worktree per epic. Planning (epics and tasks as files under docs/plans, created with ticket.py) stays as it is and stays decoupled from execution through a new `epic-run` skill.

## Intent and why

The flow solves the right problem: agents silently narrow the agreed scope, so an implementer's claim must be checked by someone who did not write the code, against acceptance conditions, with the tests run on the committed HEAD. The machinery built around that idea is now the cost: the three recorded epics (21 to 23 tasks each) took four to seven plan-execute runs and about six agent sessions per task (implementer, verifier, reviewer, fixer, verifier, land, plus triage and classifier calls), and the orchestrator reads a 25-field return after every run. The user wants the guarantee kept and the orchestration dropped: push on model quality and instructions, keep the epic and task planning they like.

## Goals

- About 2N+3 agent sessions for an epic of N tasks (implementer and reviewer per task, planner, scope auditor, record writer); no Workflow run, no heartbeat.
- Every task still has acceptance conditions; a reviewer who did not write the code runs the verify command on HEAD and checks each AC against the files; one scope auditor per epic checks README goals and every AC against the integrated diff.
- An epic planned in one session can be executed from any other with `epic-run`; the orchestrator keeps planning while implementers run in the background.
- One integration worktree per epic, tasks in dependency order inside it, no per-task trees, landing, forward merges or rulings files.
- Every removed mechanism is pinned removed by a retirement test; every remaining doc describes the lean flow; `mise run test` and `mise run lint` are green on main.

## Non-goals

- Changing the hooks, init, template-update, component skills, git and pull-request skills, start-debugging, start-research, start-discovery, interrogate or the research agents beyond wording.
- A nested epic-runner agent that spawns its own subagents.
- A release or CHANGELOG entry.
- The user's global rules file outside this repository (it names plan-execute; the user updates it).

## Anti-goals

- Reintroducing orchestration in prose: a SKILL.md that re-describes tiers, gates and return fields is the same cost in a different file. SKILL.md is capped at 150 lines.
- Losing the structural checks: an implementer's own "verified" claim must never be the record.
- A red main at any task boundary.

## Constraints

- Hooks run under bare python3 3.9+; nothing here touches them beyond a docstring.
- `ticket.py` keeps its restricted frontmatter, the writer rule (main checkout only, self-committing) and slugs; existing done epics under docs/plans/done keep their old fields and must still load.
- `mise run test` and `mise run lint` green at every task commit; retirement tests assert on `git ls-files`.
- Meta mode: tasks commit on branch `lean-development-flow` in the integration tree; the epic closes by `ticket.py close` (rebase, verify, fast-forward local main); nothing is pushed.

## Decisions

### D1: One integration worktree per epic, tasks sequential inside it
Tasks run in `ticket.py tasks` dependency order in the epic's integration tree, each committing on branch `<epic>`. Alternatives: keep per-task worktrees with in-run landing (today; the landing, forward-merge, fork-point and MERGE-line machinery is about a third of plan-execute.js and most of the escalation reasons), or let the orchestrator pick parallel trees for disjoint tasks (reintroduces merging). Why: intra-epic parallelism bought little (tasks of one epic share files and tests) and cost the most code; parallelism stays across epics, which is what the user uses. (my call)

### D2: Fix rounds continue the same agents
A reviewer's findings go back to the same implementer with SendMessage, and the re-review to the same reviewer; at most two fix rounds, then the task is `escalated` for the orchestrator's judgement. Alternatives: a fresh fixer per round (today; it re-reads everything), unlimited rounds (ran 9 and 5 before the cap). Why: the context is already paid for; a continued agent sees its own diff and the findings. (my call)

### D3: One reviewer replaces verifier, spec-reviewer, quality-reviewer, tiers and triage
Per task, one sonnet reviewer: clean tree and HEAD, run verify on HEAD, every AC against the files, debt-marker grep, then quality. Alternatives: keep the script verifier (1012 lines plus a haiku relay) and the split reviewers; keep tiers. Why: the verifier's checks are five shell commands any reviewer runs; the split existed to shorten prompts for sonnet, and the records show the extra sessions, not extra findings. Risky diffs keep `interrogate` as an opt-in panel.

### D4: The approval ledger goes; the gate approves README goals and task acceptance conditions
Alternatives: keep approvals.json with ids mapped to tasks. Why: with every task carrying ACs and the auditor reading README goals, the ledger is a second copy of the same list; it added `decide`, `questions` plumbing, per-item statuses in the return and a record table. `questions` stays, writing design.md's Open questions. (my call, Q4)

### D5: Task frontmatter slims to ten keys
title, status, repo, value, files, verify, depends_on, model, review, verified_head. owns, uses, provides (shared-parts machinery for parallel trees), estimate*, actual* (calibrated on run actuals that no longer exist), worktree, branch, run go. `ticket.py task <epic> <task> --status ...` records outcomes. (Q1 covers estimates)

### D6: Per-task model is a planning decision
The planner sets `model`: opus when the task adds a module or touches more than five files, else sonnet; the planner itself runs on opus. Reviewer and scope auditor on sonnet. Why: the user's stated lever is model quality and instructions; precise ACs and a strong planner are where scope is protected cheapest.

### D7: `epic-run` is the execution entry point
A short skill that runs the phase 4 loop of start-development for one planned epic from any session; start-development phase 4 invokes it. Why: planning and execution are decoupled by the user's request, and a skill name is what a fresh session can be told.

### D8: The loop runs in the orchestrator session with background dispatches
Agent calls run in the background and notify on completion, so the session stays free to plan another epic between notifications. Alternatives: a nested opus epic-runner agent spawning implementers (unproven that a subagent can dispatch subagents here; would need a probe). (my call, Q2)

### D9: Scope audit once per epic
`scope-auditor` reads README goals and non-goals plus every task's ACs against `git diff <base>...<epic>` and the files, with the cross-task duplicate sweep. Gaps become new tasks via `new-task`; the epic cannot close while a task is not done.

### D10: Everything removed is pinned removed
Retirement tests on `git ls-files` for the workflows directory, heartbeat, verifier scripts, the run-loop subcommands, the split reviewers and the deleted references; a word test over the plugin and the root docs for the retired vocabulary.

### D11: This epic runs on the lean loop
Dogfooding: the orchestrator runs D1, D2, D3 by hand on this epic (no plan-execute run), which also proves the loop before the docs claim it. (Q3)

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| research-code-internal | skipped: the plan deletes helpers and adds one subcommand and one skill; the reuse hunt would scan code being removed | | |
| research-code-external | skipped: the design is a reduction of in-house flow, no analogue to survey | | |
| research-papers | skipped: no algorithmic core | | |
| research-docs | skipped: no library or platform API changes; the Agent tool's SendMessage continuation is documented in the tool list of this harness (docs/plans/todo/lean-development-flow/README.md Description) | | |

Discovery was done inline by the orchestrator (the three records under docs/plans/done, plan-execute.js's dispatch map, ticket.py's subcommands, the harness emitter and the root tests), per the non-negotiables' exception for a brief that would cost more than the answer.

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 one integration tree, sequential tasks | ticket-lean-tasks, agents-lean-roles, start-development-rewrite |
| D2 fix rounds continue the same agents | agents-lean-roles, start-development-rewrite, epic-run-skill |
| D3 one reviewer | retire-verifier-scripts, agents-lean-roles |
| D4 ledger goes | ticket-drop-run-commands, ticket-lean-tasks, start-development-rewrite |
| D5 lean task frontmatter | ticket-lean-tasks |
| D6 per-task model | agents-lean-roles, start-development-rewrite |
| D7 epic-run | epic-run-skill, start-development-rewrite |
| D8 orchestrator loop, background dispatches | start-development-rewrite, epic-run-skill, root-docs-and-rules |
| D9 scope audit once per epic | agents-lean-roles, start-development-rewrite |
| D10 retirement tests | remove-workflows, retire-verifier-scripts, ticket-drop-run-commands, agents-lean-roles, start-development-rewrite, skills-wording, root-docs-and-rules |
| D11 dogfood | start-development-rewrite |

## Review focus

- `ticket-lean-tasks`: the loader must still read the done epics' old frontmatter; `close` without the containment gate must still refuse a failed verify.
- `agents-lean-roles`: the reviewer's order (verify on HEAD before quality) and the implementer's `undelivered`/`discovered` rules are the scope protection now; a reviewer that skips step 2 is the regression to watch.
- `start-development-rewrite`: the 150-line cap; the gate list; no return-field vocabulary creeping back.

## Left to the builder

- Exact wording of the agent files and SKILL.md within the stated rules and caps.
- Test file names beyond the ones the ACs name.
- Whether `tasks <epic>` orders by a stable topological sort or by file order with a dependency check, as long as a dependency precedes its dependents.

## Assumptions and unknowns

- SendMessage continuation of a finished background agent keeps its context (stated by the Agent tool description of this harness); confirmed by use on the first task of this epic.
- `mise run harness-setup` regenerates only the rules block of AGENTS.md; confirmed by running it in root-docs-and-rules.
- Baseline suite is green on main (the background `mise run test` run started during discovery; its tail is read before the gate).

## Open questions

- Q1: Drop time estimates and the README Time line entirely? [recommended: yes; the formula was calibrated on run actuals that no longer exist, and the user's earlier request for estimates was for the plan-execute runs]
- Q2: Run the loop in the orchestrator session with background dispatches, no nested epic-runner agent now? [recommended: yes; nested dispatch from a subagent is unproven here, and background dispatches already keep the session free for planning; a probe can be a later epic]
- Q3: Execute this epic on the lean loop by hand (no plan-execute run)? [recommended: yes; it dogfoods D1-D3 and avoids a 4-7 run marathon on a 9-task deletion epic]
- Q4: Drop the approval ledger so approving the gate message approves README goals plus every task's ACs? [recommended: yes; the auditor reads both, and the ledger duplicated them]

## Irreversible operations in scope

none beyond tracked-file deletions, all recoverable from git history; nothing is pushed.
