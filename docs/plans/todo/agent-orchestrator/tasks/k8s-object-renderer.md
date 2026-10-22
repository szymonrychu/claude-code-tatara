---
title: k8s object renderer
status: todo
repo: agent-orchestrator
value: "Turns a cluster spec into the exact Kubernetes objects of a working, peered, any-mcp-enabled agent cluster on shared CephFS."
files: [src/agent_orchestrator/k8s/__init__.py, src/agent_orchestrator/k8s/labels.py, src/agent_orchestrator/k8s/render.py, src/agent_orchestrator/k8s/on_start.py, tests/test_render.py, tests/golden/cluster_two_peers.yaml, tests/golden/cluster_single.yaml]
verify: "uv run pytest tests/test_render.py -q && mise run lint"
depends_on: [clusters-repository, cluster-token-derivation]
owns: [k8s-render]
uses: [cluster-spec, cluster-tokens, settings, any-mcp-cli, any-mcp-config, any-mcp-install, wrapper-on-start-hook]
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

`render_cluster(cluster, settings, tokens) -> list[dict]` returns, in a stable order, the objects of design D6 for cluster `<slug>` in `settings.namespace`. This is the one namespace `agents`, shared with the orchestrator's own objects; there is no clusters namespace (D26).

Every object carries the labels `agents.szymonrichert.pl/cluster=<slug>` and `app.kubernetes.io/managed-by=agent-orchestrator`.

Objects:
- PVC `agent-<slug>-workspace`: ReadWriteMany, storageClassName `settings.pvc_storage_class`, size `spec.pvc_size` or `settings.pvc_size`.
- Secret `agent-<slug>-ccw` with `CCW_AUTH_TOKEN` and `CCW_PEER_TOKEN`.
- ConfigMap `agent-<slug>-config` with two keys:
  - `config.yaml` (below)
  - `on-start.sh`, the onStart script (below)
- Service `agent-<slug>`: clusterIP None, publishNotReadyAddresses true, port 8080.
- StatefulSet `agent-<slug>`:
  - replicas, podManagementPolicy Parallel, serviceName
  - imagePullSecrets `[settings.image_pull_secret]`, omitted when the setting is empty
  - runAsUser and fsGroup 1000
  - image `spec.image` or `settings.agent_image`, the claude-code-wrapper image itself (no derived agent image, D16)
  - env:
    - POD_NAME from fieldRef
    - `CCW_PEER_URL=http://$(POD_NAME).agent-<slug>.<namespace>.svc.<domain>:8080`
    - CCW_* from the Secret
    - `CLAUDE_CODE_OAUTH_TOKEN` from Secret `settings.claude_secret_name`, key `CLAUDE_CODE_OAUTH_TOKEN` (rendered by the chart)
    - spec.env
  - probes:
    - a startupProbe on /healthz with periodSeconds 5 and `failureThreshold = ceil(settings.on_start_timeout_seconds / 5) + 12`, because the wrapper does not listen until onStart finishes
    - /healthz (liveness) and /readyz (readiness)
  - terminationGracePeriodSeconds `settings.agent_termination_grace_seconds`
  - resources from spec
  - mounts:
    - PVC subPath `workdir` (a constant, the shared workspace root) at /workdir. The session workdir is `<spec.workdir>`, so sessions and check Jobs both work in `/workdir/<spec.workdir>` (D27).
    - PVC `subPathExpr: sessions/$(POD_NAME)` at /sessions
    - emptyDirs at /opt/mise and /opt/any-mcp
    - the ConfigMap at /etc/ccw (`config.yaml` and `on-start.sh`)
- A pod-template annotation holds a hash of the ConfigMap data, so a config change rolls the pods.

The rendered `config.yaml` (D8):
- server.auth_token `${CCW_AUTH_TOKEN}`
- paths workdir_root /workdir, sessions_root /sessions
- claude:
  - `passthrough_env`: the sorted names of `spec.env`, so the accepted variables reach the claude child (its environment is an allow-list, config.py:189; D22)
  - `env`: claude_code_oauth_token `${CLAUDE_CODE_OAUTH_TOKEN}`, disable_autoupdater true, claude_autocompact_pct_override (spec.auto_compact_pct or settings.default_auto_compact_pct)
  - `model` and `effort`, when set
  - `permissions.deny: [EnterPlanMode, ExitPlanMode, AskUserQuestion]`. The wrapper default (config.py:148-150) plus AskUserQuestion, so the tool is disabled (D8, user answer Q11).
  - `mcp_servers.any-mcp`: type stdio, command /opt/any-mcp/bin/any-mcp, args `[--config, /opt/any-mcp/etc/any-mcp.yaml]`
- hooks.onStart: `[{type: command, run: "sh /etc/ccw/on-start.sh", blocking: true, on_error: deny, timeout_seconds: settings.on_start_timeout_seconds}]` (contract wrapper-on-start-hook)
- sessions: max_sessions 1, resume_on_start true, idle_timeout_seconds 0, ask_user_question deny
- prompts.system_append: the constant `ASK_IN_WRITING_PROMPT`. When the agent needs a decision or information from the user, it asks in writing in its reply, as a numbered list of questions, each followed by its recommended answer, worded so that "yes" accepts it. It never waits on an interactive question tool.
- limits.shutdown_timeout_seconds below the grace period
- when spec.peers: peers enabled, name `${POD_NAME}`, advertise_url `${CCW_PEER_URL}`, token `${CCW_PEER_TOKEN}`, static = the URL of every ordinal 0..replicas-1

`on_start.py:render_on_start(spec, settings) -> str` renders the onStart script (D16, contract any-mcp-install), POSIX sh with `set -eu`:
1. When `/opt/any-mcp/.ref` does not contain `settings.any_mcp_ref`, it removes `/opt/any-mcp/*`, runs `python3 -m venv /opt/any-mcp` and `/opt/any-mcp/bin/pip install --no-cache-dir "any-mcp @ git+<settings.any_mcp_repo>@<settings.any_mcp_ref>"`, then writes the ref to `.ref`.
2. It writes the any-mcp config as JSON to `/opt/any-mcp/etc/any-mcp.yaml`, through a quoted heredoc (no shell expansion). The config is `spec.any_mcp_config`, else the file at `settings.any_mcp_config_file`, else `{}`. Rendering raises when the JSON contains the heredoc delimiter line.
3. It runs `/opt/any-mcp/bin/any-mcp --help >/dev/null` as a smoke check.

A rerun with the same ref skips the install and rewrites only the config.

Also `labels.py`: `cluster_labels(slug)`, `selector(slug)`, `object_names(slug)`. Every object name starts with the reserved prefix `agent-<slug>`, and `object_names` asserts it (D26).

`workdir_path(spec) -> str` returns `/workdir/<spec.workdir>`, and `workdir_mount(spec) -> dict` returns the shared volumeMount. The StatefulSet, the session bootstrap (workdir name `spec.workdir`) and the check Jobs all use them (D27).

## Acceptance conditions

- AC1: a 2-replica peered cluster renders exactly the golden objects [evidence: test:tests/test_render.py::test_golden_two_replicas_with_peers]
- AC2: a single-replica cluster without peers renders exactly its golden objects and no peers block [evidence: test:tests/test_render.py::test_golden_single_without_peers]
- AC3: the rendered config.yaml, including hooks.onStart, loads with claude_code_wrapper.config.load_config after env interpolation [evidence: test:tests/test_render.py::test_rendered_ccw_config_validates]
- AC4: every object carries both labels [evidence: test:tests/test_render.py::test_all_objects_labelled]
- AC5: sessions mount uses subPathExpr sessions/$(POD_NAME) and workdir is shared [evidence: test:tests/test_render.py::test_sessions_subpathexpr_per_pod]
- AC6: peers.static lists the URL of every ordinal [evidence: test:tests/test_render.py::test_peer_static_urls_cover_every_ordinal]
- AC7: pods pull with regcred, render no imagePullSecrets when the setting is empty, and read the OAuth token from the configured Secret [evidence: test:tests/test_render.py::test_pull_secret_and_oauth_secret_ref]
- AC8: config.yaml registers any-mcp as a stdio MCP server reading /opt/any-mcp/etc/any-mcp.yaml, and /opt/any-mcp is an emptyDir [evidence: test:tests/test_render.py::test_any_mcp_server_entry]
- AC9: a ConfigMap change, including an any-mcp config change, changes the pod-template hash annotation [evidence: test:tests/test_render.py::test_config_hash_rolls_pods]
- AC10: every object is in settings.namespace, including the peer URLs [evidence: test:tests/test_render.py::test_all_objects_in_namespace]
- AC11: claude.passthrough_env lists the spec.env names and the config validates with load_config [evidence: test:tests/test_render.py::test_passthrough_env_lists_spec_env_names]
- AC12: workdir_path matches the shared mount and the session workdir name [evidence: test:tests/test_render.py::test_workdir_path_matches_mount_and_session_workdir]
- AC13: every object name uses the reserved agent-<slug> prefix [evidence: test:tests/test_render.py::test_every_object_name_uses_reserved_prefix]
- AC14: hooks.onStart runs the mounted on-start.sh blocking with on_error deny and the settings timeout, and the startupProbe covers that timeout [evidence: test:tests/test_render.py::test_on_start_hook_and_startup_probe]
- AC15: run under sh with a stub python3 and pip on PATH, the script installs from git+<repo>@<ref>, writes the config as parseable JSON, and skips the install on a second run with the same ref [evidence: test:tests/test_render.py::test_on_start_script_installs_once_and_writes_json_config]
- AC16: a config containing the heredoc delimiter line is refused [evidence: test:tests/test_render.py::test_on_start_refuses_delimiter_in_config]
- AC17: AskUserQuestion is disabled: sessions.ask_user_question is deny and claude.permissions.deny lists AskUserQuestion, EnterPlanMode and ExitPlanMode [evidence: test:tests/test_render.py::test_ask_user_question_disabled]
- AC18: prompts.system_append carries the ask-in-writing instruction (numbered questions, each with a recommended answer) [evidence: test:tests/test_render.py::test_system_append_asks_in_writing]

## Files

- `src/agent_orchestrator/k8s/__init__.py`
- `src/agent_orchestrator/k8s/labels.py`
- `src/agent_orchestrator/k8s/render.py`
- `src/agent_orchestrator/k8s/on_start.py`
- `tests/test_render.py`
- `tests/golden/cluster_two_peers.yaml`
- `tests/golden/cluster_single.yaml`

## Interfaces

- `agent_orchestrator.k8s.render:render_cluster`, `render_config_yaml`, `workdir_path`, `workdir_mount`, `ASK_IN_WRITING_PROMPT` (contract `k8s-render`)
- `agent_orchestrator.k8s.on_start:render_on_start(spec, settings) -> str`, `ANY_MCP_DIR = "/opt/any-mcp"`
- `agent_orchestrator.k8s.labels:cluster_labels`, `selector`, `object_names`, `MANAGED_BY`, `CLUSTER_LABEL`

## Expected outcome

Given a cluster row, the orchestrator produces the objects of D6, a wrapper config the pinned wrapper accepts, and an onStart script that leaves `/opt/any-mcp/bin/any-mcp` and its config in place before any session starts.

## Steps

- Write tests/test_render.py and the two golden YAML files. Run `uv run pytest tests/test_render.py -q` and expect failures.
  - AC15 runs the rendered script with `sh` in a tmp dir. `ANY_MCP_DIR` is overridable for the test, and stub `python3` and `pip` scripts on PATH record their argv.
- Implement labels.py, on_start.py and render.py.
- Rerun and expect `18 passed`, then run `mise run lint`.

## Notes

Config validation uses the ccw dev dependency pinned in pyproject: scaffold sets it, and container-images-ci re-pins it to the wrapper sha that contains epic claude-code-wrapper-orchestr. `hooks.onStart` validates only with that sha (contract wrapper-on-start-hook).

The wrapper globs sessions_root at startup, hence the per-pod subPathExpr (brief-wrapper Unknowns). A peers seed equal to self_url is skipped by the wrapper (peers.py:92), so listing every ordinal is correct.

The wrapper image is python:3.12-slim with git (claude-code-wrapper Dockerfile:18, :31), so `python3 -m venv` and the git pip install work in it. The any-mcp CLI flag `--config` follows contracts any-mcp-cli and any-mcp-config, and the config is written as JSON per any-mcp-install.

`ask_user_question: deny` refuses a call that slips through. `permissions.deny` removes the tool (config.py:148-150). `prompts.system_append` is appended to the session CLAUDE.md (claude-code-wrapper README.md:2600). Check the claude.env field name for CLAUDE_AUTOCOMPACT_PCT_OVERRIDE in code/claude-code-wrapper/src/claude_code_wrapper/claude_env.py.

- 2026-10-22 amended at the gate: single namespace (Q14), onStart install instead of a derived image (Q8), and AskUserQuestion disabled with an ask-in-writing prompt (Q11).
