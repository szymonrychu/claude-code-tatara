---
title: web ci release
status: todo
repo: agents-web
value: every agents-web change is tested in CI and main publishes the image and chart
files: [.github/workflows/ci.yaml, scripts/chart-version.sh, scripts/ci.test.mjs, .mise.toml, README.md]
verify: "npm ci --no-audit --no-fund && node --test scripts/ci.test.mjs && shellcheck --severity=error scripts/*.sh"
depends_on: [web-chart-config-ingress, web-nginx-image, web-openapi-vendor]
owns: []
uses: [web-image, web-chart, openapi-vendor]
model: ""
estimate: 6
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

# web ci release

## Requirement

GitHub Actions CI for agents-web that tests everything and publishes the image and chart to Harbor like agent-orchestrator (design D10). Paths are in code/agents-web.

Precondition, checked first: `gh secret list -R szymonrychu/agents-web` lists `HARBOR_USERNAME` and `HARBOR_PASSWORD` (set by the user, gate question). Otherwise write the workflow and tests anyway, then end `blocked` with whoCanClear "user: gh secret set HARBOR_USERNAME and HARBOR_PASSWORD -R szymonrychu/agents-web".

- `.github/workflows/ci.yaml`, on push to main, tags `v*` and pull requests:
  - `web`: setup-node 24 with npm cache, `npm ci`, `npm run lint`, `npm test`, `npm run build`, `npm run check:api`;
  - `images`: `docker build -t agents-web:ci .`, `bash scripts/image-smoke.sh agents-web:ci`, and on main only the regctl chunked push (50 MB chunks, the Cloudflare 413 limit) to `harbor.szymonrichert.pl/containers/agents-web:<sha7>`;
  - `chart`: mise, `mise run lint:chart`, `mise run test:chart`;
  - `chart-publish` (needs chart and images, main only): version from `scripts/chart-version.sh branch`, refuses an existing version, `helm package --version <v> --app-version <sha7>`, push to `oci://harbor.szymonrichert.pl/charts`;
  - `chart-publish-tag` (tags only): version from `scripts/chart-version.sh tag`, refuses an existing version, requires the image `<sha7>` in Harbor, package and push.
- `scripts/chart-version.sh`: copied from agent-orchestrator with the chart path `chart/agents-web` (`branch <ref> <sha>` gives `<Chart.version>-main.<sha7>` on main; `tag v<X.Y.Z> <sha>` gives `X.Y.Z` and refuses a tag that differs from Chart.yaml).
- `.mise.toml`: tools `node` (kept), `helm` and `shellcheck` pinned; tasks `test:chart` (`npm run test:chart`), `lint:chart` (`npm run lint:chart`), `smoke:image` (`docker build -t agents-web:smoke . && bash scripts/image-smoke.sh agents-web:smoke`); `lint` also runs shellcheck on `scripts/*.sh`.
- `scripts/ci.test.mjs` (node:test, parses the workflow with `yaml`): the triggers, the five jobs and their steps above, pushes only on main or tags, the chunk size, and `chart-version.sh` cases (main, tag, mismatched tag).
- `README.md` `## Release`: what main and a tag publish, and the Harbor secrets the repo needs.

## Acceptance conditions

- AC1: the workflow and the version script behave as required [evidence: command:node --test scripts/ci.test.mjs]
- AC2: the chart tasks and shellcheck run through mise [evidence: command:mise run lint:chart && mise run test:chart && shellcheck --severity=error scripts/*.sh]
- AC3: the repo has the Harbor secrets CI pushes with [evidence: command:test "$(gh secret list -R szymonrychu/agents-web | grep -cE '^HARBOR_(USERNAME|PASSWORD)\b')" = 2]
- AC4: the README documents the release [evidence: doc-section:README.md#Release]

## Files

- `.github/workflows/ci.yaml`
- `scripts/chart-version.sh`
- `scripts/ci.test.mjs`
- `.mise.toml`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
