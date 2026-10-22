# Init leaves a green tree design

## Summary

Init (new and adopt) and component add must leave a workbench whose `mise run lint` and
`mise run test` are green. Today an adopt of a real GitHub repo leaves both red (FEEDBACK.md
sections 1-6). Headline decisions: a project-owned allow file for lint:personal that init and
component add fill from their own output; lint:secrets drops gitlinks from the scan list; the
license holder lands in every LICENSE; a `template` pytest marker skips template-only
self-tests once the tree is initialised; the init and component-add skills tell the truth about
local-bare and the --path move.

## Intent and why

The user initialised claude-code-tatara and got a red tree on the first commit, which breaks the
workbench's own rules (TDD, boy scout, never ship on red) before any work starts. Every future
workbench made from this template would hit the same defects. Discovery facts:
`/private/tmp/claude-501/-Users-szymonri-Documents-claude-code-tatara/21d1a847-8d6b-4ee4-a271-ba52ec27cf3b/scratchpad/epic/discovery.md`
and `~/Documents/FEEDBACK.md`.

## Goals

- G1: an init (new or adopt) and a component add leave lint and test green, proven by e2e tests
  whose project name and component owner collide with a denylisted hash and whose component
  checkout holds a secret-shaped fixture.
- G2: lint:personal accepts the project's own vocabulary through a project-owned allow file.
- G3: lint:secrets scans the metarepo's own files, never a gitlink checkout, with no allowlist.
- G4: the license holder (explicit or git-author default) lands in root and every plugins/*/LICENSE.
- G5: template-only self-tests skip in an initialised workbench and still run in the template.
- G6: init and component-add skills state the local-bare limits and the --path move.

## Non-goals

- No change to the shipped denylist terms or hashes.
- No secret scanning of component repos from the metarepo; each component scans itself.
- No push of the template.

## Anti-goals

- Weakening lint:personal for the template itself: the template tree must still fail on any
  denylisted term.
- A gitleaks allowlist, or skipping any non-gitlink file from the secrets scan.
- Skipping a test in the template (the `template` marker must be a no-op there).

## Constraints

- Tests first, red seen (rules/tdd.md). `mise run lint` and `mise run test` green before landing.
- Reuse check_personal `_digest`/`_candidates`, finalize `read_json`/`write_json`,
  project_files `components()`; do not re-implement them.
- Keep the literal `git ls-files -coz --exclude-standard` in mise-tasks/lint/secrets
  (test_secret_scanning.py pins it).
- Plain ASCII in docs (no em dashes, smart quotes, arrows).

## Decisions

### D1: project-owned allow file for lint:personal

`scripts/check_personal.py` also reads `scripts/personal-allow.local.json` (shape
`{"allow": [...]}`, same entry shape as the denylist's `allow`) when present and appends its
entries to the allow list. The template ships no such file. template-update treats it as
project-owned (never arrives, never overwritten). The shipped `personal-denylist.json` stays
byte-identical after init, so `test_shipped_denylist_is_hashed_only` keeps holding.
Alternatives: edit the shipped denylist (breaks its pin and conflicts on every update); drop the
colliding hashes (loses the guard for other files). (my call) Serves A.

### D2: init and component add write the allow entries from their own output

After init or component add writes its files and before its commit, the engine scans the files
it generated or changed (AGENTS.md, docs/architecture.md, MEMORY.md, ROADMAP.md, .gitmodules,
LICENSE files, workbench.json, any other path in the init commit) with check_personal's own
digest code. Each digest hit adds `{"path": "**", "pattern": "<digest>"}` to the allow file
(deduplicated, sorted, written with finalize.write_json); `component remove` leaves entries in
place. Literal pattern hits (`/Users/`, `192.168.`, ...) are never auto-allowed: init still
leaves them for the lint to report. Alternative: hash only the project and component names
(misses the owner in .gitmodules and words in the purpose). Project-wide `**` scope confirmed by the user at the gate, 2026-10-22. Serves A.

### D3: lint:secrets skips gitlinks

The task builds the set of gitlink paths (`git ls-files -s` entries with mode 160000) and skips
them in its copy loop, keeping the `git ls-files -coz --exclude-standard` listing; every other
file is still copied and scanned. No `.gitleaks.toml` allowlist. Components run their own secret
scanning. Alternative: a `.gitleaks.toml` path allowlist (breaks test_secret_scanning.py:19/:26
and the template's no-allowlist policy). Serves B.

### D4: the holder lands in every LICENSE

`finalize.license_file` rewrites the Copyright line of the root LICENSE and of every
`plugins/*/LICENSE` with the same holder (explicit `--license-holder`, else `default_holder`);
`--license none` removes only the root LICENSE (plugin licenses stay, rewritten). The template's
`plugins/workbench-secrets/LICENSE` is aligned with the root holder. `test_license_options` is
updated, and a test pins every plugins/*/LICENSE == root after init and the default-holder
fallback. Init SKILL.md says the holder defaults to the git author. A custom `--license-file` is copied over the root and every plugins/*/LICENSE (user confirmed at the gate, 2026-10-22). template-update keeps the project side of every plugins/*/LICENSE. Serves C.

### D5: a `template` pytest marker, skipped once initialised

Register a `template` marker in pyproject.toml. A `scripts/tests/conftest.py` (and the same
hook for the pack and plugin test roots that need it) skips marked tests when the workbench root
is initialised. One helper `is_initialised(root)` in `scripts/init_engine/project_files.py`
(AGENTS.md has no uninitialised block) owns the check; cli.py:159-162, update.py:16-18 and
doctor.py:94 call it instead of their copies. Every test that asserts the uninitialised template
state, or whose fixture copies the live root's template files, gets the marker (the list in the
discovery brief section 5). Tests that pass on an initialised tree stay unmarked. A test runs
the suite against an initialised copy and asserts no failures. Alternatives: retire template
tests at init through owned.INSTANCE_OWNED (template-update brings scripts/ back, and the pinned
owned list changes); rebuild fixtures from a pristine template snapshot (none exists offline
after init). (my call) Serves D.

### D6: skill text

`plugins/workbench/skills/init/SKILL.md` step 1 says adopt accepts `local-bare[:<dir>]` only
with `--path` on a checkout that has no origin, and never with `--url`; step 3 says `--path`
moves the checkout into `code/<name>` (the original path no longer exists). `component-add`
SKILL.md says the same for its existing-checkout mode. test_init_skills.py pins both. Serves E.

### D7: end-to-end proof

e2e tests initialise a template copy (new and adopt) whose project name and adopted repo owner
are terms whose digests are in that copy's denylist, adopt a component whose checkout holds a
secret-shaped fixture built at run time, then add a second component, and assert `mise run lint`
and `mise run test` exit 0 and `git status` is clean after each step. Serves A, B, C, D.

## Research

| Lens | Ran or skipped | Adopted | Rejected |
|---|---|---|---|
| research-code-internal | ran (reuse-hunter) | _digest/_candidates reuse, read_json/write_json, components(), default_holder exists, one is_initialised helper (cli.py:159, update.py:16, doctor.py:94) | .gitleaks.toml allowlist (test_secret_scanning.py:26) |
| research-code-external | skipped: in-house glue, no external analogue decides it | - | - |
| research-papers | skipped: no algorithmic core | - | - |
| research-docs | skipped: gitleaks and pytest used as already pinned; markers and conftest skip are core pytest | - | - |

## Research inputs

| Source | Entry | Lands in |
|---|---|---|
| discovery 1/2 | reuse _digest/_candidates, read_json/write_json, components() | personal-allow-file, init-writes-allow-entries |
| discovery 1/2 | component add writes .gitmodules via write_all path | init-writes-allow-entries |
| discovery 3 | cp -RP copies gitlink checkouts | secrets-skip-gitlinks |
| discovery 4 | license_file root only; default_holder untested; secrets pack LICENSE inconsistent | license-every-plugin |
| discovery 5 | no markers; is_initialised copied three times; failing test list | template-marker-skip |
| discovery 6 | SKILL.md:24-26, :46, component-add SKILL.md:30 | skill-text-local-bare-move |
| FEEDBACK.md all | e2e proof | e2e-init-green |

## Decision coverage

| Decision | Tasks |
|---|---|
| D1 project-owned allow file for lint:personal | personal-allow-file |
| D2 init and component add write the allow entries | init-writes-allow-entries |
| D3 lint:secrets skips gitlinks | secrets-skip-gitlinks |
| D4 the holder lands in every LICENSE | license-every-plugin |
| D5 a template pytest marker | template-marker-skip |
| D6 skill text | skill-text-local-bare-move |
| D7 end-to-end proof | e2e-init-green |

## Contracts

| Part | Owner | Consumers | Where defined |
|---|---|---|---|
| `personal-allow-local` | personal-allow-file | init-writes-allow-entries, e2e-init-green | `scripts/check_personal.py` |
| `is-initialised` | template-marker-skip | e2e-init-green | `scripts/init_engine/project_files.py` |

## Review focus

- lint:personal must still fail in the template tree on any denylisted term; the local file must
  only ever add allow entries, never remove patterns or hashes.
- lint:secrets must still scan every non-gitlink tracked and untracked file, including files
  inside `code/` that are not gitlinks (e.g. code/.gitkeep).
- The `template` marker must never skip anything in the uninitialised template.
- template-update must not overwrite or delete personal-allow.local.json.

## Left to the builder

- How the gitlink set is built in bash (bash 3.2 compatible, no associative arrays).
- Exact list of files D2 scans, as long as it covers every file the init or component-add
  commit touches.
- Whether pack/plugin test roots need their own conftest hook or are green after D4 alone.

## Assumptions and unknowns

- Assumed: no plugin test (test:plugin) fails on an initialised tree beyond the pack LICENSE
  test; confirmed by the D5 whole-suite test on an initialised copy.
- Assumed: template-update has a project-owned path list the allow file can join; the builder
  confirms in scripts/init_engine/update.py.

## Open questions

none

## Irreversible operations in scope

none
