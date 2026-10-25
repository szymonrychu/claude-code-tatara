# MEMORY

Dated entries, newest last. Supersede an entry rather than deleting it. One line per non-obvious decision.

2026-10-22: project initialised; components: claude-code-wrapper; adoption method: adopt --url (fresh clone).
2026-10-22: template update 3145b85bafed.
2026-10-23: components now: claude-code-wrapper, any-mcp; via component add (new scaffold).
2026-10-23: components now: claude-code-wrapper, any-mcp, agent-orchestrator; via component add (new scaffold).
2026-10-23: components now: claude-code-wrapper, any-mcp, agent-orchestrator, agents-helmfile; via component add (new scaffold).
2026-10-23: template update 22ec5df62575.
2026-10-23: cloud sessions: ported the template's scripts/cloud_session_start.py SessionStart hook and docs/claude-cloud.md runbook (template PR szymonrychu/workbench#1) ahead of the next template update, so the workbench plugins load and submodule pushes work in Claude Code cloud sessions; the next template update merges identical content.
2026-10-23: standing approval (user): open gate questions the user does not answer are taken at their recommended answer; the epics proceed on that basis without a further ask.
2026-10-23: cloud test infra: the orchestrator DB tests need Docker (testcontainers); in a cloud session start `dockerd` in the background first, it works there.
2026-10-23: standing approval (user): run hive-mode-leadership-handove and web-ui-cluster-tabs-with-fil to completion and push to main (pushing main deploys nothing); never deploy - finish with copy-paste deploy commands for the user to run.
2026-10-24: overnight agent history for web-ui-cluster-tabs-with-fil and cluster-presets was squashed and force-pushed under the user's name (user's request); SHAs in those records are pre-squash. Now: claude-code-wrapper 1ced775 is now e9ffa62, agent-orchestrator 9ab0d60 is now be90ac8 (plus review fixes), agents-helmfile 8bf0b6b is now 13e5ffa.
2026-10-25: standing approval (user): agents may run `mise run apply` in code/agents-helmfile (live agents namespace) for the epics' apply-smoke tasks; supersedes the 2026-10-23 never-deploy rule for that command.
2026-10-25: never put `mise run apply` (or any live deploy) in a task's AC evidence: the plan-execute verifier runs `command:` evidence verbatim, and on cluster-scaling it re-applied an old pin from an unbuilt task tree (helm rev 12 rollback). Use `mise run diff` or a judgement AC; the orchestrator runs the apply.
2026-10-25: gate approved (user: "Go") for agents-web-component, frontend-decoupling, configuration-improvements, agents-webhook-component, agents-webhook-microservice, agents-schedule-component, agents-schedule-microservice; every open gate question taken at its recommended answer, including the four public GitHub repos (agents-web, agents-common, agents-webhook, agents-schedule) and the unauthenticated, signature-checked webhook ingest.
2026-10-25: components now: claude-code-wrapper, any-mcp, agent-orchestrator, agents-helmfile; via init:refresh.
2026-10-25: components now: claude-code-wrapper, any-mcp, agent-orchestrator, agents-helmfile, agents-web; via component add (new scaffold).
