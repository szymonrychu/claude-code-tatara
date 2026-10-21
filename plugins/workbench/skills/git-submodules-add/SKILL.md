---
name: git-submodules-add
description: "Add git repos as submodules under code/, auto-detecting each remote's default branch. Use to add, import, or vendor a repo into code/."
---

Adds git repositories as submodules under `code/`, tracking each remote's
actual default branch (not a hardcoded `main`). Idempotent: re-running with
a URL that is already present under `code/` is a no-op skip, not an error.

## Procedure

1. Collect the git URL(s) to add from the user's request (SSH or HTTPS, one
   or more).
2. Run:
   ```
   mise exec -- python3 ${CLAUDE_PLUGIN_ROOT}/skills/git-submodules-add/scripts/add.py <url> [<url> ...]
   ```
3. Read the printed report (`REPO STATUS DETAIL` table):
   - `added` - submodule created at `code/<name>`, tracking the resolved
     default branch (shown in DETAIL as `branch=<name>`).
   - `skipped` - `code/<name>` already exists or is already a submodule.
     Nothing changed.
   - `failed` - the remote's default branch could not be resolved, or
     `git submodule add` itself failed (DETAIL has the git error).
4. The script exits non-zero iff any URL failed; the run still adds every
   URL that succeeded (failures never abort the others). Report failures to
   the user with the DETAIL text; do not retry silently.
5. The submodule name is derived from the URL's last path segment (trailing
   `.git` and slash stripped), e.g. `git@github.com:org/repo.git` -> `repo`.
