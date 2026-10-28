---
title: orchestrator release job
status: todo
repo: agents-orchestrator
value: "agents-orchestrator images get X.Y.Z, X.Y and X tags that survive Harbor retention, and the canonical next-version script the other repos copy"
files: [scripts/next_version.py, tests/test_next_version.py, .github/workflows/ci.yaml, tests/test_images.py, tests/test_chart_ci.py, scripts/chart-version.sh, README.md, MEMORY.md]
verify: "mise run lint && mise exec -- uv run pytest tests/test_next_version.py tests/test_images.py tests/test_chart_ci.py tests/test_project_name.py tests/test_frontend_retired.py"
depends_on: []
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 8
expected_tokens: 1819809
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orchestrator release job

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

This task delivers them in agents-orchestrator and creates the canonical `scripts/next_version.py` and `tests/test_next_version.py` that agents-web, agents-webhook, agents-schedule and agents-matrix-connector copy byte for byte. The release job needs `lint`, `test`, `images`, `chart`, `e2e` and `chart-publish`. The `push: tags: ["v*"]` trigger, the `chart-publish-tag` job and the `tag` mode of `scripts/chart-version.sh` are removed (D9); README `## Releasing` is rewritten for the release job and MEMORY.md gets the dated entry (D11).

## Acceptance conditions

- ac1: With no vX.Y.Z tag the script prints exactly 0.1.0 without scanning history, even when the history holds a `feat!` commit [evidence: test:tests/test_next_version.py::test_no_tag_gives_0_1_0]
- ac2: From v1.2.3, only fix, chore, docs and "Merge pull request" commits give 1.2.4 [evidence: test:tests/test_next_version.py::test_fix_chore_docs_bump_patch]
- ac3: From v1.2.3, a fix plus a `feat(scope):` commit give 1.3.0 (highest bump wins) [evidence: test:tests/test_next_version.py::test_feat_bumps_minor]
- ac4: `Feat:` and `FEAT(x):` subjects bump minor (type is case-insensitive) [evidence: test:tests/test_next_version.py::test_feat_type_is_case_insensitive]
- ac5: From v1.2.3, each of `feat!:`, `fix!:` and `refactor(api)!:` gives 2.0.0 [evidence: test:tests/test_next_version.py::test_bang_bumps_major]
- ac6: From v1.2.3, a commit whose body has a `BREAKING CHANGE:` line, and one with a `BREAKING-CHANGE:` line, each give 2.0.0 [evidence: test:tests/test_next_version.py::test_breaking_change_footer_bumps_major]
- ac7: From v0.3.1, a `feat!:` commit gives 1.0.0 (BREAKING bumps major literally on 0.x) [evidence: test:tests/test_next_version.py::test_breaking_on_0x_bumps_major]
- ac8: From v1.0.0, a `--no-ff` merge whose subject is "Merge pull request #1 from x/y" and whose branch holds a `feat:` commit gives 1.1.0 (no first-parent scan) [evidence: test:tests/test_next_version.py::test_merge_commit_branch_commits_counted]
- ac9: With tags v0.9.0, v0.10.0, v1.2, vfoo and v2.0.0-rc1 reachable, the base is v0.10.0 (strict regex, numeric order), so a fix gives 0.10.1 [evidence: test:tests/test_next_version.py::test_highest_semver_tag_is_base]
- ac10: When HEAD carries v1.0.0 the script prints nothing and exits 0 [evidence: test:tests/test_next_version.py::test_head_tagged_prints_nothing]
- ac11: When HEAD is a parent of a commit tagged v1.1.0 (a newer main commit already released) the script prints nothing and exits 0 [evidence: test:tests/test_next_version.py::test_head_contained_in_newer_tag_prints_nothing]
- ac12: Every import of `scripts/next_version.py` is in `sys.stdlib_module_names` [evidence: test:tests/test_next_version.py::test_script_is_stdlib_only]
- ac13: Run on this repo (no vX.Y.Z tag yet) the real script prints 0.1.0 [evidence: command:python3 scripts/next_version.py]
- ac14: Job `release` has `if` equal to the main-push condition, `needs` equal to every other job of the workflow (lint, test, images, chart, e2e, chart-publish), `permissions` equal to `{contents: write}` and `concurrency` equal to `{group: release, cancel-in-progress: false}` [evidence: test:tests/test_images.py::test_release_job_runs_last_on_main_push]
- ac15: The release job's checkout uses `fetch-depth: 0` and `fetch-tags: true` [evidence: test:tests/test_images.py::test_release_job_fetches_full_history_and_tags]
- ac16: The version step (id `version`) runs `python3 scripts/next_version.py` into `$GITHUB_OUTPUT`, and every later step of the job has `if: steps.version.outputs.version != ''` [evidence: test:tests/test_images.py::test_release_job_computes_version_with_script]
- ac17: The job retags with exactly three `regctl image copy "$IMAGE:$SHORTSHA" ...` lines targeting `$VERSION`, `$VERSION_MINOR` and `$VERSION_MAJOR`, its env IMAGE is harbor.szymonrichert.pl/containers/agents-orchestrator, its regctl-installer is pinned to a 40-hex SHA, it logs in with HARBOR_USERNAME and HARBOR_PASSWORD, and it has no `docker`, `regctl image import` or `--blob-chunk` [evidence: test:tests/test_images.py::test_release_job_retags_manifest_only]
- ac18: The last step runs `git tag "v$VERSION" "$GITHUB_SHA"` then `git push origin "refs/tags/v$VERSION"`, after every `regctl image copy` step, with no `--force` or `-f`, and the workflow text has no `secrets.GITHUB_TOKEN` [evidence: test:tests/test_images.py::test_release_job_pushes_git_tag_last]
- ac19: The workflow has no `push.tags` trigger and no `chart-publish-tag` job; `scripts/chart-version.sh tag v<Chart version> <sha>` exits 2 [evidence: test:tests/test_chart_ci.py::test_no_tag_trigger_or_tag_publish_job]
- ac20: `scripts/chart-version.sh` still prints `<version>-main.<sha7>` for main and exits 2 for any other ref, tag refs included [evidence: test:tests/test_chart_ci.py::test_chart_version_scheme]
- ac21: README `## Releasing` describes the release job (versions from conventional commits since the last vX.Y.Z tag, first release 0.1.0, image tags X.Y.Z, X.Y and X, git tag vX.Y.Z, pin X.Y.Z), no longer describes a tag-triggered chart publish, and still names `-main.`, oci://harbor.szymonrichert.pl/charts and Chart.yaml [evidence: test:tests/test_chart_ci.py::test_readme_documents_releasing]
- ac22: MEMORY.md has a 2026-10-28 entry giving the why of the version rules, the first release 0.1.0, the "contained in" skip, retag-then-tag order and the retired tag path [evidence: doc-section:MEMORY.md]
- ac23: Lint passes [evidence: command:mise run lint]

## Files

- `scripts/next_version.py`
- `tests/test_next_version.py`
- `.github/workflows/ci.yaml`
- `tests/test_images.py`
- `tests/test_chart_ci.py`
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
