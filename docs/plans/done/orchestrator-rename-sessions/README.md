---
title: orchestrator-rename-sessions
blockers: [webhook-event-filters]
stage: review
owner: Szymon Richert
repos: [agents-orchestrator, any-mcp, agents-common, agents-webhook, agents-web, agents-helmfile]
created: 2026-10-25
---

# orchestrator rename and sessions

## Project brief

What: Rename agent-orchestrator to agents-orchestrator everywhere (repo, submodule, package, chart, images, release, docs) for consistency, and clean up nomenclature so a cluster is called a session throughout the API, UI and docs, fixing the web UI accordingly.
How: The orchestrator renames the GitHub repo and moves the submodule; then one task chain per repo renames names and vocabulary test-first (nomenclature guard tests, forward DB migrations, any-mcp and agents-common v0.3.0), and the live namespace moves to new releases: old app uninstalled, a new CNPG database imported from the old one, new releases up, smoke green, old database hibernated. Design: design.md.
Why: User request 2026-10-25: 'Agent-orchestrator 1. Rename to agents-orchestrator (consistency) 2. Nomenclature cleanup leading to webUI fixes -> clusters == sessions'

## Description

The orchestrator is the only component not named agents-*, and its unit is called cluster in the API, DB, client, webhook and most of the UI while the UI menu already says Sessions. This epic renames the project and the unit across agents-orchestrator, any-mcp, agents-common, agents-webhook, agents-web and agents-helmfile with no aliases, frees the word session by renaming the wrapper's session id to wrapper_session_id, and moves the live namespace without deleting data. Blocked by webhook-event-filters, which touches the same agents-webhook and agents-web files.

## Goals

- No tracked file in a touched repo names agent-orchestrator outside dated history; repo, submodule, package, chart, image and releases are agents-orchestrator.
- The orchestrator's unit is called session in every API, DB table and column, label, client, service and UI text; Kubernetes, CNPG and kind clusters keep their word; guard tests pin it.
- The web UI says session in every label, title, placeholder, tooltip and empty state.
- The live namespace runs the renamed releases with the presets carried over and a green smoke.
- No live data is deleted: the old database stays hibernated.

## Non-goals

- Deleting the old CNPG cluster, its S3 backups or the old Harbor repositories.
- Renaming ORCH_, orch, X-Orch-*, the agent-<slug> object prefix or the wrapper's own /v1/sessions API.
- Amending agents-schedule-microservice and workspace-s3-cache (orchestrator step O3 after this epic).

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-25)

Epic review of orchestrator-rename-sessions, 2026-10-25.

- Scope audit: CLEAN. No "cluster" meaning the unit is left in any repo (only Kubernetes/CNPG wording, applied migrations, changelogs and retirement guards). The GitHub repo and submodule are renamed, the live releases are renamed, the old DB is hibernated (not deleted), and terraform main has only the agents-orchestrator Keycloak client.
- Security review: no medium-or-higher findings. SSO returns 302 on /api/v1/sessions, /webhooks/api/ and /. ORCH_ALLOWED_CIDRS is 127.0.0.1/32. Service port 8002 is ClusterIP with an exact allowlist. The agent API requires X-Orch-Session. The old DB has no endpoints. The new CNPG uses verify-full TLS and its own S3 path.
  - LOW: the old Secret agent-orchestrator-proxy is pending deletion by the U2 terraform apply (MR !260).
  - LOW, noted and not done now: no NetworkPolicies in the namespace, a shared S3 backup key, enableSuperuserAccess on the new cluster.
- Every task was reviewed alone, with fix rounds where findings came up: the sweep guard missed migration 0005, the bootstrap DB path, the stale smoke any-mcp pin, a MEMORY wording error, and the App.tsx split.
- Full suites (main CI green):
  - agents-orchestrator bba074f: 787 passed locally, e2e 36 passed.
  - agents-webhook 838ba1f, agents-web 5a8d6c8 (335 passed), agents-common v0.3.0, any-mcp v0.3.0.
  - agents-helmfile: 136 passed.
- Live: cutover applied, imported DB with 2 presets and schema 0001-0005, diff "No affected releases", smoke OK.
