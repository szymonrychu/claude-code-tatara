# agents matrix connector deploy retro

<!-- retro:generated:begin -->
## Tasks

Delivery order; written by `ticket.py retro`.

| Task | Points (estimate) | Points (post-delivery) | Minutes (expected) | Minutes (actual) | Tokens (expected) | Tokens (actual) |
|---|---|---|---|---|---|---|
| helmfile matrix secrets | 2 | 2 | 7 | 8 | 538938 | 569216 |
| web matrix api client | 3 | 3 | 7 | 4 | 907602 | 460985 |
| helmfile matrix releases | 3 | 3 | 7 | 11 | 907602 | 610173 |
| web chats rooms page | 5 | 5 | 14 | 5 | 1860143 | 1164667 |
| smoke matrix check | 2 | 2 | 7 | 11 | 538938 | 871583 |
| orchestrator repin ab37f1e | 1 | 1 | 4 | 4 | 669602 | 182128 |
| web chats access panels | 5 | 3 | 14 | 5 | 1860143 | 538758 |
| web chats menu entry | 1 | 1 | 5 | 2 | 678580 | 194601 |
| helmfile web chats entry | 1 | 1 | 5 | 7 | 678580 | 343679 |
| apply smoke matrix | 1 | 1 | 5 | 26 | 678580 | 985030 |
| live reply proof | 1 | 1 | 4 | 2 | 668998 | 236276 |
| Total | 25 | 23 | 79 | 85 | 9987706 | 6157096 |

## Deltas

| Task | Points (post-delivery - estimate) | Minutes (actual / expected) | Tokens (actual / expected) |
|---|---|---|---|
| helmfile matrix secrets | 0 | 1.14 | 1.06 |
| web matrix api client | 0 | 0.57 | 0.51 |
| helmfile matrix releases | 0 | 1.57 | 0.67 |
| web chats rooms page | 0 | 0.36 | 0.63 |
| smoke matrix check | 0 | 1.57 | 1.62 |
| orchestrator repin ab37f1e | 0 | 1.00 | 0.27 |
| web chats access panels | -2 | 0.36 | 0.29 |
| web chats menu entry | 0 | 0.40 | 0.29 |
| helmfile web chats entry | 0 | 1.40 | 0.51 |
| apply smoke matrix | 0 | 5.20 | 1.45 |
| live reply proof | 0 | 0.50 | 0.35 |

- MdAPE points: 0.0%
- MdAPE minutes: 75.0%
- MdAPE tokens: 96.9%
<!-- retro:generated:end -->

## Retro

| Went well | Went bad / could be improved |
|---|---|
| 11 tasks delivered; 10 closed with 0 fix rounds (suites 169, 383, 182, 395, 396, 184 passed), 1 needed a fix round (web chats rooms page). | web chats rooms page: a failed rules load (listRules) was silently swallowed; caught only in review, 1 fix round. |
| Whole-diff review of agents-web clean (396 passed), PR #12 merged 122a404 with CI green; security review of agents-helmfile found 0 crit/high/med, 2 LOW dropped with reasons (sha7 pin convention, in-cluster http to synapse). | The CNPG backup credentials file (agents-webhook-db/default.secrets.yaml) was missing from the plan; helmfile matrix releases found it via the helmfile_build test (1 impl fix round, ruled byte-copy, 11 min vs 7). |
| Live apply OK, no post-apply drift, smoke OK, allow rule 3 created, joke message delivered (helmfile PR #26 merged d23e917). | The deploy waited hours: first on the user setting HARBOR_USERNAME/HARBOR_PASSWORD on szymonrychu/agents-matrix-connector, then on two other deploy epics using the shared helmfile/web files. |
| The orchestrator repin was added mid-epic on the main session's request and closed in 0 fix rounds (4 min vs 4). | The deploy was "green" but unusable: the plan never set a default preset, so the user's first real message was ignored with reason no_preset (default_preset_id null) until the user picked Default and PUT /settings returned 200. |
| Scope audit G1 (live reply unproven) became task live-reply-proof, closed in 2 min vs 4: inbound in-2 handled in session mx-1, reply out-1 sent. | The scope audit caught no_preset only after the user hit it; no pre-apply step checked that a message could be routed to an agent. |
| Points estimates held (MdAPE 0.0%); web chats access panels re-scored 5 to 3. | The subagent's kubectl exec for the joke message was denied by the permission classifier; the user approved and the orchestrator sent it. apply smoke matrix took 26 min vs 5 (5.20x). |
| UI tasks ran far under budget in tokens (web chats rooms page 1164667 vs 1860143; access panels 538758 vs 1860143). | Estimates remain flat and off: minutes MdAPE 75.0%, tokens MdAPE 96.9% (total 6157096 vs 9987706; repin 0.27x). |
| | The connector sends no read receipts (not in design); the user noticed after the deploy. |

## Improvements

- Code:
  - agents-web chats rooms page: keep a test that a failed listRules shows an error and does not render an empty list.
  - agents-helmfile agents-webhook-db/default.secrets.yaml copy: byte-copied encrypted file used by the matrix db; a test pinning each db release's backup credentials file exists (helmfile_build found it only by accident).
  - agents-matrix-connector: no read receipts sent; add m.read receipt after a handled inbound event.
- Delivered differently:
  - Orchestrator repin ab37f1e task added mid-epic at the main session's request (services Secret change needed the new pin).
  - Out-of-list file added: the CNPG backup credentials byte-copy (agents-webhook-db/default.secrets.yaml), ruled ok by precedent (schedule-db, orchestrator-db).
  - PresetSelect emptyLabel and the ChatsPage.test getSettings mock were out-of-list edits, judged ok by the reviewer.
  - Default preset was not in the plan; set live by the user (Default, PUT /settings) after the first message hit no_preset.
  - Task live-reply-proof added by scope audit gap G1.
- Tech debt:
  - Byte-copied shared S3 backup credentials (agents-helmfile): per-service credentials would remove it; same practice as webhook and schedule.
  - Default preset lives only in live connector settings, not in helmfile values: declare it in the release values so a redeploy cannot drop it.
  - Synapse reached over in-cluster http and sha7 image pin (agents-helmfile): accepted LOWs; a NetworkPolicy and digest pins would remove them.
  - Core epic agents-matrix-connector close stayed gated on the Harbor secrets for szymonrychu/agents-matrix-connector.
- Workflow:
  - recurring (agents-matrix-connector): a new repo's Harbor secrets are a user step no skill lists, blocking CI and now the deploy for hours. Change: component-add emits a required-repo-secrets checklist and the plan records it as a user step before any epic depending on the image is dispatched.
  - recurring (agents-schedule-microservice, agents-schedule-deploy, agents-matrix-connector): flat seeds with minutes and tokens far off (minutes MdAPE 75.0% here, 166.7%, 61.5%, 83.3% before; tokens 96.9% here, 40.5%, 31.6%, 70.8%); live apply/smoke tasks ran 3-5x on minutes (26 vs 5 here, 19 vs 5 and 13 vs 5 in schedule-deploy). Change: planning should seed live apply and smoke tasks at 15-25 min and UI/doc tasks lower, calibrated from earlier epics' actuals.
  - Deploy plans should include a "first real message" acceptance: apply is not done until a message reaches an agent and gets a reply (default preset, routing). Change: add to the deploy-epic template in start-development a usability acceptance criterion; single occurrence, not recurring.
  - Subagent live exec (kubectl exec) is denied by the permission classifier: plan live-proof tasks as orchestrator-run steps or pre-approve them; single occurrence, not recurring.
