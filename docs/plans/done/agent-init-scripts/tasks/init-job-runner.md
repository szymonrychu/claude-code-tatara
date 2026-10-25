---
title: init job runner
status: done
repo: agent-orchestrator
value: init scripts run exactly once per cluster and the outcome is recorded
files: [src/agent_orchestrator/reconciler/init.py, src/agent_orchestrator/reconciler/loop.py, src/agent_orchestrator/reconciler/checks.py, tests/test_init_runner.py, README.md, MEMORY.md]
verify: "uv run pytest tests/test_init_runner.py tests/test_reconciler.py tests/test_checks.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [init-scripts-spec-field]
owns: [orch-cluster-status-init, orch-init-workdir-files]
uses: [orch-cluster-spec-init-scripts, orch-render-hash-invariant]
model: opus
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-init-scripts-init-job-runner/agent-orchestrator
branch: agent-init-scripts-init-job-runner
verified_head: 36d4fed9a4856bed44ceec5026b58c52fabe83bc
run: agent-init-scripts
provides: [init-gate, init-sh-render]
acs_for_audit: []
process_gaps: ["The independent verification report said 'Worktree not clean at verification', but `git status --short` in the worktree printed nothing at review time. The two verification findings only say the top-level pass/exit were not captured. I re-ran the targeted pytest, ruff check and ruff format --check myself: 50 tests passed, 'All checks passed!', '130 files already formatted'."]
fork_point: 1bf5c9636de7f32da8e68faf1291b0622da5386b
---

# init job runner

## Requirement

Run a cluster's init scripts exactly once per cluster, as one Kubernetes Job, and record the run in `clusters.status.init` (user decisions C1, C2; design D2, D3). Paths are in code/agent-orchestrator.

New module `src/agent_orchestrator/reconciler/init.py` with `InitRunner(pool, kube, settings)` and `async step(cluster) -> InitGate`, called from `ReconcileLoop._converge` in `reconciler/loop.py` after the apply and prune and before `_bootstrap_sessions`.

State, written only by the reconciler through the existing merging `_write_status` (other status keys survive): `status.init = {state, scripts_hash, started_at, finished_at, exit_code, log_tail, reason, job}` (contract orch-cluster-status-init). `state` is one of `skipped`, `running`, `succeeded`, `failed`.
- First converge of a cluster with no `status.init`: empty `spec.init_scripts` writes `{state: skipped, scripts_hash: init_scripts_hash([])}` and nothing else happens; a non-empty list writes `{state: running, started_at, scripts_hash: init_scripts_hash(spec.init_scripts), job: null}` and then creates the Job. Once `status.init` exists the runner never starts another Job for that cluster, whatever later edits do to `spec.init_scripts` (a cluster created with no scripts and edited later still never runs them; edits apply to the next cluster).
- Crash safety (pattern of `reconciler/checks.py`): the state is written before the create; `job` is set to the Job name only after the create succeeds. On a later tick with state `running`: Job absent and `job` null means create it (crashed between the write and the create); Job absent and `job` set means `failed`, reason `job_missing`; a Job without the cluster labels means `failed`, reason `foreign_object`; a create error means `failed`, reason `job_create_failed: <msg>` cut to 2000 chars.
- Outcome: Job Complete gives `succeeded`, exit 0; Job Failed gives `failed` with the container exit code; DeadlineExceeded or no outcome `DEADLINE_SECONDS + DEADLINE_GRACE_SECONDS` after `started_at` gives `failed`, reason `timeout`. `log_tail` is the pod log tail (200 lines, 16 KiB, the checks limits). `finished_at` is set. After recording the outcome the runner deletes the Job (background propagation).
- Job `agent-<slug>-init` (name helper in init.py, built with `k8s/labels.prefix`): the cluster labels plus `agents.szymonrichert.pl/init: "true"`; image `spec.image or settings.agent_image`; `restartPolicy: Never`, `backoffLimit: 0`, `activeDeadlineSeconds: 1800`, no `ttlSecondsAfterFinished`; `securityContext` runAsUser 1000 / fsGroup 1000; the cluster PVC with `workdir_mount(spec)` and `workingDir: workdir_path(spec)`; env from `spec.env`; resources as the agent container; `imagePullSecrets` when `settings.image_pull_secret` is set. Command `["sh", "-c", WRAPPER, "agent-init", INIT_SH]`, where INIT_SH is a header comment (cluster slug, "run once at cluster start by agent-orchestrator; edits through the init scripts API or the orchestrator_init_scripts_edit tool apply to the next cluster") followed by each script under a `# --- script <n> ---` line, and WRAPPER creates `$INIT_DIR` (`spec.INIT_DIR`), writes `.agent-init/.gitignore` containing `*`, writes `$1` to `.agent-init/init.sh`, runs it with `sh -eu` with stdout and stderr to `.agent-init/init.log`, prints the log and exits with the script's exit code. Files on the shared workdir (contract orch-init-workdir-files): `<workdir_path>/.agent-init/init.sh`, `init.log`, `.gitignore`.
- Gate: `_bootstrap_sessions` is skipped while `status.init` is absent or `running`; then phase is `pending` and the message carries `init running`. On `failed` sessions start, phase is `degraded` and the message carries `init failed` (with the exit code or reason). `skipped` and `succeeded` change nothing. The init Job pod is never an agent (`_observe` already ignores non-ordinal pod names; the test pins it).
- A converge never prunes the init Job; a discard deletes it (`DISCARD_ORDER` already deletes labelled Jobs; the test pins it).
- Reuse the checks helpers `_condition`, `_tail`, `_exit_code` and the limits constants by importing them from `reconciler/checks.py` (rename to public names there if ruff or clarity asks; keep checks behaviour unchanged).
- Docs: README `### Reconcile loop` gains the init step and states, README `## Data model` row for `clusters` mentions `status.init`; MEMORY.md dated 2026-10-24 entry: init scripts run once per cluster as a reconciler Job recorded in `status.init` (why: status has one writer that survives restarts; a pod marker races under Parallel pods), pod-local installs by a script do not reach agent pods (only the shared workdir is shared), failure starts sessions degraded instead of blocking.

Interfaces: `reconciler/init.py::InitRunner`, `reconciler/init.py::init_job_name`, `reconciler/init.py::render_init_job`; status shape above.

Steps: write `tests/test_init_runner.py` against `tests/fakes/fake_kube.py` (first tick creates once, second tick does not, skipped never runs after an edit, crash between write and create, job_missing, foreign_object, timeout, success and failure outcomes with log tail and exit code, Job deleted after the outcome, gate holds sessions while running and releases on failure, discard deletes the init Job) and see it fail; then implement.

## Acceptance conditions

- AC1: a cluster with scripts gets exactly one Job agent-<slug>-init across repeated ticks, and status.init goes running then succeeded with exit_code 0, log_tail and finished_at [evidence: test:tests/test_init_runner.py::test_runs_once_and_records_success]
- AC2: a failed script records failed with the container exit code and log tail, sessions start, phase degraded and the message names init failed [evidence: test:tests/test_init_runner.py::test_failure_records_and_releases_sessions]
- AC3: a cluster first seen with no scripts records skipped and never creates a Job, also after its init_scripts are edited to a non-empty list [evidence: test:tests/test_init_runner.py::test_skipped_never_runs_after_edit]
- AC4: an edit after a run never starts a second Job [evidence: test:tests/test_init_runner.py::test_edit_after_run_never_reruns]
- AC5: a crash between the running write and the create creates the Job on the next tick; a vanished created Job records job_missing; an unlabelled Job records foreign_object; an overdue Job records timeout [evidence: test:tests/test_init_runner.py::test_crash_and_failure_reasons]
- AC6: no session is bootstrapped while init is absent or running, and phase is pending with init running in the message [evidence: test:tests/test_init_runner.py::test_sessions_held_while_running]
- AC7: the Job writes .agent-init/init.sh, init.log and a .gitignore of * in the workdir, runs as uid 1000 with the agent image, spec.env and the PVC mount [evidence: test:tests/test_init_runner.py::test_render_init_job]
- AC8: the init Job is deleted after its outcome is recorded, is not pruned by a converge, is deleted by a discard, and its pod never becomes an agent row [evidence: test:tests/test_init_runner.py::test_job_lifecycle_and_not_an_agent]
- AC9: existing reconciler and checks tests still pass [evidence: command:uv run pytest tests/test_reconciler.py tests/test_checks.py -q]
- AC10: README documents the init step and status.init, MEMORY.md has the dated decision [evidence: command:grep -q "status.init" README.md && grep -q "init" MEMORY.md && grep -q "2026-10-24" MEMORY.md]
- AC11: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/reconciler/init.py`
- `src/agent_orchestrator/reconciler/loop.py`
- `src/agent_orchestrator/reconciler/checks.py`
- `tests/test_init_runner.py`
- `README.md`
- `MEMORY.md`

## Interfaces

- `reconciler/init.py::InitRunner.step`, `init_job_name`, `render_init_job`.
- `clusters.status.init` shape (contract orch-cluster-status-init) and `<workdir>/.agent-init/` files (contract orch-init-workdir-files).

## Expected outcome

A new cluster with scripts runs them once in one Job, records the outcome in `status.init`, and its agents get sessions after the run; edits, restarts and scaling never run them again.

## Steps

- Red: write `tests/test_init_runner.py` on `tests/fakes/fake_kube.py`; `uv run pytest tests/test_init_runner.py -q` fails on the missing module.
- Green: implement `reconciler/init.py`, call it from `_converge` before `_bootstrap_sessions`, gate the bootstrap; run the verify command: all pass.
- Docs: README Reconcile loop and Data model, MEMORY.md dated entry.

## Notes

- `_write_status` merges keys (`reconciler/loop.py:500-520`); write `{"init": {...}}` through it so the discard hook keys survive.
- `_observe` skips pods whose name suffix is not an ordinal (`loop.py:282`), so `agent-<slug>-init-xxxxx` never becomes an agent.
- `DISCARD_ORDER` already deletes labelled Jobs; `PRUNE_ORDER` has no Job, so converge never prunes it.
