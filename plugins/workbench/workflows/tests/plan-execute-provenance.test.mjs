// Gate provenance (flow-speed D7): in a run without args.epic the verifier excludes the lines
// each merged same-repo dependency branch added; an epic run adds none.
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
  short: id,
  files: [`src/${id}.py`],
  review: 'full',
  ...extra,
})
const deliverable = (id) => ({
  taskId: id,
  complete: true,
  summary: 'did it',
  filesChanged: [`src/${id}.py`],
  branch: `b-${id}`,
  tests: { added: [`tests/test_${id}.py`], wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED tests/test_x.py::test_x' } },
  verification: { command: 'mise run test', passed: true, evidence: '3 passed' },
})
const okVerify = { head: 'abc1234', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [] }

async function run(args, tasks) {
  const fn = async (prompt, opts) => {
    const role = opts.label.split(':')[1]
    const id = opts.label.split(':')[2].split(/[#+]/)[0]
    if (role === 'impl' || role === 'fix') return deliverable(id)
    if (role === 'verify') return okVerify
    if (role === 'review') return { clean: true, findings: [], filesRead: [`src/${id}.py`] }
    if (role === 'land') return { landed: true, head: `land-${id}`, conflict: false, verification: { command: 'x', passed: true, evidence: 'verify: pass' }, notes: '' }
    if (role === 'audit') return { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
  return runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks, ...args }, agent: fn })
}
const verifyPrompts = (r, id) => r.calls.filter((c) => c.opts.label.split(':')[1] === 'verify' && c.opts.label.includes(`:${id}`)).map((c) => c.prompt)

test('non-epic-verify-excludes-dependency-branches', async () => {
  const r = await run({}, [task('a'), task('x'), task('b', { dependsOn: ['a', 'x'] }), task('c', { repo: 'web', dependsOn: ['a'] })])
  assert.equal(r.error, undefined)
  const [pb] = verifyPrompts(r, 'b')
  assert.ok(pb.includes("--exclude-ref 'b-a'"), pb)
  assert.ok(pb.includes("--exclude-ref 'b-x'"), pb)
  const [pa] = verifyPrompts(r, 'a')
  assert.ok(!pa.includes('--exclude-ref'), pa)
  const [pc] = verifyPrompts(r, 'c')
  assert.ok(!pc.includes('--exclude-ref'), 'a dependency in another repo is not merged into this tree')
})

test('epic-verify-passes-no-exclude-ref', async () => {
  const r = await run({ name: 'epic-x', epic: 'epic-x', baseRef: 'epic-x', mainCheckout: '/main' }, [task('a', { worktree: '/wt/epic-x-a' }), task('b', { worktree: '/wt/epic-x-b', dependsOn: ['a'] })])
  assert.equal(r.error, undefined)
  const [pb] = verifyPrompts(r, 'b')
  assert.ok(pb && !pb.includes('--exclude-ref'), pb)
})
