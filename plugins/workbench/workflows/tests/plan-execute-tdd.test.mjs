// The red-evidence TDD gate and the review contract of plan-execute.js. Round-1
// evidence: wroteTestFirst was a boolean nobody checked, and reviewers returned
// findings with no kind and no evidence, and stayed silent about what they skipped.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const IMPLEMENTER_MD = readFileSync(fileURLToPath(new URL('../../agents/implementer.md', import.meta.url)), 'utf8')
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

const RED = { command: 'pytest', output: 'FAILED tests/test_a.py::test_x' }

const deliverable = (id, tests) => ({
  taskId: id,
  complete: true,
  summary: 'did it',
  filesChanged: ['src/a.py'],
  branch: `b-${id}`,
  tests,
  verification: { command: 'pytest tests/test_a.py', passed: true, evidence: '3 passed' },
})

const okVerify = { head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [], diffstat: { files: 2, addedNonTest: 40, addedTest: 10 }, acs: [{ id: 'AC1', met: true, how: 'ok' }] }

// impl: tests for the implementer; fixes get red evidence unless fixTests says otherwise.
function fakeAgent({ implTests, fixTests, review, verify } = {}) {
  return async (prompt, opts) => {
    const [, role, rest] = opts.label.split(':')
    const id = rest.split(/[#+]/)[0]
    if (role === 'impl') return deliverable(id, implTests)
    if (role === 'fix') return deliverable(id, fixTests || { added: ['tests/test_a.py'], wroteTestFirst: true, red: RED })
    if (role === 'verify') return verify || okVerify
    if (role === 'review') {
      const round = Number(rest.split('#')[1])
      return { clean: true, findings: [], filesRead: ['src/a.py'], ...(review ? review(round, prompt) : {}) }
    }
    if (role === 'audit') return { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
}
const run = (args, agent) => runWorkflow(SCRIPT, { args: { brief: BRIEF, ...args }, agent })
const ofRole = (r, role) => r.calls.filter((c) => c.opts.label.split(':')[1] === role)

test('the deliverable schema offers tests.red without requiring it', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ implTests: { added: ['tests/test_a.py'], wroteTestFirst: true, red: RED } }))
  const s = ofRole(r, 'impl')[0].opts.schema.properties.tests
  assert.deepEqual(s.required, ['added', 'wroteTestFirst'])
  const red = s.properties.red
  assert.equal(red.type, 'object')
  assert.deepEqual(red.required, ['command', 'output'])
  assert.equal(red.properties.command.type, 'string')
  assert.equal(red.properties.output.type, 'string')
  assert.equal(red.description, 'the failing run before the implementation: the command and the real tail naming the failing test')
})

test('wroteTestFirst without red evidence sends the task to a fixer', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ implTests: { added: ['tests/test_a.py'], wroteTestFirst: true } }))
  assert.equal(r.error, undefined)
  const fix = ofRole(r, 'fix')
  assert.equal(fix.length, 1)
  assert.ok(fix[0].prompt.includes('No red evidence'))
  assert.ok(fix[0].prompt.includes('tests/test_a.py'))
  assert.ok(fix[0].prompt.includes('every behaviour change is written test-first and the red run is reported'))
  assert.equal(r.result.tasks[0].clean, true)
})

test('an empty red output counts as missing', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ implTests: { added: ['tests/test_a.py'], wroteTestFirst: true, red: { command: 'pytest', output: '  ' } } }),
  )
  assert.ok(ofRole(r, 'fix')[0].prompt.includes('No red evidence'))
})

test('red evidence present: clean with no fix', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ implTests: { added: ['tests/test_a.py'], wroteTestFirst: true, red: RED } }))
  assert.equal(ofRole(r, 'fix').length, 0)
  assert.equal(r.result.tasks[0].clean, true)
  assert.equal(r.result.finished, true)
})

test('a small task without red evidence is reviewed and fixed, not skipped', async () => {
  const r = await run(
    { tasks: [task('T1', { files: ['a.py', 'b.py'], review: undefined, ac: [{ id: 'AC1', text: 'it works', evidence: { kind: 'test', ref: 'x' } }] })] },
    fakeAgent({ implTests: { added: [], wroteTestFirst: true } }),
  )
  assert.equal(ofRole(r, 'fix').length, 1)
  assert.match(ofRole(r, 'fix')[0].prompt, /\(tests\) - No red evidence/)
})

test('wroteTestFirst false with a listed exception is clean', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ implTests: { added: [], wroteTestFirst: false, note: 'docs-only template edit' } }),
  )
  assert.equal(ofRole(r, 'fix').length, 0)
  assert.equal(r.result.tasks[0].clean, true)
})

test('wroteTestFirst false without an exception gets the revert recipe', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ implTests: { added: [], wroteTestFirst: false, note: 'ran out of time' } }),
  )
  const fix = ofRole(r, 'fix')
  assert.equal(fix.length, 1)
  const p = fix[0].prompt
  assert.ok(p.includes('TDD skipped'))
  assert.ok(p.includes('git show'))
  assert.ok(
    p.includes(
      'commit first, then for each changed non-test file: git show <merge-base>:<path> > <path>; run the test (must fail); git show HEAD:<path> > <path>; run again (must pass); paste both tails into tests.red and verification.evidence',
    ),
  )
  assert.ok(p.includes('evidence: ran out of time'))
  // guard-bash blocks a file-scoped checkout or restore, so the recipe must not use one
  assert.ok(!/git (checkout --|restore)/.test(p))
})

test('wroteTestFirst false with no note reports (no note)', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ implTests: { added: [], wroteTestFirst: false } }))
  assert.ok(ofRole(r, 'fix')[0].prompt.includes('evidence: (no note)'))
})

test('a fixer that still reports no red evidence is checked again', async () => {
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({
      implTests: { added: ['tests/test_a.py'], wroteTestFirst: true },
      fixTests: { added: ['tests/test_a.py'], wroteTestFirst: true },
    }),
  )
  // the same gate finding twice in a row escalates at once as gate-repeat; the
  // round after the clean review is gate-only, so the fixer saw it but no second reviewer ran
  assert.equal(r.result.tasks[0].stopped, 'gate-repeat')
  assert.equal(ofRole(r, 'review').length, 1)
  assert.equal(ofRole(r, 'fix').length, 1)
  assert.ok(ofRole(r, 'fix')[0].prompt.includes('No red evidence'))
  assert.equal(r.result.tasks[0].processOnly, true)
  assert.equal(r.result.processGaps[0].gate, 'no-red-evidence')
})

test('impl and fix agents are told red evidence is part of the deliverable', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ implTests: { added: ['tests/test_a.py'], wroteTestFirst: true } }))
  const s = 'Red evidence is part of the deliverable: tests.red carries the command and the failing tail from before the implementation.'
  // The rule is method: it lives in agents/implementer.md, which both calls run as.
  assert.ok(IMPLEMENTER_MD.includes(s))
  assert.equal(ofRole(r, 'impl')[0].opts.agentType, 'workbench:implementer')
  assert.equal(ofRole(r, 'fix')[0].opts.agentType, 'workbench:implementer')
})

// ---------------------------------------------------------------- review contract
test('the review schema requires kind and evidence and offers declined and cannotVerify', async () => {
  const r = await run({ tasks: [task('T1')] }, fakeAgent({ implTests: { added: ['tests/test_a.py'], wroteTestFirst: true, red: RED } }))
  const s = ofRole(r, 'review')[0].opts.schema
  const item = s.properties.findings.items
  assert.deepEqual(item.required, ['severity', 'kind', 'file', 'summary', 'requirement', 'evidence'])
  assert.equal(item.properties.kind.type, 'string')
  assert.deepEqual(item.properties.kind.enum, ['missing', 'extra', 'wrong', 'quality'])
  assert.equal(item.properties.evidence.type, 'string')
  assert.equal(item.properties.evidence.description, 'file:line or the command output that shows it')
  assert.ok(!s.required.includes('declined'))
  assert.ok(!s.required.includes('cannotVerify'))
  assert.equal(s.properties.declined.type, 'array')
  assert.deepEqual(s.properties.declined.items.required, ['what', 'why'])
  assert.equal(s.properties.declined.items.properties.what.type, 'string')
  assert.equal(s.properties.declined.items.properties.why.type, 'string')
  assert.equal(s.properties.cannotVerify.type, 'array')
  assert.equal(s.properties.cannotVerify.items.type, 'string')
})

test('declined and cannotVerify accumulate per task across rounds, de-duplicated, and reach the top level', async () => {
  const f = { severity: 'high', kind: 'wrong', file: 'src/a.py', summary: 'bug', requirement: 'r', evidence: 'src/a.py:3' }
  const r = await run(
    { tasks: [task('T1'), task('T2')] },
    fakeAgent({
      implTests: { added: ['tests/test_a.py'], wroteTestFirst: true, red: RED },
      review: (round, prompt) => {
        if (!prompt.includes('plan task T1')) return {}
        return round === 1
          ? { clean: false, findings: [f], declined: [{ what: 'perf', why: 'no benchmark' }], cannotVerify: ['live webhook'] }
          : { declined: [{ what: 'perf', why: 'no benchmark' }, { what: 'i18n', why: 'not in scope' }], cannotVerify: ['live webhook', 'prod db'] }
      },
    }),
  )
  assert.equal(r.error, undefined)
  const t1 = r.result.tasks.find((t) => t.id === 'T1')
  const t2 = r.result.tasks.find((t) => t.id === 'T2')
  assert.deepEqual(t1.declined, [{ what: 'perf', why: 'no benchmark' }, { what: 'i18n', why: 'not in scope' }])
  assert.deepEqual(t1.cannotVerify, ['live webhook', 'prod db'])
  assert.deepEqual(t2.declined, [])
  assert.deepEqual(t2.cannotVerify, [])
  assert.deepEqual(r.result.declined, [
    { taskId: 'T1', what: 'perf', why: 'no benchmark' },
    { taskId: 'T1', what: 'i18n', why: 'not in scope' },
  ])
  assert.deepEqual(r.result.cannotVerify, [
    { taskId: 'T1', item: 'live webhook' },
    { taskId: 'T1', item: 'prod db' },
  ])
})

test('declined and cannotVerify are arrays on the small-task and failure paths too', async () => {
  const r = await run(
    { tasks: [task('T1', { files: ['a.py', 'b.py'], review: undefined, ac: [{ id: 'AC1', text: 'it works', evidence: { kind: 'test', ref: 'x' } }] }), task('T2')] },
    async (prompt, opts) => {
      const [, role, rest] = opts.label.split(':')
      const id = rest.split(/[#+]/)[0]
      if (role === 'impl' && id.startsWith('task-t2')) return null
      if (role === 'impl') return deliverable(id, { added: ['tests/test_a.py'], wroteTestFirst: true, red: RED })
      if (role === 'verify') return okVerify
      if (role === 'audit') return { complete: true, missing: [] }
      throw new Error(`unexpected agent ${opts.label}`)
    },
  )
  assert.equal(r.error, undefined)
  for (const t of r.result.tasks) {
    assert.deepEqual(t.declined, [], `${t.id} declined`)
    assert.deepEqual(t.cannotVerify, [], `${t.id} cannotVerify`)
  }
  assert.deepEqual(r.result.declined, [])
  assert.deepEqual(r.result.cannotVerify, [])
})

test('a verifier revert proof clears the TDD finding', async () => {
  const proof = { ran: true, failedOnBase: true, passedOnHead: true, files: ['src/a.py'] }
  const r = await run(
    { tasks: [task('T1')] },
    fakeAgent({ implTests: { added: [], wroteTestFirst: false, note: 'ran out of time' }, verify: { ...okVerify, tdd: proof } }),
  )
  assert.equal(ofRole(r, 'fix').length, 0)
  assert.equal(r.result.tasks[0].clean, true)
})

test('a revert run that did not prove it leaves the TDD finding', async () => {
  for (const tdd of [{ ran: true, failedOnBase: false, passedOnHead: true }, { ran: true, failedOnBase: true, passedOnHead: false }, { ran: false }, null]) {
    const r = await run(
      { tasks: [task('T1')] },
      fakeAgent({ implTests: { added: [], wroteTestFirst: false, note: 'ran out of time' }, verify: { ...okVerify, tdd } }),
    )
    assert.ok(ofRole(r, 'fix')[0].prompt.includes('TDD skipped'), JSON.stringify(tdd))
  }
})
