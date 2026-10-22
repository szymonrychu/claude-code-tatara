---
title: Release
status: todo
repo: any-mcp
value: "any-mcp is a standard pip package and tag v0.1.0 is a verified, installable release"
files: [CHANGELOG.md, .github/workflows/release.yml, tests/test_release.py]
verify: "uv run --frozen pytest tests/test_release.py -q && mise run lint"
depends_on: [docs-readme-concepts]
owns: []
uses: [any-mcp-cli]
model: sonnet
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

# Release

## Requirement

Make any-mcp a standard installable package with release tooling for the pinned git tag `v0.1.0` (design D16, D18). Publishing to a package index is not part of this task (claude-code-wrapper does not publish either).

- `CHANGELOG.md` with a top entry `## v0.1.0` listing what v0.1.0 delivers (plugin API, discovery, transports, OpenAPI plugin, harness, examples, docs).
- `.github/workflows/release.yml`: on push of tags `v*.*.*`; fails unless the tag equals `v` plus the `pyproject.toml` version; runs `mise run lint` and `mise run test`; builds the wheel with `uv build --wheel` and installs it into a clean venv; installs `any-mcp @ git+https://github.com/${{ github.repository }}@${{ github.ref_name }}` into another clean venv; runs `any-mcp --version` and `any-mcp --help` from both; creates a GitHub release whose body is the CHANGELOG section of the tag.
- `tests/test_release.py`:
  - the versions agree: `pyproject.toml`, `importlib.metadata.version("any-mcp")`, the top CHANGELOG entry and the README pinned install tag;
  - the workflow has the trigger, tag check, wheel build, git install and smoke steps;
  - `uv build --wheel` into a temp dir, install the wheel into a fresh venv (`uv venv` plus `uv pip install --python <venv>`), and `<venv>/bin/any-mcp --version` prints `any-mcp 0.1.0`;
  - `pip install` of `any-mcp @ git+file://<repo>@HEAD` into a fresh venv gives a working `any-mcp --help`;
  - `uv tool install <wheel>` with temporary `UV_TOOL_DIR` and `UV_TOOL_BIN_DIR` puts a working `any-mcp` on that bin dir (`--version` prints the version).

## Acceptance conditions

- AC1: pyproject, package metadata, the CHANGELOG top entry and the README pinned tag all say 0.1.0 [evidence: test:tests/test_release.py::test_versions_agree]
- AC2: the release workflow triggers on version tags, checks the tag, builds and installs the wheel, installs from the git tag, smoke-tests and publishes the GitHub release [evidence: test:tests/test_release.py::test_release_workflow_shape]
- AC3: a wheel built with uv build installs into a fresh venv and any-mcp --version prints any-mcp 0.1.0 [evidence: test:tests/test_release.py::test_wheel_installs_and_reports_version]
- AC4: installing from git+file at HEAD into a fresh venv gives a working any-mcp --help [evidence: test:tests/test_release.py::test_install_from_git_head]
- AC5: uv tool install of the wheel puts a working any-mcp on the tool bin dir [evidence: test:tests/test_release.py::test_uv_tool_install]
- AC6: the CHANGELOG entry describes every v0.1.0 deliverable in user terms [evidence: judgement]
- AC7: lint passes [evidence: command:mise run lint]

## Files

- `CHANGELOG.md`
- `.github/workflows/release.yml`
- `tests/test_release.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.
