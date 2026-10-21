// Continuation handoffs carry the read set, and the read gate and
// the read-only-tests rule share one path matcher (round 3 audit).
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const IMPLEMENTER_MD = readFileSync(fileURLToPath(new URL('../../agents/implementer.md', import.meta.url)), 'utf8')
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const HEADING = 'Already read by the previous agent - do not re-read these unless you need a range not listed:'

const T1 = {
  id: 'T1',
  title: 'task T1',
  repo: 'api',
  worktree: '/wt/T1',
  requirement: 'requirement for T1',
  value: 'worth it',
  files: ['src/a.py', 'src/b.py', 'tests/test_a.py'],
  review: 'full',
}

const deliverable = (extra = {}) => ({
  taskId: 'T1',
  complete: true,
  summary: 'did it',
  filesChanged: ['src/a.py'],
  branch: 'b-T1',
  tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED' } },
  verification: { command: 'pytest', passed: true, evidence: '3 passed' },
  ...extra,
})
const handoff = (n, readSet) => ({
  ...deliverable({ complete: false, status: 'handoff' }),
  handoff: {
    doneSoFar: `slice ${n}`,
    remaining: ['the rest'],
    nextStep: 'go on',
    testState: '1 failed',
    wipCommit: `abc${n}`,
    ...(readSet ? { readSet } : {}),
  },
})

// impl hands off once per entry of `handoffs` (each a readSet or undefined), then delivers
async function chain(handoffs) {
  let n = 0
  const agent = async (prompt, opts) => {
    const role = opts.label.split(':')[1]
    if (role === 'impl') return n < handoffs.length ? handoff(n + 1, handoffs[n++]) : deliverable()
    if (role === 'verify') return { head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: 'ok', debtMarkers: [] }
    if (role === 'review') return { clean: true, findings: [], filesRead: ['src/a.py'] }
    if (role === 'audit') return { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
  const r = await runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks: [T1] }, agent })
  return r.calls.filter((c) => c.opts.label.split(':')[1] === 'impl' || /\+\d$/.test(c.opts.label))
}

test('the schema has an optional readSet on the handoff', async () => {
  const calls = await chain([])
  const h = calls[0].opts.schema.properties.handoff
  assert.ok(!h.required.includes('readSet'))
  const rs = h.properties.readSet
  assert.equal(rs.type, 'array')
  assert.deepEqual(rs.items.required, ['path'])
  assert.deepEqual(Object.keys(rs.items.properties).sort(), ['lines', 'note', 'path'])
  // The handoff instruction naming readSet is in agents/implementer.md, the agent the call runs as.
  assert.equal(calls[0].opts.agentType, 'workbench:implementer')
  assert.match(IMPLEMENTER_MD, /readSet/)
})

test('a handoff readSet appears in the continuation prompt', async () => {
  const calls = await chain([[{ path: 'src/a.py', lines: '1-50', note: 'parser entry' }, { path: 'src/b.py', note: 'helpers' }]])
  assert.equal(calls.length, 2)
  assert.ok(calls[1].prompt.includes(HEADING))
  assert.ok(calls[1].prompt.includes('- src/a.py:1-50 - parser entry'))
  assert.ok(calls[1].prompt.includes('- src/b.py - helpers'))
  assert.ok(!calls[0].prompt.includes(HEADING))
})

test('chained handoffs accumulate the read set without duplicates', async () => {
  const calls = await chain([
    [{ path: 'src/a.py', lines: '1-50', note: 'parser entry' }],
    [{ path: 'src/a.py', lines: '1-50', note: 'parser entry again' }, { path: 'src/c.py', lines: '5-9', note: 'config' }],
  ])
  assert.equal(calls.length, 3)
  const p = calls[2].prompt
  assert.equal(p.split('- src/a.py:1-50 - ').length - 1, 1)
  assert.ok(p.includes('- src/a.py:1-50 - parser entry'))
  assert.ok(p.includes('- src/c.py:5-9 - config'))
})

test('no heading when the readSet is absent or empty', async () => {
  for (const hs of [[undefined], [[]]]) {
    const calls = await chain(hs)
    assert.equal(calls.length, 2)
    assert.ok(!calls[1].prompt.includes(HEADING))
  }
})

// ---------------------------------------------------------------- one path matcher
const PAIRS = [
  ['./a/b.py', 'a/b.py', true],
  ['a/b.py', 'x/a/b.py', true],
  ['x/a/b.py', 'a/b.py', true],
  ['./a/b.py', 'x/a/b.py', true],
  ['a/b.py', 'xa/b.py', false],
  ['a/b.py', 'a/c.py', false],
]

test('the read gate and the read-only-tests rule match paths identically', async () => {
  for (const [a, b, same] of PAIRS) {
    // read gate: the implementer changed `a`, the review read `b`
    let reviews = 0
    const gate = async (prompt, opts) => {
      const role = opts.label.split(':')[1]
      if (role === 'impl') return deliverable({ filesChanged: [a] })
      if (role === 'verify') return { head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: 'ok', debtMarkers: [] }
      if (role === 'review') { reviews += 1; return { clean: true, findings: [], filesRead: [b] } }
      if (role === 'audit') return { complete: true, missing: [] }
      throw new Error(`unexpected agent ${opts.label}`)
    }
    await runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks: [T1] }, agent: gate })
    assert.equal(reviews === 1, same, `read gate ${a} vs ${b}`)

    // read-only tests: a finding names `b` (a test file), the fix round changed test `a`
    const testA = a.replace('b.py', 'test_b.py')
    const testB = b.replace('b.py', 'test_b.py')
    let fixes = 0
    let rev = 0
    const ro = async (prompt, opts) => {
      const role = opts.label.split(':')[1]
      if (role === 'impl') return deliverable()
      if (role === 'fix') { fixes += 1; return deliverable({ tests: { added: [], wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED' } } }) }
      if (role === 'verify') {
        const n = Number(opts.label.split('#')[1])
        return n === 1
          ? { head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: 'ok', debtMarkers: [] }
          : { head: 'def456', clean: true, command: 'pytest', passed: true, evidence: 'ok', debtMarkers: [], changedSincePrevious: [{ file: testA, status: 'M' }] }
      }
      if (role === 'review') {
        rev += 1
        const f = { severity: 'high', kind: 'wrong', file: testB, summary: 'broken', requirement: 'it works', evidence: 'x' }
        return { clean: rev > 1, findings: rev === 1 ? [f] : [], filesRead: ['src/a.py'] }
      }
      if (role === 'audit') return { complete: true, missing: [] }
      throw new Error(`unexpected agent ${opts.label}`)
    }
    await runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks: [T1] }, agent: ro })
    assert.equal(fixes === 1, same, `read-only tests ${testA} vs ${testB}`)
  }
})

test('plan-execute.js defines the matcher once and no caller re-implements it', () => {
  const src = readFileSync(SCRIPT, 'utf8')
  assert.match(src, /const stripDot = /)
  assert.match(src, /function pathMatches\(/)
  // the two directions of the one suffix test, both inside pathMatches
  assert.equal((src.match(/endsWith\(`\//g) || []).length, 2)
  assert.equal((src.match(/replace\(\/\^\\\.\\\/\//g) || []).length, 1)
})
