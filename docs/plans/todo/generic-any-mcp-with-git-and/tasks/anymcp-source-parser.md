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

- `src/any_mcp/sources.py:Source`, a frozen dataclass: `raw: str`, `kind: Literal["local", "git"]`, `path: str | None` (local only, verbatim), `url: str | None` (git only, without `git::`, shorthand expanded to `https://github.com/<owner>/<repo>.git`), `subdir: str` (`""` when none), `ref: str | None`.
- `src/any_mcp/sources.py:parse_source(text: str) -> Source`, raising `any_mcp.errors.ConfigError` whose message starts with `plugin source '<text>': `.
- Consumers: `any_mcp.install` (task anymcp-source-installer), `any_mcp.config` (task anymcp-source-plugin-loading), agents-orchestrator `spec.py` (task orch-any-mcp-sources-spec) imports `parse_source` and reads `kind`, `url`, `subdir`.

## Expected outcome

Every accepted form of design D1 parses into a `Source`, and every refused form fails with one `ConfigError` line that says what is wrong.

## Steps

- Red: write `tests/test_sources.py` with the eight acceptance tests as parametrised accept and reject tables; run `uv run --frozen pytest -q tests/test_sources.py`: fails on the missing module.
- Green: write `src/any_mcp/sources.py`; run the task's verify: passes.

## Notes

- Rulings and their pin tests: local wins only on `./`, `../`, `/` prefixes (test_local_sources); the first `//` after the scheme's `://` splits the subdir (test_git_sources, with a URL whose path has no `//`); `?ref=` is parsed after the subdir (test_git_sources); a shorthand keeps a given `.git` suffix and adds none twice (test_github_shorthand); `depth` is named in the error (test_unsupported_query_refused).
- Pure string work: no I/O, no git call. Use `urllib.parse` only where it does not normalise the URL in surprising ways; the url field is the user's URL minus `git::` and the `//subdir?query` tail.
- The orchestrator restricts further (https only); this parser stays generic (https, ssh, file).
- Never the word "cluster" in new text.
