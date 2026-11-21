# Harness context baseline (2026-11-21)

This measures the always-loaded context of the Claude Code harness in this workbench: root CLAUDE.md and AGENTS.md, rules without `paths:` frontmatter, skill and agent description frontmatter, and the superpowers SessionStart bootstrap (full text of using-superpowers/SKILL.md). Tokens are ceil(chars / 4), an approximation. The using-superpowers skill appears twice by design (its description, and the full text injected by the session-start bootstrap). The `/skill-doctor` context numbers include name and overhead, so they differ from the description-only counts here. It is the S-74 pre-change baseline, to be rerun by the future `cc-harness-usage-recheck`.

Command:

    python3 scripts/harness_footprint.py --date 2026-11-21

| Source | Kind | Chars | Tokens |
|---|---|---|---|
| AGENTS.md | instructions | 21122 | 5281 |
| superpowers:using-superpowers | session-start | 3180 | 795 |
| CLAUDE.md | instructions | 613 | 154 |
| plugins/workbench/skills/research-docs/SKILL.md | skill-description | 558 | 140 |
| plugins/workbench/agents/security-researcher.md | agent-description | 515 | 129 |
| plugins/workbench/skills/init/SKILL.md | skill-description | 448 | 112 |
| plugins/workbench/skills/pill/SKILL.md | skill-description | 445 | 112 |
| plugins/workbench/agents/architect-researcher.md | agent-description | 436 | 109 |
| plugins/workbench/agents/submodule-auditor.md | agent-description | 417 | 105 |
| plugins/workbench/skills/research-papers/SKILL.md | skill-description | 408 | 102 |
| plugins/workbench/agents/codebase-cartographer.md | agent-description | 404 | 101 |
| plugins/workbench/skills/template-update/SKILL.md | skill-description | 403 | 101 |
| plugins/workbench/skills/release/SKILL.md | skill-description | 389 | 98 |
| plugins/workbench/skills/research-code-internal/SKILL.md | skill-description | 392 | 98 |
| superpowers:diagnosing-superpowers | skill-description | 375 | 94 |
| plugins/workbench/agents/scm-shepherd.md | agent-description | 363 | 91 |
| plugins/workbench/skills/research-code-external/SKILL.md | skill-description | 359 | 90 |
| plugins/workbench/skills/pullrequests-watch/SKILL.md | skill-description | 317 | 80 |
| plugins/workbench-infra/agents/helmfile-differ.md | agent-description | 313 | 79 |
| plugins/workbench/agents/reuse-hunter.md | agent-description | 312 | 78 |
| plugins/workbench/skills/handoff/SKILL.md | skill-description | 288 | 72 |
| plugins/workbench-observability/agents/k8s-triage.md | agent-description | 280 | 70 |
| plugins/workbench-infra/agents/tf-planner.md | agent-description | 270 | 68 |
| plugins/workbench/skills/component-add/SKILL.md | skill-description | 252 | 63 |
| plugins/workbench/skills/pullrequests-review-loop/SKILL.md | skill-description | 252 | 63 |
| plugins/workbench/agents/research-docs-purist.md | agent-description | 233 | 59 |
| superpowers:receiving-code-review | skill-description | 234 | 59 |
| plugins/workbench-observability/skills/grafana-debugging-start/SKILL.md | skill-description | 225 | 57 |
| superpowers:verification-before-completion | skill-description | 225 | 57 |
| plugins/workbench/agents/research-practitioner.md | agent-description | 221 | 56 |
| plugins/workbench-observability/skills/kubectl-logs-query/SKILL.md | skill-description | 219 | 55 |
| plugins/workbench/agents/research-paper-scout.md | agent-description | 218 | 55 |
| plugins/workbench/skills/component-remove/SKILL.md | skill-description | 213 | 54 |
| superpowers:brainstorming | skill-description | 213 | 54 |
| plugins/workbench/agents/research-prior-art-scout.md | agent-description | 206 | 52 |
| plugins/workbench-secrets/skills/secrets-env/SKILL.md | skill-description | 204 | 51 |
| plugins/workbench/agents/research-reviewer.md | agent-description | 199 | 50 |
| superpowers:using-git-worktrees | skill-description | 196 | 49 |
| plugins/workbench/skills/pullrequests-update/SKILL.md | skill-description | 191 | 48 |
| plugins/workbench/skills/pullrequests-list/SKILL.md | skill-description | 178 | 45 |
| plugins/workbench/skills/git-worktrees-commit/SKILL.md | skill-description | 175 | 44 |
| plugins/workbench/skills/start-research/SKILL.md | skill-description | 176 | 44 |
| superpowers:executing-plans | skill-description | 170 | 43 |
| plugins/workbench/skills/git-worktrees-create/SKILL.md | skill-description | 161 | 41 |
| superpowers:using-superpowers | skill-description | 154 | 39 |
| plugins/workbench/skills/git-submodules-refresh/SKILL.md | skill-description | 145 | 37 |
| plugins/workbench-secrets/skills/sops-secret-helper/SKILL.md | skill-description | 141 | 36 |
| plugins/workbench/skills/git-submodules-add/SKILL.md | skill-description | 134 | 34 |
| plugins/workbench/skills/git-worktrees-push/SKILL.md | skill-description | 136 | 34 |
| superpowers:dispatching-parallel-agents | skill-description | 106 | 27 |
| superpowers:requesting-code-review | skill-description | 107 | 27 |
| superpowers:finishing-a-development-branch | skill-description | 101 | 26 |
| superpowers:writing-skills | skill-description | 97 | 25 |
| superpowers:systematic-debugging | skill-description | 91 | 23 |
| superpowers:subagent-driven-development | skill-description | 85 | 22 |
| superpowers:writing-plans | skill-description | 84 | 21 |
| superpowers:test-driven-development | skill-description | 79 | 20 |
| **Total** | | 38428 | 9629 |

## Subtotals per kind

| Kind | Sources | Chars | Tokens |
|---|---|---|---|
| instructions | 2 | 21735 | 5435 |
| skill-description | 40 | 9126 | 2297 |
| agent-description | 14 | 4387 | 1102 |
| session-start | 1 | 3180 | 795 |

## CLI reports

`claude -p "/usage"` in a fresh non-interactive session reports only an empty session (0 tokens, $0.0000), so it carries no baseline information.

`claude -p "/skill-doctor"` output (no account identifiers present):

    Skills loaded this session

      skill                                            source                   context  7d tokens   uses  last used
      superpowers:brainstorming                        superpowers                  ~80          -     0x  never
      superpowers:diagnosing-superpowers               superpowers                 ~140          -     0x  never
      superpowers:dispatching-parallel-agents          superpowers                  ~50          -     0x  never
      superpowers:executing-plans                      superpowers                  ~70          -     0x  never
      superpowers:finishing-a-development-branch       superpowers                  ~50          -     0x  never
      superpowers:receiving-code-review                superpowers                  ~90          -     0x  never
      superpowers:requesting-code-review               superpowers                  ~50          -     0x  never
      superpowers:systematic-debugging                 superpowers                  ~40          -     0x  never
      superpowers:test-driven-development              superpowers                  ~40          -     0x  never
      superpowers:using-git-worktrees                  superpowers                  ~80          -     0x  never
      superpowers:using-superpowers                    superpowers                  ~60          -     0x  never
      superpowers:verification-before-completion       superpowers                  ~90          -     0x  never
      superpowers:writing-skills                       superpowers                  ~40          -     0x  never
      workbench:component-add                          workbench                    ~90          -     0x  never
      workbench:component-remove                       workbench                    ~80          -     0x  never
      workbench:git-submodules-add                     workbench                    ~60          -     0x  never
      workbench:git-submodules-refresh                 workbench                    ~60          -     0x  never
      workbench:git-worktrees-commit                   workbench                    ~70          -     0x  never
      workbench:git-worktrees-create                   workbench                    ~70          -     0x  never
      workbench:git-worktrees-push                     workbench                    ~60          -     0x  never
      workbench:handoff                                workbench                   ~100          -     0x  never
      workbench:init                                   workbench                   ~160          -     0x  never
      workbench:pill                                   workbench                   ~150          -     0x  never
      workbench:pullrequests-list                      workbench                    ~70          -     0x  never
      workbench:pullrequests-review-loop               workbench                   ~100          -     0x  never
      workbench:pullrequests-update                    workbench                    ~80          -     0x  never
      workbench:pullrequests-watch                     workbench                   ~120          -     0x  never
      workbench:release                                workbench                   ~140          -     0x  never
      workbench:research-code-external                 workbench                   ~130          -     0x  never
      workbench:research-code-internal                 workbench                   ~140          -     0x  never
      workbench:research-docs                          workbench                   ~200          -     0x  never
      workbench:research-papers                        workbench                   ~150          -     0x  never
      workbench:start-research                         workbench                    ~70          -     0x  never
      workbench:template-update                        workbench                   ~140          -     0x  never
      workbench-observability:grafana-debugging-start  workbench-observability      ~90          -     0x  never
      workbench-observability:kubectl-logs-query       workbench-observability      ~90          -     0x  never
      workbench-secrets:secrets-env                    workbench-secrets            ~80          -     0x  never
      workbench-secrets:sops-secret-helper             workbench-secrets            ~60          -     0x  never
      superpowers:subagent-driven-development          superpowers                  ~40       1.5m     1x  today
      superpowers:writing-plans                        superpowers                  ~40     943.6k     1x  today

      context = this skill's one-line listing in the system prompt, included every turn
      (dash = not in the current listing, costs nothing; full SKILL.md loads only when it runs)
      7d tokens = tokens attributed to the skill over the last 7 days of sessions on this machine

    25 plugin skills loaded but never invoked, from workbench, workbench-observability, workbench-secrets. Each one adds to the system prompt every turn. Plugin skills can't be turned off individually - disable those plugins in /plugin.
