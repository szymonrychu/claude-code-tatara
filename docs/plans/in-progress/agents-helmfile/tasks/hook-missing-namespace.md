---
title: hook missing namespace
status: escalated
repo: agents-helmfile
value: a first deploy into an empty cluster works
files: [.hook.sh, tests/test_helmfile_base.py]
verify: "uv run pytest tests/test_helmfile_base.py -q && mise run lint"
depends_on: [helmfile-base]
owns: []
uses: []
model: ""
estimate: 5
estimate_by: formula
actual: ""
actual_roles: ""
review: ""
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agents-helmfile-hook-missing-namespace/agents-helmfile
branch: agents-helmfile-hook-missing-namespace
verified_head: 1fcd489ba971394e2d64fdca49f904ba730a3f11
run: agents-helmfile
provides: []
acs_for_audit: []
process_gaps: []
---

# hook missing namespace

## Requirement

Found by db-release on the live cluster: the .hook.sh prepare step runs kubectl diff on raw/regcred.pre.secrets.yaml and fails (rc=2, 'namespaces "agents" not found') before the namespace exists, so helmfile build/diff exits 1 on a fresh cluster. Make the prepare step tolerate a missing namespace: when namespace agents does not exist, skip the regcred diff (report it as to-be-created) and let presync create the namespace and apply regcred as today. Keep the rc>1 abort for every other kubectl failure. Pin it with a test that stubs kubectl to return NotFound for the namespace.

## Acceptance conditions

- AC1: prepare on a missing namespace does not fail and reports the namespace as to-be-created [evidence: test:tests/test_helmfile_base.py::test_prepare_tolerates_missing_namespace]
- AC2: any other kubectl failure still aborts [evidence: test:tests/test_helmfile_base.py::test_prepare_aborts_on_other_kubectl_errors]

## Files

- `.hook.sh`
- `tests/test_helmfile_base.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

helmfile build/diff/apply work against a cluster without namespace agents.

What is true and observable when the task is done.

## Steps

- Red: live helmfile build exits 1 (namespaces agents not found); write the stubbed-kubectl tests, see them fail.
- Make prepare tolerate a missing namespace; run green and the live build.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Ruling

- 2026-10-23 accepted: round-cap only on AC3, which could not pass before the release tasks land (planning error by the orchestrator); AC3 moved to db-release AC5. AC1/AC2 verified on 1fcd489: tests/test_helmfile_base.py passed, lint and gitleaks clean.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

## Notes

AC3 (live helmfile build on a cluster without namespace agents) moved to db-release AC5: it cannot pass before any release exists (orchestrator ruling 2026-10-23).
