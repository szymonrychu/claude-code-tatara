// D12 / remark 2.2: the haiku relay cannot invert a verdict. Pass, clean and AC results come from
// the script's fields (exit code) only; the agent's passed/met/note never override them.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const task = (id) => ({ id, title: id, repo: 'api', worktree: `/wt/${id}`, requirement: 'r', value: 'v', files: ['src/a.py'], review: 'full', ac: [{ id: 'AC1', text: 'no matches', evidence: { kind: 'command', ref: '! git grep foo' } }] })
const deliverable = (id) => ({ taskId: id, complete: true, summary: 's', filesChanged: ['src/a.py'], branch: `b-${id}`, tests: { added: ['t'], wroteTestFirst: true, red: { command: 'p', output: 'FAILED' } }, verification: { command: 'p', passed: true, evidence: 'ok' } })
const base = { head: 'abc', clean: true, command: 'c', evidence: 'e', debtMarkers: [], diffstat: { files: 1, addedNonTest: 1, addedTest: 1 } }

function agentWith(verifyResult) {
  return async (prompt, opts) => {
    const [, role, rest] = opts.label.split(':')
    if (role === 'impl' || role === 'fix') return deliverable(rest.split(/[#+]/)[0])
    if (role === 'verify') return verifyResult
    if (role === 'review') return { clean: true, findings: [], filesRead: ['src/a.py'] }
    if (role === 'audit') return { complete: true, missing: [] }
    throw new Error(opts.label)
  }
}
const go = (v) => runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks: [task('T1')] }, agent: agentWith(v) })
const gates = (r) => JSON.stringify([r.error && String(r.error), r.result])

test('verify prompt forbids gloss', async () => {
  const r = await go({ ...base, exit: 0, passed: true, acs: [{ id: 'AC1', met: true, exit: 0 }] })
  const p = r.calls.find((c) => c.opts.label.includes(':verify:')).prompt
  assert.ok(!/20 words/.test(p))
  assert.ok(/exit code/.test(p))
})

test('agent passed=true against script exit 1 is logged and the script wins', async () => {
  const r = await go({ ...base, exit: 1, passed: true, acs: [{ id: 'AC1', met: true, exit: 0 }] })
  assert.ok(r.logs.some((l) => /passed/.test(l) && /contradict/.test(l)), r.logs.join('\n'))
  assert.ok(gates(r).includes('verify-failed'))
})

test('a command AC is met by its exit alone: exit 1 is unmet whatever met says', async () => {
  const r = await go({ ...base, exit: 0, passed: true, acs: [{ id: 'AC1', met: true, exit: 1, how: 'note: fine really' }] })
  assert.ok(r.logs.some((l) => /AC1/.test(l) && /contradict/.test(l)), r.logs.join('\n'))
  assert.ok(gates(r).includes('ac-unmet'))
})

test('script fields win over relay gloss', async () => {
  const r = await go({ ...base, exit: 0, passed: false, acs: [{ id: 'AC1', met: true, exit: 0 }], note: 'looks failed to me' })
  assert.ok(!gates(r).includes('verify-failed'))
  assert.ok(!r.error && r.result, gates(r))
  assert.ok(!gates(r).includes('ac-unmet'), gates(r))
})
