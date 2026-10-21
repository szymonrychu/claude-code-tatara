// A run must never launch with zero tasks (remark 2.8): named-copy refuses an
// --args file without a non-empty tasks array, and plan-execute's own guard is pinned.
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { mkdtempSync, readdirSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const CLI = fileURLToPath(new URL('../named-copy.mjs', import.meta.url))
const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const BRIEF = { what: 'a plugin', how: 'workflows', why: 'reliable delivery' }

test('named copy refuses empty tasks', () => {
  for (const [label, args] of [
    ['tasks is empty', { brief: BRIEF, tasks: [] }],
    ['tasks is missing', { brief: BRIEF }],
    ['tasks is not an array', { brief: BRIEF, tasks: 'T1' }],
  ]) {
    const dir = mkdtempSync(join(tmpdir(), 'named-copy-empty-'))
    const file = join(dir, 'args.json')
    writeFileSync(file, JSON.stringify(args))
    const out = join(dir, 'out')
    spawnSync('mkdir', [out])
    const r = spawnSync('node', [CLI, 'plan-execute', 'x', out, '--args', file], { encoding: 'utf8' })
    assert.equal(r.status, 1, label)
    assert.equal(r.stderr, 'named-copy: args.tasks is empty - nothing to execute\n', label)
    assert.deepEqual(readdirSync(out), [], label)
  }
})

test('plan execute throws on empty tasks', async () => {
  const r = await runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks: [] }, agent: async () => ({}) })
  assert.match(String(r.error), /plan-execute: args\.tasks is empty - nothing to execute/)
  assert.equal(r.calls.length, 0)
})
