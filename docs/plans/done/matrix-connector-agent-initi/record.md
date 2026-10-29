# matrix connector agent-initiated and follow-up messages record

## Asked

Agents (session leaders) must reach the user's Matrix (Messenger) chat at any time, not only as the answer to a chat-started turn: initiate a chat, send follow-ups without a user reply in between, reply to a specific message and react with an emoji, list the rooms they may post to and read delivery status. Final gate (2026-10-27): a hard 1:1 binding between a chat room and a session replaces last-speaker routing. Posting is allowed only to policy-allowed rooms bound to the session or flagged agents_may_initiate (off by default); the agent token never leaves the orchestrator. Docs, unit/contract/e2e tests and a live smoke in the owner DM were in scope.

## Shipped

Epic review verdict: pass (2026-10-29). 35 of 35 task files are done, each verified head is an ancestor of its repo's main.

- agents-matrix-connector: PR #3 (merge edfb876, 13 tasks, merge commit so the web openapi pin 23f0424 stays reachable), PR #4 (merge c98c501, outbound limits and pool/binding fixes).
- agents-orchestrator: PR #30 (merge 37edd58, chat relay, chart, contract, tools allow, plugins pin), PR #31 (6b467b7, chat env scoped to the api container), PR #32 (merge a9f936f, trigger-service sessions get no chat tools).
- agents-web: PR #21 (merge 6ea3457, "Agents may start chats" switch).
- any-mcp-tatara-plugins: PR #2 (merge 4506e70, chat tools, release 0.2.0), tag v0.2.0 on 4506e70.
- agents-helmfile: PRs #39 (c223998), #41 (f4be334), #42 (260bdc2, cct2's test fix for the 0.3.3 agent image pin), #44 (0d10dce), #45 (f94d143), #46 (6ee8826), #47 (52b6893, chat-smoke MEMORY entry). #40 (0.3.3 pin) was another session's and is not part of the epic.
- Deployed (all smokes OK): connector c98c501, orchestrator a9f936f, web 6ea3457, agent image 0.3.3, plugins ref v0.2.0, from helmfile main 52b6893 (last functional pin 6ee8826). Sequence: orchestrator 37edd58 ~19:33Z 2026-10-28; connector edfb876 21:25Z; orchestrator 37edd58 with chat FAILED (migrate init crash-loop), helm rolled back to the previous revision, healthy; orchestrator 6b467b7 OK; web 6ea3457 OK; connector c98c501 ~01:20Z 2026-10-29 alone; orchestrator a9f936f time unknown (not in the notes). Evidence: /workdir/workdir/.logs/matrix-deploy-2026-10-28/.
- Live smoke (chat-smoke, owner DM): rc=0, caller bound mx-34 (before and after), hours since last inbound 2, S1-S4 accepted then sent. User (via mx-34 msg 325, 2026-10-29 02:34Z and 02:36Z): "Lovely" (smile emoji), "all recommended, go". S1-S3 display acceptably; reply and react are kept, send is kept, no removal tasks. S4 (replaced or not shown) is unverified: the user gave no detail.

## Tasks

Status is `done` for all 35. All verified heads are non-empty and found in the epic's git log (main of the repo). Review rounds are `unknown` where the orchestrator notes do not record them; the notes give only CI run ids and minutes for most tasks. Tails are from the task Notes unless marked.

| Task | Repo | Status | Verified head | Review rounds | Verification tail |
|---|---|---|---|---|---|
| mxc-sends-schema | agents-matrix-connector | done | bb794ed | unknown | CI 40732610268 green (DB tests CI-only) |
| mxc-room-initiate-flag | agents-matrix-connector | done | 23f0424 | unknown | CI 40734264708 green |
| mxc-agent-room-policy | agents-matrix-connector | done | fc70272 | unknown | unknown |
| mxc-agent-listener | agents-matrix-connector | done | 221c793 | unknown | unknown |
| mxc-agent-routes | agents-matrix-connector | done | 0380120 | unknown | CI 40740444262 green |
| mxc-matrix-send-event | agents-matrix-connector | done | 1153021 | unknown | unknown |
| mxc-bot-sends-delivery | agents-matrix-connector | done | 18963f2 | 1 fix round (fix1: dropped unused matrix param) | CI 40744168950 green |
| mxc-room-session-binding | agents-matrix-connector | done | 9c031d0 | unknown | CI 40746644847 green |
| mxc-skip-duplicate-final | agents-matrix-connector | done | f9d4899 | unknown | CI 40747755877 green |
| mxc-prompt-message-refs | agents-matrix-connector | done | 4568022 | unknown | CI 40748215902 green |
| mxc-chart-agent-port | agents-matrix-connector | done | cc19c54 | unknown | CI 40749340758 green |
| mxc-api-blank-text | agents-matrix-connector | done | ed9c0f7 | unknown | CI 40750406829 green |
| mxc-e2e-agent-sends | agents-matrix-connector | done | 40810bd | unknown | CI 40751882452 green, 345 passed |
| mxc-outbound-limits | agents-matrix-connector | done | 5c8583d | unknown (impl 11 min, review 1 min) | unknown; PR #4 merge and main CI run by a sonnet agent, result not in the notes |
| mxc-pool-and-binding | agents-matrix-connector | done | aaa9aa4 | unknown (impl 7 min, review 2 min) | unknown; PR #4 as above |
| orch-chat-relay | agents-orchestrator | done | 62e1908 | unknown | CI 40732285270 test/lint/chart green; e2e pending at review |
| orch-plugins-pin-0-3-0 (pins 0.2.0) | agents-orchestrator | done | af167e8 | unknown | unknown |
| orch-chart-chat | agents-orchestrator | done | 2ff2888 | unknown | unknown; ac1 (test_chat_url_in_configmap) superseded by orch-chat-env-scope, intended |
| orch-chat-contract | agents-orchestrator | done | 9d5419c | unknown | unknown |
| orch-chat-tools-allow | agents-orchestrator | done | 1be7f31 | unknown | CI 40742034508 test/lint/chart green; e2e pending at review |
| orch-chat-env-scope | agents-orchestrator | done | df39983 | unknown (impl 38 min, review 2 min) | main CI 40779692636 green incl. chart-publish (PR #31, from the review notes) |
| orch-chat-untrusted-sessions | agents-orchestrator | done | b21a292 | unknown (impl 55 min, review 2 min) | unknown; PR #32 |
| plugin-chat-tools | any-mcp-tatara-plugins | done | 670e021 | unknown | CI 40734865565 and 40734905366 green; local test_source_install failure is the pod's git version |
| plugins-release-0-3-0 (releases 0.2.0) | any-mcp-tatara-plugins | done | 073328e | unknown | PR #2 merged 4506e70, main CI 40736029763 green, tag v0.2.0 pushed |
| web-room-initiate-toggle | agents-web | done | 431f8d2 | unknown | CI 40735421358 pending at review; web main CI 40752648038 success (review notes) |
| helmfile-chat-secrets | agents-helmfile | done | 4c7ef2a | unknown | unknown; no CI in the repo, local verify only |
| helmfile-orch-chat-pin | agents-helmfile | done | 6998c2b | unknown | check-pins ok 9 pins; ac1 superseded by helmfile-orch-chat-fix-pin |
| helmfile-chat-values | agents-helmfile | done | ab48151 | unknown | unknown; no CI in the repo |
| helmfile-web-toggle-pin | agents-helmfile | done | c1825b7 | unknown (review 1 min) | unknown |
| chat-smoke-script | agents-helmfile | done | 0804582 | unknown | unknown |
| helmfile-orch-chat-fix-pin | agents-helmfile | done | 1f0ca4b | unknown (impl 6 min, review 2 min) | unknown; PR #44 |
| helmfile-smoke-helpers | agents-helmfile | done | 9233d08 | unknown (impl 20 min, review 8 min) | unknown; PR #45 |
| helmfile-connector-fix-pin | agents-helmfile | done | 051affd | unknown (impl 2 min, review 1 min) | unknown |
| helmfile-orch-untrusted-pin | agents-helmfile | done | 5f0956b | unknown (impl 2 min, review 1 min) | unknown |
| chat-live-smoke | agents-helmfile | done | fd1a382 | unknown | ac1-ac6: Harbor tags 200, `mise run diff` rc=0, `mise run smoke` "smoke: OK", only the owner DM has agents_may_initiate true, binding mx-34 before and after, chat-smoke rc=0; ac7 user confirmed (S4 unverified); ac8 PR #47 fd1a382 merged 52b6893 |

Where notes and files differ: the notes' "Done 24/27" and "34/35" were mid-run counts; the files show 35 of 35 done. chat-live-smoke has verified_head fd1a382, a docs-only MEMORY.md commit (ac8); its points_actual of 1 is the reviewer's score of that doc step only, against 8 estimated. For 26 tasks the files carry no actual minutes or tokens ("no agent records"), so the RETRO totals cover 9 of 35 tasks.

## Rulings

- What: mxc-sends-schema backfill takes the binding slug from the session's first run (NULL if pruned), never a follow run; Q12 (backfill) answered yes. Why: recommended answer; a follow run's slug is not the session's origin. Cost if wrong: the owner DM is bound to a stale or wrong session until the 60 s binding sweep releases it.
- What: web openapi/matrix.source pins connector epic-branch commit 23f0424, and connector PR #3 merges with a merge commit, not a squash. Why: connector main lacked the flag until the merge and the pinned sha had to stay reachable. Cost if wrong: unreachable sha, `npm run check:api` fails in web. (Review: content equals connector main edfb876, checked by JSON equality.)
- What: helmfile PR #41 (chat secrets) held unmerged until helmfile-chat-values set chat.url on the same branch. Why: the orchestrator release does not render with a token and no url. Cost if wrong: a pinned main that cannot render or apply the orchestrator.
- What: tasks in different repos ran in parallel lanes, one task at a time within a repo. Why: separate trees, no shared writes. Cost if wrong: merge conflicts across lanes (none recorded).
- What: failed orchestrator apply (37edd58 with chat) was rolled back by helm and fixed by two new tasks (orch-chat-env-scope, helmfile-orch-chat-fix-pin) instead of retrying; chat-live-smoke was made to depend on the pin. Why: ORCH_CHAT_URL sat in the shared ConfigMap, the token only in the api env, so the migrate init crashed on the Settings pair check. Cost if wrong: the orchestrator stays without chat; busy pods were kept, so no session loss.
- What: phase 5 judgement (judgement.md). Acted on, as fix tasks, without asking: security M2 plus slug-length and m<n> probing LOWs (mxc-outbound-limits); connector Consider 1 (nested pool acquisition) and 2 (failed initiating send releases the binding) (mxc-pool-and-binding); security M1 (chat tools granted to every session) plus the orchestrator Consider on the e2e literal allow list (orch-chat-untrusted-sessions, new created_by_service migration); web-helmfile Act on (stale_pids stderr noise) plus the scope-audit duplicate sweep (helmfile-smoke-helpers).
- What: dropped as not-this-task: the reviewer's medium that Sender._claim holds a connection while RoomPolicy.refusal takes more (sender.py:88-106,150-165). Why: pre-existing, bounded by the single sequential bot loop, no cycle. Cost if wrong: pool starvation if sender concurrency is ever added.
- What: noted, not fixed: security LOW NetworkPolicy on port 8001 (cluster-level; 256-bit token, api container only); LOW plugin pinned by tag v0.2.0 (pre-existing pattern; tag = 4506e70 = uv.lock); connector Consider 3 (PREAMBLE missed after a failed first prompt, not a regression); orchestrator Noted items (upstream 401 passthrough, env override can recreate the crash, stale wording, query forwarding); web MEMORY.md entry (Consider). Cost if wrong: any pod can attempt the connector agent port (token is the only barrier); a moved tag would change code in agent pods; the untrusted-input framing could be missed for one session after a failed first prompt.
- What: scope audit accepted two superseded ACs: helmfile-orch-chat-pin ac1 (by helmfile-orch-chat-fix-pin) and orch-chart-chat ac1 (by orch-chat-env-scope). Why: intended replacement of a wrong design. Cost if wrong: none, tests exist under the new names.
- What: Q7 (user, via mx-34 msg 325): reply and react kept, send kept, no removal tasks, even though S4 is unverified. Why: the user said "all recommended, go" after S1-S3 displayed acceptably. Cost if wrong: if S4 is in fact broken, an agent-chat case goes unnoticed until the user reports it.
- What: user-approved deletion of the 10 smoke sessions named smoke-*-1793219392 and smoke-*-1793237575 only (msg 325). Cost if wrong: none beyond those sessions.
- What: noted, not doing now: orchestrator `claude.existingSecretKey` is unused (k8s/render.py:236 hardcodes CLAUDE_CODE_OAUTH_TOKEN).

## Discovered and blocked

- S4 not verified: the user did not say what Messenger showed for S4. Cleared by the user, in Messenger via mx-34. Not blocking; reply/react were kept on the user's go.
- Orchestrator `claude.existingSecretKey` unused (k8s/render.py:236). Not scheduled; the orchestrator owner or the user must put it in an epic.
- No NetworkPolicy on connector port 8001 (and none in the orchestrator chart). Cleared by a cluster operator or a later chart epic; the report is based on the repos only.
- Live room flags and cluster RBAC were not checked by the security review. Cleared by the operator in the web UI (only the owner DM has agents_may_initiate true as of the smoke).
- agents-helmfile has no CI; its tests need network (helmfile build, Harbor chart pull) and some need the SOPS key. Clearing needs a CI workflow, owned by the helmfile maintainer.
- Agent pods have no Docker and no helm version: DB tests and chart tests were CI-only evidence. Cleared by CI only.
- helmfile main went red after another session's PR #40 (agent image 0.3.3, merged 19:37Z, not applied); fixed by PR #42. Who applied 0.3.3 was asked of mx-34 (msg 253); the handoff records 0.3.3 as deployed.
- cct2 leader agent-cct2-1 is wedged by the stale-Stop bug (wrapper 0.3.2, DB says busy since 18:51Z, 9 messages queued); read-only finding sent to mx-34 (msg 309). mx-34 decides; nothing was changed. Not part of this epic.
- Web UI: the switch is enabled for rooms the user cannot allow (infrastructure, encrypted, denied) and a bound room shows no "bound to session" hint. Noted by the review and the task; the web owner decides.
- chat-smoke prints `/proc/<pid>/cmdline: No such file or directory` noise: fixed in helmfile-smoke-helpers.

## Not pushed

Checked against the local `origin/*` refs (no fetch, no network). In the five component repos (agents-matrix-connector, agents-orchestrator, agents-web, any-mcp-tatara-plugins, agents-helmfile) `git log origin/main..main` is empty: main is pushed. The remote branches matrix-connector-agent-initi still exist on origin for the connector and the plugins; local epic branches are gone. Superrepo (claude-code-tatara) main has one unpushed commit, 65bcbb64 (chore(ticket): matrix-connector-agent-initi retro); this record file is written but not committed. The supervisor pushes superrepo main as an approved fast-forward after rebasing on origin (msgs 214/249), over HTTP/1.1.

## Lessons routed to

- Chart env that one container needs was rendered into the shared ConfigMap and crashed the migrate init at the first live apply; the original test (test_chat_url_in_configmap) pinned the wrong design. Check to add: an orchestrator chart test that renders the chat values and feeds each container's env to the real Settings class (done in part by test_configmap_has_no_chat_url; add the init-container Settings case) plus a CI step in agents-helmfile that runs `helmfile template -l name=agents-orchestrator` with a token and a url. The test needs Harbor access, so a pod-local run is not enough; route to a helmfile CI workflow.
- A new agent tool went to every session, including webhook and schedule sessions reading attacker text (security M1). Check to add: a test in tests/test_on_start.py that enumerates tool grants per session origin and fails when a trusted-only tool is granted to a trigger session (added with created_by_service). The design-time question "which session origins get this tool" is a judgement call: add it to the Review focus of the design template in start-development.
- Outbound flooding of a real person's account had only a count-then-insert limit. Check to add: a connector test that fires parallel sends and asserts the cap (added in mxc-outbound-limits); a checklist item for any feature that messages a human, owned by the design template (judgement call).
- Nested pool acquisition inside a request. Check to add: a test with pool max_size below the number of concurrent requests (added: "concurrent agent requests on a full pool"); apply the same fixture to the other DB-backed routes.
- An agent-call helper was copied into two shell scripts. Check to add: an agents-helmfile test that fails when `agent_call` or `agent_py` is defined outside scripts/lib/smoke-common.sh.
- Redirection order bug (`< file 2> /dev/null`) let stale-pid noise into the smoke log. Check to add: a test that the stale scan on a vanished pid prints nothing to stderr (added in helmfile-smoke-helpers).
- agents-helmfile main went red from a merge by another session and it has no CI. Check to add: a GitHub workflow running `mise run test` and `mise run lint` on every PR (recurring retro tech debt).
- 26 of 35 tasks closed with no actual minutes or tokens, so the RETRO MdAPE rests on 9 tasks. Check to add: `ticket.py task --status done` warns or refuses when actuals are empty for a task that had agent roles.
- Task files listed fewer files than their commits touched (orch-chat-env-scope) and verified_head was stored as a short sha in one task (chat-live-smoke). Check to add: `ticket.py` compares the task `files` with `git diff --stat` at done and normalises verified_head to the full sha.
- Live tasks ran 3-8x over the minute estimates (orch-chat-env-scope 6.67x, orch-chat-untrusted-sessions 8.14x, helmfile-smoke-helpers 5.60x). Estimation is a judgement call: edit the live-task multiplier in the planning guidance of start-development, not a hook.
- The epic stayed open for hours on one human confirmation (chat-live-smoke ac7). Judgement call: edit start-development so a human-confirmation AC is asked for as soon as the evidence exists and does not block the other close steps.
