// Tests are read-only in a fix round: a modified, deleted or renamed existing test
// that no finding and no tests.added names is a high quality finding.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const SUMMARY = 'Tests changed in a fix round without a finding or tests.added naming them: '

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

const deliverable = (added) => ({
  taskId: 'T1',
  complete: true,
  summary: 'did it',
  filesChanged: ['src/a.py'],
  branch: 'b-T1',
  tests: { added, wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED' } },
  verification: { command: 'pytest', passed: true, evidence: '3 passed' },
})
const finding = (file) => ({ severity: 'high', kind: 'wrong', file, summary: 'broken', requirement: 'it works', evidence: 'x' })

// Round 1 review finds one issue in findingFile; the fixer reports fixAdded; the
// second verifier reports `changed`. Later reviews are clean.
async function scenario({ changed, fixAdded = [], findingFile = 'src/a.py' }) {
  let reviews = 0
  const agent = async (prompt, opts) => {
    const role = opts.label.split(':')[1]
    if (role === 'impl') return deliverable(['tests/test_a.py'])
    if (role === 'fix') return deliverable(fixAdded)
    if (role === 'verify') {
      const n = Number(opts.label.split('#')[1])
      return n === 1
        ? { head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: 'ok', debtMarkers: [] }
        : { head: 'def456', clean: true, command: 'pytest', passed: true, evidence: 'ok', debtMarkers: [], changedSincePrevious: changed }
    }
    if (role === 'review') {
      reviews += 1
      return { clean: reviews > 1, findings: reviews === 1 ? [finding(findingFile)] : [], filesRead: ['src/a.py'] }
    }
    if (role === 'audit') return { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
  const r = await runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks: [T1] }, agent })
  return { r, fixes: r.calls.filter((c) => c.opts.label.split(':')[1] === 'fix') }
}

test('a modified test named by nothing produces a high quality finding and a second fix', async () => {
  const { fixes } = await scenario({ changed: [{ file: 'tests/test_a.py', status: 'M' }] })
  assert.equal(fixes.length, 2)
  assert.ok(fixes[1].prompt.includes(SUMMARY + 'tests/test_a.py'))
  assert.ok(fixes[1].prompt.includes('M tests/test_a.py'))
  assert.ok(fixes[1].prompt.includes('git diff --name-status abc123..def456'))
  assert.ok(fixes[1].prompt.includes('[high/quality] tests/test_a.py'))
})

test('tests.added naming the file clears it', async () => {
  const { r, fixes } = await scenario({ changed: [{ file: 'tests/test_a.py', status: 'M' }], fixAdded: ['tests/test_a.py'] })
  assert.equal(fixes.length, 1)
  assert.equal(r.result.tasks[0].clean, true)
})

test('a finding naming the test file clears it', async () => {
  const { fixes } = await scenario({ changed: [{ file: 'tests/test_a.py', status: 'M' }], findingFile: 'tests/test_a.py' })
  assert.equal(fixes.length, 1)
})

test('path matching accepts a path that ends with the other', async () => {
  const { fixes } = await scenario({ changed: [{ file: 'tests/test_a.py', status: 'M' }], fixAdded: ['/wt/T1/api/tests/test_a.py'] })
  assert.equal(fixes.length, 1)
})

test('an added test never produces a finding', async () => {
  const { fixes } = await scenario({ changed: [{ file: 'tests/test_a.py', status: 'A' }] })
  assert.equal(fixes.length, 1)
})

test('a deleted test produces one', async () => {
  const { fixes } = await scenario({ changed: [{ file: 'tests/test_b.py', status: 'D' }] })
  assert.equal(fixes.length, 2)
  assert.ok(fixes[1].prompt.includes(SUMMARY + 'tests/test_b.py'))
  assert.ok(fixes[1].prompt.includes('D tests/test_b.py'))
})

test('a renamed test (R100) produces one', async () => {
  const { fixes } = await scenario({ changed: [{ file: 'tests/test_c.py', status: 'R100' }] })
  assert.equal(fixes.length, 2)
})

test('a modified non-test file never produces a finding', async () => {
  const { fixes } = await scenario({ changed: [{ file: 'src/a.py', status: 'M' }] })
  assert.equal(fixes.length, 1)
})
