Superseded by research-mindmaps (2026-11-12)

# knowledge-notes (LightRAG notes for sessions): future work

Deferred 2026-11-02 by the user (mx-99 #691, chat m157): the user does their own discovery first. Nothing built; no branches or repos exist.

## Research and options (2026-11-01)

### Item 4: LightRAG notes for sessions (single instance, multitenant, preset switch)

Full upstream research with sources: `.scratchpad/tatara-next/lightrag-research.md`
(lightrag-hku 1.5.7, 2026-09-02, and `main`).

#### LightRAG facts that decide the design

- **No multitenancy in one process.** A `lightrag-server` process serves exactly one
  `WORKSPACE`, set at startup. The `LIGHTRAG-WORKSPACE` header is read only by `/health`.
  PRs for per-request workspaces were closed unmerged (#2445, #3397); issue #3631 is still only a
  design. Upstream advice: one single-replica Deployment per workspace, all on one Postgres,
  isolated by a `workspace` column; never two instances on one workspace. Auth is one
  `X-API-Key` or a single-admin JWT, with no per-workspace permissions. "Single instance,
  multitenant" is therefore not possible with the official server today.
- **Storage fits our stack.** The all-Postgres setup is PGKV + PGVector + PGTableGraph (new in
  1.5.6, no Apache AGE) + PGDocStatus. It needs only pgvector, which the CNPG standard images
  include. LightRAG runs `CREATE EXTENSION vector` at start, so the extension must exist or the
  role must be allowed to create it. Check that our `ghcr.io/cloudnative-pg/postgresql:16`
  variant ships pgvector.
- **It needs an LLM we do not have.** Inserting text always runs LLM entity/relation extraction.
  Local, global, hybrid and mix queries call an LLM for keywords, and answers need one too.
  The docs ask for a 30B-class model with 32k+ context. The server has no Anthropic binding.
  Using the Claude subscription OAuth token for a third-party app is against Anthropic's terms,
  and no agent has an API key. That leaves three ways in:
  - an OpenAI-compatible key (OpenAI, OpenRouter, Gemini, Bedrock);
  - a 30B local model, which means a GPU node;
  - agent-side extraction. Over HTTP this is `/graph/entity|relation/create`, which call no LLM
    but store no text chunks. `insert_custom_kg` with chunks exists only in the Python library.
    Retrieval without an LLM works through `naive` mode (embeddings only), or through
    `only_need_context` or `/query/data` with caller-supplied `hl_keywords`/`ll_keywords`.
- **An embedding model is needed in every LightRAG option.** It can run locally: TEI or Ollama,
  for example bge-m3.
- **There is no official MCP server.** The community ones are immature and cannot switch
  workspace. Our own any-mcp plugin is the way in either way.

#### What exists here

- Preset switch precedent: `spec.kube_access: bool | None` (`spec.py:657`). It is sparse, and
  the setting gates it (`k8s/render.py:60-62`). `/meta` reports whether it is available
  (`api/sessions.py:226`), so the web form shows the toggle only when it is.
- The system prompt hook for "encourage agents": the rendered wrapper config
  `prompts.system_append` (`k8s/render.py:256`).
- Agent auth already exists. Pods carry `ORCH_AGENT_TOKEN` and `ORCH_SESSION_ID`
  (`render.py:32,324`), and the orchestrator plugin calls `/agent/v1` with them. A gateway route
  on the agent API can therefore pin the tenant server-side, so agents cannot spoof it. Relay
  precedent: `api/admin_relay.py` and `api/forward.py`.
- Name clash: the wrapper config already has `notes` (hive notes, `render.py:261`). The feature
  needs another name, such as `knowledge` or `kb`.
- Microservice skeleton: agents-schedule or agents-usage, plus agents-common (settings, pool,
  migrator, ServiceTokenGate), plus the helmfile CNPG `-db` release pattern.

#### Smallest design (options)

- **A: `agents-knowledge` service without LightRAG (MVP).** A new Python service with its own
  CNPG database, the sole writer of a `notes(tenant, id, title, body, tags, created_by_session,
  created_at, updated_at, tsv, embedding?)` table. One process serves every tenant through a
  tenant column. Search is Postgres full-text plus pg_trgm. Adding pgvector with an in-cluster
  TEI embedding model (CPU, bge-small or bge-m3) gives semantic search. No LLM is needed;
  Claude summarises and links at write time.
- **B: LightRAG library inside `agents-knowledge`.** One process keeps a LightRAG instance per
  workspace (tenant), all on one Postgres. Writes go through `insert_custom_kg` with the
  entities, relations and chunks the agent extracts. Reads use `naive` mode, or context-only
  with agent-supplied keywords. This keeps the LightRAG graph format, so full LightRAG can be
  switched on later with an LLM key. Risks:
  - It relies on library internals and a path upstream does not support for multi-workspace.
  - LightRAG may still call the LLM for description merges.
  - An embedding model is required.
- **C: Official `lightrag-server`.** One Deployment per enabled tenant: helmfile per tenant, or
  the orchestrator reconciler creating one per preset. It needs an LLM key (OpenAI-compatible,
  or a GPU-hosted 30B model) plus embeddings. It is not single-instance, and isolation comes
  only from per-tenant API keys.

The following are common to all three:
- Preset switch `spec.knowledge: bool | None`, available only while `ORCH_KNOWLEDGE_URL` is set.
- When the switch is on, the orchestrator does two things:
  - It adds encouragement text to `system_append`: record decisions, findings and gotchas, and
    search before starting.
  - It exposes `/agent/v1/knowledge/*` gateway routes that pin `tenant = <preset name>` (or the
    session slug for sessions without a preset).
- The tatara plugin loads tools `orchestrator_knowledge_put|search|get|delete` only when the
  switch is on.
- The web preset form gets the switch. A Knowledge browser page (list, search, delete per
  tenant) is optional.

**Epic `knowledge-notes`:**
- K1: the service, v0.1.0. Repo, CI release, chart, migration `0001_notes.sql`.
- K2: helmfile. The `agents-knowledge-db` CNPG release (pgvector checked), the service release,
  the TEI release if embeddings are on, and the orchestrator env.
- K3: orchestrator. Spec field, gateway, system prompt text, `/meta`, openapi. No migration,
  because the spec is JSONB. Next free minor.
- K4: plugins. Tools. v0.7.0 or the next free version.
- K5: web. Switch, and optionally the page. Next free minor.

Deploy order: K2 DB, then K1, then K3, then K4 with the plugins ref bump, then K5.

#### Questions

1. Engine:
   - (a) a plain pgvector/full-text notes service, no LLM [MVP, Recommended];
   - (b) the LightRAG library in one multitenant service with agent-side extraction;
   - (c) the official LightRAG server per tenant plus an LLM key.
2. LLM key: can you provide an OpenAI-compatible key (OpenAI or OpenRouter)? Only (c) needs
   one, and it unlocks real LightRAG extraction.
   - (a) no key, choose 1a or 1b [MVP, Recommended];
   - (b) yes, then 1c becomes viable.
3. Tenant unit:
   - (a) preset name [MVP, Recommended];
   - (b) session;
   - (c) preset plus an opt-in shared global tenant.
4. Semantic search:
   - (a) full-text plus trigram only [MVP];
   - (b) add pgvector with an in-cluster TEI bge-m3 on CPU [Recommended].
5. Access path:
   - (a) an orchestrator gateway on the agent API that pins the tenant server-side
     [MVP, Recommended];
   - (b) the plugin calls the service directly with a per-tenant token.
6. Human and superleader access:
   - (a) none, agents only [MVP];
   - (b) a web Knowledge page with search and delete, plus superleader admin tools
     [Recommended].
7. Default for existing presets:
   - (a) off, opt-in per preset [MVP, Recommended];
   - (b) on for all.

## Sources

Upstream research with cited sources is in `.scratchpad/tatara-next/lightrag-research.md`, which holds the cited upstream research for this plan.
