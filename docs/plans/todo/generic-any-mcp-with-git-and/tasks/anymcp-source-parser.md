---
title: anymcp source parser
status: todo
repo: any-mcp
value: "one exact grammar for Terraform-like plugin sources, shared by any-mcp and the orchestrator"
files: [src/any_mcp/sources.py, tests/test_sources.py]
verify: "uv run --frozen pytest -q tests/test_sources.py && mise run lint"
depends_on: []
model: opus
review: ""
verified_head: ""
points: 3
expected_minutes: 7
expected_tokens: 977684
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# anymcp source parser

## Requirement

Goal G2 (epic README), verbatim: "any-mcp installs and loads plugins from Terraform-module-like sources: git repo with optional //subdir and ?ref=, and local directory paths." User request, verbatim: "Allow to install plugins using similar notation as terraform modules allow to." and "It must still be possible (when using pip installed any-mcp) to provide path to local dir, where plugin is defined (again- similar to terraform module handling)." Design D1: "`any_mcp.sources.parse_source(text) -> Source` is the only parser in Python (the orchestrator imports it)."

Scope (any-mcp), the grammar of design D1:
- Local: starts with `./`, `../` or `/`; the path is kept verbatim (resolution against a base directory is the installer's job). `//` and `?` are not allowed in a local source.
- Git: `git::<url>[//<subdir>][?ref=<ref>]`, `<url>` scheme `https`, `ssh` or `file`; scp-like `git@host:o/r` is refused with a hint to use `git::ssh://`.
- Shorthand: `github.com/<owner>/<repo>[//<subdir>][?ref=<ref>]` means `git::https://github.com/<owner>/<repo>.git...`.
- The query allows only `ref`; `depth`, `sshkey` or any other key is an error naming the key. An empty ref, a ref starting with `-`, or a ref outside `[A-Za-z0-9._/-]` or containing `..` is an error.
- Subdir: relative, no leading `/`, no empty or `..` segment.
- Anything else (bare `foo/bar`, `https://...` without `git::`, pip-style `git+https://...`) is an error that lists the accepted forms.
- New module `src/any_mcp/sources.py` with `Source` and `parse_source`; errors are `any_mcp.errors.ConfigError`; tests in `tests/test_sources.py`.

## Acceptance conditions

- ac1: ./x, ../x and /abs/x parse as kind local with the path kept verbatim, and a local source containing // or ? is refused [evidence: test:tests/test_sources.py::test_local_sources]
- ac2: git::https, git::ssh and git::file URLs parse into url, subdir and ref, with //sub/dir and ?ref= each optional [evidence: test:tests/test_sources.py::test_git_sources]
- ac3: github.com/owner/repo with optional //subdir and ?ref= parses as git with url https://github.com/owner/repo.git [evidence: test:tests/test_sources.py::test_github_shorthand]
- ac4: a query key other than ref (depth, sshkey, any other) is refused with a message naming the key [evidence: test:tests/test_sources.py::test_unsupported_query_refused]
- ac5: an empty ref, a ref starting with -, a ref with a character outside [A-Za-z0-9._/-] and a ref containing .. are refused [evidence: test:tests/test_sources.py::test_bad_refs_refused]
- ac6: a subdir with a leading /, an empty segment or a .. segment is refused [evidence: test:tests/test_sources.py::test_bad_subdirs_refused]
- ac7: bare owner/repo, https:// without git::, pip-style git+https://, scp-like git@host:o/r and git:: with a scheme other than https, ssh or file are refused with a message listing the accepted forms [evidence: test:tests/test_sources.py::test_unrecognised_forms_refused]
- ac8: lint passes [evidence: command:mise run lint]

## Files

- `src/any_mcp/sources.py`
- `tests/test_sources.py`

## Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

## Expected outcome

What is true and observable when the task is done.

## Steps

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

## Notes

Context the implementer needs: pitfalls, existing code to reuse, decisions already made.
