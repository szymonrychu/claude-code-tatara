// validate-tasks.mjs --epic: test refs no runner can execute are lint failures (D6).
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'

const CLI = fileURLToPath(new URL('../validate-tasks.mjs', import.meta.url))
const README = `---\ntitle: Alpha\nblockers: []\nstage: build\nrepos: [api]\ncreated: 2026-10-17\n---\n\n# Alpha\n\n## Project brief\n\nWhat: a\nHow: b\nWhy: c\n\n## Description\n\nd\n\n## Goals\n\n- g\n\n## Non-goals\n\n- n\n`
const DESIGN = `# D\n\n## Decisions\n\n### D1: first\n\ntext\n\n## Decision coverage\n\n| Decision | Tasks |\n|---|---|\n| D1 first | t-one |\n\n## Contracts\n\n| Part | Owner | Consumers | Where defined |\n|---|---|---|---|\n`
const LEDGER = [{ id: 'A', text: 'x', decisions: ['D1'], tasks: ['t-one'], status: 'approved' }]
const TASK = (ref) =>
  `---\ntitle: X\nstatus: todo\nrepo: api\nvalue: worth it\nfiles: [src/x.py]\nverify: pytest tests/test_x.py\ndepends_on: []\nowns: []\nuses: []\n---\n\n# X\n\n## Requirement\n\nBuild.\n\n## Acceptance conditions\n\n- a1: works [evidence: test:${ref}]\n\n## Files\n\n- src/x.py\n\n## Expected outcome\n\nx\n\n## Steps\n\n- go\n`
// A workbench root (code/api checkout) with docs/plans beside it; `files` seeds the checkout.
const epic = (ref, files = {}, { checkout = true } = {}) => {
  const wb = mkdtempSync(join(tmpdir(), 'vt-runner-'))
  const api = join(wb, 'code', 'api')
  if (checkout) {
    mkdirSync(api, { recursive: true })
    spawnSync('git', ['init', '-q', api])
    for (const [f, text] of Object.entries(files)) {
      mkdirSync(join(api, f, '..'), { recursive: true })
      writeFileSync(join(api, f), text)
    }
  }
  const d = join(wb, 'docs', 'plans', 'in-progress', 'alpha')
  mkdirSync(join(d, 'tasks'), { recursive: true })
  writeFileSync(join(d, 'README.md'), README)
  writeFileSync(join(d, 'design.md'), DESIGN)
  writeFileSync(join(d, 'approvals.json'), JSON.stringify(LEDGER))
  writeFileSync(join(d, 'tasks', 't-one.md'), TASK(ref))
  return d
}
const cli = (d) => spawnSync(process.execPath, [CLI, '--epic', d], { encoding: 'utf8', env: { ...process.env, WORKBENCH_ROOT: '' } })

test('unrunnable test ref fails the lint', () => {
  const t = cli(epic('src/x.test.tsx::a', { 'src/x.test.tsx': '' }))
  assert.equal(t.status, 1, t.stderr)
  assert.match(t.stderr, /ac: task t-one a1: no runner for src\/x\.test\.tsx; add a refRunners entry or use a command: ref/)

  const d = epic('legacy/test_x.rb::t', { 'legacy/test_x.rb': '' })
  const r = cli(d)
  assert.equal(r.status, 1, r.stderr)
  assert.match(r.stderr, /ac: task t-one a1: no runner for legacy\/test_x\.rb; add a refRunners entry or use a command: ref/)
})

test('runnable test ref lints ok', () => {
  const r = cli(epic('tests/test_x.py::test_a', { 'tests/test_x.py': '', 'pyproject.toml': '[project]\nname="x"\n' }))
  assert.equal(r.status, 0, r.stderr)
})

test('new test file is resolved from its path package markers', () => {
  assert.equal(cli(epic('pkg/tests/test_x.py::test_a', { 'pkg/pyproject.toml': '[project]\nname="x"\n' })).status, 0)
  const bad = cli(epic('pkg/spec/x_spec.rb::t', { 'pkg/pyproject.toml': '[project]\nname="x"\n' }))
  assert.equal(bad.status, 1, bad.stderr)
  assert.match(bad.stderr, /no runner for pkg\/spec\/x_spec\.rb/)
})

test('missing checkout only warns', () => {
  const d = epic('legacy/test_x.rb::t', {}, { checkout: false })
  const r = cli(d)
  assert.equal(r.status, 0, r.stderr)
  assert.doesNotMatch(r.stderr, /no runner for/)
  assert.equal(r.stderr.split('\n').filter((l) => l === 'warning: task t-one: repo checkout not found, test refs not checked').length, 1, r.stderr)
})

test('runner CLI failure other than exit 2 fails the lint', () => {
  const r = cli(epic('tests/test_x.py::a', { 'tests/test_x.py': '', 'pyproject.toml': '[project]\nname="x"\n', '.claude/workbench.json': '{ not json' }))
  assert.equal(r.status, 1, r.stderr)
  assert.match(r.stderr, /ac: task t-one a1: runner check failed for tests\/test_x\.py/)
})
