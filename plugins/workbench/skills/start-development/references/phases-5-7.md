# Phases 5-7: verify, merge, record

Detail for phases 5-7 of `SKILL.md`.

## Phase 5 - Verify

The epic review: the whole change, after every task is delivered, before the epic can be done.
1. **Enter review.** `ticket.py stage <epic> review` (refuses while a task is open or unverified).
2. **Whole-diff review.** `start-review --single` on the integrated diff; `workbench:interrogate` for
   `panel` tier tasks, a contested design, or authz, secrets, concurrency, rules engines, migrations.
3. **Scope.** One `workbench:plan-execute` run with `auditOnly: true`, `args.epic`, `args.epicReadme`
   (its Goals and Non-goals define done) and `ticket.py tasks <epic>` as `args.tasks`. It is the
   epic's one audit (`args.audit` is `'off'` on epic runs); each gap is a new task in the epic.
   No epic: a run's own audit covers scope; after `finished: false`, dispatch `scope-auditor`.
4. **The one full-suite run.** The repo's `suites` from `.claude/workbench.json` (the merger already
   runs them after each merge), else `"${CLAUDE_PLUGIN_ROOT}/skills/worktree-merge/scripts/suite-lock.sh"
   -- mise run test`; `mise run lint`, `pre-commit run --all-files` where set; quote the output.
5. **Security and infra.** Secrets, SOPS, RBAC, ingress, privilege, `hostPath`/`hostNetwork`, CI
   vars, image pins, hooks or permissions: `security-researcher`. Terraform or chart changes: when the
   `workbench-infra` pack is enabled, `tf-planner` / `helmfile-differ`; an unlisted destroy stops the run.
6. **Gaps go back.** Place every `processGaps` entry; drop wrong findings, recorded. Real ones: new
   tasks, `ticket.py stage <epic> build` (`stage build` is always allowed), phase 4, then step 1.
7. **Verdict.** `ticket.py review <epic> --verdict pass --notes-file <notes>` when all is clean, else
   `--verdict fail` and step 6; the last `Verdict:` line counts. Then `epic-move` (`ticket.py move <epic> done`):
   it needs the pass, every task done, verified and merged into `--base`, and removes only merged,
   clean worktrees, listing any it left; `epic-worktrees-remove` (`ticket.py reap --epic <epic>`) removes every remaining worktree of the epic.

Meta mode with no `origin` remote ends here: edits handed to the user to commit, then the phase 7
record. With an `origin` remote it continues into phase 6 and lands like a component.

## Phase 6 - Merge

Per epic: `epic-move` to done closes it (Phase 5, step 7), `epic-worktrees-remove` sweeps leftover
merged worktrees, and the record is at `ticket.py path <epic> record`.

1. **Wrap.** Component mode only. Every task worktree must already be merged and cleaned up by a
   `worktree-merger` agent; one still standing never landed - resolve that first. Then
   `git-worktrees-commit` (per-repo semantic titles you compose), `git-worktrees-push`, and the
   `pullrequests-update` (cross-linked "Complementary MRs/PRs"). `pullrequests-update` and
   `pullrequests-watch` pick the host per repo from `remote get-url origin`, never assumed, per
   `references/merge-hosts.md`.
2. **Watch, acting per MR/PR as each resolves.** `pullrequests-watch` streams
   `RESOLVED <repo> <status> <detail>` as each reaches a terminal state; act on each line as it
   arrives, per `references/merge-hosts.md`, never on all of them at once.
3. **Merge each MR/PR the moment it is ready**: green + mergeable + zero unresolved reviews. This
   session owns its own MRs; anything opened by other automation is never agent-merged. **After each
   merge, re-check every still-open MR** and rebase and push the ones it unblocked.
4. **Watch the deploy.** `pullrequests-watch` with `--deploy` (GitHub and GitLab) against the merged set, acting per
   repo as each resolves. A failed deploy is recorded and fixed, not silently retried.
   A repo with a `deploy` config and no k8s deploy: `python3 ${CLAUDE_PLUGIN_ROOT}/skills/start-development/scripts/deploy-hook.py`
   (deploy, then verify). A step only the user may run follows `references/user-run-steps.md`.
5. **Post-deploy health.** Run `grafana-debugging-start` against the affected services (and
   `k8s-triage` for pod-level symptoms) when the `workbench-observability` pack is enabled, else the
   repo's `deploy.verify` command from `.claude/workbench.json`. A green pipeline is not a healthy
   service. A failed health check continues in `start-debugging`.

## Phase 7 - Record

After a pass verdict `epic-move` to done closes the epic and `epic-worktrees-remove` clears
leftover worktrees. Dispatch `record-writer` (sonnet) with the epic dir (README, design.md, tasks/,
approvals.json), every `workbench:plan-execute` return value, `git log` per repo, the MR/PR URLs and
deploy outcome, and your rulings (every escalation, dropped finding and process gap, with what you
decided). It fills `templates/record.md` at `ticket.py path <epic> record` (legacy dated files:
`doc_path.sh record "<topic>"`) and writes nothing else. Then send the user ONE closing message,
three lines at most (rules/concise-orchestrator.md): the record path, the MR/PR URLs that need their
eyes, and anything blocked, each named with who can clear it.
