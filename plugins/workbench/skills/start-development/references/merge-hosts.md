# Merge hosts: pick the host per repo, act per RESOLVED line

Read from Phase 6 of `start-development`.

**Pick the host per repo, do not assume GitLab.** Check the remote before
dispatching anything:

```sh
git -C <repo> remote get-url origin
```

| Host | Update | Watch | Review loop |
|---|---|---|---|
| GitHub, GitLab | `pullrequests-update` | `pullrequests-watch` | `pullrequests-review-loop` on GitHub (GitHub-only), the GitLab review-discussion procedure below on GitLab |

The skills detect the host per repo from origin. The rule (D10): the
`WORKBENCH_SCM_HOSTS` map first (comma-separated `hostname=github|gitlab`,
exact hostname, case-insensitive), then the substring rule (hostname contains
`github` -> gh, `gitlab` -> glab), else local-only: no PR/MR exists, skip the
repo and say so. A workbench can hold several hosts, so this is per repo, not
once per run. Both hosts take the same arguments and emit the same `RESOLVED`
lines and `reviews=` field, so everything below reads the same either way.

## Act on each RESOLVED line as it arrives

The watch skill streams a `RESOLVED <repo> <status> <detail>` line the instant
each MR/PR reaches a terminal state. Never gate an action on all MRs having
resolved - they are independent, and batching lets the slowest set the latency
for every other. Per line:

- green + mergeable + `reviews=0 unresolved` - merge THAT MR now.
- `mergeable=conflict`, or behind target - rebase that worktree branch, push,
  re-watch that MR alone. This is work, not a wait.
- `reviews=<N> unresolved`, N > 0 - on GitHub run `pullrequests-review-loop`
  and judge each finding, never obey blindly. On GitLab follow the GitLab
  review-discussion procedure: read the unresolved count from
  `pullrequests-watch` `reviews=`, open each unresolved discussion in the MR UI
  or API, judge each one (fix the real ones, reply and resolve the wrong ones),
  push, and re-watch that MR alone. review-loop is GitHub-only. Record a
  finding only if it survives judgement.
- `checks=failed` - read the `reasons:` log tail, dispatch a fixer into that
  worktree, push, re-watch. Dispatch `scm-shepherd` when the cause is not in
  the tail.
- `no pipeline launched` - carry forward as-is.
