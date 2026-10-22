# Flow speed and token optimization design

## Summary

The plan-execute flow keeps every check it has (independent verifier on HEAD, review loop, scope
audit, approval ledger) and stops paying for the parts that measured as waste in the 2026-10-20/21
session: full-suite verifies pinned at the 600 s Bash cap, a third TDD-revert run, AC refs that name
renamed tests, gate findings on dependency text, cascades from medium findings, orchestrator
wake-ups and manual relaunch steps, three haiku calls per verify, inlined audit context. Estimates
become agent minutes from a fitted formula (`minutes = 4.0 * (files + 1)^0.22 * (6.9 if the verify
is the full suite else 1)`), with an epic line `k * max(critical path, sum / P)`, and actuals are
stamped from the run's transcripts so the record compares the two. Template only: `plugins/workbench`,
root `AGENTS.md` and `MEMORY.md`. Planned against the code as it will be after epic
integration worktrees lands (blocker).

Epic estimate with the new formula (16 tasks, all targeted verifies): sum 92 agent-min, critical path
45 min (verify-task-bounded-runs, verify-scope-wiring, ac-evidence-map, gate-provenance,
review-tiering, cascade-release, audit-context-and-models, cache-prefix-change), P = 1.6, run wall
58 min, expected wall at k = 2.0: 115 min (about 1.9 h), plus one relaunch for the cache probe (D6).

## Intent and why

The user asked (U1) for an epic that cuts token usage and speeds delivery while keeping the review
loop and the task-completeness checks, based on this session's epics, and (U2) for realistic task
estimates in agent time plus an epic delivery estimate. The brief
(`docs/research/flow-token-optimization.md`, gitignored; numbers copied here) measured 592 workflow
agents (30.4M cost-weighted tokens, 1942 agent-minutes) and the orchestrator (19.3M cw):

- Verification is 55% of agent-minutes; full-suite tasks are 32% of tasks but 71% of agent-minutes,
  each verify pinned at the 600 s Bash cap; `--tdd-revert` runs the suite three times.
- Rounds beyond the first are 38% of agent-minutes; 56% of fix rounds carry a `ref-missing` AC
  finding (the AC names a test written under another name); forward-merged gate text and process-only
  TDD findings add 29 fix rounds.
- Heartbeat plus notification turns are 70% of orchestrator tokens.
- 19 root escalations caused 183 dependency-failed task-runs and 11 relaunches; epic A took 913 min
  wall against about 450 predicted by its critical path.
- Planner estimates are 6.9x high at the median and uncorrelated with actuals (r = 0.10); `actual`
  is always 0 because nothing produces `durationMs` and the `--run-dir` fallback misses `#n` labels.

## Goals

- A verify never runs the full suite inside the task loop: a task's `verify` is targeted (the lint
  fails a full-suite one on an unstarted task), verify-task runs the command at most twice with
  `--tdd-revert`, every subprocess is bounded and reports `timeout`, and a non-sha `--prev-head`
  never reaches argparse.
- An AC ref that names a renamed test resolves through the implementer's `acEvidence` map or a
  file-plus-substring match, with `matchedBy` recorded for the auditor.
- Parking and debt gates never report a line that came from a merged dependency branch.
- Dependents of a dependency verified with only process or only medium findings start in the same
  run; continue auto-accepts `processOnly` and `triageRejected` tasks; a relaunch never re-runs a
  done task.
- Review tier `skip` covers doc-only and test-only diffs with every AC met; light-tier fixes to
  reviewer findings get a scoped re-review; RISK_PATH stays `full`; the verifier gets the requirement.
- The heartbeat makes no haiku call by default and wakes the orchestrator only on a changed digest
  (at most every 30 minutes), STALL or END; `ticket.py continue --launch` does continue, clean
  landings and args in one command and prints the one Workflow launch and heartbeat arm.
- One haiku call per verify instead of three; at most 2 concurrent verifies per repo; ready tasks
  start in critical-path order; forward-merge, no-conflict landing and verifier-settled audit rows
  run on haiku; audit and planner read per-task files instead of inlined requirements.
- The prompt-cache change ships only if a probe shows a cache-creation saving; otherwise the probe
  numbers and a no-op decision are recorded.
- `ticket.py estimate <epic>` writes task minutes from the formula (parameters in one JSON, refit
  shipped), the README Time section and the gate show sum, critical path, expected wall and actual,
  and `apply-run` stamps `actual` and per-role minutes from the run dir.

## Non-goals

- Dropping or weakening independent verification, the review loop, the scope audit or the approval
  ledger.
- The in-run landing itself, `landed` in the return, fork-point diffs and forward-merge via the epic
  branch: epic integration worktrees delivers those.
- `~/Documents/claude-infra-plugin` (template only).
- Changing the Workflow runtime (no clock in scripts, no per-agent cwd option, notification
  delivery): only what the plugin controls.

## Anti-goals

- A regression slips to main because a targeted verify missed it: the epic close full suite
  (blocker D5) and the phase 5 full-suite run stay.
- A lenient AC match accepts a wrong test silently: exact match first, substring only within the
  named file, `matchedBy` shown to the auditor.
- A stalled run goes unnoticed: STALL detection keeps polling every 600 s.
- Non-epic plan-execute runs change behaviour beyond the named gates.
- Estimates become a budget: Time stays report-only.

## Constraints

- Test first per task (rules/tdd.md); `mise run test` and `mise run lint` green before the epic
  lands.
- The Workflow runtime forbids `Date.now()` and `new Date()` in scripts (workflows/tests/harness.mjs
  `CLOCK_ERROR`, pinned by plan-execute-duration.test.mjs): plan-execute cannot measure time.
- plan-execute reads no file and no task estimate (plan-execute-duration.test.mjs); everything it
  needs comes in through args.
- Task frontmatter stays in the restricted format (scalars, quoted strings, inline lists).
- New node test titles are single kebab tokens (refRunners `--test-name-pattern {name}`).
- Verify commands are targeted: the workflows component suite (about 3 s), or named pytest files plus
  `ruff check`; the start-development component suite takes 2 min and is never a task verify.
- The plugin loads from a versioned cache: changes are live only after the epic reaches main and the
  plugin is updated, so this epic itself runs on the pre-change flow.


## Measured baseline and ranked optimizations

Copied from the research brief docs/research/flow-token-optimization.md (gitignored), sections (a) to (c), so the tracked design carries Goals 1 and 2.

Epic: flow-speed-and-token-optimiz. Data: session 24dd7e5c (2026-10-20 10:27Z to 10-21 13:46Z, 27.3 h): 15 plan-execute workflows (592 agents), 44 direct subagents, the orchestrator transcript, 13 run returns, the record of project-agnostic-multi-harne (epic A, 86 tasks) and the live epic-integration-worktrees (epic B, 21 tasks). Scripts in `docs/research/flow-token-optimization/`: parse_agents.py, parse_returns.py, parse_main.py, parse_failures.py + analyze.py (failures.md), fit.py/fit2.py/extra.py (estimator, shares), flow-map.md (code reading with file:line cites). CSVs: scratchpad `flow-research/`.

cw = cost-weighted tokens at standard price ratios to base input: cache read 0.1, cache write 1.25, output 5.

### (a) Measured baseline

| Scope | Agents | Raw tokens | input / output / cache read / cache write | cw | cw share |
|---|---|---|---|---|---|
| Workflow agents | 592 | 107.5M | 7k / 0.79M / 93.7M (87%) / 13.7M (13%, all 1h TTL) | 30.4M | 47% |
| Orchestrator (624 turns) | 1 | 170.2M | 1.6k / 0.28M / 169.1M (99.4%) / 0.77M | 19.3M | 30% |
| Direct subagents (planners, cartographers, research, panel, mergers) | 44 | 96.1M | 3k / 35k / 91.9M / 4.2M | 14.6M | 23% |

Workflow agents by role (agent-min = summed per-agent wall; total 1942):

| Role | n | Model | Raw | cw share | Agent-min (share) | Wall med / p90 s |
|---|---|---|---|---|---|---|
| impl | 118 | sonnet 96, haiku 17, opus 5 | 49.2M | 32.9% | 441 (23%) | 89 / 601 |
| review | 157 | sonnet 146, haiku 11 | 22.0M | 24.7% | 153 (8%) | 37 / 140 |
| verify | 206 | haiku | 11.8M | 23.7% | 1072 (55%) | 66 / 1037 |
| fix | 104 | sonnet 101, opus 3 | 16.4M | 14.4% | 266 (14%) | 51 / 426 |
| audit, triage | 1, 6 | sonnet, haiku | 7.5M, 0.6M | 3.1%, 1.2% | 7 | - |

Rounds beyond the first (review #2+#3: 43 agents, 49 min; fix #2: 21, 78 min; verify #2+#3: 104, 605 min) are 38% of agent-minutes and 33% of workflow tokens; 84% of tasks had more than one verify, 39% more than one review.

Per task (94 tasks, all rounds and relaunches): agent-minutes median 8.9, mean 20.6, p90 58.7 (full distribution in (d)). A full-suite `verify` is the strongest predictor (r = 0.74): 40.9 min median vs 5.0 targeted; verify alone 26.3 vs 1.4, impl+review+fix 16.7 vs 3.2 because implementers and fixers run the suite too. Per model (cw): sonnet 66%, haiku 29%, opus 5%.

Cache: per-agent cache write median 17k (verify) to 28k (impl), the whole system prompt plus first message on every agent; cross-agent sharing is near zero even for the static-first reviewPrompt (24k). Writes are 57% of workflow cw, reads 31%, output 13%.

Cascades: 19 root escalations (gate-repeat 9, round-cap 6, verify-agent-died 2, review-shallow 1, no-progress 1) caused 183 dependency-failed task-runs and 11 relaunch runs. Runs 2 and 3 each ran one task at the DAG top and blocked 61 and 60 tasks: 154 min wall and 2.5M tokens. Epic A wall, run 1 start to run 13 end: 913 min, of which 210 min (23%) were orchestrator decision gaps.

Orchestrator: 156 heartbeat turns (median interval 9.9 min) = 24.4% of its tokens; 271 notification turns = 46.2%; record 13%; relaunch prep 10.6%; user dialogue 3% (10 human messages). Context peaked at 543k; 42% of the span had no workflow running.

Failure-mode cost (strict / upper attribution; failures.md):

| Mode | Occurrences | Tokens | Agent-min |
|---|---|---|---|
| 3 Verifier 600 s Bash cap, deaths, `--prev-head` argparse | 46 capped, 4 deaths, 5 argparse | 5.25M | 743 |
| 8 Full-suite verify (median call 600 s capped vs 27 s targeted) | 57 of 206 verifiers | 4.8M | 636 |
| 4 AC ref names a missing or renamed test | 68 verifies, 58 of 104 fix rounds | 3.7M / 15.7M | 117 / 385 |
| 2 Escalation cascade, relaunch | 183 dependency-failed, 11 relaunches | 4.0M | 108 (+154 wall) |
| 1 Forward-merged text trips parking/debt gates | 16 fix rounds, 13 gate-repeat stops | 2.0M / 4.0M | 52 / 109 |
| 6 Dependency-merge conflicts in implementers | 5 impl at 2.5x a clean one | 3.2M excess | 7 |
| 5 Process-only TDD findings re-raised | 13 fix rounds | 0.9M / 3.2M | 12 / 93 |

Modes 3 and 8 overlap on 46 agents. Merging is scripted inside workflows; its cost is the 15 direct mergers (7.3M raw, p90 55 min) and orchestrator merge turns.

### (b) Where the spend goes

1. Verification wall-clock: 55% of agent-minutes; full-suite tasks are 32% of tasks but 71% of agent-minutes (1377 of 1942), each verify pinned at the 600 s Bash cap, and `--tdd-revert` runs the suite three times.
2. Rounds beyond the first: 38% of agent-minutes, 33% of workflow tokens; 56% of fix rounds carry a `ref-missing` AC finding, a plan-data defect (the AC names a test that was written under another name), not a code defect; forward-merged gate text and TDD process findings add 29 fix rounds.
3. Orchestrator wake-ups: heartbeat plus notification turns are 70% of orchestrator tokens (120M raw, about 13M cw, 20% of all spend) for a progress line each; relaunch and record turns add 24%.
4. Cache writes: 57% of workflow cw; every agent rebuilds its prefix (per-worktree cwd in the system prompt, task-first ordering in implPrompt and verifyPrompt).
5. Planning and research direct agents: 23% of all cw; two planners 31.7M raw; one epic audit 7.5M raw.
6. Cascade and relaunch time: epic A took 913 min wall; the critical path at parallelism 3 predicts about 450.

### (c) Ranked optimizations

Savings are against the workflow baseline (30.4M cw, 1942 agent-min, 913 min epic wall). Every item keeps the review loop, independent verification, scope audit and approval ledger; only what each runs, and when, changes.

Quick wins:

1. Verify scoping, single landing suite. plan-execute.js `verifyCommand` :1013 and `targetedVerify` :347: require a targeted `t.verify` (AC test refs plus changed test files), never fall back to the implementer's free-text command; the full suite runs once per landing under the existing merge-gate suite-lock. verify-task.py `tdd_revert` :595: run only AC-referenced tests on base and reuse the :664 result instead of a third run; subprocess timeouts at :47/:65; explicit Bash timeout in verifyPrompt :1023; validate `--prev-head` as a sha. Saving: -35% to -45% agent-minutes (modes 3 and 8; impl/fix self-checks shrink too), -10% workflow tokens, no verifier deaths or argparse rounds. Risk: a regression outside the targeted set is caught at landing, not in the loop; the landing suite and scope audit already cover it.
2. AC evidence robustness. implPrompt :860 and fixPrompt :964 omit `t.ac` though implementer.md:88 demands exact test refs. Pass the AC list, have the implementer return an `acEvidence` map (AC id to final test name), and let `_test_name_missing` (VT:389) fall back to file-plus-substring, recording `matchedBy`. Saving: 58 of 104 fix rounds carry this; strict -3.7M tokens/-117 min, upper -15.7M/-385 min; expect -10% to -20% tokens, -15% agent-minutes. Risk: a lenient match accepts a wrong test; exact first, substring second, auditor sees matchedBy.
3. Orchestrator quiet mode and one-shot relaunch. heartbeat.py:53-57 beat 600 s to 1800 s on the 1h cache, `--no-eta` default, no wake on an unchanged digest; one END notification per workflow instead of per-agent hand-backs; `ticket.py continue --launch` (continue_cmd.py:134-161) does continue, MERGE dispatch, Workflow launch and heartbeat arm in one call. Saving: -60% orchestrator tokens (about 12M cw, 18% of all spend), most of the 210 min decision gaps (-20% epic wall). Risk: slower stall detection; keep STALL at 3 quiet beats.
4. Prompt-cache prefix. Order implPrompt and verifyPrompt static-first like reviewPrompt :907 and launch agents from the main checkout cwd with the worktree path in the prompt, so system prompts are byte-identical per agent type. Saving: if 60% of each 17-28k prefix becomes a read, -25% to -30% workflow cw. Risk: none to quality; the per-worktree-cwd hypothesis is inferred from the write sizes and needs a hook-probe measurement first.
5. Gate provenance. verify-task.py parking :309 and debt :265 diff against merge-base, so forward-merged dependency lines count as introduced; exclude lines present in a merged dependency branch. Saving: 9 of 19 root escalations, 2.0M to 4.0M tokens plus their cascades. Risk: low; the dependency's own gate judged those lines.
6. Model per role. Forward-merge :2272, the no-conflict merger path and verifier-settled audit rows to haiku; review stays sonnet. Saving: 2% to 3%.

Structural:

7. Cascade containment and mid-run landing. `released` :1978 fails every transitive dependent on any unresolved finding, and nothing lands until continue. Release when the dependency is verified with only process or medium findings or all ACs met; land released tasks into the epic branch mid-run; auto-accept `triageRejected` and `processOnly` in continue. Saving: 183 dependency-failed task-runs and 11 relaunches; epic wall from 913 toward 450 min (-40%). Risk: a dependent builds on code later fixed; forwardMerge :2254 plus re-verify already handles that.
8. Review tiering. Pass `--requirement` (VT:636, never passed) so tier hints work; widen `skip` :148-150 to doc-only and test-only diffs with all ACs met; scoped re-review of light-tier fixes to reviewer findings (:1435, never re-reviewed today). Saving: about a third of first reviews, -7% tokens. Risk: moderate; RISK_PATH stays full, the scope audit backstops.
9. Planner granularity. phases-1-3.md:83 sizes "about an hour"; fixed cost per task is about 150k cw and 1-3 file tasks take 3-7 min. Size by test files and verify runtime; merge sibling tasks under 3 files sharing a test file. Saving: about 20 fewer verify-review cycles, -10% to -15% tokens. Risk: larger diffs, bounded by the 150-line rule.
10. Audit and planner context by file. Audit prompt :2111 inlines every requirement (7.5M raw); write per-task sections to a file; planners get a section index. Saving: -3% workflow, -30% direct.
11. Fan-out cap and triage. Cap concurrent verifies per repo at 2 and start ready tasks in critical-path order (runTasks :1971; 3-4 concurrent suites are what pin verifies at 600 s; redundant after item 1). Fold the three haiku calls in VT:677-707 into one: about 1 min per verify.

## Decisions

### D1: Targeted verify only, bounded verify-task runs

plan-execute's `verifyCommand` never falls back to the implementer's free-text command: with no
`t.verify` it passes `--targeted`, and verify-task builds the command from the runners of the AC
`test:` refs and the changed test files. verify-task bounds every subprocess (`--timeout`, default
480 s per command, so two runs plus triage finish inside the verifier's 600 s Bash call) and reports
`timeout: {command, seconds}` with `passed: false`; it rejects a `--prev-head` that is not a 7-40
hex sha with a JSON result naming the error; `--tdd-revert` runs only the AC-referenced tests on the
reverted base (the command when there are none) and reuses the main run's exit for `passedOnHead`, so
the command runs at most twice. plan-execute passes `--prev-head` only when the previous head is a
sha, quoted, and the verifier prompt sets the Bash timeout to 600000 ms. The landing verify stays the
blocker's (`merge.py --no-suites --verify <task verify>`) and the full suite runs once at epic close.
Alternatives: a run-end full suite per plan-execute run (rejected: the close and phase 5 already run
it, and a per-run suite adds 10 minutes of serial wall); a lint warning only (rejected: the brief
measured 71% of agent-minutes on full-suite tasks). (my call) Serves U1.

### D2: AC evidence map from implementer to verifier

implPrompt and fixPrompt carry the task's AC list (id, text, evidence ref). The implementer and
fixer return `acEvidence`, a map from AC id to the final `file::name` of the test that proves it.
plan-execute writes the map next to the ACs and passes `--ac-evidence`; verify-task resolves a
`test:` AC through the map first, then the exact ref, then a test in the named file whose name
contains the ref's name (or the reverse), and records `matchedBy: acEvidence|exact|substring`. A
substring match is never `verifier settled` for the audit. Alternative: tell the planner to name
tests better (rejected: the implementer decides names). Serves U1.

### D3: Orchestrator quiet mode and one-shot relaunch

The heartbeat polls the journal every 600 s, prints END and STALL at once, and prints a progress
line only when the digest changed and at least 1800 s passed since its last line; the haiku ETA is
opt-in (`--eta`; `--no-eta` stays accepted). `ticket.py continue --launch` runs the existing
continue steps, lands each pending done task itself by running merge.py from the main checkout,
prints `MERGE` lines only for landings that failed (exit 2, worktree-merger as today), writes the
args and named copy, and prints one `LAUNCH <script> <args>` line and one `ARM <heartbeat command>`
line. run-handback.md is written for the END line only. The 30-minute silence is a gate question
(Q1) because it relaxes the 10-minute bounded-wait rule for this one watcher; the plan follows the
recommended answer. Serves U1.

### D4: Estimator from files and verify kind, epic wall from critical path and parallelism

`plugins/workbench/scripts/lib/estimator.json` holds every parameter: task intercept 4.0, exponent
0.22, full-suite factor 6.9, P = 1.5 at 15 open tasks or fewer and 3 at 30 or more (linear between,
my call), k = 2.0, and the full-suite command patterns. `scripts/lib/estimator.py` computes task
minutes, the epic line (`sum`, `cp` = longest `depends_on` path by minutes, `run_wall = max(cp,
sum / P)`, `epic_wall = k * run_wall`) and `refit` (log-space least squares over done tasks with
`actual`, or over the shipped 94-task fixture). `ticket.py estimate <epic>` writes each task's
`estimate` with `estimate_by: formula` unless it is `override` (set by `new-task --estimate`), and
regenerates the README Time line: `Estimate: <sum> agent-min | Critical path: <cp> min | Expected
wall at P=<p>: <h> h (k=<k>) | Actual: <a> min | Remaining estimate: <r> min`; it prints the line
plus the three longest-path tasks for the gate. `new-task` without `--estimate` computes the
formula value. Serves U2, Dc.

### D5: Actuals are stamped from the run dir after the run returns

plan-execute cannot read a clock (Constraints), so "plan-execute emits durationMs" is delivered the
way the runtime prescribes ("stamp results after the workflow returns"): `apply-run --run-dir` (and
`continue --run`, which already passes the run dir) derives per task `durationMs` (first to last
transcript timestamp of the task's agents) and `roleMs` (summed agent spans per role) from the
journal labels `<name>:<role>:<task>[#n|+n]`, fixing the `#n` miss. `actual` becomes minutes of
summed agent spans (the estimator's unit) and `actual_roles` a quoted scalar such as
`"impl 3, verify 5, review 1, fix 2"`. The record's estimate-versus-actual table gains the role
split. (my call; serves Dc) Serves U2, Dc.

### D6: Prompt-cache prefix change gated by a probe

hook-probe.js gains a cache mode: three sequential `workbench:implementer` agents with a
static-first prompt and three with today's task-first order, each doing one trivial read.
`hook-evidence.py --cache <run dir>` prints each agent's first-turn `cache_creation_input_tokens`,
`cache_read_input_tokens` and `cwd`, and a verdict: `CACHE saving` when the second and third
static-first agents create under 5k each, else `CACHE none`. The orchestrator runs the probe once
cache-probe lands (Workflow on the integration tree's hook-probe.js), then records the result in this
design under `## Cache probe result`. cache-prefix-change reads that section: on `saving` it orders
implPrompt and verifyPrompt static-first with the task lines last; on `none` it changes no prompt
and records the numbers and the no-op decision in `MEMORY.md`; with no result it returns `blocked`
(whoCanClear: the orchestrator). Workflow agents already start in the main conversation's cwd (blocker
facts), which the probe's `cwd` column confirms. Serves Db.

### D7: Gate provenance through excluded dependency refs

verify-task takes `--exclude-ref <ref>` (repeatable): an added line whose text is also added by that
ref relative to the merge base is dropped before the debt and parking scans. plan-execute passes the
same-repo dependency branches it merged in non-epic runs; epic runs pass none, because their diff
base is the epic branch or the fork point (blocker D4, D14). Serves U1.

### D8: Cascade containment beyond in-run landing

`released(d)` also releases dependents when `d` is verified, not blocked, and every open finding is
`medium` and not a gate finding (`mediumOnly`); the task still escalates for a ruling and the return
marks `mediumOnly: true`. A released medium-only task releases its dependents but does not land until the orchestrator rules; an accept ruling lands it like any released task (amended 2026-10-22, epic review: the builder check answer wins; delivered by medium-only-hold).
`ticket.py continue` auto-accepts every verified task the return marks `processOnly` (reason not
`review-shallow`) or `triageRejected`, recording a ruling with the reason. A relaunch's args never
contain a done task: only escalated, blocked, dependency-failed and unstarted tasks. Serves Da.

### D9: Review tiering

verifyPrompt passes `--requirement` so the tier hint sees the task; `skip` also applies to diffs
whose changed files are all docs (`*.md`) or all test files, with every AC met and no RISK_PATH
match; a light-tier fixer that changed files to fix reviewer findings gets one scoped re-review
(effort medium) of only those files; RISK_PATH stays `full`. Serves U1.

### D10: Sizing by test files and verify runtime

phases-1-3.md and the planner agent size a task by its test files and verify runtime instead of
"about an hour": one test file's worth of behaviour, a targeted verify, sibling tasks under 3 files
that share a test file merged, `ticket.py estimate` for minutes (`--estimate` only as an override).
validate-tasks.mjs fails a full-suite verify on a task with status `todo` (warns on started tasks)
with a split hint, and drops the over-90 estimate warning. This plan follows the rule (Dd). Serves
Dd, U2.

### D11: Audit and planner context by file

On the ticket flow `ticket.py args` adds each task's `taskFile` path; the audit prompts list task
ids, titles, trees and task file paths instead of inlining every requirement (under 10k characters
for a 21-task epic), and the scope auditor reads each task file's Requirement section. The planner
agent reads a brief by its heading index (grep the headings, read the sections it needs). Serves U1.

### D12: Fan-out cap, start order, haiku for mechanical roles, one triage call

At most 2 verifier agents run at once per repo (a per-repo queue around independentVerify); ready
tasks start in descending order of transitive dependents (the critical-path proxy, since
plan-execute reads no estimate). Forward-merge runs on haiku; the land agent runs on haiku and a land
that reports a conflict is re-dispatched once on sonnet before `land-failed`; audit rows the verifier
settled (every AC met by test, symbol, command or doc-section evidence, `matchedBy` not `substring`)
go to one haiku scope-auditor call and the rest to the sonnet one, merged before splitAudit. Review
stays sonnet. triage.py gets one `verify` mode answering parking, AC plausibility and tier in one
haiku call. Serves U1.

### D13: One full-suite predicate

`estimator.json` lists the full-suite command patterns (`mise run test`, `make test`, `npm test`,
`pnpm test`, `yarn test`, `go test ./...`, `cargo test` with no filter, bare `pytest` or `uv run
pytest` with no path, `run-tests.sh` without `--only`) and a command equal to one of the repo's
workbench.json `suites` entries is full too. estimator.py (Python) and validate-tasks.mjs (node)
both read that list; there is no second copy. (my call) Serves U2, U1.

### D14: Quiet heartbeat, 30-minute progress
Yes: the plan-execute heartbeat stays silent while nothing changes and prints progress at most every 30 minutes; END and STALL print at once (STALL after 30 minutes without journal change); AGENTS.md ground rule 4 names that watcher as the exception to the 10-minute bound. (user decision)

## Research

| Lens | Ran or skipped | Adopted ideas | Rejected ideas |
|---|---|---|---|
| research-code-internal | ran: docs/research/flow-token-optimization.md and flow-token-optimization/flow-map.md (fable, file:line cites, numbers copied above) | the 11 Plan inputs (brief "Plan inputs"); estimator fit (brief "(d) Estimates", fit2.py) | per-landing full suite (D1); a run-end suite (D1) |
| research-code-external | skipped: in-house workflow tuning; no external analogue decides between approaches | none | none |
| research-papers | skipped: the estimator is a two-feature log-linear fit on measured data, no algorithmic core | none | none |
| research-docs | skipped: no external API used in a new way; the prompt-caching behaviour is measured by the probe (D6) instead of read | none | none |

## Research inputs

| Source | Entry | Lands in |
|---|---|---|
| brief Plan inputs 1 | validate-tasks rejects a full-suite verify with a split hint | planner-sizing-rule |
| brief Plan inputs 1 | `--tdd-revert` at most twice, AC-referenced tests on base; subprocess timeouts give `timeout`; non-sha `--prev-head` rejected | verify-task-bounded-runs |
| brief Plan inputs 1 | verifyCommand never uses the implementer's command; explicit Bash timeout; sha-only prev-head in the prompt | verify-scope-wiring |
| brief Plan inputs 1 | the landing suite still runs once under the merge gate | verify-scope-wiring (pins the land command; the full suite runs at close, blocker D5) |
| brief Plan inputs 2 | AC list in impl and fix prompts, `acEvidence`, resolution order, `matchedBy`, harness-config-migrate#1 fixture | ac-evidence-map |
| brief Plan inputs 3 | heartbeat default beat 1800 s, no ETA call, no turn on an unchanged digest | heartbeat-quiet |
| brief Plan inputs 3 | `continue --launch`, auto-accept triageRejected and processOnly | continue-launch |
| brief Plan inputs 3 | run-handback covers END only | flow-docs-update |
| brief Plan inputs 4 | `ticket.py estimate`, Time line, refit, 94-task fixture MdAPE under 0.5 | estimator-model, estimate-and-actuals |
| brief Plan inputs 4 | returns carry `durationMs` and `roleMs`; `--run-dir` matches `#n` labels | estimate-and-actuals (stamped from the run dir, D5) |
| brief Plan inputs 4 | task-fields.md, README Time template, planner.md, phases-1-3.md | flow-docs-update, planner-sizing-rule |
| brief Plan inputs 5 | 3-implementer probe, cache_creation under 5k on the second and third | cache-probe |
| brief Plan inputs 5 | task-specific lines last; agents launch from the main checkout | cache-prefix-change (gated, D6) |
| brief Plan inputs 6 | dependency-branch lines excluded from parking and debt gates; init-engine-new fixture | gate-provenance |
| brief Plan inputs 7 | release on process-only or medium-only findings | cascade-release |
| brief Plan inputs 7 | auto-accept triageRejected and processOnly; relaunch re-runs only escalated tasks and their unlanded dependents | continue-launch |
| brief Plan inputs 7 | land released tasks mid-run under the suite-lock; return reports `landed` | rejected: delivered by epic integration worktrees (land-in-run, land-outcomes) |
| brief Plan inputs 8 | `--requirement` passed; doc-only and test-only skip; scoped re-review of light fixes; RISK_PATH full | review-tiering |
| brief Plan inputs 9 | sizing by test files and verify runtime; merge siblings; lint warns on full-suite verify instead of estimate over 90 | planner-sizing-rule (fails on todo tasks, D10) |
| brief Plan inputs 10 | audit prompt under 10k chars for a 21-task epic; auditor and planner read per-section files | audit-context-and-models, planner-sizing-rule |
| brief Plan inputs 11 | at most 2 concurrent verifies per repo; critical-path start order | verify-scope-wiring |
| brief Plan inputs 11 | forward-merge and verifier-settled audit rows on haiku; no-conflict merger on haiku | audit-context-and-models |
| brief (c) item 11 | fold the three haiku calls in verify-task into one | triage-one-call |
| brief (c) item 3 | one END notification per workflow instead of per-agent hand-backs | rejected: notification delivery belongs to the Workflow runtime, not the plugin (Non-goals) |
| brief (d) | the planner is 6.9x high; formula and epic estimator | estimator-model, estimate-and-actuals; this plan's estimates |

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 targeted verify, bounded verify-task runs | verify-task-bounded-runs, verify-scope-wiring, planner-sizing-rule |
| D2 AC evidence map | ac-evidence-map |
| D3 quiet heartbeat and one-shot relaunch | heartbeat-quiet, continue-launch, flow-docs-update |
| D4 estimator and epic line | estimator-model, estimate-and-actuals, flow-docs-update |
| D5 actuals from the run dir | estimate-and-actuals, flow-docs-update |
| D6 cache prefix gated by a probe | cache-probe, cache-prefix-change |
| D7 gate provenance | gate-provenance |
| D8 cascade containment remainder | cascade-release, continue-launch, flow-docs-update |
| D9 review tiering | review-tiering, flow-docs-update |
| D10 sizing by test files and verify runtime | planner-sizing-rule |
| D11 audit and planner context by file | audit-context-and-models, planner-sizing-rule |
| D12 fan-out cap, start order, haiku roles, one triage call | verify-scope-wiring, audit-context-and-models, triage-one-call |
| D13 one full-suite predicate | estimator-model, planner-sizing-rule |
| D14 Quiet heartbeat, 30-minute progress | heartbeat-quiet, flow-docs-update |

## Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| estimator-params | estimator-model | estimate-and-actuals, planner-sizing-rule | `plugins/workbench/scripts/lib/estimator.json` |
| verify-task-cli | verify-task-bounded-runs | verify-scope-wiring | `plugins/workbench/scripts/verify-task.py` |
| ac-evidence | ac-evidence-map | audit-context-and-models | `plugins/workbench/workflows/plan-execute.js` |
| cache-probe-verdict | cache-probe | cache-prefix-change | `plugins/workbench/scripts/hook-evidence.py` |
| epic-time-line | estimate-and-actuals | flow-docs-update | `plugins/workbench/skills/start-development/scripts/ticket_cmds/estimate.py` |
| continue-launch-lines | continue-launch | flow-docs-update | `plugins/workbench/skills/start-development/scripts/ticket_cmds/continue_cmd.py` |

Cross-epic contracts (registered in `docs/plans/contracts.json`, owner epic integration worktrees,
consumer this epic): `land-step` (plan-execute.js; used by verify-scope-wiring, cascade-release,
audit-context-and-models), `fork-point` (plan-execute.js; used by gate-provenance), `epic-run-args`
(ticket_cmds/args.py; used by audit-context-and-models) and `merge-target-worktree` (merge.py; used by
continue-launch).

## Review focus

- verify-task.py: no path runs the command a third time, every subprocess has a timeout, and a
  timeout or bad `--prev-head` still prints one JSON object.
- The AC resolution order: exact before substring, substring only inside the named file, and
  `matchedBy: substring` never counted as verifier settled.
- runTasks: the per-repo verify queue cannot deadlock (a queued verify always starts when one
  finishes), medium-only release never releases a blocked or unverified task, and non-epic runs
  keep today's release rule apart from medium-only.
- continue `--launch`: merge.py runs only for done tasks off the epic branch, never with `--force`,
  and a failed landing leaves both trees and prints the MERGE line.
- The audit split: every AC row reaches exactly one of the two auditor calls.
- The estimator refit: pure-Python least squares reproduces the fit within the stated tolerance.

## Left to the builder

- Helper names and module layout inside verify-task.py, triage.py, plan-execute.js, estimator.py and
  the ticket_cmds modules, within the contracts above.
- The exact full-suite regexes, as long as every pattern in D13 matches and every targeted example
  in estimator-model's AC does not.
- The probe's trivial agent task and prompt text, within D6.
- The wording of the docs, within the needles the doc tests pin.

## Assumptions and unknowns

- Blocker: epic integration worktrees lands first; this plan assumes its code. Files it changes that
  this epic also changes: `plugins/workbench/workflows/plan-execute.js` (land-in-run, land-outcomes,
  fork-point-diffs, forward-merge-via-epic, plan-execute-epic-names),
  `skills/start-development/scripts/ticket.py` (epic-base-wiring, epic-close-sweep,
  fork-point-record, integration-tree-create, name-lookup-parsers, slug-collision-guard,
  single-hyphen-names), `ticket_cmds/continue_cmd.py` (epic-base-wiring, epic-close-command),
  `ticket_cmds/args.py` and `tests/test_ticket_args.py` (epic-base-wiring), `tests/test_ticket_run.py`
  (docs-worktree-refs, epic-base-wiring), `tests/test_ticket_continue.py`, `references/run-handback.md`,
  `references/phase-4-execute.md` and `SKILL.md` (docs-flow-phases), `references/tickets.md`
  (docs-worktree-refs), `tests/test_review_flow_docs.py` and root `AGENTS.md`
  (docs-readmes-fallback), `agents/implementer.md` (docs-worktree-refs), and
  `skills/worktree-merge/scripts/merge.py` (merge-target-worktree, merge-contained-check,
  epic-close-sweep). Confirmed by `ticket.py facts` File owners; each task re-reads the landed code.
- The land step dispatches one `workbench:worktree-merger` agent per landing with
  `merge.py --name <tree> --base <epic> --keep --no-suites --verify <task verify>` (blocker D4);
  audit-context-and-models changes only its model. Confirmed by reading land-in-run's code once
  landed.
- The 94-task fixture source is
  `/private/tmp/claude-501/-Users-szymonri-Documents-workbench/24dd7e5c-62ee-4970-92ad-0076f6552463/scratchpad/flow-research/F/task_actuals.json`
  (fields `task, files, full, agent_min`); estimator-model copies those four fields into the repo.
  If the file is gone, the task returns `blocked` naming the orchestrator, who regenerates it with
  the brief's parse scripts.
- Workflow agents start in the main conversation's cwd (blocker design facts); the probe records
  `cwd` per agent to confirm it.
- Whether static-first prompts produce cross-agent cache reads is unknown; D6's probe settles it
  before any prompt changes.


## Cache probe result

Run 2026-10-22, workflow run wf_c93a609a-e42 (hook-probe.js args.probe=cache, run dir ~/.claude/projects/-Users-szymonri-Documents-workbench/<session>/subagents/workflows/wf_c93a609a-e42), read with `hook-evidence.py --cache`:

| Agent | cache_creation_input_tokens | cache_read_input_tokens |
|---|---|---|
| static#1 | 21830 | 0 |
| static#2 | 14855 | 6975 |
| static#3 | 14855 | 6975 |
| task#1 | 14855 | 6975 |
| task#2 | 14855 | 6975 |
| task#3 | 14855 | 6975 |

Verdict: `CACHE none static=14855,14855 task=14855,14855`. Static-first ordering reads no more cache than task-first: every agent after the first reads the same 6975-token shared prefix and creates the same 14855 tokens, whatever the prompt order. All six ran in cwd /Users/szymonri/Documents/workbench. cache-prefix-change therefore changes no prompt and records the no-op (D6).

## Open questions

none: Q1 (D3, quiet heartbeat with 30-minute progress) answered yes at the gate on 2026-10-22, recorded as D14.

## Irreversible operations in scope

none: continue `--launch` runs merge.py with `--keep` on local, unpushed task and epic branches
only (the blocker's land path); nothing is deleted, force-pushed or released.

## Builder check answers

- verify-task.py `--timeout` is one shared deadline (default 540 s) across every command a single call runs (the main run, the TDD-revert base run and triage), so the verifier's 600 s Bash call never dies; a command that hits the deadline yields `timeout` and the remaining steps are skipped and reported. (my call)
- Q1 (quiet heartbeat) is a gate question; heartbeat-quiet builds the answer recorded at the gate.
- The cache probe: after cache-probe lands, the orchestrator runs the probe workflow itself and writes `## Cache probe result` (numbers plus the run dir) into this design.md. cache-prefix-change is excluded from the run that delivers cache-probe and runs in the next one, so it never starts blocked. (my call)
- A task released as mediumOnly releases its dependents (they merge its task branch as today) but does not land on the epic branch until the orchestrator rules; a "fix" ruling remediates it and forward-merges plus re-verifies the dependents before anything lands. (my call)
- The land result gets an additive `conflict` status (with the conflicting files) if the integration epic's land-step does not already expose one; this extends the land-step contract additively and is recorded in the contracts table. (my call)
- `acsForAudit` (per-task return field) and `acTable()` (plan-execute.js epic-close audit) exist today; audit-context-and-models reaches ac-evidence-map transitively through cascade-release, review-tiering and gate-provenance. (answered)
- The 94-task fixture source now lives at docs/research/flow-token-optimization/data/F/task_actuals.json (local, gitignored); estimator-model commits the derived fixture under plugins/workbench/scripts/tests/fixtures/. (answered)
