# Generic any-mcp with git and local plugin sources implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: opus)

### S1: anymcp source parser

- Status: done
- Files: `src/any_mcp/sources.py`, `tests/test_sources.py`
- Verify: `uv run --frozen pytest -q tests/test_sources.py && mise run lint`
- Verified head: bc5dfc73f2eabdcb8de6cfdabc2dd620312a19da

#### Requirement

Goal G2 (epic README), verbatim: "any-mcp installs and loads plugins from Terraform-module-like sources: git repo with optional //subdir and ?ref=, and local directory paths." User request, verbatim: "Allow to install plugins using similar notation as terraform modules allow to." and "It must still be possible (when using pip installed any-mcp) to provide path to local dir, where plugin is defined (again- similar to terraform module handling)." Design D1: "`any_mcp.sources.parse_source(text) -> Source` is the only parser in Python (the orchestrator imports it)."

Scope (any-mcp), the grammar of design D1:
- Local: starts with `./`, `../` or `/`; the path is kept verbatim (resolution against a base directory is the installer's job). `//` and `?` are not allowed in a local source.
- Git: `git::<url>[//<subdir>][?ref=<ref>]`, `<url>` scheme `https`, `ssh` or `file`; scp-like `git@host:o/r` is refused with a hint to use `git::ssh://`.
- Shorthand: `github.com/<owner>/<repo>[//<subdir>][?ref=<ref>]` means `git::https://github.com/<owner>/<repo>.git...`.
- The query allows only `ref`; `depth`, `sshkey` or any other key is an error naming the key. An empty ref, a ref starting with `-`, or a ref outside `[A-Za-z0-9._/-]` or containing `..` is an error.
- Subdir: relative, no leading `/`, no empty or `..` segment.
- Anything else (bare `foo/bar`, `https://...` without `git::`, pip-style `git+https://...`) is an error that lists the accepted forms.
- New module `src/any_mcp/sources.py` with `Source` and `parse_source`; errors are `any_mcp.errors.ConfigError`; tests in `tests/test_sources.py`.

#### Acceptance conditions

- ac1: ./x, ../x and /abs/x parse as kind local with the path kept verbatim, and a local source containing // or ? is refused [evidence: test:tests/test_sources.py::test_local_sources]
- ac2: git::https, git::ssh and git::file URLs parse into url, subdir and ref, with //sub/dir and ?ref= each optional [evidence: test:tests/test_sources.py::test_git_sources]
- ac3: github.com/owner/repo with optional //subdir and ?ref= parses as git with url https://github.com/owner/repo.git [evidence: test:tests/test_sources.py::test_github_shorthand]
- ac4: a query key other than ref (depth, sshkey, any other) is refused with a message naming the key [evidence: test:tests/test_sources.py::test_unsupported_query_refused]
- ac5: an empty ref, a ref starting with -, a ref with a character outside [A-Za-z0-9._/-] and a ref containing .. are refused [evidence: test:tests/test_sources.py::test_bad_refs_refused]
- ac6: a subdir with a leading /, an empty segment or a .. segment is refused [evidence: test:tests/test_sources.py::test_bad_subdirs_refused]
- ac7: bare owner/repo, https:// without git::, pip-style git+https://, scp-like git@host:o/r and git:: with a scheme other than https, ssh or file are refused with a message listing the accepted forms [evidence: test:tests/test_sources.py::test_unrecognised_forms_refused]
- ac8: lint passes [evidence: command:mise run lint]

#### Files

- `src/any_mcp/sources.py`
- `tests/test_sources.py`

#### Interfaces

- `src/any_mcp/sources.py:Source`, a frozen dataclass: `raw: str`, `kind: Literal["local", "git"]`, `path: str | None` (local only, verbatim), `url: str | None` (git only, without `git::`, shorthand expanded to `https://github.com/<owner>/<repo>.git`), `subdir: str` (`""` when none), `ref: str | None`.
- `src/any_mcp/sources.py:parse_source(text: str) -> Source`, raising `any_mcp.errors.ConfigError` whose message starts with `plugin source '<text>': `.
- Consumers: `any_mcp.install` (task anymcp-source-installer), `any_mcp.config` (task anymcp-source-plugin-loading), agents-orchestrator `spec.py` (task orch-any-mcp-sources-spec) imports `parse_source` and reads `kind`, `url`, `subdir`.

#### Expected outcome

Every accepted form of design D1 parses into a `Source`, and every refused form fails with one `ConfigError` line that says what is wrong.

#### Steps

- Red: write `tests/test_sources.py` with the eight acceptance tests as parametrised accept and reject tables; run `uv run --frozen pytest -q tests/test_sources.py`: fails on the missing module.
- Green: write `src/any_mcp/sources.py`; run the task's verify: passes.

#### Notes

- Rulings and their pin tests: local wins only on `./`, `../`, `/` prefixes (test_local_sources); the first `//` after the scheme's `://` splits the subdir (test_git_sources, with a URL whose path has no `//`); `?ref=` is parsed after the subdir (test_git_sources); a shorthand keeps a given `.git` suffix and adds none twice (test_github_shorthand); `depth` is named in the error (test_unsupported_query_refused).
- Pure string work: no I/O, no git call. Use `urllib.parse` only where it does not normalise the URL in surprising ways; the url field is the user's URL minus `git::` and the `//subdir?query` tail.
- The orchestrator restricts further (https only); this parser stays generic (https, ssh, file).
- Never the word "cluster" in new text.

- 2026-10-26 done

### S2: plugins repo bootstrap

- Status: done
- Files: `.mise.toml`, `pyproject.toml`, `uv.lock`, `.github/workflows/ci.yml`, `tests/test_smoke.py`, `tests/test_repo.py`, `README.md`
- Verify: `mise run install && mise run test && mise run lint`
- Verified head: 014598816a8155013ec7928af23cd7caeb208d97

#### Requirement

Goal G3 (epic README), verbatim: "any-mcp-tatara-plugins is a working repo: topic subdirectories, per-plugin packages, tests and lint in CI, documented source notation." User request, verbatim: "Create separate any-mcp-tatara-plugins repo, which will serve as a bucket for platform specific tools. Group them into topics in subdirs." Orchestrator design call, verbatim: "any-mcp-tatara-plugins layout: `<topic>/<plugin>/` (pyproject, src, tests); first topic `orchestration/` with the orchestrator plugin moved out of any-mcp ...; repo-level mise tasks run every plugin's tests and lint; README documents the topic layout and the source notation." Design D6 (tooling part). The scaffold pins `python = "3.14.6"` while any-mcp uses 3.12: this task moves the repo to 3.12.

Scope (any-mcp-tatara-plugins):
- `.mise.toml`: `python = "3.12"`, `uv`; tasks `install` (`uv sync` covering every workspace member), `test` (`uv run pytest`), `lint` (`uv run ruff check . && uv run ruff format --check .`), `fmt` (`uv run ruff format . && uv run ruff check --fix .`); drop the `pipx:pytest` and standalone `ruff` tools.
- `pyproject.toml` (root, not a package): a uv workspace whose members are every `<topic>/<plugin>` directory holding a `pyproject.toml`; dev group `pytest>=8.3`, `pytest-asyncio`, `ruff`; ruff line-length 100, rules `E F I UP B SIM`, target py312; pytest collecting `tests/` and every `<topic>/<plugin>/tests/`, `asyncio_mode = "auto"`. any-mcp is added to the dev group by task plugins-orchestration-plugin.
- `uv.lock`.
- `.github/workflows/ci.yml`: like any-mcp's (`on: push, pull_request`, `permissions: contents: read`, `actions/checkout` and `jdx/mise-action` pinned by sha, `mise run install`, `mise run lint`, `mise run test`). No secrets.
- Delete `tests/test_smoke.py`: no longer accurate, it is the scaffold placeholder (`assert True`) and asserts nothing.
- New `tests/test_repo.py`: the tooling, CI, layout and README tests in the acceptance conditions.
- `README.md`: what the repo is (the platform-specific plugin bucket for any-mcp), the topic layout `<topic>/<plugin>/` (pyproject with an `any_mcp.plugins` entry point, `src/`, `tests/`), how to add a plugin, the source notation (local `./`, `../`, `/`; `git::https://github.com/szymonrychu/any-mcp-tatara-plugins.git//<topic>/<plugin>?ref=vX.Y.Z`; `github.com/szymonrychu/any-mcp-tatara-plugins//<topic>/<plugin>?ref=vX.Y.Z`), install with `any-mcp plugins install <source>` or a `source:` config entry, and releases as `vX.Y.Z` tags on main.

#### Acceptance conditions

- ac1: mise pins python 3.12 and defines install, test, lint (ruff check and format check) and fmt tasks run through uv [evidence: test:tests/test_repo.py::test_mise_tooling]
- ac2: the interpreter running the tests is 3.12 [evidence: test:tests/test_repo.py::test_interpreter_is_312]
- ac3: CI runs mise run install, lint and test on push and pull_request with read-only permissions and sha-pinned actions [evidence: test:tests/test_repo.py::test_ci_workflow]
- ac4: every topic/plugin directory with a pyproject.toml is a uv workspace member, declares an any_mcp.plugins entry point and has a tests directory that the test run collects [evidence: test:tests/test_repo.py::test_plugin_layout]
- ac5: README documents the topic layout, adding a plugin, and the source notation with a git::, a github.com/ and a local example [evidence: test:tests/test_repo.py::test_readme_documents_layout_and_notation]
- ac6: the scaffold placeholder test is no longer tracked [evidence: command:test -z "$(git ls-files tests/test_smoke.py)"]
- ac7: install, test and lint pass [evidence: command:mise run install && mise run test && mise run lint]

#### Files

- `.mise.toml`
- `pyproject.toml`
- `uv.lock`
- `.github/workflows/ci.yml`
- `tests/test_smoke.py`
- `tests/test_repo.py`
- `README.md`

#### Interfaces

- `.mise.toml` tasks `install`, `test`, `lint`, `fmt` (the commands in the Requirement); later tasks and CI call only these.
- Layout contract pinned by `tests/test_repo.py::test_plugin_layout`: `<topic>/<plugin>/pyproject.toml` with an `[project.entry-points."any_mcp.plugins"]` table, `<topic>/<plugin>/src/`, `<topic>/<plugin>/tests/`; every such directory is a uv workspace member.

#### Expected outcome

`mise run install && mise run test && mise run lint` pass on Python 3.12 locally and in CI, and the README tells a plugin author where a plugin goes and how users reference it.

#### Steps

- Red: write `tests/test_repo.py`; run `uv run pytest -q tests/test_repo.py` (after a first `.mise.toml` python change so the interpreter is 3.12): fails.
- Green: `.mise.toml`, root `pyproject.toml`, `uv lock`, CI workflow, README; `git rm tests/test_smoke.py`; run the task's verify: passes.

#### Notes

- The scaffold's `.mise.toml` pins `python = "3.14.6"`, `uv = "0.12.23"`, `ruff`, `pipx:pytest`; replace with any-mcp's shape (`python = "3.12"`, `uv`, `_.python.venv`).
- The workspace member glob must not pick up `tests/` or `.github/` (uv refuses a member without a pyproject); with no plugin yet, ac4 holds vacuously and becomes concrete in task plugins-orchestration-plugin.
- Same-named test modules in several plugins need pytest `--import-mode=importlib` or unique names: choose one and pin it in test_repo.py.
- CI action shas: copy any-mcp's `.github/workflows/ci.yml` pins.
- The repo is public and its CI needs no secrets (user, 2026-10-26).

- 2026-10-26 done

### S3: web plugin source parser

- Status: done
- Files: `src/presets/pluginSource.ts`, `src/presets/pluginSource.test.ts`
- Verify: `npx vitest run src/presets/pluginSource.test.ts && npm run build && mise run lint`
- Verified head: 2095c1af53fe2a7d30e39dc033c3422e34235546

#### Requirement

User request, verbatim: "In webUI add ability to provide links to such plugins (defined by repo, or dir in repo in git ref) (plus button, shows line textbox where it can be pasted- multiple plugins can be provided)." Goal G5 (epic README), verbatim: "The agents-web preset form edits the plugin sources: a "+" button adds a one-line text box per source, several sources allowed." Design D10, verbatim: "`src/presets/pluginSource.ts` mirrors D1 for the sources the orchestrator accepts (D8) with the same messages". Design D1 (the grammar) and D8 ("only `git::https://` and `github.com/` sources").

Scope (agents-web):
- New `src/presets/pluginSource.ts`: `pluginSourceError(text: string): string | undefined` (undefined when valid) over the trimmed text, applying design D1's rules to the forms D8 accepts: `git::https://<host>/<path>[//<subdir>][?ref=<ref>]` and `github.com/<owner>/<repo>[//<subdir>][?ref=<ref>]`; local paths, `git::ssh://`, `git::file://` and every form D1 refuses are refused, with a message naming the problem (the meaning of any-mcp's messages; byte equality across repos is not required).
- New `src/presets/pluginSource.test.ts` with the cases of the acceptance conditions.
- No text uses the word "cluster" (`src/nomenclature.test.ts`).

#### Acceptance conditions

- ac1: git::https URLs with optional //subdir and ?ref= and the github.com/owner/repo shorthand are accepted [evidence: command:npx vitest run src/presets/pluginSource.test.ts -t 'accepts remote sources']
- ac2: local paths, git::ssh and git::file are refused with a message that only https git sources are allowed [evidence: command:npx vitest run src/presets/pluginSource.test.ts -t 'refuses local and non-https sources']
- ac3: query keys other than ref, empty refs, refs starting with - or containing .., subdirs with a leading /, an empty or a .. segment, and unrecognised forms are refused with a message naming the problem [evidence: command:npx vitest run src/presets/pluginSource.test.ts -t 'refuses malformed sources']
- ac4: surrounding whitespace is ignored and an empty line is refused as empty [evidence: command:npx vitest run src/presets/pluginSource.test.ts -t 'trims and refuses empty']
- ac5: the type check and build pass [evidence: command:npm run build]
- ac6: lint passes [evidence: command:mise run lint]

#### Files

- `src/presets/pluginSource.ts`
- `src/presets/pluginSource.test.ts`

#### Interfaces

- `src/presets/pluginSource.ts`: `export function pluginSourceError(text: string): string | undefined` (undefined when valid; the caller stores the trimmed text).
- Consumed by `src/sessions/sessionSpecForm.ts` in task web-preset-plugin-sources.

#### Expected outcome

The web app refuses, with a readable reason, every source the orchestrator would refuse under design D1 and D8, and accepts every one it would accept.

#### Steps

- Red: write `src/presets/pluginSource.test.ts` with the four `describe`/`it` groups named in the acceptance conditions as tables of accepted and refused strings; run `npx vitest run src/presets/pluginSource.test.ts`: fails on the missing module.
- Green: write `src/presets/pluginSource.ts`; run the task's verify: passes.

#### Notes

- Rulings and their pin tests: only `git::https://` and `github.com/` forms are valid (refuses local and non-https sources; gate Q1 recommended answer); `?depth=` is refused naming `depth` (refuses malformed sources).
- Mirror the accept and reject cases of any-mcp `tests/test_sources.py` (task anymcp-source-parser) for the forms D8 keeps; messages need the same meaning, not the same bytes.
- Test names must contain the `-t` strings of the acceptance conditions.
- No text uses the word "cluster" (`src/nomenclature.test.ts`); `npm run build` runs `tsc -b`.

- 2026-10-26 done

- 2026-10-27 done

### S4: anymcp source installer

- Status: done
- Files: `src/any_mcp/install.py`, `tests/test_install.py`
- Verify: `uv run --frozen pytest -q tests/test_install.py && mise run lint`
- Verified head: a9bc488c9aeb43bec06660e368227cda0afd7898

#### Requirement

Goal G2 (epic README), verbatim: "any-mcp installs and loads plugins from Terraform-module-like sources: git repo with optional //subdir and ?ref=, and local directory paths." Non-goal, verbatim: "No per-plugin dependency isolation (separate venvs or processes)." Design D3, verbatim:

"`any_mcp.install` resolves a `Source` to an installed distribution:
- Git: a ref that is a full 40-hex SHA is fetched by SHA (`git fetch --depth 1 origin <sha>`), falling back to a `--filter=blob:none` fetch and checkout when the server refuses; a branch or tag (found by `git ls-remote`) is a shallow, blob-filtered clone of that ref; anything else (a short SHA) is a blob-filtered full clone then `git checkout`; no ref means the remote default branch. Sparse checkout limits the tree to the subdir. Every git call puts user values after `--`, runs with a timeout, and the resolved subdir must stay inside the checkout (symlinks resolved). A missing subdir is an error naming url, ref, resolved SHA and subdir.
- Cache dir `$ANY_MCP_CACHE_DIR`, default `<sys.prefix>/any-mcp-sources` (my call: the cache lives with the environment the packages are installed into, so a cache hit means installed). Key (normalised url, ref, subdir); a `manifest.json` records per key the source string, resolved SHA, checkout dir and distribution name. A SHA ref is cached forever; a branch, tag or default-branch entry is reused as is at startup and re-resolved only by an explicit install, like `terraform init -upgrade`.
- The source directory must hold a `pyproject.toml` with `[project].name`; it is installed with `<sys.executable> -m pip install` (git sources; local sources with `-e`, so they stay in place and edits show on restart, my call). Then `importlib.invalidate_caches()` and the distribution's `any_mcp.plugins` entry points are read; none is an error, several need `plugin` (D2).
- No `python_path` or `sys.path` insertion for sources."

Scope (any-mcp): new module `src/any_mcp/install.py`, tests in `tests/test_install.py`. Git runs for real against local repositories built in `tmp_path` (`file://` URLs); pip and the entry-point lookup are injectable so the unit tests do not install into the dev environment (the real pip path is proven end to end by task anymcp-source-plugin-loading).

#### Acceptance conditions

- ac1: a git source at a tag and at a branch is shallow-cloned with only its subdir checked out, pip-installed from that subdir, and the manifest records the source string, resolved SHA, directory and distribution name [evidence: test:tests/test_install.py::test_git_tag_and_branch_install]
- ac2: a full 40-hex SHA ref is fetched by SHA and, when that fetch fails, through a blob-filtered fetch and checkout; a short SHA ref is checked out after a blob-filtered full clone; no ref installs the remote default branch [evidence: test:tests/test_install.py::test_sha_refs_and_fallback]
- ac3: a SHA source in the manifest is never fetched again, even on explicit install; a branch or tag source in the manifest is reused with no git call unless refresh is set, and with refresh is re-resolved and reinstalled when its SHA moved [evidence: test:tests/test_install.py::test_cache_rules]
- ac4: a local source resolves against base_dir and is pip-installed editable in place, never copied into the cache [evidence: test:tests/test_install.py::test_local_source_editable_in_place]
- ac5: a subdir missing at the resolved commit is an error naming url, ref, resolved SHA and subdir, and a subdir that resolves outside the checkout through a symlink is refused [evidence: test:tests/test_install.py::test_subdir_missing_or_escaping]
- ac6: a source directory without pyproject.toml or without [project].name, a distribution with no any_mcp.plugins entry point, and a failing pip install are ConfigErrors naming the source [evidence: test:tests/test_install.py::test_package_errors]
- ac7: every git and pip call is an argv list run without a shell and with a timeout, and every URL and path given to git follows -- [evidence: test:tests/test_install.py::test_subprocess_hygiene]
- ac8: the cache dir is $ANY_MCP_CACHE_DIR when set, else <sys.prefix>/any-mcp-sources [evidence: test:tests/test_install.py::test_cache_dir]
- ac9: lint passes [evidence: command:mise run lint]

#### Files

- `src/any_mcp/install.py`
- `tests/test_install.py`

#### Interfaces

- `src/any_mcp/install.py:Installed`, a frozen dataclass: `source: Source`, `directory: Path` (the plugin package directory), `distribution: str`, `sha: str | None` (None for local), `entry_points: dict[str, str]` (entry-point name to `module:attr`).
- `install(source: Source, *, base_dir: Path, refresh: bool) -> Installed`: fetch when needed (D3 cache rules), pip-install, read entry points; `refresh=True` is an explicit install.
- `installed(source: Source, *, base_dir: Path) -> Installed | None`: the manifest lookup without any git or pip call.
- `cache_dir() -> Path`: `$ANY_MCP_CACHE_DIR`, else `Path(sys.prefix) / "any-mcp-sources"`; `manifest.json` inside it.
- Injectable for tests: the subprocess runner for pip and the entry-point lookup (`importlib.metadata.distribution`); git always runs for real.

#### Expected outcome

Given a `Source`, any-mcp ends with the plugin's distribution installed in its own environment, a manifest entry describing it, and its `any_mcp.plugins` entry points known, with no unnecessary fetch.

#### Steps

- Red: write `tests/test_install.py`, building bare git repos in `tmp_path` with a plugin package under a subdir (a tag, a branch, two commits), and the acceptance tests; run `uv run --frozen pytest -q tests/test_install.py`: fails on the missing module.
- Green: write `src/any_mcp/install.py`; run the task's verify: passes.

#### Notes

- Rulings and their pin tests: a SHA source is never re-fetched even with refresh (test_cache_rules); a tag or branch with refresh is reinstalled only when the resolved SHA moved (test_cache_rules); local sources are editable and resolved against `base_dir` (test_local_source_editable_in_place); every URL and path argument to git follows `--` (test_subprocess_hygiene, by recording argv).
- The by-SHA fallback test makes the `git fetch --depth 1 origin <sha>` call fail through the runner wrapper, since a `file://` server may allow it.
- `pip` is `[sys.executable, "-m", "pip", "install", ...]` with `--no-input` and `--disable-pip-version-check`; a missing pip module is a `ConfigError` saying so (uv-made venvs have none).
- After install call `importlib.invalidate_caches()` before reading entry points (anymap Unknowns).
- Use `git -c protocol.file.allow=always` only in tests if newer git refuses `file://` in submodule-like contexts; never in src.
- Security is the review focus: no `shell=True`, a timeout on every call, refs validated by the parser, symlink-resolved subdir inside the checkout.

- 2026-10-27 done

### S5: any-mcp source parser parity with the web grammar

- Status: done
- Files: `src/any_mcp/sources.py`, `tests/test_sources.py`
- Verify: `unset VIRTUAL_ENV && uv run --frozen pytest -q -o addopts="" tests/test_sources.py && mise run lint`
- Verified head: 4aceb148623d7ff2d0f8bfbd8fc30db90b3fc986

#### Requirement

Review finding (2026-10-27, web-plugin-source-parser review, parity check against src/any_mcp/sources.py): any-mcp's parser accepts git sources the design's grammar (D8: `git::https://<host>/<path>`) does not: `git::https://github.com` and `git::https://github.com/` (no repo path), `git::https://host//sub` and `git::https:///x` (empty host or empty repo path before the `//` subdir separator), and locations containing control characters such as a newline. Tighten `_parse_git` so a git location must be an http(s) or other allowed scheme URL with a non-empty host and a non-empty repo path, no whitespace in a remote (git:: or github.com) source, and no control characters in any source - a local path may contain spaces (user requirement: local plugin directories keep working); each refusal uses the existing `plugin source '<text>': <problem>` message form. The agents-web parser (src/presets/pluginSource.ts in the web tree) already refuses these; after this task both parsers decide identically on the remote https subset.

#### Acceptance conditions

- ac1: git sources with no repo path (`git::https://github.com`, `git::https://github.com/`, `git::https://host//sub`) and with an empty host (`git::https:///x`) are refused with a message naming the problem [evidence: test:tests/test_sources.py::test_git_location_needs_host_and_path]
- ac2: remote sources containing whitespace (space, tab) and any source containing a control character (newline, tab in a local path) are refused, while a local path containing a space is accepted [evidence: test:tests/test_sources.py::test_whitespace_and_control_refused]
- ac3: the parser tests, nomenclature and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q -o addopts="" tests/test_sources.py tests/test_nomenclature.py && mise run lint]

#### Files

- `src/any_mcp/sources.py`
- `tests/test_sources.py`

#### Interfaces

- `src/any_mcp/sources.py:_parse_git` and the top-level parse entry: stricter location checks; public API unchanged.

#### Expected outcome

any-mcp refuses every remote source the web form refuses, with the same message form.

#### Steps

- Red: add the two tests; run the task's verify; expect failures.
- Green: tighten the parser; run the task's verify and ac3 on the committed HEAD.

#### Notes

- Depends on anymcp-source-installer only to serialize work in the any-mcp tree (same file area); no functional dependency.
- Reference: agents-web tree /Users/szymonri/Documents/claude-code-tatara/.claude/worktrees/generic-any-mcp-with-git-and/agents-web/src/presets/pluginSource.ts (HOST_AND_PATH) and its tests.
- The orchestrator-side check (task orch-any-mcp-sources-spec) must follow the same rules.

- 2026-10-27 amended: orchestrator over-specified: local paths with spaces must keep working; whitespace refusal limited to remote sources

- 2026-10-27 done

### S6: anymcp source plugin loading

- Status: done
- Files: `src/any_mcp/config.py`, `src/any_mcp/discovery.py`, `src/any_mcp/cli.py`, `docs/configuration.md`, `tests/test_source_plugins.py`, `tests/fixtures/source_plugin/pyproject.toml`, `tests/fixtures/source_plugin/src/source_plugin/__init__.py`
- Verify: `uv run --frozen pytest -q tests/test_source_plugins.py tests/test_cli.py tests/test_discovery.py tests/test_config.py tests/test_docs_reference.py && mise run lint`
- Verified head: dfad12bba43ab063041c75616f57a42895ae88e8

#### Requirement

Goal G2 (epic README), verbatim: "any-mcp installs and loads plugins from Terraform-module-like sources: git repo with optional //subdir and ?ref=, and local directory paths." User request, verbatim: "It must still be possible (when using pip installed any-mcp) to provide path to local dir, where plugin is defined (again- similar to terraform module handling)."

Design D2, verbatim: "`PluginEntry` gains `source: str | None`; `plugin` becomes optional. Exactly one rule: an entry has a `plugin` or a `source` or both; with a `source`, `plugin` is an entry-point name (never `module:Class`) that picks among the source package's `any_mcp.plugins` entry points, required only when the package declares more than one. The `source` string is validated by `parse_source` at config load. `name` stays required."

Design D4, verbatim: "New subcommand `any-mcp plugins install [--config PATH] [SOURCE ...]` installs each given source, or every `plugins[].source` of the config, as an explicit install (refreshes branch and tag refs). It reads only the `source` strings (expanding `${VAR}` in those strings alone), so a config whose plugin `config` names variables unset in the install environment still installs (my call: the onStart hook does not carry the agent's runtime env). Errors exit 78 with one line. At server startup (`load_plugins`, all three paths), a source entry missing from the manifest is installed first, then loaded."

Scope (any-mcp):
- `src/any_mcp/config.py`: `PluginEntry.source`, optional `plugin`, the D2 validation.
- `src/any_mcp/discovery.py`: `load_plugins` resolves source entries through `any_mcp.install` (install on a manifest miss, base dir = the config's `base_dir`), then loads the chosen entry point.
- `src/any_mcp/cli.py`: the `plugins install` subcommand; every existing invocation keeps working.
- `docs/configuration.md`: `plugins[].source`, the changed `plugins[].plugin` row, the `plugins install` command, `ANY_MCP_CACHE_DIR` (the "only variable" sentence is no longer true), and the trust model: a source is operator-trusted code installed into the server's environment.
- Tests in `tests/test_source_plugins.py` with a fixture plugin package under `tests/fixtures/source_plugin/` (pyproject with one `any_mcp.plugins` entry point).

#### Acceptance conditions

- ac1: an entry with a source and no plugin validates, an entry with neither is refused, with a source a module:Class plugin value is refused, and an invalid source string fails config load with the parser's message [evidence: test:tests/test_source_plugins.py::test_entry_source_validation]
- ac2: load_plugins installs a source entry missing from the manifest and loads its single any_mcp.plugins entry point; with several entry points plugin picks one, and without plugin the load fails naming them [evidence: test:tests/test_source_plugins.py::test_load_plugins_source_entries]
- ac3: any-mcp plugins install SOURCE... installs each given source with refresh, and --config PATH installs every plugins[].source of the file, expanding ${VAR} only inside source strings, so a config whose plugin config names an unset variable still installs [evidence: test:tests/test_source_plugins.py::test_plugins_install_command]
- ac4: an install or load failure exits 78 with one stderr line naming the source [evidence: test:tests/test_source_plugins.py::test_install_failure_exit_code]
- ac5: end to end in a fresh venv with pip, any-mcp installed from the working tree installs the fixture plugin from a local path and from a git::file:// repository with //subdir and ?ref=, and --list-tools lists its tool for each [evidence: test:tests/test_source_plugins.py::test_end_to_end_local_and_git_sources]
- ac6: existing invocations keep working: the CLI, discovery, config and docs tests pass [evidence: command:uv run --frozen pytest -q tests/test_cli.py tests/test_discovery.py tests/test_config.py tests/test_docs_reference.py tests/test_docs_links.py]
- ac7: docs/configuration.md documents plugins[].source, the plugins install command and ANY_MCP_CACHE_DIR [evidence: command:grep -qF 'plugins[].source' docs/configuration.md && grep -qF 'any-mcp plugins install' docs/configuration.md && grep -qF 'ANY_MCP_CACHE_DIR' docs/configuration.md]
- ac8: lint passes [evidence: command:mise run lint]

#### Files

- `src/any_mcp/config.py`
- `src/any_mcp/discovery.py`
- `src/any_mcp/cli.py`
- `docs/configuration.md`
- `tests/test_source_plugins.py`
- `tests/fixtures/source_plugin/pyproject.toml`
- `tests/fixtures/source_plugin/src/source_plugin/__init__.py`

#### Interfaces

- `src/any_mcp/config.py:PluginEntry`: `plugin: str | None = None`, `source: str | None = None`; a model validator enforcing design D2 and calling `any_mcp.sources.parse_source` on `source`.
- `src/any_mcp/discovery.py:load_plugins(config, *, http_transport=None)`: unchanged signature; source entries go through `any_mcp.install.installed(...)`, else `install(..., refresh=False)`, base dir `config.base_dir`.
- CLI: `any-mcp plugins install [--config PATH] [SOURCE ...]`, exit 0 on success, 78 with one stderr line on a ConfigError, printing one line per installed source (`<source> <distribution> <sha or local>`).
- `tests/fixtures/source_plugin/`: a hatchling package `any-mcp-source-plugin` exposing entry point `source_plugin` with one tool.

#### Expected outcome

An any-mcp config entry `{name: x, source: <git or local source>}` installs and loads like any other plugin, and `any-mcp plugins install` pre-installs sources for a hook.

#### Steps

- Red: write `tests/test_source_plugins.py` and the fixture package; run `uv run --frozen pytest -q tests/test_source_plugins.py`: fails.
- Green: config, discovery and CLI changes; run the task's verify: passes.
- Docs: update `docs/configuration.md`; run ac6 and ac7 commands: pass.

#### Notes

- Rulings and their pin tests: with a source, `plugin` names an entry point, never `module:Class` (test_entry_source_validation); `plugins install --config` expands `${VAR}` only inside source strings (test_plugins_install_command, with a config whose plugin config names an unset variable); install-on-miss at startup does not refresh (test_load_plugins_source_entries).
- The end-to-end test follows `tests/test_release.py`: `uv venv --seed` in `tmp_path`, install any-mcp from `ROOT` (the working tree, not a git URL, so uncommitted work counts), then run the venv's `any-mcp`; set `ANY_MCP_CACHE_DIR` into `tmp_path`. The git variant commits the fixture into a temp repo under a subdir and tags it.
- The subcommand must not break `any-mcp --config ...` or `any-mcp --plugin ...` with no subcommand (ac6 covers the CLI tests).
- `tests/test_docs_reference.py` requires every top-level config key and CLI flag documented; `ANY_MCP_CONFIG is the only variable` is no longer true and changes in configuration.md.
- `tests/test_import_boundary.py` scans `src/any_mcp` and `examples`: keep fastmcp imports out of the new code.

- 2026-10-27 done

### S7: anymcp remove orchestrator

- Status: done
- Files: `src/any_mcp/orchestrator.py`, `tests/test_orchestrator_plugin.py`, `tests/test_nomenclature.py`, `tests/test_generic.py`, `README.md`
- Verify: `uv run --frozen pytest -q tests/test_generic.py tests/test_docs_links.py && mise run lint`
- Verified head: ee0e02701a84b42ef0059bba4395308864ec4f64

#### Requirement

Goal G1 (epic README), verbatim: "any-mcp contains no platform-specific plugin; the orchestrator plugin lives in any-mcp-tatara-plugins under a topic subdirectory, with the same tools and behaviour." User request, verbatim: "Make anyMcp generic." Non-goal, verbatim: "No backward-compatibility alias for the removed any_mcp.orchestrator module." Design D5, verbatim: "`src/any_mcp/orchestrator.py` and `tests/test_orchestrator_plugin.py` are deleted with no shim; a retirement test pins their absence through `git ls-files` and that src, examples and docs carry no `/agent/v1`. `tests/test_nomenclature.py` is deleted: it guards exactly those files, and the guard moves with them to the plugins repo. README's "Orchestrator plugin" section is replaced by a "Plugin sources" section pointing at any-mcp-tatara-plugins."

Scope (any-mcp):
- Delete `src/any_mcp/orchestrator.py` and `tests/test_orchestrator_plugin.py` (the plugin and its tests move to any-mcp-tatara-plugins in task plugins-orchestration-plugin).
- Delete `tests/test_nomenclature.py`: no longer accurate, it asserts `git ls-files` returns exactly the two deleted files plus README.md and guards their wording; the guard moves with the files.
- New `tests/test_generic.py`: the retirement and genericity tests in the acceptance conditions.
- `README.md`: remove the "Orchestrator plugin" section; add a "Plugin sources" section with the notation forms (local `./`, `../`, `/`; `git::https://...//subdir?ref=`; `github.com/owner/repo//subdir?ref=`), a `source:` config example, `any-mcp plugins install`, and a pointer to https://github.com/szymonrychu/any-mcp-tatara-plugins for the platform plugins.

#### Acceptance conditions

- ac1: src/any_mcp/orchestrator.py, tests/test_orchestrator_plugin.py and tests/test_nomenclature.py are no longer tracked [evidence: test:tests/test_generic.py::test_orchestrator_plugin_retired]
- ac2: no tracked file under src, examples or docs contains /agent/v1, orchestrator or hive [evidence: test:tests/test_generic.py::test_no_platform_names]
- ac3: importing any_mcp.orchestrator raises ModuleNotFoundError (no alias) [evidence: test:tests/test_generic.py::test_no_orchestrator_alias]
- ac4: README has no Orchestrator plugin section and has a Plugin sources section naming the git::, github.com/ and local forms, plugins install and any-mcp-tatara-plugins [evidence: test:tests/test_generic.py::test_readme_plugin_sources_section]
- ac5: the whole any-mcp suite passes without the removed module [evidence: command:mise run test]
- ac6: lint passes [evidence: command:mise run lint]

#### Files

- `src/any_mcp/orchestrator.py`
- `tests/test_orchestrator_plugin.py`
- `tests/test_nomenclature.py`
- `tests/test_generic.py`
- `README.md`

#### Interfaces

- Removed: module `any_mcp.orchestrator` (`OrchestratorPlugin`, `OrchestratorConfig`); no alias anywhere.
- Kept: `any_mcp.errors.error_result`, `redact`, `UpstreamError` (the moved plugin imports them).

#### Expected outcome

any-mcp's tracked tree has no platform-specific plugin, its README points platform users at any-mcp-tatara-plugins and plugin sources, and the full suite is green.

#### Steps

- Red: write `tests/test_generic.py`; run `uv run --frozen pytest -q tests/test_generic.py`: ac1, ac2 (README excluded from ac2), ac3 and ac4 fail.
- Green: `git rm src/any_mcp/orchestrator.py tests/test_orchestrator_plugin.py tests/test_nomenclature.py`; rewrite the README section; run the task's verify, then `mise run test`: pass.

#### Notes

- TDD exception for the deletions: deletion pinned by a retirement test (`test_orchestrator_plugin_retired` asserts on `git ls-files`, never on the filesystem).
- Ruling and its pin test: ac2 scans only `src/`, `examples/` and `docs/` (test_no_platform_names); CHANGELOG and MEMORY keep their history.
- The README Plugin sources section documents the command from task anymcp-source-plugin-loading; keep `tests/test_docs_links.py` green (README links every docs page, Quickstart equals `examples/hello/hello.py`).
- The plugin's README content (tools table) is reused by task plugins-orchestration-plugin from any-mcp `v0.4.0`, so nothing needs saving here.

- 2026-10-27 done

### S8: anymcp release 0.5.0

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `CHANGELOG.md`, `README.md`, `MEMORY.md`, `tests/test_release.py`, `tests/test_package.py`, `tests/test_docs_links.py`
- Verify: `uv run --frozen pytest -q tests/test_release.py tests/test_package.py tests/test_docs_links.py && mise run lint`
- Verified head: 8a5aee11a0fcc3265ec4a32105e1e4425da76a63

#### Requirement

Design D5, verbatim: "Release v0.5.0 (breaking, user's design call) with CHANGELOG, README pins and the version-pinned tests updated as no longer accurate; MEMORY records the reversal of the 2026-10-24 decision." Orchestrator design call, verbatim: "any-mcp: remove orchestrator.py and its tests (no backward compatibility shim), nomenclature/package/docs tests updated as inaccurate, release as a new minor version (0.5.0) with CHANGELOG."

Scope (any-mcp):
- `pyproject.toml` version `0.5.0`; `uv.lock` refreshed.
- `CHANGELOG.md`: `## v0.5.0` on top, a "Breaking:" line naming the removed `any_mcp.orchestrator` and where the plugin now lives (any-mcp-tatara-plugins, `orchestration/orchestrator`), then bullets: plugin sources (`plugins[].source`, the notation forms), `any-mcp plugins install`, `ANY_MCP_CACHE_DIR`, `plugins[].plugin` optional with a source.
- `README.md`: the pinned install lines name `v0.5.0`.
- `MEMORY.md`: a dated entry titled "any-mcp is generic, plugins come from sources" that reverses the 2026-10-24 entry and says why (user request: any-mcp reusable outside this platform; platform plugins live in any-mcp-tatara-plugins).
- Tests no longer accurate because the version moves to 0.5.0: `tests/test_release.py` (`PINNED_LINE`, `test_versions_agree`, `test_wheel_installs_and_reports_version`, `test_uv_tool_install`), `tests/test_package.py::test_version_from_metadata`, `tests/test_docs_links.py::test_readme_install_forms`: each asserts `0.5.0`.
- The tag push is the orchestrator's (design Rollout R1), not this task's.

#### Acceptance conditions

- ac1: pyproject, installed metadata, the CHANGELOG top heading and README agree on 0.5.0 [evidence: test:tests/test_release.py::test_versions_agree]
- ac2: any_mcp.__version__ is 0.5.0 [evidence: test:tests/test_package.py::test_version_from_metadata]
- ac3: README install forms name v0.5.0 [evidence: test:tests/test_docs_links.py::test_readme_install_forms]
- ac4: the v0.5.0 CHANGELOG section has a Breaking: line and names any-mcp-tatara-plugins, plugins install and ANY_MCP_CACHE_DIR [evidence: command:s=$(sed -n '/^## v0.5.0/,/^## v0.4.0/p' CHANGELOG.md) && echo "$s" | grep -q '^Breaking:' && echo "$s" | grep -q 'any-mcp-tatara-plugins' && echo "$s" | grep -q 'plugins install' && echo "$s" | grep -q 'ANY_MCP_CACHE_DIR']
- ac5: MEMORY.md records the reversal of the built-in plugin decision [evidence: command:grep -q '^## 20[0-9-]* - any-mcp is generic, plugins come from sources' MEMORY.md]
- ac6: the whole suite passes, including the install-from-committed-HEAD tests [evidence: command:mise run test]
- ac7: lint passes [evidence: command:mise run lint]

#### Files

- `pyproject.toml`
- `uv.lock`
- `CHANGELOG.md`
- `README.md`
- `MEMORY.md`
- `tests/test_release.py`
- `tests/test_package.py`
- `tests/test_docs_links.py`

#### Interfaces

- Version `0.5.0` everywhere the release tests pin it; CHANGELOG section `## v0.5.0` (the release workflow extracts it verbatim).

#### Expected outcome

The any-mcp tree is ready for the orchestrator to tag `v0.5.0` (Rollout R1): versions agree, CHANGELOG and MEMORY explain the breaking change.

#### Steps

- Red: change the pinned versions in the three test files; run `uv run --frozen pytest -q tests/test_release.py tests/test_package.py tests/test_docs_links.py`: fails.
- Green: bump pyproject, `uv lock`, README pins, CHANGELOG, MEMORY; commit, then run `mise run test` (the install tests read the committed HEAD): passes.

#### Notes

- `tests/test_release.py` installs from `git+file://ROOT@<HEAD sha>`: commit before running the full suite or those tests see the old tree.
- CHANGELOG style: one or two summary lines with the "Breaking:" prefix, then `- ` bullets wrapped near 100 columns (see v0.3.0).
- MEMORY entries are `## YYYY-MM-DD - title`, newest first.
- The tag push is Rollout R1, not this task.

- 2026-10-27 done

### S9: plugins orchestration plugin

- Status: done
- Files: `orchestration/orchestrator/pyproject.toml`, `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`, `orchestration/orchestrator/tests/test_orchestrator_plugin.py`, `orchestration/orchestrator/README.md`, `pyproject.toml`, `uv.lock`, `tests/test_nomenclature.py`, `tests/test_source_install.py`
- Verify: `mise run install && mise run test && mise run lint`
- Verified head: b42184c696040a1d6b868c61445569227ad6e73f

#### Requirement

Goal G1 (epic README), verbatim: "any-mcp contains no platform-specific plugin; the orchestrator plugin lives in any-mcp-tatara-plugins under a topic subdirectory, with the same tools and behaviour." Goal G3, verbatim: "any-mcp-tatara-plugins is a working repo: topic subdirectories, per-plugin packages, tests and lint in CI, documented source notation." User request, verbatim: "Group them into topics in subdirs." Orchestrator design call, verbatim: "first topic `orchestration/` with the orchestrator plugin moved out of any-mcp (OrchestratorPlugin and its tests, same tool names and behaviour incl. the v0.4.0 session tools)". Design D6: distribution `any-mcp-tatara-orchestrator`, module `any_mcp_tatara_orchestrator`, entry point `orchestrator`; plugin packages declare `any-mcp` unversioned as a dependency.

Needs a merged upstream: any-mcp v0.5.0 released (design Rollout R1). Do not start before `git ls-remote https://github.com/szymonrychu/any-mcp refs/tags/v0.5.0` prints a sha.

Scope (any-mcp-tatara-plugins):
- `orchestration/orchestrator/pyproject.toml`: name `any-mcp-tatara-orchestrator`, version `0.1.0`, `requires-python = ">=3.12"`, `dependencies = ["any-mcp"]`, hatchling, `[project.entry-points."any_mcp.plugins"] orchestrator = "any_mcp_tatara_orchestrator:OrchestratorPlugin"`.
- `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`: any-mcp v0.4.0's `src/any_mcp/orchestrator.py`, unchanged except the module docstring (no longer "built-in").
- `orchestration/orchestrator/tests/test_orchestrator_plugin.py`: any-mcp v0.4.0's `tests/test_orchestrator_plugin.py`, unchanged except its import of the plugin.
- `orchestration/orchestrator/README.md`: the plugin's documentation moved from any-mcp v0.4.0 README "Orchestrator plugin" (config fields, the eleven tools and routes, allow-list note), with the config example using `source: github.com/szymonrychu/any-mcp-tatara-plugins//orchestration/orchestrator?ref=v0.1.0` instead of `plugin: any_mcp.orchestrator:OrchestratorPlugin`.
- Root `pyproject.toml` and `uv.lock`: the dev group gains `any-mcp` pinned to the `v0.5.0` tag through `[tool.uv.sources]`; the plugin is a workspace member.
- `tests/test_nomenclature.py`: any-mcp v0.4.0's guard, its `FILES` the moved plugin source, test and README, `PINNED_NAME` kept.
- `tests/test_source_install.py`: the end-to-end and metadata tests in the acceptance conditions.

#### Acceptance conditions

- ac1: the moved plugin tests pass against the package, including the eleven tools and the session tools [evidence: command:uv run --frozen pytest -q orchestration/orchestrator/tests]
- ac2: the moved test file differs from any-mcp v0.4.0 tests/test_orchestrator_plugin.py only in import lines [evidence: command:test "$(curl -fsSL https://raw.githubusercontent.com/szymonrychu/any-mcp/v0.4.0/tests/test_orchestrator_plugin.py | diff - orchestration/orchestrator/tests/test_orchestrator_plugin.py | grep '^[<>]' | grep -cv 'import')" -eq 0]
- ac3: the plugin module differs from any-mcp v0.4.0 src/any_mcp/orchestrator.py only in its module docstring and import lines [evidence: command:test "$(curl -fsSL https://raw.githubusercontent.com/szymonrychu/any-mcp/v0.4.0/src/any_mcp/orchestrator.py | diff - orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py | grep '^[<>]' | grep -v 'import' | grep -cv '^[<>] """')" -eq 0]
- ac4: any-mcp v0.5.0 in a fresh venv installs the plugin through any-mcp plugins install from ./orchestration/orchestrator and from a git::file:// URL of this repository with //orchestration/orchestrator and ?ref=<HEAD sha>, and --list-tools with an orchestrator config lists the eleven orchestrator_ tools [evidence: test:tests/test_source_install.py::test_orchestrator_plugin_installs_from_sources]
- ac5: the distribution is any-mcp-tatara-orchestrator with the single entry point orchestrator = any_mcp_tatara_orchestrator:OrchestratorPlugin and an unversioned any-mcp dependency [evidence: test:tests/test_source_install.py::test_orchestrator_distribution_metadata]
- ac6: the plugin's files carry no old nomenclature and the guard's file list is exactly tracked [evidence: test:tests/test_nomenclature.py::test_no_old_nomenclature]
- ac7: the plugin README lists the eleven tools with their routes [evidence: command:test "$(grep -c '^| `orchestrator_' orchestration/orchestrator/README.md)" -eq 11]
- ac8: the whole repo's tests and lint pass [evidence: command:mise run test && mise run lint]

#### Files

- `orchestration/orchestrator/pyproject.toml`
- `orchestration/orchestrator/src/any_mcp_tatara_orchestrator/__init__.py`
- `orchestration/orchestrator/tests/test_orchestrator_plugin.py`
- `orchestration/orchestrator/README.md`
- `pyproject.toml`
- `uv.lock`
- `tests/test_nomenclature.py`
- `tests/test_source_install.py`

#### Interfaces

- Distribution `any-mcp-tatara-orchestrator` 0.1.0, module `any_mcp_tatara_orchestrator`, `__all__ = ["OrchestratorPlugin"]`, entry point `orchestrator` in group `any_mcp.plugins`.
- The plugin's contract is any-mcp v0.4.0's unchanged: plugin name `orchestrator`, config `OrchestratorConfig` (`base_url`, `token`, `session`, `agent`, `slug`, `max_replicas`, `static`, `hive`, `auto_compact_pct`), eleven `orchestrator_*` tools and their `/agent/v1` routes.
- Source string the orchestrator renders (task orch-render-plugin-sources): `git::https://github.com/szymonrychu/any-mcp-tatara-plugins//orchestration/orchestrator?ref=v0.1.0`.

#### Expected outcome

The orchestrator plugin installs from this repo through any-mcp v0.5.0's plugin sources and behaves exactly as it did inside any-mcp v0.4.0.

#### Steps

- Red: copy the v0.4.0 test file with the new import, write `tests/test_source_install.py` and `tests/test_nomenclature.py`; run `uv run --frozen pytest -q`: fails on the missing package.
- Green: package files, root dev group and `uv lock`; run the task's verify: passes. Run the ac2 and ac3 diff commands: print nothing beyond import and docstring lines.

#### Notes

- Copy from the any-mcp tag, not a working tree: `git -C <any-mcp> show v0.4.0:src/any_mcp/orchestrator.py` and `v0.4.0:tests/test_orchestrator_plugin.py`, and README lines 74-111 for the plugin README.
- Rulings and their pin tests: the plugin declares `any-mcp` unversioned (test_orchestrator_distribution_metadata), so it installs beside any-mcp v0.4.0 in the orchestrator dev env before its pin moves; the nomenclature guard keeps `PINNED_NAME = "test_cluster_key_refused"` (test_no_old_nomenclature).
- The end-to-end test builds a fresh venv (`uv venv --seed`), installs any-mcp v0.5.0 from `git+https://github.com/szymonrychu/any-mcp@v0.5.0`, runs `any-mcp plugins install` for both source forms with `ANY_MCP_CACHE_DIR` in `tmp_path`, then `--list-tools` with an orchestrator entry whose config uses literal values (no network I/O at load: `test_no_io_at_load`). The git form needs the work committed (`git+file`-style HEAD sha, as in any-mcp's release tests).
- Never the word "cluster" outside the pinned test name.

- 2026-10-27 done

### S10: orch plugins dev dependency

- Status: done
- Files: `pyproject.toml`, `uv.lock`, `tests/test_on_start.py`, `tests/test_agent_scale.py`, `tests/test_agent_init_scripts.py`, `tests/test_agent_session_messaging.py`
- Verify: `unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_on_start.py tests/test_agent_scale.py tests/test_agent_init_scripts.py tests/test_agent_session_messaging.py tests/test_images.py && mise run lint`
- Verified head: 77e270ecec6cedbc4e71fe0b44df0e3b7e1abd88

#### Requirement

Goal G4 (epic README), verbatim: "agents-orchestrator renders the orchestrator plugin from the plugins repo at a pinned ref and accepts a list of extra plugin sources per preset and session, installed in agent pods." Orchestrator design call, verbatim: "test imports of OrchestratorPlugin move to the plugins package (dev dependency)." Design D9, verbatim: "The dev group gains `any-mcp-tatara-orchestrator @ git+<plugins repo>@<plugins tag>#subdirectory=orchestration/orchestrator`; every test import of `any_mcp.orchestrator` moves to `any_mcp_tatara_orchestrator`."

Needs a merged upstream: any-mcp-tatara-plugins tag `v0.1.0` (design Rollout R2). Do not start before `git ls-remote https://github.com/szymonrychu/any-mcp-tatara-plugins refs/tags/v0.1.0` prints a sha.

Scope (agents-orchestrator, base: the merged state of epic cross-session-messaging-and, any-mcp still pinned at v0.4.0):
- `pyproject.toml` dev group: `any-mcp-tatara-orchestrator @ git+https://github.com/szymonrychu/any-mcp-tatara-plugins@v0.1.0#subdirectory=orchestration/orchestrator`; `uv.lock` refreshed (`uv lock`).
- `tests/test_on_start.py`, `tests/test_agent_scale.py`, `tests/test_agent_init_scripts.py`, `tests/test_agent_session_messaging.py`: `from any_mcp.orchestrator import OrchestratorPlugin` becomes `from any_mcp_tatara_orchestrator import OrchestratorPlugin`; nothing else changes in them (the rendered `plugin` string in test_on_start.py stays until task orch-render-plugin-sources).

#### Acceptance conditions

- ac1: no test imports any_mcp.orchestrator and the four modules import OrchestratorPlugin from any_mcp_tatara_orchestrator [evidence: command:! grep -rnE 'from any_mcp\.orchestrator|import any_mcp\.orchestrator' tests && test "$(grep -rl 'from any_mcp_tatara_orchestrator import OrchestratorPlugin' tests | wc -l | tr -d ' ')" -eq 4]
- ac2: the dev group pins the plugin package to the plugins repo tag v0.1.0 and uv.lock carries it [evidence: command:grep -qF 'any-mcp-tatara-orchestrator @ git+https://github.com/szymonrychu/any-mcp-tatara-plugins@v0.1.0#subdirectory=orchestration/orchestrator' pyproject.toml && grep -qF 'name = "any-mcp-tatara-orchestrator"' uv.lock]
- ac3: the init scripts plugin parity test passes through the plugins-repo package [evidence: test:tests/test_agent_init_scripts.py::test_plugin_parity]
- ac4: the session tools parity test passes through the plugins-repo package [evidence: test:tests/test_agent_session_messaging.py::test_session_tools_parity]
- ac5: the four moved modules and the images test pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_on_start.py tests/test_agent_scale.py tests/test_agent_init_scripts.py tests/test_agent_session_messaging.py tests/test_images.py]
- ac6: lint passes [evidence: command:mise run lint]

#### Files

- `pyproject.toml`
- `uv.lock`
- `tests/test_on_start.py`
- `tests/test_agent_scale.py`
- `tests/test_agent_init_scripts.py`
- `tests/test_agent_session_messaging.py`

#### Interfaces

- `pyproject.toml` `[dependency-groups].dev`: `any-mcp-tatara-orchestrator @ git+https://github.com/szymonrychu/any-mcp-tatara-plugins@v0.1.0#subdirectory=orchestration/orchestrator`.
- Test import: `from any_mcp_tatara_orchestrator import OrchestratorPlugin`.

#### Expected outcome

The orchestrator test suite drives the released plugins-repo plugin, so any-mcp can move to v0.5.0 (which has no `any_mcp.orchestrator`) without breaking a test.

#### Steps

- Red: change the four imports; run the task's verify: fails with ModuleNotFoundError.
- Green: add the dev dependency, `uv lock`, `uv sync`; run the task's verify: passes.

#### Notes

- any-mcp stays at v0.4.0 here; both modules coexist because the plugin package declares `any-mcp` unversioned.
- Leave the rendered `plugin: any_mcp.orchestrator:OrchestratorPlugin` strings in test_on_start.py alone; task orch-render-plugin-sources changes them with on_start.py.
- Orchestrator tests need Docker (testcontainers; check the Docker VM disk first) and run with `VIRTUAL_ENV` unset; if pytest fails with import errors from a stale `.venv` shebang, recreate it with `uv sync`.

- 2026-10-27 done

### S11: orch any-mcp 0.5.0 pin

- Status: done
- Files: `src/agents_orchestrator/settings.py`, `pyproject.toml`, `uv.lock`, `tests/test_settings.py`, `tests/test_images.py`, `README.md`, `tests/golden/session_single.yaml`, `tests/golden/session_two_peers.yaml`
- Verify: `unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_settings.py tests/test_images.py tests/test_render.py tests/test_on_start.py && mise run lint`
- Verified head: 745ca1daa1743320f70bd3fd6c6a54d03252a82e

#### Requirement

Goal G4 (epic README), verbatim: "agents-orchestrator renders the orchestrator plugin from the plugins repo at a pinned ref and accepts a list of extra plugin sources per preset and session, installed in agent pods." Design D7, verbatim: "New settings `any_mcp_plugins_repo` (`ORCH_ANY_MCP_PLUGINS_REPO`, default `https://github.com/szymonrychu/any-mcp-tatara-plugins`) and `any_mcp_plugins_ref` (`ORCH_ANY_MCP_PLUGINS_REF`, default `v0.1.0`, release tag only like `ORCH_ANY_MCP_REF`). ... Settings default `any_mcp_ref` `v0.5.0`." Design D9, verbatim: "`tests/test_images.py` pins the dev dependency tag to `any_mcp_plugins_ref`, as it pins any-mcp's."

Needs a merged upstream: any-mcp tag `v0.5.0` (design Rollout R1). Do not start before `git ls-remote https://github.com/szymonrychu/any-mcp refs/tags/v0.5.0` prints a sha.

Scope (agents-orchestrator):
- `src/agents_orchestrator/settings.py`: `any_mcp_ref = "v0.5.0"`; new `any_mcp_plugins_repo`, `any_mcp_plugins_ref` with the `_TAG_RE` validator of `any_mcp_ref`.
- `pyproject.toml`: `any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.5.0`; `uv.lock` refreshed.
- `README.md`: Configuration rows `ORCH_ANY_MCP_PLUGINS_REPO` and `ORCH_ANY_MCP_PLUGINS_REF`; the `ORCH_ANY_MCP_REF` default and the `## Images` any-mcp sentence name `v0.5.0`, and that sentence names the plugins dev dependency pin too.
- `tests/test_settings.py::test_defaults` asserts any-mcp `v0.4.0`: no longer accurate because the pin moves to v0.5.0 (design D7); it asserts `v0.5.0` and the two plugins defaults. New `test_any_mcp_plugins_ref_must_be_release_tag`.
- `tests/test_images.py`: new `test_plugins_dev_pin_matches_settings_ref`.
- `tests/golden/session_single.yaml`, `tests/golden/session_two_peers.yaml`: regenerated with the golden helper of `tests/test_render.py` (`UPDATE_GOLDEN=1`; the onStart script names the ref).

#### Acceptance conditions

- ac1: the pyproject any-mcp pin, uv.lock and the settings default agree on v0.5.0 [evidence: test:tests/test_images.py::test_pyproject_any_mcp_pin_matches_settings_ref]
- ac2: the plugins dev dependency tag and uv.lock agree with the any_mcp_plugins_ref default [evidence: test:tests/test_images.py::test_plugins_dev_pin_matches_settings_ref]
- ac3: the defaults are any_mcp_ref v0.5.0, any_mcp_plugins_repo https://github.com/szymonrychu/any-mcp-tatara-plugins and any_mcp_plugins_ref v0.1.0 [evidence: test:tests/test_settings.py::test_defaults]
- ac4: ORCH_ANY_MCP_PLUGINS_REF accepts only a vX.Y.Z tag [evidence: test:tests/test_settings.py::test_any_mcp_plugins_ref_must_be_release_tag]
- ac5: README documents both new settings and the v0.5.0 default [evidence: command:grep -qF '`ORCH_ANY_MCP_REF` | `v0.5.0`' README.md && grep -qF '`ORCH_ANY_MCP_PLUGINS_REF` | `v0.1.0`' README.md && grep -qF '`ORCH_ANY_MCP_PLUGINS_REPO`' README.md]
- ac6: the settings, images, render, onStart, README and spec validation tests pass with the regenerated goldens [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_settings.py tests/test_images.py tests/test_render.py tests/test_on_start.py tests/test_readme_api.py tests/test_sessions_repo.py]
- ac7: lint passes [evidence: command:mise run lint]

#### Files

- `src/agents_orchestrator/settings.py`
- `pyproject.toml`
- `uv.lock`
- `tests/test_settings.py`
- `tests/test_images.py`
- `README.md`
- `tests/golden/session_single.yaml`
- `tests/golden/session_two_peers.yaml`

#### Interfaces

- `settings.py:Settings.any_mcp_ref = "v0.5.0"`, `any_mcp_plugins_repo: str = "https://github.com/szymonrychu/any-mcp-tatara-plugins"`, `any_mcp_plugins_ref: str = "v0.1.0"` (env `ORCH_ANY_MCP_PLUGINS_REPO`, `ORCH_ANY_MCP_PLUGINS_REF`), the ref validated by `_TAG_RE`.
- Consumed by task orch-render-plugin-sources (`k8s/on_start.py`).

#### Expected outcome

The orchestrator runs on any-mcp v0.5.0 (its spec validation understands `source` entries) and knows the plugins repo and tag to render.

#### Steps

- Red: update `test_defaults`, add `test_any_mcp_plugins_ref_must_be_release_tag` and `test_plugins_dev_pin_matches_settings_ref`; run `unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_settings.py tests/test_images.py`: fails.
- Green: settings, pyproject, `uv lock`, README; regenerate goldens with `UPDATE_GOLDEN=1`; run the task's verify: passes.

#### Notes

- `tests/test_settings.py:test_env_names_documented_in_readme` requires every setting documented as `ORCH_<NAME>` in README `## Configuration`.
- The golden diff is the any-mcp ref only; on_start.py does not change here.
- Orchestrator tests need Docker (testcontainers) and `VIRTUAL_ENV` unset; recreate a stale `.venv` with `uv sync`.
- (orchestrator note 2026-10-27) orch-plugins-dev-dependency added `[tool.uv] override-dependencies = ["any-mcp @ git+https://github.com/szymonrychu/any-mcp@v0.4.0"]` to pyproject.toml because the plugins package's workspace pins any-mcp v0.5.0 and uv refused two URLs. This task's pin move to v0.5.0 must bump that override to v0.5.0 or remove it if uv no longer needs it, and uv.lock must resolve one any-mcp.

- 2026-10-27 done

### S12: orch any-mcp sources spec

- Status: done
- Files: `src/agents_orchestrator/spec.py`, `openapi.json`, `README.md`, `MEMORY.md`, `tests/test_spec_any_mcp_sources.py`
- Verify: `unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_spec_any_mcp_sources.py tests/test_readme_api.py tests/test_sessions_repo.py && mise run lint`
- Verified head: ff5421890ea722b67924fd2735b107ff37e23426

#### Requirement

Goal G4 (epic README), verbatim: "agents-orchestrator renders the orchestrator plugin from the plugins repo at a pinned ref and accepts a list of extra plugin sources per preset and session, installed in agent pods." User request, verbatim: "In webUI add ability to provide links to such plugins (defined by repo, or dir in repo in git ref) (plus button, shows line textbox where it can be pasted- multiple plugins can be provided)." Design D8, verbatim: "`SessionSpec.any_mcp_sources: list[str] | None = None`, sparse and create-time (name avoids `spec.wrapper.plugins`). Validation: at most 20 entries of at most 500 characters (my call, the init_scripts caps' shape), each parsed by `any_mcp.sources.parse_source`; only `git::https://` and `github.com/` sources (gate Q1); each source renders as the plugin entry `{name, source}` with the name derived from the last subdir segment, else the repo name without `.git`, lower-cased, characters outside `[a-z0-9_-]` replaced by `-`, cut to 20 (my call); a name that does not match any-mcp's name pattern, repeats another derived name, equals `orchestrator`, or equals a plugin name of the effective any-mcp config (the spec's, else the settings default) is an error naming the index. ... `any_mcp_config` plugin entries with a `source` follow the same remote-only rule (gate Q1). No host allowlist (gate Q2)."

Scope (agents-orchestrator):
- `src/agents_orchestrator/spec.py`: the field, `ANY_MCP_SOURCES_MAX = 20`, `ANY_MCP_SOURCE_MAX_CHARS = 500`, a field validator (count, length, non-empty, any-mcp's parser, remote https only), `source_plugin_name(source: str) -> str` (used by task orch-render-plugin-sources), and in `validate_spec` the name checks against the effective any-mcp config and the remote-only rule for `any_mcp_config` entries with a `source`.
- `openapi.json`: regenerated (`uv run python -m agents_orchestrator.api.openapi > openapi.json`).
- `README.md`: the spec field in the session spec documentation, with the accepted forms and the name rule.
- `MEMORY.md`: a dated entry for the derived names and the remote-only rule, with the why.
- New `tests/test_spec_any_mcp_sources.py`.

#### Acceptance conditions

- ac1: a preset or session spec without any_mcp_sources stores and returns no such key [evidence: test:tests/test_spec_any_mcp_sources.py::test_sparse_when_unset]
- ac2: git::https and github.com/ sources validate and round-trip in order [evidence: test:tests/test_spec_any_mcp_sources.py::test_remote_sources_accepted]
- ac3: local paths, git::ssh, git::file and any string any-mcp's parser refuses are errors naming the index and the reason [evidence: test:tests/test_spec_any_mcp_sources.py::test_refused_sources]
- ac4: more than 20 entries, an entry over 500 characters and an empty entry are refused [evidence: test:tests/test_spec_any_mcp_sources.py::test_caps]
- ac5: the derived name is the last subdir segment, else the repo name without .git, lower-cased, other characters replaced by -, cut to 20 [evidence: test:tests/test_spec_any_mcp_sources.py::test_source_plugin_name]
- ac6: a derived name that is invalid, repeated, equal to orchestrator, or equal to a plugin name of the spec's any_mcp_config, else of the settings default config, is refused naming the index [evidence: test:tests/test_spec_any_mcp_sources.py::test_name_collisions_refused]
- ac7: any_mcp_config plugin entries with a local or non-https source are refused [evidence: test:tests/test_spec_any_mcp_sources.py::test_any_mcp_config_sources_remote_only]
- ac8: creating a preset with an invalid source answers 422 naming any_mcp_sources and the index [evidence: test:tests/test_spec_any_mcp_sources.py::test_api_refuses_invalid_source]
- ac9: openapi.json matches the app [evidence: test:tests/test_readme_api.py::test_openapi_json_matches_app]
- ac10: README documents the field [evidence: command:grep -qF 'any_mcp_sources' README.md]
- ac11: lint passes [evidence: command:mise run lint]

#### Files

- `src/agents_orchestrator/spec.py`
- `openapi.json`
- `README.md`
- `MEMORY.md`
- `tests/test_spec_any_mcp_sources.py`

#### Interfaces

- `spec.py:SessionSpec.any_mcp_sources: list[str] | None = None`; `ANY_MCP_SOURCES_MAX = 20`; `ANY_MCP_SOURCE_MAX_CHARS = 500`.
- `spec.py:source_plugin_name(source: str) -> str`: the D8 derivation on a parsed source (no validation of the result; validation reports bad names).
- Errors keep the `validate_spec` / field-validator style: `any_mcp_sources[<i>]: <reason>`.
- OpenAPI: `SessionSpec.any_mcp_sources` as an optional array of strings (consumed by task web-preset-plugin-sources through `npm run sync:api`).

#### Expected outcome

Presets and sessions accept a sparse list of remote plugin sources, refuse anything the pods could not install or that would clash with another plugin name, and the API schema shows the field.

#### Steps

- Red: write `tests/test_spec_any_mcp_sources.py`; run `unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_spec_any_mcp_sources.py`: fails.
- Green: spec.py; regenerate `openapi.json` (`uv run python -m agents_orchestrator.api.openapi > openapi.json`); README and MEMORY; run the task's verify: passes.

#### Notes

- Rulings and their pin tests: remote https git only, local, ssh and file refused (test_refused_sources; gate Q1 recommended answer); names collide also with the settings default any-mcp config when the spec has none (test_name_collisions_refused); a stored preset is re-validated on PUT like other fields (no "unchanged from stored" exemption).
- Persistence needs no migration: spec is jsonb; presets dump `exclude_unset`, sessions `exclude_none`, so `None` stays sparse (test_sparse_when_unset).
- Precedent for list caps and messages: `init_scripts` (`spec.py:483`).
- Orchestrator tests need Docker (testcontainers) and `VIRTUAL_ENV` unset; recreate a stale `.venv` with `uv sync`. Never the word "cluster" in new text (`tests/test_nomenclature.py`).

- 2026-10-27 done

### S13: orch render plugin sources

- Status: done
- Files: `src/agents_orchestrator/k8s/on_start.py`, `tests/test_on_start.py`, `tests/test_render.py`, `tests/golden/session_single.yaml`, `tests/golden/session_two_peers.yaml`, `tests/e2e/test_e2e_kind.py`, `README.md`, `MEMORY.md`
- Verify: `unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_on_start.py tests/test_render.py && mise run lint`
- Verified head: 0ad4102b1c01097e4aaea023639ec9e8b3ab78f7

#### Requirement

Goal G4 (epic README), verbatim: "agents-orchestrator renders the orchestrator plugin from the plugins repo at a pinned ref and accepts a list of extra plugin sources per preset and session, installed in agent pods." Goal G6, verbatim: "Deployed through agents-helmfile; agent sessions still get the orchestrator tools." Design D7, verbatim: "The reserved entry keeps name, namespace, allow and config, and replaces `plugin` with `source: git::<repo>//orchestration/orchestrator?ref=<ref>`. The onStart script, after writing the config, runs `/opt/any-mcp/bin/any-mcp plugins install --config /opt/any-mcp/etc/any-mcp.yaml` before `--help`." Design D8, verbatim: "each source renders as the plugin entry `{name, source}` ... Rendered after the base config's entries and before the reserved entry."

Scope (agents-orchestrator):
- `src/agents_orchestrator/k8s/on_start.py`: `PLUGIN_CLASS` goes; the reserved entry carries `source` built from `settings.any_mcp_plugins_repo` and `settings.any_mcp_plugins_ref`; `any_mcp_config` appends one `{name: source_plugin_name(s), source: s}` per `spec.any_mcp_sources` entry after the base entries and before the reserved entry (also when the reserved entry is omitted); `render_on_start` runs the install line after the heredoc and before `--help`, on every run (not only when `.ref` changes).
- Tests no longer accurate because the reserved entry is now a source (design D7): the tests of `tests/test_on_start.py` that pin the entry's `plugin` value (`test_hive_entry_and_allow`, the alone-session entry test, `test_user_orchestrator_entry_replaced`) assert the `source` instead; `tests/test_render.py` gains the install-line and hash tests.
- `tests/golden/session_single.yaml`, `tests/golden/session_two_peers.yaml`: regenerated (`UPDATE_GOLDEN=1`).
- `tests/e2e/test_e2e_kind.py`: the on-start assertions expect the orchestrator entry's `source` and that `/opt/any-mcp/bin/pip show any-mcp-tatara-orchestrator` succeeds in a session pod.
- `README.md`: the onStart and any-mcp sections describe the source install and `any_mcp_sources` rendering.
- `MEMORY.md`: a dated entry: the reserved plugin comes from the plugins repo at a pinned tag, installed by `any-mcp plugins install` in onStart, with the why.

#### Acceptance conditions

- ac1: the reserved entry, for every session that rendered it before, has source git::<plugins repo>//orchestration/orchestrator?ref=<plugins ref> and no plugin key, keeps name, namespace, allow and config, and validates under the installed any-mcp [evidence: test:tests/test_on_start.py::test_reserved_entry_is_plugins_repo_source]
- ac2: each any_mcp_sources entry renders as name and source after the base config's entries and before the reserved entry, also when the reserved entry is omitted [evidence: test:tests/test_on_start.py::test_any_mcp_sources_rendered]
- ac3: the onStart script runs any-mcp plugins install --config with the config path after writing the config and before --help, on every run [evidence: test:tests/test_render.py::test_on_start_installs_plugin_sources]
- ac4: a different ORCH_ANY_MCP_PLUGINS_REF or any_mcp_sources changes the config hash [evidence: test:tests/test_render.py::test_config_hash_follows_plugin_sources]
- ac5: the onStart, render, README and nomenclature tests pass with the regenerated goldens [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_on_start.py tests/test_render.py tests/test_readme_api.py tests/test_nomenclature.py]
- ac6: the kind e2e module still collects with the source assertions (it runs in CI through mise run test:e2e) [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q --collect-only -m e2e tests/e2e/test_e2e_kind.py]
- ac7: lint passes [evidence: command:mise run lint]

#### Files

- `src/agents_orchestrator/k8s/on_start.py`
- `tests/test_on_start.py`
- `tests/test_render.py`
- `tests/golden/session_single.yaml`
- `tests/golden/session_two_peers.yaml`
- `tests/e2e/test_e2e_kind.py`
- `README.md`
- `MEMORY.md`

#### Interfaces

- `k8s/on_start.py`: reserved entry `{"name": "orchestrator", "namespace": "orchestrator", "source": f"git::{settings.any_mcp_plugins_repo}//orchestration/orchestrator?ref={settings.any_mcp_plugins_ref}", "allow": ..., "config": ...}`; user source entries `{"name": source_plugin_name(s), "source": s}`.
- onStart script order: install any-mcp when `.ref` differs, write the config heredoc, `/opt/any-mcp/bin/any-mcp plugins install --config /opt/any-mcp/etc/any-mcp.yaml`, `/opt/any-mcp/bin/any-mcp --help >/dev/null`.
- Unchanged: `RESERVED_PLUGIN`, `main_agent_only_tools = ["mcp__any-mcp__orchestrator_*"]`, the any-mcp MCP server command, `on_error: deny`.

#### Expected outcome

Every agent pod installs the orchestrator plugin from the plugins repo at the pinned tag plus the session's extra sources before claude starts, and its leader sees the same orchestrator tools as before.

#### Steps

- Red: write `test_reserved_entry_is_plugins_repo_source`, `test_any_mcp_sources_rendered`, `test_on_start_installs_plugin_sources`, `test_config_hash_follows_plugin_sources`, and update the inaccurate entry assertions named in the Requirement; run `unset VIRTUAL_ENV && uv run --frozen pytest -q tests/test_on_start.py tests/test_render.py`: fails.
- Green: on_start.py; regenerate goldens with `UPDATE_GOLDEN=1`; update the e2e assertions; run the task's verify: passes. README and MEMORY; run ac5, ac6, ac7: pass.

#### Notes

- Rulings and their pin tests: the install line runs on every onStart run, not only on a new any-mcp ref (test_on_start_installs_plugin_sources: the stub `any-mcp` logs `plugins install` on the second run too); source entries sit before the reserved entry (test_any_mcp_sources_rendered); the reserved entry exists for exactly the sessions it did before (test_reserved_entry_is_plugins_repo_source, both alone and hive).
- The `test_render.py` stub `python3 -m venv` writes fake `pip` and `any-mcp` scripts that log their argv: extend the existing pattern.
- An install failure fails the onStart hook, which blocks the session (`on_error: deny`): that is the intended visible failure (design D4).
- The kind e2e runs in CI (`mise run test:e2e`); locally ac6 only proves it collects.
- Orchestrator tests need Docker (testcontainers) and `VIRTUAL_ENV` unset; recreate a stale `.venv` with `uv sync`. Never the word "cluster" in new text.

- 2026-10-27 done

### S14: web preset plugin sources

- Status: done
- Files: `openapi/orchestrator.json`, `openapi/orchestrator.source`, `src/api/schema.d.ts`, `src/sessions/sessionSpecForm.ts`, `src/presets/PresetForm.tsx`, `src/presets/PresetForm.test.tsx`
- Verify: `npx vitest run src/presets/PresetForm.test.tsx && npm run build && mise run lint`
- Verified head: 97b68456158eeb8ede9460b5dea424c6fcd48bdb

#### Requirement

User request, verbatim: "In webUI add ability to provide links to such plugins (defined by repo, or dir in repo in git ref) (plus button, shows line textbox where it can be pasted- multiple plugins can be provided)." Goal G5 (epic README), verbatim: "The agents-web preset form edits the plugin sources: a "+" button adds a one-line text box per source, several sources allowed." Orchestrator design call, verbatim: "agents-web: preset form "any-mcp plugins" section: a "+" button adds a one-line text box per source, each removable, validated against the notation with an inline error, stored as spec.any_mcp_sources." Design D10, verbatim: "a "+" icon button (precedent `src/chat/ScaleControl.tsx`, `@mui/icons-material/Add`) adds a one-line text box, each row removable, an inline error per row, stored as `spec.any_mcp_sources` only when non-empty."

Scope (agents-web, base: the merged state of epic cross-session-messaging-and):
- Sync the orchestrator API: `npm run sync:api -- orchestrator` (with `--from <the epic's agents-orchestrator tree>` when the default `../agents-orchestrator` is not it) after task orch-any-mcp-sources-spec is committed there; this rewrites `openapi/orchestrator.json`, `openapi/orchestrator.source` and `src/api/schema.d.ts` (generated, never hand-edited).
- `src/sessions/sessionSpecForm.ts`: `FormValues.anyMcpSources: string[]` (blank `[]`), per-row errors in `FormErrors` like `initScripts`, `stateFromPreset` loads `any_mcp_sources`, `validate` uses `pluginSourceError` per row, `toPresetSpec` writes the trimmed rows only when there is at least one.
- `src/presets/PresetForm.tsx`: an "any-mcp plugins" section after the any-mcp config field: one single-line `TextField` per row with an inline error and a remove `IconButton`, and a "+" `IconButton` (`@mui/icons-material/Add`, aria-label "Add any-mcp plugin") that appends an empty row; add the key to the `text()` exclusion type.
- `src/presets/PresetForm.test.tsx`: the tests in the acceptance conditions.
- No text uses the word "cluster" (`src/nomenclature.test.ts`).

#### Acceptance conditions

- ac1: the section starts with no rows and saving an untouched preset sends no any_mcp_sources [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t 'any-mcp plugins sparse by default']
- ac2: each click on the + button adds a one-line text box, and several pasted sources save as any_mcp_sources in row order, trimmed [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t 'any-mcp plugins add rows and save']
- ac3: a row's remove button removes that row, and removing every row saves no any_mcp_sources [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t 'any-mcp plugins remove rows']
- ac4: an invalid row shows its inline error and blocks saving, and a preset with sources loads one row per source [evidence: command:npx vitest run src/presets/PresetForm.test.tsx -t 'any-mcp plugins validate and load']
- ac5: the vendored orchestrator schema has any_mcp_sources and the generated types match it [evidence: command:grep -q '"any_mcp_sources"' openapi/orchestrator.json && npm run check:api]
- ac6: the type check and build pass [evidence: command:npm run build]
- ac7: the whole web suite, including the nomenclature guard, passes [evidence: command:npm test]
- ac8: lint passes [evidence: command:mise run lint]

#### Files

- `openapi/orchestrator.json`
- `openapi/orchestrator.source`
- `src/api/schema.d.ts`
- `src/sessions/sessionSpecForm.ts`
- `src/presets/PresetForm.tsx`
- `src/presets/PresetForm.test.tsx`

#### Interfaces

- `sessionSpecForm.ts`: `FormValues.anyMcpSources: string[]`, `FormErrors.anyMcpSources?: (string | undefined)[]`, `SetKey` gains `'anyMcpSources'`; `toPresetSpec` writes `spec.any_mcp_sources` (trimmed rows) only when the list is non-empty.
- `PresetForm.tsx`: "any-mcp plugins" section; add button `aria-label="Add any-mcp plugin"` with the `Add` icon; remove buttons `aria-label="Remove any-mcp plugin <n>"`; one single-line `TextField` per row labelled "any-mcp plugin <n>".
- Generated: `openapi/orchestrator.json`, `openapi/orchestrator.source`, `src/api/schema.d.ts` from the orchestrator tree carrying task orch-any-mcp-sources-spec.

#### Expected outcome

A preset author clicks "+", pastes a source per row, sees an inline error on a bad one, and the saved preset carries `any_mcp_sources` in row order; an untouched form stays sparse.

#### Steps

- Sync: `npm run sync:api -- orchestrator` (with `--from <orchestrator tree>` if needed); run `npm run check:api`: passes.
- Red: write the four PresetForm tests; run `npx vitest run src/presets/PresetForm.test.tsx`: fails.
- Green: sessionSpecForm.ts and PresetForm.tsx; run the task's verify, then `npm test`: pass.

#### Notes

- Row-list precedent: init scripts (`PresetForm.tsx` around the "Add init script" button) and `errors.initScripts?.[i]`; "+" icon precedent `src/chat/ScaleControl.tsx`.
- Rulings and their pin tests: rows are trimmed on save (add rows and save); an empty row is an error, not silently dropped (validate and load); removing every row makes the field sparse again (remove rows).
- The preset copy path (`copiedSpec`) copies the spec as is; no change needed.
- No text uses the word "cluster" (`src/nomenclature.test.ts`); `npm run build` runs `tsc -b`.

- 2026-10-27 done

### S15: helmfile deploy pin

- Status: done
- Files: `helmfile.yaml.gotmpl`, `values/agents-orchestrator/common.yaml`, `values/agents-web/common.yaml`, `tests/test_orchestrator_release.py`, `tests/test_web_release.py`, `tests/test_smoke_script.py`, `README.md`
- Verify: `uv run --frozen pytest -q tests/test_orchestrator_release.py tests/test_web_release.py tests/test_smoke_script.py && mise run lint`
- Verified head: 65fc75ba3c8f8ee0580d410cdab7e37a5a8b240c

#### Requirement

Goal G6 (epic README), verbatim: "Deployed through agents-helmfile; agent sessions still get the orchestrator tools." Orchestrator design call, verbatim: "agents-helmfile: pin new orchestrator chart/image, ORCH_ANY_MCP_REF v0.5.0 and ORCH_ANY_MCP_PLUGINS_REF tag". Design D11, verbatim: "agents-helmfile pins the new orchestrator and web charts and images, `ORCH_ANY_MCP_REF: v0.5.0` and `ORCH_ANY_MCP_PLUGINS_REF: v0.1.0`."

Needs merged upstreams: the agents-orchestrator PR of this epic merged with its image `b3a2975` and chart `0.1.0-main.b3a2975` published by main CI; the agents-web PR merged with its image and chart `0.1.0-main.4701820` published (design Rollout R3). The shas are filled in by `ticket.py amend` before dispatch.

Scope (agents-helmfile, base: the merged state of epic cross-session-messaging-and):
- `helmfile.yaml.gotmpl`: agents-orchestrator chart `0.1.0-main.b3a2975`; agents-web chart `0.1.0-main.4701820`.
- `values/agents-orchestrator/common.yaml`: `image.tag: b3a2975` (quoted if all digits); `env.ORCH_ANY_MCP_REF: v0.5.0`; new `env.ORCH_ANY_MCP_PLUGINS_REPO: https://github.com/szymonrychu/any-mcp-tatara-plugins` and `env.ORCH_ANY_MCP_PLUGINS_REF: v0.1.0` with a comment: the reserved orchestrator plugin is installed from that repo at that tag.
- `values/agents-web/common.yaml`: `image.tag: "4701820"`.
- Tests no longer accurate because the pins move (design D11): `tests/test_orchestrator_release.py` (`PIN`; `test_any_mcp_configured_for_new_sessions` asserts v0.5.0 and the two plugins values), `tests/test_web_release.py` (the agents-web sha), `tests/test_smoke_script.py::test_any_mcp_version_is_the_orchestrator_values_ref` (`0.5.0`).
- `README.md`: the any-mcp line names the plugins repo source of the orchestrator tools.
- Never the word "cluster" outside the allowed phrases of `tests/test_nomenclature.py`.

#### Acceptance conditions

- ac1: the orchestrator chart version and image tag agree on the orchestrator merge sha [evidence: test:tests/test_orchestrator_release.py::test_orchestrator_pin_matches_image]
- ac2: new sessions install any-mcp v0.5.0 and the orchestrator plugin from https://github.com/szymonrychu/any-mcp-tatara-plugins at v0.1.0 [evidence: test:tests/test_orchestrator_release.py::test_any_mcp_configured_for_new_sessions]
- ac3: the agents-web chart version and image tag agree on the agents-web merge sha [evidence: test:tests/test_web_release.py::test_web_pin_matches_image]
- ac4: the smoke script expects any-mcp 0.5.0 from the orchestrator values [evidence: test:tests/test_smoke_script.py::test_any_mcp_version_is_the_orchestrator_values_ref]
- ac5: the whole helmfile test suite, including the stale-path and nomenclature tests, passes [evidence: command:mise run test]
- ac6: lint (ruff, shellcheck, gitleaks) passes [evidence: command:mise run lint]

#### Files

- `helmfile.yaml.gotmpl`
- `values/agents-orchestrator/common.yaml`
- `values/agents-web/common.yaml`
- `tests/test_orchestrator_release.py`
- `tests/test_web_release.py`
- `tests/test_smoke_script.py`
- `README.md`

#### Interfaces

- `values/agents-orchestrator/common.yaml` `env`: `ORCH_ANY_MCP_REPO`, `ORCH_ANY_MCP_REF: v0.5.0`, `ORCH_ANY_MCP_PLUGINS_REPO: https://github.com/szymonrychu/any-mcp-tatara-plugins`, `ORCH_ANY_MCP_PLUGINS_REF: v0.1.0` (read by `scripts/smoke.sh` in task helmfile-smoke-plugin-tools).
- Chart and image pins: `0.1.0-main.<sha7>` and `<sha7>` for agents-orchestrator and agents-web.

#### Expected outcome

`mise run diff` shows only the new orchestrator and web releases with the new settings; after the apply new sessions install any-mcp v0.5.0 and the orchestrator plugin from the plugins repo.

#### Steps

- Red: update the pinned values in the three test files; run `uv run --frozen pytest -q tests/test_orchestrator_release.py tests/test_web_release.py tests/test_smoke_script.py`: fails.
- Green: helmfile.yaml.gotmpl and the two values files, README; run the task's verify, then `mise run test`: pass.

#### Notes

- The shas come from Rollout R3 through `ticket.py amend` before dispatch (precedent: epic leader-auto-handover task helmfile-deploy-pin); an all-digit sha7 is quoted in YAML.
- The apply, diff and smoke are orchestrator steps (Rollout R4, R5), never this task's.
- Never the word "cluster" outside the allowed phrases of `tests/test_nomenclature.py`.

- 2026-10-27 done

### S16: Orchestrator refuses credentials in plugin source URLs

- Status: done
- Files: `src/agents_orchestrator/spec.py`, `tests/test_spec_any_mcp_sources.py`, `README.md`
- Verify: `unset VIRTUAL_ENV && uv run --frozen pytest -q -o addopts="" tests/test_spec_any_mcp_sources.py && mise run lint`
- Verified head: faedbd7564f86a7079049f14a095532ac23c7c75

#### Requirement

Security review finding (LOW, accepted as a fix 2026-10-27): a remote source with credentials in the URL, such as `git::https://user:token@github.com/o/r.git`, passes validation, and any-mcp then writes the raw source into install error messages (onStart hook output) and into its plaintext manifest.json. The orchestrator must refuse any remote any_mcp_sources entry (and any source in any_mcp_config) whose URL carries userinfo (a `@` before the host, user or user:password), with the message form `plugin source '<text>': credentials in the URL are not allowed`, never echoing the secret part in the error (redact everything before `@` in the echoed text). The reserved plugin source rendered from settings is unaffected.

#### Acceptance conditions

- ac1: any_mcp_sources entries with `user@`, `user:pass@` or `:token@` before the host are refused 422 with the credentials message, and the response does not contain the secret part [evidence: test:tests/test_spec_any_mcp_sources.py::test_source_with_credentials_refused]
- ac2: spec, readme and nomenclature tests and lint pass [evidence: command:unset VIRTUAL_ENV && uv run --frozen pytest -q -o addopts="" tests/test_spec_any_mcp_sources.py tests/test_readme_api.py tests/test_nomenclature.py && mise run lint]

#### Files

- `src/agents_orchestrator/spec.py`
- `tests/test_spec_any_mcp_sources.py`
- `README.md`

#### Interfaces

- Same message form as the existing source checks; parity between orchestrator (spec.py remote_source_problem) and web (pluginSource.ts).

#### Expected outcome

A source with credentials in its URL is refused with a redacted message.

#### Steps

- Red: add the test; run the task's verify; expect failure.
- Green: add the check; run the task's verify on the committed HEAD.

#### Notes

- From the phase-5 security review (sonnet), LOW finding accepted as a fix. any-mcp v0.5.0 itself still accepts userinfo for local use; a later any-mcp release may align (noted, not in scope).
- Keep the word cluster out of new text.

- 2026-10-27 done

### S17: Web form refuses credentials in plugin source URLs

- Status: done
- Files: `src/presets/pluginSource.ts`, `src/presets/pluginSource.test.ts`
- Verify: `npx vitest run src/presets/pluginSource.test.ts && npm run build && mise run lint`
- Verified head: cd1eb81203bc605fc11d0e08a78d2d6a7ba7120f

#### Requirement

Security review finding (LOW, accepted as a fix 2026-10-27): the preset form's plugin source check (src/presets/pluginSource.ts) accepts a remote source with credentials in the URL, such as `git::https://user:token@github.com/o/r.git`. Refuse any remote source whose URL carries userinfo (a `@` before the host), with the message `plugin source '<text>': credentials in the URL are not allowed`, redacting everything before `@` in the echoed text, so the web matches the orchestrator's rule.

#### Acceptance conditions

- ac1: sources with `user@`, `user:pass@` or `:token@` before the host are refused with the credentials message and the message does not contain the secret part [evidence: test:src/presets/pluginSource.test.ts]
- ac2: the parser tests, build and lint pass [evidence: command:npx vitest run src/presets/pluginSource.test.ts && npm run build && mise run lint]

#### Files

- `src/presets/pluginSource.ts`
- `src/presets/pluginSource.test.ts`

#### Interfaces

- Same message form as the existing source checks; parity between orchestrator (spec.py remote_source_problem) and web (pluginSource.ts).

#### Expected outcome

A source with credentials in its URL is refused with a redacted message.

#### Steps

- Red: add the test; run the task's verify; expect failure.
- Green: add the check; run the task's verify on the committed HEAD.

#### Notes

- From the phase-5 security review (sonnet), LOW finding accepted as a fix. any-mcp v0.5.0 itself still accepts userinfo for local use; a later any-mcp release may align (noted, not in scope).
- Keep the word cluster out of new text.

- 2026-10-27 done

### S18: helmfile smoke plugin tools

- Status: done
- Files: `scripts/smoke.sh`, `tests/test_smoke_script.py`, `README.md`
- Verify: `uv run --frozen pytest -q tests/test_smoke_script.py && mise run lint`
- Verified head: 3fd172f

#### Requirement

Goal G6 (epic README), verbatim: "Deployed through agents-helmfile; agent sessions still get the orchestrator tools." Goal G4, verbatim: "... accepts a list of extra plugin sources per preset and session, installed in agent pods." Orchestrator design call, verbatim: "smoke proves a session lists orchestrator tools from the plugins repo." Design D11, verbatim: "Smoke proves, in the smoke session's pod, that the `any-mcp-tatara-orchestrator` distribution is installed, the rendered config's orchestrator entry names the plugins repo at the pinned ref, and `any-mcp --list-tools` lists `orchestrator_sessions_list`; and that a session created with `any_mcp_sources: ["git::https://github.com/szymonrychu/any-mcp//examples/petstore?ref=v0.5.0"]` lists `petstore_` tools (petstore is a packaged plugin that loads with an empty config). Live steps run by the orchestrator (Rollout)." Retro (matrix-read-receipts, agents-matrix-connector-depl): live proof is an orchestrator-run step, so this task writes and offline-tests the steps; the orchestrator runs `mise run smoke` after the apply (design Rollout R5).

Scope (agents-helmfile `scripts/smoke.sh`, in the style of its existing steps, same parameters):
- Plugin tools step, in the existing smoke session's pod after the any-mcp version check: `kubectl exec <pod> -c ccw -- /opt/any-mcp/bin/pip show any-mcp-tatara-orchestrator` succeeds; `/opt/any-mcp/etc/any-mcp.yaml` in the pod contains `any-mcp-tatara-plugins//orchestration/orchestrator?ref=<ORCH_ANY_MCP_PLUGINS_REF>` (read from the orchestrator values like `ORCH_ANY_MCP_REF`); `/opt/any-mcp/bin/any-mcp --config /opt/any-mcp/etc/any-mcp.yaml --list-tools` in the pod lists `orchestrator_sessions_list`.
- Extra source step: a session `smoke-src-<ts>` created with a raw spec (`replicas: 1`, `any_mcp_sources: ["git::https://github.com/szymonrychu/any-mcp//examples/petstore?ref=v<any-mcp version>"]`) gets a Ready pod whose `--list-tools` lists a tool starting with `petstore_`.
- The cleanup trap deletes `smoke-src-<ts>` on every exit.
- The header comment and `README.md` (`mise run smoke` paragraph) describe both steps; never the word "cluster" outside the allowed phrases of `tests/test_nomenclature.py`.
- `tests/test_smoke_script.py`: tests for both steps with the existing fake kubectl and curl harness.

#### Acceptance conditions

- ac1: the plugin tools step passes when pip show finds any-mcp-tatara-orchestrator, the pod config names the plugins repo source at ORCH_ANY_MCP_PLUGINS_REF and list-tools lists orchestrator_sessions_list, and fails smoke naming the check when any of these does not hold [evidence: test:tests/test_smoke_script.py::test_orchestrator_plugin_from_plugins_repo]
- ac2: the extra source step creates its session with the petstore source at the pinned any-mcp tag, passes when that pod lists a petstore_ tool, and fails smoke naming the check otherwise [evidence: test:tests/test_smoke_script.py::test_extra_plugin_source_step]
- ac3: the trap deletes the extra source session on success and on a failure [evidence: test:tests/test_smoke_script.py::test_plugin_source_session_cleaned_up]
- ac4: the new steps never print the agent token or any other secret [evidence: test:tests/test_smoke_script.py::test_plugin_steps_print_no_token]
- ac5: the smoke script tests and the nomenclature and hygiene guards pass [evidence: command:uv run --frozen pytest -q tests/test_smoke_script.py tests/test_nomenclature.py tests/test_repo_hygiene.py]
- ac6: lint (ruff, shellcheck, gitleaks) passes [evidence: command:mise run lint]

#### Files

- `scripts/smoke.sh`
- `tests/test_smoke_script.py`
- `README.md`

#### Interfaces

- `scripts/smoke.sh`: reads `ORCH_ANY_MCP_PLUGINS_REF` from the orchestrator values the way it reads `ORCH_ANY_MCP_REF`; failure lines `smoke: FAIL: <check>`; new session name `smoke-src-<ts>`.
- In-pod commands: `/opt/any-mcp/bin/pip show any-mcp-tatara-orchestrator`, `cat /opt/any-mcp/etc/any-mcp.yaml`, `/opt/any-mcp/bin/any-mcp --config /opt/any-mcp/etc/any-mcp.yaml --list-tools`.

#### Expected outcome

`mise run smoke` after the apply proves the live sessions get the orchestrator tools from the plugins repo at the pinned tag and that a per-session extra source installs in its pod.

#### Steps

- Red: write the four tests with the existing fake kubectl and curl harness (fake answers for pip show, the config cat and list-tools); run `uv run --frozen pytest -q tests/test_smoke_script.py`: fails.
- Green: the two steps and the trap entry in smoke.sh, README; run the task's verify: passes.

#### Notes

- Rulings and their pin tests: the extra source uses the petstore example at the any-mcp tag from the values (test_extra_plugin_source_step asserts the created spec); the list-tools output is matched on `orchestrator_sessions_list` and a `petstore_` prefix, never on a full list (test_orchestrator_plugin_from_plugins_repo, test_extra_plugin_source_step).
- `--list-tools` in the pod expands `${ORCH_AGENT_*}` from the container env; the exec must not echo it (test_plugin_steps_print_no_token).
- Live run is Rollout R5, by the orchestrator, not this task.
- Never the word "cluster" outside the allowed phrases of `tests/test_nomenclature.py` (`in-cluster` is allowed).

- 2026-10-27 done

- 2026-10-27 done

## Files to delete

none recorded in the epic format

## Final verify

none recorded in the epic format

## After merge

none
