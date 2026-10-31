---
title: agents-helmfile
repos: [agents-helmfile]
created: 2026-10-22
owner: Szymon Richert
rung: 1
---

# agents-helmfile

## What and why

What: agents-helmfile, a new component (public szymonrychu/agents-helmfile): a minimal helmfile repo that manages namespace agents and installs the agent-orchestrator chart.
How: helmfile.yaml.gotmpl with a CNPG database release and the orchestrator release, SOPS secrets, copied .env, local mise tasks, pytest over rendered templates and a smoke script.
Why: The user wants the orchestrator running on the cluster, LAN-only at agents.szymonrichert.pl, with every new session starting with any-mcp.

agents-helmfile: a new public component (code/agents-helmfile, origin szymonrychu/agents-helmfile), a minimal helmfile-style repo that manages the Kubernetes namespace `agents`: a CNPG Postgres (agent-orchestrator-db) and the agent-orchestrator Helm chart, exposed only to 192.168.1.0/24 without authentication at https://agents.szymonrichert.pl. SOPS-encrypted secrets (Claude OAuth token, orchestrator master key), a copied .env, local mise tasks lint/test/diff/apply, repo tests and a smoke script that proves the UI answers and that a new session starts with any-mcp preinstalled. Apply is done by the orchestrator after the PR merges.

## Scope ladder

### Rung 1: agreed scope (migrated)

- 1.1: Namespace agents with regcred, a CNPG database release with S3 backups and the agent-orchestrator release from oci://harbor.szymonrichert.pl/charts.
- 1.2: LAN-only ingress (nginx, letsencrypt-prod, whitelist-source-range 192.168.1.0/24, 3600 s read timeout), no auth.
- 1.3: SOPS-encrypted secrets; no plaintext secret ever committed or printed.
- 1.4: Local mise tasks lint, test, diff, apply, smoke; .env copied and gitignored.
- 1.5: Repo tests over rendered templates and a smoke script proving any-mcp is listed by a fresh agent pod.

## Agreed scope

Rung 1, migrated from the epic format: the epic's goals were its agreed scope.

## Non-goals

- No CI-driven apply (local mise tasks only).
- No authentication and no public exposure beyond the whitelist.
- No other namespaces, buckets or releases from the infrastructure helmfile.
- No chart, image or orchestrator code (agent-orchestrator epic).

## Design

Migrated from the epic format; the design sections without a plan.md heading are under Migrated notes.

## Decisions

### D1: Separate flat helmfile repo with local mise tasks (A1)

One `helmfile.yaml.gotmpl`, the infrastructure `*default` template (values layering, hook) and `.hook.sh` trimmed to what one namespace needs; no buckets. Alternatives: a new bucket in the infrastructure helmfile (rejected: user decision Q7; infrastructure applies through CI), or plain `helm install` (rejected: loses SOPS values layering and the regcred hook). `mise run diff|apply` load `.env`; apply depends on lint and test.

### D2: CNPG database with the existing S3 backup settings (A2)

`cnpg/cluster` 0.9.0, `force: false`, one instance, database and owner `agent_orchestrator`. The orchestrator reads CNPG's generated `agent-orchestrator-db-app` Secret, so no password is declared. Backups copy the only enabled-backup config in the infrastructure helmfile (jellystat-database: bucket `database-backup-szymonrychu`, daily, 30d), with its own `path`. (my call) The ai-bucket databases have backups disabled, so jellystat's settings are the template.

### D3: LAN-only ingress without auth (A3)

nginx, `letsencrypt-prod`, `whitelist-source-range: 192.168.1.0/24`, read/send timeouts 3600 s, TLS secret `agent-orchestrator-tls`, no auth annotation; `ORCH_ALLOWED_CIDRS=192.168.1.0/24` enforces the same inside the app. external-dns publishes the Cloudflare record (user decision; ingress-nginx sees real LAN IPs, so the whitelist keeps outside clients out).

### D4: SOPS-encrypted secrets from a bootstrap script (A4)

`scripts/bootstrap-secrets.sh` creates `values/agent-orchestrator/default.secrets.yaml` (`claudeOauthToken`, `masterKey`) and `values/agent-orchestrator-db/default.secrets.yaml` (S3 keys) once, never overwriting. The token is read from the existing Kubernetes secret that has key `CLAUDE_CODE_OAUTH_TOKEN` in namespace `tatara`, falling back to `magic-trainer`, found by key name listing. Values go process to process only. Hygiene tests (`git ls-files` based) fail on any plaintext secret or tracked `.env`.

### D5: any-mcp in every new session, proved by a smoke script (A5)

The orchestrator renders the any-mcp onStart install per cluster (user decision Q8); this repo supplies the settings that enable it and the pinned any-mcp tag. `scripts/smoke.sh` checks the UI, creates a 1-replica cluster through the API, waits for the pod, requires `any-mcp` in `kubectl exec ... -- claude mcp list`, and always discards the cluster. Tested offline with a fake API and fake kubectl; run for real after the apply.

## Open questions

none

## Research

| Lens | Ran | Adopted | Rejected |
|---|---|---|---|
| infrastructure brief (brief-infra.md) | ran | LAN ingress precedent argo-workflows/common.yaml:137-152; regcred hook `.hook.sh`; cnpg 0.9.0 shape buzz-database | CI apply, buckets |
| external web | skipped (homelab conventions, no external API) | none | none |

### Research inputs

| Source | Entry | Lands in |
|---|---|---|
| brief-infra.md section 2 | IP-restricted ingress annotations, regcred hook, SOPS layering | helmfile-base, orchestrator-release |
| brief-infra.md section 5 | per-app CNPG Postgres | db-release |
| brief-infra.md section 4 | images pulled through Harbor need regcred | helmfile-base |
| brief-infra.md Unknowns | backup bucket for new PVC databases | db-release (copied config) |

## Irreversible operations

- Creating the public GitHub repo szymonrychu/agents-helmfile (approved at the gate, step 5.1), done by the orchestrator.
- `mise run apply` against the live cluster after the PR merges: creates namespace `agents`, a CNPG cluster with PVCs, a public Cloudflare DNS record via external-dns and a Let's Encrypt certificate. Done by the orchestrator, not a task; covered by the user's request to install the orchestrator, and preceded by `mise run diff`.
- Reading the Claude OAuth token from namespace tatara/magic-trainer: read-only, value never printed.

## Migrated notes

### README.md: Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.

Verdict: pass (2026-10-23)

Security pass: no critical/high; acted on the kube-context guard (EXPECTED_KUBE_CONTEXT), gitignore for kube/decrypted material, no xtrace in hook scripts, pinned tools; private hostnames/IPs recorded as acceptable for a public homelab repo. helmfile diff against the live cluster: all additions, all in namespace agents, nothing cluster-scoped. Rendered ingress verified: host agents.szymonrichert.pl, letsencrypt-prod TLS, whitelist 192.168.1.0/24, denylist the five node IPs. Scope audit: files deliver A1-A5; apply, DNS and smoke are the deploy phase. Final tip: 44 passed, lint and gitleaks clean, helmfile build 0, pinned tools install.
Rulings: hook missing-namespace AC moved to db-release (planning error); orchestrator-release secrets file regenerated by the orchestrator (classifier denies the write to subagents; token from tatara/tatara-anthropic); stale ACs reconciled with the user's no-.env decision and chart-rendered source ranges.

Verdict: pass (2026-10-23)

Security pass: no critical/high; acted on the kube-context guard (EXPECTED_KUBE_CONTEXT), gitignore for kube/decrypted material, no xtrace in hook scripts, pinned tools; private hostnames/IPs recorded as acceptable for a public homelab repo. helmfile diff against the live cluster: all additions, all in namespace agents, nothing cluster-scoped. Rendered ingress verified: host agents.szymonrichert.pl, letsencrypt-prod TLS, whitelist 192.168.1.0/24, denylist the five node IPs. Scope audit: files deliver A1-A5; apply, DNS and smoke are the deploy phase. Final tip: 44 passed, lint and gitleaks clean, helmfile build 0, pinned tools install.
Rulings: hook missing-namespace AC moved to db-release (planning error); orchestrator-release secrets file regenerated by the orchestrator (classifier denies the write to subagents; token from tatara/tatara-anthropic); stale ACs reconciled with the user's no-.env decision and chart-rendered source ranges.

Verdict: pass (2026-10-23)

Security pass: no critical/high; acted on the kube-context guard (EXPECTED_KUBE_CONTEXT), gitignore for kube/decrypted material, no xtrace in hook scripts, pinned tools; private hostnames/IPs recorded as acceptable for a public homelab repo. helmfile diff against the live cluster: all additions, all in namespace agents, nothing cluster-scoped. Rendered ingress verified: host agents.szymonrichert.pl, letsencrypt-prod TLS, whitelist 192.168.1.0/24, denylist the five node IPs. Scope audit: files deliver A1-A5; apply, DNS and smoke are the deploy phase. Final tip: 44 passed, lint and gitleaks clean, helmfile build 0, pinned tools install.
Rulings: hook missing-namespace AC moved to db-release (planning error); orchestrator-release secrets file regenerated by the orchestrator (classifier denies the write to subagents; token from tatara/tatara-anthropic); stale ACs reconciled with the user's no-.env decision and chart-rendered source ranges.

Verdict: pass (2026-10-23)

Security pass: no critical/high; acted on the kube-context guard (EXPECTED_KUBE_CONTEXT), gitignore for kube/decrypted material, no xtrace in hook scripts, pinned tools; private hostnames/IPs recorded as acceptable for a public homelab repo. helmfile diff against the live cluster: all additions, all in namespace agents, nothing cluster-scoped. Rendered ingress verified: host agents.szymonrichert.pl, letsencrypt-prod TLS, whitelist 192.168.1.0/24, denylist the five node IPs. Scope audit: files deliver A1-A5; apply, DNS and smoke are the deploy phase. Final tip: 44 passed, lint and gitleaks clean, helmfile build 0, pinned tools install.
Rulings: hook missing-namespace AC moved to db-release (planning error); orchestrator-release secrets file regenerated by the orchestrator (classifier denies the write to subagents; token from tatara/tatara-anthropic); stale ACs reconciled with the user's no-.env decision and chart-rendered source ranges.
Deploy: first apply rolled back (orchestrator referenced agent-orchestrator-db-app; CNPG creates agent-orchestrator-db-cluster-app) - fixed with a render-derived test; then LAN 403 from the API allowlist (on flannel the hostNetwork ingress reaches the api from node pod-network gateways 10.244.N.0/.1) - ORCH_ALLOWED_CIDRS set to each node podCIDR .0/31; smoke checked the wrong claude config dir - now checks the session config dir. Final: apply exit 0, all pods Running, LAN GET / and /api/v1/meta 200, mise run smoke OK (any-mcp Connected, 0.1.0, cluster discarded).

### design.md: Summary

A new public component, code/agents-helmfile (origin szymonrychu/agents-helmfile), is a minimal helmfile repo for namespace `agents`. It installs a CNPG Postgres (`agent-orchestrator-db`) and the agent-orchestrator chart from oci://harbor.szymonrichert.pl/charts, exposes the UI only to 192.168.1.0/24 without authentication at https://agents.szymonrichert.pl, keeps its secrets SOPS-encrypted, and is applied from the operator's machine with local mise tasks. A smoke script proves the UI answers and that a freshly created agent pod lists any-mcp.

### design.md: Intent and why

The user wants the orchestrator running on the homelab cluster, reachable from the LAN, with every scheduled session starting with any-mcp. The infrastructure helmfile is a large, CI-applied metarepo; the user wants a small separate repo for this namespace, applied locally.

### design.md: Goals

- Namespace `agents` with regcred, `agent-orchestrator-db` (cnpg/cluster 0.9.0, S3 backups) and `agent-orchestrator` releases.
- LAN-only ingress, no auth, certificate from letsencrypt-prod, SSE-safe timeouts.
- Encrypted Claude OAuth token and master key; tooling mirrored from the infrastructure helmfile (.envrc + .mise.toml); no .env is copied (user decision 2026-10-23).
- Local mise tasks lint, test, diff, apply, smoke.
- Repo tests over the rendered helmfile and a smoke script that checks the UI and `claude mcp list`.

### design.md: Non-goals

- No CI-driven apply, no other buckets or namespaces, no authentication, no chart or image code (owned by agent-orchestrator).

### design.md: Anti-goals

- Any plaintext secret in git, a log or a transcript.
- A release that reaches beyond namespace `agents`.
- An ingress reachable from outside the LAN without the whitelist.

### design.md: Constraints

- Mirror the infrastructure helmfile conventions (`.sops.yaml` PGP key, `.hook.sh` regcred copy, `*default` template, mise tool pins) but only for one namespace.
- Raw sops decrypt to stdout is blocked by the guard hook: secret handling only pipes between processes.
- No `.env` is copied: the infrastructure helmfile has none; its `.envrc`/`.mise.toml` are mirrored (user decision 2026-10-23). `.env` stays gitignored for local overrides.
- The chart, its values and the image tags are owned by the agent-orchestrator epic; this repo consumes them (contracts `agent-orchestrator-chart`, `agent-orchestrator-settings-env`, `agent-orchestrator-image`).

### design.md: Decision coverage

| Decision | Tasks |
|---|---|
| D1 Separate flat helmfile repo with local mise tasks | scaffold-repo, helmfile-base, mise-tasks |
| D2 CNPG database with the existing S3 backup settings | db-release |
| D3 LAN-only ingress without auth | orchestrator-release |
| D4 SOPS-encrypted secrets from a bootstrap script | secrets-bootstrap |
| D5 any-mcp in every new session, proved by a smoke script | orchestrator-release, smoke-script |

### design.md: Contracts

This epic owns no shared part.

### design.md: Cross-epic contracts

Consumed from the agent-orchestrator epic, registered in docs/plans/contracts.json.

| Contract | Owner epic | Consumer epic | Used by tasks | Where defined |
|---|---|---|---|---|
| `agent-orchestrator-chart` | agent-orchestrator | agents-helmfile | orchestrator-release | `code/agent-orchestrator/chart/values.yaml` |
| `agent-orchestrator-settings-env` | agent-orchestrator | agents-helmfile | orchestrator-release | `code/agent-orchestrator/src/agent_orchestrator/settings.py` |
| `agent-orchestrator-image` | agent-orchestrator | agents-helmfile | orchestrator-release | `code/agent-orchestrator/.github/workflows/ci.yaml` |

### design.md: Review focus

- Secret handling in `scripts/bootstrap-secrets.sh` and the hygiene tests.
- The ingress annotations and the whitelist (the only access control).
- That nothing in values is plaintext and `.env` is untracked.

### design.md: Left to the builder

- The exact chart value keys (read from `helm show values` of the published chart).
- The chart and image tags (read from the published chart and the agent-orchestrator CI).
- The smoke script's pod label and API paths (from the agent-orchestrator API contract).

### design.md: Assumptions and unknowns

- The agent-orchestrator epic ships and publishes the chart before orchestrator-release runs (blocker epic); confirmed with `helm show chart`.
- `helmfile build` renders without fetching charts or decrypting secrets; confirmed by the first test run, otherwise tests parse the YAML directly.
- The PGP private key is available on the operator machine (needed by `apply`, as in the infrastructure repo).

### approvals.json

- A1: A separate helmfile-like repo agents-helmfile in claude-code-tatara manages namespace agents, with a copied .env, and is applied by local mise tasks (lint, test, diff, apply). [decisions: D1] [tasks: scaffold-repo, helmfile-base, mise-tasks, hook-missing-namespace, apply-guard-and-hygiene] [status: approved]
- A2: The orchestrator gets a CNPG Postgres (agent-orchestrator-db) in namespace agents with the existing CNPG backup config. [decisions: D2] [tasks: db-release] [status: approved]
- A3: The orchestrator is installed from its helm chart on namespace agents and exposed only to 192.168.1.0/24, with no auth, at agents.szymonrichert.pl. [decisions: D3] [tasks: orchestrator-release, db-secret-name-from-cnpg, api-allowlist-pod-gateways] [status: approved]
- A4: Secrets (the Claude OAuth token copied from the existing secret, a generated master key) are SOPS-encrypted and never printed or committed unencrypted. [decisions: D4] [tasks: secrets-bootstrap] [status: approved]
- A5: Every newly scheduled session starts with any-mcp preinstalled, proven by a smoke script (UI answers on the LAN, a 1-replica cluster yields a ready pod whose claude mcp list shows any-mcp). [decisions: D5] [tasks: orchestrator-release, smoke-script, smoke-session-mcp-check] [status: approved]
