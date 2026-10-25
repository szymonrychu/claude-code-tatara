---
title: release v0.1.0
status: todo
repo: agents-schedule
value: "a fixed, immutable chart and image of agents-schedule exist for the deployment to pin"
files: [README.md, MEMORY.md]
verify: "git ls-remote --exit-code --tags origin v0.1.0 && uv run ruff check ."
depends_on: [kind-e2e-api, dockerfile-and-ci, chart-ingress-and-test-hook, api-docs-and-openapi, service-entrypoints]
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

- Part `agents-schedule-release`: chart `0.1.0`, image `<sha7>` of tag v0.1.0; consumed by `deploy-schedule`.

## Expected outcome

Chart 0.1.0 and its image are published and recorded.

## Steps

- Confirm main CI is green on the merged commit (`gh run list -R szymonrychu/agents-schedule -b main -L 1`).
- `git tag v0.1.0 <merged sha> && git push origin v0.1.0`; wait for `chart-publish-tag` to succeed.
- AC2 and AC3 commands exit 0; write README ## Releases and the MEMORY entry.

## Notes

- Irreversible: published chart versions are immutable and the tag is public (listed at the gate).
- The release sha is filled with `ticket.py amend` once the merge lands, as the precedent deploy-pin tasks do.
