---
title: check jobs
status: todo
repo: agent-orchestrator
value: "Runs verification commands against a cluster's shared workspace, which is how the bench scores correctness."
files: [src/agent_orchestrator/reconciler/checks.py, src/agent_orchestrator/reconciler/loop.py, tests/fakes/fake_kube.py, tests/test_checks.py]
verify: "uv run pytest tests/test_checks.py -q && mise run lint"
depends_on: [session-bootstrap]
owns: []
uses: [queue-sql, kube-api, agents-repo, k8s-render]
model: ""
estimate: 6
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

# check jobs

## Requirement

Checks as Jobs (D10).

The reconciler claims queued checks (`claim_check`) and creates Job `agent-<slug>-check-<id>`. The Job has:
- the cluster labels plus `agents.szymonrichert.pl/check=<id>`
- image `settings.check_image` (default the agent image), `imagePullSecrets: [regcred]`
- `command: [sh, -c, <command>]`, workingDir /workdir
- the cluster PVC mounted at /workdir (subPath `spec.workdir`), runAsUser and fsGroup 1000
- backoffLimit 0, activeDeadlineSeconds 1800, ttlSecondsAfterFinished 3600

Each tick reads running checks:
- A succeeded Job is recorded with `passed`, exit code 0 and the pod log tail (last 200 lines, at most 16 KiB).
- A failed Job is recorded with `failed`, the container's exit code and the tail.
- A Job past its deadline is recorded with `failed`, exit_code null and log_tail `timeout`.

For a deleting cluster, queued checks are cancelled (`cancel_checks`) and its Jobs are deleted with its other objects.

## Acceptance conditions

- AC1: a check renders a Job mounting the cluster PVC at /workdir [evidence: test:tests/test_checks.py::test_job_rendered_with_pvc_mount]
- AC2: a succeeded Job records passed, exit 0 and the log tail [evidence: test:tests/test_checks.py::test_success_records_exit_and_log]
- AC3: a failed Job records the container exit code [evidence: test:tests/test_checks.py::test_failure_records_exit_code]
- AC4: a deadline-exceeded Job records failed with timeout [evidence: test:tests/test_checks.py::test_timeout_marks_failed]
- AC5: discarding a cluster cancels its queued checks and deletes its Jobs [evidence: test:tests/test_checks.py::test_deleting_cluster_cancels_checks]

## Files

- `src/agent_orchestrator/reconciler/checks.py`
- `src/agent_orchestrator/reconciler/loop.py`
- `tests/fakes/fake_kube.py`
- `tests/test_checks.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
