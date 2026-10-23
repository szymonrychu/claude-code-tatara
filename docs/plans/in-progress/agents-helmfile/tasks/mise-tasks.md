---
title: mise tasks
status: in-progress
repo: agents-helmfile
value: "One command each to diff and apply the namespace locally, guarded by lint and tests."
files: [mise.toml, README.md, tests/test_mise_tasks.py]
verify: "uv run pytest tests/test_mise_tasks.py -q && mise run lint"
depends_on: [helmfile-base]
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# mise tasks

## Requirement

Add the operator tasks and the README.

- `mise.toml` tasks `diff`: `helmfile -f helmfile.yaml.gotmpl diff --detailed-exitcode --suppress-secrets` (exit 2 means changes; the task documents it and passes it through); `apply`: `helmfile -f helmfile.yaml.gotmpl apply --suppress-secrets` (hook-driven regcred and raw manifests, rollback on failure from helmDefaults). Both load `.env` through the mise `[env]` block, never call scripts/bootstrap-secrets.sh, and accept `--selector name=<release>` as a task argument. `apply` has `depends = ["lint", "test"]` so a broken tree cannot be applied. A `kube-context` guard task (a `depends` of diff and apply) fails unless `kubectl config current-context` is non-empty and `kubectl version` reaches the API, printing only the context name.
- `README.md`: what the repo is, the namespace, releases and host, that the ingress is LAN-only without auth, `.env` handling (copied from the infrastructure helmfile, ignored, never printed), the secrets bootstrap, and a `## Operating` section covering `mise run lint|test|diff|apply|smoke`; applies are manual and local.
- `tests/test_mise_tasks.py` parses mise.toml (tomllib) and asserts the tasks diff, apply, lint and test exist, diff uses `--detailed-exitcode` and `--suppress-secrets`, apply depends on lint and test, no task redirects a decrypt to a file, and the README names every task.

## Acceptance conditions

- AC1: diff and apply tasks exist with the detailed exit code and suppressed secrets [evidence: command:uv run pytest tests/test_mise_tasks.py -q -k diff_and_apply_tasks]
- AC2: apply depends on lint and test [evidence: command:uv run pytest tests/test_mise_tasks.py -q -k apply_depends_on_lint_and_test]
- AC3: no task decrypts secrets to disk [evidence: command:uv run pytest tests/test_mise_tasks.py -q -k no_task_decrypts_to_disk]
- AC4: README documents the repo and every mise task [evidence: doc-section:README.md#Operating]
- AC5: mise lists the tasks [evidence: command:mise tasks ls | grep -q '^diff' && mise tasks ls | grep -q '^apply']

## Files

- `mise.toml`
- `README.md`
- `tests/test_mise_tasks.py`

## Interfaces

none

## Expected outcome

`mise run diff` and `mise run apply` exist, are guarded, and the README explains the repo.

## Steps

- Write tests/test_mise_tasks.py; run it; expect failures.
- Add the tasks to mise.toml and write README.md.
- Rerun the test and `mise run lint`; expect `passed`.

## Notes

Do not run apply or diff against the cluster in this task. mise.toml was created by scaffold-repo: only add tasks.
