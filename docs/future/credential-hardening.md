# credential-hardening: plan (spec)

Status: future work, not started. Deferred 2026-11-02 by the user (mx-99 #905, chat m182): plan
for the Recommended options, implement nothing until the user says so.

Approved for planning: mx-99 #888. Sources read on origin/main: claude-code-wrapper 8be5d63 (v0.8.1),
agents-orchestrator 2ff61fa (latest tag v3.5.0), retro `docs/plans/claude-usage-monitor/retro.md`
(finding 3, rec 3; the file has since moved out of docs/plans), `.scratchpad/wrapper-mise-token/*.md`.
Claude Code pinned at 2.1.304 (wrapper `Dockerfile` `CLAUDE_CODE_VERSION`); the same binary is
installed in this pod.

## What and why

Wrapper 0.8.1 cleaned the mise, setup, git and plugin children. Three holes remain:
(a) Claude Code's own Bash, hooks and stdio MCP children inherit the claude env, so they get
`CLAUDE_CODE_OAUTH_TOKEN`, `CCW_HOOK_TOKEN` and `ORCH_AGENT_TOKEN`;
(b) wrapper `command` hook actions get the full service env minus `CCW_USAGE_TOKEN` only
(`hooks.py:225`, base env from `manager.py:1443` and `hooks.py:438`), so preset hooks
(`agents-orchestrator spec.py:487`) see `CCW_AUTH_TOKEN`, `CCW_PEER_TOKEN` and the OAuth token;
(c) everything runs as uid 1000 (`render.py:591`, `Dockerfile` USER agent), so any agent process
reads `/proc/<wrapper pid>/environ` (all secrets) and the wrapper's state files.

## Research findings (cited)

1. The setting exists. Exact name `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB`, value `1`.
   https://code.claude.com/docs/en/env-vars ("Set to 1 to strip credentials from the environments
   of the subprocesses Claude Code starts, such as Bash commands, hooks, and stdio MCP servers").
   Added v2.1.83 (https://github.com/anthropics/claude-code/releases/tag/v2.1.83), PID namespace
   added v2.1.98 (.../releases/tag/v2.1.98). The wrapper already models it as
   `claude.env.claude_code_subprocess_env_scrub` (`claude_env.py:1594`).
2. What it strips (env-vars#what-the-subprocess-environment-scrub-removes): any name or value that
   looks like a credential; keeps `GITHUB_TOKEN`, `GH_TOKEN`, proxies, `GIT_CONFIG_*`; REMOVES
   `CLAUDE_CONFIG_DIR`. Not configurable. Binary 2.1.304: explicit list includes
   `CLAUDE_CODE_OAUTH_TOKEN`; the name regex matches `(^|_)(TOKEN|SECRET|KEY|AUTH|PAT|...)`, so
   `CCW_HOOK_TOKEN` and `ORCH_AGENT_TOKEN` are stripped too.
3. On Linux Bash runs in its own PID namespace: no `/proc` reads of host processes, and `ps`,
   `pgrep`, `kill` cannot see them (same docs section).
4. Undocumented side effects, confirmed in the 2.1.304 binary: (i) "Permission mode forced to
   default ... Declare allowedTools explicitly" (bypassPermissions and auto are ignored);
   (ii) "bubblewrap is required for subprocess env scrubbing" (the image has no bwrap);
   (iii) write-protected paths `.claude/commands`, `.claude/agents`, `.git/info` pinned at launch.
5. Probe in this agent pod: user and PID namespaces work, a mount namespace fails ("cannot change
   root filesystem propagation: Permission denied", AppArmor `cri-containerd.apparmor.d` enforce).
   bwrap needs a mount namespace, so the scrub will not start under the default profile.
6. Hooks: "A hook process inherits the parent environment, apart from the OTEL_* exporter
   variables ... and, when CLAUDE_CODE_SUBPROCESS_ENV_SCRUB is set to 1, the variables it strips"
   (https://code.claude.com/docs/en/hooks). statusLine: gets JSON on stdin, `COLUMNS`, `LINES`
   (https://code.claude.com/docs/en/statusline); whether the scrub applies to it is undocumented.
7. Related: `CLAUDE_CODE_MCP_ALLOWLIST_ENV=1` starts stdio MCP servers with a baseline env plus
   their configured `env` (env-vars). `CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR` exists in the binary
   but is not on the env-vars page (undocumented).
8. Claude Code docs offer no way to run Bash as another user; they recommend a container or the
   sandbox (https://code.claude.com/docs/en/sandboxing). Kubernetes gives a non-root container no
   ambient capabilities, so a uid 1000 wrapper cannot setuid its children.

## Threat model

Attacker: prompt-injected agent code (Bash, hooks, MCP, repo mise tasks) running as the claude uid.
Assets: OAuth token (account), `CCW_AUTH_TOKEN` (drive the wrapper: turns, terminals, files),
`CCW_PEER_TOKEN` (other pods), `CCW_USAGE_TOKEN` (forge usage), preset hook secrets.
Out of scope: tokens deliberately given to the agent (`ORCH_AGENT_TOKEN`, `GH_TOKEN`, spec env),
a hostile operator, kernel escapes. Goal: no wrapper secret and no OAuth token readable from env,
`/proc` or files by any claude-spawned process.

## Decisions (user, 2026-11-02)

Every question was resolved to its Recommended option A. Rejected alternatives are one line each.

1. Scrub rollout: A. On for every agent pod, with all adaptations, after the spike passes. If the
   spike fails, stop and ask the user. Rejected: B per-preset opt-in default off (MVP only);
   C skip the scrub and pass OAuth via the undocumented `CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR`.
2. bwrap mount namespace: A. `appArmorProfile: Unconfined` on the ccw container only when the
   scrub is on. Rejected: B a custom node AppArmor profile (infra change).
3. Permissions under the scrub: A. Render `permissions.allow` for all built-in tools and `mcp__*`,
   same effect as today. Rejected: B a narrow allow list per preset.
4. Hook token scope: A. Per run, bound to its session, expiry = action timeout, revoked on exit.
   Rejected: B per run, expiry only, full API.
5. Hook env: A. Allow-list: base vars, passthrough, action env, managed `CCW_*`, `CCW_API_TOKEN`.
   Rejected: B full env minus a deny-list.
6. Privilege model for (c): A. Wrapper uid 0 with SETUID, SETGID, KILL, CHOWN, FOWNER,
   DAC_OVERRIDE only, children as 1000. Rejected: B non-root wrapper uid plus a setuid launcher
   (needs privilege escalation); C same uid, wrapper non-dumpable only (MVP only).
7. Hook command uid: A. Agent uid 1000 like claude. Rejected: B a dedicated uid 1001.
8. Releases: A. Wrapper and orchestrator take the next free version, decided at build time and
   reserved at merge (numbers in "Release numbers" are as of plan time).

## Design

(a) Scrub, on for every agent pod (decision 1). Orchestrator renders
`claude.env.claude_code_subprocess_env_scrub: true`. Adaptations it forces: image installs
`bubblewrap`; ccw container gets `appArmorProfile: Unconfined` (finding 5, decision 2); render
puts an explicit `permissions.allow` covering built-in tools and `mcp__*` (finding 4i, decision 3);
`ccw-hook` and `ccw statusline` read the relay token from a 0600 file whose absolute path is in
the settings.json command line (env name stripped, `CLAUDE_CONFIG_DIR` stripped); any-mcp gets
`ORCH_AGENT_TOKEN` through the MCP server's configured `env` (spike confirms it survives).
A spike runs first: real claude 2.1.304 in an agent pod with the scrub on, checking relay, statusLine,
any-mcp, permission prompts, protected paths, docker, and that `cat /proc/*/environ` finds nothing.
Rollout to all pods happens only after the spike passes; if it fails, stop and ask the user.

(b) Hook token (decisions 4 and 5). `HookDispatcher._command` builds an allow-listed env:
`BASE_ENV` + `claude.passthrough_env` (via `allowed_env`) + action `env` + the managed `CCW_*`
vars, then `without_secrets` on the inherited part. New `CCW_API_TOKEN`: random per action run,
held in an in-memory store with scope (its session, or the instance for instance events), expiry =
action `timeout_seconds` + 5 s, revoked when the process exits. `require_auth` accepts it only on
its own session's routes. `CCW_AUTH_TOKEN`, `CCW_PEER_TOKEN`, Claude credentials never reach a hook.

(c) Separate uid (decisions 6 and 7). Wrapper runs as uid 0 with caps dropped to SETUID, SETGID,
KILL, CHOWN, FOWNER, DAC_OVERRIDE, `allowPrivilegeEscalation: false`, and
`prctl(PR_SET_DUMPABLE, 0)`. New config `claude.child_user: {uid, gid}` (orchestrator sets
1000:1000): claude (`pty_proc.py` Popen `user/group/extra_groups`), terminals, git, setup, mise,
plugin installs and hook commands all run as 1000. Wrapper-private state (event logs, turns, meta,
hook-state, peers state) is chowned root 0700/0600 on start; claude-owned dirs (config dir,
workdir, HOME, /opt/mise, /opt/any-mcp) stay 1000. The file API does its I/O with
`openat2(RESOLVE_NO_SYMLINKS|RESOLVE_BENEATH)` or in a uid-1000 helper, so a planted symlink
cannot turn root reads or writes outside the workdir. Refuse to start when `child_user` is set and
the process cannot setuid (no fallback).

## Files and components touched

- claude-code-wrapper: `hooks.py` (env allow-list, token mint), new `hook_tokens.py`,
  `api/auth.py`, `manager.py` (`_dispatcher`, spawns, chown), `pty_proc.py`, `terminals.py`,
  `tooling.py`, `files.py`, `session.py` (`build_env`), `bootstrap/settings.py`, `hook_relay.py`,
  `statusline.py`, `config.py` (`child_user`), `service.py` (dumpable, privilege check),
  `Dockerfile` (bubblewrap, USER root, agent user kept), `README.md` (trust model, hook env,
  per-process env map from retro rec 3), `MEMORY.md`, tests.
- agents-orchestrator: `k8s/render.py` (scrub flag, `permissions.allow`, `child_user`, container
  `securityContext` and `appArmorProfile`), `k8s/on_start.py` (assert no secret use),
  `e2e/agent-test.Dockerfile` (base image), `tests/test_render*.py`, `MEMORY.md`.
- agents-helmfile: wrapper and orchestrator pins, `tests/test_orchestrator_release.py`
  (`WRAPPER_PIN`), `mise run smoke` credential-probe step, `MEMORY.md`.
- any-mcp: none, unless the spike shows configured MCP `env` is also stripped (then a token-file
  option).

## Test approach

- Wrapper unit (TDD): hook env holds no `CCW_AUTH_TOKEN`, `CCW_PEER_TOKEN`, OAuth value or name,
  holds `CCW_API_TOKEN`; token valid during the run, 401 after exit or expiry, 403 on another
  session; relay and statusLine read the token file; `child_user` spawns run as 1000.
- Wrapper container integration (`mise run test:integration`, image as root with the caps):
  a fake-claude Bash step dumps `env`, `/proc/1/environ`, `/proc/$PPID/environ`, every
  `/proc/*/environ`, the hook-state dir; assert no sentinel secret by name or value; claude uid 1000.
- Orchestrator render tests: scrub flag, allow list, securityContext, appArmorProfile, child_user.
- Live e2e (agents-helmfile smoke, real claude): a session whose prompt runs
  `env; cat /proc/[0-9]*/environ; ls -la /sessions` into a file; the harness counts occurrences of
  the real OAuth, auth, peer and usage token values (counts only, never printed): all zero; a hook,
  statusLine relay, any-mcp tool call, `gh auth status` and `docker ps` still work.

## Risks

- Scrub strips `CCW_HOOK_TOKEN`: hook relay and turn completion break unless moved to a file.
- Scrub forces permission mode default: a missing allow rule stalls the PTY on a prompt.
- bwrap needs a mount namespace: AppArmor must be relaxed for the ccw container (security trade).
- Plugins' mise env: a `mise.toml` env template that reads a token (`GITLAB_TOKEN`) gets nothing
  in Bash; `/opt/mise` must stay uid 1000 when the wrapper is root.
- Git credentials: `GH_TOKEN` survives the scrub; `GITLAB_TOKEN` (glab) and other spec tokens do
  not reach Bash. Session `gitconfig` must be readable by 1000.
- any-mcp: `ORCH_AGENT_TOKEN` stripped from its env unless configured `env` survives (spike).
- statusLine relay: scrub coverage undocumented; the file token covers both cases. The usage token
  stays in the root wrapper only, now unreadable.
- Docker sidecar: socket group access for uid 1000; bwrap must bind the socket path.
- `ps`/`kill` cannot see processes of other Bash calls; `.claude/agents` edits may be refused.
- Existing PVC files owned by 1000: one-time chown of wrapper-private paths at start.
- Claude version bumps can change the scrub list (it changed at v2.1.251): pin test on the version.

## Scope

Single scope, the complete one (all decisions A): (a) scrub on for every agent pod after the
spike (bwrap, AppArmor, allow list, any-mcp env); (b) hook allow-list env and scoped
`CCW_API_TOKEN`; (c) root wrapper with children as 1000, non-dumpable, private state chowned, file
API symlink hardening; live credential e2e in smoke; README per-process env map; MEMORY.
Rejected smaller scope: the MVP cut (scrub as a per-preset opt-in default off, wrapper
non-dumpable only) is not chosen.

## Release numbers

Next free at build time (decision 8); reserve at merge (retro rec 6), take next free on collision.
At plan time: claude-code-wrapper v0.9.0 (latest tag v0.8.1, no open PR); agents-orchestrator
v3.8.0 (latest tag v3.5.0; v3.6.0 and v3.7.0 pending, open PRs #57 and #36); agents-helmfile: pin
PR, no tag.
