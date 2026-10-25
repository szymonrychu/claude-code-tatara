---
title: apply smoke web cutover
status: todo
repo: agents-helmfile
value: "the live UI is served by agents-web behind the same SSO, proven by the smoke"
files: [MEMORY.md]
verify: "mise run diff && mise run smoke"
depends_on: [deploy-pin-web, smoke-web-ui]
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
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

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
