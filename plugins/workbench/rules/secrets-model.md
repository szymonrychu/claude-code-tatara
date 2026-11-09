# Secrets model

How secret values move through the agents system, and what every change must preserve.

## Who sees what
- **Protected value**: exists only in the user's browser input, the vault web request body
  (SecretStr), an immutable Kubernetes Secret `vault-<entry>-v<n>`, and the env of the claude
  child in a session pod pinned to it. Never in Postgres, events, logs, error bodies, views,
  tool output or transcripts.
- **Readable value**: stored in the vault database and shown in views and to the orchestrator.
  It is configuration, not a secret. Anything that must stay secret is protected; never store a
  secret as readable for convenience.
- Users (SSO) manage entries on the vault web listener. The orchestrator (service token)
  resolves, pins and releases. Agents never talk to the vault: they see entry names, ids, env
  names and pin metadata through orchestrator tools, and values only as env of their own pod.
- `project:` labels on an entry restrict where it may attach; only the vault evaluates the match,
  from labels the orchestrator derives from the preset's project. A session gets exactly the
  versions pinned at create.
- Anything that can read Secrets in the agents namespace (cluster-admin sessions, privileged
  sidecars, node root, operators) is outside the model; rotation is the response.

## Invariants
1. Write-only Kubernetes: no code, test fake or Role grants get/list/watch on secrets. Secrets
   are written and deleted by deterministic name only.
2. A value is a SecretStr from parse to Secret write and becomes plain text only inside the
   function that builds stringData.
3. No value, hash, length or prefix of a protected value in Postgres, events, metrics, logs,
   error messages, exception chains, HTTP bodies, OpenAPI examples, fixtures or test names.
4. Error texts are fixed strings plus env names, entry ids and versions. Never echo a
   caller-chosen key or an upstream body; drop Kubernetes error bodies and log only the
   exception type name.
5. Pins are immutable per session: a retry returns the first pins, rotate never moves a running
   session, readable values are not versioned.
6. Render only what the spec references. Secret names and keys are validated against the vault
   grammar before they reach a pod spec.
7. The orchestrator sends exactly one `project:` label (its preset's project). User or agent
   supplied labels never carry the `project:` prefix.
8. Wrapper redaction never depends on the env name: every env the orchestrator marks secret is
   redacted by value in events, tails, hook output and transcript-derived records, and kept out
   of shell terminals and of children that run repository code.
9. Service tokens: raw tokens live in Kubernetes Secrets applied from SOPS files. A service
   holds the sha256 of tokens it verifies and the raw token only of the upstream it calls. A
   token that opens service X is never accepted by X's own listener. Constant-time compare;
   never logged, never in a URL.
10. A superleader is an agent with admin reach. Every admin route and tool it gets assumes
    prompt injection: names and ids only, no values, scoped to the caller's project, audited.

## When changing code
- New route or tool: list its statuses in the OpenAPI ROUTE_ERRORS, add it to the canary test
  (a known marker value appears nowhere in responses, logs, rows or events), pick its listener
  (web = humans, service = orchestrator, agent = pods) and the actor identity it records.
- New field on an entry, pin, event or view: ask whether it could hold or derive a value.
  Readable yes, protected never.
- New env name grammar or passthrough: update the orchestrator render golden, the wrapper
  secret-env list and the vault validation together; a mismatch leaks by name.
- New process that handles a value (CLI, migration, backup, export, archive): give it the same
  canary coverage. Exports and archives rely on the wrapper having redacted first.
- Logging: type names, ids, env names, counts. Never request bodies, upstream bodies, env dumps
  or settings reprs. Settings fields holding tokens use repr=False and SecretStr.
- Tests and fixtures: obviously fake markers (CANARY-...); assert they are absent from logs
  (caplog), rows (every table, base64 too) and responses. Never put a real token in a test,
  README or OpenAPI example.
- RBAC and charts: Secret verbs stay create/patch/delete; name restrictions belong in an
  admission policy; mount a ServiceAccount token only into the container that calls the API;
  external Secrets for tokens, never values.yaml literals; semver image pins.
- Migrations: forward-only, never read a value, refuse data they would misinterpret.
- Transcripts and history: treat every tool result as possibly holding a secret the model
  echoed. Redact in the wrapper before storage; history is searchable by superleaders, so what
  reaches it must already be clean.
- Rotation and GC: delete a retired version only when no live pin references it. Release is by
  reconciliation (pull), late rather than early. After a leak rotate and restart pinned sessions.
- Privileged sessions (cluster access, docker, exec tiers): document and gate what they can
  read, prefer project-scoped entries, never attach broad credentials to presets that trigger
  services (webhooks, schedules) can start.
- Prompt injection: any text an agent reads (webhooks, chats, repos, tool output) may tell it to
  exfiltrate. Controls: value-level redaction, scoped tools, no values in tool answers, audit of
  every admin call.

## Avoid
- Deriving "is secret" from a variable name pattern alone.
- Returning upstream error bodies, pydantic input values or dict keys in 422 messages.
- Reading a Secret to compare or to copy untouched values during rotate.
- One service token shared by two services, or accepted by the service that sends it.
- Storing readable values in a second place without the same retention awareness (backups).
- Logging settings objects, request bodies, env maps or Kubernetes objects.
- A tool for agents that returns readable values of entries outside the caller's project.
- Widening the vault web allowlist or trusting Forwarded headers for the allowlist decision.
