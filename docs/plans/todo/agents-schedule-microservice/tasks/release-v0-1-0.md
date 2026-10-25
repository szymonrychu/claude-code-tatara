---
title: release v0.1.0
status: todo
repo: agents-schedule
value: "a fixed, immutable chart and image of agents-schedule exist for the deployment to pin"
files: [README.md, MEMORY.md]
verify: "git ls-remote --exit-code --tags origin v0.1.0 && uv run ruff check ."
depends_on: [kind-e2e-api, dockerfile-and-ci, chart-ingress-and-test-hook, api-docs-and-openapi, service-entrypoints]
owns: [agents-schedule-release]
uses: [agents-schedule-image, agents-schedule-chart]
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

# release v0.1.0

## Requirement

Release agents-schedule v0.1.0 (design D14; approval A6). Runs after this epic's agents-schedule branch has merged to main and the main CI run is green. Tag the merged main commit `v0.1.0` and push the tag; CI `chart-publish-tag` publishes chart `0.1.0` and the main `images` job has published `harbor.szymonrichert.pl/containers/agents-schedule:<sha7>` for that commit. README `## Releases` records `v0.1.0` with the image sha7 and chart version; MEMORY.md records the release with the date.

## Acceptance conditions

- AC1: tag v0.1.0 is on origin and points at a commit on main [evidence: command:git fetch origin --tags && git merge-base --is-ancestor v0.1.0 origin/main]
- AC2: chart 0.1.0 is published [evidence: command:helm show chart oci://harbor.szymonrichert.pl/charts/agents-schedule --version 0.1.0]
- AC3: the image for the tagged commit is published [evidence: command:docker manifest inspect harbor.szymonrichert.pl/containers/agents-schedule:$(git rev-parse --short=7 v0.1.0)]
- AC4: README records the release [evidence: doc-section:README.md#Releases]

## Files

- `README.md`
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
