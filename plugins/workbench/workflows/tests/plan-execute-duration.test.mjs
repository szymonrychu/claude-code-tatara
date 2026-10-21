// plan-execute reads no clock (the runtime forbids it); the task estimate is never read.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const task = (id, extra = {}) => ({ id, title: `task ${id}`, repo: 'api', worktree: `/wt/${id}`, requirement: `req ${id}`, value: 'worth it', files: [`src/${id}.py`], ...extra })
const agent = async (prompt, opts) => {
  await new Promise((r) => setTimeout(r, 40))
  const role = opts.label.split(':')[1]
  if (role === 'impl') {
    return { taskId: 'T1', complete: true, summary: 'did', filesChanged: ['src/a.py'], branch: 'b', tests: { added: ['t'], wroteTestFirst: true, red: { command: 'p', output: 'FAILED x' } }, verification: { command: 'p', passed: true, evidence: '3 passed' } }
  }
  if (role === 'verify') return { head: 'abc', clean: true, command: 'p', passed: true, evidence: '3 passed', debtMarkers: [] }
  if (role === 'audit') return { complete: true, missing: [] }
  return { filesRead: ['src/a.py'], clean: true, findings: [] }
}

test('a full run succeeds under the Date-forbidding harness and carries no durationMs', async () => {
  const r = await runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks: [task('T1', { estimate: 30 })] }, agent })
  assert.equal(r.error, undefined)
  const t = r.result.tasks.find((x) => x.id === 'T1')
  assert.ok(t)
  assert.ok(!('durationMs' in t))
})

test('the script source reads no clock', () => {
  const src = readFileSync(SCRIPT, 'utf8')
  assert.ok(!src.includes('Date.now'))
  assert.ok(!src.includes('new Date'))
})

test('no code path in plan-execute reads the task estimate', () => {
  assert.ok(!/estimate/i.test(readFileSync(SCRIPT, 'utf8')))
})
