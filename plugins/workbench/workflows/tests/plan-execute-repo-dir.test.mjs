// Run 1 stalled because every merge instruction was `cd <wt>/<repo> && git merge`,
// and on a plain repo the worktree IS the repo root. repoDir(t) resolves both
// layouts at run time; the guard stops before any merge outside the task's checkout.
import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import { mkdirSync, mkdtempSync, readFileSync, realpathSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { test } from 'node:test'
import { fileURLToPath } from 'node:url'
import { runWorkflow } from './harness.mjs'

const SCRIPT = fileURLToPath(new URL('../plan-execute.js', import.meta.url))
const IMPLEMENTER_MD = readFileSync(fileURLToPath(new URL('../../agents/implementer.md', import.meta.url)), 'utf8')
const BRIEF = { what: 'a plugin', how: 'workflows and hooks', why: 'reliable delivery' }

const task = (id, worktree, extra = {}) => ({
  id,
  title: `task ${id}`,
  repo: 'api',
  worktree,
  requirement: `requirement for ${id}`,
  value: 'worth it',
  files: [`src/${id}-a.py`, `src/${id}-b.py`, `tests/test_${id}.py`],
  verify: `pytest tests/test_${id}.py`,
  ...extra,
})

const idOf = (short) => short.replace('task-', '').replace(/^t(\d+)/, 'T$1')
const deliverable = (id) => ({
  taskId: id,
  complete: true,
  summary: 'did it',
  filesChanged: ['src/a.py'],
  branch: `b-${id}`,
  tests: { added: ['tests/test_a.py'], wroteTestFirst: true, red: { command: 'pytest', output: 'FAILED tests/test_a.py::test_x' } },
  verification: { command: 'pytest tests/test_a.py', passed: true, evidence: '3 passed' },
})
const okVerify = { head: 'abc123', clean: true, command: 'pytest', passed: true, evidence: '3 passed', debtMarkers: [] }
const okMerge = { merged: true, conflict: false, head: 'def456', verification: { command: 'x', passed: true, evidence: 'ok' } }
const gapOnT1 = { complete: false, missing: [{ item: 'retry path', taskId: 'T1', evidence: 'src/T1-a.py has no retry' }] }

function agent() {
  let audits = 0
  return async (prompt, opts) => {
    const [, role, rest] = opts.label.split(':')
    const short = rest.split(/[#+]/)[0]
    if (role === 'impl' || role === 'fix') return deliverable(idOf(short))
    if (role === 'verify') return okVerify
    if (role === 'review' && rest === 'task-t1#1') return { clean: false, findings: [{ severity: 'high', file: 'src/a.py', summary: 'bug', requirement: 'req' }], filesRead: ['src/a.py'] }
    if (role === 'review') return { clean: true, findings: [], filesRead: ['src/a.py'] }
    if (role === 'merge') return okMerge
    if (role === 'audit') return ++audits === 1 ? gapOnT1 : { complete: true, missing: [] }
    throw new Error(`unexpected agent ${opts.label}`)
  }
}

const git = (cwd, ...a) => execFileSync('git', a, { cwd, encoding: 'utf8' }).trim()
const sh = (cmd) => execFileSync('sh', ['-c', cmd], { encoding: 'utf8' }).trim()

// workbench layout: <wt>/api is the repo; plain layout: <wt> is the repo.
function layouts() {
  const root = realpathSync(mkdtempSync(join(tmpdir(), 'repo-dir-')))
  const wb = join(root, 'wb')
  const plain = join(root, 'plain')
  mkdirSync(join(wb, 'api'), { recursive: true })
  mkdirSync(plain, { recursive: true })
  git(join(wb, 'api'), 'init', '-q')
  git(plain, 'init', '-q')
  return { wb: { wt: wb, dir: join(wb, 'api') }, plain: { wt: plain, dir: plain } }
}

const EXPR = /\$\(if \[ -d [^)]*?; fi\)/

for (const [name, key] of [['workbench <wt>/<repo>', 'wb'], ['plain-repo <wt>', 'plain']]) {
  test(`${name}: every prompt resolves the checkout through repoDir and guards the merge`, async () => {
    const L = layouts()[key]
    const tasks = [task('T1', L.wt + '-t1'), task('T2', L.wt, { dependsOn: ['T1'] })]
    const r = await runWorkflow(SCRIPT, { args: { brief: BRIEF, tasks }, agent: agent() })
    assert.equal(r.error, undefined)
    const byRole = (role, short) => r.calls.filter((c) => c.opts.label.startsWith(`pe:${role}:${short}`))
    const impl = byRole('impl', 'task-t2')[0].prompt
    const verify = byRole('verify', 'task-t2')[0].prompt
    const merge = byRole('merge', 'task-t2')[0].prompt
    const fix = byRole('fix', 'task-t1')[0].prompt

    for (const p of [impl, verify, merge]) {
      const expr = p.match(EXPR)
      assert.ok(expr, 'prompt carries the run-time layout resolution')
      // the emitted shell resolves to the right directory for this layout
      assert.equal(sh(`echo ${expr[0]}`), L.dir)
      assert.ok(!p.includes(`${L.wt}/api && git`), 'no hard-coded <wt>/<repo> cd')
    }
    // dependency merge and forward merge assert the toplevel before merging
    for (const p of [impl, merge]) {
      assert.match(p, /git rev-parse --show-toplevel/)
      const line = p.split('\n').find((l) => l.includes('git merge --no-edit'))
      assert.ok(line.indexOf('--show-toplevel') < line.indexOf('git merge --no-edit'), 'guard precedes merge')
      assert.match(p, /stop and report/i)
    }
    // behaviour: the emitted command merges in the right checkout and refuses elsewhere
    const id = ['-c', 'user.name=t', '-c', 'user.email=t@t']
    git(L.dir, ...id, 'commit', '-q', '--allow-empty', '-m', 'base')
    git(L.dir, 'checkout', '-q', '-b', 'feat')
    git(L.dir, ...id, 'commit', '-q', '--allow-empty', '-m', 'feat work')
    git(L.dir, 'checkout', '-q', '-')
    const base = git(L.dir, 'rev-parse', 'HEAD')
    for (const p of [impl, merge]) {
      const cmd = p.match(/(D="[^\n`]*?git merge --no-edit \S+?)(?=[`.\s]*(?:\.|\n|If|$))/)[1].replace(/[`.]+$/, '')
      assert.match(cmd, /git rev-parse --show-toplevel.*git merge --no-edit/, 'guard text precedes the merge')
      assert.match(cmd, /pwd -P/)
      const feat = cmd.replace(/git merge --no-edit \S+$/, 'git merge --no-edit feat')
      const env = 'GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t'
      // right layout: the command as emitted merges the branch
      sh(`${env} ${feat.replace(/^D=/, 'export D=')}`)
      assert.notEqual(git(L.dir, 'rev-parse', 'HEAD'), base, 'merged in the task checkout')
      git(L.dir, 'reset', '-q', '--hard', base)

      // wrong directory: a subdirectory of a real repo holding a mergeable branch
      const sub = join(L.dir, 'sub')
      mkdirSync(sub, { recursive: true })
      const wrong = feat.replace(EXPR, `$(echo ${sub})`)
      assert.notEqual(wrong, feat)
      assert.equal(sh(`${env} ${wrong} || echo BLOCKED`).split('\n').pop(), 'BLOCKED')
      assert.equal(git(L.dir, 'rev-parse', 'HEAD'), base, 'nothing merged from the wrong directory')
    }

    // impl and fix carry the rule in agents/implementer.md, the agent they run as;
    // the merge agent carries it in its prompt. impl and fix still name their checkout.
    for (const role of ['impl', 'fix']) assert.equal(r.calls.find((c) => c.opts.label.startsWith(`pe:${role}:`)).opts.agentType, 'workbench:implementer', role)
    assert.ok(fix.match(EXPR) && fix.match(EXPR)[0].includes(`${L.wt}-t1/api`), 'fix prompt resolves its own checkout through repoDir')
    for (const p of [IMPLEMENTER_MD, merge]) {
      assert.match(p, /`git merge`, `git commit` and `git reset` run only inside/)
      assert.match(p, /never in the main checkout or another task's tree/)
    }
  })
}
