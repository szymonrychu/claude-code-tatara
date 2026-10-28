---
title: orch-security-hardening
status: todo
repo: agents-orchestrator
value: Claude credentials never land in S3 and CI cannot run a moving third-party action with push secrets
files: [src/agents_orchestrator/reconciler/cache.py, src/agents_orchestrator/spec.py, tests/test_cache_jobs_render.py, tests/test_cache_archive.py, .github/workflows/ci.yaml, MEMORY.md]
verify: uv run pytest tests/test_cache_jobs_render.py tests/test_cache_archive.py -q
depends_on: [orch-sessions-save-unconverged]
model: sonnet
review: ""
verified_head: ""
points: 3
expected_minutes: 6
expected_tokens: 950968
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# orch-security-hardening

## Requirement

Two security findings of the epic review (.scratchpad/session-loss/review/security.md), my call to fix before merge:
1. The /sessions backup (`reconciler/cache.py`, sessions target renders `CACHE_EXCLUDE` as `[]`) archives every file under /sessions into S3, including Claude credential files (for example `<ses>/config/.credentials.json`). Exclude credential files from the sessions archive (a fixed exclude list for the sessions target, fnmatch globs on the relative path, covering `.credentials.json` at any depth). First read how agent pods get their Claude credentials (wrapper settings, chart, secret mounts) and confirm a restore without those files leaves the pod authenticated; if credentials exist only inside /sessions, stop and return that as a question instead of excluding. Test first.
2. `.github/workflows/ci.yaml` uses `regclient/actions/regctl-installer@main` (about lines 38, 99, 137) in jobs that hold the Harbor push secrets. Pin it to the same commit SHA agents-web uses (`dd58ad94f76adb73d8ac1bf75ed25f01545d5b32`, comment with the date) and add a top-level `permissions: contents: read` block (raise per job only where a job needs more; read each job first).
Record both decisions in MEMORY.md with the date and why.

## Acceptance conditions

- AC1: the sessions save Job renders a CACHE_EXCLUDE that excludes credential files at any depth [evidence: test:tests/test_cache_jobs_render.py::test_sessions_save_excludes_credentials]
- AC2: archive.pack with the sessions exclude list leaves out a nested config/.credentials.json and keeps transcripts [evidence: test:tests/test_cache_archive.py::test_sessions_exclude_drops_credentials]
- AC3: no workflow step uses a moving regctl-installer ref [evidence: command:! grep -n "regctl-installer@main" .github/workflows/ci.yaml]
- AC4: the workflow declares top-level permissions [evidence: command:grep -q "^permissions:" .github/workflows/ci.yaml]
- AC5: MEMORY.md records the credential exclude [evidence: command:grep -q "credentials" MEMORY.md]

## Files

- `src/agents_orchestrator/reconciler/cache.py`
- `src/agents_orchestrator/spec.py`
- `tests/test_cache_jobs_render.py`
- `tests/test_cache_archive.py`
- `.github/workflows/ci.yaml`
- `MEMORY.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
