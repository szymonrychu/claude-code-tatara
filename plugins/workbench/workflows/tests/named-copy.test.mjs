// named-copy.mjs gives one workflow run its own name. meta.name must be a pure
// literal and Workflow ignores a passed title, so a per-run name means a copy.
import assert from 'node:assert/strict'
import { execFileSync, spawnSync } from 'node:child_process'
import { mkdtempSync, readFileSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const CLI = fileURLToPath(new URL('../named-copy.mjs', import.meta.url))
const ROOT = fileURLToPath(new URL('../..', import.meta.url)).replace(/\/$/, '')
const ORIG = fileURLToPath(new URL('../plan-execute.js', import.meta.url))

test('writes a copy whose meta.name carries the run name and prints its path', () => {
  const out = mkdtempSync(join(tmpdir(), 'named-copy-'))
  const path = execFileSync('node', [CLI, 'plan-execute', 'auth-refresh', out], { encoding: 'utf8' }).trim()
  assert.equal(path, join(out, 'plan-execute-auth-refresh.js'))
  const copy = readFileSync(path, 'utf8')
  assert.match(copy, /^export const meta = \{\n  name: 'plan-execute:auth-refresh',\n/)
  // only the name line and the ARGS line (pluginRoot) differ
  assert.equal(copy.replace(/^const ARGS = Object\.assign.*$/m, ARGS_LINE).replace("name: 'plan-execute:auth-refresh'", "name: 'plan-execute'"), readFileSync(ORIG, 'utf8'))
})

test('rejects a run name that is not a lowercase slug, writing nothing', () => {
  const out = mkdtempSync(join(tmpdir(), 'named-copy-'))
  const r = spawnSync('node', [CLI, 'plan-execute', "x'; evil", out], { encoding: 'utf8' })
  assert.notEqual(r.status, 0)
  assert.match(r.stderr, /slug/)
})

test('rejects an unknown workflow', () => {
  const out = mkdtempSync(join(tmpdir(), 'named-copy-'))
  const r = spawnSync('node', [CLI, 'no-such-flow', 'auth', out], { encoding: 'utf8' })
  assert.notEqual(r.status, 0)
})

// --args embeds the run's args in the copy so task text never passes through the
// orchestrator's context at launch.
const ARGS_LINE = "const ARGS = (typeof args !== 'undefined' && args) || {}"
const argsFile = (obj) => {
  const f = join(mkdtempSync(join(tmpdir(), 'named-copy-args-')), 'args.json')
  writeFileSync(f, typeof obj === 'string' ? obj : JSON.stringify(obj))
  return f
}
const BRIEF = { what: 'a plugin', how: 'workflows', why: 'reliable' }
const embedTask = {
  id: 'T1', title: 'task T1', repo: 'api', worktree: '/wt/T1', requirement: 'embedded requirement',
  value: 'worth it', files: ['src/a.py', 'src/b.py', 'tests/test_a.py'],
}

test('plan-execute reads args only through the one ARGS line', () => {
  const lines = readFileSync(ORIG, 'utf8').split('\n')
  assert.equal(lines.filter((l) => l === ARGS_LINE).length, 1)
  const code = (l) => l.replace(/'[^']*'|"[^"]*"|`[^`]*`/g, '""')
  const direct = lines.filter((l) => !/^\s*\/\//.test(l) && l !== ARGS_LINE && /\bargs\b/.test(code(l)))
  assert.deepEqual(direct, [])
})

test('--args rewrites the ARGS line to embed the JSON under runtime args', () => {
  const out = mkdtempSync(join(tmpdir(), 'named-copy-'))
  const path = execFileSync('node', [CLI, 'plan-execute', 'x', out, '--args', argsFile({ name: 'e', n: 1, tasks: [embedTask] })], { encoding: 'utf8' }).trim()
  const copy = readFileSync(path, 'utf8')
  assert.ok(!copy.includes(ARGS_LINE))
  assert.ok(copy.includes(`const ARGS = Object.assign({}, {"name":"e","n":1,"tasks":${JSON.stringify([embedTask])},"pluginRoot":${JSON.stringify(ROOT)}}, (typeof args !== 'undefined' && args) || {})`))
  assert.equal(copy.replace(/^const ARGS = Object\.assign.*$/m, ARGS_LINE).replace("'plan-execute:x'", "'plan-execute'"), readFileSync(ORIG, 'utf8'))
})

test('runtime args override embedded ones; embedded run with no args reaches its first agent', async () => {
  const out = mkdtempSync(join(tmpdir(), 'named-copy-'))
  const path = execFileSync('node', [CLI, 'plan-execute', 'x', out, '--args', argsFile({ brief: BRIEF, name: 'emb', tasks: [embedTask] })], { encoding: 'utf8' }).trim()
  const seen = []
  const agent = async (prompt, opts) => {
    seen.push({ prompt, label: opts.label })
    throw new Error('stop')
  }
  const r1 = await runWorkflow(path, { args: undefined, agent })
  assert.ok(r1.calls.length >= 1, String(r1.error))
  assert.match(r1.calls[0].prompt, /embedded requirement/)
  assert.match(r1.calls[0].opts.label, /^emb:/)
  const r2 = await runWorkflow(path, { args: { name: 'over' }, agent })
  assert.match(r2.calls[0].opts.label, /^over:/)
  assert.match(r2.calls[0].prompt, /embedded requirement/)
})

test('--args fails when the copy has no ARGS line, naming the workflow', () => {
  const r = spawnSync('node', [CLI, 'hook-probe', 'x', mkdtempSync(join(tmpdir(), 'named-copy-')), '--args', argsFile({})], { encoding: 'utf8' })
  assert.equal(r.status, 1)
  assert.equal(r.stderr, 'named-copy: hook-probe.js has no ARGS line\n')
})

test('--args fails on unreadable or invalid JSON with the file and the error', () => {
  const out = mkdtempSync(join(tmpdir(), 'named-copy-'))
  const missing = join(out, 'nope.json')
  const a = spawnSync('node', [CLI, 'plan-execute', 'x', out, '--args', missing], { encoding: 'utf8' })
  assert.equal(a.status, 1)
  assert.ok(a.stderr.startsWith(`named-copy: ${missing}: `))
  const bad = argsFile('{not json')
  const b = spawnSync('node', [CLI, 'plan-execute', 'x', out, '--args', bad], { encoding: 'utf8' })
  assert.equal(b.status, 1)
  assert.ok(b.stderr.startsWith(`named-copy: ${bad}: `))
})


test('the copy always embeds the absolute pluginRoot, with and without --args, runtime args overriding', () => {
  const out = mkdtempSync(join(tmpdir(), 'named-copy-'))
  const plain = readFileSync(execFileSync('node', [CLI, 'plan-execute', 'x', out], { encoding: 'utf8' }).trim(), 'utf8')
  assert.ok(plain.includes(`const ARGS = Object.assign({}, {"pluginRoot":${JSON.stringify(ROOT)}}, (typeof args !== 'undefined' && args) || {})`))
  const withArgs = readFileSync(execFileSync('node', [CLI, 'plan-execute', 'y', out, '--args', argsFile({ name: 'e', pluginRoot: '/stale', tasks: [embedTask] })], { encoding: 'utf8' }).trim(), 'utf8')
  assert.ok(withArgs.includes(`"pluginRoot":${JSON.stringify(ROOT)}`))
  assert.ok(!withArgs.includes('/stale'))
})
