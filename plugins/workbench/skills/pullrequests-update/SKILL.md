---
name: pullrequests-update
description: "Create or update pull requests (GitHub) and merge requests (GitLab) for pushed code/ branches, host detected per repo from origin, cross-linking companions across repos that changed together."
---

# pullrequests-update

Creates or updates the PR or MR for a pushed branch across one or more repos in `code/`, then cross-links each description with the other PRs/MRs from the same run. The host is detected per repo from its `origin`, so one run may mix GitHub and GitLab repos.

## Host map

Per repo, from the origin hostname: `WORKBENCH_SCM_HOSTS` first (`host=github|gitlab`, comma-separated, e.g. `git.example.com=gitlab`), then a hostname containing `github` means GitHub and one containing `gitlab` means GitLab. Anything else is local-only: the repo gets a `skipped` row `local-only: no PR/MR host for <origin>` and does not fail the run. A malformed `WORKBENCH_SCM_HOSTS` exits 2 naming the entry.

## Procedure

1. Confirm the branch is already pushed for each target repo (see git-worktrees-push).
2. For each repo, write a short description in your own words: what changed and why. The first non-empty line becomes the title of a new PR/MR.
3. Optionally decide a semver level (`patch`/`minor`/`major`) per repo for the push-CD release pipeline.
4. Run the script once:

   ```
   mise exec -- python3 ${CLAUDE_PLUGIN_ROOT}/skills/pullrequests-update/scripts/update.py --branch <branch> --repos repoA,repoB \
     --body repoA="<description for repoA>" \
     --body repoB="<description for repoB>" \
     --semver repoA=minor
   ```

5. Pass 1 creates a PR/MR (or edits the existing one) per repo. Pass 2 rewrites each body as your description plus a `Complementary PRs` (GitHub repo) or `Complementary MRs` (GitLab repo) section listing every other PR/MR of the run, on either host, then applies the semver label.
6. Relay the report (repo, status `created`/`updated`/`skipped`/`failed`, `<url> | <semver outcome>`). A failure does not stop other repos; the exit code is 1 if any repo or semver step failed.

## Arguments

- `--branch` the pushed branch; `--repos` comma-separated names of submodules under `code/`.
- `--body repo=text` one per repo; a missing body is a per-repo failure.
- `--semver repo=LEVEL` optional; labels `semver:<LEVEL>`, created if missing. An invalid level is a per-repo failure. An existing `semver:*` label is never changed (`semver skipped (has semver:<x>)`). No `--semver` shows `-`.
