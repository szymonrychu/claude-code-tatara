---
title: common orchestrator client
status: todo
repo: agents-common
value: trigger services call the orchestrator through one tested client and test against one fake
files: [src/agents_common/orchestrator.py, src/agents_common/fake_orchestrator.py, tests/test_orchestrator_client.py]
verify: "uv run pytest tests/test_orchestrator_client.py -q && uv run ruff check . && uv run ruff format --check ."
depends_on: [common-scaffold]
owns: [agents-common-orchestrator-client, agents-common-fake-orchestrator]
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

# common orchestrator client

## Requirement

An async HTTP client of the orchestrator's service API and a fake orchestrator for tests (design D1, D8, D10). Paths are in code/agents-common.

- `orchestrator.py`: `OrchestratorClient(base_url, token, timeout=15)` over `httpx.AsyncClient`, sending `Authorization: Bearer <token>`. Methods, each mapping one route of the orchestrator's service port (D10): `list_presets()`, `get_preset(id)`, `create_cluster(preset_id, slug) -> Cluster` (`POST /api/v1/clusters {preset_id, slug}`; on 409 `conflict` it lists `GET /api/v1/clusters` and returns the cluster with that slug, so create is idempotent), `get_cluster(id)`, `list_messages(cluster_id)`, `post_message(cluster_id, text) -> Message`, `get_message(id) -> Message`. Typed results (`Preset`, `Cluster`, `Message` with `turn`) as pydantic models holding only the fields used. Errors: `OrchestratorError(status, code, message)` from the orchestrator's error body; `NotFound` for 404; transport errors and 5xx raise `OrchestratorUnavailable` (retryable). No retry loop inside the client.
- `fake_orchestrator.py`: `FakeOrchestrator` holding presets, clusters and messages in memory, exposing `app` (a Starlette app with exactly those routes, the same status codes and error bodies `{error: {code, message}}`, 401 without the configured bearer token, 409 on a taken slug) and helpers `add_preset`, `complete_turn(message_id, final_text)`, `fail_turn(message_id)`, `fail_next(route, status)`; usable in-process through `httpx.ASGITransport` and as a server for e2e.
- `tests/test_orchestrator_client.py` against the fake: every method; 409 resolves the existing cluster; 401 surfaces as OrchestratorError(401); 5xx and a connection error raise OrchestratorUnavailable; the bearer header is sent.

## Acceptance conditions

- AC1: every client method round-trips against the fake with the bearer header [evidence: command:uv run pytest tests/test_orchestrator_client.py -q -k roundtrip]
- AC2: create_cluster on a taken slug returns the existing cluster [evidence: command:uv run pytest tests/test_orchestrator_client.py -q -k conflict]
- AC3: 401, 404, 5xx and transport errors map to the typed errors [evidence: command:uv run pytest tests/test_orchestrator_client.py -q -k error]
- AC4: the fake serves exactly the service-port routes of design D10 used by the client [evidence: symbol:src/agents_common/fake_orchestrator.py::FakeOrchestrator]
- AC5: lint passes [evidence: command:uv run ruff check . && uv run ruff format --check .]

## Files

- `src/agents_common/orchestrator.py`
- `src/agents_common/fake_orchestrator.py`
- `tests/test_orchestrator_client.py`

## Interfaces

- Owns `agents-common-orchestrator-client`: `agents_common.orchestrator.{OrchestratorClient, Preset, Cluster, Message, OrchestratorError, NotFound, OrchestratorUnavailable}`.
- Owns `agents-common-fake-orchestrator`: `agents_common.fake_orchestrator.FakeOrchestrator`.
- Mirrors orchestrator routes (contracts `orch-presets-api`, `orch-cluster-create-api`, `orch-service-tokens`): `POST /api/v1/clusters {preset_id, slug}` 201 ClusterView, 409 `conflict`; `POST /api/v1/clusters/{id}/messages {text}` 202 `{message_id, status}`; `GET /api/v1/messages/{id}` MessageView with `status` and `turn{status, completed_at, final_text}`.

## Expected outcome

Services talk to the orchestrator only through this client; every test uses the fake.

## Steps

- Red: write the tests against the fake's expected behaviour; run: import errors.
- Green: write the fake, then the client; tests pass. Run the verify command.

## Notes

- Field names from `code/agent-orchestrator/src/agent_orchestrator/api/schemas.py` (ClusterView, MessageView, PresetView) and `api/messages.py:post_message`, `api/clusters.py:create_cluster` (409 at L186). Slug rules: DNS-1123 label, at most 40 characters (`spec.py:validate_slug`).
