---
title: helmfile smoke sessions
status: todo
repo: agents-helmfile
value: "the live smoke proves the renamed releases and session routes, and a guard keeps the names"
files: [scripts/smoke.sh, mise.toml, tests/test_smoke_script.py, tests/test_nomenclature.py, README.md, AGENTS.md]
verify: "uv run pytest -q tests/test_smoke_script.py tests/test_mise_tasks.py tests/test_nomenclature.py && mise run lint"
depends_on: [helmfile-consumers-rename]
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 14
expected_tokens: 895472
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# helmfile smoke sessions

## Requirement

Move the live smoke and the helmfile docs to the new names and guard the repo (design D1, D2, D12; contract `orch-sessions-api` as consumer). Paths are in code/agents-helmfile.

- `scripts/smoke.sh`: default release `agents-orchestrator` (port-forward `deploy/agents-orchestrator-api`, Services `agents-orchestrator`, `agents-orchestrator-agents`, `agents-orchestrator-services:8002`), routes `/api/v1/sessions...`, session wording in variables, logs and failure messages, label `agents.szymonrichert.pl/session=<slug>`, the leader and scale checks on the session routes; the wrapper's own session config dir check keeps its wording.
- `mise.toml`: the smoke task description says session.
- `tests/test_smoke_script.py` (test first): the fake API serves `/api/v1/sessions` only and the default routes name `agents-orchestrator`; every existing case keeps passing on the new names.
- `README.md`, `AGENTS.md`: releases, Secrets and the cutover in the new names; `MEMORY.md` is written by deploy-cutover.
- New `tests/test_nomenclature.py` (D12): every tracked file has no `/cluster/i` naming the orchestrator's unit and no `agent[-_]orchestrator`, allowlisting the Kubernetes/CNPG/kind phrases (the cnpg `cluster:` values key, `db-cluster`, `cluster-info`, `cluster-issuer`, `cluster.local`), the dated-history files, and the old db release kept hibernated (`agent-orchestrator-db` in helmfile.yaml.gotmpl, `values/agent-orchestrator-db/`, the import source names in `values/agents-orchestrator-db/common.yaml`, tests/test_db_release.py), each allowlist entry commented with its reason.

## Acceptance conditions

- AC1: the smoke drives the session routes and the renamed releases [evidence: test:tests/test_smoke_script.py::test_happy_path_exits_zero_and_cleans_up]
- AC2: no tracked file names the unit cluster or the old project outside the commented allowlist [evidence: command:uv run pytest -q tests/test_nomenclature.py]
- AC3: the smoke suite and lint pass [evidence: command:uv run pytest -q tests/test_smoke_script.py tests/test_mise_tasks.py && mise run lint]

## Files

- `scripts/smoke.sh`
- `mise.toml`
- `tests/test_smoke_script.py`
- `tests/test_nomenclature.py`
- `README.md`
- `AGENTS.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
