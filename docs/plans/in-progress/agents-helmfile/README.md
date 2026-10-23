---
title: agents-helmfile
blockers: [agent-orchestrator]
stage: build
owner: Szymon Richert
repos: [agents-helmfile]
created: 2026-10-22
---

# agents-helmfile

## Project brief

What: agents-helmfile, a new component (public szymonrychu/agents-helmfile): a minimal helmfile repo that manages namespace agents and installs the agent-orchestrator chart.
How: helmfile.yaml.gotmpl with a CNPG database release and the orchestrator release, SOPS secrets, copied .env, local mise tasks, pytest over rendered templates and a smoke script.
Why: The user wants the orchestrator running on the cluster, LAN-only at agents.szymonrichert.pl, with every new session starting with any-mcp.

## Description

agents-helmfile: a new public component (code/agents-helmfile, origin szymonrychu/agents-helmfile), a minimal helmfile-style repo that manages the Kubernetes namespace `agents`: a CNPG Postgres (agent-orchestrator-db) and the agent-orchestrator Helm chart, exposed only to 192.168.1.0/24 without authentication at https://agents.szymonrichert.pl. SOPS-encrypted secrets (Claude OAuth token, orchestrator master key), a copied .env, local mise tasks lint/test/diff/apply, repo tests and a smoke script that proves the UI answers and that a new session starts with any-mcp preinstalled. Apply is done by the orchestrator after the PR merges.

## Goals

- Namespace agents with regcred, a CNPG database release with S3 backups and the agent-orchestrator release from oci://harbor.szymonrichert.pl/charts.
- LAN-only ingress (nginx, letsencrypt-prod, whitelist-source-range 192.168.1.0/24, 3600 s read timeout), no auth.
- SOPS-encrypted secrets; no plaintext secret ever committed or printed.
- Local mise tasks lint, test, diff, apply, smoke; .env copied and gitignored.
- Repo tests over rendered templates and a smoke script proving any-mcp is listed by a fresh agent pod.

## Non-goals

- No CI-driven apply (local mise tasks only).
- No authentication and no public exposure beyond the whitelist.
- No other namespaces, buckets or releases from the infrastructure helmfile.
- No chart, image or orchestrator code (agent-orchestrator epic).

## Time

Estimate: 43 agent-min | Critical path: 33 min | Expected wall at P=1.5: 1.1 h (k=2.0) | Actual: 0 min | Remaining estimate: 0 min

## Review

Filled when the epic reaches stage `review`: the verdict, the findings acted on, the findings dropped.
