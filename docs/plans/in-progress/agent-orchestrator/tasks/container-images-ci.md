---
title: container images ci
status: in-progress
repo: agent-orchestrator
value: "Every main commit yields a pushed, immutable orchestrator image, with the agent image, the wrapper config validation and the any-mcp pin all on one wrapper sha and one any-mcp tag."
files: [.github/workflows/ci.yaml, tests/test_images.py, pyproject.toml, uv.lock, README.md]
verify: "uv run pytest tests/test_images.py -q && mise run lint"
depends_on: [spa-serving-and-dockerfile, k8s-object-renderer, settings-model]
owns: [agent-orchestrator-image]
uses: [settings, any-mcp-release, wrapper-idle-since, wrapper-context-surface, wrapper-user-message-event, wrapper-peers-view, wrapper-on-start-hook]
model: ""
estimate: 6
estimate_by: formula
actual: ""
actual_roles: ""
review: full
worktree: /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/agent-orchestrator-container-images-ci/agent-orchestrator
branch: agent-orchestrator-container-images-ci
verified_head: ""
run: ""
provides: []
---

# container images ci

## Requirement

The image CI (D16, D17). Only the orchestrator image is built here: there is no derived agent image, and the agent pods run the claude-code-wrapper image named by `ORCH_AGENT_IMAGE` (user answer Q8). This task depends on epics claude-code-wrapper-orchestr and any-mcp.

Pins, kept equal by tests:
- The claude-code-wrapper dev dependency in pyproject.toml and uv.lock is pinned by git to the commit of the claude-code-wrapper main merge that contains epic claude-code-wrapper-orchestr, the onStart hook included. The renderer's config validation therefore tests the wrapper the agents run.
- README `## Images` names the recommended agent image `harbor.szymonrichert.pl/containers/claude-code-wrapper:<sha7>` of that same commit. That is the value the chart's `agentImage` and agents-helmfile set.
- The `any-mcp` runtime dependency (added by scaffold for spec validation, D22) in pyproject.toml and uv.lock is pinned to the same release tag as the `any_mcp_ref` default in settings.py (contract any-mcp-release, planned v0.1.0).

`.github/workflows/ci.yaml`:
- Job `images` builds the orchestrator image from the root Dockerfile.
- Smoke step: `docker run --rm <orchestrator> --help`.
- On push to main only, it logs in to Harbor with the secrets HARBOR_USERNAME and HARBOR_PASSWORD and pushes `harbor.szymonrichert.pl/containers/agent-orchestrator:<sha7>` with regctl, as claude-code-wrapper's build.yaml does.
- Pull requests build and smoke-test without pushing.
- No job builds or pushes an agent image.

README `## Images` names the orchestrator image and its tag rule, the recommended agent image, and that any-mcp reaches agent pods through the rendered onStart hook, not through an image.

## Acceptance conditions

- AC1: CI builds, smoke-tests and on main only pushes exactly one image, containers/agent-orchestrator:<sha7> [evidence: test:tests/test_images.py::test_ci_pushes_orchestrator_image_on_main_only]
- AC2: the ccw dev dependency pins the same wrapper commit as the agent image README names [evidence: test:tests/test_images.py::test_ccw_dev_dependency_matches_agent_image_sha]
- AC3: no derived agent image exists: the repo tracks no agent-image/ directory and ci.yaml builds no agent image [evidence: test:tests/test_images.py::test_no_derived_agent_image]
- AC4: the pyproject any-mcp dependency pins the same tag as the settings any_mcp_ref default [evidence: test:tests/test_images.py::test_pyproject_any_mcp_pin_matches_settings_ref]
- AC5: the renderer's config validation, hooks.onStart included, passes on the re-pinned wrapper [evidence: command:uv run pytest tests/test_render.py -q]
- AC6: the orchestrator image builds and answers --help [evidence: command:docker build -t agent-orchestrator:test . && docker run --rm agent-orchestrator:test --help]
- AC7: README documents the images [evidence: doc-section:README.md#Images]

## Files

- `.github/workflows/ci.yaml`
- `tests/test_images.py`
- `pyproject.toml`
- `uv.lock`
- `README.md`

## Interfaces

- image name: contract `agent-orchestrator-image` (consumed by this repo's chart default `image.repository` and by epic agents-helmfile)
- README `## Images`: the recommended agent image tag

## Expected outcome

Main CI pushes `containers/agent-orchestrator:<sha7>`. The renderer's ccw config validation runs against the same wrapper commit the agent pods run, and any-mcp has one pinned tag.

## Steps

- Write tests/test_images.py with the four named tests. They parse ci.yaml with yaml.safe_load, parse pyproject.toml and README.md, and check `git ls-files agent-image`. Run them and expect failures.
- Write the CI job, re-pin both dependencies (`uv lock`) and write the README section.
- Rerun `uv run pytest tests/test_images.py -q` and expect `4 passed`.
- Run AC5 and AC6, then `mise run lint`.

## Notes

Get the wrapper sha with `git -C ../claude-code-wrapper rev-parse origin/main` after epic claude-code-wrapper-orchestr merges. The any-mcp tag is the one in contract any-mcp-release; confirm it with `git ls-remote --tags https://github.com/szymonrychu/any-mcp`.

The repo secrets are set by the orchestrator at origin creation. Local AC6 needs no Harbor access, because the root Dockerfile builds from public bases.

The no-derived-image test pins a removal against an earlier plan, so it asserts on `git ls-files`, never on the filesystem.

- 2026-10-22 amended at the gate: derived agent image dropped (Q8). any-mcp is installed by the onStart script of k8s-object-renderer.
