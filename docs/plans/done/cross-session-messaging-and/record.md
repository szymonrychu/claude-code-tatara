# Cross-session messaging and Kubernetes access session options record

## Asked

Two opt-in per-session options on agents-orchestrator sessions: superleader cross-session messaging (a superleader's leader lists and messages the leaders of all open sessions; every other leader lists and messages only superleaders) and cluster-admin in-cluster Kubernetes access, gated by a chart value. Spans agents-orchestrator, any-mcp, agents-web, agents-helmfile. Goals G1-G5, including deploy and preset updates ("facebook chat" messaging on, "claude-code-tatara" Kubernetes access on).

## Shipped

All four repos merged; epic review verdict: pass (2026-10-26).
- any-mcp fa03c36..9f506b2, PR https://github.com/szymonrychu/any-mcp/pull/4, tag v0.4.0 (sessions_list, session_send).
- agents-orchestrator 915207c..de16c14, PR https://github.com/szymonrychu/agents-orchestrator/pull/22.
- agents-web 9302d1d..de64208, PR https://github.com/szymonrychu/agents-web/pull/15.
- agents-helmfile d6fa24a..a68e876, PRs https://github.com/szymonrychu/agents-helmfile/pull/30 and /pull/31.
- Deploy: agents-helmfile 86ee171 applied (orchestrator de16c14, web de64208, wrapper 0.3.0 pin from the previous epic applied for the first time); rollouts OK; ClusterRoleBinding agents-orchestrator-kube-access -> cluster-admin. Smoke (third run) passed incl. kube access and superleader messaging. Presets: facebook chat session_messaging true, claude-code-tatara kube_access true.
- Full suites at review: orchestrator 1027 passed (non-integration), agents-web 429, any-mcp 215, agents-helmfile 208; lint clean.

## Tasks

16 of 16 done (14 planned + 2 discovered; agent-serviceaccounts-do-not was a review-finding task, counted among the 16 as a third added task: planned 13, added 3). All verified heads appear in the repo git logs. Review rounds and verification tails are not in the orchestrator notes except where stated; the suite totals are in Shipped.

| Task | Status | Verified head | Review rounds | Verification tail |
|---|---|---|---|---|
| anymcp-session-tools (any-mcp) | done | 99a57d0 | none recorded | unknown (any-mcp suite 215 passed at epic review) |
| orch-session-message-sender | done | dc9d165 | none recorded | unknown |
| web-chat-session-messages | done | feab561 | none recorded | unknown (agents-web 429 passed at epic review) |
| orch-session-options-spec | done | 8a8a560 | none recorded | unknown |
| chart-kube-access-rbac | done | 9382104 | 1 fix round (nomenclature word in a comment) | unknown |
| orch-agent-service-accounts | done | bbb9c1c | none recorded | unknown |
| orch-agent-session-messaging | done | dbff3bc | none recorded | unknown |
| orch-any-mcp-pin-0-4-0 | done | 566d8e9 | none recorded | unknown |
| web-preset-session-options | done | decf266 | none recorded | unknown |
| orch-kube-access-render | done | ecff370 | none recorded | unknown |
| orch-render-session-tools | done | 87c7833 | none recorded | unknown |
| allow-the-init-scripts-tools (discovered) | done | 6da5e87 | 1 fix round (e2e assertions, from PR CI; fix f92cc8d) | unknown |
| agent-serviceaccounts-do-not (review finding) | done | 876e70f | none recorded | unknown |
| smoke-session-options (agents-helmfile) | done | 24024b4 | none recorded | unknown |
| helmfile-deploy-pin | done | f81208d | none recorded | unknown (agents-helmfile 208 passed at epic review) |
| smoke-waits-for-agent-readin (discovered) | done | d1c09ff | none recorded | unknown |

Orchestrator suite 1027 passed after the e2e fix; PR #22 CI green after f92cc8d. Notes and files agree on status and heads; no empty verified_head.

## Rulings

- Messaging model changed at the gate to one-sided superleader (option needed on one end only; tools rendered for every session; target_not_superleader refusal). Why: user decision. Cost if wrong: rework of agent routes, tool rendering and tests across orchestrator and any-mcp.
- Q1: no kubectl install by the orchestrator (kubectl comes from a user hook or the agent). Why: user decision. Cost if wrong: sessions with kube_access have no kubectl until the preset hook provides it (R7 depends on this).
- Q2: trigger sessions get cluster-admin when kube_access is on. Why: user decision. Cost if wrong: over-broad privilege; mitigated by opt-in per session and chart value gate.
- Interrogate panel (fable/opus/sonnet) before the gate changed the plan: pair budget (cross-turn ping-pong), docs honesty (cluster-admin equivalence of namespace workload/Secret creation), template rename (kube-access-binding.yaml, nomenclature guard). Why: panel findings. Cost if wrong: unbounded ping-pong, misleading README, failing guard.
- Security MEDIUM (agent ServiceAccounts inheriting api annotations) fixed as task agent-serviceaccounts-do-not. Cost if ignored: cloud identity leaking to agent pods, breaking G3.
- Security LOW dismissed: 404 vs 403 slug probing (slugs are not secret). Cost if wrong: slug enumeration, low impact.
- Security LOW dismissed: advisory limit overshoot under concurrent sends (documented D10). Cost if wrong: brief overshoot of message limits.
- mx-4 discarded (idle, 0 queued) when enabling messaging on facebook chat. Cost if wrong: loss of that session's queued input; none queued.
- Smoke second-run failure attributed to the orchestrator's own stray port-forward, not a product defect; third run passed. Cost if wrong: an intermittent smoke failure goes unfixed.
- Both discovered gaps (init-scripts tools missing from allow list; smoke make-leader race) placed as new tasks rather than dropped.

## Discovered and blocked

- Discovered: allow-the-init-scripts-tools (agents told to use a tool no allow list included) - fixed.
- Discovered: smoke-waits-for-agent-readin (pre-existing make-leader race) - fixed (agents-helmfile #31).
- Blocked: R7 live kubectl proof in a claude-code-tatara session, pending the user's preset edit U1 (kubectl source/kubeconfig removal in the preset). Cleared by the user. Access itself already proven by the smoke (SelfSubjectAccessReview */* allowed).

## Not pushed

Submodules (any-mcp, agents-orchestrator, agents-web, agents-helmfile): main equals origin/main, nothing unpushed. Superrepo claude-code-tatara: main is 189 commits ahead of origin/main (includes the epic's ticket commits and the submodule pointer bump 2230232, plus earlier local work). Pushed by the user (or the next explicit push request).

## Lessons routed to

- Nomenclature word slipping into a comment (chart-kube-access-rbac round): mechanical; the existing tests/test_nomenclature.py caught it only after commit. Add a pre-commit hook running the nomenclature test on staged files in agents-orchestrator.
- Kind e2e assertions stale after an allow-list change (caught only in PR CI): mechanical; add a test in tests/test_on_start.py deriving the expected allow list from the constants (the e2e assertions should import them), so unit tests fail first.
- Agent told to use a tool no allow list included: mechanical; test_allowed_tools_exist_in_plugin (added in allow-the-init-scripts-tools) covers it; extend to scan init Job text for tool names.
- Smoke race (make-leader before agent ready): mechanical; fixed by readiness wait and retry in the smoke script; no further check.
- Orchestrator notes lacked per-task review rounds and verification tails: judgement call; edit the epic-run skill to have the orchestrator write rounds and the verifier's summary line into each task Notes section.
