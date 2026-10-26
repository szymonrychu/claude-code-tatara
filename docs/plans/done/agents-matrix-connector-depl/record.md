# agents matrix connector deploy record

## Asked

Deploy the new agents-matrix-connector (Matrix bot bridging Facebook Messenger via mautrix-meta to agents-orchestrator sessions, own CNPG database) into namespace `agents` through agents-helmfile, and add a Chats page to agents-web (rooms, users, allow/deny rules, default preset, recent messages). Revision R1 (user 2026-10-25): the connector takes over Hermes' Matrix user and Facebook account; only the Hermes home-channel owner DM is allowed. Once deployed, send the user a joke message.

## Shipped

11 of 11 planned tasks done. agents-helmfile: connector and connector-db releases, secrets bootstrap, smoke checks, orchestrator re-pin to ab37f1e, agents-web pin 122a404 (2d65d0a..8bce546, 8 commits). agents-web: typed matrix API client, Chats rooms page, access panels, menu entry (d81b219..162770e, 5 commits).
PRs: https://github.com/szymonrychu/agents-helmfile/pull/26 (merged d23e917), https://github.com/szymonrychu/agents-web/pull/12 (merged 122a404; deploy CI run 40276462101 passed).
Deploy: APPLY OK; post-apply `mise run diff` clean (exit 0), `mise run smoke` OK (api and bot Available, sync healthy as the bot user, rules round trip, /rooms 200, config.json lists backend matrix); allow rule 3 for the owner DM; joke sent once (event $01CfkFLBQBwuEVAhq9pIa2utcAVE81xQ7uir1bCT0tE). Live reply proven (G1): inbound in-2 handled in session mx-1, reply out-1 sent, run 1 handled.
Epic review verdict: pass (2026-10-26). Suites: helmfile 184 passed, web 396 passed.

## Tasks

Review rounds are fix rounds from the orchestrator notes. Every verified head appears in the epic git log. No task lacks a verified head. Files and notes agree; the orchestrator notes record no verification tail for helmfile-web-chats-entry beyond the suite line.

| Task | Status | Verified head | Review rounds | Verification tail |
|---|---|---|---|---|
| helmfile-matrix-secrets | done | f09b2a4 | 0 | full suite 169 passed |
| web-matrix-api-client | done | e679002 | 0 | web suite 383 passed |
| helmfile-matrix-releases | done | 20589c3 | 1 (impl: db backup secrets) | full suite 174 passed |
| web-chats-rooms-page | done | 5fd77da | 1 (listRules failure swallowed) | suite 390 passed |
| smoke-matrix-check | done | b0b7a61 | 0 | suite 182 passed |
| orchestrator-repin-ab37f1e | done | 2a8376b | 0 | no tail recorded (unknown) |
| web-chats-access-panels | done | 716ac9b | 0 | suite 395 passed |
| web-chats-menu-entry | done | 162770e | 0 | suite 396 passed |
| helmfile-web-chats-entry | done | 72b381e | 0 | suite 184 passed |
| apply-smoke-matrix | done | 8bce546 | 0 | `mise run diff` exit 0, `mise run smoke` exit 0, "smoke: OK" |
| live-reply-proof | done | 8bce546 | 0 | `mise run diff` task verify; live proof in g1-proof.md (AC1, AC2 met) |

## Rulings

- helmfile-matrix-releases: byte-copied the encrypted agents-webhook-db/default.secrets.yaml for the connector db backup secrets (out-of-list file allowed). Why: precedent, schedule-db and orchestrator-db are identical copies. Cost if wrong: shared backup credentials across dbs; rotating means re-encrypting each copy.
- web-chats-rooms-page: PresetSelect emptyLabel change outside the file list judged ok. Cost if wrong: a shared component behaves differently for other forms; revert one prop.
- web-chats-access-panels: ChatsPage.test getSettings mock addition judged ok. Cost if wrong: a test mock masks a real call; low.
- helmfile-matrix-secrets: sentinels added to sandbox tests judged ok by the reviewer. Cost if wrong: test-only noise.
- Security review of agents-helmfile (2d65d0a..72b381e): 2 LOW findings dropped. (1) sha7 image pin: repo-wide convention. (2) plain http to synapse: in-cluster only, same as Hermes, NetworkPolicy out of scope. Cost if wrong: a mutable-tag collision risk or cleartext traffic inside the cluster.
- apply-smoke-matrix: the `kubectl exec` into the bot pod to send the joke was refused by the permission classifier; the user approved and the orchestrator sent it once. Cost if wrong: one unwanted message to the owner DM.
- Post-deploy: first user reply was ignored (no_preset, default_preset_id null). User chose the "Default" preset; set by PUT /settings (200). Cost if wrong: replies run under the wrong preset; changeable in the Chats page.
- Scope audit gap G1 (live reply unproven) placed as task live-reply-proof; closed.

## Discovered and blocked

- Read receipts are not sent by the connector (not in design). Not blocked; needs a new epic in agents-matrix-connector, the user decides.
- Core epic agents-matrix-connector close needs HARBOR_USERNAME/HARBOR_PASSWORD secrets on szymonrychu/agents-matrix-connector (gh secret list empty 2026-10-26). The user (repo admin) clears it.
- Transient gpg/sops "Cannot allocate memory" on regcred.pre.secrets.yaml in the first post-apply `mise run diff` (rc=1); the re-run was clean. No owner needed; watch for recurrence.

## Not pushed

agents-helmfile main and agents-web main: nothing unpushed (`git log origin/main..main` empty); both PRs merged and branches exist on origin.
Workbench root main: 31 commits ahead of origin/main, including f57bb02 (submodule pointers d23e917, 122a404) and the ticket commits of this epic. The user pushes.

## Lessons routed to

- Apply requests must state that the services Secret changed so the orchestrator api restarts (notes, 7b): add a check in the apply-smoke task template or a smoke assertion that the orchestrator pods are on the new checksum (mechanical).
- The first live message was ignored because default_preset_id was null: add a smoke check (scripts/smoke.sh) failing when the connector /settings has no default preset (mechanical).
- Subagent `kubectl exec` is denied by the classifier: edit the start-development apply-smoke guidance so the main session or an approved step performs live sends (judgement call).
- Missing db backup secrets surfaced only in implementation: add a test in agents-helmfile asserting every db release has a backup secrets file (mechanical).
