// Review tiers see the task and skip reviews that add nothing (D9): the verify call carries
// the requirement, settled doc-only and test-only diffs skip whatever their size, and a
// light-tier fix to reviewer findings gets one scoped re-review before the task settles.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }

const task = (id, extra = {}) => ({
  id,
  title: `task ${id}`,
  repo: 'api',
  worktree: `/wt/${id}`,
  requirement: `requirement for ${id}`,
  value: 'worth it',
  files: ['docs/a.md'],
  ...extra,
})
const AC = (kind = 'doc-section') => [{ id: 'AC1', text: 'it is documented', evidence: { kind, ref: 'x' } }]
const deliverable = (id, filesChanged) => ({
  taskId: id,
  complete: true,
  summary: 'did it',
  filesChanged,
  branch: `b-${id}`,
  tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED tests/test_a.py::test_x' } },
  verification: { command: 'pytest tests/test_a.py', passed: true, evidence: '3 passed' },
})
const okVerify = {
  head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [],
  diffstat: { files: 9, addedNonTest: 900, addedTest: 30 }, acs: [{ id: 'AC1', met: true, how: 'ok' }], tierHint: null,
}
const role = (c) => c.opts.label.split(':')[1]
const finding = (summary, file = 'src/a.py') => ({ severity: 'high', file, summary, requirement: 'r' })

function fakeAgent({ changed = ['docs/a.md'], verify = () => ({}), review } = {}) {
  let nv = 0
  return async (prompt, opts) => {
    const r = role({ opts })
    const id = opts.label.split(':')[2].split('#')[0].replace('task-', '').toUpperCase()
    if (r === 'impl' || r === 'fix') return deliverable(id, changed)
    if (r === 'verify') return { ...okVerify, ...verify(++nv) }
    if (r === 'review') {
      const round = Number(opts.label.split('#')[1].split('-')[0])
      return { filesRead: changed, ...(review ? review(round) : { clean: true, findings: [] }) }
    }
    if (r === 'audit') return { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
}
const run = (t, agent) => runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks: [t] }, agent })
const calls = (r, name) => r.calls.filter((c) => role(c) === name)

test('first-verify-passes-the-requirement', async () => {
  const r = await run(
    task('T1', { review: 'light', requirement: "it's the requirement" }),
    fakeAgent({
      changed: ['src/a.py'],
      verify: (n) => (n === 1 ? {} : { head: 'def456', changedSincePrevious: [{ status: 'M', file: 'src/a.py' }] }),
      review: (round) => (round === 1 ? { clean: false, findings: [finding('x')] } : { clean: true, findings: [] }),
    }),
  )
  const verifies = calls(r, 'verify')
  assert.ok(verifies.length >= 2)
  assert.ok(verifies[0].prompt.includes(`--requirement 'it'\\''s the requirement'`), 'first verify')
  assert.doesNotMatch(verifies[1].prompt, /--requirement/)
})

test('doc-only-diff-with-acs-met-skips-review', async () => {
  const r = await run(task('T1', { ac: AC() }), fakeAgent({ changed: ['docs/a.md', 'README.md'] }))
  assert.equal(calls(r, 'review').length, 0)
})

test('test-only-diff-with-acs-met-skips-review', async () => {
  const r = await run(task('T1', { ac: AC('test') }), fakeAgent({ changed: ['tests/test_a.py', 'src/b.test.mjs'] }))
  assert.equal(calls(r, 'review').length, 0)
})

test('a large mixed doc-and-code diff stays light', async () => {
  const r = await run(task('T1', { ac: AC() }), fakeAgent({ changed: ['docs/a.md', 'src/a.py'] }))
  assert.equal(calls(r, 'review').length, 1)
})

test('risk-path-doc-diff-stays-full', async () => {
  for (const p of ['docs/auth.md', 'tests/test_auth.py']) {
    const r = await run(
      task('T1', { ac: AC() }),
      fakeAgent({ changed: [p], review: (round) => (round === 1 ? { clean: false, findings: [finding('x')] } : { clean: true, findings: [] }) }),
    )
    assert.equal(calls(r, 'review').length, 2, p)
    assert.equal(calls(r, 'review')[0].opts.effort, 'high', p)
  }
})

test('a doc-only diff with an unmet ac, a verifier finding or a judgement ac is not skipped', async () => {
  const cases = [
    { fake: { verify: () => ({ acs: [{ id: 'AC1', met: false, how: 'no' }] }) }, ac: AC() },
    { fake: { verify: () => ({ debtMarkers: [{ file: 'docs/a.md', line: 1, marker: 'TODO' }] }) }, ac: AC() },
    { fake: {}, ac: AC('judgement') },
  ]
  for (const c of cases) {
    const r = await run(task('T1', { ac: c.ac }), fakeAgent(c.fake))
    assert.ok(calls(r, 'review').length >= 1, JSON.stringify(c.fake))
  }
})

test('an explicit review value still wins over the doc-only skip, and the tierHint can raise it', async () => {
  let r = await run(task('T1', { ac: AC(), review: 'light' }), fakeAgent())
  assert.equal(calls(r, 'review').length, 1)
  r = await run(
    task('T1', { ac: AC() }),
    fakeAgent({ verify: () => ({ tierHint: 'full' }), review: (round) => (round === 1 ? { clean: false, findings: [finding('x')] } : { clean: true, findings: [] }) }),
  )
  assert.equal(calls(r, 'review').length, 2)
})

test('light-fix-to-reviewer-findings-gets-scoped-re-review', async () => {
  const r = await run(
    task('T1', { review: 'light' }),
    fakeAgent({
      changed: ['src/a.py'],
      verify: (n) => (n === 1 ? {} : { head: 'def456', changedSincePrevious: [{ status: 'M', file: 'src/a.py' }, { status: 'M', file: 'tests/test_a.py' }] }),
      review: (round) => (round === 1 ? { clean: false, findings: [finding('x')] } : { clean: true, findings: [] }),
    }),
  )
  const reviews = calls(r, 'review')
  assert.equal(reviews.length, 2)
  assert.equal(reviews[1].opts.effort, 'medium')
  const p = reviews[1].prompt
  const scope = p.slice(p.indexOf('Scoped re-review'), p.indexOf('Scoped re-review') + 400)
  assert.match(scope, /- src\/a\.py/)
  assert.doesNotMatch(scope, /tests\/test_a\.py/)
  assert.equal(r.result.tasks[0].clean, true)
})

test('light: findings of the scoped re-review go to one fixer and its verifier, no further review', async () => {
  const r = await run(
    task('T1', { review: 'light' }),
    fakeAgent({
      changed: ['src/a.py'],
      verify: (n) => (n === 1 ? {} : { head: `h${n}`, changedSincePrevious: [{ status: 'M', file: n === 2 ? 'src/a.py' : 'src/b.py' }] }),
      review: (round) => (round <= 2 ? { clean: false, findings: [finding(`issue ${round}`, round === 1 ? 'src/a.py' : 'src/b.py')], filesRead: ['src/a.py', 'src/b.py'] } : { clean: true, findings: [] }),
    }),
  )
  assert.equal(calls(r, 'review').length, 2)
  assert.equal(calls(r, 'fix').length, 2)
  assert.equal(calls(r, 'verify').length, 3)
  assert.equal(r.result.tasks[0].clean, true)
})

test('light: a fix that changed no file a reviewer finding named is not re-reviewed', async () => {
  const r = await run(
    task('T1', { review: 'light' }),
    fakeAgent({
      changed: ['src/a.py'],
      verify: (n) => (n === 1 ? {} : { changedSincePrevious: [] }),
      review: (round) => (round === 1 ? { clean: false, findings: [finding('x')] } : { clean: true, findings: [] }),
    }),
  )
  assert.equal(calls(r, 'review').length, 1)
})
