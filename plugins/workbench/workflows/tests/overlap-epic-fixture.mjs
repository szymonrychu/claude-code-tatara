// Shared fixture: an epic on disk whose two tasks share one file.
import { spawnSync } from 'node:child_process'
import { mkdirSync, mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const CLI = fileURLToPath(new URL('../validate-tasks.mjs', import.meta.url))
const README = `---\ntitle: Alpha\nblockers: []\nstage: build\nrepos: [api]\ncreated: 2026-10-17\n---\n\n# Alpha\n\n## Project brief\n\nWhat: a\nHow: b\nWhy: c\n\n## Description\n\nd\n\n## Goals\n\n- g\n\n## Non-goals\n\n- n\n`
const DESIGN = `# D\n\n## Decisions\n\n### D1: first\n\ntext\n\n## Decision coverage\n\n| Decision | Tasks |\n|---|---|\n| D1 first | t-one, t-two |\n\n## Contracts\n\n| Part | Owner | Consumers | Where defined |\n|---|---|---|---|\n`
const LEDGER = [{ id: 'A', text: 'x', decisions: ['D1'], tasks: ['t-one', 't-two'], status: 'approved' }]
const TASK = (own, shared) =>
  `---\ntitle: X\nstatus: todo\nrepo: api\nvalue: worth it\nfiles: [${own}, ${shared}]\nverify: pytest tests/test_x.py\ndepends_on: []\nowns: []\nuses: []\n---\n\n# X\n\n## Requirement\n\nBuild.\n\n## Acceptance conditions\n\n- a1: works [evidence: command:true]\n\n## Files\n\n- ${own}\n- ${shared}\n\n## Expected outcome\n\nx\n\n## Steps\n\n- go\n`
export const epic = (shared, config) => {
  const wb = mkdtempSync(join(tmpdir(), 'vt-overlap-'))
  const api = join(wb, 'code', 'api')
  mkdirSync(api, { recursive: true })
  // The plans root has no workbench marker here, so config reads the root checkout's file.
  spawnSync('git', ['init', '-q', wb])
  if (config !== undefined) {
    mkdirSync(join(wb, '.claude'), { recursive: true })
    writeFileSync(join(wb, '.claude', 'workbench.json'), config)
  }
  const d = join(wb, 'docs', 'plans', 'in-progress', 'alpha')
  mkdirSync(join(d, 'tasks'), { recursive: true })
  writeFileSync(join(d, 'README.md'), README)
  writeFileSync(join(d, 'design.md'), DESIGN)
  writeFileSync(join(d, 'approvals.json'), JSON.stringify(LEDGER))
  writeFileSync(join(d, 'tasks', 't-one.md'), TASK('src/a.py', shared))
  writeFileSync(join(d, 'tasks', 't-two.md'), TASK('src/b.py', shared))
  return d
}
export const cli = (d) => spawnSync(process.execPath, [CLI, '--epic', d], { encoding: 'utf8', env: { ...process.env, WORKBENCH_ROOT: '' } })
