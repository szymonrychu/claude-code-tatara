---
title: apply guard and hygiene
status: done
repo: agents-helmfile
value: apply can only ever hit the homelab cluster and nothing sensitive gets committed or traced
files: [mise.toml, .gitignore, .hook.sh, tests/test_mise_tasks.py, tests/test_repo_hygiene.py, tests/test_helmfile_base.py]
verify: "uv run pytest tests/test_mise_tasks.py tests/test_repo_hygiene.py tests/test_helmfile_base.py -q -p no:cacheprovider && mise run lint"
depends_on: [helmfile-base, hook-missing-namespace, mise-tasks, scaffold-repo, smoke-script]
owns: []
uses: []
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agents-helmfile-apply-guard-and-hygiene/agents-helmfile
branch: agents-helmfile-apply-guard-and-hygiene
verified_head: cdc29e5562c37f5dcf2af56b8d35d46d3c1f3f11
run: agents-helmfile
provides: []
acs_for_audit: []
process_gaps: []
fork_point: 6b8fa017763c2ea130a9a77556e7e14e88cdfb7e
---

# apply guard and hygiene

## Requirement

Security review findings: (medium) mise.toml apply/diff kube-context guard only checks that a context exists; compare the current context to EXPECTED_KUBE_CONTEXT (default kubernetes-admin@kubernetes, the homelab context) and fail on mismatch. (low) .gitignore adds kubeconfig*, *.kubeconfig, .kube/, *.pem, *.key, *.dec*, *.decrypted*. (low) .hook.sh run_hook_script drops bash -x so secret-handling hook scripts are never traced. (low) pin the 'latest' tools in mise.toml (uv, jq, gitleaks) to exact versions and pin the helm-diff plugin version.

## Acceptance conditions

- AC1: apply and diff refuse a kube context other than EXPECTED_KUBE_CONTEXT [evidence: test:tests/test_mise_tasks.py::test_kube_context_guard_rejects_unexpected_context]
- AC2: .gitignore covers kube and decrypted material [evidence: test:tests/test_repo_hygiene.py::test_gitignore_covers_kube_and_decrypted_files]
- AC3: the hook never runs scripts with xtrace [evidence: test:tests/test_helmfile_base.py::test_hook_scripts_not_traced]
- AC4: no tool in mise.toml is latest and helm-diff is pinned [evidence: test:tests/test_mise_tasks.py::test_tools_pinned]

## Files

- `mise.toml`
- `.gitignore`
- `.hook.sh`
- `tests/test_mise_tasks.py`
- `tests/test_repo_hygiene.py`
- `tests/test_helmfile_base.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

The security findings are closed and pinned by tests.

What is true and observable when the task is done.

## Steps

- Write the failing tests; run red.
- Implement; run green.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
