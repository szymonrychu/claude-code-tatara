---
title: orchestrator release
status: done
repo: agents-helmfile
value: "The orchestrator runs in namespace agents and answers at agents.szymonrichert.pl from the LAN only, with new sessions carrying any-mcp."
files: [helmfile.yaml.gotmpl, values/agent-orchestrator/common.yaml, tests/test_orchestrator_release.py]
verify: "uv run pytest tests/test_orchestrator_release.py tests/test_db_release.py -q && mise run lint"
depends_on: [db-release]
model: ""
review: ""
verified_head: fa002cae130bc3a28a8d7d713d91aceb9e12b712
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 10
actual_tokens: 1982025
actual_roles: "impl 5, review 4"
actual_role_tokens: "impl 1245755, review 736270"
---

# orchestrator release

## Requirement

Add release `agent-orchestrator` to `helmfile.yaml.gotmpl`: chart `oci://harbor.szymonrichert.pl/charts/agent-orchestrator`, `version` pinned to the chart version published by the agent-orchestrator epic (read it with `helm show chart oci://harbor.szymonrichert.pl/charts/agent-orchestrator`; an unpublished chart means the blocker epic is not done), namespace `agents`, timeout 600, `needs: [agents/agent-orchestrator-db]`, labels `purpose: agents`, `application: agent-orchestrator`, `<<: *default`. Consume contracts `agent-orchestrator-chart`, `agent-orchestrator-settings-env` and `agent-orchestrator-image`: read the chart's real `values.yaml` (`helm show values`) and map onto its actual key names; where this text names a value, the chart key that carries it is the one to set.

`values/agent-orchestrator/common.yaml`:
- image: `harbor.szymonrichert.pl/containers/agent-orchestrator` at the tag CI published (`<sha7>`, or the chart default when it tracks appVersion); `imagePullSecrets` regcred comes from `values/common.yaml`.
- database: the chart's Postgres connection pointed at the CNPG app Secret `agent-orchestrator-db-app` (key `uri` for `ORCH_DATABASE_URL`, or the host/user/password keys when the chart takes parts); no password in plain values.
- master key and Claude token from the encrypted file made by secrets-bootstrap: `masterKey` into `ORCH_MASTER_KEY` and `claudeOauthToken` into Secret `agent-orchestrator-claude` key `CLAUDE_CODE_OAUTH_TOKEN` in namespace agents (the name the settings default `claude_secret_name` uses). Render them as a chart-supported secret, or when the chart cannot create them, as `values/agent-orchestrator/raw/*.common.pre.secrets.yaml` applied by the hook (encrypted, never decrypted to disk).
- ingress: enabled, `className: nginx`, host `agents.szymonrichert.pl`, annotations `cert-manager.io/cluster-issuer: letsencrypt-prod`, `kubernetes.io/tls-acme: "true"`, `nginx.ingress.kubernetes.io/whitelist-source-range: "192.168.1.0/24"`, `nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"` and `proxy-send-timeout: "3600"` (SSE streams), tls secret `agent-orchestrator-tls`; no auth annotations. external-dns publishes the record by default (user decision: the public Cloudflare record is accepted; access is gated by the whitelist). The orchestrator also enforces `ORCH_ALLOWED_CIDRS` itself.
- RBAC and the service account come from the chart; the release adds none.

`tests/test_orchestrator_release.py` asserts on `helmfile_build()` and `layered_values('agent-orchestrator')`: chart URL, pinned non-empty version, namespace, `needs`, the exact whitelist and timeout annotations, host, TLS, absence of any auth annotation (`auth-url`, `auth-signin`, `oauth2`), the ORCH env values, the DB Secret reference, and that no plain values file holds a token or master key.

## Acceptance conditions

- AC0: the ingress denies the cluster node IPs (chart value ingress.denySourceRanges = [192.168.1.26/32, 192.168.1.27/32, 192.168.1.28/32, 192.168.1.29/32, 192.168.1.65/32], read with `kubectl get nodes -o wide` at build time) and allows 192.168.1.0/24 (ingress.allowSourceRanges), so agent pods SNATed to node IPs cannot reach the API through the ingress [evidence: command:uv run pytest tests/test_orchestrator_release.py -q]
- AC1: the release installs the harbor chart at a pinned version in namespace agents after the database [evidence: command:uv run pytest tests/test_orchestrator_release.py -q -k release_chart_version_and_needs]
- AC2: the ingress is nginx, letsencrypt-prod, host agents.szymonrichert.pl, whitelisted to 192.168.1.0/24 with a 3600s read timeout and no auth annotation [evidence: command:uv run pytest tests/test_orchestrator_release.py -q -k ingress_lan_only_no_auth]
- AC3: ORCH_ALLOWED_CIDRS and ORCH_AGENT_IMAGES are set to the specified values [evidence: command:uv run pytest tests/test_orchestrator_release.py -q -k orch_env_values]
- AC4: the database connection reads the CNPG app Secret and no plain value holds a password [evidence: command:uv run pytest tests/test_orchestrator_release.py -q -k database_from_cnpg_secret]
- AC5: the master key and the Claude token reach the release only through encrypted sources [evidence: command:uv run pytest tests/test_orchestrator_release.py -q -k secrets_only_via_encrypted_files]
- AC6: new sessions are configured to start with any-mcp installed [evidence: command:uv run pytest tests/test_orchestrator_release.py -q -k any_mcp_configured_for_new_sessions]
- AC7: helmfile build succeeds with both releases [evidence: command:mise exec -- helmfile -f helmfile.yaml.gotmpl build >/dev/null]

## Files

- `helmfile.yaml.gotmpl`
- `values/agent-orchestrator/common.yaml`
- `tests/test_orchestrator_release.py`

## Interfaces

Consumes contracts agent-orchestrator-chart, agent-orchestrator-settings-env, agent-orchestrator-image.

## Expected outcome

`helmfile build` lists release agent-orchestrator with the LAN-only ingress, the ORCH env, the DB Secret reference and encrypted secrets only.

## Steps

- Write tests/test_orchestrator_release.py; run it; expect failures.
- Run `helm show chart` and `helm show values` on the published chart (published by agent-orchestrator CI as oci://harbor.szymonrichert.pl/charts/agent-orchestrator version 0.1.0-main.ccb7c04 (appVersion ccb7c04, confirmed in Harbor); try anonymous first, else `helm registry login` with the Harbor robot credentials supplied by the orchestrator, never printed), then add the release and values/agent-orchestrator/common.yaml (and raw/ secrets manifests when the chart cannot create the Secrets).
- Rerun both release tests and `mise run lint`; expect `passed`.

## Notes

Orchestrator ruling 2026-10-23: the source-range annotations are rendered by the chart from ingress.allowSourceRanges / ingress.denySourceRanges (verified with helmfile template: whitelist-source-range 192.168.1.0/24, denylist-source-range the five node IPs); the values must not set the annotations by hand.

Ingress precedent: ~/Documents/infrastructure/code/helmfile helmfiles/coding/values/argo-workflows/common.yaml:137-152. The settings contract names the exact ORCH_* variables; the image tags come from the agent-orchestrator CI. Pin versions and tags, never `latest`.

- 2026-10-23 run agents-helmfile: dependency-failed on db-release
