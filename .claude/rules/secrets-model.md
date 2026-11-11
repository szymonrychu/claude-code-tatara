---
paths:
  - "code/agents-*/**"
  - "code/claude-code-wrapper/**"
  - "code/any-mcp*/**"
  - ".worktrees/**/agents-*/**"
  - ".worktrees/**/claude-code-wrapper/**"
  - ".worktrees/**/any-mcp*/**"
---

# Secrets model

## The model in brief (who sees what)
- Protected value: exists only in the user's browser input, the vault web request body (SecretStr), an immutable Kubernetes Secret `vault-<entry>-v<n>`, and the env of the claude child in a session pod pinned to it. Nobody else: not Postgres, not events, not logs, not error bodies, not views, not tool output, not transcripts.
- Readable value: stored in the vault database, shown in vault views and to the orchestrator; it is configuration, not a secret. Anything that must stay secret is protected; never store a secret as readable "for convenience".
- Users (SSO) manage entries on the vault web listener. The orchestrator (service token) resolves, pins and releases. Agents never talk to the vault; they see entry names, ids, env names and pin metadata through orchestrator tools, and the values only as env of their own pod.
- Scope: `project:` labels on an entry restrict where it may be attached; the vault alone evaluates the match from the labels the orchestrator derives from the session's project scope (home plus user-approved extra projects). A session gets exactly the versions pinned at its create.
- Trust boundary: anything that can read Secrets in the agents namespace (cluster-admin sessions, privileged sidecars, node root, cluster operators) is outside the model; rotation is the response after such access.

## Invariants to preserve
1. Write-only Kubernetes: no code, test fake or Role grants get/list/watch on secrets; Secrets are written and deleted by deterministic name only.
2. A value is a SecretStr from parse to Secret write; it becomes plain text only inside the function that builds stringData.
3. No value, hash, length or prefix of a protected value in Postgres, events, metrics, logs, error messages, exception chains, HTTP bodies, OpenAPI examples, fixtures or test names.
4. Error texts are fixed strings plus env names, entry ids and versions. Never echo a caller-chosen key or an upstream API body; Kubernetes error bodies are dropped, only the exception type name is logged.
5. Pins are immutable per session: a retry returns the first pins; rotate never moves a running session; readable values are not versioned.
6. Render only what the spec references: a pin renders when the spec entry is a vault ref, and Secret names and keys are validated against the vault's grammar before they reach a pod spec.
7. Labels: each secret has one owning project (its `project:` label). A session may use secrets of any project in its scope (home project plus extra projects); the orchestrator sends one `project:` label per project of that scope and the vault matches an entry whose `project:` label is in the session's scope; an entry with a `project:` label outside the scope never matches, and an entry with no labels matches any scope. Every widening of a scope (an extra project on a preset or a running session) is granted only by a user-approved proposal; user or agent supplied labels never carry the `project:` prefix.
8. Redaction in the wrapper must not depend on the env name: every env the orchestrator marks as secret is redacted by value in events, tails, hook output and transcript-derived records, kept out of shell terminals and out of children that run repository code.
9. Tokens between services: raw tokens live in Kubernetes Secrets applied from SOPS files; a service holds the sha256 of tokens it verifies and the raw token only of the upstream it calls; a token that opens service X is never also accepted by X's own listener; constant-time compare; never logged, never in a URL.
10. Superleader = agent with admin reach. Every admin route and tool it gets must assume prompt injection: names and ids only, no values, scoped to the caller's project, audited.

## What to look after when changing code
- New route or tool: list its statuses in the OpenAPI ROUTE_ERRORS, add it to the canary test (a known marker value must appear nowhere in responses, logs, rows or events), decide which listener it belongs to (web = humans, service = orchestrator, agent = pods) and which identity it records as actor.
- New field on an entry, pin, event or view: ask "could this hold or derive a value?"; readable yes, protected never.
- New env name grammar or passthrough: update the orchestrator render golden, the wrapper secret-env list and the vault validation together; a mismatch leaks by name.
- New process that handles a value (CLI, migration, backup, export, archive): give it the same canary coverage; exports and archives exclude transcripts' unredacted material only if the wrapper redacts first.
- Logging: log type names, ids, env names, counts. Never log request bodies, upstream bodies, env dumps or settings reprs; Settings fields holding tokens use repr=False and SecretStr.
- Tests and fixtures: use obviously fake markers (CANARY-...), assert they do not appear in logs (caplog), rows (scan every table, base64 too) or responses; never copy a real token into a test, a README example or an OpenAPI example.
- RBAC and charts: Secret verbs stay create/patch/delete; name restrictions belong in an admission policy; mount a ServiceAccount token only into the container that calls the API; external Secrets for tokens, never values.yaml literals; semver image pins.
- Migrations: forward-only, never read a value; refuse to run on data they would misinterpret.
- Transcripts and history: treat every tool result as potentially containing a secret the model echoed; redaction happens in the wrapper before storage; history is searchable by superleaders, so what reaches it must already be clean.
- Rotation and GC: a retired version is deleted only when no live pin references it; release is by reconciliation (pull), fail-safe late rather than early; after a leak rotate and restart the pinned sessions.
- Privileged sessions (cluster access, docker, exec tiers): document and gate what they can read; prefer project-scoped entries for them; never attach broad credentials to presets that trigger services (webhooks, schedules) can start.
- Prompt-injection posture: any text an agent reads (webhooks, chats, repos, tool output) may instruct it to exfiltrate; the controls are value-level redaction, scoped tools, no values in tool answers, and audit of every admin call.

## Things to avoid
- Deriving "is secret" from a variable name pattern alone.
- Returning upstream error bodies, pydantic input values or dict keys in 422 messages.
- Reading a Secret "just to compare" or "to copy untouched values" during rotate.
- A single service token shared by two services, or a token both sent and accepted by the same service.
- Storing readable values in a second place without the same retention awareness (backups).
- Logging settings objects, request bodies, env maps or Kubernetes objects.
- Adding a tool for agents that returns readable values of entries outside the caller's project.
- Widening the vault web allowlist or trusting Forwarded headers for the allowlist decision.
