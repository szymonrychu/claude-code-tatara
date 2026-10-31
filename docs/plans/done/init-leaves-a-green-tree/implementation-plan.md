# Init leaves a green tree implementation plan

## Agreed rung

Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks.

## Approach

Migrated from the epic format: one step per task file, in dependency order, each with its status, files, verify, verified head and every body section.

## Chunk 1: migrated tasks (model: sonnet)

### S1: personal allow file

- Status: done
- Files: `scripts/check_personal.py`, `scripts/tests/test_check_personal.py`, `scripts/tests/init_engine/test_update.py`
- Verify: `mise exec -- pytest scripts/tests/test_check_personal.py scripts/tests/init_engine/test_update.py -q && mise run lint:personal`
- Verified head: 191d8ecfd47512fccb20c27e27b6656b4286f39f

#### Requirement

scripts/check_personal.py also reads scripts/personal-allow.local.json (shape {"allow": [...]}, same entry shape as the shipped denylist allow) when present and appends its entries to the allow list; a missing file changes nothing. The file only ever adds allow entries; it cannot remove patterns or hashes. The template ships no such file and scripts/personal-denylist.json stays byte-identical. template-update never brings or overwrites the file (a test pins this). In the template tree lint:personal still fails on any denylisted term.

#### Acceptance conditions

- AC1: a term whose digest is denylisted passes once an allow entry for its path and digest is in personal-allow.local.json [evidence: test:scripts/tests/test_check_personal.py::test_local_allow_file_accepts_project_vocabulary]
- AC2: without the local file the same term still fails, and the local file cannot remove a denylist pattern [evidence: test:scripts/tests/test_check_personal.py::test_local_allow_file_only_adds]
- AC3: the shipped denylist stays hashed-only and the template tree stays clean [evidence: test:scripts/tests/test_check_personal.py::test_shipped_denylist_is_hashed_only]
- AC4: a template update leaves a project's personal-allow.local.json untouched [evidence: test:scripts/tests/init_engine/test_update.py::test_update_keeps_personal_allow_local]

#### Files

- `scripts/check_personal.py`
- `scripts/tests/test_check_personal.py`
- `scripts/tests/init_engine/test_update.py`

#### Interfaces

check_personal.py: scan() also loads scripts/personal-allow.local.json (`{"allow": [{"path", "pattern"}]}`) when it exists; contract personal-allow-local.

#### Expected outcome

With a matching local allow entry lint:personal passes; without it the same term fails; the template tree is unchanged.

#### Steps

- Write the failing tests in test_check_personal.py and test_update.py; run them red.
- Extend scan() in scripts/check_personal.py to append local allow entries; run green, then `mise run lint:personal`.

#### Notes

Design D1. Reuse the existing allow-entry shape. template-update never brings the file because the template does not ship it; pin that.

### S2: ruff E501 errors in scripts/tests/test_secret_scanning.py (e.g. line 193) make `mise run lint` root fail after merging the epic branch

- Status: done
- Files: `scripts/tests/test_secret_scanning.py:193`
- Verify: none
- Verified head: 5619cda9d76f90d8717064e2dddaac772bfe5bdd

#### Requirement

ruff E501 errors in scripts/tests/test_secret_scanning.py (e.g. line 193) make `mise run lint` root fail after merging the epic branch

Where: scripts/tests/test_secret_scanning.py:193

Why: owned by the gitlink-free secrets scan task; lint:root fails until fixed

#### Acceptance conditions

- AC1: ruff E501 errors in scripts/tests/test_secret_scanning.py (e.g. line 193) make `mise run lint` root fail after merging the epic branch at scripts/tests/test_secret_scanning.py:193 is resolved [evidence: judgement]

#### Files

- `scripts/tests/test_secret_scanning.py:193`

#### Interfaces

Keep the interfaces around scripts/tests/test_secret_scanning.py:193 unchanged unless resolving it requires otherwise: ruff E501 errors in scripts/tests/test_secret_scanning.py (e.g. line 193) make `mise run lint` root fail after merging the epic branch.

#### Expected outcome

ruff E501 errors in scripts/tests/test_secret_scanning.py (e.g. line 193) make `mise run lint` root fail after merging the epic branch at scripts/tests/test_secret_scanning.py:193 is resolved, and owned by the gitlink-free secrets scan task; lint:root fails until fixed no longer applies.

#### Steps

1. Write a failing test that shows: ruff E501 errors in scripts/tests/test_secret_scanning.py (e.g. line 193) make `mise run lint` root fail after merging the epic branch.
2. Fix it at scripts/tests/test_secret_scanning.py:193.
3. Run the task verify command and confirm it passes.

#### Ruling

- 2026-10-22 accepted: e2e-init-green: verifier timed out (540s deadline vs 48-min file); hand-verified on 27d001e: 'mise exec -- pytest scripts/tests/e2e/test_instantiate.py -q' -> 7 passed in 2867.48s. ruff-e501: no change needed, the wrap landed in ce694a7; no targeted tests apply (pure formatting).

#### Notes

Discovered in task `init-writes-allow-entries` during run `init-leaves-a-green-tree`.

### S3: secrets skip gitlinks

- Status: done
- Files: `mise-tasks/lint/secrets`, `scripts/tests/test_secret_scanning.py`
- Verify: `mise exec -- pytest scripts/tests/test_secret_scanning.py -q && mise run lint:secrets`
- Verified head: 18769df0a3587552e11f617b38624f8e0d917c5d

#### Requirement

mise-tasks/lint/secrets builds the set of gitlink paths (git ls-files -s entries of mode 160000) and skips them in its copy loop, so no submodule checkout is staged for gitleaks. It keeps the literal `git ls-files -coz --exclude-standard` listing, --redact and --config, stays bash 3.2 compatible (no associative arrays), copies and scans every other tracked and untracked file (including code/.gitkeep and files inside code/ that are not gitlinks), and .gitleaks.toml gains no allowlist.

#### Acceptance conditions

- AC1: a secret-shaped fixture inside a gitlink checkout is not reported and the task exits 0 [evidence: test:scripts/tests/test_secret_scanning.py::test_lint_task_skips_gitlink_checkouts]
- AC2: a leak in a non-gitlink file under code/ is still detected [evidence: test:scripts/tests/test_secret_scanning.py::test_lint_task_scans_non_gitlink_files_under_code]
- AC3: the existing pins (literal listing, no allowlist) still pass [evidence: test:scripts/tests/test_secret_scanning.py::test_pinned_and_no_allowlist]
- AC4: the secrets lint family passes [evidence: command:mise run lint:secrets]

#### Files

- `mise-tasks/lint/secrets`
- `scripts/tests/test_secret_scanning.py`

#### Interfaces

mise-tasks/lint/secrets: bash 3.2, no associative arrays; keep literal `git ls-files -coz --exclude-standard`.

#### Expected outcome

A gitlink checkout holding a secret-shaped fixture does not fail the task; a leak in any non-gitlink file still does.

#### Steps

- Add the two failing tests to test_secret_scanning.py (fixture secret built at run time); run red.
- Build the gitlink path set from `git ls-files -s` (mode 160000) and skip those in the copy loop; run green, then `mise run lint:secrets`.

#### Notes

Design D3. test_secret_scanning.py:19/:26 pin the no-allowlist policy; do not touch .gitleaks.toml. Precedent for 160000 detection: test_adopt.py:99.

### S4: license every plugin

- Status: done
- Files: `scripts/init_engine/finalize.py`, `scripts/init_engine/owned.py`, `scripts/init_engine/update.py`, `scripts/tests/init_engine/test_update.py`, `scripts/tests/init_engine/test_finalize.py`, `plugins/workbench-secrets/LICENSE`, `plugins/workbench/skills/init/SKILL.md`
- Verify: `mise exec -- pytest scripts/tests/init_engine/test_finalize.py scripts/tests/init_engine/test_update.py plugins/workbench-infra/tests/test_pack_infra.py scripts/tests/test_root_stubs.py -q && mise run lint:personal`
- Verified head: $(see below)

#### Requirement

finalize.license_file rewrites the Copyright line of the root LICENSE and of every plugins/*/LICENSE with the same holder (explicit --license-holder, else default_holder, the git author). --license none removes only the root LICENSE; plugin licenses stay and are rewritten. plugins/workbench-secrets/LICENSE in the template is aligned with the root holder. test_license_options is updated; tests pin every plugins/*/LICENSE == root after init and the default-holder fallback. The init SKILL.md says the holder defaults to the git author. template-update keeps the project side of every plugins/*/LICENSE exactly as it keeps the root LICENSE (owned.GENERATED_ON_CONFLICT or its equivalent), so a holder rewrite never conflicts on update. --license-file <path> copies that file over the root LICENSE and every plugins/*/LICENSE. Pack LICENSE tests stay green under every --license mode.

#### Acceptance conditions

- AC1: after init with --license-holder every plugins/*/LICENSE Copyright line equals the root one [evidence: test:scripts/tests/init_engine/test_finalize.py::test_license_holder_in_every_plugin]
- AC2: without --license-holder the git author is used in all licenses [evidence: test:scripts/tests/init_engine/test_finalize.py::test_license_default_holder_fallback]
- AC3: --license none removes only the root LICENSE [evidence: test:scripts/tests/init_engine/test_finalize.py::test_license_options]
- AC4: the pack LICENSE test passes [evidence: test:plugins/workbench-infra/tests/test_pack_infra.py::test_license_and_readme]
- AC5: init SKILL.md states the git-author default [evidence: judgement:]
- AC6: template-update keeps the project holder in every plugins/*/LICENSE without a conflict [evidence: test:scripts/tests/init_engine/test_update.py::test_update_keeps_plugin_license_holder]
- AC7: --license-file lands in the root and every plugins/*/LICENSE [evidence: test:scripts/tests/init_engine/test_finalize.py::test_license_file_in_every_plugin]

#### Files

- `scripts/init_engine/finalize.py`
- `scripts/tests/init_engine/test_finalize.py`
- `plugins/workbench-secrets/LICENSE`
- `scripts/init_engine/owned.py`
- `scripts/init_engine/update.py`
- `scripts/tests/init_engine/test_update.py`
- `plugins/workbench/skills/init/SKILL.md`

#### Interfaces

finalize.license_file(root, opts, first): rewrites root LICENSE and every plugins/*/LICENSE; default_holder(root) is the fallback.

#### Expected outcome

Every LICENSE Copyright line carries the same holder after init; --license none removes only the root file.

#### Steps

- Write failing tests (every plugin LICENSE equals root; default-holder fallback) and update test_license_options; run red.
- Extend license_file in scripts/init_engine/finalize.py, align plugins/workbench-secrets/LICENSE, edit init SKILL.md; run green.

#### Notes

Design D4. test_pack_infra.py::test_license_and_readme and test_root_stubs.py::test_license_mit_identical must stay green in the template.

### S5: init writes allow entries

- Status: done
- Files: `scripts/init_engine/finalize.py`, `scripts/init_engine/cli.py`, `scripts/init_engine/project_files.py`, `scripts/tests/init_engine/test_new.py`, `scripts/tests/init_engine/test_adopt.py`, `scripts/tests/init_engine/test_component.py`
- Verify: `mise exec -- pytest scripts/tests/init_engine/test_new.py scripts/tests/init_engine/test_adopt.py scripts/tests/init_engine/test_component.py -q && mise run lint:personal`
- Verified head: 5d7ad13c4af6f8b19ccfb2c9b5b948fd4e937fd7

#### Requirement

After init (new and adopt) and component add write their files and before their commit, the engine scans every file it generated or changed (AGENTS.md, docs/architecture.md, MEMORY.md, ROADMAP.md, .gitmodules, LICENSE files, workbench.json, any other path in the commit) with check_personal's own _digest/_candidates (imported, not re-implemented). Each digest hit adds {"path": "**", "pattern": "<digest>"} to scripts/personal-allow.local.json (deduplicated, sorted, written with finalize.write_json, read with finalize.read_json); the file is staged in the same commit. component remove leaves entries in place. Literal pattern hits (/Users/, 192.168. ...) are never auto-allowed. After each step `mise run lint:personal` exits 0 for a project name and component owner whose digests are denylisted.

#### Acceptance conditions

- AC1: init with a project name whose digest is denylisted writes the allow entry and lint:personal passes [evidence: test:scripts/tests/init_engine/test_new.py::test_init_allows_project_vocabulary]
- AC2: adopt with an owner whose digest is denylisted (in .gitmodules) writes the entry [evidence: test:scripts/tests/init_engine/test_adopt.py::test_adopt_allows_owner_vocabulary]
- AC3: component add writes entries for its own output, deduplicated and sorted [evidence: test:scripts/tests/init_engine/test_component.py::test_component_add_allows_owner_vocabulary]
- AC4: a literal pattern hit is not auto-allowed [evidence: test:scripts/tests/init_engine/test_new.py::test_literal_hits_not_auto_allowed]
- AC5: the personal lint family passes on the changed files [evidence: command:mise run lint:personal]

#### Files

- `scripts/init_engine/finalize.py`
- `scripts/init_engine/cli.py`
- `scripts/init_engine/project_files.py`
- `scripts/tests/init_engine/test_new.py`
- `scripts/tests/init_engine/test_adopt.py`
- `scripts/tests/init_engine/test_component.py`

#### Interfaces

finalize: a helper that digests the generated files with check_personal._digest/_candidates and writes scripts/personal-allow.local.json via read_json/write_json; called by init, adopt and cli.cmd_component_add before their commit.

#### Expected outcome

After init, adopt and component add the personal lint is green for denylisted project and owner names, and the allow file is in the same commit.

#### Steps

- Write the failing tests in test_new.py, test_adopt.py, test_component.py; run red.
- Implement the helper and call it before each commit; run green, then `mise run lint:personal`.

#### Notes

Design D2. Import check_personal from scripts/ (see finalize.collision_override for the loader pattern). Never auto-allow literal pattern hits. component remove leaves entries.

### S6: skill text local bare move

- Status: done
- Files: `plugins/workbench/skills/init/SKILL.md`, `plugins/workbench/skills/component-add/SKILL.md`, `plugins/workbench/skills/init/tests/test_init_skills.py`
- Verify: `mise exec -- pytest plugins/workbench/skills/init/tests/test_init_skills.py -q`
- Verified head: 9577be0393919b2aa6906bf191ca2e0a3b5da8fd

#### Requirement

plugins/workbench/skills/init/SKILL.md step 1 says adopt accepts local-bare[:<dir>] only with --path on a checkout that has no origin, and never with --url; step 3 says --path moves the checkout into code/<name> (the original path no longer exists). plugins/workbench/skills/component-add/SKILL.md says the same for its existing-checkout mode. test_init_skills.py pins both statements.

#### Acceptance conditions

- AC1: init SKILL.md states the local-bare limits and the --path move [evidence: test:plugins/workbench/skills/init/tests/test_init_skills.py::test_init_skill_states_local_bare_and_move]
- AC2: component-add SKILL.md states the --path move [evidence: test:plugins/workbench/skills/init/tests/test_init_skills.py::test_component_add_skill_states_move]

#### Files

- `plugins/workbench/skills/init/SKILL.md`
- `plugins/workbench/skills/component-add/SKILL.md`
- `plugins/workbench/skills/init/tests/test_init_skills.py`

#### Interfaces

none

#### Expected outcome

Both SKILL.md files state the local-bare limits and that --path moves the checkout into code/<name>.

#### Steps

- Add the two failing doc assertions to test_init_skills.py; run red.
- Edit init SKILL.md steps 1 and 3 and component-add SKILL.md; run green.

#### Notes

Design D6. Engine facts: adopt.plan_path accepts local-bare only with --path and no origin; cli.cmd_adopt refuses it with --url; the move is os.rename in adopt.py.

### S7: template marker skip

- Status: done
- Files: `pyproject.toml`, `scripts/tests/conftest.py`, `scripts/init_engine/project_files.py`, `scripts/init_engine/cli.py`, `scripts/init_engine/update.py`, `scripts/doctor.py`, `scripts/tests/test_root_config.py`, `scripts/tests/init_engine/test_project_files.py`
- Verify: `mise exec -- pytest scripts/tests/test_root_config.py scripts/tests/init_engine/test_project_files.py scripts/tests/test_doctor.py -q && mise run lint:root`
- Verified head: 5619cda9d76f90d8717064e2dddaac772bfe5bdd

#### Requirement

Register a `template` marker in pyproject.toml. scripts/tests/conftest.py skips marked tests when the workbench root is initialised, and is a no-op in the uninitialised template (the marker never skips anything there). One helper is_initialised(root) in scripts/init_engine/project_files.py (AGENTS.md has no uninitialised block) owns the check; cli.py, update.py and doctor.py call it instead of their copies. Every test that asserts the uninitialised template state, or whose fixture copies the live root's template files, gets the marker (list in discovery brief section 5: the e2e instantiate/template_update tests, the listed finalize, project_files, refresh, update, update_conflicts, update_unrelated, agents_md, check_personal, lint_personal_task, marketplace, root_stubs, root_tooling and secret_scanning tests). Tests that pass on an initialised tree stay unmarked. The whole-suite run on an initialised copy is e2e-init-green AC4. scripts/doctor.py is a standalone script: load project_files through the sibling loader pattern (finalize.collision_override) or sys.path, whichever doctor already supports. Pack/plugin test roots get the same hook only if still red after license-every-plugin.

#### Acceptance conditions

- AC1: is_initialised is true for an initialised AGENTS.md and false for the template one [evidence: test:scripts/tests/init_engine/test_project_files.py::test_is_initialised]
- AC2: the template marker is registered and skips nothing in the uninitialised template [evidence: test:scripts/tests/test_root_config.py::test_template_marker_registered_and_noop_in_template]
- AC3: a TEMPLATE_ONLY id that names no collected test fails collection, so the list cannot rot [evidence: test:scripts/tests/test_root_config.py::test_template_only_ids_all_exist]
- AC4: cli, update and doctor use the shared helper [evidence: symbol:scripts/init_engine/project_files.py::is_initialised]

#### Files

- `pyproject.toml`
- `scripts/tests/conftest.py`
- `scripts/init_engine/project_files.py`
- `scripts/init_engine/cli.py`
- `scripts/init_engine/update.py`
- `scripts/doctor.py`
- `scripts/tests/test_root_config.py`
- `scripts/tests/init_engine/test_project_files.py`

#### Interfaces

project_files.is_initialised(root) -> bool; pytest marker `template`; scripts/tests/conftest.py collection hook.

#### Expected outcome

Template-only tests skip in an initialised workbench, run in the template; the suite is green on an initialised copy.

#### Steps

- Write failing tests for is_initialised, marker registration and the initialised-copy suite run; run red.
- Add the helper, replace the copies in cli.py, update.py, doctor.py, register the marker, add the conftest hook, mark the template-only tests; run green, then `mise run lint:root`.

#### Ruling

- 2026-10-22 accepted: gate-repeat false positive: conftest.py:78 skipif is the deliverable (template marker skip, D5), not a debt marker; conftest.py:68 is an explanatory comment on the stale-id check, not parking. Verified on 5619cda: 31 passed, lint:root clean.

#### Notes

Design D5. The marker is applied centrally: conftest.py holds the TEMPLATE_ONLY list of test node ids and adds the template marker to them at collection, so no other test file is edited. Test list in the discovery brief section 5. Do not touch owned.INSTANCE_OWNED. The marker must be a no-op in the template.

### S8: e2e init green

- Status: done
- Files: `scripts/tests/e2e/test_instantiate.py`, `scripts/tests/e2e/helpers.py`, `scripts/tests/e2e/conftest.py`
- Verify: `mise exec -- pytest scripts/tests/e2e/test_instantiate.py -q`
- Verified head: 27d001e0d8cbaf0335376f2c75492f90f82cc853

#### Requirement

e2e tests initialise a template copy (new and adopt) whose project name and adopted repo owner are terms whose digests are in that copy's denylist, adopt a component whose checkout holds a secret-shaped fixture built at run time, then add a second component, and assert `mise run lint` and `mise run test` exit 0 and `git status` is clean after each step. Uses the personal-allow.local.json writer and reader, the gitlink-skipping secrets task, the all-LICENSE holder and is_initialised/template marker from the other tasks.

#### Acceptance conditions

- AC1: new init leaves lint and test green and a clean status [evidence: test:scripts/tests/e2e/test_instantiate.py::test_new_init_leaves_green_tree]
- AC2: adopt of a repo with a colliding owner and secret-shaped fixture leaves lint and test green [evidence: test:scripts/tests/e2e/test_instantiate.py::test_adopt_leaves_green_tree]
- AC3: a second component add keeps lint and test green [evidence: test:scripts/tests/e2e/test_instantiate.py::test_second_component_add_stays_green]
- AC4: the scripts suite run against an initialised copy has no failures [evidence: test:scripts/tests/e2e/test_instantiate.py::test_suite_green_on_initialised_copy]

#### Files

- `scripts/tests/e2e/test_instantiate.py`
- `scripts/tests/e2e/helpers.py`
- `scripts/tests/e2e/conftest.py`

#### Interfaces

none

#### Expected outcome

New init, adopt with a colliding owner and secret fixture, and a second component add each leave lint and test green and git status clean.

#### Steps

- Write the failing e2e tests in test_instantiate.py first (red if any other task is missing).
- Fix any remaining gap they expose in the owning task's files; run green.

#### Ruling

- 2026-10-22 accepted: e2e-init-green: verifier timed out (540s deadline vs 48-min file); hand-verified on 27d001e: 'mise exec -- pytest scripts/tests/e2e/test_instantiate.py -q' -> 7 passed in 2867.48s. ruff-e501: no change needed, the wrap landed in ce694a7; no targeted tests apply (pure formatting).

#### Notes

Design D7. Build the secret-shaped fixture at run time; pick a project name and owner whose digests are in the copy's denylist.

- 2026-10-22 run init-leaves-a-green-tree: dependency-failed on template-marker-skip

### S9: refresh writes allow entries

- Status: done
- Files: `scripts/init_engine/cli.py`, `scripts/tests/init_engine/test_refresh.py`, `scripts/tests/init_engine/test_update.py`
- Verify: `mise exec -- pytest scripts/tests/init_engine/test_refresh.py scripts/tests/init_engine/test_update.py -q && mise run lint:personal`
- Verified head: 8bfd79ad2557a25c7f3c73ca2d9e6027773a3fb7

#### Requirement

`init:refresh` (scripts/init_engine/cli.py cmd_refresh, which template-update also runs after its merge at update.py:261) calls finalize.allow_vocabulary, so a workbench initialised before the allow file existed gains its project-vocabulary allow entries on refresh and on template-update. Found updating claude-code-tatara (initialised with the pre-fix template): init:update refused because lint:personal still failed on the project name in AGENTS.md and docs/architecture.md. The refresh writes and stages scripts/personal-allow.local.json in its own commit; literal pattern hits stay un-allowed; an already-correct allow file is left byte-identical.

#### Acceptance conditions

- AC1: refresh on an initialised workbench whose project name digest is denylisted writes the allow entry and lint:personal passes [evidence: test:scripts/tests/init_engine/test_refresh.py::test_refresh_allows_project_vocabulary]
- AC2: template-update of such a workbench (initialised without an allow file) completes and lint:personal passes [evidence: test:scripts/tests/init_engine/test_update.py::test_update_backfills_allow_file]
- AC3: refresh with a correct allow file leaves it byte-identical [evidence: test:scripts/tests/init_engine/test_refresh.py::test_refresh_allow_file_idempotent]

#### Files

- `scripts/init_engine/cli.py`
- `scripts/tests/init_engine/test_refresh.py`
- `scripts/tests/init_engine/test_update.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

Refresh and template-update leave lint:personal green on a workbench initialised before the allow file existed.

What is true and observable when the task is done.

#### Steps

- Write the three failing tests (refresh allows vocabulary, update backfills, idempotent); run red.
- Call finalize.allow_vocabulary from cmd_refresh and stage the allow file in its commit; run green, then mise run lint:personal.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S10: e2e behind slow marker

- Status: done
- Files: `pyproject.toml`, `scripts/tests/e2e/test_instantiate.py`, `.mise.toml`, `mise-tasks/test/scripts`, `.github/workflows/ci.yml`, `scripts/tests/test_root_config.py`, `scripts/tests/test_root_tooling.py`, `AGENTS.md`
- Verify: `mise exec -- pytest scripts/tests/test_root_config.py scripts/tests/test_root_tooling.py -q && mise exec -- pytest scripts/tests/e2e/test_instantiate.py -q -m 'not slow'`
- Verified head: 3145b85bafedc529a439194f60d7b2c7adcc88b5

#### Requirement

The template's default `mise run test` must not grow by the ~48 minutes the e2e green-tree tests take (review finding). Register a `slow` pytest marker in pyproject.toml; mark the heavy e2e tests in scripts/tests/e2e/test_instantiate.py `slow` (at least test_suite_green_on_initialised_copy and any test that runs the full `mise run test` inside a copy); the default test:scripts run deselects them (`-m "not slow"`); a new mise task `e2e` (NOT under the `test:` namespace, since root `test` depends on `test:*`) runs `pytest -m slow`; .github/workflows/ci.yml runs `mise run e2e` as its own job. The fast checks (new init, adopt, second component add asserting lint green and clean status) stay in the default suite, using lint plus a reduced, fast test target instead of the full suite. AGENTS.md Template maintenance and README "Maintaining the template" mention `mise run e2e`.

#### Acceptance conditions

- AC1: the default test:scripts run deselects slow tests and the slow marker is registered [evidence: test:scripts/tests/test_root_config.py::test_slow_marker_registered_and_deselected_by_default]
- AC2: `mise run e2e` exists outside the test: namespace and runs only slow tests [evidence: test:scripts/tests/test_root_tooling.py::test_e2e_task_runs_slow_tests]
- AC3: CI runs mise run e2e as its own job [evidence: test:scripts/tests/test_root_tooling.py::test_ci_runs_e2e_job]
- AC4: the fast green-tree e2e tests still run by default and pass [evidence: command:mise exec -- pytest scripts/tests/e2e/test_instantiate.py -q -m "not slow"]

#### Files

- `pyproject.toml`
- `scripts/tests/e2e/test_instantiate.py`
- `.mise.toml`
- `mise-tasks/test/scripts`
- `.github/workflows/ci.yml`
- `scripts/tests/test_root_config.py`
- `scripts/tests/test_root_tooling.py`
- `AGENTS.md`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

The requirement above holds, pinned by the acceptance tests.

What is true and observable when the task is done.

#### Steps

- Write the failing acceptance tests; run red.
- Implement; run green with the verify command.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S11: license missing refusal

- Status: done
- Files: `scripts/init_engine/finalize.py`, `scripts/tests/init_engine/test_finalize.py`
- Verify: `mise exec -- pytest scripts/tests/init_engine/test_finalize.py -q`
- Verified head: b8c4d961156e31aee4df83055a80b29e20456f66

#### Requirement

Restore the refusal finalize.license_file raised before this epic: with license unset (None) on the first run and the root LICENSE missing, init refuses with `Refusal("LICENSE is missing...")` as it did before (review finding, finalize.py:178-183), while the epic's new behaviour (holder in every plugins/*/LICENSE, --license none removes only the root, --license-file copied everywhere) stays.

#### Acceptance conditions

- AC1: first run with no --license and no root LICENSE refuses with the LICENSE-missing message [evidence: test:scripts/tests/init_engine/test_finalize.py::test_license_missing_refuses_on_first_run]
- AC2: existing license tests stay green [evidence: test:scripts/tests/init_engine/test_finalize.py::test_license_options]

#### Files

- `scripts/init_engine/finalize.py`
- `scripts/tests/init_engine/test_finalize.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

The requirement above holds, pinned by the acceptance tests.

What is true and observable when the task is done.

#### Steps

- Write the failing acceptance tests; run red.
- Implement; run green with the verify command.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

### S12: ci workflow test pins e2e job

- Status: done
- Files: `scripts/tests/test_ci_workflow.py`
- Verify: `mise exec -- pytest scripts/tests/test_ci_workflow.py -q`
- Verified head: 9d7de6cc5a869fa4377594c7b7c3bcbf2691d141

#### Requirement

scripts/tests/test_ci_workflow.py::test_has_check_and_secrets_jobs pins .github/workflows/ci.yml to exactly two jobs (asserts 2 == count of 'runs-on: ubuntu-latest'), so the e2e job added by e2e-behind-slow-marker fails the full suite (1 failed, 494 passed). Update the test to pin the three jobs check, secrets and e2e by name, with e2e running mise run e2e, without loosening the other assertions.

#### Acceptance conditions

- AC1: the CI workflow test pins jobs check, secrets and e2e and passes [evidence: test:scripts/tests/test_ci_workflow.py::test_has_check_and_secrets_jobs]

#### Files

- `scripts/tests/test_ci_workflow.py`

#### Interfaces

Signatures, schemas and contracts this task builds or must keep, with file:symbol.

#### Expected outcome

The full suite is green with the three CI jobs pinned.

What is true and observable when the task is done.

#### Steps

- The test currently fails on HEAD (red already seen: assert 3 == 2).
- Update it to pin check, secrets and e2e by name; run green.

Test first. One step per bullet, with the exact command and the output to expect.
A retirement test asserts on `git ls-files <path>`, never on the filesystem.

#### Notes

Context the implementer needs: pitfalls, shared parts to reuse, decisions already made.

## Files to delete

none recorded in the epic format

## Final verify

`mise run test && mise run lint`

## After merge

none

## Rulings (migrated)

- template-marker-skip: accept true, at 2026-10-22T15:15:32Z: gate-repeat false positive: conftest.py:78 skipif is the deliverable (template marker skip, D5), not a debt marker; conftest.py:68 is an explanatory comment on the stale-id check, not parking. Verified on 5619cda: 31 passed, lint:root clean.
- e2e-init-green: accept true, at 2026-10-22T20:43:01Z: e2e-init-green: verifier timed out (540s deadline vs 48-min file); hand-verified on 27d001e: 'mise exec -- pytest scripts/tests/e2e/test_instantiate.py -q' -> 7 passed in 2867.48s. ruff-e501: no change needed, the wrap landed in ce694a7; no targeted tests apply (pure formatting).
- ruff-e501-errors-in-scripts: accept true, at 2026-10-22T20:43:01Z: e2e-init-green: verifier timed out (540s deadline vs 48-min file); hand-verified on 27d001e: 'mise exec -- pytest scripts/tests/e2e/test_instantiate.py -q' -> 7 passed in 2867.48s. ruff-e501: no change needed, the wrap landed in ce694a7; no targeted tests apply (pure formatting).
