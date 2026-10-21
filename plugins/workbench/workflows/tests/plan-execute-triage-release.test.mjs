// A verified task stopped on findings that haiku triage rejects as false releases its
// dependents (D1, remark 2.5); any real verdict or a triage throw keeps dependency-failed.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const task = (id, extra = {}) => ({
  id, title: `task ${id}`, repo: 'api', worktree: `/wt/${id}`, requirement: `requirement for ${id}`,
  value: 'worth it', files: [`src/${id}.py`, `tests/test_${id}.py`], review: 'full', ...extra,
})
const red = { command: 'pytest', output: 'FAILED' }
const finding = (summary) => ({ severity: 'high', file: 'src/a.py', line: 1, summary, requirement: 'keeps notices' })
// A fresh finding every round, so the task ends on round-cap with open findings.
const endless = { review: (l) => ({ clean: false, findings: [finding(`bug ${l}`), finding(`other ${l}`)] }) }

function agentFor(behaviours, triage) {
  return async (prompt, opts) => {
    const [, role, id] = opts.label.split(':')
    const root = id.replace(/#.*$/, '').replace(/^task-/, '').toUpperCase()
    const b = behaviours[root] || {}
    if (role === 'impl' || role === 'fix') {
      return {
        taskId: root, complete: true, summary: 'did it', filesChanged: ['src/a.py'], branch: `b-${root}`,
        verification: { command: 'pytest', passed: true, evidence: '3 passed' },
        tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red },
      }
    }
    if (role === 'review') return { clean: true, findings: [], filesRead: ['src/a.py'], ...(b.review ? b.review(opts.label) : {}) }
    if (role === 'verify') return { head: 'abc', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [] }
    if (role === 'false-finding') return triage(prompt, opts)
    if (role === 'triage') return { repeated: [] }
    if (role === 'audit') return { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
}
const run = (tasks, behaviours, triage) => runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks }, agent: agentFor(behaviours, triage) })
const started = (r, id) => r.calls.some((c) => c.opts.label.split(':')[1] === 'impl' && c.opts.label.split(':')[2] === `task-${id.toLowerCase()}`)
const T1 = task('T1')
const T2 = task('T2', { dependsOn: ['T1'] })
const allFalse = () => ({ verdicts: [{ index: 0, verdict: 'false', reason: 'tail shows pass' }, { index: 1, verdict: 'false', reason: 'not a defect' }] })

test('triage rejected findings release dependents', async () => {
  const r = await run([T1, T2], { T1: endless }, allFalse)
  assert.ok(started(r, 'T2'), 'T2 started')
  const t1 = r.result.tasks.find((t) => t.id === 'T1')
  assert.equal(t1.triageRejected, true)
  assert.equal(t1.verified, true)
  assert.notEqual(r.result.tasks.find((t) => t.id === 'T2').stopped, 'dependency-failed')
})

test('triage rejected task still escalates', async () => {
  const r = await run([T1, T2], { T1: endless }, allFalse)
  const e = r.result.escalated.find((x) => x.id === 'T1')
  assert.ok(['round-cap', 'no-progress'].includes(e.reason), e.reason)
  assert.ok(e.findings.length >= 2)
  assert.ok(e.findings.every((f) => f.verdict === 'false' && f.verdictReason))
  assert.equal(r.result.finished, false)
})

test('one real finding keeps dependents blocked', async () => {
  const mixed = () => ({ verdicts: [{ index: 0, verdict: 'false', reason: 'refuted' }, { index: 1, verdict: 'real', reason: 'unproven' }] })
  const r = await run([T1, T2], { T1: endless }, mixed)
  assert.ok(!started(r, 'T2'))
  assert.equal(r.result.tasks.find((t) => t.id === 'T2').stopped, 'dependency-failed')
  assert.notEqual(r.result.tasks.find((t) => t.id === 'T1').triageRejected, true)
  const e = r.result.escalated.find((x) => x.id === 'T1')
  assert.deepEqual(e.findings.slice(0, 2).map((f) => [f.verdict, f.verdictReason]), [['false', 'refuted'], ['real', 'unproven']])
})

test('a triage throw keeps today behaviour', async () => {
  const r = await run([T1, T2], { T1: endless }, () => { throw new Error('boom') })
  assert.ok(!started(r, 'T2'))
  assert.equal(r.result.tasks.find((t) => t.id === 'T2').stopped, 'dependency-failed')
  assert.equal(r.result.tasks.find((t) => t.id === 'T1').triageRejected, false)
})

test('an unusable triage result (no verdicts) keeps today behaviour', async () => {
  const r = await run([T1, T2], { T1: endless }, () => ({ verdicts: null, error: 'cannot run' }))
  assert.ok(!started(r, 'T2'))
})

test('the triage call is one haiku agent running false-finding', async () => {
  const r = await run([T1], { T1: endless }, allFalse)
  const calls = r.calls.filter((c) => c.prompt.includes('false-finding'))
  assert.equal(calls.length, 1)
  assert.equal(calls[0].opts.model, 'haiku')
})
