---
title: matrix connector release job
status: todo
repo: agents-matrix-connector
value: "agents-matrix-connector images get X.Y.Z, X.Y and X tags that survive Harbor retention, so the connector deploy stops breaking on pruned sha7 tags"
files: [scripts/next_version.py, tests/test_next_version.py, .github/workflows/ci.yaml, tests/test_ci.py, README.md, MEMORY.md]
verify: "mise run lint && mise exec -- uv run pytest tests/test_next_version.py tests/test_ci.py"
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

# matrix connector release job

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

This task delivers them in agents-matrix-connector. `scripts/next_version.py` and `tests/test_next_version.py` are byte-for-byte copies of agents-orchestrator's (task orchestrator-release-job). The release job needs lint, test, chart, images, chart-publish. This repo has no `v*` trigger, no `chart-publish-tag` job and no chart-version.sh tag mode; the test pins that absence (D9). A new README `## Release` section documents the release job and MEMORY.md gets the dated entry (D11).

## Acceptance conditions

- ac1: scripts/next_version.py is byte-identical to agents-orchestrator's on the epic branch [evidence: command:git -C /Users/szymonri/Documents/claude-code-tatara/code/agents-orchestrator show semver-image-tags-at-the-end:scripts/next_version.py | cmp - scripts/next_version.py]
- ac2: tests/test_next_version.py is byte-identical to agents-orchestrator's on the epic branch [evidence: command:git -C /Users/szymonri/Documents/claude-code-tatara/code/agents-orchestrator show semver-image-tags-at-the-end:tests/test_next_version.py | cmp - tests/test_next_version.py]
- ac3: Every script case passes in this repo's runner (no tag gives 0.1.0, patch, minor, case-insensitive type, bang and footer major, 0.x major, merge commits counted, highest semver base, HEAD tagged or contained prints nothing, stdlib only) [evidence: command:mise exec -- uv run pytest tests/test_next_version.py]
- ac4: Run on this repo (no vX.Y.Z tag yet) the real script prints 0.1.0 [evidence: command:python3 scripts/next_version.py]
- ac5: Job `release` has `if` equal to the main-push condition, `needs` equal to every other job of the workflow (lint, test, chart, images, chart-publish), `permissions` equal to `{contents: write}` and `concurrency` equal to `{group: release, cancel-in-progress: false}` [evidence: test:tests/test_ci.py::test_release_job_runs_last_on_main_push]
- ac6: The release job's checkout uses `fetch-depth: 0` and `fetch-tags: true` [evidence: test:tests/test_ci.py::test_release_job_fetches_full_history_and_tags]
- ac7: The version step (id `version`) runs `python3 scripts/next_version.py` into `$GITHUB_OUTPUT`, and every later step has `if: steps.version.outputs.version != ''` [evidence: test:tests/test_ci.py::test_release_job_computes_version_with_script]
- ac8: Exactly three `regctl image copy "$IMAGE:$SHORTSHA" ...` lines targeting `$VERSION`, `$VERSION_MINOR` and `$VERSION_MAJOR`, env IMAGE harbor.szymonrichert.pl/containers/agents-matrix-connector, regctl-installer pinned to a 40-hex SHA, Harbor login with HARBOR_USERNAME and HARBOR_PASSWORD, and no `docker`, `regctl image import` or `--blob-chunk` in the job [evidence: test:tests/test_ci.py::test_release_job_retags_manifest_only]
- ac9: The last step runs `git tag "v$VERSION" "$GITHUB_SHA"` then `git push origin "refs/tags/v$VERSION"`, after every copy, with no `--force` or `-f`, and the workflow has no `secrets.GITHUB_TOKEN` [evidence: test:tests/test_ci.py::test_release_job_pushes_git_tag_last]
- ac10: The workflow has no `push.tags` trigger and no `chart-publish-tag` job [evidence: test:tests/test_ci.py::test_no_tag_trigger_or_tag_publish_job]
- ac11: Every test of tests/test_ci.py passes, the pinned secret set `{HARBOR_USERNAME, HARBOR_PASSWORD}` included (the release job names no other secret) [evidence: command:mise exec -- uv run pytest tests/test_ci.py]
- ac12: README `## Release` (new) describes the release job (versions from conventional commits since the last vX.Y.Z tag, first release 0.1.0, image tags X.Y.Z, X.Y and X, git tag vX.Y.Z, pin X.Y.Z) and main chart publishing [evidence: doc-section:README.md#Release]
- ac13: MEMORY.md has a 2026-10-28 entry giving the why of the release job [evidence: doc-section:MEMORY.md]
- ac14: Lint passes [evidence: command:mise run lint]

## Files

- `scripts/next_version.py`
- `tests/test_next_version.py`
- `.github/workflows/ci.yaml`
- `tests/test_ci.py`
- `README.md`
- `MEMORY.md`

## Interfaces

`scripts/next_version.py` (design D2-D5), the contract every repo's copy keeps:

- Run as `python3 scripts/next_version.py` with the repo's work tree as the current directory; Python stdlib only (`subprocess` to `git`), py312 syntax.
- Tags that count: names matching `^v\d+\.\d+\.\d+$` only.
- If any counting tag contains HEAD (`git tag --contains HEAD`): print nothing, exit 0 (HEAD tagged, or a newer main commit already released).
- Else base = the numerically highest counting tag reachable from HEAD (`git tag --merged HEAD`); none: print `0.1.0`, exit 0, no history scan.
- Else scan every commit of `<base>..HEAD` (no `--first-parent`); per commit: major if the subject matches `^[A-Za-z]+(\([^)]*\))?!:` or a line of the message starts with `BREAKING CHANGE:` or `BREAKING-CHANGE:`; minor if the subject's type is `feat` (case-insensitive, optional `(scope)`); else patch. Highest bump wins; major `(X+1).0.0`, minor `X.(Y+1).0`, patch `X.Y.(Z+1)`, also on 0.x. Print `X.Y.Z` plus newline, exit 0.
- A git failure exits non-zero with the git error on stderr.

`release` job in `.github/workflows/ci.yaml` (design D1, D6-D8), shape (step names free, everything else as written):

```yaml
  release:
    needs: [<every other job of this workflow>]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions:
      contents: write
    concurrency:
      group: release
      cancel-in-progress: false
    env:
      HARBOR_URL: harbor.szymonrichert.pl
      IMAGE: harbor.szymonrichert.pl/containers/<repo>
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          fetch-tags: true
      - name: Compute version
        id: version
        run: echo "version=$(python3 scripts/next_version.py)" >> "$GITHUB_OUTPUT"
      - uses: regclient/actions/regctl-installer@dd58ad94f76adb73d8ac1bf75ed25f01545d5b32 # main as of 2026-10-25
        if: steps.version.outputs.version != ''
      - name: Login to Harbor
        if: steps.version.outputs.version != ''
        env:
          HARBOR_USERNAME: ${{ secrets.HARBOR_USERNAME }}
          HARBOR_PASSWORD: ${{ secrets.HARBOR_PASSWORD }}
        run: echo "$HARBOR_PASSWORD" | regctl registry login "$HARBOR_URL" -u "$HARBOR_USERNAME" --pass-stdin
      - name: Tag image
        if: steps.version.outputs.version != ''
        env:
          VERSION: ${{ steps.version.outputs.version }}
        run: |
          SHORTSHA="${GITHUB_SHA::7}"
          VERSION_MINOR="${VERSION%.*}"
          VERSION_MAJOR="${VERSION%%.*}"
          regctl image copy "$IMAGE:$SHORTSHA" "$IMAGE:$VERSION"
          regctl image copy "$IMAGE:$SHORTSHA" "$IMAGE:$VERSION_MINOR"
          regctl image copy "$IMAGE:$SHORTSHA" "$IMAGE:$VERSION_MAJOR"
      - name: Push git tag
        if: steps.version.outputs.version != ''
        env:
          VERSION: ${{ steps.version.outputs.version }}
        run: |
          git tag "v$VERSION" "$GITHUB_SHA"
          git push origin "refs/tags/v$VERSION"
```

No `docker`, `regctl image import`, `--blob-chunk` or `--force` in the job; the workflow never names `secrets.GITHUB_TOKEN`.

Test names, the same in all five repos (Python functions in the four Python repos, node:test names in agents-web):

- Script: `test_no_tag_gives_0_1_0`, `test_fix_chore_docs_bump_patch`, `test_feat_bumps_minor`, `test_feat_type_is_case_insensitive`, `test_bang_bumps_major`, `test_breaking_change_footer_bumps_major`, `test_breaking_on_0x_bumps_major`, `test_merge_commit_branch_commits_counted`, `test_highest_semver_tag_is_base`, `test_head_tagged_prints_nothing`, `test_head_contained_in_newer_tag_prints_nothing`, and in Python `test_script_is_stdlib_only`.
- Workflow: `test_release_job_runs_last_on_main_push`, `test_release_job_fetches_full_history_and_tags`, `test_release_job_computes_version_with_script`, `test_release_job_retags_manifest_only`, `test_release_job_pushes_git_tag_last`, `test_no_tag_trigger_or_tag_publish_job`.

agents-matrix-connector specifics: `needs: [lint, test, chart, images, chart-publish]`; IMAGE `harbor.szymonrichert.pl/containers/agents-matrix-connector`. `scripts/next_version.py` and `tests/test_next_version.py` are copied unchanged from agents-orchestrator; the six workflow tests go into `tests/test_ci.py` by the names above.

## Expected outcome

On a green push to main the `release` job tags `agents-matrix-connector:<sha7>` as X.Y.Z, X.Y and X and pushes vX.Y.Z, or skips cleanly when HEAD is already released; the task verify passes locally.

## Steps

1. Red (script): `git -C /Users/szymonri/Documents/claude-code-tatara/code/agents-orchestrator show semver-image-tags-at-the-end:tests/test_next_version.py > tests/test_next_version.py`; run `mise exec -- uv run pytest tests/test_next_version.py`; expect failures because `scripts/next_version.py` does not exist.
2. Green (script): `git -C /Users/szymonri/Documents/claude-code-tatara/code/agents-orchestrator show semver-image-tags-at-the-end:scripts/next_version.py > scripts/next_version.py`; rerun; expect all passed; check both files with `cmp` (ac1, ac2); run `python3 scripts/next_version.py` (ac4).
3. Red (workflow): add the six workflow tests and make the Notes' test changes in `tests/test_ci.py`; run `mise exec -- uv run pytest tests/test_ci.py`; expect the new and changed tests to fail on the current ci.yaml.
4. Green (workflow): edit `.github/workflows/ci.yaml` and the other files the Requirement names, README and MEMORY.md; run the task verify; expect lint clean and every test passing.

## Notes

- No existing test in `tests/test_ci.py` becomes inaccurate: `test_pr_checks_and_secrets` accepts the release job (its secret steps sit in a job guarded by the main condition, and it names only HARBOR_USERNAME and HARBOR_PASSWORD). If one fails, the layout is wrong, not the test.
- `test_no_tag_trigger_or_tag_publish_job` passes before any change here (this repo never had a tag trigger); it is a guard that pins the absence, say so in the red step instead of claiming it failed.
- `chart-publish` here has no regctl-installer; the release job brings its own pinned one.
- README has no release section today; add `## Release` (before `## Security` or after `## Operations`).
- Never edit the two copied files here: a defect goes back to agents-orchestrator (return it as a discovered item), so every copy stays identical.
- Noted, not doing now: anything else in ci.yaml (the existing jobs stay as they are).
