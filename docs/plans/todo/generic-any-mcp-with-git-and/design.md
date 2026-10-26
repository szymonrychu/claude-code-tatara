# Generic any-mcp with git and local plugin sources design

## Summary

any-mcp drops its only platform-specific plugin (the orchestrator plugin) and gains plugin sources in
a Terraform/go-getter subset notation: local directories and git repos with an optional `//subdir` and
`?ref=`. A source is a Python package that any-mcp fetches, pip-installs into its own environment and
loads by its `any_mcp.plugins` entry point. The orchestrator plugin moves, unchanged in tools and
behaviour, to the new repo any-mcp-tatara-plugins under the topic `orchestration/`. agents-orchestrator
renders its reserved plugin entry as a source pinned to a plugins-repo tag and accepts a per-session
`any_mcp_sources` list; agents-web edits that list with a "+" button; agents-helmfile deploys it.

## Intent and why

User request, verbatim (2026-10-27): "Make anyMcp generic. Create separate any-mcp-tatara-plugins repo,
which will serve as a bucket for platform specific tools. Group them into topics in subdirs. Allow to
install plugins using similar notation as terraform modules allow to. In webUI add ability to provide
links to such plugins (defined by repo, or dir in repo in git ref) (plus button, shows line textbox
where it can be pasted- multiple plugins can be provided). It must still be possible (when using pip
installed any-mcp) to provide path to local dir, where plugin is defined (again- similar to terraform
module handling)."

any-mcp is meant to be reusable outside this platform; today it ships agents-orchestrator tools inside
its own package (MEMORY.md 2026-10-24 decision, reversed here). Sessions should pull platform tools
from a versioned plugin bucket instead.

## Goals

- G1: any-mcp contains no platform-specific plugin; the orchestrator plugin lives in
  any-mcp-tatara-plugins under a topic subdirectory, with the same tools and behaviour.
- G2: any-mcp installs and loads plugins from Terraform-module-like sources: git repo with optional
  //subdir and ?ref=, and local directory paths.
- G3: any-mcp-tatara-plugins is a working repo: topic subdirectories, per-plugin packages, tests and
  lint in CI, documented source notation.
- G4: agents-orchestrator renders the orchestrator plugin from the plugins repo at a pinned ref and
  accepts a list of extra plugin sources per preset and session, installed in agent pods.
- G5: the agents-web preset form edits the plugin sources: a "+" button adds a one-line text box per
  source, several sources allowed.
- G6: deployed through agents-helmfile; agent sessions still get the orchestrator tools.

## Non-goals

- No backward-compatibility alias for the removed any_mcp.orchestrator module.
- No plugin registry or marketplace beyond git and local sources; no `?depth=` or archive (http
  tarball) sources.
- No per-plugin dependency isolation (separate venvs or processes).

## Anti-goals

- An agent session that starts without the orchestrator tools (a broken reserved entry blocks the
  session through onStart `on_error: deny`).
- Any platform name (`/agent/v1`, orchestrator, hive) left in any-mcp's src, examples or docs.
- Git or pip invoked with user-controlled values in option position, or a subdir escaping its checkout.
- A source change that needs a coordinated edit in two parsers with different rules: the web parser
  mirrors the any-mcp grammar and both are pinned by tests on the same cases.

## Constraints

- Python 3.12 in any-mcp and the plugins repo (the scaffold's `python = "3.14.6"` is replaced).
- Execution starts after epic cross-session-messaging-and merges. Base files: its merged state of
  agents-orchestrator `k8s/on_start.py` (session tools for every session, D11 there), settings and
  pyproject pinning any-mcp `v0.4.0`, `tests/test_agent_session_messaging.py`; agents-web
  `sessionSpecForm.ts` and `PresetForm.tsx` with the session option switches; agents-helmfile
  `values/agents-orchestrator/common.yaml`, `tests/test_orchestrator_release.py` and
  `tests/test_smoke_script.py` with the v0.4.0 pins and the session option smoke steps.
- Nomenclature guards in any-mcp, agents-orchestrator, agents-web and agents-helmfile: no new path or
  text uses the word "cluster".
- Cross-repo releases happen between tasks, by the orchestrator, never by implementers (Rollout).
- House rules: no backward compatibility, tests changed only when no longer accurate (named per task),
  retirement tests on `git ls-files`.

## Decisions

### D1: Source notation, a go-getter subset, parsed by one any-mcp module (my call)

`any_mcp.sources.parse_source(text) -> Source` is the only parser in Python (the orchestrator imports
it). Grammar:

- Local: starts with `./`, `../` or `/`. Relative paths resolve against the config file's directory
  (CLI arguments: the working directory). Used in place, never copied. `//` and `?` are not allowed in
  a local source.
- Git: `git::<url>[//<subdir>][?ref=<ref>]`, `<url>` scheme `https`, `ssh` or `file` (my call: `file`
  makes the offline tests possible; scp-like `git@host:o/r` is refused with a hint to use
  `git::ssh://`).
- Shorthand: `github.com/<owner>/<repo>[//<subdir>][?ref=<ref>]` means
  `git::https://github.com/<owner>/<repo>.git...`.
- The query allows only `ref`; `depth`, `sshkey` or any other key is an error naming the key. An empty
  ref, a ref starting with `-`, or a ref outside `[A-Za-z0-9._/-]` or containing `..` is an error.
- Subdir: relative, no leading `/`, no empty or `..` segment.
- Anything else (bare `foo/bar`, `https://...` without `git::`, pip-style `git+https://...`) is an error
  that lists the accepted forms.

Alternatives: pip's `git+https://...@ref#subdirectory=` (rejected: the user asked for Terraform-like
notation); full go-getter (rejected: non-goal, getters beyond git and local not needed).

### D2: Plugin entries take `source`; `plugin` becomes an optional entry-point name for them (my call)

`PluginEntry` gains `source: str | None`; `plugin` becomes optional. Exactly one rule: an entry has a
`plugin` or a `source` or both; with a `source`, `plugin` is an entry-point name (never `module:Class`)
that picks among the source package's `any_mcp.plugins` entry points, required only when the package
declares more than one. The `source` string is validated by `parse_source` at config load. `name` stays
required (my call: names drive tool prefixes and must be known before anything is installed).
Alternative: a top-level `sources:` list (rejected: a source without an entry has no name, namespace,
allow or config).

### D3: Installation: fetch into a cache, pip-install into any-mcp's own environment (my call)

`any_mcp.install` resolves a `Source` to an installed distribution:

- Git: a ref that is a full 40-hex SHA is fetched by SHA (`git fetch --depth 1 origin <sha>`), falling
  back to a `--filter=blob:none` fetch and checkout when the server refuses; a branch or tag (found by
  `git ls-remote`) is a shallow, blob-filtered clone of that ref; anything else (a short SHA) is a
  blob-filtered full clone then `git checkout`; no ref means the remote default branch. Sparse checkout
  limits the tree to the subdir. Every git call puts user values after `--`, runs with a timeout, and
  the resolved subdir must stay inside the checkout (symlinks resolved). A missing subdir is an error
  naming url, ref, resolved SHA and subdir.
- Cache dir `$ANY_MCP_CACHE_DIR`, default `<sys.prefix>/any-mcp-sources` (my call: the cache lives
  with the environment the packages are installed into, so a cache hit means installed). Key
  (normalised url, ref, subdir); a `manifest.json` records per key the source string, resolved SHA,
  checkout dir and distribution name. A SHA ref is cached forever; a branch, tag or default-branch
  entry is reused as is at startup and re-resolved only by an explicit install, like `terraform init
  -upgrade`.
- The source directory must hold a `pyproject.toml` with `[project].name`; it is installed with
  `<sys.executable> -m pip install` (git sources; local sources with `-e`, so they stay in place and
  edits show on restart, my call). Then `importlib.invalidate_caches()` and the distribution's
  `any_mcp.plugins` entry points are read; none is an error, several need `plugin` (D2).
- No `python_path` or `sys.path` insertion for sources.

Alternatives: `sys.path` + `module:Class` on the checkout (rejected: no declared dependencies, module
shadowing, namespace merging; sources brief D2-D4); `uv pip` (rejected: uv is not in agent pods); a
separate venv per plugin (rejected: non-goal).

### D4: `any-mcp plugins install` and install-on-miss at startup (my call)

New subcommand `any-mcp plugins install [--config PATH] [SOURCE ...]` installs each given source, or
every `plugins[].source` of the config, as an explicit install (refreshes branch and tag refs). It reads
only the `source` strings (expanding `${VAR}` in those strings alone), so a config whose plugin
`config` names variables unset in the install environment still installs (my call: the onStart hook
does not carry the agent's runtime env). Errors exit 78 with one line. At server startup
(`load_plugins`, all three paths), a source entry missing from the manifest is installed first, then
loaded. Alternative: install only at startup (rejected: a slow first install would hit the MCP client's
startup timeout instead of failing the onStart hook visibly).

### D5: any-mcp becomes generic, released as v0.5.0 (my call)

`src/any_mcp/orchestrator.py` and `tests/test_orchestrator_plugin.py` are deleted with no shim; a
retirement test pins their absence through `git ls-files` and that src, examples and docs carry no
`/agent/v1`. `tests/test_nomenclature.py` is deleted: it guards exactly those files, and the guard
moves with them to the plugins repo. README's "Orchestrator plugin" section is replaced by a "Plugin
sources" section pointing at any-mcp-tatara-plugins. Release v0.5.0 (breaking, user's design call) with
CHANGELOG, README pins and the version-pinned tests updated as no longer accurate; MEMORY records the
reversal of the 2026-10-24 decision.

### D6: any-mcp-tatara-plugins layout and tooling (my call)

`<topic>/<plugin>/` each a package: `pyproject.toml` (hatchling, `[project.entry-points."any_mcp.plugins"]`),
`src/<module>/`, `tests/`. First plugin `orchestration/orchestrator/`: distribution
`any-mcp-tatara-orchestrator`, module `any_mcp_tatara_orchestrator`, entry point `orchestrator` (my
call). Plugin packages declare `any-mcp` unversioned as a dependency (my call, precedent
`examples/petstore/pyproject.toml`): the host any-mcp satisfies it, and an unversioned requirement lets
the orchestrator dev environment hold the plugin beside any-mcp v0.4.0 before the pin moves. Repo root:
a uv workspace over `*/*` members with a dev group (pytest, pytest-asyncio, ruff, any-mcp pinned to
`v0.5.0` by `[tool.uv.sources]`), mise `python = "3.12"`, tasks `install`, `test`, `lint`, `fmt` in
any-mcp's form, CI workflow like any-mcp's (no secrets). Repo-level tests pin the tooling, the layout
(every `<topic>/<plugin>` is a package with an entry point and tests), the nomenclature guard, and an
end-to-end install of each plugin through `any-mcp plugins install`. README documents the topic layout,
adding a plugin and the source notation. Releases are `vX.Y.Z` tags on main (first `v0.1.0`), no
release workflow (my call: nothing is published beyond the tag).

### D7: The orchestrator renders its reserved entry as a source at a pinned plugins tag (my call)

New settings `any_mcp_plugins_repo` (`ORCH_ANY_MCP_PLUGINS_REPO`, default
`https://github.com/szymonrychu/any-mcp-tatara-plugins`) and `any_mcp_plugins_ref`
(`ORCH_ANY_MCP_PLUGINS_REF`, default `v0.1.0`, release tag only like `ORCH_ANY_MCP_REF`). The reserved
entry keeps name, namespace, allow and config, and replaces `plugin` with
`source: git::<repo>//orchestration/orchestrator?ref=<ref>`. The onStart script, after writing the
config, runs `/opt/any-mcp/bin/any-mcp plugins install --config /opt/any-mcp/etc/any-mcp.yaml` before
`--help`. Settings default `any_mcp_ref` `v0.5.0`. The `mcp__any-mcp__orchestrator_*` tool prefix and
`RESERVED_PLUGIN` are namespace-based and unchanged. Alternative: a second pip line for the plugins
package in onStart (rejected: it bypasses the source notation the sessions use, so the reserved plugin
would prove nothing about it).

### D8: Spec field `any_mcp_sources` (my call)

`SessionSpec.any_mcp_sources: list[str] | None = None`, sparse and create-time (name avoids
`spec.wrapper.plugins`). Validation: at most 20 entries of at most 500 characters (my call, the
init_scripts caps' shape), each parsed by `any_mcp.sources.parse_source`; only `git::https://` and
`github.com/` sources (gate Q1); each source renders as the plugin entry `{name, source}` with the name
derived from the last subdir segment, else the repo name without `.git`, lower-cased, characters
outside `[a-z0-9_-]` replaced by `-`, cut to 20 (my call); a name that does not match any-mcp's name
pattern, repeats another derived name, equals `orchestrator`, or equals a plugin name of the effective
any-mcp config (the spec's, else the settings default) is an error naming the index. Rendered after the
base config's entries and before the reserved entry. `any_mcp_config` plugin entries with a `source`
follow the same remote-only rule (gate Q1). No host allowlist (gate Q2): preset authors already run
arbitrary init scripts in agent pods. Alternatives: full plugin entries only through `any_mcp_config` (rejected: the user
asked for one pasteable line per source; full entries stay possible there); a name from the installed
entry point (rejected: unknown until install, so collisions could not be refused at validation).

### D9: Orchestrator tests use the plugins package as a dev dependency (my call)

The dev group gains `any-mcp-tatara-orchestrator @ git+<plugins repo>@<plugins tag>#subdirectory=orchestration/orchestrator`;
every test import of `any_mcp.orchestrator` moves to `any_mcp_tatara_orchestrator`.
`tests/test_images.py` pins the dev dependency tag to `any_mcp_plugins_ref`, as it pins any-mcp's. Alternative: vendoring the plugin into the orchestrator tests (rejected: a
second copy that drifts from the released plugin).

### D10: Web: a mirrored notation check and a "+" row list (my call)

`src/presets/pluginSource.ts` mirrors D1 for the sources the orchestrator accepts (D8) with the same
messages; `PresetForm.tsx` gets an "any-mcp plugins" section: a "+" icon button (precedent
`src/chat/ScaleControl.tsx`, `@mui/icons-material/Add`) adds a one-line text box, each row removable,
an inline error per row, stored as `spec.any_mcp_sources` only when non-empty. Alternative: server-only validation (rejected: the user
asked for a pasteable line per source; an inline error per row is the form's existing pattern for
init scripts).

### D11: Deploy and smoke (my call)

agents-helmfile pins the new orchestrator and web charts and images, `ORCH_ANY_MCP_REF: v0.5.0` and
`ORCH_ANY_MCP_PLUGINS_REF: v0.1.0`. Smoke proves, in the smoke session's pod, that the
`any-mcp-tatara-orchestrator` distribution is installed, the rendered config's orchestrator entry names
the plugins repo at the pinned ref, and `any-mcp --list-tools` lists `orchestrator_sessions_list`; and
that a session created with `any_mcp_sources: ["git::https://github.com/szymonrychu/any-mcp//examples/petstore?ref=v0.5.0"]`
lists `petstore_` tools (petstore is a packaged plugin that loads with an empty config). Live steps run
by the orchestrator (Rollout). Alternative: a dedicated smoke plugin in the plugins repo (rejected: not asked;
petstore is already a released packaged plugin).

### D12: Release order (my call)

any-mcp v0.5.0, then the plugins repo `v0.1.0` (its dev group needs any-mcp v0.5.0), then the
orchestrator pins, then web, then helmfile. Each pin bump is its own task after the producing repo's
merge and tag (Rollout). Alternative: plugins repo first, pinned to any-mcp v0.4.0 (rejected: its
end-to-end install test needs `any-mcp plugins install`, which ships in v0.5.0).

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| any-mcp map | ran (docs/research/2026-10-27-anymcp-generic-anymcp-map.md) | `PluginEntry` touch point (config.py:63), entry-point group (discovery.py:21), exit 78 (cli.py:22), test blast radius (test_nomenclature, test_release, test_package, test_docs_links), version bump list | making `error_result`/`redact` public (Unknowns; the moved plugin keeps importing `any_mcp.errors`, which any-mcp keeps) |
| consumers map | ran (docs/research/2026-10-27-anymcp-generic-consumers-map.md) | onStart is the only pip site (on_start.py:77), spec list precedent `init_scripts` (spec.py:429), row-list UI (PresetForm.tsx:220), pins in settings, pyproject, test_images, helmfile values and smoke | pip `#subdirectory` as the stored form (section 8; the user asked for Terraform notation) |
| sources (Terraform, pip, git, importlib) | ran (docs/research/2026-10-27-anymcp-generic-sources.md) | go-getter grammar subset, fetch-by-SHA with fallback, blob filter and sparse checkout, `--` before user values, timeouts, subdir escape check, install as a distribution for entry points and deps (D5) | `sys.modules` collision detection (sources fix-as-ac; pip-installed distributions share site-packages and isolation is a non-goal), `git clone --revision` (needs git 2.49), tree sha256 in the manifest, `uv pip --dry-run` preflight (not asked; pip fails on conflicts) |
| reuse hunt | skipped: the two cartographer maps cover reuse | - | - |

## Research inputs

Retro proposals of the most recently done epics, recurring workflow ones first:

- Recurring (paste-env-contents-into-the, matrix-read-receipts): a ruling not pinned by a test is found
  only in review; every ruling in a task's Notes names its pin test. Acts: every task, chiefly
  anymcp-source-parser, anymcp-source-installer, orch-any-mcp-sources-spec, web-plugin-source-parser.
- Recurring (matrix-read-receipts, agents-matrix-connector-depl): live proof and cleanup are
  orchestrator-run steps. Acts: Rollout R5; helmfile-smoke-plugin-tools writes the offline-tested steps.
- Recurring (matrix-read-receipts): list user-action steps up front. Acts: Rollout "User steps" (none).
- Recurring (agents-matrix-connector, agents-matrix-connector-depl): a new repo's CI needs were found
  late. Acts: plugins-repo-bootstrap (CI uses no secrets, user-confirmed), Rollout R2 checks CI green.
- Recurring (agents-schedule-deploy, agents-matrix-connector): seeds off; points vary per task kind.
  Acts: points of every task (installer 5, pins 2, smoke 3).
- Recurring (agents-matrix-connector): per-task reviews missed trust-boundary defects. Acts: Review
  focus on anymcp-source-parser and anymcp-source-installer.
- agents-schedule-deploy: the web nomenclature guard broke a task; web verify needs `npm run build`.
  Acts: web-plugin-source-parser, web-preset-plugin-sources.
- paste-env-contents-into-the: `ticket.py amend` lints the whole epic. Acts: every task's AC format.
- paste-env-contents-into-the: stale orchestrator `.venv`; agents-matrix-connector: Docker disk for
  testcontainers. Acts: Notes of every agents-orchestrator task.
- agents-schedule-deploy: api pods do not restart on a Secret change. The new settings ride the
  ConfigMap and the image tag changes in the same apply. Acts: Rollout R4.

Findings:

- `tests/test_nomenclature.py` asserts `git ls-files` of exactly the orchestrator plugin files and
  fails once they go. Acts: anymcp-remove-orchestrator, plugins-orchestration-plugin.
- `PluginEntry.plugin` is required and `extra="forbid"` (config.py:63). Acts:
  anymcp-source-plugin-loading.
- The docs tests require every top-level config key and CLI flag documented (test_docs_reference.py:51,
  :57) and say `ANY_MCP_CONFIG` is the only variable read. Acts: anymcp-source-plugin-loading.
- The orchestrator imports `any_mcp.config.AnyMcpConfig` at runtime for spec validation (spec.py:641).
  Acts: orch-any-mcp-0-5-0-pin, orch-any-mcp-sources-spec.
- Four orchestrator test modules import `any_mcp.orchestrator` (test_on_start.py:9,
  test_agent_scale.py:8, test_agent_init_scripts.py:103, test_agent_session_messaging.py). Acts:
  orch-plugins-dev-dependency.
- `test_images.py:106` pins pyproject any-mcp tag to the settings default. Acts: orch-any-mcp-0-5-0-pin.
- onStart writes the config then runs only `--help` (on_start.py:77). Acts: orch-render-plugin-sources.
- The agent image is python:3.12-slim with git (claude-code-wrapper Dockerfile:18,31). Acts:
  orch-render-plugin-sources (no image change).
- The plugins scaffold pins Python 3.14.6 and has no pyproject or CI. Acts: plugins-repo-bootstrap.
- `examples/petstore` is a packaged plugin with an entry point that loads with an empty config. Acts:
  helmfile-smoke-plugin-tools.

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 source notation | anymcp-source-parser, web-plugin-source-parser |
| D2 plugin entries take source | anymcp-source-plugin-loading |
| D3 installation | anymcp-source-installer |
| D4 install subcommand and install on miss | anymcp-source-plugin-loading |
| D5 generic any-mcp v0.5.0 | anymcp-remove-orchestrator, anymcp-release-0-5-0 |
| D6 plugins repo layout | plugins-repo-bootstrap, plugins-orchestration-plugin |
| D7 reserved entry as a source | orch-any-mcp-0-5-0-pin, orch-render-plugin-sources |
| D8 any_mcp_sources | orch-any-mcp-sources-spec, orch-render-plugin-sources |
| D9 plugins package dev dependency | orch-plugins-dev-dependency, orch-any-mcp-0-5-0-pin |
| D10 web form | web-plugin-source-parser, web-preset-plugin-sources |
| D11 deploy and smoke | helmfile-smoke-plugin-tools, helmfile-deploy-pin |
| D12 release order | anymcp-release-0-5-0, plugins-orchestration-plugin, orch-plugins-dev-dependency, helmfile-deploy-pin |

## Review focus

- anymcp-source-parser and anymcp-source-installer: every git argument after `--`, refs starting with
  `-` refused, subdir `..` and symlink escape refused, timeouts on every subprocess, no shell. These are
  the trust boundary: an orchestrator preset author's string reaches git and pip in an agent pod that
  holds the agent token.
- anymcp-source-installer: the cache rules (SHA forever, branch and tag refreshed only on explicit
  install) and that a manifest hit really means installed in this environment.
- anymcp-source-plugin-loading: `plugins install --config` must not expand `${VAR}` outside `source`.
- plugins-orchestration-plugin: the plugin and its tests are the v0.4.0 code with only import paths
  changed (ac pins the test diff).
- orch-render-plugin-sources: the reserved entry is rendered for exactly the sessions it was before;
  the onStart install line runs after the config is written.
- web-plugin-source-parser: the same accept and reject cases as the Python parser for the forms D8
  allows.

## Left to the builder

- Internal names in `any_mcp.sources` and `any_mcp.install` beyond the interfaces in the tasks; the
  manifest's JSON layout beyond the recorded fields; git and pip timeout values (module constants).
- How the argparse subcommand coexists with the existing flags, as long as every existing invocation
  keeps working.
- uv workspace and pytest discovery details in the plugins repo (for example `--import-mode=importlib`
  for same-named test modules), within D6.
- UI wording within D10 and the nomenclature guards.

## Rollout

Release and deploy steps run by the orchestrator between and after tasks:

- R1: after anymcp-source-parser through anymcp-release-0-5-0 merge to any-mcp main (PR, CI green),
  push tag `v0.5.0` on that commit; the release workflow must pass. Then plugins-orchestration-plugin
  is dispatched.
- R2: after plugins-repo-bootstrap and plugins-orchestration-plugin merge to any-mcp-tatara-plugins main
  (PR, CI green), push tag `v0.1.0` on that commit. Then orch-plugins-dev-dependency is dispatched.
- R3: after the agents-orchestrator PR merges, main CI publishes image `<sha7>` and chart
  `0.1.0-main.<sha7>`; after the agents-web PR merges, its image and chart publish. The shas reach
  helmfile-deploy-pin through `ticket.py amend` before it is dispatched.
- R4: after the agents-helmfile PR merges: `mise run diff`, then `mise run apply`. The settings
  ConfigMap and image tag change together, so api, dispatcher, ingester and reconciler pods roll; every
  agent StatefulSet's onStart text changes, so its pods roll once (run when no turn is in flight).
- R5: `mise run smoke` (includes the plugin source steps of helmfile-smoke-plugin-tools).
- R6: update the submodule pointers in the workbench for any-mcp, any-mcp-tatara-plugins,
  agents-orchestrator, agents-web and agents-helmfile.

User steps, asked up front at the gate: none (the plugins repo exists and its CI needs no secrets).

## Assumptions and unknown facts

- Agent pods reach github.com over https (probe of the previous epic's builder check: HTTP 200).
- `pip` in the `/opt/any-mcp` venv installs a hatchling package from a local directory without network
  beyond the build backend download from PyPI; pods already download from PyPI when installing any-mcp.
- The onStart hook's environment lacks the agent's `ORCH_AGENT_*` variables: not verified, so D4 makes
  install independent of them.
- `pytest` `testpaths` globbing and uv workspace members over `*/*` work with the pinned uv; confirmed
  by plugins-repo-bootstrap's own run, never assumed in a later task.

## Open questions
- Q1: Should the orchestrator and the web form accept only remote https git sources (git::https://... and github.com/...) in any_mcp_sources and in any_mcp_config source entries, refusing local paths, git::ssh and git::file (agent pods have no SSH keys and no meaningful local plugin dirs)? Local paths stay fully supported in any-mcp itself. [recommended: yes, remote https git only in the orchestrator and web]
- Q2: Should any_mcp_sources accept any git host and repo, with no allowlist, since preset authors can already run arbitrary init scripts in agent pods? [recommended: yes, no host allowlist]

## Irreversible operations in scope

- any-mcp tag `v0.5.0` push (R1) and any-mcp-tatara-plugins tag `v0.1.0` push (R2): published release
  tags; covered by the gate approval.
- The agents-helmfile apply (R4): rolls every running agent pod once (in-flight turns are interrupted);
  covered by the gate approval and run when no turn is in flight.
