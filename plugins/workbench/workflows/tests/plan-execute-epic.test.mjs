// args.epic naming: the run name, task shorts and worktree paths must all name the epic and task.
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
  worktree: `/wt/epic-x-${id}`,
  requirement: `requirement for ${id}`,
  value: 'worth it',
  short: id,
  files: [`src/${id}-a.py`, `tests/test_${id}.py`],
  ...extra,
})
const deliverable = (id) => ({
  taskId: id,
  complete: true,
  summary: 'did it',
  filesChanged: ['src/a.py'],
  branch: `epic-x-${id}`,
  tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED tests/test_a.py::test_x' } },
  verification: { command: 'pytest tests/test_a.py', passed: true, evidence: '3 passed' },
})
const agent = async (prompt, opts) => {
  const [, role, short] = opts.label.split(':')
  if (role === 'impl') return deliverable(short)
  if (role === 'verify') return { head: 'abc', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [] }
  if (role === 'review') return { clean: true, findings: [], filesRead: ['src/a.py'] }
  throw new Error(`unexpected agent ${opts.label}`)
}
const run = (args) => runWorkflow(SCRIPT, { args: { brief: BRIEF, ...args }, agent })
const rejects = async (args, re) => {
  const r = await run(args)
  assert.ok(r.error, 'expected a throw')
  assert.match(String(r.error.message || r.error), re)
}

const E = { name: 'epic-x', epic: 'epic-x' }

test('name must equal epic', async () => {
  await rejects({ name: 'other', epic: 'epic-x', tasks: [task('a')] }, /plan-execute: args\.name must equal args\.epic \(epic-x\)/)
})

test('epic must be a slug', async () => {
  await rejects({ name: 'Epic X', epic: 'Epic X', tasks: [task('a')] }, /slug/)
})

test('short must equal id, explicit or derived', async () => {
  await rejects({ ...E, tasks: [task('a', { short: 'nope' })] }, /task a.*short/)
  await rejects({ ...E, tasks: [task('a', { short: undefined })] }, /task a.*short/)
})

test('epic-worktree-must-end-in-epic-hyphen-id', async () => {
  await rejects({ ...E, tasks: [task('a', { worktree: '/wt/a' })] }, /plan-execute: task a worktree \/wt\/a must be epic-x-a/)
})

test('repo-subdir-worktree-passes', async () => {
  const r = await run({ ...E, tasks: [task('a', { worktree: '/wt/epic-x-a/api' })] })
  assert.equal(r.error, undefined)
  assert.equal(r.result.epic, 'epic-x')
  assert.ok(r.calls.some((c) => c.opts.label === 'epic-x:impl:a'))
})

test('without epic nothing changes', async () => {
  const r = await run({ name: 'pe', audit: 'off', tasks: [task('a', { short: undefined, worktree: '/wt/whatever' })] })
  assert.equal(r.error, undefined)
  assert.equal(r.result.epic, undefined)
  assert.ok(r.calls.some((c) => c.opts.label.startsWith('pe:impl:')))
})

test('epic-worktree-name-over-57-throws', async () => {
  const epic = 'e'.repeat(38)
  const id = 'i'.repeat(19)
  assert.equal(`${epic}-${id}`.length, 58)
  await rejects(
    { name: epic, epic, tasks: [task(id, { worktree: `/wt/${epic}-${id}` })] },
    /worktree name .* is 58 chars; the cap is 57/,
  )
})

test('epic-worktree-name-of-57-passes', async () => {
  const epic = 'e'.repeat(38)
  const id = 'i'.repeat(18)
  assert.equal(`${epic}-${id}`.length, 57)
  const r = await run({ name: epic, epic, tasks: [task(id, { worktree: `/wt/${epic}-${id}` })] })
  assert.equal(r.error, undefined)
})

test('epic-worktree-legacy-double-hyphen-accepted', async () => {
  const r = await run({ ...E, tasks: [task('a', { worktree: '/wt/epic-x--a' }), task('b', { worktree: '/wt/epic-x--b/api' })] })
  assert.equal(r.error, undefined)
})

test('legacy-worktree-name-of-58-chars-passes-and-59-throws', async () => {
  const epic = 'e'.repeat(38)
  const ok = 'i'.repeat(18)
  assert.equal(`${epic}--${ok}`.length, 58)
  const r = await run({ name: epic, epic, tasks: [task(ok, { worktree: `/wt/${epic}--${ok}` })] })
  assert.equal(r.error, undefined)
  const id = 'i'.repeat(19)
  await rejects({ name: epic, epic, tasks: [task(id, { worktree: `/wt/${epic}--${id}` })] }, /is 59 chars; the cap is 58/)
})
