---
name: pullrequests-list
description: "List open PRs or MRs for one code/ repo on GitHub or GitLab, classified by merge readiness: G ready, C conflicted, R checks failed. Use to list or review open PRs/MRs for a repo."
---

# pullrequests-list

Lists every open PR/MR of a single `code/` repo, classifies each by merge
readiness, and prints a table sorted oldest-to-newest. The host (GitHub or
GitLab) is detected from the repo's `origin`.

## Procedure

1. Invoke the script once, passing the repo name:

   ```
   mise exec -- python3 ${CLAUDE_PLUGIN_ROOT}/skills/pullrequests-list/scripts/list.py --repo <repo>
   ```

2. Read the table (`URL`, `ST`, `DESCRIPTION`). Codes, priority C over R over G:

   | Code | GitLab | GitHub |
   |---|---|---|
   | C | `detailed_merge_status=conflict` or `has_conflicts` | `mergeable=CONFLICTING` |
   | R | head pipeline `failed` or `canceled` | check rollup reduces to failed |
   | G | everything else | everything else |

3. DESCRIPTION is the PR `body` (GitHub) or MR `description` (GitLab),
   stripped and cut to 200 characters plus `...`. The title is not shown.

## Exit rule

- Exit 1 when any PR/MR is C or R; otherwise 0.
- No open PR/MR: an empty table, exit 0.
- Malformed `WORKBENCH_SCM_HOSTS` entry: usage error, exit 2.
- Local-only repo: prints `local-only: no PR/MR host for <origin>`, exit 0.
