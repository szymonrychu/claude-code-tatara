---
title: create agents-web repo
status: in-progress
repo: superrepo
value: "the UI has its own repo, with its history, ready for its own image and chart"
files: [.gitmodules, code/agents-web, AGENTS.md]
verify: "git config --file .gitmodules --get submodule.agents-web.branch && cd code/agents-web && npm ci --no-audit --no-fund && npx vitest run src/App.test.tsx && npm run lint"
depends_on: []
model: ""
review: full
verified_head: ""
points: 1
expected_minutes: 5
expected_tokens: 750000
points_actual: ""
actual_minutes: ""
actual_tokens: ""
actual_roles: ""
actual_role_tokens: ""
---

# create agents-web repo

## Requirement

Create the component `agents-web` (TypeScript) with `workbench:component-add` and give its main the full history of `agent-orchestrator/frontend` at the repo root. Runs in the superrepo (meta mode). Outward-facing: it creates the public GitHub repo `szymonrychu/agents-web` (approved at the gate by name) and pushes its main.

Precondition, checked first: agent-orchestrator main contains the merges of agent-init-scripts (PR agent-orchestrator#10) and cluster-scaling (`gh pr list -R szymonrychu/agent-orchestrator --state merged --search agent-init-scripts` and the cluster-scaling PR both merged). Otherwise end `blocked`, whoCanClear "orchestrator: land agent-init-scripts and cluster-scaling first".

1. From the workbench root of this worktree: `mise run component:add -- --component agents-web:typescript --remote github --forge-owner szymonrychu --public --confirm-forge --role "agents-web=Web UI of the agents system (React/MUI SPA served as static files by nginx-unprivileged), reaching each backend (agent-orchestrator first) through its documented HTTP API on one host"`. It scaffolds `code/agents-web`, creates and pushes the GitHub origin and adds the submodule (`.gitmodules`, branch main).
2. In `code/agents-web`: `git fetch https://github.com/szymonrychu/agent-orchestrator main`, then `git subtree split --prefix=frontend FETCH_HEAD -b ao-frontend`. Record the fetched agent-orchestrator commit (`git rev-parse FETCH_HEAD`) as `<ao-sha>`.
3. `git rm` the scaffold placeholders `index.js`, `index.test.js`, then `git merge --allow-unrelated-histories ao-frontend` with these resolutions inside the merge commit: `package.json` is the frontend's, with `name` set to `agents-web` and a `fmt` script `eslint src --fix` added (the scaffold `.mise.toml` runs `npm run fmt`); `.gitignore` is the union (`node_modules/`, `dist/`); scaffold `AGENTS.md`, `CLAUDE.md`, `MEMORY.md`, `ROADMAP.md`, `README.md`, `.mise.toml` are kept. The merge message names `<ao-sha>`.
4. `MEMORY.md` gets a dated 2026-10-25 entry: "imported frontend/ from agent-orchestrator <ao-sha> with history (git subtree split); agent-orchestrator/frontend is frozen from this commit until frontend-decoupling deletes it".
5. `npm ci --no-audit --no-fund && npm test && npm run lint` pass in `code/agents-web`; then push main to origin (a fast-forward of the scaffold commit; the repo is new and has no CI yet).
6. Commit the superrepo changes (`.gitmodules`, the `code/agents-web` gitlink, the `AGENTS.md` components row component-add writes) on this task's branch. Fill the role in the `AGENTS.md` project block if component-add left a placeholder.

The scripts `gen:api` and `check:api` still point at `../openapi.json` after the import; frontend-decoupling task web-openapi-vendor fixes them. Do not touch any file of agent-orchestrator.

## Acceptance conditions

- AC1: the public GitHub repo szymonrychu/agents-web exists and its main is the local main [evidence: command:gh repo view szymonrychu/agents-web --json visibility -q .visibility | grep -qx PUBLIC && cd code/agents-web && git fetch -q origin && test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"]
- AC2: code/agents-web is a submodule of the workbench tracking main [evidence: command:git config --file .gitmodules --get submodule.agents-web.branch | grep -qx main && git ls-files --stage code/agents-web | grep -q '^160000']
- AC3: the frontend history is kept at the repo root [evidence: command:cd code/agents-web && test "$(git rev-list --count HEAD -- src/api/client.ts)" -ge 2 && test -n "$(git ls-files src/App.tsx)" && test -z "$(git ls-files index.js index.test.js frontend)"]
- AC4: the moved UI passes its own tests and lint [evidence: command:cd code/agents-web && npm ci --no-audit --no-fund && npm test && npm run lint]
- AC5: MEMORY.md records the imported agent-orchestrator commit and the freeze [evidence: command:grep -Eq 'agent-orchestrator [0-9a-f]{40}' code/agents-web/MEMORY.md && grep -q frozen code/agents-web/MEMORY.md]
- AC6: no agent-orchestrator file changed and no repo other than szymonrychu/agents-web was created [evidence: judgement:the task diff and the gh calls in the task notes reviewed against the requirement]

## Files

- `.gitmodules`
- `code/agents-web`
- `AGENTS.md`

## Interfaces

- Provides contract `agents-web-repo` (docs/plans/contracts.json): `code/agents-web`, origin https://github.com/szymonrychu/agents-web, the frontend at the repo root with its history, and the import line `agent-orchestrator <sha40>` in its `MEMORY.md`, read by frontend-decoupling tasks web-openapi-vendor and orch-drop-frontend-build.

## Expected outcome

`code/agents-web` is a workbench submodule whose main holds the moved UI with its git history, green on `npm test` and `npm run lint`.

## Steps

- Check the precondition.
- `mise run component:add -- ...` as in the requirement; confirm `gh repo view szymonrychu/agents-web`.
- Subtree split and merge in `code/agents-web`; `npm ci && npm test && npm run lint`: pass; push main.
- Commit the superrepo changes; run the AC commands.

## Notes

- No TDD cycle applies: repository creation and a history import with no behaviour change (the moved code's own tests are the check).
- After this epic closes, the orchestrator runs `git submodule update --init code/agents-web` in the main checkout before frontend-decoupling starts: ticket.py treats a task repo without a `code/<repo>` checkout as a meta task.
- `git subtree split` keeps the commit history of `frontend/` with paths rewritten to the root; `git merge --allow-unrelated-histories` joins it to the scaffold commit.

Orchestrator notes (2026-10-25): step 1 is DONE by the orchestrator (the permission classifier refuses public repo creation inside subagents; the user approved a rule): `mise run component:add` created https://github.com/szymonrychu/agents-web (public), added submodule code/agents-web and committed "chore(workbench): add component agents-web" on this task's branch. Start at step 2. If `git push` to the new repo is denied in step 5, stop as blocked with whoCanClear "orchestrator" and leave everything else committed.
