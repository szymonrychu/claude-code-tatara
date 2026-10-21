// Process-only results (design D19): a task whose final verification passed clean on
// its HEAD and whose only open findings are bookkeeping gates (no-red-evidence,
// tdd-skipped, review-shallow) releases its dependents; any other finding does not.
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
  review: 'full',
  ...extra,
})
const red = { command: 'pytest', output: 'FAILED' }
const okImpl = { tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red } }
const finding = (summary) => ({ severity: 'high', file: 'src/a.py', line: 1, summary, requirement: 'keeps notices' })

// behaviours: { [taskId]: { impl, review } } ; impl is the deliverable overrides
function agentFor(behaviours) {
  return async (prompt, opts) => {
    const [, role, id] = opts.label.split(':')
    const root = id.replace(/#.*$/, '').replace(/^task-/, '').toUpperCase()
    const b = behaviours[root] || {}
    if (role === 'impl' || role === 'fix') {
      return {
        taskId: root, complete: true, summary: 'did it', filesChanged: ['src/a.py'], branch: `b-${root}`,
        verification: { command: 'pytest', passed: true, evidence: '3 passed' },
        ...okImpl, ...(b.impl || {}),
      }
    }
    if (role === 'review') return { clean: true, findings: [], filesRead: ['src/a.py'], ...(b.review ? b.review(opts.label) : {}) }
    if (role === 'verify') return { head: 'abc', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [] }
    if (role === 'triage') return { repeated: [] }
    if (role === 'audit') return { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
}
const run = (tasks, behaviours, args = {}) => runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks, ...args }, agent: agentFor(behaviours) })
const started = (r, id) => r.calls.some((c) => c.opts.label.split(':')[1] === 'impl' && c.opts.label.split(':')[2] === `task-${id.toLowerCase()}`)
const T1 = task('T1')
const T2 = task('T2', { dependsOn: ['T1'] })

const noRed = { impl: { tests: { added: ['tests/test_a.py'], wroteTestFirst: true } } }
const tddSkipped = { impl: { tests: { added: [], wroteTestFirst: false, note: 'just because' } } }
const shallow = { review: () => ({ filesRead: [] }) }

for (const [gate, b] of [['no-red-evidence', noRed], ['tdd-skipped', tddSkipped]]) {
  test(`a ${gate}-only task releases its dependents`, async () => {
    const r = await run([T1, T2], { T1: b })
    assert.ok(started(r, 'T2'), 'T2 started')
    const t1 = r.result.tasks.find((t) => t.id === 'T1')
    assert.equal(t1.verified, true)
    assert.equal(t1.clean, false)
    assert.equal(t1.processOnly, true)
    assert.ok(t1.processGaps.every((g) => g.gate === gate))
    assert.ok(t1.processGaps.length >= 1)
    assert.ok(!r.result.escalated.some((e) => e.id === 'T1'))
    const t2 = r.result.tasks.find((t) => t.id === 'T2')
    assert.notEqual(t2.stopped, 'dependency-failed')
  })
}

test('a review-shallow task releases dependents but is escalated and the run is not finished', async () => {
  const r = await run([T1, T2], { T1: shallow, T2: shallow })
  assert.ok(started(r, 'T2'), 'T2 started')
  assert.deepEqual(r.result.escalated.map((e) => [e.id, e.reason]), [['T1', 'review-shallow'], ['T2', 'review-shallow']])
  assert.equal(r.result.finished, false)
  const t1 = r.result.tasks.find((t) => t.id === 'T1')
  assert.equal(t1.verified, true)
  assert.equal(t1.processOnly, true)
})

test('only no-red-evidence and tdd-skipped processOnly tasks leave the run finished', async () => {
  for (const b of [noRed, tddSkipped]) assert.equal((await run([T1, T2], { T1: b })).result.finished, true)
})

test('a process finding mixed with a code finding does not release dependents', async () => {
  const r = await run([T1, T2], { T1: { ...noRed, review: () => ({ clean: false, findings: [finding('bug')] }) } })
  assert.ok(!started(r, 'T2'))
  assert.equal(r.result.tasks.find((t) => t.id === 'T2').stopped, 'dependency-failed')
  assert.notEqual(r.result.tasks.find((t) => t.id === 'T1').processOnly, true)
  assert.ok(r.result.escalated.some((e) => e.id === 'T1'))
})

test('processGaps entries carry taskId, what, where and gate', async () => {
  const r = await run([T1], { T1: noRed })
  const g = r.result.processGaps.filter((x) => x.gate === 'no-red-evidence')
  assert.equal(g.length, 1)
  assert.deepEqual(Object.keys(g[0]).sort(), ['gate', 'taskId', 'what', 'where'])
  assert.equal(g[0].taskId, 'T1')
  assert.match(g[0].what, /red evidence/i)
  assert.equal(g[0].where, 'tests/test_a.py')
})

test('an approval item is delivered for a processOnly task and escalated when a sibling task escalated', async () => {
  const r = await run([T1, task('T3')], { T1: noRed, T3: { review: () => ({ clean: false, findings: [finding('bug')] }) } }, {
    approvals: [
      { id: 'A', text: 'item A', tasks: ['T1'] },
      { id: 'B', text: 'item B', tasks: ['T1', 'T3'] },
    ],
  })
  const st = Object.fromEntries(r.result.approvals.map((a) => [a.id, a.status]))
  assert.equal(st.A, 'delivered')
  assert.equal(st.B, 'escalated')
})
