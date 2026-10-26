# Cross-session messaging and Kubernetes access session options retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| anymcp session tools | 3 | 2 | 7 | 5 | 977684 | 616636 |
| orch session message sender | 5 | 5 | 12 | 8 | 1686779 | 1551801 |
| web chat session messages | 2 | 2 | 6 | 3 | 553016 | 367055 |
| orch session options spec | 3 | 3 | 7 | 10 | 977684 | 1867270 |
| chart kube access rbac | 3 | 3 | 7 | 4 | 977684 | 874456 |
| orch agent service accounts | 3 | 3 | 7 | 14 | 977684 | 1056760 |
| orch agent session messaging | 5 | 5 | 12 | 7 | 1686779 | 3551619 |
| orch any-mcp pin 0.4.0 | 2 | 2 | 6 | 4 | 553016 | 742305 |
| web preset session options | 3 | 3 | 7 | 4 | 977684 | 760642 |
| orch kube access render | 3 | 3 | 7 | 3 | 977684 | 967422 |
| orch render session tools | 3 | 2 | 6 | 4 | 553016 | 1565873 |
| Allow the init-scripts tools agents are told to use | 2 | 2 | 5 | 3 | 553016 | 542373 |
| Agent ServiceAccounts do not inherit api annotations | 1 | 1 | 4 | 2 | 661202 | 235424 |
| smoke session options | 5 | 5 | 12 | 35 | 1686779 | 2711690 |
| helmfile deploy pin | 2 | 2 | 6 | 17 | 553016 | 471124 |
| Smoke waits for agent readiness before make-leader | 2 | 2 | 5 | 12 | 545296 | 543584 |
| Total | 47 | 45 | 116 | 135 | 14898019 | 18426034 |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| anymcp session tools | -1 | 0.71 | 0.63 |
| orch session message sender | 0 | 0.67 | 0.92 |
| web chat session messages | 0 | 0.50 | 0.66 |
| orch session options spec | 0 | 1.43 | 1.91 |
| chart kube access rbac | 0 | 0.57 | 0.89 |
| orch agent service accounts | 0 | 2.00 | 1.08 |
| orch agent session messaging | 0 | 0.58 | 2.11 |
| orch any-mcp pin 0.4.0 | 0 | 0.67 | 1.34 |
| web preset session options | 0 | 0.57 | 0.78 |
| orch kube access render | 0 | 0.43 | 0.99 |
| orch render session tools | -1 | 0.67 | 2.83 |
| Allow the init-scripts tools agents are told to use | 0 | 0.60 | 0.98 |
| Agent ServiceAccounts do not inherit api annotations | 0 | 0.50 | 0.36 |
| smoke session options | 0 | 2.92 | 1.61 |
| helmfile deploy pin | 0 | 2.83 | 0.85 |
| Smoke waits for agent readiness before make-leader | 0 | 2.40 | 1.00 |

- MdAPE points: 0.0%
- MdAPE minutes: 65.2%
- MdAPE tokens: 27.0%
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| Interrogate panel (fable/opus/sonnet) ran on the design before the gate and caught a nomenclature break and a ping-pong hole before build. | An implementer claimed an AC passed that it had run before committing (tracked-files guard); the claim was not true of the committed tree. |
| Parallel per-repo task lanes (any-mcp, orchestrator, web, helmfile, chart); 16 tasks, points MdAPE 0.0% (47 est vs 45 post-delivery). | A task's AC named a nonexistent test file (orchestrator-written task), so the AC could not be verified as written. |
| Security review found a real MEDIUM (agent ServiceAccounts inherited api annotations); fixed as task agent-serviceaccounts-do-not (2 min vs 4). | Implementers' pytest `-q` config hides pass counts, so verify claims carried no numbers. |
| Whole-diff review found no findings across seams; scope audit: all landed; full suites green (orchestrator 1027, web 429, any-mcp 215, helmfile 208). | PR e2e (agents-orchestrator #22) caught two kind assertions still expecting the two-tool allow list; the task's local verify could not run kind (fixed f92cc8d). |
| Scope audit/review findings became tasks (init-scripts tools allow list, SA annotations, smoke readiness) and closed quickly. | Pre-existing smoke race (make-leader before agent ready) surfaced only at live deploy; smoke session options took 35 min vs 12 (2.92x), smoke readiness fix 12 vs 5, helmfile deploy pin 17 vs 6. |
| Third smoke run passed incl. kube access and superleader messaging (send, framed delivery, target_not_superleader refusal). | The orchestrator's own stray port-forward broke the second smoke run. |
| | Deploy also applied the never-applied wrapper 0.3.0 pin from the previous epic, widening the live change beyond this epic. |
| | Minutes MdAPE 65.2% and tokens 27.0%; orch agent session messaging tokens 3551619 vs 1686779 (2.11x), orch render session tools 2.83x, orch agent service accounts 14 vs 7 min. |

## Improvements

- Code:
  - agents-orchestrator kind e2e tests: allow-list assertions hard-code tool names; derive them from the shared allow-list constant so a list change cannot break e2e only.
  - agents-helmfile smoke script: wait for agent readiness before make-leader (landed in a68e876); keep a test or check pinning the wait.
  - tracked-files guard (orchestrator tests): add a check that runs against the committed tree, not the working tree.
- Delivered differently:
  - Added beyond plan: allow-the-init-scripts-tools (agents told to use a tool no allow list included) and agent-serviceaccounts-do-not (security MEDIUM), plus smoke-waits-for-agent-readin; each from review, audit or live findings.
  - Deploy applied wrapper 0.3.0 pin from the previous epic for the first time, alongside orchestrator de16c14 and web de64208.
  - R7 live kubectl proof left pending the user's U1 preset edit; access proven by the smoke instead.
- Tech debt:
  - ClusterRoleBinding agents-orchestrator-kube-access binds cluster-admin (agents-helmfile / chart): a scoped ClusterRole would remove it.
  - Advisory session-message limit can overshoot (D10, documented): an atomic counter would remove it.
  - 404 vs 403 slug probing (LOW, dismissed): uniform 404 would remove it.
- Workflow:
  - recurring (agents-matrix-connector-depl, matrix-read-receipts, agents-schedule-deploy): live apply/smoke tasks run 2.4-2.9x over the minutes seed here (35 vs 12, 17 vs 6, 12 vs 5). Change: seed live apply/smoke tasks at 15-25 min in planning, calibrated from earlier actuals.
  - recurring (matrix-read-receipts): a smoke port-forward broke a run (there it died, here the orchestrator left a stray one). Change: smoke script owns its port-forward (trap cleanup, kill stale on the port first) and orchestrator runs no manual port-forwards during smoke.
  - recurring (agents-matrix-connector, paste-env-contents-into-the): defects or false claims found late (security review, e2e, live deploy) that per-task verify missed. Change: epic-run requires implementer hand-backs to quote the verify summary line with counts and verify against the committed head sha; run pytest with a summary-printing flag (not bare -q) in task verify commands.
  - Orchestrator-written task ACs must name existing files: ticket.py lint should check that test paths in ACs exist or are marked "new" (one-off, Retro table only).
  - Pre-deploy check that lists previously unapplied pins in agents-helmfile (one-off, Retro table only).
