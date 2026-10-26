# matrix read receipts retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| mxc read receipts | 2 | 2 | 6 | 5 | 545296 | 913402 |
| connector repin receipts | 1 | 1 | 4 | 4 | 665870 | 255136 |
| apply receipts live | 1 | 1 | 4 | 90 | 665870 | 1044057 |
| Total | 4 | 4 | 14 | 99 | 1877036 | 2212595 |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| mxc read receipts | 0 | 0.83 | 1.68 |
| connector repin receipts | 0 | 1.00 | 0.38 |
| apply receipts live | 0 | 22.50 | 1.57 |

- MdAPE points: 0.0%
- MdAPE minutes: 20.0%
- MdAPE tokens: 40.3%
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| 3 tasks delivered; connector repin receipts closed in 0 fix rounds (4 min vs 4, tokens 255136 vs 665870, 0.38x, suite 184 passed). | mxc read receipts needed 1 fix round: the id tiebreak was not pinned by tests (suite 192 passed after the fix); tokens 913402 vs 545296 (1.68x). |
| Epic review clean: scope audit clean, helm rev 2 (chart 0.1.0-main.98b0803), post-apply diff showed no drift; PRs agents-matrix-connector #2 and agents-helmfile #27 landed. | apply receipts live took 90 min vs 4 (22.50x), tokens 1044057 vs 665870 (1.57x); minutes MdAPE only 20.0% because the other two tasks were on estimate. |
| Points estimates held (MdAPE 0.0%, 4 vs 4); the receipt POST answered 200 and the user confirmed the message shows as seen (AC3). | The main orchestrator session was gone; the apply ran in this session only after the user's standing approval (AskUserQuestion), with a clean pre-diff changing only the connector. |
| Apply was gated on a clean pre-diff and a one-time user approval, so the live change touched only the connector. | The apply and diff hit a transient gpg "Cannot allocate memory" error; restarting gpg-agent and retrying fixed it. |
| Smoke passed on the re-run and the leftovers were removed with the user's OK. | The first smoke failed because its local port-forward died; it left smoke resources behind and the permission classifier blocked the subagent's cleanup DELETEs until the user approved. |
| | The live proof (AC3) depended on the user sending a message; it could not be completed unattended. |

## Improvements

- Code:
  - agents-matrix-connector read receipt path: keep tests pinning the id tiebreak (which event gets the receipt) so it cannot regress; the pin was added only after review.
- Delivered differently:
  - The apply ran in the planning/retro session, not the main orchestrator (gone), by explicit user approval for this epic only.
  - The live proof (AC3) was confirmed by the user's message ('Seems to be working'), not by an automated check.
- Tech debt:
  - Smoke script leaves resources behind when its port-forward dies (agents-helmfile smoke task): make it clean up in a trap or use a labelled sweep.
  - gpg-agent memory flake on apply/diff (local tooling): no fix in place; a retry wrapper in the apply task would remove the manual restart.
- Workflow:
  - recurring (agents-matrix-connector-depl, agents-schedule-deploy): live apply and smoke tasks run far over the minutes seed (90 vs 4 here, 26 vs 5 and 19 vs 5 before). Change: seed live apply/smoke tasks at 15-25 min and add user-dependent proof steps on top, calibrated from earlier actuals.
  - recurring (agents-matrix-connector-depl): the permission classifier blocks subagent live actions (kubectl exec there, cleanup DELETEs here). Change: plan live proof and cleanup as orchestrator-run steps, or record the approval in the plan before dispatch.
  - recurring (agents-matrix-connector-depl): acceptance that needs a user action (first real message there, a sent message here) stalls the apply task. Change: the deploy template lists user-action steps and asks for them up front, so the user is ready when the apply lands.
  - Smoke port-forward dying and the gpg flake are single occurrences; Retro table only.
