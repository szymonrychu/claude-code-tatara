# Semver image tags at the end of main builds implementation plan

## Agreed rung

Rung 1 of plan.md, all items 1.1-1.8: 1.1-1.5 as migrated, 1.6-1.8 the user's gate rule of 2026-10-31 ("Fix it permanently by setting a rule to always semver tag containers before deploying"). Q1 answered with its recommendation: chart-publish-tag, the `push: tags: [v*]` trigger and chart-version.sh's tag mode are removed (D9). Nothing outside these items is built.

## Approach

Component mode across six submodules plus the superrepo. Chunks run in order:

1. Chunk 1 (S1-S6): the release job in the five image-building repos, one PR per repo (S2 and S5 share the agents-web PR). Migrated steps keep their epic-format body sections.
2. Chunk 2 (S7): the workbench hard rule in the superrepo AGENTS.md, independent of chunk 1.
3. Gate between chunk 2 and chunk 3 (orchestrator, not a build step): each chunk 1 PR is merged as soon as it is green (act on the first, never the batch), and its main run's `release` job is watched to green. Evidence per repo: `git -C code/<repo> ls-remote --tags origin 'v*'` lists vX.Y.Z; Harbor answers 200 for `GET https://harbor.szymonrichert.pl/v2/containers/<repo>/manifests/<X.Y.Z>` (read-only, credentials from Secret `regcred` in namespace agents, as in agents-helmfile MEMORY.md 2026-10-27); its digest equals the digest of `:<sha7>`. Then the superrepo pointer is committed. Chunk 3 needs these five versions.
4. Chunk 3 (S8-S9): agents-helmfile, one PR: the semver guard, the X.Y.Z pins and the helmfile copy of the rule.
5. Chunk 4 (S10): the live apply, run by the orchestrator session from agents-helmfile main after the chunk 3 PR merges.

Rules for every chunk: read every file of the step in one pass before editing; TDD red then green, each run once; never edit, skip or xfail a test to pass unless it is named below as no longer accurate; targeted verify only; no em dashes; `UV_PYTHON=3.12` in agents-matrix-connector.

## Chunk 1: release jobs (model: opus)

### S1: orchestrator release job

- Status: todo
- Covers: 1.1, 1.2, 1.3, 1.4
- Test first: the red steps under its #### Steps
- Change: as its #### Requirement and #### Steps
- Model: opus (chunk)
- Files: `scripts/next_version.py`, `tests/test_next_version.py`, `.github/workflows/ci.yaml`, `tests/test_images.py`, `tests/test_chart_ci.py`, `scripts/chart-version.sh`, `README.md`, `MEMORY.md`
- Verify: `mise run lint && mise exec -- uv run pytest tests/test_next_version.py tests/test_images.py tests/test_chart_ci.py tests/test_project_name.py tests/test_frontend_retired.py`
- Verified head: none

#### Requirement

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

#### Acceptance conditions

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

#### Files

- `scripts/next_version.py`
- `tests/test_next_version.py`
- `.github/workflows/ci.yaml`
- `tests/test_images.py`
- `tests/test_chart_ci.py`
- `scripts/chart-version.sh`
- `README.md`
- `MEMORY.md`

#### Interfaces

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

#### Expected outcome

On a green push to main the `release` job computes the version, copies `agents-orchestrator:<sha7>` to X.Y.Z, X.Y and X, then pushes git tag vX.Y.Z; with HEAD already in a release tag it skips every step after the version and succeeds. Locally the verify passes and `python3 scripts/next_version.py` prints `0.1.0`. No `v*` trigger, no `chart-publish-tag`, no chart-version.sh tag mode remain.

#### Steps

1. Red (script): write `tests/test_next_version.py` with the twelve script tests; run `mise exec -- uv run pytest tests/test_next_version.py`; expect every test to fail because `scripts/next_version.py` does not exist.
2. Green (script): write `scripts/next_version.py`; rerun; expect all passed. Run `python3 scripts/next_version.py`; expect `0.1.0`.
3. Red (workflow): add the five `test_release_job_*` tests to `tests/test_images.py`, add `test_no_tag_trigger_or_tag_publish_job` and make the Notes' test changes in `tests/test_chart_ci.py`, extend `test_readme_documents_releasing`; run `mise exec -- uv run pytest tests/test_images.py tests/test_chart_ci.py`; expect the new and changed tests to fail on the current ci.yaml, script and README.
4. Green (workflow): edit `.github/workflows/ci.yaml` (add `release`, drop `tags: ["v*"]` and `chart-publish-tag`), `scripts/chart-version.sh` (drop the tag branch), README `## Releasing`, MEMORY.md; run the task verify; expect lint clean and every listed test file passing.

#### Notes

- Tests that D9 makes inaccurate, and only these change: `tests/test_chart_ci.py::test_chart_job_on_every_push` asserts `"v*" in on["push"]["tags"]` (that line goes); `test_publish_only_main_and_tags_after_images` asserts `chart-publish-tag`'s needs and if (keep the chart-publish half, rename it `test_publish_only_main_after_images`); `test_chart_version_scheme` expects `tag v<version>` exit 0 and `tag v9.9.9` exit 1 (both become exit 2); `test_publish_refuses_existing_version` and `test_package_sets_app_version_sha7` loop over `chart-publish-tag` (loop over `chart-publish` only). `tests/test_images.py`'s existing tests stay as they are: the release job reuses the same IMAGE string, uses `regctl image copy` (not `import`) and its login is not in the `images` job.
- `tests/test_project_name.py::test_chart_and_ci_named` and `tests/test_frontend_retired.py::test_ci_has_no_npm` read ci.yaml; they are in the verify and must stay green unchanged.
- Script tests use real `git` in `tmp_path` repos, never mocked git output (retro proposal, design Research inputs). Pass commit identity through env (`GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME`, `GIT_COMMITTER_EMAIL`) and isolate from the host config (`GIT_CONFIG_GLOBAL=os.devnull`, `GIT_CONFIG_NOSYSTEM=1`): CI runners have no identity and a host may sign commits or tags. `git init -b main`; empty commits with `git commit --allow-empty -m <msg>`; lightweight tags.
- Merge case: branch `feature` with a `feat:` commit, back on main, `git merge --no-ff feature -m "Merge pull request #1 from x/y"`. Contained case: tag v1.0.0, commit c1, commit c2 tagged v1.1.0, `git checkout --detach <c1>`, expect empty stdout.
- Locate the script as `Path(__file__).resolve().parent.parent / "scripts" / "next_version.py"` and run it with `sys.executable`, cwd the temp repo. Nothing repo-specific may appear in either file: both are copied byte for byte into agents-webhook, agents-schedule and agents-matrix-connector (identical ruff config: line-length 100, py312, E F I UP B SIM), and the script into agents-web.
- `test_script_is_stdlib_only`: `ast`-parse the script; every top-level module of every `import`/`from ... import` is in `sys.stdlib_module_names`.
- README `## Releasing` today says a `vX.Y.Z` tag publishes chart `X.Y.Z` and how to cut one by hand; those bullets go, the main-publish, refusal and robot-rights bullets stay.
- Noted, not doing now: `regctl-installer@main` in `images` and `chart-publish`; the release job uses the pinned SHA.

### S2: web script tests wired

- Status: todo
- Covers: 1.4
- Test first: the red steps under its #### Steps
- Change: as its #### Requirement and #### Steps
- Model: opus (chunk)
- Files: `package.json`, `.mise.toml`, `.github/workflows/ci.yaml`, `scripts/ci.test.mjs`
- Verify: `mise run lint && mise exec -- npm run test:scripts`
- Verified head: none

#### Requirement

Decision given for this epic (verbatim): "Script: one stdlib-only Python script, byte-identical in the five repos, tested in each repo's own test runner (pytest in the Python repos; agents-web: its own runner spawning python3, read its package.json); no third-party version action (research: supply-chain risk in a contents: write job)."

Epic README Goal (verbatim): "Tests that pin the CI layout are updated to the new layout, and each repo's lint and tests pass."

design.md D10 (verbatim): "agents-web gets the npm script `\"test:scripts\": \"node --test 'scripts/*.test.mjs'\"`; the `web` CI job runs `npm run test:scripts` after `npm test`; `.mise.toml`'s `test` task runs `npm test` then `npm run test:scripts`. This wires the orphaned `scripts/ci.test.mjs` (13 tests, run by nothing today) and `scripts/sync-api.test.mjs`, and later `scripts/next_version.test.mjs`."

Discovery (verbatim): "`scripts/ci.test.mjs` (node:test, 13 tests) ... ORPHANED: not run by `npm test` (vitest include is `src/**/*.test.{ts,tsx}`, `vite.config.ts`), `test:chart` (`chart/tests/*.test.mjs`), mise or CI."

#### Acceptance conditions

- ac1: package.json has the script `"test:scripts": "node --test 'scripts/*.test.mjs'"` with `"test"` still `vitest run`, the `web` job runs `npm run test:scripts` after `npm test`, and `.mise.toml`'s `test` task runs `npm test` then `npm run test:scripts`, all asserted by `test_scripts_tests_are_wired` in scripts/ci.test.mjs [evidence: command:mise exec -- node --test --test-name-pattern=test_scripts_tests_are_wired scripts/ci.test.mjs]
- ac2: `npm run test:scripts` runs scripts/ci.test.mjs and scripts/sync-api.test.mjs and reports fail 0 [evidence: command:mise exec -- npm run test:scripts]
- ac3: Lint passes [evidence: command:mise run lint]

#### Files

- `package.json`
- `.mise.toml`
- `.github/workflows/ci.yaml`
- `scripts/ci.test.mjs`

#### Interfaces

- `package.json` `scripts["test:scripts"]` = `node --test 'scripts/*.test.mjs'` (quoted glob: node expands it, so it works the same in npm's sh and in mise).
- `.github/workflows/ci.yaml` job `web`: a step `- run: npm run test:scripts` directly after `- run: npm test`.
- `.mise.toml` `[tasks.test]` `run = ["npm test", "npm run test:scripts"]`.
- New node:test in `scripts/ci.test.mjs`: `test_scripts_tests_are_wired`, reading package.json, ci.yaml and .mise.toml.

#### Expected outcome

`mise run test` and the `web` CI job run every `scripts/*.test.mjs` file, so `scripts/ci.test.mjs` and `scripts/sync-api.test.mjs` stop being dead, and web-release-job's `scripts/next_version.test.mjs` runs as soon as it exists.

#### Steps

1. Red: add `test_scripts_tests_are_wired` to `scripts/ci.test.mjs`; run `mise exec -- node --test --test-name-pattern=test_scripts_tests_are_wired scripts/ci.test.mjs`; expect it to fail on the missing `test:scripts` script.
2. Green: add the npm script, the CI step and the mise task change; rerun the same command (pass), then `mise exec -- npm run test:scripts` (expect `fail 0`, about 23 tests) and `mise run lint`.

#### Notes

- Do not change `"test": "vitest run"`: agents run `npm test -- <file>` and appending node to it would hand that file to node.
- `mise run test` locally also runs vitest, which needs `npm ci --no-audit --no-fund` first in a stale tree (missing `@codemirror/*`); that is a local env step, not a code change.
- The existing test "web job: node 24 with npm cache and the four npm scripts" stays accurate; extend nothing else in ci.test.mjs here (the release layout is web-release-job's).

### S3: matrix connector release job

- Status: todo
- Covers: 1.1, 1.2, 1.3, 1.4
- Test first: the red steps under its #### Steps
- Change: as its #### Requirement and #### Steps
- Model: opus (chunk)
- Files: `scripts/next_version.py`, `tests/test_next_version.py`, `.github/workflows/ci.yaml`, `tests/test_ci.py`, `README.md`, `MEMORY.md`
- Verify: `mise run lint && mise exec -- uv run pytest tests/test_next_version.py tests/test_ci.py`
- Verified head: none

#### Requirement

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

#### Acceptance conditions

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

#### Files

- `scripts/next_version.py`
- `tests/test_next_version.py`
- `.github/workflows/ci.yaml`
- `tests/test_ci.py`
- `README.md`
- `MEMORY.md`

#### Interfaces

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

#### Expected outcome

On a green push to main the `release` job tags `agents-matrix-connector:<sha7>` as X.Y.Z, X.Y and X and pushes vX.Y.Z, or skips cleanly when HEAD is already released; the task verify passes locally.

#### Steps

1. Red (script): `git -C /Users/szymonri/Documents/claude-code-tatara/code/agents-orchestrator show semver-image-tags-at-the-end:tests/test_next_version.py > tests/test_next_version.py`; run `mise exec -- uv run pytest tests/test_next_version.py`; expect failures because `scripts/next_version.py` does not exist.
2. Green (script): `git -C /Users/szymonri/Documents/claude-code-tatara/code/agents-orchestrator show semver-image-tags-at-the-end:scripts/next_version.py > scripts/next_version.py`; rerun; expect all passed; check both files with `cmp` (ac1, ac2); run `python3 scripts/next_version.py` (ac4).
3. Red (workflow): add the six workflow tests and make the Notes' test changes in `tests/test_ci.py`; run `mise exec -- uv run pytest tests/test_ci.py`; expect the new and changed tests to fail on the current ci.yaml.
4. Green (workflow): edit `.github/workflows/ci.yaml` and the other files the Requirement names, README and MEMORY.md; run the task verify; expect lint clean and every test passing.

#### Notes

- No existing test in `tests/test_ci.py` becomes inaccurate: `test_pr_checks_and_secrets` accepts the release job (its secret steps sit in a job guarded by the main condition, and it names only HARBOR_USERNAME and HARBOR_PASSWORD). If one fails, the layout is wrong, not the test.
- `test_no_tag_trigger_or_tag_publish_job` passes before any change here (this repo never had a tag trigger); it is a guard that pins the absence, say so in the red step instead of claiming it failed.
- `chart-publish` here has no regctl-installer; the release job brings its own pinned one.
- README has no release section today; add `## Release` (before `## Security` or after `## Operations`).
- Never edit the two copied files here: a defect goes back to agents-orchestrator (return it as a discovered item), so every copy stays identical.
- Noted, not doing now: anything else in ci.yaml (the existing jobs stay as they are).

### S4: schedule release job

- Status: todo
- Covers: 1.1, 1.2, 1.3, 1.4
- Test first: the red steps under its #### Steps
- Change: as its #### Requirement and #### Steps
- Model: opus (chunk)
- Files: `scripts/next_version.py`, `tests/test_next_version.py`, `.github/workflows/ci.yaml`, `tests/test_ci_workflow.py`, `scripts/chart-version.sh`, `README.md`, `MEMORY.md`
- Verify: `mise run lint && mise exec -- uv run pytest tests/test_next_version.py tests/test_ci_workflow.py`
- Verified head: none

#### Requirement

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

This task delivers them in agents-schedule. `scripts/next_version.py` and `tests/test_next_version.py` are byte-for-byte copies of agents-orchestrator's (task orchestrator-release-job). The release job needs lint, test, chart, e2e, images, chart-publish. The `push: tags: ["v*"]` trigger, the `chart-publish-tag` job and the `tag` mode of `scripts/chart-version.sh` are removed (D9). README `## Releases` (rewritten, the v0.1.0 line kept) documents the release job and MEMORY.md gets the dated entry (D11).

#### Acceptance conditions

- ac1: scripts/next_version.py is byte-identical to agents-orchestrator's on the epic branch [evidence: command:git -C /Users/szymonri/Documents/claude-code-tatara/code/agents-orchestrator show semver-image-tags-at-the-end:scripts/next_version.py | cmp - scripts/next_version.py]
- ac2: tests/test_next_version.py is byte-identical to agents-orchestrator's on the epic branch [evidence: command:git -C /Users/szymonri/Documents/claude-code-tatara/code/agents-orchestrator show semver-image-tags-at-the-end:tests/test_next_version.py | cmp - tests/test_next_version.py]
- ac3: Every script case passes in this repo's runner (no tag gives 0.1.0, patch, minor, case-insensitive type, bang and footer major, 0.x major, merge commits counted, highest semver base, HEAD tagged or contained prints nothing, stdlib only) [evidence: command:mise exec -- uv run pytest tests/test_next_version.py]
- ac4: Run on this repo, where v0.1.0 (on 6cfa955) is the only vX.Y.Z tag, the real script prints a version above 0.1.0 (it bumps from v0.1.0, never restarts at 0.1.0) [evidence: command:python3 scripts/next_version.py]
- ac5: Job `release` has `if` equal to the main-push condition, `needs` equal to every other job of the workflow (lint, test, chart, e2e, images, chart-publish), `permissions` equal to `{contents: write}` and `concurrency` equal to `{group: release, cancel-in-progress: false}` [evidence: test:tests/test_ci_workflow.py::test_release_job_runs_last_on_main_push]
- ac6: The release job's checkout uses `fetch-depth: 0` and `fetch-tags: true` [evidence: test:tests/test_ci_workflow.py::test_release_job_fetches_full_history_and_tags]
- ac7: The version step (id `version`) runs `python3 scripts/next_version.py` into `$GITHUB_OUTPUT`, and every later step has `if: steps.version.outputs.version != ''` [evidence: test:tests/test_ci_workflow.py::test_release_job_computes_version_with_script]
- ac8: Exactly three `regctl image copy "$IMAGE:$SHORTSHA" ...` lines targeting `$VERSION`, `$VERSION_MINOR` and `$VERSION_MAJOR`, env IMAGE harbor.szymonrichert.pl/containers/agents-schedule, regctl-installer pinned to a 40-hex SHA, Harbor login with HARBOR_USERNAME and HARBOR_PASSWORD, and no `docker`, `regctl image import` or `--blob-chunk` in the job [evidence: test:tests/test_ci_workflow.py::test_release_job_retags_manifest_only]
- ac9: The last step runs `git tag "v$VERSION" "$GITHUB_SHA"` then `git push origin "refs/tags/v$VERSION"`, after every copy, with no `--force` or `-f`, and the workflow has no `secrets.GITHUB_TOKEN` [evidence: test:tests/test_ci_workflow.py::test_release_job_pushes_git_tag_last]
- ac10: The workflow has no `push.tags` trigger and no `chart-publish-tag` job [evidence: test:tests/test_ci_workflow.py::test_no_tag_trigger_or_tag_publish_job]
- ac11: `scripts/chart-version.sh` prints `0.4.2-main.abcdef1` for main in the temporary tree and exits 2 for `tag v0.4.2` and every other non-main ref [evidence: test:tests/test_ci_workflow.py::test_chart_version_script]
- ac12: Every test of tests/test_ci_workflow.py passes against the new layout (jobs list release and not chart-publish-tag, no tag trigger, the images-job checks unchanged) [evidence: command:mise exec -- uv run pytest tests/test_ci_workflow.py]
- ac13: README `## Releases` describes the release job (versions from conventional commits since the last vX.Y.Z tag, image tags X.Y.Z, X.Y and X, git tag vX.Y.Z, pin X.Y.Z), keeps the v0.1.0 line as history and says releases after it are automatic [evidence: doc-section:README.md#Releases]
- ac14: MEMORY.md has a 2026-10-28 entry giving the why of the release job, bumping from v0.1.0, and the retired tag path [evidence: doc-section:MEMORY.md]
- ac15: Lint passes [evidence: command:mise run lint]

#### Files

- `scripts/next_version.py`
- `tests/test_next_version.py`
- `.github/workflows/ci.yaml`
- `tests/test_ci_workflow.py`
- `scripts/chart-version.sh`
- `README.md`
- `MEMORY.md`

#### Interfaces

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

agents-schedule specifics: `needs: [lint, test, chart, e2e, images, chart-publish]`; IMAGE `harbor.szymonrichert.pl/containers/agents-schedule`. `scripts/next_version.py` and `tests/test_next_version.py` are copied unchanged from agents-orchestrator; the six workflow tests go into `tests/test_ci_workflow.py` by the names above.

#### Expected outcome

On a green push to main the `release` job tags `agents-schedule:<sha7>` as X.Y.Z, X.Y and X and pushes vX.Y.Z, or skips cleanly when HEAD is already released; the task verify passes locally.

#### Steps

1. Red (script): `git -C /Users/szymonri/Documents/claude-code-tatara/code/agents-orchestrator show semver-image-tags-at-the-end:tests/test_next_version.py > tests/test_next_version.py`; run `mise exec -- uv run pytest tests/test_next_version.py`; expect failures because `scripts/next_version.py` does not exist.
2. Green (script): `git -C /Users/szymonri/Documents/claude-code-tatara/code/agents-orchestrator show semver-image-tags-at-the-end:scripts/next_version.py > scripts/next_version.py`; rerun; expect all passed; check both files with `cmp` (ac1, ac2); run `python3 scripts/next_version.py` (ac4).
3. Red (workflow): add the six workflow tests and make the Notes' test changes in `tests/test_ci_workflow.py`; run `mise exec -- uv run pytest tests/test_ci_workflow.py`; expect the new and changed tests to fail on the current ci.yaml.
4. Green (workflow): edit `.github/workflows/ci.yaml` and the other files the Requirement names, README and MEMORY.md; run the task verify; expect lint clean and every test passing.

#### Notes

- Tests that D9 makes inaccurate, and only these change in `tests/test_ci_workflow.py`: `test_workflow_jobs_and_targets` lists `chart-publish-tag`, asserts `on.push.tags == ["v*"]`, `chart-publish-tag`'s if, loops over it and asserts `chart-version.sh tag` (those parts go, `release` joins the job list, the `TAG` constant goes); `test_chart_version_script` expects `tag v0.4.2` exit 0 and `tag v9.9.9` exit 1 (both exit 2 with empty stdout). `test_images_job_checks_uid_and_no_dev_deps` and the rest stay as they are.
- ac4 needs tag v0.1.0 in the tree: `git tag -l v0.1.0` must list it (it is on 6cfa955 locally and on origin); if a fresh tree lacks it, `git fetch --tags origin`. The printed version depends on the commit types since v0.1.0 (patch 0.1.1, or 0.2.0 when a `feat` is among them); it must never be 0.1.0.
- README `## Releases` holds the hand-recorded v0.1.0 line; keep it as history and add that later releases come from the release job.
- Never edit the two copied files here: a defect goes back to agents-orchestrator (return it as a discovered item), so every copy stays identical.
- Noted, not doing now: anything else in ci.yaml (the existing jobs stay as they are).

### S5: web release job

- Status: todo
- Covers: 1.1, 1.2, 1.3, 1.4
- Test first: the red steps under its #### Steps
- Change: as its #### Requirement and #### Steps
- Model: opus (chunk)
- Files: `scripts/next_version.py`, `scripts/next_version.test.mjs`, `.github/workflows/ci.yaml`, `scripts/ci.test.mjs`, `scripts/chart-version.sh`, `README.md`, `MEMORY.md`
- Verify: `mise run lint && mise exec -- npm run test:scripts`
- Verified head: none

#### Requirement

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

This task delivers them in agents-web. `scripts/next_version.py` is a byte-for-byte copy of agents-orchestrator's (task orchestrator-release-job); its tests are `scripts/next_version.test.mjs`, node:test spawning `python3`, run by `npm run test:scripts` (task web-script-tests-wired). The release job needs `web`, `images`, `chart` and `chart-publish`. The `push: tags: ["v*"]` trigger, the `chart-publish-tag` job and the `tag` mode of `scripts/chart-version.sh` are removed (D9); README `## Release` is rewritten for the release job and MEMORY.md gets the dated entry (D11).

#### Acceptance conditions

- ac1: scripts/next_version.py is byte-identical to agents-orchestrator's on the epic branch [evidence: command:git -C /Users/szymonri/Documents/claude-code-tatara/code/agents-orchestrator show semver-image-tags-at-the-end:scripts/next_version.py | cmp - scripts/next_version.py]
- ac2: scripts/next_version.test.mjs has the eleven script cases of the orchestrator task under the same names (test_no_tag_gives_0_1_0 through test_head_contained_in_newer_tag_prints_nothing), each spawning python3 on scripts/next_version.py in a real temporary git repo, and all pass [evidence: command:mise exec -- node --test scripts/next_version.test.mjs]
- ac3: Run on this repo (no vX.Y.Z tag yet) the real script prints 0.1.0 [evidence: command:python3 scripts/next_version.py]
- ac4: Job `release` has `if` equal to the main-push condition, `needs` equal to every other job (web, images, chart, chart-publish), `permissions` equal to `{contents: write}` and `concurrency` equal to `{group: release, cancel-in-progress: false}` [evidence: command:mise exec -- node --test --test-name-pattern=test_release_job_runs_last_on_main_push scripts/ci.test.mjs]
- ac5: The release job's checkout uses `fetch-depth: 0` and `fetch-tags: true` [evidence: command:mise exec -- node --test --test-name-pattern=test_release_job_fetches_full_history_and_tags scripts/ci.test.mjs]
- ac6: The version step (id `version`) runs `python3 scripts/next_version.py` into `$GITHUB_OUTPUT`, and every later step has `if: steps.version.outputs.version != ''` [evidence: command:mise exec -- node --test --test-name-pattern=test_release_job_computes_version_with_script scripts/ci.test.mjs]
- ac7: Exactly three `regctl image copy "$IMAGE:$SHORTSHA" ...` lines targeting `$VERSION`, `$VERSION_MINOR` and `$VERSION_MAJOR`, env IMAGE harbor.szymonrichert.pl/containers/agents-web, regctl-installer pinned to a 40-hex SHA, Harbor login with HARBOR_USERNAME and HARBOR_PASSWORD, and no `docker`, `regctl image import` or `--blob-chunk` in the job [evidence: command:mise exec -- node --test --test-name-pattern=test_release_job_retags_manifest_only scripts/ci.test.mjs]
- ac8: The last step runs `git tag "v$VERSION" "$GITHUB_SHA"` then `git push origin "refs/tags/v$VERSION"`, after every copy, with no `--force` or `-f`, and the workflow has no `secrets.GITHUB_TOKEN` [evidence: command:mise exec -- node --test --test-name-pattern=test_release_job_pushes_git_tag_last scripts/ci.test.mjs]
- ac9: No `push.tags` trigger and no `chart-publish-tag` job [evidence: command:mise exec -- node --test --test-name-pattern=test_no_tag_trigger_or_tag_publish_job scripts/ci.test.mjs]
- ac10: "exactly the five jobs" now lists chart, chart-publish, images, release and web [evidence: command:mise exec -- node --test --test-name-pattern="exactly the five jobs" scripts/ci.test.mjs]
- ac11: `scripts/chart-version.sh tag v<Chart version> <sha>` exits 2 like every non-main ref, and main still prints `<version>-main.<sha7>` [evidence: command:mise exec -- node --test --test-name-pattern="chart-version.sh" scripts/ci.test.mjs]
- ac12: Every scripts test passes: ci.test.mjs, sync-api.test.mjs and next_version.test.mjs [evidence: command:mise exec -- npm run test:scripts]
- ac13: README `## Release` describes the release job (versions from conventional commits since the last vX.Y.Z tag, first release 0.1.0, image tags X.Y.Z, X.Y and X, git tag vX.Y.Z, pin X.Y.Z) and no longer says CI runs on `v*` tags or that a tag publishes the chart [evidence: doc-section:README.md#Release]
- ac14: MEMORY.md has a 2026-10-28 entry giving the why of the release job, the node:test wiring and the retired tag path [evidence: doc-section:MEMORY.md]
- ac15: Lint passes [evidence: command:mise run lint]

#### Files

- `scripts/next_version.py`
- `scripts/next_version.test.mjs`
- `.github/workflows/ci.yaml`
- `scripts/ci.test.mjs`
- `scripts/chart-version.sh`
- `README.md`
- `MEMORY.md`

#### Interfaces

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

agents-web specifics: `needs: [web, images, chart, chart-publish]`; IMAGE `harbor.szymonrichert.pl/containers/agents-web`. `scripts/next_version.py` is copied unchanged from agents-orchestrator. `scripts/next_version.test.mjs` (node:test, `node:child_process` `spawnSync("python3", [script], {cwd, env})`) holds the eleven script tests by the names above; the six workflow tests go into `scripts/ci.test.mjs` by the names above. `scripts/chart-version.sh` keeps `branch main <sha>` and exits 2 for everything else.

#### Expected outcome

On a green push to main the `release` job tags `agents-web:<sha7>` as X.Y.Z, X.Y and X and pushes vX.Y.Z; `npm run test:scripts` runs the new script tests and the updated layout tests, all passing; `python3 scripts/next_version.py` prints `0.1.0` here.

#### Steps

1. Red (script): write `scripts/next_version.test.mjs` with the eleven cases; run `mise exec -- node --test scripts/next_version.test.mjs`; expect failures because `scripts/next_version.py` does not exist.
2. Green (script): `git -C /Users/szymonri/Documents/claude-code-tatara/code/agents-orchestrator show semver-image-tags-at-the-end:scripts/next_version.py > scripts/next_version.py`; rerun; expect `fail 0`. `cmp` it against the orchestrator copy (ac1); `python3 scripts/next_version.py` prints `0.1.0`.
3. Red (workflow): add the six workflow tests and make the Notes' test changes in `scripts/ci.test.mjs`; run `mise exec -- node --test scripts/ci.test.mjs`; expect the new and changed tests to fail on the current ci.yaml and script.
4. Green (workflow): edit `.github/workflows/ci.yaml` (add `release`, drop `tags: ["v*"]` and `chart-publish-tag`), `scripts/chart-version.sh` (drop the tag branch), README `## Release`, MEMORY.md; run the task verify; expect lint clean and `fail 0`.

#### Notes

- Tests that D9 makes inaccurate, and only these change in `scripts/ci.test.mjs`: "triggers: push main, tags v*, pull requests" asserts `on.push.tags` (becomes push main and pull requests, no tags; rename to match); "exactly the five jobs" (still five: chart, chart-publish, images, release, web); "chart-publish-tag: tags only, requires the image, versions and pushes" (removed with the job); "chart-version.sh: matching tag gives X.Y.Z" and "chart-version.sh: mismatched tag is refused" (replaced by "chart-version.sh: tag refs publish nothing", exit 2). "every Harbor login step is in a push-only job or guarded" and "every regctl-installer use is pinned to a 40-hex commit SHA" (`uses.length >= 3`: images, chart-publish, release) stay as they are.
- Do not change "test_scripts_tests_are_wired" (task web-script-tests-wired).
- Script tests use real `git` in `mkdtempSync(join(tmpdir(), ...))` repos, never mocked output; identity through env (`GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME`, `GIT_COMMITTER_EMAIL`) plus `GIT_CONFIG_GLOBAL=/dev/null` and `GIT_CONFIG_NOSYSTEM=1`; mirror the orchestrator test file case by case (read it on the epic branch with `git -C /Users/szymonri/Documents/claude-code-tatara/code/agents-orchestrator show semver-image-tags-at-the-end:tests/test_next_version.py`).
- The `web` CI job has no mise; `python3` and `git` come with ubuntu-latest.
- README `## Release` today says CI runs on `v*` tags and that a tag publishes the chart; both go.
- Never edit `scripts/next_version.py` here: a defect goes back to agents-orchestrator (return it as a discovered item), so the five copies stay identical.

### S6: webhook release job

- Status: todo
- Covers: 1.1, 1.2, 1.3, 1.4
- Test first: the red steps under its #### Steps
- Change: as its #### Requirement and #### Steps
- Model: opus (chunk)
- Files: `scripts/next_version.py`, `tests/test_next_version.py`, `.github/workflows/ci.yaml`, `tests/test_ci.py`, `scripts/chart-version.sh`, `README.md`, `MEMORY.md`
- Verify: `UV_PYTHON=3.12 mise run lint && UV_PYTHON=3.12 mise exec -- uv run pytest tests/test_next_version.py tests/test_ci.py`
- Verified head: none

#### Requirement

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

This task delivers them in agents-webhook. `scripts/next_version.py` and `tests/test_next_version.py` are byte-for-byte copies of agents-orchestrator's (task orchestrator-release-job). The release job needs lint, test, chart, e2e, images, chart-publish. The `push: tags: ["v*"]` trigger, the `chart-publish-tag` job and the `tag` mode of `scripts/chart-version.sh` are removed (D9). A new README `## Release` section documents the release job and MEMORY.md gets the dated entry (D11).

#### Acceptance conditions

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

#### Files

- `scripts/next_version.py`
- `tests/test_next_version.py`
- `.github/workflows/ci.yaml`
- `tests/test_ci.py`
- `scripts/chart-version.sh`
- `README.md`
- `MEMORY.md`

#### Interfaces

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

agents-webhook specifics: `needs: [lint, test, chart, e2e, images, chart-publish]`; IMAGE `harbor.szymonrichert.pl/containers/agents-webhook`. `scripts/next_version.py` and `tests/test_next_version.py` are copied unchanged from agents-orchestrator; the six workflow tests go into `tests/test_ci.py` by the names above.

#### Expected outcome

On a green push to main the `release` job tags `agents-webhook:<sha7>` as X.Y.Z, X.Y and X and pushes vX.Y.Z, or skips cleanly when HEAD is already released; the task verify passes locally.

#### Steps

1. Red (script): `git -C /Users/szymonri/Documents/claude-code-tatara/code/agents-orchestrator show semver-image-tags-at-the-end:tests/test_next_version.py > tests/test_next_version.py`; run `UV_PYTHON=3.12 mise exec -- uv run pytest tests/test_next_version.py`; expect failures because `scripts/next_version.py` does not exist.
2. Green (script): `git -C /Users/szymonri/Documents/claude-code-tatara/code/agents-orchestrator show semver-image-tags-at-the-end:scripts/next_version.py > scripts/next_version.py`; rerun; expect all passed; check both files with `cmp` (ac1, ac2); run `python3 scripts/next_version.py` (ac4).
3. Red (workflow): add the six workflow tests and make the Notes' test changes in `tests/test_ci.py`; run `UV_PYTHON=3.12 mise exec -- uv run pytest tests/test_ci.py`; expect the new and changed tests to fail on the current ci.yaml.
4. Green (workflow): edit `.github/workflows/ci.yaml` and the other files the Requirement names, README and MEMORY.md; run the task verify; expect lint clean and every test passing.

#### Notes

- Tests that D9 makes inaccurate, and only these change in `tests/test_ci.py`: `test_jobs_exist` lists `chart-publish-tag` (swap for `release`); `test_triggers_include_pull_requests_main_and_tags` asserts `on.push.tags == ["v*"]` (drop that line, rename `test_triggers_include_pull_requests_and_main`); `test_chart_publish_conditions_and_repo` asserts `chart-publish-tag`'s if and `chart-version.sh tag` (those two lines go); `test_secrets_only_in_publishing_steps` accepts the tag condition as a job guard (only MAIN remains); `test_chart_version_script` expects `tag v0.1.0` exit 0 and `tag v9.9.9` exit 1 (both exit 2 with empty stdout).
- Local env: always prefix uv and mise commands with `UV_PYTHON=3.12` (uv otherwise picks a managed Python 3.15 and fails building google-re2; probe 2026-10-28 in design.md Constraints). Not a repo change.
- README has no release section today; add `## Release` after `## Helm chart`.
- Never edit the two copied files here: a defect goes back to agents-orchestrator (return it as a discovered item), so every copy stays identical.
- Noted, not doing now: anything else in ci.yaml (the existing jobs stay as they are).

## Chunk 2: workbench hard rule (model: sonnet)

### S7: semver deploy rule in the workbench AGENTS.md

- Files: `AGENTS.md`, `scripts/tests/test_agents_md.py` (superrepo, workbench root; in the plan's superrepo worktree)
- Covers: 1.7
- Test first: `test_semver_deploy_hard_rule` in `scripts/tests/test_agents_md.py`, run red with `pytest scripts/tests/test_agents_md.py -q` (fails: the rule is absent from the project block).
- Change: add one bullet at the end of `## Component hard rules` inside the `<!-- workbench:project:begin -->` block of `AGENTS.md`, verbatim: `- Deploy only semver-tagged images (X.Y.Z); never a sha tag; a component's main build releases the semver tag before helmfile pins it.`
- Verify: `pytest scripts/tests/test_agents_md.py -q && mise run lint:agents-md && mise run lint:em-dash`; expect all passed (skips unchanged) and both lints clean.
- Model: sonnet

#### Requirement

User's gate answer 2 (verbatim): "Fix it permanently by setting a rule to always semver tag containers before deploying". The rule is a Component hard rule of the workbench AGENTS.md project block, placed where the init engine's refresh keeps it. Source of truth: `scripts/init_engine/project_files.py:agents_md` rebuilds the project block from the existing `## Component hard rules` section (`pick`: kept unless `--hard-rule` is passed or the section is a placeholder), so the AGENTS.md block itself is the source; there is no separate config (`.claude/workbench.json` holds only `refRunners`).

#### Acceptance conditions

- ac1: The project block's `## Component hard rules` section contains the line `- Deploy only semver-tagged images (X.Y.Z); never a sha tag; a component's main build releases the semver tag before helmfile pins it.` [evidence: test:scripts/tests/test_agents_md.py::test_semver_deploy_hard_rule]
- ac2: `mise run init:refresh` keeps the rule: after it, `grep -c "Deploy only semver-tagged images" AGENTS.md` prints 1 [evidence: command:mise run init:refresh && grep -c "Deploy only semver-tagged images" AGENTS.md]. Any other file refresh changes is not part of this step: report it with `git status --short` and restore it, never commit it.
- ac3: The root test and lint families pass [evidence: command:pytest scripts/tests/test_agents_md.py -q && mise run lint:agents-md && mise run lint:em-dash]

#### Notes

- The test reads the block with the existing `_block("project")` helper and splits on `## ` headings; assert the rule sits under `Component hard rules`, not anywhere in the file.
- Do not run `mise run harness-setup`; the rules block is not touched.

## Chunk 3: agents-helmfile semver pins and guard (model: opus)

Precondition: the chunk 1 PRs are merged and each repo's main `release` job is green (Approach, item 3). Work in `code/agents-helmfile` on a branch from `origin/main` (fetch first: the local checkout is behind, origin/main pins 2d6d722, ab78d97, 838ba1f, chart 0.1.0 plus image 6cfa955, c98c501).

### S8: semver guard plus orchestrator, web and webhook pins

- Files: `tests/test_semver_pins.py` (new), `values/agents-orchestrator/common.yaml`, `values/agents-web/common.yaml`, `values/agents-webhook/common.yaml`, `helmfile.yaml.gotmpl`, `tests/test_orchestrator_release.py`, `tests/test_web_release.py`, `tests/test_webhook_release.py`
- Covers: 1.5 (three of five components), 1.6
- Test first: write `tests/test_semver_pins.py`; run `uv run --frozen pytest tests/test_semver_pins.py -q` under `mise exec --`; expect it to fail for agents-orchestrator, agents-web, agents-webhook, agents-schedule and agents-matrix-connector (sha7 tags) and pass for the claude-code-wrapper 0.3.3 references.
- Change: pin `image.tag` of the three components to their released X.Y.Z (quoted strings), and each chart `version:` in `helmfile.yaml.gotmpl` to `<Chart.yaml version>-main.<sha7 of that release commit>` (chart and image from one commit, design Deploy step 2); update the three release tests named below.
- Verify: `mise exec -- uv run --frozen pytest tests/test_semver_pins.py tests/test_orchestrator_release.py tests/test_web_release.py tests/test_webhook_release.py -q -k "not agents-schedule and not agents-matrix-connector"` then `mise run lint`; expect all selected tests passed, lint clean.
- Model: opus (chunk)

#### Requirement

Plan item 1.6 (gate addition, user's answer 2 verbatim: "Fix it permanently by setting a rule to always semver tag containers before deploying"): agents-helmfile `mise run test` fails when any harbor.szymonrichert.pl/containers image tag deployed by the helmfile is not X.Y.Z. Plan item 1.5: every one of the five components is pinned to an X.Y.Z image released by this plan.

#### Acceptance conditions

- ac1: `test_semver_pins.py` enumerates the releases from `helmfile build` (the `helmfile_build` fixture), skips releases with `installed: false`, and for each remaining release walks its `layered_values`: every string leaf matching `harbor\.szymonrichert\.pl/containers/[^:\s]+:(\S+)` and every mapping whose `repository` starts with `harbor.szymonrichert.pl/containers/` (with its `tag`; a missing tag fails) must have a tag matching `^\d+\.\d+\.\d+$`; parametrized with the release name as the test id [evidence: test:tests/test_semver_pins.py]
- ac2: A non-vacuity test asserts that agents-orchestrator, agents-web, agents-webhook, agents-schedule and agents-matrix-connector each yield at least one containers image reference [evidence: test:tests/test_semver_pins.py::test_every_component_has_a_containers_image]
- ac3: Red before the pins: the guard fails for the five component releases on origin/main's sha7 pins [evidence: judgement:the implementer quotes the red run's failure lines]
- ac4: values/agents-orchestrator, agents-web and agents-webhook `image.tag` are X.Y.Z released by this plan, each with an existing Harbor manifest (`GET /v2/containers/<repo>/manifests/<X.Y.Z>` 200, as in MEMORY.md 2026-10-27) and git tag `vX.Y.Z` on origin [evidence: command:git -C ../<repo> ls-remote --tags origin vX.Y.Z]
- ac5: Each of the three chart versions is `<version>-main.<sha7>` where sha7 is the commit of tag vX.Y.Z, and `helm show chart oci://harbor.szymonrichert.pl/charts/<chart> --version <v>` returns it [evidence: command:helm show chart oci://harbor.szymonrichert.pl/charts/<chart> --version <v>]
- ac6: The selected tests and lint pass [evidence: command:the Verify line]

#### Notes

- Tests no longer accurate after the re-pin (the only tests changed, each because it hardcodes a sha7 pin the plan replaces): `tests/test_orchestrator_release.py` (`PIN = "2d6d722"`; `test_orchestrator_pin_matches_image` asserts `[0-9a-f]{7}` and `0.1.0-main.{tag}`): becomes an X.Y.Z regex on the image tag, the chart version equal to the pinned `-main.<sha7>` constant and the image tag equal to the pinned X.Y.Z constant. `tests/test_web_release.py::test_web_pin_matches_image` (`[0-9a-f]{7}`, `"ab78d97"`): same shape. `tests/test_webhook_release.py` (`SHA = "838ba1f"`, `test_webhook_pin_and_needs`): chart version the new constant, plus an image tag X.Y.Z assertion if it reads the tag. `test_agent_image_pins_agree` stays unchanged (wrapper 0.3.3).
- Quote every X.Y.Z in YAML (`tag: "0.1.0"`).
- `scripts/check_pins.py` already resolves an X.Y.Z image pin through tag vX.Y.Z; do not change it. Its docstring names only the orchestrator and web image tags as pin sources: noted, not doing now.
- Pin the version each release job actually produced (read its log or `git ls-remote --tags`); never compute it locally.

### S9: schedule and matrix-connector pins, helmfile rule

- Files: `values/agents-schedule/common.yaml`, `values/agents-matrix-connector/common.yaml`, `helmfile.yaml.gotmpl`, `tests/test_schedule_release.py`, `tests/test_matrix_connector_release.py`, `AGENTS.md`, `MEMORY.md`
- Covers: 1.5 (the remaining two components), 1.6 (all releases green), 1.8
- Test first: the S8 guard is still red for agents-schedule and agents-matrix-connector; confirm with `mise exec -- uv run --frozen pytest tests/test_semver_pins.py -q` before editing. The AGENTS.md and MEMORY.md lines are doc edits (TDD exception: a doc edit).
- Change: pin both components' `image.tag` to their released X.Y.Z and chart versions to `<version>-main.<sha7>` of the release commit (agents-schedule moves off chart `0.1.0` to its main chart of the same commit, design Deploy step 2); update the two release tests named below; add the rule to `AGENTS.md`; add a dated MEMORY.md entry.
- Verify: `mise run lint && mise run test`; expect lint clean and `passed` with 0 failed. (Here the component suite is the targeted verify: the guard spans every release.)
- Model: opus (chunk)

#### Requirement

Plan items 1.5 and 1.6 as in S8, for the remaining two components; plan item 1.8: code/agents-helmfile AGENTS.md carries the rule "Deploy only semver-tagged images (X.Y.Z); never a sha tag; a component's main build releases the semver tag before helmfile pins it".

#### Acceptance conditions

- ac1: values/agents-schedule and agents-matrix-connector `image.tag` are X.Y.Z released by this plan, Harbor manifest 200 and git tag on origin [evidence: command:git -C ../<repo> ls-remote --tags origin vX.Y.Z]
- ac2: Both chart versions are `<version>-main.<sha7>` of the vX.Y.Z commit and `helm show chart` returns them [evidence: command:helm show chart oci://harbor.szymonrichert.pl/charts/<chart> --version <v>]
- ac3: The guard passes for every release [evidence: test:tests/test_semver_pins.py]
- ac4: `AGENTS.md` has a `## Deploy rule` section with the rule line verbatim [evidence: command:grep -c "Deploy only semver-tagged images (X.Y.Z); never a sha tag" AGENTS.md]
- ac5: MEMORY.md has a 2026-10-31 entry: the incident (every deployed sha7 pruned, cache-restore pod), the five X.Y.Z pins with their chart versions and digests, and that `tests/test_semver_pins.py` plus `check-pins` enforce the rule [evidence: doc-section:MEMORY.md]
- ac6: `mise run check-pins` passes for the new pins [evidence: command:mise run check-pins]
- ac7: The full component suite and lint pass [evidence: command:mise run lint && mise run test]

#### Notes

- Tests no longer accurate after the re-pin: `tests/test_schedule_release.py` (`version == "0.1.0"` twice, `tag == "6cfa955"`, `test_schedule_pin_matches_release` asserting `[0-9a-f]{7}`): an X.Y.Z regex on the tag, the chart version and tag equal to the new constants. `tests/test_matrix_connector_release.py` (`SHA = "c98c501"`, `test_matrix_connector_pin_and_needs`): the chart version the new constant.
- Never put `mise run apply` in AC evidence (agents-helmfile MEMORY.md 2026-10-25 incident).

## Chunk 4: deploy (model: sonnet)

Run by the orchestrator session from `code/agents-helmfile` at origin/main after the chunk 3 PR merges; not an implementer task in a worktree tree.

### S10: apply the agents namespace and check health

- Files: none in git (the Lease manifest is written under `/Users/szymonri/Documents/claude-code-tatara/.scratchpad/semver-image-tags-at-the-end/lease.yaml`; logs under `/Users/szymonri/Documents/claude-code-tatara/.logs`)
- Covers: 1.5 (applied and healthy)
- Test first: none (a live operation; its checks are the acceptance conditions below).
- Change: claim the deploy Lease, `mise run diff`, the image-existence check, `mise run apply`, health check, release the Lease.
- Verify: `kubectl -n agents get pods` all Ready, and `mise run diff` exits 0 after the apply.
- Model: sonnet

#### Requirement

Plan item 1.5: "the agents namespace is applied and healthy with every pod pulling a semver tag."

#### Procedure

1. Claim Lease `agents/agents-helmfile-apply` (workbench practice, cct2 2026-10-28): `kubectl -n agents create -f lease.yaml` with `apiVersion: coordination.k8s.io/v1`, `kind: Lease`, `spec: {holderIdentity: <this session>, acquireTime: <now, RFC 3339 micro>, leaseDurationSeconds: 3600}`. `create` failing means the Lease exists: under 60 minutes old, wait (bounded at 10 minutes, then re-check); stale, message its holder via the superleader before deleting it. Never apply without the Lease.
2. `mise run kube-context` passes (local default `kubernetes-admin@kubernetes`; in a pod `EXPECTED_KUBE_CONTEXT=in-cluster-sa`); never bypass the guard.
3. Every pinned X.Y.Z answers 200 on Harbor (`GET /v2/containers/<repo>/manifests/<X.Y.Z>`).
4. `mise run diff` reviewed: only the five releases' image tags, chart versions and derived labels change.
5. `mise run apply` (depends on lint, test, check-pins and kube-context), logged to `.logs/semver-apply-<timestamp>.log`.
6. Health: every pod in namespace agents is Ready; `mise run smoke` ends with "smoke: OK".
7. Delete the own Lease.

#### Acceptance conditions

- ac1: The Lease was created with this session as holderIdentity before the diff and deleted by it after the health check [evidence: judgement:orchestrator quotes holderIdentity, acquireTime and the delete]
- ac2: Every pod in namespace agents is Ready [evidence: command:kubectl -n agents get pods]
- ac3: Every harbor.szymonrichert.pl/containers image of a running pod has an X.Y.Z tag [evidence: command:kubectl -n agents get pods -o jsonpath='{..image}' | tr ' ' '\n' | grep harbor.szymonrichert.pl/containers/ | sort -u]
- ac4: `ORCH_CACHE_IMAGE` in the orchestrator settings ConfigMap is `harbor.szymonrichert.pl/containers/agents-orchestrator:<X.Y.Z>` [evidence: command:kubectl -n agents get configmap -o yaml | grep ORCH_CACHE_IMAGE]
- ac5: The post-apply diff shows no changes [evidence: command:mise run diff]
- ac6: The smoke passes [evidence: command:mise run smoke]

## Files to delete

none

## Final verify

On the last commit of each repo, its own commands:

- `mise run --cd code/agents-orchestrator lint && mise run --cd code/agents-orchestrator test`
- `mise run --cd code/agents-web lint && mise run --cd code/agents-web test`
- `mise run --cd code/agents-webhook lint && mise run --cd code/agents-webhook test`
- `mise run --cd code/agents-schedule lint && mise run --cd code/agents-schedule test`
- `UV_PYTHON=3.12 mise run --cd code/agents-matrix-connector lint && UV_PYTHON=3.12 mise run --cd code/agents-matrix-connector test`
- `mise run --cd code/agents-helmfile lint && mise run --cd code/agents-helmfile test`
- superrepo: `mise run lint && mise run test`

DB and e2e suites that need Docker run in each PR's CI; that CI run is the full-suite gate where the local tree cannot run them.

## After merge

1. After each chunk 1 PR merges: its main `release` job green, tag and Harbor checks (Approach, item 3); commit the moved submodule pointer in the superrepo.
2. After the chunk 3 PR merges: S10.
3. Commit the final submodule pointers in the superrepo.
