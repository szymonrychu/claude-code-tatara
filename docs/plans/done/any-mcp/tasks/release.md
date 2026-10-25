---
title: Release
status: done
repo: any-mcp
value: "any-mcp is a standard pip package and tag v0.1.0 is a verified, installable release"
files: [CHANGELOG.md, .github/workflows/release.yml, tests/test_release.py]
verify: "uv run --frozen pytest tests/test_release.py -q && mise run lint"
depends_on: [docs-readme-concepts, input-required-adapter, config-model]
model: sonnet
review: ""
verified_head: 9e90317fc354518208d8eaac0f3ecd00e00f3710
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: 9
actual_tokens: 661202
actual_roles: "impl 4, review 5"
actual_role_tokens: "impl 400898, review 260304"
---

# Release

## Requirement

Make any-mcp a standard installable package with release tooling for the pinned git tag `v0.1.0` (design D16, D18). Publishing to a package index is not part of this task (claude-code-wrapper does not publish either).

- `CHANGELOG.md` with a top entry `## v0.1.0` listing what v0.1.0 delivers (plugin API, optional input-required hook, discovery, transports, OpenAPI plugin, harness, examples, docs).
- `.github/workflows/release.yml`: on push of tags `v*.*.*`; fails unless the tag equals `v` plus the `pyproject.toml` version; runs `mise run lint` and `mise run test`; builds the wheel with `uv build --wheel` and installs it into a clean venv; installs `any-mcp @ git+https://github.com/${{ github.repository }}@${{ github.ref_name }}` into another clean venv; runs `any-mcp --version` and `any-mcp --help` from both; creates a GitHub release whose body is the CHANGELOG section of the tag.
- `tests/test_release.py`:
  - the versions agree: `pyproject.toml`, `importlib.metadata.version("any-mcp")`, the top CHANGELOG entry and the README pinned install tag;
  - the workflow has the trigger, tag check, wheel build, git install and smoke steps;
  - `uv build --wheel` into a temp dir, install the wheel into a fresh venv (`uv venv` plus `uv pip install --python <venv>`), and `<venv>/bin/any-mcp --version` prints `any-mcp 0.1.0`;
  - `pip install` of `any-mcp @ git+file://<repo>@HEAD` into a fresh venv gives a working `any-mcp --help`;
  - `uv tool install <wheel>` with temporary `UV_TOOL_DIR` and `UV_TOOL_BIN_DIR` puts a working `any-mcp` on that bin dir (`--version` prints the version).
  - the orchestrator onStart path (design D20): `python -m venv <tmp>/any-mcp` then `<tmp>/any-mcp/bin/pip install "any-mcp @ git+file://<repo>@HEAD"` (stdlib venv and plain pip, no uv), write `any-mcp.yaml` with `json.dumps` (a `plugins` entry for an installed example plugin), then run `<tmp>/any-mcp/bin/any-mcp --config <file> --help` and `<tmp>/any-mcp/bin/python -c` loading the file with `any_mcp.config.load_config`; both succeed.
  - the README and the CHANGELOG state the exact install line the onStart script uses: `python -m venv /opt/any-mcp && /opt/any-mcp/bin/pip install "any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.1.0"`, the console script path `/opt/any-mcp/bin/any-mcp`, and that the config file may be JSON.

## Acceptance conditions

- AC1: pyproject, package metadata, the CHANGELOG top entry and the README pinned tag all say 0.1.0 [evidence: test:tests/test_release.py::test_versions_agree]
- AC2: the release workflow triggers on version tags, checks the tag, builds and installs the wheel, installs from the git tag, smoke-tests and publishes the GitHub release [evidence: test:tests/test_release.py::test_release_workflow_shape]
- AC3: a wheel built with uv build installs into a fresh venv and any-mcp --version prints any-mcp 0.1.0 [evidence: test:tests/test_release.py::test_wheel_installs_and_reports_version]
- AC4: installing from git+file at HEAD into a fresh venv gives a working any-mcp --help [evidence: test:tests/test_release.py::test_install_from_git_head]
- AC5: uv tool install of the wheel puts a working any-mcp on the tool bin dir [evidence: test:tests/test_release.py::test_uv_tool_install]
- AC6a: the plain venv plus pip install from git at HEAD works as the onStart script would run it, with a json.dumps-written config that the installed any-mcp loads [evidence: test:tests/test_release.py::test_onstart_install_path]
- AC6b: the README and the CHANGELOG state the pinned onStart install line, the /opt/any-mcp/bin/any-mcp path and the JSON config option [evidence: test:tests/test_release.py::test_pinned_install_line_documented]
- AC6: the CHANGELOG entry describes every v0.1.0 deliverable in user terms [evidence: judgement]
- AC7: lint passes [evidence: command:mise run lint]

## Files

- `CHANGELOG.md`
- `.github/workflows/release.yml`
- `tests/test_release.py`

## Interfaces

Cross-epic contract `any-mcp-install` (consumer: the agent-orchestrator onStart hook script): the exact pinned install line and config format above. Cross-epic contract `any-mcp-release`: tag `v0.1.0` on `main` of `github.com/szymonrychu/any-mcp`, installable with `pip install "any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.1.0"`, console script `any-mcp` (consumer: the agent-orchestrator agent image).

## Expected outcome

Every install form in the README works from a standard wheel, and pushing tag `v0.1.0` produces a verified GitHub release.

## Steps

- Write `tests/test_release.py`; run `uv run --frozen pytest tests/test_release.py -q`; expect failures on the missing CHANGELOG and workflow.
- Write `CHANGELOG.md` and `.github/workflows/release.yml`; rerun (all pass), then `mise run lint`.

## Notes

The git install test needs the work committed (it installs `HEAD`); commit before running it. The install tests use the network for dependencies; reuse the uv cache. The tag itself is pushed by the orchestrator after the epic closes on `main` (an irreversible operation listed at the gate); it never moves once pushed.

- 2026-10-23 run any-mcp: dependency-failed on docs-readme-concepts, input-required-adapter
