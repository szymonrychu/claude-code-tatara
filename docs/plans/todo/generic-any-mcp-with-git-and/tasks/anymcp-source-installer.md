---
title: anymcp source installer
status: todo
repo: any-mcp
value: any-mcp fetches git and local plugin sources safely and installs them as packages
files: [src/any_mcp/install.py, tests/test_install.py]
verify: "uv run --frozen pytest -q tests/test_install.py && mise run lint"
depends_on: [anymcp-source-parser]
model: opus
review: ""
verified_head: ""
points: 5
expected_minutes: 11
expected_tokens: 1694306
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# anymcp source installer

## Requirement

Goal G2 (epic README), verbatim: "any-mcp installs and loads plugins from Terraform-module-like sources: git repo with optional //subdir and ?ref=, and local directory paths." Non-goal, verbatim: "No per-plugin dependency isolation (separate venvs or processes)." Design D3, verbatim:

"`any_mcp.install` resolves a `Source` to an installed distribution:
- Git: a ref that is a full 40-hex SHA is fetched by SHA (`git fetch --depth 1 origin <sha>`), falling back to a `--filter=blob:none` fetch and checkout when the server refuses; a branch or tag (found by `git ls-remote`) is a shallow, blob-filtered clone of that ref; anything else (a short SHA) is a blob-filtered full clone then `git checkout`; no ref means the remote default branch. Sparse checkout limits the tree to the subdir. Every git call puts user values after `--`, runs with a timeout, and the resolved subdir must stay inside the checkout (symlinks resolved). A missing subdir is an error naming url, ref, resolved SHA and subdir.
- Cache dir `$ANY_MCP_CACHE_DIR`, default `<sys.prefix>/any-mcp-sources` (my call: the cache lives with the environment the packages are installed into, so a cache hit means installed). Key (normalised url, ref, subdir); a `manifest.json` records per key the source string, resolved SHA, checkout dir and distribution name. A SHA ref is cached forever; a branch, tag or default-branch entry is reused as is at startup and re-resolved only by an explicit install, like `terraform init -upgrade`.
- The source directory must hold a `pyproject.toml` with `[project].name`; it is installed with `<sys.executable> -m pip install` (git sources; local sources with `-e`, so they stay in place and edits show on restart, my call). Then `importlib.invalidate_caches()` and the distribution's `any_mcp.plugins` entry points are read; none is an error, several need `plugin` (D2).
- No `python_path` or `sys.path` insertion for sources."

Scope (any-mcp): new module `src/any_mcp/install.py`, tests in `tests/test_install.py`. Git runs for real against local repositories built in `tmp_path` (`file://` URLs); pip and the entry-point lookup are injectable so the unit tests do not install into the dev environment (the real pip path is proven end to end by task anymcp-source-plugin-loading).

## Acceptance conditions

- ac1: a git source at a tag and at a branch is shallow-cloned with only its subdir checked out, pip-installed from that subdir, and the manifest records the source string, resolved SHA, directory and distribution name [evidence: test:tests/test_install.py::test_git_tag_and_branch_install]
- ac2: a full 40-hex SHA ref is fetched by SHA and, when that fetch fails, through a blob-filtered fetch and checkout; a short SHA ref is checked out after a blob-filtered full clone; no ref installs the remote default branch [evidence: test:tests/test_install.py::test_sha_refs_and_fallback]
- ac3: a SHA source in the manifest is never fetched again, even on explicit install; a branch or tag source in the manifest is reused with no git call unless refresh is set, and with refresh is re-resolved and reinstalled when its SHA moved [evidence: test:tests/test_install.py::test_cache_rules]
- ac4: a local source resolves against base_dir and is pip-installed editable in place, never copied into the cache [evidence: test:tests/test_install.py::test_local_source_editable_in_place]
- ac5: a subdir missing at the resolved commit is an error naming url, ref, resolved SHA and subdir, and a subdir that resolves outside the checkout through a symlink is refused [evidence: test:tests/test_install.py::test_subdir_missing_or_escaping]
- ac6: a source directory without pyproject.toml or without [project].name, a distribution with no any_mcp.plugins entry point, and a failing pip install are ConfigErrors naming the source [evidence: test:tests/test_install.py::test_package_errors]
- ac7: every git and pip call is an argv list run without a shell and with a timeout, and every URL and path given to git follows -- [evidence: test:tests/test_install.py::test_subprocess_hygiene]
- ac8: the cache dir is $ANY_MCP_CACHE_DIR when set, else <sys.prefix>/any-mcp-sources [evidence: test:tests/test_install.py::test_cache_dir]
- ac9: lint passes [evidence: command:mise run lint]

## Files

- `src/any_mcp/install.py`
- `tests/test_install.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
