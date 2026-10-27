# deploy-safe agent sessions design

## Summary

Agent sessions must survive deploys and pod restarts. The orchestrator ingester re-attaches after a wrapper resume and
leaves `dead`; a dead agent never leads; agent StatefulSets use `updateStrategy: OnDelete` and a reconciler replacer
rolls one idle pod at a time, leader last after a handover; the wrapper continues a turn interrupted by its own
shutdown; the onStart plugin install is non-fatal; Claude transcripts (`/sessions`) are backed up to S3 at discard and
restored on recreate through the existing cache Jobs; agents-web says what a discard loses and shows an
agent-unavailable banner; no red main build is published or deployed; a kind e2e rolls the agent image mid-turn; then
release, pin, apply and smoke with a live check.

## Intent and why

On 2026-10-27 the agents-helmfile #35 apply rolled every agent pod at once (default RollingUpdate), including the pod
whose leader was running the apply. Every wrapper resume answered 200, but the ingester had ended each stream on the
wrapper's `session_closed`, never re-attached (same wrapper session id, unchanged `AgentRef`) and re-marked the agent
`dead` from the stored close (`ingester/loop.py:106-140,191-195,296-306`). The dispatcher delivers only to idle agents
(`db/queue.py:273`), so messages sat queued for 20+ minutes. The user saw hung sessions, discarded both, and lost both
conversations because discard deletes the PVC and the S3 cache never saved `/sessions`. Main CI run 40565058706
(96e46f3) had failed e2e yet its image and chart were published and deployed. User request (verbatim): "Figuring out
what happened that the session hanged 2. Convert the evidence into actionable epic and fix it autonomously".

## Goals

G1-G10 of the README, verbatim there; each is covered by acceptance conditions (Decision coverage below).

## Non-goals

- Running helmfile apply as an in-cluster Job runner (G3 keeps the deployer's busy pod from being rolled instead).
- Sending Claude's documented exit keystrokes on SIGTERM (inferred need only; noted, not doing now).
- Changing hive leadership handover semantics beyond excluding dead agents.
- Periodic (non-discard) transcript backups.

## Anti-goals

- A busy agent pod or a leader mid-turn is ever deleted by the replacer, with or without a deadline.
- The replacer or the sessions restore overwrites a live session's `/sessions` (a restore only ever runs before the
  session's first agent pod exists).
- A second S3 client, a second busy predicate, a second continue-prompt mechanism or a second GitHub status poller.
- A pin check with an override flag, or a publish path that skips lint, test or e2e.
- A test edited, skipped or xfailed to pass, except the ones named in the tasks as no longer accurate.

## Constraints

- Component hard rules: Python services (web is TypeScript), services talk only through HTTP or the queue, one writer
  per table, queue rows change only through status-guarded updates.
- Orchestrator conventions: level-triggered crash-safe reconcile (status written before the create), database clock for
  times, every module docstring cites its decisions, MEMORY.md takes a dated entry with the why.
- No Docker in agent pods: orchestrator DB and e2e tests run only in GitHub CI (retro, recurring).
- Wrapper tests use the fake claude only; `uv run` only; ASCII only, no em dashes.
- No backward compatibility shims; deploys and the planned release tag are pre-approved (D13).

## Decisions

### D1: Agent StatefulSets roll by OnDelete plus an idle-only replacer, leader last

User decision, verbatim: "Rollouts: agent StatefulSet updateStrategy OnDelete; the reconciler replaces outdated pods
(pod controller-revision-hash != status.updateRevision) one pod at a time per session, only when that agent is idle
(reuse the _draining busy predicate; no dispatching/verifying message), the leader last and only after leadership moved
to an idle eligible member (existing handover), a single-agent session rolls when idle. Never force-replace a busy pod
(no deadline); the session status exposes the pending roll. Partition/PDB/maxUnavailable rejected (research.md). Any pod
that dies anyway comes back on the new template (accepted)."

- Alternatives: RollingUpdate `partition` (ordinal-only, cannot skip a busy middle ordinal), PDBs (do not limit
  StatefulSet rolling updates or direct deletes), `maxUnavailable` (feature gate off on 1.35.4-1.36), preStop waiting
  (hard-capped by the grace period) - all rejected in research.md section 1.
- (my call) The busy SQL of `_draining` is extracted once and shared by the drain and the replacer (reuse.md
  do-not-build: "a second drain/busy query"); the replacer's idle test is "not busy, no `dispatching`/`verifying`
  message, not the leader".
- (my call) "Existing handover": the reconciler queues a `leadership_requests` handover row from the current leader
  (`db/leadership.py:insert_request`, kind `handover`, reason `rollout`, no target) only when every other outdated pod
  is replaced and an idle eligible member exists; the dispatcher's pass applies it as it applies every handover
  (`leader_reason` `handover: rollout`). The leader pod is deleted only after `session_leaders` names another agent.
- (my call) `status.rollout` (written with the other status fields, dropped when nothing is pending):
  `{"revision": <updateRevision>, "pending": [ordinals], "waiting": [ordinals held busy], "leader_pending": bool}`.
- (my call) The switch to OnDelete and any template change of the same release reach the StatefulSet in one
  server-side apply, so the deploy of this epic itself rolls no pod by the controller.

### D2: A deploy never runs inside a pod that the same deploy rolls

User decision, verbatim: ""A deploy never runs inside a pod that the same deploy rolls" is satisfied by D1: the
deployer's pod is busy for the whole apply+smoke turn so it is not rolled until idle; an in-cluster Job runner is a
non-goal. Add an orchestrator test that pins this (busy pod with outdated revision is not deleted across reconcile
ticks)."

### D3: The ingester re-attaches after a successful wrapper resume

User decision, verbatim: "Ingester root cause: the bootstrapper's successful resume becomes a re-attach trigger (e.g. a
resume generation/timestamp on the agent row included in AgentRef or equivalent); a stored session_closed is honoured
only if no resume happened after it; re-attach replays from the last stored seq (wrapper keeps seq across resume;
carto-orchestrator.md item 1). Amend tests/test_ingester.py:723 with the reason. Also mark the agent idle/ready again on
re-attach so the dispatcher delivers."

- (my call) "After it" is decided by database order (the events row id or the database clock), never by comparing the
  wrapper's event `ts` with the database clock (clock-skew debt recorded by leader-auto-handover).
- (my call) The marker is a new column on `agents` written only by the reconciler (the agents row's writer), in a new
  migration numbered after the highest one on main when the task runs (0008 today; 0009 if
  slash-commands-from-chat's `0008_slash_messages.sql` lands first).
- `tests/test_ingester.py::test_session_closed_marks_dead_and_stops` is amended: it still holds when no resume
  followed the close; the reason is written in the test.

### D4: A dead agent is never eligible to lead

User decision, verbatim: "Leader eligibility excludes agents whose agent_status is dead (db/eligibility.py), all call
sites covered by tests."

- (my call) Both `ELIGIBLE` and `READY_STAYS` (the manual make-leader target) exclude a dead agent; a leader whose
  agent is dead is handled as a lost leader (moved after `LEADER_GRACE_SECONDS`, reason `leader_lost`), so G2's
  "leadership moves to a live agent" holds. This is the exclusion itself, not a new handover rule (README non-goal).

### D5: The wrapper continues a turn its own shutdown interrupted

User decision, verbatim: "Wrapper: a turn interrupted by service shutdown is recorded distinguishably from a user
stop/delete; on resume (API resume and load_persisted) such a turn is continued with restart_continue_prompt when
configured; the orchestrator renders a default restart_continue_prompt (render.py:130). Wrapper gets a release tag (next
patch, 0.3.2) and pyproject version fixed to match."

- (my call) Mechanism: on service shutdown the running turn stays `running` in turns.jsonl with a marker
  (`interrupted: "shutdown"`), no `turn_failed` is emitted; a user stop or delete keeps ending it `failed` with
  `session_stopped`. On resume with `restart_continue_prompt` set, the fresh Session adopts that record and continues
  the same `turn_id` (a `turn_resumed` event, cause `resume`), so the orchestrator's turn row and message complete
  normally; without the prompt it ends `failed` with error `service_shutdown`. A turn left `running` by a killed process
  is treated the same way. Alternative rejected: end the turn `failed` at shutdown and start a new turn on resume (the
  orchestrator would record a failure and the message would not complete).
- (my call) The default prompt is an orchestrator setting `ORCH_DEFAULT_RESTART_CONTINUE_PROMPT` (default "Claude was
  restarted. Continue the task where you left off.", the wrapper's own example text), overridden by
  `spec.wrapper.restart_continue_prompt`.
- Release: tag `v0.3.2` (Q1 covers a v0.4.0 tagged first by slash-commands-from-chat), pyproject and `__version__`
  equal, pushed by the orchestrator session after the wrapper PR merges (precedent wrapper-release-0-3-0).

### D6: The onStart plugin install is non-fatal

User decision, verbatim: "onStart plugin install: stays blocking (tools ready before sessions resume) but with on_error
allow, and the on_start.py script logs and swallows an install failure (never exits non-zero for it, never exit 2); a
failed install leaves the pod Ready."

- (my call) Both installs are covered: the any-mcp package install (then `.ref` is not written, so the next start
  retries) and `any-mcp plugins install`; the trailing `any-mcp --help` check is skipped after a failed install. Each
  failure prints one line to stderr naming the step.

### D7: Claude transcripts are backed up with the workdir and restored on recreate

User decision, verbatim: "Transcript backup: reuse the cache Job/runner/archive/transfer/presign (parameterised, no
second S3 client). At discard, after the workdir save, save the PVC `sessions/` subtree as its own S3 object for that
session; at create, when the object exists for the same slug, restore it before agent pods start; the bootstrapper then
adopts the restored wrapper session of each ordinal (pod names are stable per slug) and resumes it instead of creating a
new one. Only when the session cache (spec.cache) is configured; otherwise nothing is backed up and the API/web say so.
Status exposes the last sessions backup (finished_at, bytes)."

- (my call) Object `<cache_s3_prefix>sessions/<slug>.tar.zst`: cache keys match `^[a-z0-9][a-z0-9._-]{0,62}$`
  (`spec.py:173`, no `/`), so it never collides with a workspace key. Jobs `agent-<slug>-sessions-save|restore`, label
  `agents.szymonrichert.pl/cache: sessions-save|sessions-restore`, mount PVC subPath `sessions`, no excludes, the same
  `cache_max_bytes` cap and hardening. Status `status.cache.sessions_save|sessions_restore` in the existing run shape
  (`state`, `started_at`, `finished_at`, `bytes`, `reason`, `job`).
- (my call) A save runs only after a sessions restore in `restored`, `miss` or `reset` (the workdir rule,
  `SAVE_OK_RESTORE_STATES`); a session whose StatefulSet already existed when the feature arrived records the restore
  `skipped` with reason `pods_exist` and still saves at discard. A restore never runs once a pod of the session exists.
- (my call) "Before agent pods start": while the sessions restore is pending the StatefulSet is applied with
  `replicas: 0`.

### D8: agents-web states what a discard loses and shows an agent-unavailable banner

User decision, verbatim: "Web: the discard dialog states exactly what is lost vs backed up (from the new status/meta
fields); the chat shows an "agent unavailable" banner when messages are queued and no agent is idle/ready, with the age
of the oldest queued message (orchestrator summary exposes oldest_queued_at; agent state `dead` is mapped in
agentMarkState). Re-sync the vendored OpenAPI (npm run sync:api)."

- (my call) API: `SessionSummary.oldest_queued_at` (null when none), also carried by the `message_status` stream frame
  so the banner stays live; `SessionView.backup` `{workdir: bool, transcripts: bool, reason: str|null,
  last_transcripts_backup: {finished_at, bytes}|null}`, where each flag is true only when the discard would really save
  it (spec.cache set, `cache_available`, its restore state allows the save) and `reason` names why not
  (`no_session_cache`, `cache_not_configured`, or the skip reason).
- (my call) `agentMarkState('dead', ready)` returns `error`. The banner shows when `summary.queued > 0` and no agent is
  ready and `idle` (Q2 asks whether busy-only hives should show it).

### D9: No red main build is published or deployed

User decision, verbatim: "Red builds: agents-orchestrator CI pushes images and publishes charts only after lint, test and
e2e pass (split the push out of `images` or gate a retag; e2e must not need the pushed image if that is how it works
today, check); agents-web image push and chart-publish need the `web` job. agents-helmfile gets a pin check (gh api
check-runs, or reuse plugins/workbench/skills/_lib/scm.py reducers) for every pinned main-built commit (orchestrator,
web, webhook, schedule, matrix-connector charts; wrapper release tag resolved to its commit) that apply depends on; no
override flag. Its tests use fakes like tests/test_smoke_script.py."

- Checked: the e2e job builds and loads its own images (`mise run test:e2e`, `scripts/e2e.sh`); it does not pull the
  pushed orchestrator image, so `e2e` may stop needing `images`.
- (my call) The pin check calls `gh api repos/szymonrychu/<repo>/commits/<ref>/check-runs` from a script in
  agents-helmfile: the submodule is an independent repo and cannot import the workbench's `_lib/scm.py`. A pin passes
  only when at least one check run exists and every one is `completed` with conclusion `success`, `neutral` or
  `skipped`. `0.1.0-main.<sha7>` resolves to that commit; a release version `X.Y.Z` (agents-schedule chart `0.1.0`,
  wrapper image `0.3.2`) resolves through tag `vX.Y.Z`. `mise run apply` depends on it.

### D10: The main CI e2e failure is diagnosed and fixed before e2e gates publishing

User decision, verbatim: "The orchestrator main CI e2e failed on run 40565058706 (commit 96e46f3) while the PR run
40562435463 passed: one task diagnoses it from the run log (gh run view --log-failed) and fixes the cause, so gating on
e2e keeps main green."

- Probe (planner, read-only): the failed test is `tests/e2e/test_e2e_kind.py::test_in_session_pod_refused_by_allowlist`,
  `httpx.RemoteProtocolError: Server disconnected without sending a response.` on the port-forwarded `api` client,
  `1 failed, 39 passed`. The cause is the task's to confirm.

### D11: A kind e2e rolls the agent image while a turn runs

User decision, verbatim: "Regression e2e (kind, tests/e2e/test_e2e_kind.py): roll the agent image (helm upgrade to a
second tag of the same image) while a slow turn runs; assert the busy pod is not replaced until idle, the leader rolls
last, the wrapper session id is unchanged, the interrupted/queued messages are delivered and the agent never stays
dead. Lengthen the fake "slow" turn as needed."

- (my call) A new scenario turn (its own match text) holds the long turn, so the 4 s "slow" turn other tests rely on
  is unchanged. For "interrupted" messages the test also deletes one busy pod by hand (a crash, accepted under D1): it
  returns on the new template, its wrapper session id is unchanged and its interrupted turn completes through the D5
  continuation.

### D12: smoke.sh gets a session-continuity check on a smoke-owned pod

User decision, verbatim: "smoke.sh in agents-helmfile gets a session-continuity check if a safe trigger exists without
rolling real agents; otherwise record why not (my call)."

- (my call) A safe trigger exists: deleting the pod of a session the smoke itself created (smoke already scales its
  own session's pods). After one real turn, the pod is deleted; the smoke asserts the pod returns Ready, the agent's
  wrapper session id is unchanged, the agent is not `dead`, and a message sent after the restart reaches `sent`. No
  user session and no template change is involved.

### D13: Release, pin, apply, smoke and a live check

User decision, verbatim: "Delivery: wrapper tag 0.3.2, orchestrator/web pins, agents-helmfile bump, apply, smoke, plus a
live check after the deploy that no busy agent pod was replaced (reconciler logs / pod ages). Deploys and planned
release tags are pre-approved."

- Precedent: leader-auto-handover tasks wrapper-release-0-3-0, orch-wrapper-pin-0-3-0, helmfile-deploy-pin,
  helmfile-apply-smoke. Live applies and the tag push are run by the orchestrator session, never a subagent.

### D14: Sequencing with the in-progress epic slash-commands-from-chat

(my call) Fact: 11 of this epic's 22 tasks share files with not-done tasks of in-progress epic
slash-commands-from-chat (wrapper `session.py`, `manager.py`, `router.py`, release files; orchestrator `render.py`,
golden files, `settings.py`, `ingester/loop.py`, `views.py`, `schemas.py`, `openapi.json`, wrapper pins,
`test_e2e_kind.py`; web vendored OpenAPI), and `ticket.py new-task` refuses them while that epic is in progress and is
not a blocker of this one. The 11 tasks with no shared file are created; the other 11 (orch-ingester-reattach,
orch-onstart-nonfatal, orch-default-continue-prompt, orch-rollout-replacer, orch-api-session-safety,
orch-e2e-main-failure, wrapper-shutdown-turn-resume, wrapper-patch-release, orch-wrapper-pin-patch,
orch-e2e-rollout-mid-turn, web-sync-session-safety-api) are prepared verbatim in `.scratchpad/session-loss/plan/`
(`tasks.json` plus `<slug>.req.md` and `<slug>.ac.md`) and created once Q3 is answered.

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| research-code-internal (cartographers, lane 1) | ran; LSP was unavailable to every cartographer, so lane 1 fell back to grep and Read (`.scratchpad/session-loss/carto-orchestrator.md`, `carto-wrapper.md`, `carto-web.md`, `carto-deploy.md`) | ingester re-attach seam (`ingester/loop.py:292-306`); wrapper seq continues across resume (`events.py:157-158`); fake kube `_sync_pods` (`tests/fakes/fake_kube.py:358`); e2e builds its own images (`scripts/e2e.sh`) | none |
| reuse hunt (lane 2) | ran: `.scratchpad/session-loss/reuse.md` (grep only, jscpd unavailable) | cache Job/runner/archive/transfer/presign parameterised; `_draining`; leadership handover; `continue_turn`/`restart_continue_prompt`; smoke fakebin harness | separate deploy-time CI poller in the workbench (D9 puts the check in agents-helmfile) |
| research-docs and prior art (lane 3) | ran: `docs/research/2026-10-27-session-survival.md` (`.scratchpad/session-loss/research.md`) | OnDelete plus busy-aware replacer [1][5]; `--resume` keeps the id [6]; Last-Event-ID replay [12]; check-runs not combined status [19] | partition [1]; PDB gating [2]; preStop-only [3]; maxUnavailable [20]; deadline-bounded replacement (user D1: no deadline) |
| incident evidence (lane 4) | ran: `hang-analysis.md` (root cause), `cluster-evidence.md`, `code-analysis.md`, `mx34-hypotheses.md` | root cause D3; dead-leader D4; continue prompt D5; onStart D6; red-main publish D9 | hypotheses A (two status rows) and C (web) refuted by evidence |
| research-papers | skipped: no algorithmic core | none | none |

## Research inputs

| Finding | Source | Task |
|---|---|---|
| recurring workflow: Harbor prunes wrapper sha7 tags; pin the wrapper by release tag and cut it before the orchestrator pin | RETRO file-editor-with-tabs-and-hi, generic-any-mcp-with-git-and | wrapper-patch-release before orch-wrapper-pin-patch; helmfile-deploy-pins pins `claude-code-wrapper:<release>` |
| recurring workflow: live apply, smoke, e2e and release tasks run 3-4x the minutes seed | RETRO leader-auto-handover, generic-any-mcp-with-git-and | helmfile-apply-live-check 5 points, orch-e2e-rollout-mid-turn 5, helmfile-smoke-continuity 5 |
| recurring workflow: no Docker in agent pods, orchestrator DB and e2e tests are CI-only | RETRO file-editor-with-tabs-and-hi, file-download-in-file-browse, leader-auto-handover | every orchestrator DB task names its CI evidence in Notes; epic-run treats the PR CI watcher as the full-suite gate |
| recurring workflow: defects missed per task surfaced only in the epic review (size caps, deadlines) | RETRO file-editor-with-tabs-and-hi, leader-auto-handover | Review focus; orch-sessions-backup-save AC on the size cap; helmfile-smoke-continuity notes every wait has its own deadline |
| recurring workflow: fakes encoded a wrong assumption about an external tool's output | RETRO generic-any-mcp-with-git-and | helmfile-pin-check: fakes built from a captured real `gh api .../check-runs` response committed as a fixture |
| recurring workflow: a vitest load flake was never named | RETRO markdown-rendering-in-chat, file-editor-with-tabs-and-hi | web tasks' Notes: save the failing test name and output tail before any rerun |
| recurring workflow: `new-task` keeps only Requirement, AC and Files | RETRO leader-auto-handover | every task carries interfaces, steps and notes inside its Requirement |
| ingester never re-attaches after `session_closed` (fix-as-ac) | reuse.md, hang-analysis.md | orch-ingester-reattach |
| `restart_continue_prompt` not defaulted (fix-as-ac) | reuse.md | orch-default-continue-prompt |
| StatefulSet has no updateStrategy (fix-as-ac) | reuse.md, research.md | orch-rollout-replacer |
| `load_persisted` never continues a running turn (fix-as-ac) | reuse.md, carto-wrapper.md | wrapper-shutdown-turn-resume |
| onStart denies on any failure (fix-as-ac) | reuse.md, mx34-hypotheses.md | orch-onstart-nonfatal |
| cache Jobs fixed to workdir restore/save, gated by spec.cache (fix-as-ac) | reuse.md | orch-sessions-backup-save, orch-sessions-backup-restore |
| chart-publish does not need e2e; image pushed before e2e | carto-deploy.md, research.md | orch-ci-publish-gate |
| agents-web publish does not need the `web` job | carto-web.md | web-ci-publish-gate |
| exit keystrokes on SIGTERM; grace documentation (research fix-as-ac) | research.md | not acted on: README non-goal |
| helmfile in a Job runner; SSE epoch; SessionStart id verification (research ideas) | research.md | not acted on: non-goal (D2) or not in the user decisions |
| `_target_ready` omits `wrapper_session_id IS NOT NULL` (code item) | RETRO leader-auto-handover | not acted on: no ruling recorded; D4 only adds the dead exclusion |
| agents-helmfile has no CI workflows (tech debt) | RETRO leader-auto-handover | noted, not doing now |

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 OnDelete plus idle-only replacer, leader last | orch-rollout-replacer, orch-api-session-safety, orch-e2e-rollout-mid-turn |
| D2 A deploy never runs inside a pod the same deploy rolls | orch-rollout-replacer, helmfile-apply-live-check |
| D3 Ingester re-attaches after a resume | orch-ingester-reattach, orch-e2e-rollout-mid-turn |
| D4 A dead agent is never eligible to lead | orch-dead-agent-ineligible |
| D5 Wrapper continues a shutdown-interrupted turn | wrapper-shutdown-turn-resume, orch-default-continue-prompt, wrapper-patch-release, orch-wrapper-pin-patch |
| D6 Non-fatal onStart plugin install | orch-onstart-nonfatal |
| D7 Transcripts backed up and restored | orch-sessions-backup-save, orch-sessions-backup-restore, orch-api-session-safety |
| D8 Discard notice and agent-unavailable banner | orch-api-session-safety, web-sync-session-safety-api, web-discard-backup-notice, web-agent-unavailable-banner |
| D9 No red main build published or deployed | orch-ci-publish-gate, web-ci-publish-gate, helmfile-pin-check |
| D10 Main CI e2e failure fixed | orch-e2e-main-failure |
| D11 Kind e2e rolls the image mid-turn | orch-e2e-rollout-mid-turn |
| D12 Smoke session-continuity check | helmfile-smoke-continuity |
| D13 Release, pin, apply, smoke, live check | wrapper-patch-release, orch-wrapper-pin-patch, helmfile-deploy-pins, helmfile-apply-live-check |
| D14 Sequencing with slash-commands-from-chat | orch-dead-agent-ineligible, orch-sessions-backup-save, orch-sessions-backup-restore, web-ci-publish-gate, helmfile-pin-check, helmfile-smoke-continuity |

## Review focus

- The replacer: the window between its idle check and the pod delete (a message claimed in between must not be lost:
  it is retried through the existing verify path, never dropped); a pod is never deleted while busy, leading, or holding
  a `dispatching`/`verifying` message, across any number of ticks; one pod at a time per session.
- Fake kube revision modelling matches the real controller: under OnDelete a pod keeps its `controller-revision-hash`
  until deleted and returns at `status.updateRevision`.
- The ingester's "resume after close" order uses database order only; re-attach never re-projects replayed events.
- The sessions restore never touches a session with an existing pod; the archive honours `cache_max_bytes` and symlinks
  as the workdir archive does; no credential reaches the Job beyond the one presigned URL.
- The pin check's fakes match a captured real `gh api` response; every pin source in helmfile is covered; no override.
- Smoke step: every wait has its own deadline (leader-auto-handover retro).

## Left to the builder

- The replacer's module layout (a new `reconciler/rollout.py` or functions in `loop.py`) and how `_converge` orders it
  with bootstrap and drain, within D1.
- The re-attach marker's exact column (a timestamp or a counter) and how `_stored_closed` compares, within D3's
  database-order rule.
- The CI shape for D9 in agents-orchestrator: a separate push job or a gated push step, as long as nothing reaches
  Harbor before lint, test and e2e pass, and e2e does not need the pushed image.
- How the wrapper stores the interrupt marker (a TurnRecord field or a session.json field), within D5.

## Assumptions and unknown facts

- Real Kubernetes labels each StatefulSet pod with `controller-revision-hash` equal to a revision name compared with
  `status.updateRevision` (research.md marks the label low confidence); the kind e2e (orch-e2e-rollout-mid-turn)
  confirms it.
- Real Claude 2.1.304 `--resume <id>` keeps the session id and appends to the same transcript (research.md [6]); the
  fake claude stands in for it in every test; the live check in helmfile-apply-live-check observes it.
- A restored wrapper session passes the wrapper's `_check_resumable` (config dir, transcript, workdir at the same path
  per slug); orch-sessions-backup-restore proves it against the real wrapper contract leg in CI.
- Who runs `gh` in agents-helmfile (auth in the deploying pod) is the deploy session's; the apply task checks it first.

## Open questions
- Q1: slash-commands-from-chat (in progress) will tag claude-code-wrapper v0.4.0; if v0.4.0 is tagged before this epic's wrapper release, cut the next patch above the latest tag (v0.4.1) instead of v0.3.2 (tasks wrapper-patch-release, orch-wrapper-pin-patch, helmfile-deploy-pins, helmfile-apply-live-check)? [recommended: yes]
- Q2: The agent-unavailable banner shows whenever messages are queued and no agent is ready and idle, so a hive whose agents are all busy shows it too; keep that literal reading of D8? [recommended: yes, keep it; the banner gives the queued count and the oldest message's age]

## Irreversible operations in scope

- Tag `v0.3.2` (or per Q1) pushed on claude-code-wrapper `main`; release.yaml retags `:0.3.2` and `:latest`
  (pre-approved, D13; orchestrator session only).
- `mise run apply` of agents-helmfile on the live namespace `agents`: the orchestrator migration adding the re-attach
  column runs on start (additive); agent pods are then replaced by the replacer when idle (pre-approved, D13).
- Sessions backup objects `<prefix>sessions/<slug>.tar.zst` are overwritten on every discard of that slug (same policy
  as the workspace cache object).
