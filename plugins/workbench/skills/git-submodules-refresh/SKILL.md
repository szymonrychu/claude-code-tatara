---
name: git-submodules-refresh
description: "Fast-forward code/ submodule checkouts to their tracked branch tip, reporting per-repo results. Use to update, sync, pull, or refresh submodules."
---

# git-submodules-refresh

Updates the workbench's `code/<repo>` submodule checkouts to the tip of
their tracked branch (`.gitmodules` `submodule.<name>.branch`, default
`main`). Fetches then fast-forwards only; never forces or rebases. Every
repo is handled independently and failures never abort the others.

## Procedure

1. Run the script from anywhere inside the workbench:
   ```
   mise exec -- bash ${CLAUDE_PLUGIN_ROOT}/skills/git-submodules-refresh/scripts/refresh.sh [--repos a,b,c]
   ```
   Omit `--repos` to refresh every submodule under `code/`. With it, pass a
   comma-separated list of submodule names.
2. Read the aggregate report the script prints to stdout: one row per repo
   with `REPO`, `STATUS` (`ok` or `failed`), and `DETAIL`.
   - `ok` with `<old-sha> -> <new-sha>` means it fast-forwarded.
   - `ok` with `up to date (<sha>)` means nothing changed.
   - `failed` means an unknown repo name, a fetch error, or a
     non-fast-forward (local commits diverged from the tracked branch);
     `DETAIL` carries the reason. Report it to the user rather than forcing
     anything.
3. The script exits non-zero iff any repo failed. Treat that as a signal to
   surface the failed repos to the user, not to retry automatically.

## Before refreshing, when the checkout's state is unknown

A fast-forward is safe, but it silently does nothing useful if a submodule is
detached, parked on a feature branch, or carrying commits that were never
pushed - and a `failed` row with "non-fast-forward" is the symptom, not the
diagnosis. When you do not already know the tree is clean, dispatch the
`submodule-auditor` agent first: it reports, per submodule, how far behind
upstream it is, unpushed commits, detached HEAD, a dirty worktree, and the
case that matters most - a submodule with no remote at all, where this disk
is the only copy. It is read-only and never moves a pointer.

Worth doing whenever a fix "isn't showing up", or before trusting any scan run
against the tree: a stale duplicate checkout of the same repos can exist next to the
canonical one, and a scan against it reports drift that upstream already
resolved.
