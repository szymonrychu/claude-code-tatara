// Refs and paths reaching verifier shell commands are quoted or validated.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const red = { command: 'pytest', output: 'FAILED tests/test_a.py::test_x' }
const verification = { command: 'pytest', passed: true, evidence: '3 passed' }
const okVerify = { head: 'abc', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [] }
const task = (extra = {}) => ({
  id: 'a', title: 'task a', repo: 'api', worktree: '/wt/epic-x-a', requirement: 'req', value: 'worth it',
  short: 'a', files: ['src/a.py'], verify: 'pytest tests/test_a.py', review: 'full', ...extra,
})
const agent = async (prompt, opts) => {
  const role = opts.label.split(':')[1]
  if (role === 'impl' || role === 'fix') return { taskId: 'a', complete: true, summary: 's', filesChanged: ['src/a.py'], branch: 'epic-x-a', tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red }, verification }
  if (role === 'verify') return okVerify
  if (role === 'review') return { clean: true, findings: [], filesRead: ['src/a.py'] }
  if (role === 'false-finding') return { verdicts: [] }
  if (role === 'triage') return { repeated: [] }
  if (role === 'land') return { landed: true, head: 'h', base: 'b', conflict: false, verification, notes: '' }
  if (role === 'audit') return { complete: true, missing: [] }
  throw new Error(`unexpected agent ${opts.label}`)
}
const run = (t, args = {}) => runWorkflow(SCRIPT, { args: { brief: BRIEF, name: 'epic-x', epic: 'epic-x', baseRef: 'epic-x', mainCheckout: '/repo', ...args, tasks: [t] }, agent })
const verifyPrompts = (r) => r.calls.filter((c) => c.opts.label.split(':')[1] === 'verify').map((c) => c.prompt)

test('non-sha-fork-point-is-ignored-and-logged', async () => {
  const evil = 'x; touch /tmp/pwned'
  const r = await run(task({ forkPoint: evil }))
  assert.equal(r.error, undefined)
  const all = r.calls.map((c) => c.prompt).join('\n')
  assert.ok(!all.includes(evil), 'the non-sha fork point never reaches a prompt')
  assert.ok(verifyPrompts(r).some((p) => p.includes("--base 'epic-x'")))
  assert.ok(JSON.stringify(r.logs || r).includes('forkPoint ignored: not a sha'))
})

test('sha-fork-point-and-base-ref-are-shell-quoted', async () => {
  const r = await run(task({ forkPoint: 'abc1234' }))
  assert.ok(verifyPrompts(r).some((p) => p.includes("--base 'abc1234'")))
  const r2 = await run(task(), { baseRef: 'main; id' })
  assert.ok(verifyPrompts(r2).some((p) => p.includes("--base 'main; id'")))
})

test('repo-dir-quotes-worktree-and-repo', async () => {
  const r = await run(task({ repo: 'a"b$(id)`x`' }))
  assert.equal(r.error, undefined)
  const p = r.calls.map((c) => c.prompt).join('\n')
  assert.ok(p.includes("if [ -d '/wt/epic-x-a/a\"b$(id)`x`' ]"), p)
  assert.ok(!p.includes('"/wt/epic-x-a/a'), 'no double-quoted worktree')
})
