// Risk-tiered per-task review: skip < light < full < panel.
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
  files: [`src/${id}.py`, `tests/test_${id}.py`],
  ...extra,
})
const AC = (kind = 'test') => [{ id: 'AC1', text: 'it works', evidence: { kind, ref: 'x' } }]
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
  diffstat: { files: 2, addedNonTest: 40, addedTest: 30 }, acs: [{ id: 'AC1', met: true, how: 'ok' }], tierHint: null,
}
const role = (c) => c.opts.label.split(':')[1]
const finding = (summary) => ({ severity: 'high', file: 'src/a.py', summary, requirement: 'r' })

function fakeAgent({ changed = ['src/a.py'], verify = {}, review } = {}) {
  return async (prompt, opts) => {
    const r = role({ opts })
    const id = opts.label.split(':')[2].split('#')[0].replace('task-', '').toUpperCase()
    if (r === 'impl' || r === 'fix') return deliverable(id, changed)
    if (r === 'verify') return { ...okVerify, ...verify }
    if (r === 'review') {
      const round = Number(opts.label.split('#')[1])
      return { filesRead: ['src/a.py'], ...(review ? review(round) : { clean: true, findings: [] }) }
    }
    if (r === 'audit') return { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
}
const run = (t, agent) => runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks: [t] }, agent })
const calls = (r, name) => r.calls.filter((c) => role(c) === name)
const firstReviewFails = (round) => (round === 1 ? { clean: false, findings: [finding('x')] } : { clean: true, findings: [] })

test('explicit review values win: true is full, false is skip, strings pass through', async () => {
  let r = await run(task('T1', { review: false, ac: AC() }), fakeAgent({ changed: ['src/auth.py'] }))
  assert.equal(calls(r, 'review').length, 0)
  r = await run(task('T1', { review: true, ac: AC() }), fakeAgent({ review: firstReviewFails }))
  assert.equal(calls(r, 'review').length, 2)
  r = await run(task('T1', { review: 'skip', ac: AC() }), fakeAgent({ changed: ['src/auth.py'] }))
  assert.equal(calls(r, 'review').length, 0)
  r = await run(task('T1', { review: 'light', ac: AC() }), fakeAgent({ review: firstReviewFails }))
  assert.equal(calls(r, 'review').length, 1)
  r = await run(task('T1', { review: 'full', ac: AC() }), fakeAgent({ review: firstReviewFails }))
  assert.equal(calls(r, 'review').length, 2)
})

test('a risk path forces full; each regex term is covered', async () => {
  for (const p of ['src/auth.py', 'a/secret.py', 'x.sops.yaml', 'rbac.yaml', 'db/migration_1.sql', 'poetry.lock', 'mutex.go', 'thread_pool.py', 'concurrency.py', '.github/ci.yml', '.gitlab-ci.yml', 'hooks/pre.sh', 'permissions.py']) {
    const r = await run(task('T1', { ac: AC() }), fakeAgent({ changed: [p], review: firstReviewFails }))
    assert.equal(calls(r, 'review').length, 2, p)
    assert.equal(calls(r, 'review')[0].opts.effort, 'high', p)
  }
})

test('skip: clean verify, all ACs met with accepted evidence, small diff, no review dispatched', async () => {
  for (const kind of ['test', 'symbol', 'command', 'doc-section']) {
    const r = await run(task('T1', { ac: AC(kind) }), fakeAgent())
    assert.equal(r.error, undefined)
    assert.equal(calls(r, 'review').length, 0, kind)
  }
})

test('light when the diff is large, has many files, an AC is unmet or judged, or pre-findings exist', async () => {
  const cases = [
    { diffstat: { files: 2, addedNonTest: 151, addedTest: 0 } },
    { diffstat: { files: 5, addedNonTest: 10, addedTest: 0 } },
    { acs: [{ id: 'AC1', met: null, how: 'judgement' }] },
    { debtMarkers: [{ file: 'src/a.py', line: 3, marker: 'TODO' }] },
  ]
  for (const verify of cases) {
    const r = await run(task('T1', { ac: AC() }), fakeAgent({ verify }))
    assert.equal(calls(r, 'review').length, 1, JSON.stringify(verify))
  }
  const r = await run(task('T1', { ac: AC('judgement') }), fakeAgent())
  assert.equal(calls(r, 'review').length, 1)
})

test('a task without ac is at least light; a met judgement ac is at least light', async () => {
  let r = await run(task('T1'), fakeAgent())
  assert.equal(calls(r, 'review').length, 1, 'no ac')
  r = await run(task('T1', { ac: [] }), fakeAgent())
  assert.equal(calls(r, 'review').length, 1, 'empty ac')
  r = await run(task('T1', { ac: AC('judgement') }), fakeAgent({ verify: { acs: [{ id: 'AC1', met: true, how: 'ok' }] } }))
  assert.equal(calls(r, 'review').length, 1, 'met judgement ac')
})

test('boundaries 150 non-test lines and 4 files still skip', async () => {
  const r = await run(task('T1', { ac: AC() }), fakeAgent({ verify: { diffstat: { files: 4, addedNonTest: 150, addedTest: 99 } } }))
  assert.equal(calls(r, 'review').length, 0)
})

test('light: exactly one review, its findings go to one fixer and the verifier, no second review', async () => {
  const r = await run(task('T1', { ac: AC(), review: 'light' }), fakeAgent({ review: () => ({ clean: false, findings: [finding('x')] }) }))
  assert.equal(calls(r, 'review').length, 1)
  assert.equal(calls(r, 'fix').length, 1)
  assert.equal(calls(r, 'verify').length, 2)
  assert.equal(calls(r, 'review')[0].opts.effort, 'medium')
  assert.match(calls(r, 'fix')[0].prompt, /x/)
})

test('tierHint can raise the tier, never lower it', async () => {
  let r = await run(task('T1', { ac: AC() }), fakeAgent({ verify: { tierHint: 'light' }, review: firstReviewFails }))
  assert.equal(calls(r, 'review').length, 1)
  r = await run(task('T1', { ac: AC() }), fakeAgent({ verify: { tierHint: 'full' }, review: firstReviewFails }))
  assert.equal(calls(r, 'review').length, 2)
  r = await run(task('T1', { ac: AC(), review: 'full' }), fakeAgent({ verify: { tierHint: 'skip' }, review: firstReviewFails }))
  assert.equal(calls(r, 'review').length, 2)
  r = await run(task('T1', { ac: AC() }), fakeAgent({ changed: ['src/auth.py'], verify: { tierHint: 'light' }, review: firstReviewFails }))
  assert.equal(calls(r, 'review').length, 2)
  r = await run(task('T1', { ac: AC() }), fakeAgent({ verify: { tierHint: 'bogus' } }))
  assert.equal(calls(r, 'review').length, 0)
})

test('panel runs the full loop and sets panel: true on the task result', async () => {
  const r = await run(task('T1', { ac: AC(), review: 'panel' }), fakeAgent({ review: firstReviewFails }))
  assert.equal(calls(r, 'review').length, 2)
  assert.equal(calls(r, 'review')[0].opts.effort, 'high')
  assert.equal(JSON.stringify(r.result).includes('"panel":true'), true)
  const h = await run(task('T1', { ac: AC() }), fakeAgent({ verify: { tierHint: 'panel' } }))
  assert.equal(JSON.stringify(h.result).includes('"panel":true'), true)
  const f = await run(task('T1', { ac: AC(), review: 'full' }), fakeAgent())
  assert.equal(JSON.stringify(f.result).includes('"panel":true'), false)
})

test('every review and audit dispatch is sonnet, even for opus-implemented tasks', async () => {
  for (const review of ['light', 'full', 'panel']) {
    const r = await run(task('T1', { ac: AC(), review, model: 'opus' }), fakeAgent({ review: firstReviewFails }))
    for (const c of r.calls) {
      if (role(c) === 'review' || role(c) === 'audit') assert.equal(c.opts.model, 'sonnet', c.opts.label)
    }
    assert.equal(calls(r, 'impl')[0].opts.model, 'opus')
    for (const c of calls(r, 'audit')) assert.equal(c.opts.effort, 'high')
  }
})
