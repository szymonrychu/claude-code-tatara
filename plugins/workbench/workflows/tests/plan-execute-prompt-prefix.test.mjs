// Prompt-cache ordering (design D6). The recorded probe verdict is `CACHE none`
// (design.md "## Cache probe result"): static-first ordering reads no more cache than
// task-first, so implPrompt and verifyPrompt keep their task-first order. This test pins
// that order; a later reorder to static-first is then a deliberate decision that must
// change this test together with a new probe result.
import assert from 'node:assert/strict'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const task = (id) => ({
  id, title: `task ${id}`, repo: 'api', worktree: `/wt/${id}`, requirement: `requirement for ${id}`,
  value: 'worth it', files: [`src/${id}.py`], review: 'full',
})
const deliverable = (id) => ({
  taskId: id, complete: true, summary: 's', filesChanged: ['src/a.py'], branch: `b-${id}`,
  tests: { added: ['t.py'], wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED' } },
  verification: { command: 'pytest', passed: true, evidence: '1 passed' },
})
const okVerify = { head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: '1 passed', debtMarkers: [], diffstat: { files: 1, addedNonTest: 5, addedTest: 5 }, acs: [] }
const agent = async (prompt, opts) => {
  const [, role, rest] = opts.label.split(':')
  if (role === 'impl' || role === 'fix') return deliverable(rest.split('#')[0])
  if (role === 'review') return { filesRead: ['src/a.py'], clean: true, findings: [] }
  if (role === 'verify') return okVerify
  if (role === 'merge') return { merged: true, conflict: false, head: 'def456', verification: { command: 'x', passed: true, evidence: 'ok' } }
  return {}
}

test('prompt-order-follows-probe-verdict', async () => {
  const r = await runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks: [task('T1'), task('T2')] }, agent })
  assert.equal(r.error, undefined)
  const first = (role, id) => r.calls.find((c) => c.opts.label.split(':')[1] === role && c.opts.label.includes(`task-${id.toLowerCase()}`))
  for (const id of ['T1', 'T2']) {
    const impl = first('impl', id).prompt
    assert.equal(impl.split('\n')[0], `Your worktree: /wt/${id}`)
    assert.ok(impl.split('\n').slice(0, 5).some((l) => l.includes(`Task ${id}:`)))
  }
  assert.notEqual(first('impl', 'T1').prompt.split('\n')[0], first('impl', 'T2').prompt.split('\n')[0])
  assert.ok(first('verify', 'T1').prompt.includes('/wt/T1'))
})
