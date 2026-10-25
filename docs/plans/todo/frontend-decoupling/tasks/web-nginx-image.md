---
title: web nginx image
status: todo
repo: agents-web
value: "the UI ships as a small non-root static image with the orchestrator's caching rules"
files: [Dockerfile, .dockerignore, nginx/default.conf, scripts/image-smoke.sh, README.md]
verify: "docker build -t agents-web:smoke . && bash scripts/image-smoke.sh agents-web:smoke && shellcheck --severity=error scripts/image-smoke.sh"
depends_on: [web-runtime-config]
model: ""
review: ""
verified_head: ""
points: 1
expected_minutes: 6
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# web nginx image

## Requirement

Ship the UI as a static image served by nginx-unprivileged, with the cache and fallback rules of agent-orchestrator `api/spa.py:SpaStaticFiles` (design D4). Paths are in code/agents-web.

- `Dockerfile`: stage `build` on `node:24-bookworm-slim` runs `npm ci` and `npm run build`; the runtime stage is `nginxinc/nginx-unprivileged` pinned to a version tag (no `latest`), copies `dist/` to `/usr/share/nginx/html` and `nginx/default.conf` to `/etc/nginx/conf.d/default.conf`, listens on 8080 and runs as the image's non-root user. No node in the runtime image.
- `.dockerignore`: `node_modules`, `dist`, `.git`, `chart`.
- `nginx/default.conf`, server on 8080, `server_tokens off`:
  - only GET and HEAD; anything else 405 with `Allow: GET, HEAD`;
  - `/healthz`: 200 `ok`;
  - `/api`, `/api/...`, and `/<segment>/api`, `/<segment>/api/...`: 404 with a JSON body, never `index.html` (another backend's path that reaches this pod is an error, not the SPA);
  - `/assets/...`: the file with `Cache-Control: public, max-age=31536000, immutable`, or 404 when missing (no fallback);
  - `/config.json`: the file with `Cache-Control: no-cache`;
  - `/`, `/index.html` and every other unknown path: `index.html` with `Cache-Control: no-cache`.
- `scripts/image-smoke.sh <image>` (bash, `set -euo pipefail`, trap removes the container, bounded waits): runs the image on a free local port, once with the default `config.json` and once with a mounted override, and checks each rule above, including that `/config.json` lists backend `orchestrator` and that the override is served. Exit 1 naming the failed case.
- `README.md` `## Image`: the serving rules and how to run the smoke.

## Acceptance conditions

- AC1: the image builds and every serving rule holds in the image smoke [evidence: command:docker build -t agents-web:smoke . && bash scripts/image-smoke.sh agents-web:smoke]
- AC2: the smoke script is shellcheck clean [evidence: command:shellcheck --severity=error scripts/image-smoke.sh]
- AC3: the runtime image is non-root and has no node [evidence: command:test "$(docker run --rm --entrypoint id agents-web:smoke -u)" != 0 && ! docker run --rm --entrypoint sh agents-web:smoke -c 'command -v node']
- AC4: the nginx base is pinned to a version tag [evidence: command:grep -Eq '^FROM (docker.io/)?nginxinc/nginx-unprivileged:[0-9]+\.[0-9]+' Dockerfile && ! grep -q ':latest' Dockerfile]
- AC5: the smoke cases cover every case of agent-orchestrator tests/test_spa.py [evidence: judgement:reviewer maps each test_spa.py test to a smoke case]
- AC6: the README documents the image [evidence: doc-section:README.md#Image]

## Files

- `Dockerfile`
- `.dockerignore`
- `nginx/default.conf`
- `scripts/image-smoke.sh`
- `README.md`

## Interfaces

- Owns `web-image`: port 8080, `/healthz`, config file path `/usr/share/nginx/html/config.json`, non-root. Uses `backends-config` (the default `public/config.json`).

## Expected outcome

`docker build` gives a small static image whose behaviour matches what the orchestrator's SPA mount did, plus `/healthz` and `/config.json`.

## Steps

- Red: write `scripts/image-smoke.sh` first; with no Dockerfile `docker build` fails, then with a bare nginx stage the smoke fails on the cache and fallback cases.
- Green: write `nginx/default.conf` and the Dockerfile until the smoke passes.
- `shellcheck --severity=error scripts/image-smoke.sh`: clean.

## Notes

- Reuse: agent-orchestrator `src/agent_orchestrator/api/spa.py:SpaStaticFiles` and `tests/test_spa.py` are the rule set.
- The oauth2-proxy injector renames the container port `http` to its sidecar; probes therefore use the port number 8080 (agents-helmfile `values/agent-orchestrator/common.yaml` comment).
- `readOnlyRootFilesystem` in the chart needs writable `/tmp` (pid and temp paths of nginx-unprivileged); keep every nginx temp path under `/tmp`.
