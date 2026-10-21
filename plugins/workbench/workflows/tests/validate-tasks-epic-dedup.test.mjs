// Dedup across epics (ticket.py check --epic) through validate-tasks --epic.
import assert from 'node:assert/strict'
import { spawnSync } from 'node:child_process'
import { mkdirSync, mkdtempSync, readFileSync, renameSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'

const CLI = fileURLToPath(new URL('../validate-tasks.mjs', import.meta.url))
const TICKET = fileURLToPath(new URL('../../skills/start-development/scripts/ticket.py', import.meta.url))
const root = mkdtempSync(join(tmpdir(), 'validate-epic-'))
const py = (...a) => {
  const r = spawnSync('python3', [TICKET, ...a], { encoding: 'utf8' })
  assert.equal(r.status, 0, r.stderr)
  return r
}
const epic = (slug, phase = 'todo') => {
  py('new-epic', '--root', root, '--title', slug, '--force')
  if (phase !== 'todo') {
    mkdirSync(join(root, phase), { recursive: true })
    renameSync(join(root, 'todo', slug), join(root, phase, slug))
  }
  return join(root, phase, slug)
}
const task = (slug, title, files, extra = []) =>
  py('new-task', '--root', root, '--epic', slug, '--title', title, '--repo', 'p', '--value', 'v', '--files', files, '--verify', 'true', ...extra)
const lint = (dir) => spawnSync(process.execPath, [CLI, '--epic', dir], { encoding: 'utf8' })

// new-task refuses a clash itself, so build the clash by moving or rewriting after the fact.
test('--epic fails on a file shared with an in-progress epic', () => {
  epic('busy-epic')
  task('busy-epic', 'Busy task', 'shared.py')
  const dir = epic('new-epic-a')
  task('new-epic-a', 'Clash task', 'shared.py')
  mkdirSync(join(root, 'in-progress'), { recursive: true })
  renameSync(join(root, 'todo', 'busy-epic'), join(root, 'in-progress', 'busy-epic'))
  const r = lint(dir)
  assert.equal(r.status, 1)
  assert.match(r.stderr, /shared\.py/)
})

test('--epic fails on a part owned by another todo epic', () => {
  epic('owner-epic')
  task('owner-epic', 'Owner task', 'o.py', ['--owns', 'widget'])
  const dir = epic('claimant-epic')
  task('claimant-epic', 'Claim task', 'c.py', ['--owns', 'gadget'])
  const f = join(dir, 'tasks', 'claim-task.md')
  writeFileSync(f, readFileSync(f, 'utf8').replace('gadget', 'widget'))
  const r = lint(dir)
  assert.equal(r.status, 1)
  assert.match(r.stderr, /widget/)
})

test('--epic on a missing directory fails', () => {
  const r = lint(join(root, 'todo', 'nope'))
  assert.equal(r.status, 1)
})
