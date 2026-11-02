# claude-usage-monitor: retro

Final review, 2026-11-02, against `plan.md` (agreed scope), `implementation.md`, the SDD ledger
(`.superpowers/sdd/implementation/progress.md`) and the merged code on origin/main:
agents-usage v0.1.0, agents-orchestrator v3.3.0, claude-code-wrapper v0.8.0 and v0.8.1,
agents-common v0.7.0, agents-webhook v0.4.0, agents-schedule v0.5.0,
agents-matrix-connector v0.4.0, agents-web v0.13.0, agents-helmfile #66, #69, #67, #73 and the
open #74.

## Verdict

Complete against the agreed scope, with three Important follow-ups (one design question for
the user, one robustness fix, one credential hardening that predates the epic).

| User requirement | Delivered | Where |
|---|---|---|
| Weekly and 5-hour usage | yes, plus any other window (shown, not gated) | agents-usage parser, `current`, web cards |
| API (Console) usage | dropped by the user (Q5) | - |
| Gradual stop per preset | yes: sparse `usage_quota {five_hour_pct, seven_day_pct}` on the preset, snapshotted into the session, default 100 | orchestrator `spec.py`, web preset form |
| Hard gate on session start and scale-up | yes: every create (main, service and admin ports) and both scale routes; 409 `usage_quota`, the insert rolls back, no pod | orchestrator `api/sessions.py`, `api/agent.py`, `api/usage_gate.py` |
| Triggers wait out a refusal | yes: webhook, schedule and matrix hold the item until `retry_at` | agents-common, the three triggers |
| Graph over time with session marks | yes: downsampled history, quota lines, 24h/7d/30d, session lane on the same x axis | agents-usage history/sessions, web `src/usage/*` |
| Passive statusLine source plus lazy probe | yes: the wrapper forwards `rate_limits`; the probe runs only on a gate read with data older than 30 min, at most once per 30 min | wrapper `usage_forward.py`, agents-usage prober |

Live (infra #807): the usage page and `/usage/v1/current` and `/history` answer 200, the source
is `statusline`, the gate is on with the default 100 %, and no preset quota is set yet (Group F,
the user's step).

## Findings

### Important

1. The gate never acts on stale data, so it is open after every idle period.
   `agents-orchestrator/src/agents_orchestrator/api/usage_gate.py:66` skips a window when
   `stale`. Usage inside one window only grows, so a stale reading that already breaches is a
   lower bound: the real value is at least that high. As built, once no agent has posted for
   30 min, the first gate read after the pause and every create in its 30 s cache window are
   allowed even at 100 %. That read also triggers the probe. If the probe fails, the 30 min
   minimum interval keeps the gate open for up to 30 more minutes.
   The scenario is likely: when the quota is reached, starts stop, the agents go quiet and the
   data goes stale. The behaviour follows Q3 ("allow and warn"), but Q3 was about missing data,
   not about a known-high reading.
   Fix: in `breach()`, gate on a stale window whose `resets_at` is in the future and whose
   `percent >= limit`. Keep allow-on-missing and allow-on-unreachable. Needs a user yes, since
   it narrows Q3.
2. No plausibility bound on `resets_at`, so one bad sample can shadow the real window for
   8 days. `agents-usage/src/agents_usage/parser.py:46-62` accepts any finite epoch, and the
   wrapper accepts up to year 2100 (`claude-code-wrapper/src/claude_code_wrapper/internal_api.py:155`).
   `current_view` (`agents-usage/src/agents_usage/api/usage.py:55-61`) reports the group with
   the latest `resets_at`. A single sample with a far-future reset then becomes "current" until
   its `observed_at` leaves the 8-day lookback. Such a sample can come from a forged post with
   the ingest token, a CLI unit change or a client bug.
   For its first 30 min it gates everything if it is high. After that it is stale (see 1), so
   the gate fails open and the UI shows the wrong number.
   Fix: refuse or ignore windows with `resets_at > observed_at + 8 days` (tighter per known
   metric: 5 h, 7 d), in both parsers.
3. The credential surface outside mise is unchanged. Wrapper 0.8.1 cleaned the mise, setup,
   git and plugin-install children (`manager.py:720`, `tooling.py:104,121`), and the ingest
   token is kept out of the claude child, hooks and the statusLine chain. The OAuth token still
   reaches two places:
   - Wrapper hook commands. `hooks.py:225` strips only `CCW_USAGE_TOKEN`, and the base env is
     the full service env (`manager.py:1443`, `hooks.py:438`), so preset-defined hook commands
     (`agents-orchestrator spec.py:487`) run with `CLAUDE_CODE_OAUTH_TOKEN` and
     `CCW_AUTH_TOKEN`.
   - Claude Code's own hooks and Bash children, because `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` is
     set nowhere (orchestrator render, helmfile values).

   Also, everything in the pod runs as uid 1000. The "token only in the wrapper server process"
   split is therefore not a boundary against code the agent runs: same-uid processes can read
   `/proc/<pid>/environ`. This is pre-existing and was noted in ledger line 171. Not a
   regression.

### Minor

- Web: the cards have no per-window stale mark, only a page-level alert
  (`agents-web/src/usage/UsagePage.tsx:39-60`). Sessions `truncated` is ignored and `limit` is
  never sent (`src/usage/UsageHistory.tsx:33`), so a busy 30d range can silently drop lane bars.
  This was parked in the D4 ledger.
- Web: any poll error hides an already loaded chart, and a range switch keeps the old error
  until the next fetch succeeds (`UsageHistory.tsx:67-70`).
- agents-common: a naive `resets_at` makes `retry_at` raise `TypeError`
  (`orchestrator.py:74`, parse at `:240-255`). Today the orchestrator always sends an offset, so
  this is only a latent bug.
- matrix: `room_holds` rows are never pruned. Growth is bounded at one row per room.
- schedule: the `store.hold` result is ignored, so "held until" is logged even when the guard
  lost the row.
- helmfile #74 is based on 450956c, before #73. The PR diff and the merged tree are fine. A
  two-dot diff looks like a web revert, so rebase it if anyone compares trees.
- The watcher's 60 s read timeout against the orchestrator stream's keepalive cadence was never
  confirmed live (A6 deferred minor). If there is no keepalive, it reconnects every 60 s, which
  is harmless but noisy.

### Over-delivery

Nothing substantive beyond the scope:
- gitleaks hooks across the repos: requested separately by the user, m148.
- wrapper 0.8.1 credential hardening: requested via mx-99 #687.
- the prober's hourly prune timer: it never runs claude, ruled in the ledger.
- the wrapper's 16-window cap.
- the web origin legend and the `usePoll` generation fix.

### Open verification (planned live checks not evidenced in the ledger)

- Step 2: a new session start then end appears as one mark in `GET /usage/v1/sessions`.
- Step 2: the first real statusLine `raw` was compared with the schema-built fixture.
- Step 3: a create with quotas unset succeeds with the gate on.
- Step 4: a screenshot shows the chart and the lane aligned.
- Group F: one gated preset end to end, once the user sets quotas.

## What came up during implementation

- The data source changed three times after approval: `-p /usage` (no plan bars), then a haiku
  stream-json poll (user challenge, #613 and #620), then the passive statusLine route with a
  lazy probe (#624). A2 and A3 were built while that was parked. The final design is better,
  but the plan and implementation docs needed two amendments mid-flight.
- Version collisions with parallel work: dind-sidecar, the permission switch, then tatara-2.
  The planned orchestrator v3.1.0 shipped as v3.3.0 and web v0.10.0 as v0.13.0. The standing
  rule "on collision take next free" (#645) removed the friction, but the docs still say the
  planned numbers.
- Credential leaks were found by review, not by design. In W1 the usage token reached hook
  commands and mise. In #22 the OAuth token reached git, setup and plugin installs through
  `passthrough_env`. Each needed a fix round, and 0.8.1 was a separate release and pin.
- The helm chart refuses an orchestrator usage token without a URL, so the planned C7/C4 split
  (gate off, then gate on) collapsed. The gate went on in the same deploy as the wrapper
  forwarding.
- Deploy blockers outside the code: no Harbor chart pull from the agent pod (held #66 for hours).
  `mise run apply` was unusable because its `test` dependency fails on environmental tests.
  `test_values_dir_moved` left main red after #66 and #70. Mid-epic, helmfile applies moved to
  the infra hive.
- Postgres tests could not run in agent pods. DB evidence came from CI, then from a local pg16
  once one was available. That pushed several real failures (C5 `ORCH_MASTER_KEY`) to PR CI.
- Leadership changed hands repeatedly (tatara-0 and tatara-1, epochs 2 to 9). The ledger and
  run notes carried the state well enough that no task was redone.

## What was overlooked in discovery and planning

- The wrapper already relayed the statusLine, which was the cheapest correct source. The first
  plan used it, but its rejection sent the design to a CLI probe. Discovery should have
  presented the passive route as "inside the new microservice's ingest", which is what the user
  accepted in the end.
- The child-process env was not mapped: which processes in an agent pod inherit which secrets
  (claude child, Claude Code hooks and Bash, wrapper hooks, mise, setup, the statusLine chain).
  Discovery did not do this, so the token rules were stated as intents and checked piecemeal in
  review. The same-uid `/proc` caveat was never considered.
- The gate's failure modes were reviewed one at a time but never against the steady state that
  matters. When the quota is reached, starts stop, agents go quiet, data goes stale and the gate
  opens (finding 1).
- Input plausibility stopped at type and range checks. Nothing bounds `resets_at` against the
  window length, and the "latest reset wins" rule turns one bad value into a long outage of
  correct data (finding 2).
- Version numbers were fixed at plan time in a multi-hive repo set. They should be reserved at
  merge time.
- Deploy prerequisites were not checked before step 1: Harbor pull credentials for the deploying
  pod, a green `mise run apply` path, and who owns applies.
- No end-to-end live check of the gate itself (refuse at quota, trigger hold, retry after reset)
  was planned before quotas are set. It is left to Group F "on request".

## Recommendations

1. Make the hard gate hold through idle periods. In `usage_gate.breach`, gate on a stale window
   that still breaches and has not reset. Fail open only when data is absent or the service is
   unreachable. One orchestrator patch with tests. Ask the user first, since it narrows Q3.
2. Bound `resets_at` at ingest and probe parse (`observed_at < resets_at <= observed_at + 8 d`,
   or per metric). Also add a test that a far-future sample cannot become `current`.
3. Finish the credential story in one small epic.
   - Set `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1` in rendered agent pods, after checking which
     tools the agents need.
   - Strip `CREDENTIAL_ENV` and `CCW_*` from wrapper hook-command env (`hooks.py:225`), with an
     allow-list for what hooks need.
   - Decide whether to run claude under a separate uid or make the wrapper non-dumpable, so the
     env split becomes a real boundary.
   - Keep a per-pod env map in the wrapper README.
4. Run the open live checks above, then one Group F end-to-end check on a scratch preset: quota
   below current usage gives 409 `usage_quota`, a trigger item is held, and the hold clears
   after `retry_at`.
5. Clear the parked web minors: per-card stale mark, surface `truncated` and send `limit`, keep
   the last good chart on a poll error. Also fix common's naive `resets_at` and prune
   `room_holds`.
6. Process:
   - Reserve versions at merge, not in the plan.
   - Before deploy step 1, verify pull credentials and a working apply path.
   - Plan a "secrets per process" table in discovery for any epic that touches agent pods.
   - Check every new decision against the system's steady state under the condition it is meant
     to handle.
