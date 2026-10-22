// Verify scope wiring (flow-speed D1, D12): every verify runs the task's own targeted command or
// verify-task --targeted, never the implementer's free-text command; --prev-head is a quoted sha or
// absent; the verifier's one Bash call carries the 600 s timeout; at most two verifiers run at once
// per repo; ready tasks start longest chain first; the land step keeps --no-suites --verify.
// Measured: full-suite verifies were 57 of 206 and 636 agent-minutes, and 3-4 concurrent suites
// pinned verifies at the 600 s cap.
import assert from 'node:assert/strict'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow, TEST_PLUGIN_ROOT } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }
const IMPL_CMD = 'mise run test'
const VERIFY_PY = `python3 '${TEST_PLUGIN_ROOT}/scripts/verify-task.py'`
const MERGE_PY = `'${TEST_PLUGIN_ROOT}/skills/worktree-merge/scripts/merge.py'`
const EPIC = { name: 'epic-x', epic: 'epic-x', baseRef: 'epic-x', mainCheckout: '/repo' }

const task = (id, extra = {}) => ({
  id,
  title: `task ${id}`,
  repo: 'api',
  worktree: `/wt/${id}`,
  requirement: `requirement for ${id}`,
  value: 'worth it',
  short: id,
  files: [`src/${id}.py`, `tests/test_${id}.py`],
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
  verification: { command: IMPL_CMD, passed: true, evidence: '3 passed' },
})
const okVerify = { head: 'abc1234', clean: true, command: 'pytest tests/test_x.py', passed: true, evidence: '3 passed', debtMarkers: [] }
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

// b: { verify(id, n) -> result, verifyDelay, implDelay(id) -> ms, audit(n) -> result }.
// Records start/end events and the peak number of agents running per role and per role+repo.
function fakeAgent(b = {}, repoOf = () => 'api') {
  const events = []
  const active = new Map()
  const peak = new Map()
  let audits = 0
  const enter = (k) => {
    active.set(k, (active.get(k) || 0) + 1)
    peak.set(k, Math.max(peak.get(k) || 0, active.get(k)))
  }
  const leave = (k) => active.set(k, active.get(k) - 1)
  const fn = async (prompt, opts) => {
    const [, role, rest] = opts.label.split(':')
    const id = rest.split(/[#+]/)[0]
    const n = Number(rest.split('#')[1] || 0)
    const keys = [role, `${role}:${repoOf(id)}`]
    events.push(`${role}-start:${id}`)
    keys.forEach(enter)
    try {
      if (role === 'impl' || role === 'fix') {
        await sleep(b.implDelay ? b.implDelay(id) : 0)
        return deliverable(id)
      }
      if (role === 'verify') {
        await sleep(b.verifyDelay || 0)
        return b.verify ? b.verify(id, n) : okVerify
      }
      if (role === 'review') return { clean: true, findings: [], filesRead: [`src/${id}.py`] }
      if (role === 'land') {
        return { landed: true, head: `land-${id}`, conflict: false, verification: { command: 'x', passed: true, evidence: 'verify: pass' }, notes: '' }
      }
      if (role === 'merge') return { merged: true, conflict: false, head: 'def4567', verification: { command: 'x', passed: true, evidence: 'ok' } }
      if (role === 'audit') {
        audits++
        return b.audit ? b.audit(audits) : { complete: true, missing: [] }
      }
      throw new Error(`unexpected agent ${opts.label}`)
    } finally {
      keys.forEach(leave)
      events.push(`${role}-end:${id}`)
    }
  }
  return { fn, events, peak }
}
const run = async (args, b, repoOf) => {
  const a = fakeAgent(b, repoOf)
  const r = await runWorkflow(SCRIPT, { args: { brief: BRIEF, ...args }, agent: a.fn })
  return { ...r, events: a.events, peak: a.peak }
}
const ofRole = (r, role, id) => r.calls.filter((c) => c.opts.label.split(':')[1] === role && (!id || c.opts.label.split(':')[2].split(/[#+]/)[0] === id))

test('verify-never-uses-implementer-command', async () => {
  const gapOnA = { complete: false, missing: [{ item: 'retry path', taskId: 'a', evidence: 'src/a.py has no retry' }] }
  const r = await run({ tasks: [task('a'), task('b', { dependsOn: ['a'] })] }, { audit: (n) => (n === 1 ? gapOnA : { complete: true, missing: [] }) })
  assert.equal(r.error, undefined)
  const verifies = ofRole(r, 'verify')
  assert.ok(verifies.length >= 2)
  for (const c of verifies) {
    assert.ok(!c.prompt.includes(IMPL_CMD), `${c.opts.label} runs the implementer's command`)
    assert.ok(!c.prompt.includes('--cmd'), c.opts.label)
  }
  // The forward-merge re-verify of a task with no verify runs verify-task --targeted, not the implementer's command.
  const merges = ofRole(r, 'merge')
  assert.equal(merges.length, 1)
  const p = merges[0].prompt
  assert.ok(!p.includes(IMPL_CMD), p)
  assert.ok(p.includes(VERIFY_PY) && p.includes('--targeted'), p)
  assert.ok(!p.includes('--cmd'), p)
  // With a task verify, the verifier and the forward merge run exactly it.
  const r2 = await run({ tasks: [task('a', { verify: 'pytest tests/test_a.py' }), task('b', { dependsOn: ['a'], verify: 'pytest tests/test_b.py' })] }, { audit: (n) => (n === 1 ? gapOnA : { complete: true, missing: [] }) })
  assert.equal(r2.error, undefined)
  assert.ok(ofRole(r2, 'verify', 'a')[0].prompt.includes("--cmd 'pytest tests/test_a.py'"))
  for (const c of [...ofRole(r2, 'verify'), ...ofRole(r2, 'merge')]) assert.ok(!c.prompt.includes(IMPL_CMD), c.opts.label)
  assert.ok(ofRole(r2, 'merge')[0].prompt.includes('Run exactly this command: pytest tests/test_b.py'))
})

test('verify-without-task-verify-passes-targeted', async () => {
  const r = await run({ tasks: [task('a')] })
  const p = ofRole(r, 'verify')[0].prompt
  assert.ok(p.includes(VERIFY_PY), p)
  assert.match(p, / --targeted /)
  assert.ok(!p.includes('--cmd'), p)
  const r2 = await run({ tasks: [task('a', { verify: 'pytest tests/test_a.py' })] })
  const p2 = ofRole(r2, 'verify')[0].prompt
  assert.ok(p2.includes("--cmd 'pytest tests/test_a.py'"), p2)
  assert.ok(!p2.includes('--targeted'), p2)
})

test('prev-head-passed-only-as-quoted-sha', async () => {
  const failThen = (head) => ({ verify: (id, n) => (n === 1 ? { ...okVerify, head, passed: false, exit: 1, evidence: '1 failed' } : okVerify) })
  const r = await run({ tasks: [task('a')] }, failThen('abc1234'))
  const v = ofRole(r, 'verify')
  assert.equal(v.length, 2)
  assert.ok(!v[0].prompt.includes('--prev-head'))
  assert.ok(v[1].prompt.includes("--prev-head 'abc1234'"), v[1].prompt)
  for (const bad of ['abc123', 'HEAD', 'abc1234; rm -rf /', 'ABC1234', '']) {
    const rb = await run({ tasks: [task('a')] }, failThen(bad))
    const vb = ofRole(rb, 'verify')
    assert.equal(vb.length, 2, `head ${JSON.stringify(bad)}`)
    assert.ok(!vb[1].prompt.includes('--prev-head'), `head ${JSON.stringify(bad)}: ${vb[1].prompt}`)
  }
})

test('verify-prompt-sets-bash-timeout', async () => {
  const r = await run({ tasks: [task('a')] })
  const p = ofRole(r, 'verify')[0].prompt
  assert.ok(p.includes('ONE Bash call'), p)
  assert.ok(p.includes('timeout: 600000'), p)
})

test('at-most-two-verifies-per-repo', async () => {
  // Five api tasks (e waits on a, so one repo's tasks wait on each other) and two web tasks.
  const repo = { a: 'api', b: 'api', c: 'api', d: 'api', e: 'api', w1: 'web', w2: 'web' }
  const tasks = Object.keys(repo).map((id) => task(id, { repo: repo[id], ...(id === 'e' ? { dependsOn: ['a'] } : {}) }))
  const order = ['a', 'b', 'c', 'd', 'w1', 'w2', 'e']
  const r = await run({ tasks }, { implDelay: (id) => order.indexOf(id) * 2, verifyDelay: 25 }, (id) => repo[id])
  assert.equal(r.error, undefined)
  assert.equal(r.result.finished, true)
  // Every queued verify started and the run reached its end: no deadlock.
  assert.equal(ofRole(r, 'verify').length, 7)
  assert.equal(r.peak.get('verify:api'), 2)
  assert.equal(r.peak.get('verify:web'), 2)
  // The cap is per repo: api and web verifiers ran at the same time.
  assert.ok(r.peak.get('verify') > 2, `verify peak ${r.peak.get('verify')}`)
  // Other roles are not limited.
  assert.ok(r.peak.get('impl:api') >= 4, `impl peak ${r.peak.get('impl:api')}`)
  // FIFO: api verifies start in the order their implementers finished.
  const starts = r.events.filter((e) => e.startsWith('verify-start:') && repo[e.split(':')[1]] === 'api').map((e) => e.split(':')[1])
  assert.deepEqual(starts, ['a', 'b', 'c', 'd', 'e'])
  // The next queued verify starts the moment one ends: a third api verify never begins before an api verify ended.
  const third = r.events.indexOf('verify-start:c')
  assert.ok(r.events.indexOf('verify-end:a') < third, r.events.join(' '))
})

test('ready-tasks-start-in-critical-path-order', async () => {
  // Ready at once: A (0 dependents), B (1: D), C (3 transitive: E, F, G), H (0, after A in input order).
  const tasks = [
    task('a'),
    task('b'),
    task('c'),
    task('d', { dependsOn: ['b'] }),
    task('e', { dependsOn: ['c'] }),
    task('f', { dependsOn: ['e'] }),
    task('g', { dependsOn: ['f'] }),
    task('h'),
  ]
  const r = await run({ tasks })
  assert.equal(r.error, undefined)
  const first = ofRole(r, 'impl').slice(0, 4).map((c) => c.opts.label.split(':')[2].split('#')[0])
  assert.deepEqual(first, ['c', 'b', 'a', 'h'])
})

test('land-command-keeps-task-verify-and-no-suites', async () => {
  const r = await run({ ...EPIC, tasks: [task('a', { worktree: '/wt/epic-x-a', verify: 'pytest tests/test_a.py' })] })
  assert.equal(r.error, undefined)
  const land = ofRole(r, 'land')
  assert.equal(land.length, 1)
  const p = land[0].prompt
  const cmd = `cd '/repo' && python3 ${MERGE_PY} --name 'epic-x-a' --base 'epic-x' --keep --no-suites --verify 'pytest tests/test_a.py'`
  assert.ok(p.includes(cmd), p)
  assert.ok(!p.includes(IMPL_CMD), p)
  // With no task verify the land verifies with the command the verifier's script ran, never the implementer's.
  const r2 = await run({ ...EPIC, tasks: [task('a', { worktree: '/wt/epic-x-a' })] })
  assert.equal(r2.error, undefined)
  const p2 = ofRole(r2, 'land')[0].prompt
  assert.ok(p2.includes(`--keep --no-suites --verify 'pytest tests/test_x.py'`), p2)
  assert.ok(!p2.includes(IMPL_CMD), p2)
})

test('land-without-any-verify-command-fails', async () => {
  // No task verify and a verifier that reported no command: nothing would check the land, so it never runs.
  const r = await run({ ...EPIC, tasks: [task('a', { worktree: '/wt/epic-x-a' })] }, { verify: () => ({ ...okVerify, command: '' }) })
  assert.equal(r.error, undefined)
  assert.equal(ofRole(r, 'land').length, 0)
  assert.equal(r.result.tasks.find((t) => t.id === 'a').stopped, 'land-failed')
})
