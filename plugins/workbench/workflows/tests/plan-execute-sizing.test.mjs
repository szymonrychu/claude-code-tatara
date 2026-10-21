// Pre-flight validation in plan-execute: task size cap, disjoint files per repo,
// and args.existing (parts already in the codebase).
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

const okVerify = { head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [] }

const role = (c) => c.opts.label.split(':')[1]
const short = (c) => c.opts.label.split(':')[2].split('#')[0].split('+')[0]

function fakeAgent({ review, audit, verify } = {}) {
  return async (prompt, opts) => {
    const c = { opts }
    await new Promise((r) => setTimeout(r, 1))
    const s = short(c)
    if (role(c) === 'impl' || role(c) === 'fix') return deliverable(s.replace('task-', '').toUpperCase())
    if (role(c) === 'review') {
      const round = Number(opts.label.split('#')[1])
      return { filesRead: ['src/a.py'], ...(review ? review(round) : { clean: true, findings: [] }) }
    }
    if (role(c) === 'verify') return { ...okVerify, ...(verify ? verify(prompt) : {}) }
    if (role(c) === 'audit') return audit ? audit(prompt) : { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
}
const run = (args, agent = fakeAgent()) => runWorkflow(SCRIPT, { args: { brief: BRIEF, ...args }, agent })
const files = (n) => Array.from({ length: n }, (_, i) => `src/f${i}.py`)
const finding = (summary) => ({ severity: 'high', file: 'src/a.py', summary, requirement: 'r' })

// ---------------------------------------------------------------- size cap
test('a task listing 9 files fails before any agent', async () => {
  const r = await run({ tasks: [task('T1', { files: files(9) })] })
  assert.match(String(r.error), /T1.*9 files.*max 8/)
  assert.match(String(r.error), /split it by test file, or set size: 'large' with a sizeReason/)
  assert.equal(r.calls.length, 0)
})

test('exactly 8 files passes', async () => {
  const r = await run({ tasks: [task('T1', { files: files(8) })] })
  assert.equal(r.error, undefined)
})

test("9 files with size 'large' and a sizeReason passes", async () => {
  const r = await run({ tasks: [task('T1', { files: files(9), size: 'large', sizeReason: 'one generated table' })] })
  assert.equal(r.error, undefined)
})

test("size 'large' without a sizeReason fails before any agent", async () => {
  for (const extra of [{}, { sizeReason: '' }, { sizeReason: 5 }]) {
    const r = await run({ tasks: [task('T1', { files: files(9), size: 'large', ...extra })] })
    assert.match(String(r.error), /T1.*size 'large' but has no sizeReason/)
    assert.match(String(r.error), /sizeReason/)
    assert.equal(r.calls.length, 0)
  }
})

// ---------------------------------------------------------------- disjoint files
test('two unordered tasks in one repo sharing a file fail, naming both and the file', async () => {
  const r = await run({ tasks: [task('T1', { files: ['src/x.py'] }), task('T2', { files: ['src/x.py', 'src/y.py'] })] })
  assert.match(String(r.error), /tasks T1 and T2 both list src\/x\.py; order them with dependsOn or give the file one owner/)
  assert.equal(r.calls.length, 0)
})

test('an overlap is allowed when one task directly dependsOn the other', async () => {
  const r = await run({ tasks: [task('T1', { files: ['src/x.py'] }), task('T2', { files: ['src/x.py'], dependsOn: ['T1'] })] })
  assert.equal(r.error, undefined)
})

test('an overlap is allowed through a transitive dependsOn', async () => {
  const r = await run({
    tasks: [
      task('T1', { files: ['src/x.py'] }),
      task('T2', { files: ['src/m.py'], dependsOn: ['T1'] }),
      task('T3', { files: ['src/x.py'], dependsOn: ['T2'] }),
    ],
  })
  assert.equal(r.error, undefined)
})

test('the same relative path in different repos is not an overlap', async () => {
  const r = await run({ tasks: [task('T1', { files: ['src/x.py'] }), task('T2', { repo: 'web', files: ['src/x.py'] })] })
  assert.equal(r.error, undefined)
})

// ---------------------------------------------------------------- args.existing
const EXISTING = [{ name: 'quoted-grant-reader', where: 'src/grants.py:read_quoted' }]
const PATTERN = /Already in the codebase[^]*- quoted-grant-reader: exists at src\/grants\.py:read_quoted/

test('args.existing appears in the impl, fix, review and audit prompts', async () => {
  let n = 0
  const r = await run(
    { tasks: [task('T1', { review: true })], existing: EXISTING },
    fakeAgent({ review: (round) => (round === 1 ? { clean: false, findings: [finding('one issue')] } : { clean: true, findings: [] }) }),
  )
  assert.equal(r.error, undefined)
  for (const rl of ['impl', 'fix', 'review', 'audit']) {
    const cs = r.calls.filter((c) => role(c) === rl)
    assert.ok(cs.length > 0, `no ${rl} call`)
    for (const c of cs) {
      n++
      assert.match(c.prompt, PATTERN, rl)
      assert.match(c.prompt, /Already in the codebase - reuse, do not rebuild:/)
    }
  }
  assert.ok(n >= 4)
  const audit = r.calls.find((c) => role(c) === 'audit')
  assert.match(audit.prompt, /A new implementation of any of these is a duplicates entry\./)
})

test('the existing group sits after the You own line and before In your tree', async () => {
  const r = await run({
    tasks: [task('T1', { owns: ['p'] }), task('T2', { dependsOn: ['T1'], files: ['src/T2.py'] })],
    existing: EXISTING,
  })
  const p = r.calls.find((c) => role(c) === 'impl' && short(c) === 'task-t1').prompt
  assert.ok(p.indexOf('You own') < p.indexOf('Already in the codebase'))
  const p2 = r.calls.find((c) => role(c) === 'impl' && short(c) === 'task-t2').prompt
  assert.ok(p2.indexOf('Already in the codebase') < p2.indexOf('In your tree'))
})

test('without existing parts the heading does not appear', async () => {
  for (const existing of [undefined, []]) {
    const r = await run({ tasks: [task('T1')], existing })
    assert.equal(r.error, undefined)
    for (const c of r.calls) assert.doesNotMatch(c.prompt, /Already in the codebase/)
    assert.doesNotMatch(r.calls.find((c) => role(c) === 'audit').prompt, /new implementation of any of these/)
  }
})

test('a malformed args.existing fails before any agent', async () => {
  for (const existing of ['x', [{ name: 'a' }], [{ name: 'a', where: 3 }], [null], {}]) {
    const r = await run({ tasks: [task('T1')], existing })
    assert.match(String(r.error), /args\.existing must be an array of \{name, where\} strings/)
    assert.equal(r.calls.length, 0)
  }
})

// ---------------------------------------------------------------- args.doNotBuild
const DNB = [{ name: 'own-retry-loop', reason: 'tenacity already provides retries' }]
const DNB_PATTERN = /Do not build - research found these unnecessary:\n- own-retry-loop: tenacity already provides retries/

test('args.doNotBuild appears in the impl, fix, review and first audit prompts', async () => {
  const r = await run(
    { tasks: [task('T1', { review: true })], doNotBuild: DNB },
    fakeAgent({ review: (round) => (round === 1 ? { clean: false, findings: [finding('one issue')] } : { clean: true, findings: [] }) }),
  )
  assert.equal(r.error, undefined)
  for (const rl of ['impl', 'fix', 'review', 'audit']) {
    const cs = r.calls.filter((c) => role(c) === rl)
    assert.ok(cs.length > 0, `no ${rl} call`)
    for (const c of cs) assert.match(c.prompt, DNB_PATTERN, rl)
  }
  const audit = r.calls.find((c) => role(c) === 'audit')
  assert.match(audit.prompt, /[Bb]uilding any of them is a `missing` finding on the task that built it/)
})

test('without doNotBuild the section does not appear', async () => {
  for (const doNotBuild of [undefined, []]) {
    const r = await run({ tasks: [task('T1')], doNotBuild })
    assert.equal(r.error, undefined)
    for (const c of r.calls) assert.doesNotMatch(c.prompt, /Do not build - research found/)
  }
})

test('a malformed args.doNotBuild fails before any agent', async () => {
  for (const doNotBuild of ['x', [{ name: 'a' }], [{ name: 'a', reason: 3 }], [null], {}]) {
    const r = await run({ tasks: [task('T1')], doNotBuild })
    assert.match(String(r.error), /plan-execute: args\.doNotBuild must be an array of \{name, reason\} strings/)
    assert.equal(r.calls.length, 0)
  }
})
