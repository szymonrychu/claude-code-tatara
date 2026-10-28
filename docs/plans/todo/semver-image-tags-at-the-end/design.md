# Semver image tags at the end of main builds design

## Summary

Every green push to main in agents-orchestrator, agents-web, agents-webhook, agents-schedule and
agents-matrix-connector ends with a `release` job. It computes the next version with one
stdlib-only Python script (`scripts/next_version.py`, byte-identical in the five repos, tested in
each repo's own runner), retags the run's already-pushed sha7 image as X.Y.Z, X.Y and X with
`regctl image copy` (manifest only) and pushes git tag vX.Y.Z last. The tag-triggered chart path
is retired; main chart publishing stays. agents-helmfile then pins all five components to X.Y.Z
in the phase 6 deploy step.

## Intent and why

Incident 2026-10-28: Harbor retention pruned the sha7 tags pinned in agents-helmfile
(agents-orchestrator 96e46f3, agents-web 01e971c, agents-webhook 838ba1f, agents-schedule
6cfa955, agents-matrix-connector 98b0803); new pods hit ImagePullBackOff. Semver tags survive
retention (claude-code-wrapper keeps 0.2.0..0.3.1 for days). Every deploy of these five
components is exposed until they pin semver tags.

## Goals

- G1: Every green push to main in agents-orchestrator, agents-web, agents-webhook, agents-schedule and agents-matrix-connector ends with a release job that needs every other job of the run and computes the next version with a tested in-repo script: BREAKING (`!` or `BREAKING CHANGE` footer) bumps major, `feat` bumps minor, anything else bumps patch, from the last vX.Y.Z tag.
- G2: The release job pushes git tag vX.Y.Z and image tags X.Y.Z, X.Y and X of the run's sha7 image to harbor.szymonrichert.pl/containers/<repo>, without re-uploading layers.
- G3: Release jobs never race: one concurrency group per repo, full history and tags fetched.
- G4: Tests that pin the CI layout are updated to the new layout, and each repo's lint and tests pass.
- G5: agents-helmfile pins every one of the five components to an X.Y.Z image tag released by this epic, and the agents namespace is applied and healthy with every pod pulling a semver tag.

G1-G4 are covered by the six tasks' acceptance conditions. G5 is verified in the phase 6 deploy
step (section "Deploy step (phase 6)"), because the X.Y.Z tags exist only after each repo's PR
merges and its release job runs (user decision).

## Non-goals

- Changing Harbor's retention policy (no admin access; semver tags already survive it).
- claude-code-wrapper, any-mcp, agents-common, any-mcp-tatara-plugins release flows.
- A shared reusable workflow or shared CI repo; each repo stays independent.
- Changelogs, GitHub Releases, version commits, a `latest` tag.
- Changing how the sha7 image is built or pushed (the `images` job stays as is).
- Chart versioning: charts keep `<Chart.version>-main.<sha7>` from main.

## Anti-goals

- A release job that retags X.Y.Z, X.Y or X onto an older commit than one already released.
- A third-party version or tagging action in a job that holds `contents: write` and Harbor credentials.
- Re-uploading image layers (Cloudflare 100 MB body limit; the import already chunks).
- Five scripts that drift apart.
- A red main in any of the five repos.

## Constraints

- Python stdlib only for the script; it runs on the runner's system `python3` (ubuntu-latest), so py312 syntax; it must pass ruff in the four Python repos (identical config: line-length 100, target py312, select E F I UP B SIM).
- Default workflow token is read-only in all five repos (`gh api .../actions/permissions/workflow`, discovery); tag push needs `permissions: contents: write`. No tag rulesets (`gh api .../rulesets` is `[]`).
- A tag pushed with GITHUB_TOKEN starts no workflow run (research finding 1).
- agents-webhook local env: uv picks a managed Python 3.15 and fails building google-re2. Probe 2026-10-28: `UV_PYTHON=3.12 mise run lint` passed ("All checks passed!", "49 files already formatted") and `UV_PYTHON=3.12 mise exec -- uv run pytest tests/test_ci.py` passed ("12 passed"). Every webhook command in this epic sets `UV_PYTHON=3.12`.
- agents-web local vitest needs `npm ci` (stale node_modules); this epic's web tests run with `node --test`, which needs only the installed `yaml` package (probe: `mise exec -- node --test 'scripts/*.test.mjs'` gave "pass 22 fail 0").
- Workflow behaviour itself is proven only by CI; the PR runs and the first main runs are the authoritative evidence (phase 6).
- House rules: TDD, no backward compatibility, no em dashes.

## Decisions

### D1: A `release` job at the end of every green main build

The decision: each `ci.yaml` gains one job `release` with `if: github.event_name == 'push' && github.ref == 'refs/heads/main'`, `needs` listing every other job of the workflow (agents-orchestrator: lint, test, images, chart, e2e, chart-publish; agents-web: web, images, chart, chart-publish; agents-webhook and agents-schedule: lint, test, chart, e2e, images, chart-publish; agents-matrix-connector: lint, test, chart, images, chart-publish), job-level `permissions: contents: write`, job-level `concurrency: {group: release, cancel-in-progress: false}` (concurrency groups are per repository), `runs-on: ubuntu-latest`. The image push in `images` is unchanged. User decision 2026-10-28.

Alternatives: tagging inside `images` (not green-gated: `images` runs in parallel with the tests); a separate workflow on `workflow_run` (harder to test, a second file); a reusable workflow (non-goal).

Why: `needs` on every job is the only way to make "green build" literal; a job-level permission keeps every other job read-only. With `cancel-in-progress: false`, a running release is never cancelled; a newer pending run replaces an older pending one, and the older commits ship in the newer version (research, concurrency). A failed release job is retried with "Re-run failed jobs", which re-runs only the failed job (a full re-run stops at chart-publish's "already published" refusal).

### D2: One stdlib-only script, byte-identical, tested in each repo's runner

The decision: `scripts/next_version.py`, created in agents-orchestrator and copied byte for byte to the other four repos. Tests: `tests/test_next_version.py` (pytest) in the four Python repos, also byte-identical (my call: identical ruff and pytest configs make that free, and one file to review); agents-web gets `scripts/next_version.test.mjs` (node:test, spawning `python3`) with the same cases and test names. Tests build real temporary git repos with `git` (never mocked git output) and set their own commit identity through `GIT_AUTHOR_*`/`GIT_COMMITTER_*` environment variables, since CI runners have no git identity. Byte identity is an acceptance condition of each copying task (`cmp` against the agents-orchestrator epic branch). User decision; test identity (my call).

Alternatives: paulhatch/semantic-version, svu, git-cliff, cocogitto (research section 1); a bash script.

Why: supply-chain risk of third-party code in a `contents: write` job (CVE-2025-30066); the rule set is tiny and fixed; first-release and 0.x behaviour become tested decisions instead of undocumented tool defaults.

### D3: Version rules

The decision: over every commit in `<base>..HEAD` (no `--first-parent`, so branch commits under "Merge pull request #N" count; research fix-as-ac), each commit's bump is: major when its subject matches `^<type>(<scope>)?!:` or any line of its message starts with `BREAKING CHANGE:` or `BREAKING-CHANGE:`; minor when its subject's type is `feat`; patch otherwise. The release bump is the highest commit bump. Major gives (X+1).0.0, minor X.(Y+1).0, patch X.Y.(Z+1). BREAKING bumps major literally, also on 0.x (v0.3.1 plus `feat!` gives 1.0.0). The type match is case-insensitive and `BREAKING CHANGE` is uppercase only, as the Conventional Commits spec rule 15 says (my call). User decision for the mapping and the 0.x rule.

Alternatives: 0.x prerelease mode (breaking bumps minor on 0.x), rejected by the user; first-parent scan (would miss branch commits behind merge subjects).

Why: matches the user's words and the spec; the merge-graph scan sees the real commit types.

### D4: Base tag and first release

The decision: only tags matching `^v\d+\.\d+\.\d+$` count; the base is the numerically highest such tag reachable from HEAD (`git tag --merged HEAD`). With no such tag, the next version is exactly `0.1.0`, with no history scan. agents-schedule already has v0.1.0 (on 6cfa955) and bumps from it. User decision (my call recorded by the orchestrator).

Alternatives: base 0.0.0 with a full history scan (gives 1.0.0 in agents-orchestrator, agents-web and agents-webhook, whose histories hold `!` commits); seed tags pushed by hand.

Why: predictable first version, no manual step.

### D5: When no release is due

The decision: the script prints nothing and exits 0 when HEAD is already contained in a vX.Y.Z tag (`git tag --contains HEAD`): HEAD itself is tagged (a re-run) or a newer main commit that descends from HEAD was already released. The workflow then skips every later step of `release` and the job succeeds. User decision for "HEAD already tagged / no commits since the last tag"; extending it to "contained in" is my call.

Alternatives: only "HEAD carries a tag".

Why: concurrency serializes release jobs but not their order. If run B (commit b, child of a) releases v0.2.0 before run A's release job starts, A would see v0.1.0 as its base, compute 0.2.0 again and copy a's image over the 0.2.0 tag before its git push failed. "Contained in" makes A skip; a's changes are already in b's release.

### D6: Manifest-only retag with regctl

The decision: steps after the version step, each guarded by `if: steps.version.outputs.version != ''`: the regctl-installer action pinned to `dd58ad94f76adb73d8ac1bf75ed25f01545d5b32` (the pin of the four repos; my call to use it in agents-orchestrator's new job too), `regctl registry login` with `HARBOR_USERNAME`/`HARBOR_PASSWORD` (the images job's login line), then `regctl image copy "$IMAGE:$SHORTSHA" "$IMAGE:$VERSION"`, `... "$IMAGE:$VERSION_MINOR"`, `... "$IMAGE:$VERSION_MAJOR"` with `SHORTSHA="${GITHUB_SHA::7}"`, `VERSION_MINOR="${VERSION%.*}"`, `VERSION_MAJOR="${VERSION%%.*}"`, and job env `IMAGE: harbor.szymonrichert.pl/containers/<repo>`, `HARBOR_URL: harbor.szymonrichert.pl`. No `docker`, no `regctl image import`, no blob-chunk settings in the job. User decision.

Alternatives: `docker pull/tag/push` (claude-code-wrapper's release.yaml; pulls and pushes layers); `regctl manifest put`.

Why: `regctl image copy` within one repository sends only the manifest under the new tag (research section 3), so nothing near the Cloudflare body limit.

### D7: Git tag pushed last, with the job token

The decision: the last step creates a lightweight tag and pushes it: `git tag "v$VERSION" "$GITHUB_SHA"` then `git push origin "refs/tags/v$VERSION"`, never forced. The push uses the token `actions/checkout` persists (default `persist-credentials`), which carries the job's `contents: write`; the workflow never names `secrets.GITHUB_TOKEN` (my call: keeps agents-matrix-connector's pinned secret set `{HARBOR_USERNAME, HARBOR_PASSWORD}` true). Lightweight tag: needs no git identity on the runner (my call). Retag first, git tag last (my call).

Alternatives: git tag first (a failed retag then leaves a tagged HEAD, and a re-run skips under D5, so the image never gets its tags); annotated tags (need a committer identity); tagging through the REST API.

Why: with the git tag last, any failure before it leaves no tag, and a re-run computes the same version and repeats the idempotent copies.

### D8: Full history and tags in the release job

The decision: the release job's checkout is `actions/checkout@v4` with `fetch-depth: 0` and `fetch-tags: true`. User decision.

Alternatives: default depth 1 (no tags, no history: the script cannot find the base).

Why: the script needs every tag and the whole graph between the base and HEAD.

### D9: Charts unchanged; tag-triggered chart path retired

The decision: main `chart-publish` stays as is (Harbor keeps chart versions: 2-11 per repo, checked 2026-10-28). In agents-orchestrator, agents-web, agents-webhook and agents-schedule the `push: tags: ["v*"]` trigger and the `chart-publish-tag` job are removed, and so is the `tag` mode of `scripts/chart-version.sh` (my call: its only caller was that job; with it gone, `tag ...` falls through to "nothing to publish", exit 2). agents-matrix-connector has neither (nothing to remove; its test pins the absence). Gate question Q1 asks the user to confirm. User decision for the job and trigger.

Alternatives: keep the job (never fires: a GITHUB_TOKEN tag starts no run, and its Chart.yaml equality check would refuse CI versions anyway); publish the chart at X.Y.Z in the release job (out of scope: charts unchanged).

Why: the release job now owns the v* namespace; a dead trigger and job would only mislead.

### D10: agents-web script tests run by a runner

The decision: agents-web gets the npm script `"test:scripts": "node --test 'scripts/*.test.mjs'"`; the `web` CI job runs `npm run test:scripts` after `npm test`; `.mise.toml`'s `test` task runs `npm test` then `npm run test:scripts`. This wires the orphaned `scripts/ci.test.mjs` (13 tests, run by nothing today) and `scripts/sync-api.test.mjs`, and later `scripts/next_version.test.mjs`. (my call; probe: the glob gives "pass 22 fail 0" today.)

Alternatives: run them through vitest (its include is `src/**/*.test.{ts,tsx}` and node:test files are not vitest files); append them to `npm test` (`npm test -- <file>` would then pass the file to node, not vitest).

Why: "agents-web: its own runner spawning python3" needs a runner that actually runs; node:test is the one `scripts/ci.test.mjs` and `chart/tests` already use.

### D11: Docs and memory

The decision: each repo's README documents the release job (versions from conventional commits since the last vX.Y.Z tag, first release 0.1.0, image tags X.Y.Z, X.Y and X, git tag vX.Y.Z, pin X.Y.Z): agents-orchestrator `## Releasing`, agents-web `## Release` and agents-schedule `## Releases` are rewritten where they describe the retired tag path (schedule keeps its v0.1.0 line); agents-webhook and agents-matrix-connector get a new `## Release` section. Each repo's MEMORY.md gets one dated entry with the why of D3-D7 and D9. (my call, from the component rules: README accurate, MEMORY.md on every non-obvious decision.)

Alternatives: design.md only.

Why: the next agent in each repo reads its README and MEMORY.md, not this epic.

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| Repos (discovery) | ran, .scratchpad/semver-tagging/discovery-repos.md | CI shape per repo, tests pinning the layout, local env notes, the schedule v0.1.0 baseline, the regctl-installer pin (discovery "Cross-repo shape", per-repo sections) | a reusable workflow (discovery "do-not-build") |
| Prior art | ran, .scratchpad/semver-tagging/research-prior-art.md | in-repo script (section 1), `regctl image copy` (section 3, https://regclient.org/cli/regctl/image/copy/), concurrency (https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/control-the-concurrency-of-workflows-and-jobs), `fetch-depth: 0` (https://github.com/actions/checkout) | third-party version actions (CVE-2025-30066, https://www.tenable.com/cve/CVE-2025-30066); docker retag (claude-code-wrapper release.yaml) |
| Harbor retention | ran, research section 4 | X.Y.Z tags keep their artifact (https://goharbor.io/docs/2.13.0/working-with-projects/working-with-images/create-tag-retention-rules/) | changing retention (non-goal, no admin access) |

## Research inputs

Retro proposals first (from `ticket.py retro --history`), then brief findings.

- Recurring workflow (generic-any-mcp-with-git-and, file-editor-with-tabs-and-hi): deploys depend on Harbor holding image tags; "does the pinned image tag survive Harbor pruning". Acted on by every release task (orchestrator-release-job, web-release-job, webhook-release-job, schedule-release-job, matrix-connector-release-job) and the phase 6 deploy step (pins X.Y.Z).
- Recurring workflow (generic-any-mcp-with-git-and, cross-session-messaging-and): test fakes encoded the same wrong assumption as the code; ACs must rest on real tool output. The script tests run real `git` in temporary repos, never mocked output: orchestrator-release-job (and the copies in web-release-job, webhook-release-job, schedule-release-job, matrix-connector-release-job).
- Recurring workflow (leader-auto-handover, paste-env-contents-into-the): `ticket.py new-task` leaves the template's Interfaces, Expected outcome, Steps and Notes; the planner fills them in every task file of this epic (all six tasks).
- Recurring workflow (file-download-in-file-browse, leader-auto-handover): no Docker in agent pods makes DB suites CI-only; task verify here is targeted (named test files plus lint) and each PR's CI run is the full-suite gate (all six tasks; phase 6).
- Recurring workflow (leader-auto-handover, generic-any-mcp-with-git-and): live apply, smoke and release work runs 3-4x over the minutes seed; no live step is a build-loop task here, the helmfile re-pin and apply are the phase 6 deploy step.
- Tech debt (generic-any-mcp-with-git-and): smoke depends on Harbor holding every deployed tag; the deploy step checks each X.Y.Z with `regctl image digest` before the helmfile change (phase 6 deploy step).
- Tech debt (leader-auto-handover): agents-helmfile has no CI workflow, so its change rests on local `mise run lint` and `mise run test` in the deploy step (phase 6; noted, not doing now: a helmfile CI workflow).
- `images` is not green-gated; only a job that needs every job is (discovery fix-as-ac): every release task.
- Default token read-only; tag push needs `contents: write` (discovery Unknowns, resolved): every release task.
- No concurrency group anywhere (discovery fix-as-ac): every release task.
- agents-web `scripts/ci.test.mjs` runs under no runner (discovery fix-as-ac): web-script-tests-wired.
- agents-web "exactly the five jobs" and agents-orchestrator "exactly one regctl image import" pin the layout (discovery fix-as-ac): web-release-job, orchestrator-release-job.
- agents-matrix-connector pins its secret set to the two Harbor secrets (discovery fix-as-ac): matrix-connector-release-job (D7 keeps it true).
- `chart-version.sh tag` refuses any tag that is not Chart.yaml's version, and a GITHUB_TOKEN tag never triggers `chart-publish-tag` (discovery and research): orchestrator-release-job, web-release-job, webhook-release-job, schedule-release-job (D9).
- Scan without `--first-parent`; match `!` and both footer spellings; unit cases no tag, patch-only, feat, `feat!`, footer, merge commit, 0.x breaking (research fix-as-ac): orchestrator-release-job.
- An older queued run could compute an already released version (research "Contradictions": concurrency keeps one pending run): D5, orchestrator-release-job.
- Noted, not doing now: agents-orchestrator's existing `regctl-installer@main` uses in `images` and `chart-publish`.

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 A release job at the end of every green main build | orchestrator-release-job, web-release-job, webhook-release-job, schedule-release-job, matrix-connector-release-job |
| D2 One stdlib-only script, byte-identical, tested in each repo's runner | orchestrator-release-job, web-release-job, webhook-release-job, schedule-release-job, matrix-connector-release-job |
| D3 Version rules | orchestrator-release-job, web-release-job, webhook-release-job, schedule-release-job, matrix-connector-release-job |
| D4 Base tag and first release | orchestrator-release-job, web-release-job, webhook-release-job, schedule-release-job, matrix-connector-release-job |
| D5 When no release is due | orchestrator-release-job, web-release-job, webhook-release-job, schedule-release-job, matrix-connector-release-job |
| D6 Manifest-only retag with regctl | orchestrator-release-job, web-release-job, webhook-release-job, schedule-release-job, matrix-connector-release-job |
| D7 Git tag pushed last, with the job token | orchestrator-release-job, web-release-job, webhook-release-job, schedule-release-job, matrix-connector-release-job |
| D8 Full history and tags in the release job | orchestrator-release-job, web-release-job, webhook-release-job, schedule-release-job, matrix-connector-release-job |
| D9 Charts unchanged; tag-triggered chart path retired | orchestrator-release-job, web-release-job, webhook-release-job, schedule-release-job, matrix-connector-release-job |
| D10 agents-web script tests run by a runner | web-script-tests-wired, web-release-job |
| D11 Docs and memory | orchestrator-release-job, web-release-job, webhook-release-job, schedule-release-job, matrix-connector-release-job |

## Review focus

- `scripts/next_version.py`: the D5 "contained in" skip, the strict tag regex, numeric (not lexical) ordering, the merge-graph scan, and that the tests really exercise each rule against a real git repo (a test that passes against a stub script asserts nothing).
- Byte identity of `scripts/next_version.py` across all five repos and of `tests/test_next_version.py` across the four Python repos; the epic review reruns the `cmp` loop after any fix round in agents-orchestrator.
- The release job's `needs` really lists every other job, and every step after the version step carries the skip guard.
- Git tag strictly after the three copies; no `--force`; no `secrets.GITHUB_TOKEN`.
- Each test edited or removed is one that the new layout made inaccurate, and the task names it.

## Left to the builder

- Internal structure of `scripts/next_version.py` (functions, error messages), within the interface in the agents-orchestrator task.
- Step names in the release job, and whether the version step also prints a "no release due" line.
- Wording of the README and MEMORY.md entries, within D11.

## Assumptions and unknown facts

- The Harbor robot can push a new tag to an existing manifest (`regctl image copy`): same push right as the import; unverified until the first main release job runs (phase 6 checks it).
- `actions/checkout@v4` with `fetch-depth: 0` and the persisted job token can push a tag when the job has `contents: write`: confirmed by the first main release job (phase 6).
- The runner's system `python3` (ubuntu-latest) is 3.12 or newer: confirmed by the first release job; the script avoids syntax newer than py312.

## Open questions
- Q1: The release job now owns v* tags and a GITHUB_TOKEN tag push never triggers a workflow, so the tag-triggered chart-publish-tag job, the push: tags: [v*] trigger and chart-version.sh's tag mode are removed in agents-orchestrator, agents-web, agents-webhook and agents-schedule (main chart-publish stays). Confirm the removal? [recommended: yes, remove them (D9)]

## Deploy step (phase 6)

Not a build-loop task: the versions exist only after each repo's PR merges and its release job runs (user decision).

1. For each of the five repos, after its PR merges: watch its main run to green; the `release` job log shows the computed version; `git ls-remote --tags origin vX.Y.Z` lists the tag; `regctl tag ls harbor.szymonrichert.pl/containers/<repo>` shows X.Y.Z, X.Y and X; `regctl image digest` of `:X.Y.Z` equals that of `:<sha7>`. Commit the moved submodule pointer in the superrepo.
2. agents-helmfile, one PR: pin each component's image tag to its X.Y.Z in `values/<component>/common.yaml` (agents-orchestrator, agents-webhook, agents-schedule, agents-matrix-connector, agents-web); chart versions pin the chart main published for the same release commit (`0.1.0-main.<sha7>`, all five, agents-schedule included, so chart and image always come from one commit). Update the tests that hardcode sha7 pins (`tests/test_orchestrator_release.py`, `tests/test_webhook_release.py`, `tests/test_schedule_release.py`, `tests/test_matrix_connector_release.py`, `tests/test_web_release.py`) to an X.Y.Z regex and the new pins; red first. `mise run lint` and `mise run test` locally (no helmfile CI).
3. Before applying: `regctl image digest` of every pinned X.Y.Z succeeds.
4. `helmfile diff` reviewed, then `mise run apply`; every pod in namespace `agents` is Ready and `kubectl get pods -n agents -o jsonpath='{..image}'` shows only semver tags for the five components (and the wrapper's 0.3.1). This verifies G5.

## Irreversible operations in scope

- Git tags vX.Y.Z pushed by CI to five origins, and image tags X.Y.Z (immutable in intent) in Harbor: covered by the user's decision 2026-10-28 that every green main build releases; D5 and D7 stop duplicate or out-of-order tags; never forced.
- Removing the `chart-publish-tag` job and `v*` trigger: covered by gate question Q1.
- agents-helmfile apply to the live `agents` namespace: phase 6, after the gate, preceded by `helmfile diff` and the image-existence check.
