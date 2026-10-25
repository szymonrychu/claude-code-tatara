# orchestrator rename and sessions record

## Asked

Rename agent-orchestrator to agents-orchestrator everywhere (repo, submodule, package, chart, images, release, docs) and call the unit a session instead of a cluster throughout the API, DB, client, webhook and UI, with no aliases. Free the word session by renaming the wrapper's session id to wrapper_session_id. Move the live namespace to the renamed releases without deleting data (old CNPG database hibernated). User request 2026-10-25: 'Agent-orchestrator 1. Rename to agents-orchestrator (consistency) 2. Nomenclature cleanup leading to webUI fixes -> clusters == sessions'.

## Shipped

All 24 tasks done. Epic review verdict: pass (2026-10-25); scope audit CLEAN (no unit-meaning "cluster" left outside Kubernetes/CNPG/kind wording, applied migrations 0001-0004, changelogs and retirement guards; no duplicates). Security review: no medium-or-higher findings; LOW: old Secret agent-orchestrator-proxy pending deletion by terraform MR !260; LOW, noted and not done: no NetworkPolicies in the namespace, a shared S3 backup key, enableSuperuserAccess on the new CNPG cluster.

Merged:
- agents-orchestrator PR #17 (bba074f).
- any-mcp PR #3 (fa03c36), tag v0.3.0.
- agents-common PR #3 (6dd79c8), tag v0.3.0.
- agents-webhook PR #7 (838ba1f).
- agents-web PR #9 (5a8d6c8).
- agents-helmfile PR #23 (f07eb98).
- terraform (gitlab.com/szymonrychu/terraform) MR !259 (U1, Keycloak client agents-orchestrator) and !260 (U2, old client and key removed).

Live (agents namespace): agents-orchestrator, agents-webhook 0.1.0-main.838ba1f, agents-web 0.1.0-main.5a8d6c8, agents-orchestrator-db imported from the old database (2 presets, schema_migrations 0001-0005). Old agent-orchestrator release uninstalled; old agent-orchestrator-db annotated cnpg.io/hibernation=on and kept. Post-apply diffs: "No affected releases" (.logs/rename-postdiff.log, .logs/rename-postdiff2.log, .logs/rename-hibernate-postdiff.log). Smoke: first run FAILED ("any-mcp --version is not 0.2.0: any-mcp 0.3.0", .logs/rename-smoke.log), then "smoke: OK" after the pin fix (.logs/rename-smoke2.log) and again after hibernation (.logs/rename-hibernate-smoke.log).

Suites read from the review: agents-orchestrator bba074f 787 passed locally, e2e 36 passed; agents-web 5a8d6c8 335 passed; agents-helmfile 136 passed; agents-webhook, agents-common and any-mcp main CI green. I ran no tests myself.

## Tasks

Status, repo, verified head and points (planned/actual) are from the task files (all `done`, all with a verified head). The plan-execute return value was not provided, so the independent verifier head, red evidence, declined, cannotVerify and forwardMerged entries could not be read, and review rounds and verification tails are "unknown"; the head shown is the task file's verified_head. The README review section says every task was reviewed alone, with fix rounds on: the sweep guard missing migration 0005, the bootstrap DB path, the stale smoke any-mcp pin, a MEMORY wording error, and the App.tsx split.

| Task | Repo | Status | Verified head | Points | Rounds | Verification tail |
|---|---|---|---|---|---|---|
| anymcp-plugin-session | any-mcp | done | 5cd9044 | 2/2 | unknown | unknown |
| anymcp-release-v0-3-0 | any-mcp | done | 53b7a66 | 1/1 | unknown | unknown |
| common-client-sessions | agents-common | done | a7b12ed | 3/3 | unknown | unknown |
| common-release-v0-3-0 | agents-common | done | 931b1de | 1/1 | unknown | unknown |
| deploy-cutover | agents-helmfile | done | bfc675b | 3/3 | unknown | unknown |
| helmfile-consumers-rename | agents-helmfile | done | 4fbd057 | 3/3 | unknown | unknown |
| helmfile-orch-db-import | agents-helmfile | done | c1f72b5 | 3/3 | unknown | unknown |
| helmfile-orch-release-rename | agents-helmfile | done | 6361a57 | 5/5 | unknown | unknown |
| helmfile-smoke-sessions | agents-helmfile | done | acd8432 | 3/3 | unknown | unknown |
| hibernate-old-orch-db | agents-helmfile | done | 0f96c62 | 2/2 | unknown | unknown |
| orch-agent-api-sessions | agents-orchestrator | done | 4811b4a | 3/3 | unknown | unknown |
| orch-chart-ci-rename | agents-orchestrator | done | b6e79b8 | 3/3 | unknown | unknown |
| orch-docs-e2e-sessions | agents-orchestrator | done | c27b228 | 3/3 | unknown | unknown |
| orch-package-rename | agents-orchestrator | done | 8ec5071 | 3/3 | unknown | unknown |
| orch-sessions-sweep | agents-orchestrator | done | 0079f7c | 8/8 | unknown | unknown |
| orch-wrapper-session-id | agents-orchestrator | done | 59d20d6 | 3/3 | unknown | unknown |
| web-api-layer-sessions | agents-web | done | c4b7edb | 5/5 | unknown | unknown |
| web-docs-names | agents-web | done | aac9e39 | 2/2 | unknown | unknown |
| web-sessions-pages | agents-web | done | c891770 | 3/3 | unknown | unknown |
| web-webhooks-session-fields | agents-web | done | 811f1b7 | 2/2 | unknown | unknown |
| web-workspace-sessions | agents-web | done | 020ff1a | 5/5 | unknown | unknown |
| webhook-docs-sessions | agents-webhook | done | 8e579ba | 2/2 | unknown | unknown |
| webhook-session-columns | agents-webhook | done | 7c630a9 | 3/3 | unknown | unknown |
| webhook-worker-sessions | agents-webhook | done | 58b0a18 | 2/2 | unknown | unknown |

Approvals ledger: the epic dir has no approvals.json, so no ledger rows. The gate approval is in root MEMORY.md (2026-10-25, user: 'Go'; Q1-Q7 yes: rename DB tables and columns, new CNPG cluster by import, hibernate old DB, Keycloak client and proxy Secret via terraform, keep ORCH_ prefix, webhook-event-filters lands first, wrapper_session_id). Irreversible ops listed at the gate were approved: repo rename, any-mcp and agents-common v0.3.0 tags, helm uninstall of agent-orchestrator, live migrations, deleting the orphan agent-orchestrator-tls, live applies. Per-entry status: unknown.

## Rulings

- O1/O2: the GitHub repo was renamed (`gh repo rename`, verified: `gh repo view szymonrychu/agents-orchestrator`) and the superrepo submodule moved to code/agents-orchestrator with `.gitmodules` section and url updated, then `mise run init:refresh` (root MEMORY.md: components now list agents-orchestrator). Cost if wrong: both reversible by renaming back; the old repo URL redirects.
- Overlap check: ticket.py's in-progress file-overlap check was repo-agnostic (pyproject.toml, uv.lock, openapi.json, AGENTS.md collided across repos), so this epic and agents-matrix-connector could not run together. Ruled: the matrix claim was reverted (822b976, nothing had run), the rename ran first, and the overlap check was fixed to be repo-aware (ticket-overlap-repo-aware, 316e340). The user then split agents-matrix-connector and agents-schedule-microservice each into a core epic and a deploy epic (blocker orchestrator-rename-sessions); scope unchanged, only grouping. Cost if wrong: a repo-aware check could miss a real cross-repo collision; the per-repo split is regrouping only.
- App.tsx move between web tasks: src/App.tsx and src/App.test.tsx compile only together with useClusters and TopBar, so their renames and guard moved from web-sessions-pages to web-workspace-sessions (both tasks amended). Cost if wrong: a compile break between the two tasks; the end state is unchanged.
- webhook scaled to 0 during the cutover: webhook migration 0005 renames events.cluster_id/cluster_slug while old pods run the old SQL under RollingUpdate, so the orchestrator scaled agents-webhook (ingest, api, worker) to 0 before the new build was applied (option used, recorded in deploy-cutover notes). Queued rows wait, nothing lost. Cost if wrong: webhook ingest is down for the apply window and deliveries wait (retry by the sender).
- Migration 0005 guard history: webhook 0004 belongs to webhook-event-filters (merged first), so the rename is 0005 in agents-webhook and in agents-orchestrator (0004 wrapper_session_id, 0005 sessions). The orch-sessions-sweep guard first missed migration 0005 and was fixed in a review round; old migrations 0001-0004 stay allowlisted. Cost if wrong: a cluster-named column survives in the DB; the scope audit found none.
- Discard-hook rename accepted as breaking: the unit-named discard surface (agents-common `discard_cluster` becoming `discard_session`, the agents-web discard dialog and the matching agent-side calls) was renamed with no alias, recorded as Breaking in the any-mcp and agents-common v0.3.0 changelogs. I could not read a separate ruling text for a hook by that name: details unknown beyond the changelogs. Cost if wrong: external callers of the old names break; there are none in the workbench repos.
- any-mcp smoke pin fix: the smoke check asserted any-mcp 0.2.0 and failed against the new 0.3.0 image (.logs/rename-smoke.log); the pin was fixed (f1cba73) and smoke passed (.logs/rename-smoke2.log). Cost if wrong: the smoke would fail or pass against the wrong version.
- Bootstrap DB path fix: a review round fixed the bootstrap DB path for the imported agents-orchestrator-db (new CNPG cluster, own S3 path, verify-full TLS per the security review). Exact change: unknown (task notes do not quote it). Cost if wrong: the import bootstrap or backups point at the old cluster's data.
- User standing approval ('You do my steps!', root MEMORY.md 2026-10-25): the orchestrator runs user-run steps itself, including outward ones; U1 (Keycloak client via terraform MR !259) before the cutover and U2 (old key removal via MR !260) after the green smoke were done that way. Steps needing the user's own credentials or a human login are still asked. Cost if wrong: an outward change made without the user present; both MRs were reversible via terraform.
- Classifier block on the first glab merge: the permission classifier blocked the first `glab mr merge`; on the user's request the allow rule Bash(glab mr merge:*) was added to .claude/settings.local.json (gitignored) so the terraform user-step MRs merge without a block. Cost if wrong: glab merges in this clone no longer prompt; the rule is local and gitignored.
- Webhook scale and apply order, release rename and database import followed design D7: old app uninstalled, new CNPG imported from the old one (no live data deleted), new releases applied, old database hibernated last. Cost if wrong: rollback before step 4 was resetting the old release to installed with the previous pins.

## Discovered and blocked

- Pre-apply diff log (.logs/rename-prediff.log) ends "[diff] ERROR task failed" because `mise run diff` exits non-zero when there are changes ("Identified at least one change"); content was as expected.
- Deletion of the old CNPG cluster, its S3 backups and the old Harbor repositories is a non-goal and stays undone: the user clears it when wanted.
- LOW findings not done now: no NetworkPolicies in the namespace, a shared S3 backup key, enableSuperuserAccess on the new cluster. The user decides.
- Old Secret agent-orchestrator-proxy is pending deletion by the terraform U2 apply (MR !260). Review noted it as pending; whether it has since been deleted: unknown.
- Orchestrator step O3 (amending agents-schedule-microservice and workspace-s3-cache tasks) runs after this epic by design D13; not done in this epic.
- Stale local code/agents-web checkout README still says "10 Clusters"; origin/main does not. Pulling the submodule clears it.
- The workbench plugin session was not reachable when the overlap bug was found; it was reported to the user. Status: unknown.
- Not verifiable by the epic reviewer: nothing else open; live apply and smoke are settled by the logs above.

## Not pushed

The superrepo submodule pins (4fbbbd5) and ticket moves are committed on main; main is not pushed; pushing the superrepo main stays with the user. All submodule PRs and tags are merged and pushed; both terraform MRs are merged.

## Lessons routed to

- The sweep guard missed migration 0005: a nomenclature guard test that scans every migration newer than the last applied-in-production one and fails on cluster-named tables, columns, indexes and constraints (added in orch-sessions-sweep).
- The smoke asserted a stale any-mcp version: a lint or test in agents-helmfile that derives the smoke's expected any-mcp version from the ORCH_ANY_MCP_REF pin rather than a literal.
- ticket.py file-overlap was repo-agnostic: a ticket.py unit test for cross-repo same-name files (done in ticket-overlap-repo-aware, 316e340).
- A rename that renames columns under a RollingUpdate can break old pods: a judgement call for the deploy skill and the task template (scale to 0 or Recreate for column renames), not a mechanical check.
- Tasks that compile only together were split across tasks (App.tsx): a judgement call for the planning skill (group files that share a compile unit), not a mechanical check.
- `mise run diff` returns non-zero on expected changes, which logs read as an error: a judgement call for the apply skill note, not a mechanical check.
