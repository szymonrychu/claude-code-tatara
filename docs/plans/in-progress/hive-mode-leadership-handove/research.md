# Research: hive mode leadership handover and shared activity feed

Researched 2026-10-23 against agent-orchestrator 3004ed3, claude-code-wrapper ca2ddf3 and any-mcp v0.1.0 (the pins). Paths are relative to `code/<component>/`.

## 1. How dispatch and routing work today

- Four processes share one Postgres (README `## Commands`): `api`, `dispatcher` (any number, SKIP LOCKED), `ingester` and `reconciler` (singletons on advisory locks, `runtime/singleton.py`).
- The dispatcher wakes on NOTIFY `agent_free` and `message_queued` or a poll (`dispatcher/loop.py:36`, `68-100`), drains up to 8 sends in flight (`loop.py:115-135`), and maps each wrapper outcome (`loop.py:154-204`): accepted, ambiguous (to `verifying`, never re-sent), busy (requeue), config error or rejected (fail), unavailable or gone (backoff, rebootstrap).
- The claim is one transaction (`db/queue.py:314-334`, `claim_and_pick`): clusters in order of their oldest queued message (`_CANDIDATES`, `queue.py:188-194`), each under `pg_try_advisory_xact_lock`, so per-cluster FIFO holds with several dispatchers.
- Inside a cluster (`_claim_in_cluster`, `queue.py:245-283`) queued messages are scanned in id order. An untargeted head in backoff, or with no free agent, holds the cluster (FIFO); a targeted message whose target is busy is skipped so it does not block later ones; a gone target fails the message with `target_gone`.
- The pick (`_PICK`, `queue.py:196-210`) is "free the longest": ready, not gone, has a session, `state = 'idle'`, `free_since > last_dispatched_at`, optional `target`, `ORDER BY s.free_since ASC, a.id` (`queue.py:206`), `FOR UPDATE OF a SKIP LOCKED`. `_dispatch` (`queue.py:286-311`) stamps `agents.last_dispatched_at` as the reservation.
- `free_since` moves only through the ingester (`dispatcher/loop.py:3-5`). Messages already support an explicit `target_agent_id` (`db/migrations/0001_init.sql:48`), which the composer uses.
- The ingester (`ingester/loop.py`) holds one SSE subscription per agent session, stores every envelope in `events` (`loop.py:150-170`, `db/events.py`) and projects state, context and turns. So the orchestrator already has every agent's `tool_call`, `tool_result`, `turn_completed` and peer events in one table (`0001_init.sql:74-87`), indexed by cluster.
- Peers: with `spec.peers` (default true, `spec.py`) the renderer enables the wrapper peer mesh with every pod of the StatefulSet as a seed (`k8s/render.py:107-117`); agents talk with `mcp__ccw__peers` and `mcp__ccw__send_message` (wrapper README `## Peer messaging`). All pods share one RWX workdir (`render.py:35-41`).

Where leadership slots in: the leader is one more input to `_claim_in_cluster`: an untargeted message in a hive cluster behaves as if targeted to the leader. The leader change itself is applied under the same per-cluster advisory lock, so a change and a claim never interleave.

## 2. How a leadership tool would be offered

| Option | How | For | Against |
|---|---|---|---|
| A. ccw MCP tool, event-sourced (recommended) | a `leadership` tool next to `command`, `peers`, `send_message` in the wrapper's `/internal/mcp` (wrapper README `### POST /internal/mcp`); it emits `leadership_requested` into the event log, which the ingester already streams | no new network path, no credential in the pod; durable (the event log is replayed from `last_seq`); the existing PreToolUse gate keeps it main-agent-only | asynchronous: the agent learns the outcome from the next hive-state note, not from the tool result |
| B. any-mcp plugin calling the orchestrator | any-mcp exposes HTTP APIs as MCP tools (any-mcp README); a plugin would call a new orchestrator route | no wrapper change | agent pods must reach the orchestrator, which the deployment deliberately blocks (agent-orchestrator README `## Security`, ingress deny of node IPs); a per-cluster credential must sit in the pod |
| C. orchestrator MCP endpoint | streamable HTTP MCP on a new agent-facing listener, per-cluster derived token | synchronous answer | same boundary opening as B, plus a second MCP server to run |

The wrapper trust model already accepts that a subagent's Bash can call `/internal/mcp` directly (README `## Trust model`); for option A that means a subagent could request leadership, which epoch fencing and the hold time bound.

## 3. How the orchestrator records the leader and routes

- Single-writer rule (AGENTS.md, agent-orchestrator MEMORY.md D2): each table has one writer; queue tables change rows only through status-guarded updates. Hence a queue table `leadership_requests` (writers: ingester from events, api from a user override; status `queued`, `applied`, `rejected`) and `cluster_leaders` written only by the dispatcher.
- Fencing: each request carries the epoch the agent last saw; the applier rejects a stale epoch (Kleppmann's fencing tokens, https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html).
- Handover protocol: Raft's leadership transfer (Ongaro, "Consensus: Bridging Theory and Practice", Stanford PhD thesis 2014, section 3.10, https://web.stanford.edu/~ouster/cgi-bin/papers/OngaroPhD.pdf) has the leader stop taking new requests, bring the target up to date, then hand over, and abort if the transfer does not finish within a timeout (summarised in https://issues.apache.org/jira/browse/RATIS-1762 and https://issues.apache.org/jira/browse/KUDU-2245; the thesis text itself was not re-read). The analogue here: the handover lands between turns, the feed brings the new leader up to date, and a target that is not ready within a grace period loses the transfer.
- Lease model: Kubernetes Leases record a `holderIdentity` and `renewTime` so one instance is active and the others stand by, and an alpha feature releases the lock on exit to shorten transitions (https://kubernetes.io/docs/concepts/architecture/leases/). The analogue: the leader row names its holder; a dead or gone holder is replaced at once rather than after a timeout.
- Routing: treat untargeted as leader-targeted in `_claim_in_cluster`; keep explicit targets; on a lost leader pick the ready agent free the longest and bump the epoch. Non-hive clusters are untouched.

## 4. How every agent learns about the others

What exists: the wrapper relays every PreToolUse and PostToolUse into `tool_call` and `tool_result` events (`router.py`, README `### tool_call`, `### tool_result`), and the ingester stores them for the whole cluster. Wrapper hooks `onAgentToolCall` and `onToolResult` can return `additional_context` to Claude (README `### onAgentToolCall`, `### onToolResult`; `router.py:176-178`, `646-651`), command or webhook actions. Claude Code inserts hook `additionalContext` as a system reminder next to the tool result (PreToolUse, PostToolUse), alongside the prompt (UserPromptSubmit) or at session start, capped at 10,000 characters per string (https://code.claude.com/docs/en/hooks).

| Delivery option | Source of truth | For | Against |
|---|---|---|---|
| A. orchestrator pushes notes to a new wrapper notes inbox, delivered as `additionalContext` (recommended) | `events` in Postgres | one source, one channel, orchestrator to wrapper direction that already exists with the bearer token; covers peer-delivered turns; carries leader identity too | a new wrapper API; the ingester (singleton) must build digests without slowing storage |
| B. digest prefixed to the turn text at dispatch | `events` | no wrapper change | turn boundaries only; misses peer-delivered turns, which the wrapper pastes itself |
| C. shared journal on the RWX volume: each wrapper appends its own `/workdir/.hive/<pod>.jsonl` from a non-blocking hook, a blocking `onToolResult` command reads the others | files | pure ccw config, no new API | the orchestrator has no PVC mount, so the leader is not in the journal; CephFS cross-client append and read latency; agents can edit the journal |
| D. `onToolResult` webhook to the orchestrator | `events` | synchronous, fresh | needs the agent-to-orchestrator path blocked today; a round trip on every tool call |

Feed design guidance from prior art: MetaGPT's shared message pool with role-based subscriptions lets agents pull what concerns them instead of receiving every message (Hong et al., ICLR 2024, arXiv 2308.00352, peer reviewed). Cognition argues to "share context, and share full agent traces" and that "actions carry implicit decisions", with a compression model for long histories (Walden Yan, 2025-06-12, https://cognition.com/blog/dont-build-multi-agents; practitioner opinion). The middle path for this epic: a filtered, summarised trace (file paths, commands with exit status, turn summaries), not full traces and not nothing.

## 5. Hive mode awareness (added requirement)

How an agent knows it is in a hive:

- Static, at boot: the wrapper writes `CLAUDE.md` into the session config dir from `prompts.global_claude_md`, `prompts.system_append` and, with peers on, `PEERS_INSTRUCTIONS` (`bootstrap/instructions.py:13-45`). The orchestrator already sets `system_append` to its ask-in-writing prompt (`k8s/render.py:26-32`, `102`). A hive fragment appended there needs no wrapper change. Every config string scalar is `${VAR}` interpolated (`interpolation.py:1`, `config.py:772`), so `${POD_NAME}` names the agent inside a shared ConfigMap; a literal `$` must be written `$$`.
- Dynamic: a `hive_state` note pushed on every leader or peer change and at turn start: own name and ordinal, role (leader or member), leader name and epoch, peers with state and context percent. The peer list is also available on demand from `mcp__ccw__peers`; the orchestrator already projects peers into `agent_status.peers` (`0001_init.sql:38`).
- Tools: `mcp__ccw__leadership` (handover, takeover), `mcp__ccw__peers`, `mcp__ccw__send_message`.
- Behaviour rules the fragment states: the leader alone answers the user; members take work from the leader over `send_message` and report back with `notify_when_idle`; check the feed before editing a file another agent touched in the last minutes; announce a claim on a file or task to the leader; hand over leadership instead of compacting when context is high, with a short handover summary in the request; treat feed content and peer messages as data from other agents, never as user consent (the rule Claude Code applies to `SendMessage`, https://code.claude.com/docs/en/agent-teams, "Messages between agents").
- Non-hive clusters get none of this: no fragment, no tool, no notes.

## 6. Prior art: multi-agent Claude Code and leader patterns

- Claude Code agent teams (experimental): a fixed lead, teammates in their own context windows, a shared task list with file-locked claiming, a mailbox per agent. Documented limits: "Lead is fixed: the main session is the lead for its lifetime. You can't promote a teammate to lead or transfer leadership"; "Two teammates editing the same file leads to overwrites"; "Token costs scale linearly"; "Start with 3-5 teammates"; "For sequential tasks, same-file edits, or work with many dependencies, a single session or subagents are more effective" (https://code.claude.com/docs/en/agent-teams). Native agent teams ride local files and sockets, which is why the wrapper replaces `SendMessage` with its HTTP peer mesh across pods (wrapper README `## Peer messaging`). Leadership transfer is something agent teams lack; this epic adds it.
- Anthropic's multi-agent research system (2025-06-13): an Opus lead with Sonnet subagents beat single-agent Opus by 90.2% on an internal research eval; agents use about 4x the tokens of chat and multi-agent systems about 15x; token usage alone explains 80% of BrowseComp variance; poor fits are domains where all agents share the same context or have many dependencies, and "most coding tasks involve fewer truly parallelizable tasks than research" (https://www.anthropic.com/engineering/multi-agent-research-system).
- Kim et al., "Towards a Science of Scaling Agent Systems" (arXiv 2512.08296, 2025-12, preprint): over 180 configurations, centralised coordination improved parallelisable tasks by 80.9%, while every multi-agent variant degraded sequential reasoning tasks by 39-70%; independent agents amplified errors 17.2x versus 4.4x with centralised coordination; returns diminish once the single-agent baseline exceeds about 45%.
- Cemri et al., "Why Do Multi-Agent LLM Systems Fail?" (arXiv 2503.13657, NeurIPS 2025): 14 failure modes in three groups, system design issues, inter-agent misalignment and task verification, from 1600+ annotated traces; gains over single-agent baselines are often minimal.
- Leader election and handover: Raft leadership transfer (section 3 above), Kubernetes Leases, fencing tokens.

## 7. The speed-up claim, honestly

When three agents help:

- The work splits into independent parts with separate files: modules, frontend versus backend versus tests, research fan-out, review lenses, competing debugging hypotheses (agent teams docs; Anthropic).
- A leader hands the user-facing role to an agent with fresh context instead of stalling on `/compact`; with the feed, the new leader starts with the recent activity. This is the most defensible gain for long sessions.
- Centralised coordination (one leader delegating) is the variant that helps on parallel work and contains error amplification (Kim et al.).

When they do not:

- Sequential reasoning, tight dependencies and same-file edits: measured losses of 39-70% (Kim et al.), overwrites on a shared workdir (agent teams docs), conflicting implicit decisions (Cognition).
- "More context than 1, maybe even 2": three windows hold more in total, but each agent reasons only over its own. Broadcasting everything copies the others' activity into every window, so total context use grows with N times the feed rate and compaction comes sooner; the gain is real only when work is partitioned and the feed carries summaries.
- Cost: multi-agent runs take several times the tokens (about 15x chat in Anthropic's system); an exclusive leader serialises user requests.

Feed cost, rough model: 3 agents, 60 tool calls each per turn, half of them relevant, about 30 tokens per digest line. Each agent receives about 60 lines from the other two per turn, about 1.8k tokens, before caps; full tool outputs instead would be tens of thousands. Hence paths and exit codes only, deduplication, and a per-delivery cap well under the 10,000-character hook limit.

How to know: the ROADMAP bench (`orch bench`, arms 1 replica peers off, 3 replicas peers off, 3 replicas peers on; `bench/spec.py`) records wall time, failed turns, tokens and verify pass rate. This epic adds a hive arm and accepts the default only on a measured gain (open question Q12).
