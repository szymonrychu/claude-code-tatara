// Medium-only release (design D8): a verified, unblocked task whose every open finding is
// medium and carries no gate releases its dependents in this run. It still escalates for a
// ruling, its return entry carries mediumOnly: true, and the run is not finished. A high or
// critical finding, a gate finding, a blocked or an unverified task never releases this way.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const MAIN = '/repo'
const EPIC = { name: 'epic-x', epic: 'epic-x', baseRef: 'epic-x', mainCheckout: MAIN }

const task = (id, extra = {}) => ({
  id, title: `task ${id}`, repo: 'api', worktree: `/wt/${id}`, requirement: `requirement for ${id}`,
  value: 'worth it', short: id.toLowerCase(), files: [`src/${id}.py`, `tests/test_${id}.py`], verify: `pytest tests/test_${id}.py`,
  review: 'full', ...extra,
})
const red = { command: 'pytest', output: 'FAILED' }
const finding = (severity, summary, extra = {}) =>
  ({ severity, kind: 'wrong', file: 'src/a.py', line: 1, summary, requirement: 'keeps notices', evidence: 'e', ...extra })
// A fresh finding set every round, so the task ends on round-cap with these findings open.
const raises = (...make) => ({ review: (l) => ({ clean: false, findings: make.map((m) => m(l)) }) })
const medium = (l) => finding('medium', `nit ${l}`)
const okVerify = { head: 'abc', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [] }
const okLand = (id) => ({
  landed: true, head: `land-${id}`, conflict: false, notes: 'merged 1 commit(s)',
  verification: { command: `pytest tests/test_${id}.py`, passed: true, evidence: '3 passed' },
})

// behaviours: { [taskId]: { review(label), verify, triage(prompt) } }
function agentFor(behaviours, events) {
  return async (prompt, opts) => {
    const [, role, id] = opts.label.split(':')
    const root = id.replace(/[#+].*$/, '').replace(/^task-/, '').toUpperCase()
    const b = behaviours[root] || {}
    events.push(`${role}:${root}`)
    if (role === 'impl' || role === 'fix') {
      return {
        taskId: root, complete: true, summary: 'did it', filesChanged: ['src/a.py'], branch: `b-${root}`,
        verification: { command: 'pytest', passed: true, evidence: '3 passed' },
        tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red },
      }
    }
    if (role === 'review') return { clean: true, findings: [], filesRead: ['src/a.py'], ...(b.review ? b.review(opts.label) : {}) }
    if (role === 'verify') return b.verify || okVerify
    if (role === 'false-finding') {
      if (b.triage) return b.triage(prompt)
      return { verdicts: [0, 1, 2, 3].map((index) => ({ index, verdict: 'real', reason: 'shown in the diff' })) }
    }
    if (role === 'triage') return { repeated: [] }
    if (role === 'land') return okLand(root.toLowerCase())
    if (role === 'audit') return { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
}
const run = async (tasks, behaviours, args = {}) => {
  const events = []
  const r = await runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks, ...args }, agent: agentFor(behaviours, events) })
  return { ...r, events }
}
const started = (r, id) => r.calls.some((c) => c.opts.label.split(':')[1] === 'impl' && c.opts.label.split(':')[2].replace(/^task-/, '').toUpperCase() === id)
const entry = (r, id) => r.result.tasks.find((t) => t.id === id)
const T1 = task('T1')
const T2 = task('T2', { dependsOn: ['T1'] })

test('medium-only-dependency-releases-dependents', async () => {
  const r = await run([T1, T2], { T1: raises(medium, medium) })
  assert.equal(r.error, undefined)
  assert.ok(started(r, 'T2'), 'T2 started')
  const t1 = entry(r, 'T1')
  assert.equal(t1.verified, true)
  assert.equal(t1.clean, false)
  assert.equal(t1.mediumOnly, true)
  assert.notEqual(entry(r, 'T2').stopped, 'dependency-failed')
  assert.equal(entry(r, 'T2').mediumOnly, false)
})

test('medium-only-task-still-escalates-with-flag', async () => {
  const r = await run([T1, T2], { T1: raises(medium) }, { approvals: [{ id: 'A', text: 'item A', tasks: ['T1'] }] })
  const e = r.result.escalated.find((x) => x.id === 'T1')
  assert.ok(e, 'T1 escalated')
  assert.ok(['round-cap', 'no-progress'].includes(e.reason), e.reason)
  assert.ok(e.findings.length >= 1)
  assert.ok(e.findings.every((f) => f.severity === 'medium'))
  assert.equal(e.mediumOnly, true)
  assert.equal(r.result.approvals.find((a) => a.id === 'A').status, 'escalated')
  assert.equal(r.result.finished, false)
})

test('triage-rejected findings do not count as open: a rejected high beside a real medium releases', async () => {
  const triage = () => ({ verdicts: [{ index: 0, verdict: 'false', reason: 'not a defect' }, { index: 1, verdict: 'real', reason: 'seen' }] })
  const r = await run([T1, T2], { T1: { ...raises((l) => finding('high', `bug ${l}`), medium), triage } })
  assert.ok(started(r, 'T2'), 'T2 started')
  assert.equal(entry(r, 'T1').mediumOnly, true)
  assert.equal(entry(r, 'T1').triageRejected, false)
})

test('high-or-gate-finding-never-releases', async () => {
  // A high or critical finding beside a medium one blocks the release.
  for (const severity of ['high', 'critical']) {
    const r = await run([T1, T2], { T1: raises(medium, (l) => finding(severity, `bug ${l}`)) })
    assert.ok(!started(r, 'T2'), `${severity}: T2 not started`)
    assert.equal(entry(r, 'T2').stopped, 'dependency-failed')
    assert.equal(entry(r, 'T1').mediumOnly, false)
    assert.ok(r.result.escalated.some((e) => e.id === 'T1' && !e.mediumOnly))
  }
  // A medium finding that carries a gate blocks it too.
  const r = await run([T1, T2], { T1: raises((l) => finding('medium', `unmet ${l}`, { gate: 'ac-unmet' })) })
  assert.ok(!started(r, 'T2'), 'gate: T2 not started')
  assert.equal(entry(r, 'T2').stopped, 'dependency-failed')
  assert.equal(entry(r, 'T1').mediumOnly, false)
})

test('unverified-medium-only-never-releases', async () => {
  // An unverified task with medium findings does not release.
  const failing = { ...okVerify, passed: false, exit: 1, evidence: '1 failed' }
  const u = await run([T1, T2], { T1: { ...raises(medium), verify: failing } })
  assert.ok(!started(u, 'T2'), 'unverified: T2 not started')
  assert.equal(entry(u, 'T1').verified, false)
  assert.equal(entry(u, 'T1').mediumOnly, false)
  // Nor does a blocked one.
  const blocked = { review: (l) => ({ clean: false, findings: [medium(l)], blocked: { reason: 'needs a credential', whoCanClear: 'the user' } }) }
  const b = await run([T1, T2], { T1: blocked })
  assert.ok(!started(b, 'T2'), 'blocked: T2 not started')
  assert.equal(entry(b, 'T1').stopped, 'blocked')
  assert.equal(entry(b, 'T1').mediumOnly, false)
})

test('medium-only-task-lands-in-epic-run', async () => {
  const a = task('a', { worktree: '/wt/epic-x-a' })
  const b = task('b', { worktree: '/wt/epic-x-b', dependsOn: ['a'] })
  const r = await run([a, b], { A: raises(medium) }, EPIC)
  assert.equal(r.error, undefined)
  assert.deepEqual(r.result.landed.map((l) => l.id), ['a', 'b'])
  assert.ok(r.events.indexOf('land:A') < r.events.indexOf('impl:B'), 'a landed before b started')
  assert.equal(entry(r, 'a').mediumOnly, true)
  assert.ok(r.result.escalated.some((e) => e.id === 'a' && e.mediumOnly))
  assert.equal(r.result.finished, false)
})
