// A throwing agent() call ends its own task, never the run (D14, remark 2.7).
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const CAP = 'TelemetrySafeError: agent({schema}): StructuredOutput retry cap (5) exceeded'

const task = (id, extra = {}) => ({
  id, title: `task ${id}`, repo: 'api', worktree: `/wt/${id}`, requirement: `req ${id}`, value: 'worth it',
  files: [`src/${id}-a.py`, `tests/test_${id}.py`], verify: `pytest tests/test_${id}.py`, ...extra,
})
const idOf = (short) => short.replace('task-', '').replace(/^t(\d+)/, 'T$1')
const deliverable = (id) => ({
  taskId: id, complete: true, summary: 'did it', filesChanged: ['src/a.py'], branch: `b-${id}`,
  tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED' } },
  verification: { command: 'pytest', passed: true, evidence: '3 passed' },
})
const okVerify = { head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [] }

// throwOn(role, short) -> Error|undefined
function fakeAgent({ throwOn = () => {}, audit = () => ({ complete: true, missing: [] }), review = { clean: true, findings: [], filesRead: ['src/a.py'] } } = {}) {
  return async (prompt, opts) => {
    const [, role, rest] = opts.label.split(':')
    const short = (rest || '').split(/[#+]/)[0]
    const e = throwOn(role, short)
    if (e) throw e
    if (role === 'impl' || role === 'fix') return deliverable(idOf(short))
    if (role === 'verify') return okVerify
    if (role === 'review') return review
    if (role === 'audit') return audit(short)
    throw new Error(`unexpected agent ${opts.label}`)
  }
}
const run = (tasks, agent, extra = {}) => runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks, ...extra }, agent })
const stopped = (r, id) => r.result.tasks.find((t) => t.id === id)

test('retry-cap throw ends only that task as agent-output-invalid', async () => {
  const r = await run([task('T1'), task('T2')], fakeAgent({ throwOn: (role, s) => (role === 'impl' && s === 'task-t1' ? new Error(CAP) : null) }))
  assert.equal(r.error, undefined)
  assert.equal(stopped(r, 'T1').stopped, 'agent-output-invalid')
  assert.match(stopped(r, 'T1').agentError, /StructuredOutput retry cap/)
  assert.ok(stopped(r, 'T1').agentError.length <= 300)
  assert.equal(stopped(r, 'T2').clean, true)
  assert.deepEqual(r.result.escalated.map((e) => [e.id, e.reason]), [['T1', 'agent-output-invalid']])
})

test('agentError is capped at 300 chars', async () => {
  const r = await run([task('T1')], fakeAgent({ throwOn: (role) => (role === 'impl' ? new Error(CAP + ' ' + 'x'.repeat(900)) : null) }))
  assert.equal(stopped(r, 'T1').agentError.length, 300)
})

for (const [role, reason] of [['impl', 'impl-agent-died'], ['verify', 'verify-agent-died'], ['review', 'review-agent-died']]) {
  test(`other throw in ${role} ends the task with ${reason}`, async () => {
    const r = await run([task('T1'), task('T2')], fakeAgent({ throwOn: (ro, s) => (ro === role && s === 'task-t1' ? new Error('boom') : null) }), { tier: 'full' })
    assert.equal(r.error, undefined)
    assert.equal(stopped(r, 'T1').stopped, reason)
    assert.ok(r.result.escalated.some((e) => e.id === 'T1' && e.reason === reason))
    assert.equal(stopped(r, 'T2').clean, true)
  })
}

test('fix throw ends the task with fix-agent-died', async () => {
  const review = { clean: false, findings: [{ severity: 'high', kind: 'wrong', file: 'src/a.py', summary: 's', requirement: 'r', evidence: 'e' }], filesRead: ['src/a.py'] }
  const r = await run([task('T1')], fakeAgent({ review, throwOn: (role) => (role === 'fix' ? new Error('boom') : null) }), { tier: 'full' })
  assert.equal(r.error, undefined)
  assert.equal(stopped(r, 'T1').stopped, 'fix-agent-died')
})

test('dependent of an invalid-output task takes the dependency-failed path', async () => {
  const r = await run([task('T1'), task('T2', { dependsOn: ['T1'] })], fakeAgent({ throwOn: (role, s) => (role === 'impl' && s === 'task-t1' ? new Error(CAP) : null) }))
  assert.equal(stopped(r, 'T2').stopped, 'dependency-failed')
})

test('an audit throw is recorded in auditError and the run returns', async () => {
  const r = await run([task('T1')], fakeAgent({ throwOn: (role) => (role === 'audit' ? new Error('audit boom') : null) }), { audit: 'run' })
  assert.equal(r.error, undefined)
  assert.match(r.result.auditError, /audit boom/)
})

test('a triage throw keeps the safe fallback and does not end the task', async () => {
  const r = await run([task('T1')], fakeAgent({ throwOn: (role) => (role === 'triage' ? new Error('t') : null) }))
  assert.equal(r.error, undefined)
})

const gap = { taskId: 'T1', item: 'half done', evidence: 'src/T1-a.py is a stub' }

test('agent output invalid escalates one task', async () => {
  const r = await run([task('T1'), task('T2')], fakeAgent({ throwOn: (role, s) => (role === 'impl' && s === 'task-t1' ? new Error(CAP) : null) }))
  assert.equal(r.error, undefined)
  const t1 = stopped(r, 'T1')
  assert.equal(t1.stopped, 'agent-output-invalid')
  assert.match(t1.agentError, /StructuredOutput retry cap/)
  assert.equal(stopped(r, 'T2').clean, true)
  assert.ok(r.result.escalated.some((e) => e.id === 'T1' && e.reason === 'agent-output-invalid'))
})

test('reviewer throw escalates review agent died', async () => {
  const r = await run([task('T1')], fakeAgent({ throwOn: (role) => (role === 'review' ? new Error('boom') : null) }), { tier: 'full' })
  assert.equal(r.error, undefined)
  assert.ok(r.result.escalated.some((e) => e.id === 'T1' && e.reason === 'review-agent-died'))
})

test('agent died reasons are escalated', async () => {
  const impl = await run([task('T1')], fakeAgent({ throwOn: (role) => (role === 'impl' ? new Error('boom') : null) }))
  assert.ok(impl.result.escalated.some((e) => e.id === 'T1' && e.reason === 'impl-agent-died'))
  const review = { clean: false, findings: [{ severity: 'high', kind: 'wrong', file: 'src/a.py', summary: 's', requirement: 'r', evidence: 'e' }], filesRead: ['src/a.py'] }
  const fix = await run([task('T1')], fakeAgent({ review, throwOn: (role) => (role === 'fix' ? new Error('boom') : null) }), { tier: 'full' })
  assert.ok(fix.result.escalated.some((e) => e.id === 'T1' && e.reason === 'fix-agent-died'))
})

test('audit throw returns audit error', async () => {
  const first = await run([task('T1')], fakeAgent({ throwOn: (role) => (role === 'audit' ? new Error('audit boom') : null) }), { audit: 'run' })
  assert.equal(first.error, undefined)
  assert.match(first.result.auditError, /audit boom/)

  const remediation = await run([task('T1')], fakeAgent({
    audit: (short) => (short === 'scope' ? { complete: false, missing: [gap] } : { complete: true, missing: [] }),
    throwOn: (role, s) => (role === 'audit' && s === 'scope-r2' ? new Error('r2 boom') : null),
  }), { audit: 'run' })
  assert.equal(remediation.error, undefined)
  assert.match(remediation.result.auditError, /r2 boom/)

  const epic = await run([task('T1')], fakeAgent({ throwOn: (role) => (role === 'audit' ? new Error('epic boom') : null) }), { auditOnly: true, epicReadme: '/e/README.md' })
  assert.equal(epic.error, undefined)
  assert.match(epic.result.auditError, /epic boom/)
})
