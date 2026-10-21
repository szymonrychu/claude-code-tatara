// Orchestrator rulings read mid-run (D1, U1, remark 2.5): an accept ruling in
// <epic dir>/rulings.json, read by one haiku agent per wave boundary, releases the
// dependents of a verified escalated task; the task keeps its escalation for the record.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const RULINGS_FILE = '/repo/docs/plans/in-progress/epic-x/rulings.json'
const task = (id, extra = {}) => ({
  id, title: `task ${id}`, repo: 'api', worktree: `/wt/${id}`, requirement: `requirement for ${id}`,
  value: 'worth it', files: [`src/${id}.py`, `tests/test_${id}.py`], review: 'full', ...extra,
})
const red = { command: 'pytest', output: 'FAILED' }
const finding = (summary) => ({ severity: 'high', file: 'src/a.py', line: 1, summary, requirement: 'keeps notices' })
// A fresh finding every round, so the task ends verified on round-cap with open findings.
const endless = { review: (l) => ({ clean: false, findings: [finding(`bug ${l}`)] }) }
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

// reader(n, prompt, opts) answers the n-th rulings read (1-based).
function agentFor(behaviours, reader) {
  let reads = 0
  return async (prompt, opts) => {
    const [, role, id] = opts.label.split(':')
    if (role === 'rulings') return reader(++reads, prompt, opts)
    const root = id.replace(/#.*$/, '').replace(/^task-/, '').toUpperCase()
    const b = behaviours[root] || {}
    if (b.delay) await sleep(b.delay)
    if (role === 'impl' || role === 'fix') {
      if (b.dies) return null
      return {
        taskId: root, complete: true, summary: 'did it', filesChanged: ['src/a.py'], branch: `b-${root}`,
        verification: { command: 'pytest', passed: true, evidence: '3 passed' },
        tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red },
      }
    }
    if (role === 'review') return { clean: true, findings: [], filesRead: ['src/a.py'], ...(b.review ? b.review(opts.label) : {}) }
    if (role === 'verify') return { head: 'abc', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [] }
    // Every open finding is real, so triage never releases on its own.
    if (role === 'false-finding') return { verdicts: [{ index: 0, verdict: 'real', reason: 'unproven' }] }
    if (role === 'triage') return { repeated: [] }
    if (role === 'audit') return { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
}
const run = (tasks, behaviours, reader, extra = { rulingsFile: RULINGS_FILE }) =>
  runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks, ...extra }, agent: agentFor(behaviours, reader) })
const started = (r, id) => r.calls.some((c) => c.opts.label.split(':')[1] === 'impl' && c.opts.label.split(':')[2] === `task-${id.toLowerCase()}`)
const readerCalls = (r) => r.calls.filter((c) => c.opts.label.split(':')[1] === 'rulings')
const stopped = (r, id) => r.result.tasks.find((t) => t.id === id).stopped
const accept = (task, reason = 'finding is false: tail shows pass') => ({ task, accept: true, reason, at: '2026-10-18T10:00:00Z' })
const T1 = task('T1')
const dep = (id, on = ['T1']) => task(id, { dependsOn: on })

test('accept ruling releases dependents', async () => {
  const r = await run([T1, dep('T2')], { T1: endless }, () => ({ rulings: [accept('T1')] }))
  assert.equal(r.error, undefined)
  assert.ok(started(r, 'T2'), 'T2 started on the ruling')
  assert.notEqual(stopped(r, 'T2'), 'dependency-failed')
  const t1 = r.result.tasks.find((t) => t.id === 'T1')
  assert.equal(t1.verified, true)
  assert.equal(t1.processOnly, false)
  assert.equal(t1.triageRejected, false)
  assert.deepEqual(t1.ruling, { accept: true, reason: 'finding is false: tail shows pass' })
  assert.deepEqual(r.result.rulingsIgnored, [])
})

test('ruled task keeps escalation', async () => {
  const r = await run([T1, dep('T2')], { T1: endless }, () => ({ rulings: [accept('T1')] }))
  const e = r.result.escalated.find((x) => x.id === 'T1')
  assert.ok(e, 'T1 still escalated')
  assert.ok(['round-cap', 'no-progress'].includes(e.reason), e.reason)
  assert.ok(e.findings.length >= 1)
  assert.deepEqual(e.ruling, { accept: true, reason: 'finding is false: tail shows pass' })
  assert.equal(r.result.finished, false)
  assert.equal(r.result.approvals.length, 0)
})

test('one reader call per boundary', async () => {
  // Three tasks wait on T1: its settling is one boundary and one read.
  const tasks = [T1, dep('T2'), dep('T3'), dep('T4')]
  const r = await run(tasks, { T1: endless }, () => ({ rulings: [accept('T1')] }))
  assert.equal(readerCalls(r).length, 1)
  for (const id of ['T2', 'T3', 'T4']) assert.ok(started(r, id), `${id} started`)
  const call = readerCalls(r)[0]
  assert.equal(call.opts.model, 'haiku')
  assert.ok(call.prompt.includes(`cat '${RULINGS_FILE}'`), call.prompt)
})

test('idle boundary with no accept fails the dependents once, no spin', async () => {
  const r = await run([T1, dep('T2'), dep('T3')], { T1: endless }, () => ({ rulings: [] }))
  assert.equal(r.error, undefined)
  assert.equal(readerCalls(r).length, 1)
  assert.equal(stopped(r, 'T2'), 'dependency-failed')
  assert.equal(stopped(r, 'T3'), 'dependency-failed')
  assert.ok(!started(r, 'T2'))
  assert.equal(r.result.escalated.find((x) => x.id === 'T1').ruling, undefined)
})

test('a ruling written after launch is seen at the next boundary', async () => {
  // T1 settles first while T3 still runs: read 1 sees no ruling, T2 keeps waiting.
  // T3 settles with nothing left running: the idle read sees the new ruling and T2 starts.
  const tasks = [T1, dep('T2'), task('T3')]
  const r = await run(tasks, { T1: endless, T3: { delay: 15 } }, (n) => ({ rulings: n === 1 ? [] : [accept('T1')] }))
  assert.equal(r.error, undefined)
  assert.equal(readerCalls(r).length, 2)
  assert.ok(started(r, 'T2'), 'T2 started on the later ruling')
  assert.notEqual(stopped(r, 'T2'), 'dependency-failed')
})

test('applied rulings are kept and never re-applied', async () => {
  // T1 and T4 both escalate and both have a waiter; T1 is ruled at the first read,
  // T4 only at the second. The second read returns T1's ruling again: applied once.
  const tasks = [T1, dep('T2'), task('T4', { review: 'full' }), dep('T5', ['T4'])]
  const r = await run(tasks, { T1: endless, T4: { ...endless, delay: 15 } }, (n) => ({
    rulings: n === 1 ? [accept('T1')] : [accept('T1'), accept('T4', 'ok too')],
  }))
  assert.equal(r.error, undefined)
  assert.equal(readerCalls(r).length, 2)
  assert.ok(started(r, 'T2') && started(r, 'T5'))
  assert.equal(r.logs.filter((l) => l.startsWith('T1: ruling accept applied')).length, 1)
  assert.deepEqual(r.result.escalated.find((x) => x.id === 'T4').ruling, { accept: true, reason: 'ok too' })
  assert.deepEqual(r.result.rulingsIgnored, [])
})

test('ruling for unverified task is ignored', async () => {
  // T6's implementer dies (unverified); its dependent T7 fails at once. NOPE is no task.
  const tasks = [T1, dep('T2'), task('T6'), dep('T7', ['T6'])]
  const rulings = [accept('T6', 'please'), accept('NOPE', 'typo'), accept('T1')]
  const r = await run(tasks, { T1: endless, T6: { dies: true } }, () => ({ rulings }))
  assert.equal(r.error, undefined)
  assert.equal(stopped(r, 'T7'), 'dependency-failed')
  assert.ok(!started(r, 'T7'))
  assert.ok(started(r, 'T2'), 'the verified task ruling still applies')
  const ignored = r.result.rulingsIgnored
  assert.deepEqual(ignored.map((x) => x.task).sort(), ['NOPE', 'T6'])
  assert.ok(ignored.every((x) => x.accept === true && x.reason && x.why), JSON.stringify(ignored))
  assert.equal(r.result.escalated.find((x) => x.id === 'T6').ruling, undefined)
})

test('a reader throw releases nothing and the run continues', async () => {
  const r = await run([T1, dep('T2')], { T1: endless }, () => { throw new Error('reader boom') })
  assert.equal(r.error, undefined)
  assert.equal(stopped(r, 'T2'), 'dependency-failed')
  assert.equal(readerCalls(r).length, 1)
  assert.ok(r.logs.some((l) => l.includes('rulings') && l.includes('reader boom')), r.logs.join('\n'))
})

test('a bad reader result releases nothing and is logged', async () => {
  const r = await run([T1, dep('T2')], { T1: endless }, () => ({ rulings: null, error: 'not JSON' }))
  assert.equal(r.error, undefined)
  assert.equal(stopped(r, 'T2'), 'dependency-failed')
  assert.ok(r.logs.some((l) => l.includes('rulings') && l.includes('unusable')), r.logs.join('\n'))
})

test('a reject ruling attaches but releases nothing', async () => {
  const r = await run([T1, dep('T2')], { T1: endless }, () => ({ rulings: [{ task: 'T1', accept: false, reason: 'real bug', at: 'x' }] }))
  assert.equal(stopped(r, 'T2'), 'dependency-failed')
  assert.deepEqual(r.result.escalated.find((x) => x.id === 'T1').ruling, { accept: false, reason: 'real bug' })
})

test('no rulings file no reader', async () => {
  const r = await run([T1, dep('T2')], { T1: endless }, () => ({ rulings: [accept('T1')] }), {})
  assert.equal(r.error, undefined)
  assert.equal(readerCalls(r).length, 0)
  assert.equal(stopped(r, 'T2'), 'dependency-failed')
  assert.equal('rulingsIgnored' in r.result, false)
  assert.equal(r.result.escalated.find((x) => x.id === 'T1').ruling, undefined)
})

test('rulingsFile must be the absolute path of rulings.json', async () => {
  for (const bad of ['rulings.json', '/repo/epic/other.json', 42]) {
    const r = await run([T1], {}, () => ({ rulings: [] }), { rulingsFile: bad })
    assert.match(String(r.error && r.error.message), /rulingsFile/)
    assert.equal(r.calls.length, 0)
  }
})

test('ruled-task-lands-before-dependents', async () => {
  // An epic run that lands: t1 escalates verified, an accept ruling releases it mid-run,
  // and it lands on epic-x before t2 starts; t2 then merges epic-x, not t1's branch.
  const etask = (id, extra = {}) => task(id, { short: id, worktree: `/wt/epic-x-${id}`, ...extra })
  const events = []
  const inner = agentFor({ T1: endless }, () => ({ rulings: [accept('t1')] }))
  const agent = async (prompt, opts) => {
    const [, role, id] = opts.label.split(':')
    events.push(`${role}-start:${id}`)
    if (role === 'land') {
      await sleep(10)
      events.push(`land-end:${id}`)
      return { landed: true, head: `land-${id}`, conflict: false, verification: { command: 'pytest', passed: true, evidence: '3 passed' }, notes: '' }
    }
    return inner(prompt, opts)
  }
  const args = { brief: BRIEF, name: 'epic-x', epic: 'epic-x', baseRef: 'epic-x', mainCheckout: '/repo', rulingsFile: RULINGS_FILE, tasks: [etask('t1'), etask('t2', { dependsOn: ['t1'] })] }
  const r = await runWorkflow(SCRIPT, { args, agent })
  assert.equal(r.error, undefined)
  const landT1 = events.indexOf('land-end:t1')
  assert.ok(events.indexOf('rulings-start:run#1') < events.indexOf('land-start:t1'), events.join(' '))
  assert.ok(landT1 >= 0 && landT1 < events.indexOf('impl-start:t2'), events.join(' '))
  assert.ok(r.result.landed.some((x) => x.id === 't1' && x.head === 'land-t1'), JSON.stringify(r.result.landed))
  assert.deepEqual(r.result.escalated.find((x) => x.id === 't1').ruling, { accept: true, reason: 'finding is false: tail shows pass' })
  const p = r.calls.find((c) => c.opts.label === 'epic-x:impl:t2').prompt
  assert.ok(p.includes('git merge --no-edit epic-x`'), p)
  assert.ok(!p.includes('git merge --no-edit b-T1'), p)
})
