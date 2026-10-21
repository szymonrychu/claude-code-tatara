# Agents this flow dispatches

Read from the Notes of `start-development`. Every agentType `workbench:plan-execute` dispatches has a row.

Dispatched when the trigger fires. Read-only agents never edit, commit, push, apply, or merge; `implementer` and
the research agents write (code in its worktree, a brief at its output path).

| Agent | Dispatch when | Phase |
|---|---|---|
| `submodule-auditor` | a checkout may be stale, detached, or unpushed | 1 |
| `codebase-cartographer` | mapping a repo in scope (via `start-discovery`) | 1 |
| `reuse-hunter` | the reuse hunt (via `research-code-internal`) | 1 |
| `architect-researcher` | more than one viable approach, or expensive to reverse | 2 |
| `research-docs-purist` | official docs of every library in scope (via `research-docs`) | 1 |
| `research-practitioner` | field experience, known failure modes (via `start-research`) | 1 |
| `research-prior-art-scout` | similar open-source projects (via `research-code-external`) | 1 |
| `research-paper-scout` | literature for an algorithmic core (via `research-papers`) | 1 |
| `research-reviewer` | adversarial check of every research brief (via `start-research`) | 1 |
| `planner` | planning an epic: design.md, tasks, approvals, contracts (input `{epic, briefs[], userDecisions[], relatedEpics[]}`) | 3 |
| `implementer` | every task's implementation, via `workbench:plan-execute` and the lean path | 4 |
| `reviewer` | one reviewer for spec and quality (via `start-review --single`) | 5 |
| `spec-reviewer` | full or panel tier work (via `start-review`) | 5 |
| `quality-reviewer` | full or panel tier work (via `start-review`) | 5 |
| `scope-auditor` | after implementation, before sign-off | 4, 5 |
| `worktree-merger` | every worktree merge, sized by `--assess` | 4, 6 |
| `verifier` | every implementer and fixer result, via `workbench:plan-execute` (`haiku`) | 4 |
| `security-researcher` | diff touches secrets, RBAC, exposure, privilege, CI, hooks | 5 |
| `tf-planner` | a terraform module changed | 5 |
| `helmfile-differ` | a chart or release changed | 5 |
| `scm-shepherd` | a pipeline failed and the cause is not in the log tail | 6 |
| `k8s-triage` | a workload looks unhealthy after deploy | 6 |

The merge role in workbench:plan-execute is a prompt role, not an agent file; verify runs as the
verifier agent.

`worktree-merger` writes the merge it lands; `record-writer` (phase 7) writes exactly one file, the
record. None replaces the gate, and every finding is still yours to judge.
