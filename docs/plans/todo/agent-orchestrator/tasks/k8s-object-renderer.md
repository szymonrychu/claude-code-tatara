---
title: k8s object renderer
status: todo
repo: agent-orchestrator
value: "Turns a cluster spec into the exact Kubernetes objects of a working, peered, any-mcp-enabled agent cluster on shared CephFS."
files: [src/agent_orchestrator/k8s/__init__.py, src/agent_orchestrator/k8s/labels.py, src/agent_orchestrator/k8s/render.py, tests/test_render.py, tests/golden/cluster_two_peers.yaml, tests/golden/cluster_single.yaml]
verify: "uv run pytest tests/test_render.py -q && mise run lint"
depends_on: [clusters-repository, cluster-token-derivation]
owns: [k8s-render]
uses: [cluster-spec, cluster-tokens, settings, any-mcp-stdio-cli, agent-orchestrator-claude-secret]
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

# k8s object renderer

## Requirement

`render_cluster(cluster, settings, tokens) -> list[dict]` returns, in a stable order, the objects of design D6 for cluster `<slug>` in `settings.namespace`.

Every object carries the labels `agents.szymonrichert.pl/cluster=<slug>` and `app.kubernetes.io/managed-by=agent-orchestrator`.

Objects:
- PVC `agent-<slug>-workspace`: ReadWriteMany, storageClassName `settings.pvc_storage_class`, size `spec.pvc_size` or `settings.pvc_size`.
- Secret `agent-<slug>-ccw` with `CCW_AUTH_TOKEN` and `CCW_PEER_TOKEN`.
- ConfigMap `agent-<slug>-config` with `config.yaml` (below) and `any-mcp.yaml` (`spec.any_mcp_config`, else the file at `settings.any_mcp_config_file`, else `{}`).
- Service `agent-<slug>`: clusterIP None, publishNotReadyAddresses true, port 8080.
- StatefulSet `agent-<slug>`:
  - replicas, podManagementPolicy Parallel, serviceName
  - imagePullSecrets `[settings.image_pull_secret]`
  - runAsUser and fsGroup 1000
  - image `spec.image` or `settings.agent_image`
  - env: POD_NAME from fieldRef; `CCW_PEER_URL=http://$(POD_NAME).agent-<slug>.<ns>.svc.<domain>:8080`; CCW_* from the Secret; `CLAUDE_CODE_OAUTH_TOKEN` from Secret `settings.claude_secret_name` key `CLAUDE_CODE_OAUTH_TOKEN`; spec.env
  - probes /healthz (liveness) and /readyz (readiness)
  - terminationGracePeriodSeconds `settings.agent_termination_grace_seconds`
  - resources from spec
  - mounts: PVC subPath `<spec.workdir>` at /workdir; PVC `subPathExpr: sessions/$(POD_NAME)` at /sessions; emptyDir at /opt/mise; ConfigMap at /etc/ccw (config.yaml) and /etc/any-mcp (any-mcp.yaml)
- A pod-template annotation holds a hash of the ConfigMap data, so a config change rolls the pods.

The rendered `config.yaml` (D8):
- server.auth_token `${CCW_AUTH_TOKEN}`
- paths workdir_root /workdir, sessions_root /sessions
- claude.env: claude_code_oauth_token `${CLAUDE_CODE_OAUTH_TOKEN}`, disable_autoupdater true, claude_autocompact_pct_override (spec.auto_compact_pct or settings.default_auto_compact_pct)
- claude.model and claude.effort when set
- claude.mcp_servers.any-mcp: type stdio, command /opt/any-mcp/bin/any-mcp, args `[--config, /etc/any-mcp/any-mcp.yaml]`
- sessions: max_sessions 1, resume_on_start true, idle_timeout_seconds 0, ask_user_question deny
- limits.shutdown_timeout_seconds below the grace period
- when spec.peers: peers enabled, name `${POD_NAME}`, advertise_url `${CCW_PEER_URL}`, token `${CCW_PEER_TOKEN}`, static = the URL of every ordinal 0..replicas-1

Also `labels.py`: `cluster_labels(slug)`, `selector(slug)`, `object_names(slug)`.

## Acceptance conditions

- AC1: a 2-replica peered cluster renders exactly the golden objects [evidence: test:tests/test_render.py::test_golden_two_replicas_with_peers]
- AC2: a single-replica cluster without peers renders exactly its golden objects and no peers block [evidence: test:tests/test_render.py::test_golden_single_without_peers]
- AC3: the rendered config.yaml loads with claude_code_wrapper.config.load_config after env interpolation [evidence: test:tests/test_render.py::test_rendered_ccw_config_validates]
- AC4: every object carries both labels [evidence: test:tests/test_render.py::test_all_objects_labelled]
- AC5: sessions mount uses subPathExpr sessions/$(POD_NAME) and workdir is shared [evidence: test:tests/test_render.py::test_sessions_subpathexpr_per_pod]
- AC6: peers.static lists the URL of every ordinal [evidence: test:tests/test_render.py::test_peer_static_urls_cover_every_ordinal]
- AC7: pods pull with regcred and read the OAuth token from the shared Secret [evidence: test:tests/test_render.py::test_pull_secret_and_oauth_secret_ref]
- AC8: config.yaml registers any-mcp as a stdio MCP server with the mounted config [evidence: test:tests/test_render.py::test_any_mcp_server_entry]
- AC9: a ConfigMap change changes the pod-template hash annotation [evidence: test:tests/test_render.py::test_config_hash_rolls_pods]

## Files

- `src/agent_orchestrator/k8s/__init__.py`
- `src/agent_orchestrator/k8s/labels.py`
- `src/agent_orchestrator/k8s/render.py`
- `tests/test_render.py`
- `tests/golden/cluster_two_peers.yaml`
- `tests/golden/cluster_single.yaml`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
