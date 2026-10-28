---
title: webhook release job
status: todo
repo: agents-webhook
value: "agents-webhook images get X.Y.Z, X.Y and X tags that survive Harbor retention, so the webhook deploy stops breaking on pruned sha7 tags"
files: [scripts/next_version.py, tests/test_next_version.py, .github/workflows/ci.yaml, tests/test_ci.py, scripts/chart-version.sh, README.md, MEMORY.md]
verify: "UV_PYTHON=3.12 mise run lint && UV_PYTHON=3.12 mise exec -- uv run pytest tests/test_next_version.py tests/test_ci.py"
depends_on: [orchestrator-release-job]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 940114
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# webhook release job

## Requirement

Epic README Goals (verbatim):

- "Every green push to main in agents-orchestrator, agents-web, agents-webhook, agents-schedule and agents-matrix-connector ends with a release job that needs every other job of the run and computes the next version with a tested in-repo script: BREAKING (`!` or `BREAKING CHANGE` footer) bumps major, `feat` bumps minor, anything else bumps patch, from the last vX.Y.Z tag."
- "The release job pushes git tag vX.Y.Z and image tags X.Y.Z, X.Y and X of the run's sha7 image to harbor.szymonrichert.pl/containers/<repo>, without re-uploading layers."
- "Release jobs never race: one concurrency group per repo, full history and tags fetched."
- "Tests that pin the CI layout are updated to the new layout, and each repo's lint and tests pass."

Decisions given for this epic (verbatim):

- "every green main build computes the next version from conventional commits since the last vX.Y.Z git tag (BREAKING -> major, feat -> minor, else patch), pushes git tag vX.Y.Z and image tags X.Y.Z, X.Y and X at the end of the build; agents-helmfile pins X.Y.Z. BREAKING -> major applies literally, also on 0.x."
- "Script: one stdlib-only Python script, byte-identical in the five repos, tested in each repo's own test runner (pytest in the Python repos; agents-web: its own runner spawning python3, read its package.json); no third-party version action (research: supply-chain risk in a contents: write job)."
- "First release when a repo has no vX.Y.Z tag: exactly 0.1.0, no history scan. agents-schedule already has v0.1.0 and bumps from it. No commits since the last tag, or HEAD already tagged: the release job exits 0 without tagging (idempotent re-runs)."
- "Release job: runs only on push to main, needs every other job of the run (a green build), permissions contents: write, concurrency group per repo with cancel-in-progress false, checkout fetch-depth 0 with tags, retag with `regctl image copy $IMAGE:$SHA7 $IMAGE:<tag>` for X.Y.Z, X.Y, X (manifest only), git tag pushed with the job token. Image push stays as is."
- "Charts unchanged: Harbor keeps chart versions (checked 2026-10-28: 2-11 versions per repo), so main chart-publish stays. The tag-triggered `chart-publish-tag` job and `push: tags: [v*]` trigger are removed where present, because the release job now owns v* tags and a GITHUB_TOKEN tag never triggers it; gate question 1 asks the user to confirm."

design.md decisions D1 to D9 and D11 apply to this repo exactly as written there (D3 version rules, D4 base tag and first release, D5 "the script prints nothing and exits 0 when HEAD is already contained in a vX.Y.Z tag", D6 manifest-only retag, D7 "Git tag pushed last, with the job token", D8 `fetch-depth: 0` and `fetch-tags: true`, D9 chart path, D11 docs and memory).

This task delivers them in agents-webhook. `scripts/next_version.py` and `tests/test_next_version.py` are byte-for-byte copies of agents-orchestrator's (task orchestrator-release-job). The release job needs lint, test, chart, e2e, images, chart-publish. The `push: tags: ["v*"]` trigger, the `chart-publish-tag` job and the `tag` mode of `scripts/chart-version.sh` are removed (D9). a new README `## Release` section documents the release job and MEMORY.md gets the dated entry (D11).

## Acceptance conditions

- ac1: scripts/next_version.py is byte-identical to agents-orchestrator's on the epic branch [evidence: command:git -C /Users/szymonri/Documents/claude-code-tatara/code/agents-orchestrator show semver-image-tags-at-the-end:scripts/next_version.py | cmp - scripts/next_version.py]
- ac2: tests/test_next_version.py is byte-identical to agents-orchestrator's on the epic branch [evidence: command:git -C /Users/szymonri/Documents/claude-code-tatara/code/agents-orchestrator show semver-image-tags-at-the-end:tests/test_next_version.py | cmp - tests/test_next_version.py]
- ac3: Every script case passes in this repo's runner (no tag gives 0.1.0, patch, minor, case-insensitive type, bang and footer major, 0.x major, merge commits counted, highest semver base, HEAD tagged or contained prints nothing, stdlib only) [evidence: command:UV_PYTHON=3.12 mise exec -- uv run pytest tests/test_next_version.py]
- ac4: Run on this repo (no vX.Y.Z tag yet) the real script prints 0.1.0 [evidence: command:python3 scripts/next_version.py]
- ac5: Job `release` has `if` equal to the main-push condition, `needs` equal to every other job of the workflow (lint, test, chart, e2e, images, chart-publish), `permissions` equal to `{contents: write}` and `concurrency` equal to `{group: release, cancel-in-progress: false}` [evidence: command:UV_PYTHON=3.12 mise exec -- uv run pytest tests/test_ci.py::test_release_job_runs_last_on_main_push]
- ac6: The release job's checkout uses `fetch-depth: 0` and `fetch-tags: true` [evidence: command:UV_PYTHON=3.12 mise exec -- uv run pytest tests/test_ci.py::test_release_job_fetches_full_history_and_tags]
- ac7: The version step (id `version`) runs `python3 scripts/next_version.py` into `$GITHUB_OUTPUT`, and every later step has `if: steps.version.outputs.version != ''` [evidence: command:UV_PYTHON=3.12 mise exec -- uv run pytest tests/test_ci.py::test_release_job_computes_version_with_script]
- ac8: Exactly three `regctl image copy "$IMAGE:$SHORTSHA" ...` lines targeting `$VERSION`, `$VERSION_MINOR` and `$VERSION_MAJOR`, env IMAGE harbor.szymonrichert.pl/containers/agents-webhook, regctl-installer pinned to a 40-hex SHA, Harbor login with HARBOR_USERNAME and HARBOR_PASSWORD, and no `docker`, `regctl image import` or `--blob-chunk` in the job [evidence: command:UV_PYTHON=3.12 mise exec -- uv run pytest tests/test_ci.py::test_release_job_retags_manifest_only]
- ac9: The last step runs `git tag "v$VERSION" "$GITHUB_SHA"` then `git push origin "refs/tags/v$VERSION"`, after every copy, with no `--force` or `-f`, and the workflow has no `secrets.GITHUB_TOKEN` [evidence: command:UV_PYTHON=3.12 mise exec -- uv run pytest tests/test_ci.py::test_release_job_pushes_git_tag_last]
- ac10: The workflow has no `push.tags` trigger and no `chart-publish-tag` job [evidence: command:UV_PYTHON=3.12 mise exec -- uv run pytest tests/test_ci.py::test_no_tag_trigger_or_tag_publish_job]
- ac11: `scripts/chart-version.sh` prints `0.1.0-main.abcdef1` for main and exits 2 for `tag v0.1.0` and every other non-main ref [evidence: command:UV_PYTHON=3.12 mise exec -- uv run pytest tests/test_ci.py::test_chart_version_script]
- ac12: Every test of tests/test_ci.py passes against the new layout: jobs list release and not chart-publish-tag, triggers are pull_request and push to main only, the secrets rule allows only main-guarded jobs or steps [evidence: command:UV_PYTHON=3.12 mise exec -- uv run pytest tests/test_ci.py]
- ac13: README `## Release` (new) describes the release job (versions from conventional commits since the last vX.Y.Z tag, first release 0.1.0, image tags X.Y.Z, X.Y and X, git tag vX.Y.Z, pin X.Y.Z) and main chart publishing [evidence: doc-section:README.md#Release]
- ac14: MEMORY.md has a 2026-10-28 entry giving the why of the release job and the retired tag path [evidence: doc-section:MEMORY.md]
- ac15: Lint passes [evidence: command:UV_PYTHON=3.12 mise run lint]

## Files

- `scripts/next_version.py`
- `tests/test_next_version.py`
- `.github/workflows/ci.yaml`
- `tests/test_ci.py`
- `scripts/chart-version.sh`
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

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
