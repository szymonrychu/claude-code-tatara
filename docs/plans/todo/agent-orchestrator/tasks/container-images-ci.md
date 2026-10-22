---
title: container images ci
status: todo
repo: agent-orchestrator
value: "Every main commit yields pushed, immutable orchestrator and agent images, and every new session gets any-mcp preinstalled."
files: [agent-image/Dockerfile, .github/workflows/ci.yaml, tests/test_images.py, pyproject.toml, uv.lock, README.md]
verify: "uv run pytest tests/test_images.py -q && mise run lint"
depends_on: [spa-serving-and-dockerfile, k8s-object-renderer]
owns: [agent-image, agent-orchestrator-image]
uses: [any-mcp-cli, any-mcp-release, wrapper-idle-since, wrapper-context-surface, wrapper-user-message-event, wrapper-peers-view]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: ""
branch: ""
verified_head: ""
run: ""
provides: []
---

# container images ci

## Requirement

The agent image and the image CI (D16, D17). It depends on epics claude-code-wrapper-orchestr and any-mcp.

`agent-image/Dockerfile`:
- `ARG WRAPPER_SHA` defaults to the sha7 of the claude-code-wrapper main commit that contains the wrapper epic.
- `FROM harbor.szymonrichert.pl/containers/claude-code-wrapper:${WRAPPER_SHA}`.
- As root it creates `/opt/any-mcp` with `python -m venv` and installs `any-mcp @ git+https://github.com/szymonrychu/any-mcp@vX.Y.Z`, pinned through `ARG ANY_MCP_REF` to the any-mcp release tag.
- Then it returns to the wrapper's user `agent`.

Re-pin the `any-mcp` runtime dependency (added by scaffold for spec validation, D22) in pyproject.toml and uv.lock to the same release tag as `ANY_MCP_REF`.

Re-pin the claude-code-wrapper dev dependency in pyproject.toml and uv.lock to the same commit as WRAPPER_SHA, so the renderer's config validation tests the image's wrapper.

`.github/workflows/ci.yaml`:
- Job `images` builds both images (orchestrator from the root Dockerfile, agent from agent-image/).
- Smoke steps: `docker run --rm --entrypoint /opt/any-mcp/bin/any-mcp <agent> --help` and `docker run --rm <orchestrator> --help`.
- On push to main only, it logs in to Harbor with secrets HARBOR_USERNAME and HARBOR_PASSWORD. It then pushes `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>` and `containers/agent-orchestrator-agent:<sha7>` with regctl, as claude-code-wrapper's build.yaml does.
- Pull requests build and smoke-test without pushing.

README `## Images` names both images and the tag rule.

## Acceptance conditions

- AC1: the agent image builds from a pinned wrapper sha [evidence: test:tests/test_images.py::test_agent_image_from_pinned_wrapper_sha]
- AC2: the ccw dev dependency pins the same wrapper commit as the image [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_image_sha]
- AC3: any-mcp is installed into /opt/any-mcp from a pinned tag [evidence: test:tests/test_images.py::test_any_mcp_installed_in_isolated_venv_from_tag]
- AC4: CI pushes both images on main only [evidence: test:tests/test_images.py::test_ci_pushes_both_images_on_main_only]
- AC5: CI smoke-tests any-mcp in the agent image [evidence: test:tests/test_images.py::test_ci_smoke_tests_any_mcp]
- AC6: the agent image runs any-mcp [evidence: command:docker build -t agent-orchestrator-agent:test agent-image && docker run --rm --entrypoint /opt/any-mcp/bin/any-mcp agent-orchestrator-agent:test --help]
- AC7: the renderer's config validation passes on the re-pinned wrapper [evidence: command:uv run pytest tests/test_render.py -q]
- AC8: the pyproject any-mcp dependency pins the same tag as ANY_MCP_REF [evidence: test:tests/test_images.py::test_pyproject_any_mcp_pin_matches_image_tag]

## Files

- `agent-image/Dockerfile`
- `.github/workflows/ci.yaml`
- `tests/test_images.py`
- `pyproject.toml`
- `uv.lock`
- `README.md`

## Interfaces

- `agent-image/Dockerfile` (contract `agent-image`, consumed by kind-e2e and by the agents' StatefulSet via ORCH_AGENT_IMAGE)
- image names: contract `agent-orchestrator-image` (consumed by the deploy epic's chart)

## Expected outcome

Main CI pushes `containers/agent-orchestrator:<sha7>` and `containers/agent-orchestrator-agent:<sha7>`; the agent image runs any-mcp.

## Steps

- Write tests/test_images.py with the six named tests: static parsing of the Dockerfile, ci.yaml (yaml.safe_load) and pyproject. Run it; expect failures.
- Write the Dockerfile and CI job and re-pin the dependency (`uv lock`).
- Rerun `uv run pytest tests/test_images.py -q`; expect `6 passed`.
- Run AC6 and AC7, then `mise run lint`.

## Notes

Get the wrapper sha with `git -C ../claude-code-wrapper rev-parse origin/main` after epic claude-code-wrapper-orchestr merges. The any-mcp tag is the one in contract any-mcp-release (planned v0.1.0); confirm it with `git ls-remote --tags https://github.com/szymonrychu/any-mcp`. The isolated venv keeps any-mcp's dependencies (fastmcp, httpx) away from ccw's. A venv copied by an init container breaks its shebangs, hence the derived image. Local AC6 needs Harbor pull access (`docker login harbor.szymonrichert.pl`). The repo secrets are set by the orchestrator at origin creation.
