---
title: agent token env render
status: todo
repo: agent-orchestrator
value: every agent pod holds a cluster-scoped credential and the orchestrator URL
files: [src/agent_orchestrator/tokens.py, src/agent_orchestrator/k8s/render.py, src/agent_orchestrator/spec.py, tests/test_tokens.py, tests/test_render.py, tests/test_spec_hive.py]
verify: "uv run pytest tests/test_tokens.py tests/test_render.py tests/test_spec_hive.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [spec-cap-static, agent-port-listener]
owns: [orch-agent-env]
uses: [orch-spec-cap-static, orch-agent-port]
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

# agent token env render

## Requirement

Foundation part F3, credential and env (D1, X1).

- `tokens.py`: `ClusterTokens.agent = HMAC(master_key, "agent:<cluster_id>")`, masked in repr like the others.
- `k8s/render.py`: the cluster Secret `agent-<slug>-ccw` gains `ORCH_AGENT_TOKEN`; the container env gains `ORCH_AGENT_TOKEN` (secretKeyRef), `ORCH_CLUSTER_ID` (the cluster id) and, when `settings.agent_api_url` is set, `ORCH_AGENT_URL`; `claude.passthrough_env` becomes `sorted(spec.env keys + ORCH_AGENT_TOKEN, ORCH_AGENT_URL, ORCH_CLUSTER_ID, POD_NAME)` so the any-mcp stdio child of Claude sees them. Rendered for every cluster, never depending on the live replica count. When `agent_api_url` is unset, `ORCH_AGENT_URL` is omitted and the reconciler logs one warning per cluster (my call: dev setups without the agents Service keep working).
- `spec.py`: `ORCH_*` joins the reserved `spec.env` key patterns, so a user cannot override the agent credential.

## Acceptance conditions

- AC1: the agent token is derived with purpose agent, differs from auth and peer, is stable per cluster and masked in repr [evidence: test:tests/test_tokens.py::test_agent_token_purpose]
- AC2: the cluster Secret carries ORCH_AGENT_TOKEN and the container env maps it plus ORCH_CLUSTER_ID and ORCH_AGENT_URL [evidence: test:tests/test_render.py::test_agent_credential_env]
- AC3: passthrough_env includes ORCH_AGENT_TOKEN, ORCH_AGENT_URL, ORCH_CLUSTER_ID and POD_NAME next to the spec env keys [evidence: test:tests/test_render.py::test_passthrough_includes_agent_env]
- AC4: without agent_api_url the env omits ORCH_AGENT_URL and render still succeeds [evidence: test:tests/test_render.py::test_no_agent_url_omits_env]
- AC5: spec.env keys starting with ORCH_ are rejected [evidence: test:tests/test_spec_hive.py::test_orch_env_reserved]
- AC6: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agent_orchestrator/tokens.py`
- `src/agent_orchestrator/k8s/render.py`
- `src/agent_orchestrator/spec.py`
- `tests/test_tokens.py`
- `tests/test_render.py`
- `tests/test_spec_hive.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
