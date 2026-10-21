// args.overlapIgnore: shared files matching a glob never trip the run-level overlap rule.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'
import { cli, epic } from './overlap-epic-fixture.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const task = (id, files) => ({ id, title: `task ${id}`, repo: 'api', worktree: `/wt/${id}`, requirement: `req ${id}`, value: 'worth it', files })
const agent = async (prompt, opts) => {
  const [, role, short] = opts.label.split(':')
  if (role === 'impl') return { taskId: short, complete: true, summary: 'did', filesChanged: ['a'], branch: `b-${short}`, tests: { added: ['t'], wroteTestFirst: true, red: { command: 'x', output: 'FAILED' } }, verification: { command: 'x', passed: true, evidence: '1 passed' } }
  if (role === 'verify') return { head: 'abc', clean: true, command: 'x', passed: true, evidence: '1 passed', debtMarkers: [] }
  if (role === 'review') return { clean: true, findings: [], filesRead: ['a'] }
  throw new Error(`unexpected agent ${opts.label}`)
}
const run = (args) => runWorkflow(SCRIPT, { args: { brief: BRIEF, ...args }, agent })
const overlapMsg = (r) => r.error && /both list/.test(String(r.error.message || r.error))

test('a shared file matching overlapIgnore does not throw', async () => {
  const tasks = [task('a', ['docs/x/README.md', 'src/a.py']), task('b', ['docs/x/README.md', 'src/b.py'])]
  for (const glob of ['README.md', '**/README.md', 'docs/**', 'docs/x/*.md']) {
    const r = await run({ tasks, overlapIgnore: [glob] })
    assert.ok(!overlapMsg(r), `glob ${glob}`)
  }
})

test('absent overlapIgnore keeps the throw; a shared non-doc file still throws', async () => {
  const tasks = [task('a', ['docs/README.md']), task('b', ['docs/README.md'])]
  assert.ok(overlapMsg(await run({ tasks })))
  const code = [task('a', ['README.md', 'src/s.py']), task('b', ['README.md', 'src/s.py'])]
  const r = await run({ tasks: code, overlapIgnore: ['README.md'] })
  assert.match(String(r.error.message || r.error), /both list src\/s\.py/)
})

test('slash glob does not match by basename', async () => {
  const tasks = [task('a', ['src/README.md']), task('b', ['src/README.md'])]
  assert.ok(overlapMsg(await run({ tasks, overlapIgnore: ['docs/*.md'] })))
})

test('overlapIgnore must be an array of strings', async () => {
  const r = await run({ tasks: [task('a', ['x'])], overlapIgnore: 'x' })
  assert.match(String(r.error.message || r.error), /overlapIgnore/)
})

test('shared doc file needs no ordering', async () => {
  const tasks = [task('a', ['tests/README.md', 'src/a.py']), task('b', ['tests/README.md', 'src/b.py'])]
  assert.ok(overlapMsg(await run({ tasks })))
  assert.ok(!overlapMsg(await run({ tasks, overlapIgnore: ['**/README.md'] })))
})

test('shared source file still throws', async () => {
  const tasks = [task('a', ['src/s.py']), task('b', ['src/s.py'])]
  const r = await run({ tasks, overlapIgnore: ['**/README.md', 'docs/**'] })
  assert.match(String(r.error.message || r.error), /both list src\/s\.py/)
})

test('double star glob matches any depth', async () => {
  for (const f of ['SKILL.md', 'skills/x/SKILL.md', 'a/b/c/SKILL.md']) {
    const tasks = [task('a', [f, 'src/a.py']), task('b', [f, 'src/b.py'])]
    assert.ok(!overlapMsg(await run({ tasks, overlapIgnore: ['**/SKILL.md'] })), f)
  }
})

test('validate tasks applies default globs', () => {
  const r = cli(epic('README.md'))
  assert.equal(r.status, 0, r.stderr)
  assert.doesNotMatch(r.stderr, /both list/, r.stderr)
})
