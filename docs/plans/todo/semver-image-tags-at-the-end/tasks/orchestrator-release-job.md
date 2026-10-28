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

agents-orchestrator specifics: `needs: [lint, test, images, chart, e2e, chart-publish]`; IMAGE `harbor.szymonrichert.pl/containers/agents-orchestrator`. Script tests in `tests/test_next_version.py`; the five `test_release_job_*` tests in `tests/test_images.py`; `test_no_tag_trigger_or_tag_publish_job` in `tests/test_chart_ci.py`. `scripts/chart-version.sh` keeps `branch main <sha>` (exit 0, `<version>-main.<sha7>`) and exits 2 for everything else; its header comment drops exit 1 for a tag mismatch (exit 1 stays only for "no version in Chart.yaml").

## Expected outcome

On a green push to main the `release` job computes the version, copies `agents-orchestrator:<sha7>` to X.Y.Z, X.Y and X, then pushes git tag vX.Y.Z; with HEAD already in a release tag it skips every step after the version and succeeds. Locally the verify passes and `python3 scripts/next_version.py` prints `0.1.0`. No `v*` trigger, no `chart-publish-tag`, no chart-version.sh tag mode remain.

## Steps

1. Red (script): write `tests/test_next_version.py` with the twelve script tests; run `mise exec -- uv run pytest tests/test_next_version.py`; expect every test to fail because `scripts/next_version.py` does not exist.
2. Green (script): write `scripts/next_version.py`; rerun; expect all passed. Run `python3 scripts/next_version.py`; expect `0.1.0`.
3. Red (workflow): add the five `test_release_job_*` tests to `tests/test_images.py`, add `test_no_tag_trigger_or_tag_publish_job` and make the Notes' test changes in `tests/test_chart_ci.py`, extend `test_readme_documents_releasing`; run `mise exec -- uv run pytest tests/test_images.py tests/test_chart_ci.py`; expect the new and changed tests to fail on the current ci.yaml, script and README.
4. Green (workflow): edit `.github/workflows/ci.yaml` (add `release`, drop `tags: ["v*"]` and `chart-publish-tag`), `scripts/chart-version.sh` (drop the tag branch), README `## Releasing`, MEMORY.md; run the task verify; expect lint clean and every listed test file passing.

## Notes

- Tests that D9 makes inaccurate, and only these change: `tests/test_chart_ci.py::test_chart_job_on_every_push` asserts `"v*" in on["push"]["tags"]` (that line goes); `test_publish_only_main_and_tags_after_images` asserts `chart-publish-tag`'s needs and if (keep the chart-publish half, rename it `test_publish_only_main_after_images`); `test_chart_version_scheme` expects `tag v<version>` exit 0 and `tag v9.9.9` exit 1 (both become exit 2); `test_publish_refuses_existing_version` and `test_package_sets_app_version_sha7` loop over `chart-publish-tag` (loop over `chart-publish` only). `tests/test_images.py`'s existing tests stay as they are: the release job reuses the same IMAGE string, uses `regctl image copy` (not `import`) and its login is not in the `images` job.
- `tests/test_project_name.py::test_chart_and_ci_named` and `tests/test_frontend_retired.py::test_ci_has_no_npm` read ci.yaml; they are in the verify and must stay green unchanged.
- Script tests use real `git` in `tmp_path` repos, never mocked git output (retro proposal, design Research inputs). Pass commit identity through env (`GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME`, `GIT_COMMITTER_EMAIL`) and isolate from the host config (`GIT_CONFIG_GLOBAL=os.devnull`, `GIT_CONFIG_NOSYSTEM=1`): CI runners have no identity and a host may sign commits or tags. `git init -b main`; empty commits with `git commit --allow-empty -m <msg>`; lightweight tags.
- Merge case: branch `feature` with a `feat:` commit, back on main, `git merge --no-ff feature -m "Merge pull request #1 from x/y"`. Contained case: tag v1.0.0, commit c1, commit c2 tagged v1.1.0, `git checkout --detach <c1>`, expect empty stdout.
- Locate the script as `Path(__file__).resolve().parent.parent / "scripts" / "next_version.py"` and run it with `sys.executable`, cwd the temp repo. Nothing repo-specific may appear in either file: both are copied byte for byte into agents-webhook, agents-schedule and agents-matrix-connector (identical ruff config: line-length 100, py312, E F I UP B SIM), and the script into agents-web.
- `test_script_is_stdlib_only`: `ast`-parse the script; every top-level module of every `import`/`from ... import` is in `sys.stdlib_module_names`.
- README `## Releasing` today says a `vX.Y.Z` tag publishes chart `X.Y.Z` and how to cut one by hand; those bullets go, the main-publish, refusal and robot-rights bullets stay.
- Noted, not doing now: `regctl-installer@main` in `images` and `chart-publish`; the release job uses the pinned SHA.
