---
title: container images ci
status: todo
repo: agent-orchestrator
value: "Every main commit yields pushed, immutable orchestrator and agent images, and every new session gets any-mcp preinstalled."
files: [agent-image/Dockerfile, .github/workflows/ci.yaml, tests/test_images.py, pyproject.toml, uv.lock, README.md]
verify: "uv run pytest tests/test_images.py -q && mise run lint"
depends_on: [spa-serving-and-dockerfile, k8s-object-renderer]
owns: [agent-image, agent-orchestrator-image]
uses: [any-mcp-stdio-cli, wrapper-idle-since, wrapper-context-surface, wrapper-user-message-event, wrapper-peers-view]
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

## Files

- `agent-image/Dockerfile`
- `.github/workflows/ci.yaml`
- `tests/test_images.py`
- `pyproject.toml`
- `uv.lock`
- `README.md`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
