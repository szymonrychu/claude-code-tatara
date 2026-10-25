---
title: apply smoke web cutover
status: in-progress
repo: agents-helmfile
value: "the live UI is served by agents-web behind the same SSO, proven by the smoke"
files: [MEMORY.md]
verify: "mise run diff && mise run smoke"
depends_on: [deploy-pin-web, smoke-web-ui]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# apply smoke web cutover

## Requirement

Apply the agents-web release and the path split to the live `agents` namespace and prove it (design D6, D8; user-approved: releases, pin bumps and the helmfile apply plus smoke are tasks of this epic). Paths are in code/agents-helmfile. The orchestrator still serves its old SPA here; nothing reaches it on `/` any more.

- `mise run diff` first, output quoted in the notes. Expected: the new `agents-web` release (Deployment, Service, ConfigMap, Ingress) and the agent-orchestrator Ingress path `/` to `/api`; anything else stops the task `blocked` with the diff, whoCanClear "user".
- `mise run apply` (it runs lint, test and the kube-context guard; never bypass the guard or set EXPECTED_KUBE_CONTEXT).
- `mise run diff` again: exit 0.
- `mise run smoke`: exit 0, including the web UI, config and routing checks.
- Live checks, quoted in the notes: `curl -s -o /dev/null -w '%{http_code} %{redirect_url}' https://lab.szymonrichert.pl/` and `.../api/v1/meta` both answer a redirect to Keycloak (each path is behind a sidecar); the web and api pods' oauth2-proxy sidecars have the same cookie name, cookie domain and cookie secret source (the `env` of both sidecar containers compared with `kubectl get pod -o json | jq`); `kubectl -n agents get certificate` shows one Ready certificate for `agent-orchestrator-tls`.
- `MEMORY.md`: a dated line: applied agents-web `0.1.0-main.<sha7>` and the `/api` path split, smoke green (quote the smoke's last line).
- A failing apply is not retried blindly: read the helm error and report its tail. Rollback is reverting this epic's helmfile commits and re-applying.

## Acceptance conditions

- AC1: the live namespace has no drift from the pinned helmfile [evidence: command:mise run diff]
- AC2: the smoke passes with the web UI, config and routing checks [evidence: command:mise run smoke]
- AC3: both sidecars share one cookie configuration [evidence: command:for app in agents-web agent-orchestrator; do kubectl -n agents get pod -l app.kubernetes.io/name=$app -o json | jq -c '[.items[0].spec.containers[] | select(.name | test("oauth2")) | .env[] | select(.name | test("COOKIE_(NAME|DOMAINS?|SECRET)")) | {name, v: (.value // .valueFrom)}] | sort_by(.name)'; done | uniq | test "$(wc -l)" -eq 1]
- AC4: MEMORY.md records the applied web release [evidence: command:grep -q "agents-web 0.1.0-main" MEMORY.md]
- AC5: the pre-apply diff showed only the web release and the orchestrator path change, and both public paths redirect to Keycloak [evidence: judgement:the diff and curl output quoted in the task notes]

## Files

- `MEMORY.md`

## Interfaces

- `mise run diff|apply|smoke` in code/agents-helmfile; the live host `lab.szymonrichert.pl`.

## Expected outcome

The live UI is served by agents-web on `/`, the API by the orchestrator on `/api`, behind one SSO session, and the smoke is green.

## Steps

- `mise run diff`: quote it (exit 2 means changes).
- `mise run apply`: exit 0.
- `mise run diff`: exit 0.
- `mise run smoke`: exit 0; quote its last line into MEMORY.md and the notes.
- Run the live checks and AC3.

## Notes

- No TDD cycle applies: this task runs an apply and writes one MEMORY.md line (doc edit exception).
- If the pod label differs from `app.kubernetes.io/name`, use the charts' selector labels in AC3's command and say so in the notes.
