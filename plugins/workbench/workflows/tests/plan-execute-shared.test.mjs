// Shared implementation parts: ownership, dependency queueing, and the
// cross-task duplication check. Derived from a past run
// where parallel tasks split by card each built their own reader
// for the same rule ("untap during each other player's untap step", "can't have
// <kind> counters"), in different ways, because no task owned the mechanic.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const IMPLEMENTER_MD = readFileSync(fileURLToPath(new URL('../../agents/implementer.md', import.meta.url)), 'utf8')
const CHECKLIST_MD = readFileSync(fileURLToPath(new URL('../../skills/start-review/references/review-checklist.md', import.meta.url)), 'utf8')
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }

const task = (id, extra = {}) => ({
  id,
  title: `task ${id}`,
  repo: 'api',
  worktree: `/wt/${id}`,
  requirement: `requirement for ${id}`,
  value: 'worth it',
  files: [`src/${id}-a.py`, `src/${id}-b.py`, `tests/test_${id}.py`],
  review: 'full', // the review loop under test; tier rules live in plan-execute-tier
  ...extra,
})

const deliverable = (id, extra = {}) => ({
  taskId: id,
  complete: true,
  summary: 'did it',
  filesChanged: ['src/a.py'],
  branch: `b-${id}`,
  tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED tests/test_a.py::test_x' } },
  verification: { command: 'pytest tests/test_a.py', passed: true, evidence: '3 passed' },
  ...extra,
})

const okVerify = { head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [], diffstat: { files: 2, addedNonTest: 40, addedTest: 10 } }

const okMerge = { merged: true, conflict: false, head: 'def456', verification: { command: 'x', passed: true, evidence: 'ok' } }

const role = (c) => c.opts.label.split(':')[1]
const short = (c) => c.opts.label.split(':')[2].split('#')[0].split('+')[0]
const idx = (calls, r, s) => calls.findIndex((c) => role(c) === r && short(c) === s)
const lastIdx = (calls, r, s) => calls.map((c) => role(c) === r && short(c) === s).lastIndexOf(true)

// Fake agent: per-task overrides keyed by short label (task-t1 ...).
function fakeAgent({ impl = {}, review = {}, audit, verify } = {}) {
  return async (prompt, opts) => {
    const c = { opts }
    // let other queued work interleave, as real agents would
    await new Promise((r) => setTimeout(r, 1))
    const s = short(c)
    if (role(c) === 'impl' || role(c) === 'fix') return deliverable(s.replace('task-', '').toUpperCase(), (impl[s] || (() => ({})))(prompt))
    if (role(c) === 'review') {
      const round = Number(opts.label.split('#')[1])
      return { filesRead: ['src/a.py'], ...(review[s] ? review[s](round, prompt) : { clean: true, findings: [] }) }
    }
    if (role(c) === 'verify') return { ...okVerify, ...(verify ? verify(s, prompt) : {}) }
    if (role(c) === 'merge') return okMerge
    if (role(c) === 'audit') return audit ? audit(prompt) : { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
}
const run = (args, agent) => runWorkflow(SCRIPT, { args: { brief: BRIEF, ...args }, agent })
const finding = (summary) => ({ severity: 'high', file: 'src/a.py', summary, requirement: 'r' })

// ---------------------------------------------------------------- validation
test('a dependsOn naming an unknown task fails before any agent', async () => {
  const r = await run({ tasks: [task('T1', { dependsOn: ['T9'] })] }, fakeAgent())
  assert.match(String(r.error), /T1.*dependsOn.*T9/)
  assert.equal(r.calls.length, 0)
})

test('a dependency cycle fails before any agent', async () => {
  const r = await run({ tasks: [task('T1', { dependsOn: ['T2'] }), task('T2', { dependsOn: ['T1'] })] }, fakeAgent())
  assert.match(String(r.error), /cycle/)
  assert.equal(r.calls.length, 0)
})

test('a shared part owned by two tasks fails before any agent, naming both', async () => {
  const r = await run(
    { tasks: [task('T1', { owns: ['untap-in-others-untap-step'] }), task('T6', { owns: ['untap-in-others-untap-step'] })] },
    fakeAgent(),
  )
  assert.match(String(r.error), /untap-in-others-untap-step.*T1.*T6/)
  assert.equal(r.calls.length, 0)
})

test('using a part another task owns without depending on that task fails', async () => {
  const r = await run(
    { tasks: [task('T6', { owns: ['counter-prohibition'] }), task('T1', { uses: ['counter-prohibition'] })] },
    fakeAgent(),
  )
  assert.match(String(r.error), /T1 uses counter-prohibition.*T6.*dependsOn/)
  assert.equal(r.calls.length, 0)
})

test('a transitive dependency on the owner is enough', async () => {
  const r = await run(
    {
      tasks: [
        task('T0', { owns: ['p'] }),
        task('T1', { dependsOn: ['T0'] }),
        task('T2', { uses: ['p'], dependsOn: ['T1'] }),
      ],
    },
    fakeAgent(),
  )
  assert.equal(r.error, undefined)
})

test('owns, uses and dependsOn must be arrays of strings', async () => {
  for (const k of ['owns', 'uses', 'dependsOn']) {
    const r = await run({ tasks: [task('T1', { [k]: 'x' })] }, fakeAgent())
    assert.match(String(r.error), new RegExp(`T1.*${k}`))
  }
})

// ---------------------------------------------------------------- queueing
test('a dependent task starts only after its dependency is reviewed clean', async () => {
  const r = await run({ tasks: [task('T1', { owns: ['p'] }), task('T2', { uses: ['p'], dependsOn: ['T1'] })] }, fakeAgent())
  assert.equal(r.error, undefined)
  assert.ok(idx(r.calls, 'impl', 'task-t2') > lastIdx(r.calls, 'review', 'task-t1'))
  assert.equal(r.result.finished, true)
})

test('a dependent starts the moment its own dependency is done, not when the whole wave is', async () => {
  // T2 is slow (3 review rounds); T3 waits only on T1 and must not wait for T2.
  const r = await run(
    {
      tasks: [task('T1'), task('T2'), task('T3', { dependsOn: ['T1'] })],
    },
    fakeAgent({ review: { 'task-t2': (round) => (round < 3 ? { clean: false, findings: [finding(`issue ${round}`)] } : { clean: true, findings: [] }) } }),
  )
  assert.equal(r.error, undefined)
  assert.ok(idx(r.calls, 'impl', 'task-t3') < lastIdx(r.calls, 'review', 'task-t2'))
})

test('a failed dependency stops its dependents; they are escalated, never silently dropped', async () => {
  const r = await run(
    { tasks: [task('T1'), task('T2', { dependsOn: ['T1'] }), task('T3', { dependsOn: ['T2'] })] },
    fakeAgent({ review: { 'task-t1': (round) => ({ clean: false, findings: [finding(`distinct issue ${round} ${'x'.repeat(round)}`)] }) } }),
  )
  assert.equal(r.error, undefined)
  assert.equal(idx(r.calls, 'impl', 'task-t2'), -1)
  assert.equal(idx(r.calls, 'impl', 'task-t3'), -1)
  const esc = Object.fromEntries(r.result.escalated.map((e) => [e.id, e]))
  assert.equal(esc.T2.reason, 'dependency-failed')
  assert.deepEqual(esc.T2.waitingOn, ['T1'])
  assert.equal(esc.T3.reason, 'dependency-failed')
  assert.equal(r.result.finished, false)
})

test('a dependent in the same repo is told to merge its dependency branches first', async () => {
  const r = await run(
    { tasks: [task('T1'), task('T2', { dependsOn: ['T1'] }), task('T3', { repo: 'web', dependsOn: ['T1'] })] },
    fakeAgent(),
  )
  const p2 = r.calls[idx(r.calls, 'impl', 'task-t2')].prompt
  assert.match(p2, /git merge --no-edit b-T1/)
  const p3 = r.calls[idx(r.calls, 'impl', 'task-t3')].prompt
  assert.doesNotMatch(p3, /git merge --no-edit b-T1/)
  assert.match(p3, /T1/)
})

// ---------------------------------------------------------------- ownership in prompts
test('implementers and reviewers see who owns each shared part, and not to rebuild it', async () => {
  const r = await run(
    {
      tasks: [
        task('T6', { owns: ['counter-prohibition'] }),
        task('T1', { owns: ['group-anthem'], uses: ['counter-prohibition'], dependsOn: ['T6'] }),
      ],
    },
    fakeAgent(),
  )
  const impl = r.calls[idx(r.calls, 'impl', 'task-t1')].prompt
  assert.match(impl, /counter-prohibition: owned by T6/)
  assert.match(impl, /You own: group-anthem/)
  // The reuse rules are method: agents/implementer.md, which the impl call runs as.
  assert.equal(r.calls[idx(r.calls, 'impl', 'task-t1')].opts.agentType, 'workbench:implementer')
  assert.match(IMPLEMENTER_MD, /do not (re)?build/i)
  const rev = r.calls[idx(r.calls, 'review', 'task-t1')]
  assert.match(rev.prompt, /counter-prohibition: owned by T6/)
  // The reimplementation rule is method: the checklist agents/reviewer.md reads, which the review call runs as.
  assert.equal(rev.opts.agentType, 'workbench:reviewer')
  assert.match(CHECKLIST_MD, /reimplemented instead of reused/)
})

test('a run without shared parts carries no ownership section', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  assert.doesNotMatch(r.calls[0].prompt, /Shared parts in this run/)
})

test('an unplanned shared part one task builds is offered to tasks that start later', async () => {
  const r = await run(
    { tasks: [task('T1'), task('T2', { dependsOn: ['T1'] })] },
    fakeAgent({ impl: { 'task-t1': () => ({ provides: [{ name: 'quoted-grant-reader', where: 'src/grants.py:read_quoted' }] }) } }),
  )
  const p2 = r.calls[idx(r.calls, 'impl', 'task-t2')].prompt
  assert.match(p2, /quoted-grant-reader: built by T1 at src\/grants.py:read_quoted/)
  assert.deepEqual(r.result.provides, [{ taskId: 'T1', name: 'quoted-grant-reader', where: 'src/grants.py:read_quoted' }])
})

test('the deliverable schema offers provides and reimplemented, both optional', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent())
  const s = r.calls[0].opts.schema
  assert.ok(s.properties.provides)
  assert.ok(s.properties.reimplemented)
  assert.ok(!s.required.includes('provides'))
  assert.ok(!s.required.includes('reimplemented'))
})

// ---------------------------------------------------------------- duplication audit
test('the scope audit checks across tasks for the same part built twice', async () => {
  const r = await run({ tasks: [task('T1', { owns: ['p'] }), task('T2')] }, fakeAgent())
  const a = r.calls.find((c) => role(c) === 'audit')
  assert.ok(a.prompt.includes('Run the duplicate sweep across these task trees.'))
  assert.match(a.prompt, /p: owned by T1/)
  // the sweep's method is the scope-auditor agent's, not the prompt's
  assert.match(readFileSync(fileURLToPath(new URL('../../agents/scope-auditor.md', import.meta.url)), 'utf8'), /built more than once/i)
  assert.ok(a.opts.schema.properties.duplicates)
})

test('duplicates the audit finds go back to the orchestrator and the run is not finished', async () => {
  const dup = { part: 'untap-in-others-untap-step', taskIds: ['T1', 'T2'], evidence: 'two readers' }
  const r = await run(
    { tasks: [task('T1'), task('T2')] },
    fakeAgent({ audit: () => ({ complete: true, missing: [], duplicates: [dup] }) }),
  )
  assert.deepEqual(r.result.duplicates, [dup])
  assert.equal(r.result.finished, false)
})

test('duplicates from the first audit survive a remediation round; the re-check does not redo the sweep', async () => {
  const dup = { part: 'p', taskIds: ['T1', 'T2'], evidence: 'two readers' }
  let n = 0
  const r = await run(
    { tasks: [task('T1'), task('T2')] },
    fakeAgent({
      audit: () =>
        ++n === 1
          ? { complete: false, missing: [{ item: 'x', taskId: 'T1', evidence: 'e' }], duplicates: [dup] }
          : { complete: true, missing: [] },
    }),
  )
  const audits = r.calls.filter((c) => role(c) === 'audit')
  assert.equal(audits.length, 2)
  assert.ok(!audits[1].prompt.includes('Run the duplicate sweep'))
  assert.deepEqual(r.result.duplicates, [dup])
  assert.equal(r.result.finished, false)
})

test('a dependency-failed task is never remediated without its dependency; its escalation survives the audit', async () => {
  const r = await run(
    { tasks: [task('T1'), task('T2', { dependsOn: ['T1'] })] },
    fakeAgent({
      review: { 'task-t1': (round) => ({ clean: false, findings: [finding(`distinct issue ${round} ${'x'.repeat(round)}`)] }) },
      audit: () => ({ complete: false, missing: [{ item: 'T2 never ran', taskId: 'T2', evidence: 'NO RESULT' }] }),
    }),
  )
  assert.equal(r.error, undefined)
  assert.equal(r.calls.filter((c) => role(c) === 'impl' && short(c).startsWith('task-t2')).length, 0)
  const t2 = r.result.escalated.find((e) => e.id === 'T2')
  assert.equal(t2.reason, 'dependency-failed')
  assert.deepEqual(t2.waitingOn, ['T1'])
})

test('only parts in the task\'s own tree are offered for reuse; others are flagged as elsewhere', async () => {
  const r = await run(
    {
      tasks: [
        task('T1', { owns: ['p'] }),
        task('T2', { uses: ['p'], dependsOn: ['T1'] }),
        task('T3', { owns: ['q'] }),
      ],
    },
    fakeAgent(),
  )
  const p2 = r.calls[idx(r.calls, 'impl', 'task-t2')].prompt
  assert.match(p2, /In your tree[^]*- p: owned by T1/)
  assert.match(p2, /Not in your tree[^]*- q: owned by T3/)
  const p3 = r.calls[idx(r.calls, 'impl', 'task-t3')].prompt
  assert.match(p3, /Not in your tree[^]*- p: owned by T1/)
  assert.doesNotMatch(p3, /In your tree/)
})

test('a cross-repo dependency is not something to go and read outside the tree', async () => {
  const r = await run({ tasks: [task('T1'), task('T3', { repo: 'web', dependsOn: ['T1'] })] }, fakeAgent())
  const p3 = r.calls[idx(r.calls, 'impl', 'task-t3')].prompt
  assert.doesNotMatch(p3, /read it there/)
  assert.match(p3, /T1.*lands with the integration/)
})
