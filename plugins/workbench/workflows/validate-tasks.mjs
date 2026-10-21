#!/usr/bin/env node
// Lint a plan-execute task list without spending an agent:
//   node workflows/validate-tasks.mjs <tasks.json> [--existing <existing.json>] [--do-not-build <dnb.json>]
//                                    [--plan <plan.md> --approvals <approvals.json>] [--approvals <approvals.json>]
//                                    [--design <design.md>]
//   node workflows/validate-tasks.mjs --epic <epic dir>
// --epic lints a ticket-flow epic directory (README, task files, approvals.json, design.md,
// ticket.py check); the tasks are derived by ticket.py tasks and ac is required.
// Runs plan-execute.js through the test harness with an agent that stops the
// run; reaching the first agent call means every validation passed.
import { spawnSync } from 'node:child_process'
import { existsSync, readdirSync, readFileSync } from 'node:fs'
import { basename, dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { lintAc } from './ac-lint.mjs'
import { runWorkflow } from './tests/harness.mjs'

const MAX_ESTIMATE_MIN = 90
const USAGE = 'usage: node validate-tasks.mjs <tasks.json> [--existing <existing.json>] [--do-not-build <dnb.json>] [--plan <plan.md>] [--approvals <approvals.json>] [--design <design.md>]\n       node validate-tasks.mjs --epic <epic dir>'
const fail = (msg, code = 1) => {
  console.error(msg)
  process.exit(code)
}
const readJson = (path) => {
  try {
    return JSON.parse(readFileSync(path, 'utf8'))
  } catch (e) {
    return fail(`${path}: ${e.message}\n${USAGE}`)
  }
}

const argv = process.argv.slice(2)
// Pull `--flag <path>` out of argv; returns the path (undefined when absent).
let badFlag = false
const takeFlag = (flag) => {
  const i = argv.indexOf(flag)
  if (i === -1) return undefined
  const path = argv[i + 1]
  if (!path) badFlag = true
  argv.splice(i, 2)
  return path
}
const epicPath = takeFlag('--epic')
const existingPath = takeFlag('--existing')
const doNotBuildPath = takeFlag('--do-not-build')
const planPath = takeFlag('--plan')
const approvalsPath = takeFlag('--approvals')
const designPath = takeFlag('--design')
const epicMode = epicPath !== undefined
const legacyBad = argv.length !== 1 || (designPath && !planPath) || (planPath && !approvalsPath)
const epicBad = argv.length || existingPath || doNotBuildPath || planPath || approvalsPath || designPath
if (badFlag || (epicMode ? epicBad : legacyBad)) fail(USAGE)

const PLUGIN = fileURLToPath(new URL('..', import.meta.url))
const SD = join(PLUGIN, 'skills', 'start-development')
const ticket = (...args) => spawnSync('python3', [join(SD, 'scripts', 'ticket.py'), ...args], { encoding: 'utf8' })
const epicDir = epicMode ? resolve(epicPath) : undefined
const plansRoot = epicMode ? dirname(dirname(epicDir)) : undefined

let tasks
let deriveError = null
if (epicMode) {
  if (!existsSync(epicDir)) fail(`${epicPath}: no such epic directory\n${USAGE}`)
  const r = ticket('tasks', epicDir, '--root', plansRoot)
  tasks = r.status === 0 ? JSON.parse(r.stdout) : []
  if (r.status !== 0) deriveError = (r.stderr.trim().split('\n')[0] || 'ticket.py tasks failed').replace(/^ticket\.py: /, 'tasks: ')
  // ticket.py leaves unset frontmatter fields as empty strings; plan-execute wants them absent.
  for (const t of tasks) for (const k of Object.keys(t)) if (t[k] === '') delete t[k]
} else {
  tasks = readJson(argv[0])
  if (!Array.isArray(tasks)) fail(`${argv[0]}: expected a JSON array of tasks\n${USAGE}`)
}
const existing = existingPath ? readJson(existingPath) : undefined
const doNotBuild = doNotBuildPath ? readJson(doNotBuildPath) : undefined
const ledgerPath = epicMode ? join(epicDir, 'approvals.json') : approvalsPath
const ledger = ledgerPath && existsSync(ledgerPath) ? readJson(ledgerPath) : undefined
if (ledger !== undefined && (!Array.isArray(ledger) || ledger.some((e) => !e || typeof e !== 'object' || Array.isArray(e)))) {
  fail(`${ledgerPath}: expected a JSON array of ledger entries\n${USAGE}`)
}
for (const t of tasks) if (t && typeof t === 'object' && !t.worktree) t.worktree = `/validate/${t.id}`

const readText = (path) => {
  try {
    return readFileSync(path, 'utf8')
  } catch (e) {
    return fail(`${path}: ${e.message}\n${USAGE}`)
  }
}

// Section text: from the line-anchored `## <name>` heading to the next `## ` heading (null when absent).
const section = (md, name) => {
  const m = new RegExp(`^## ${name}\\s*$`, 'm').exec(md)
  if (!m) return null
  const rest = md.slice(m.index + m[0].length)
  const next = rest.search(/^## /m)
  return next === -1 ? rest : rest.slice(0, next)
}
const cells = (row) => row.split('|').slice(1, -1).map((c) => c.trim().replace(/`/g, ''))
const ids = (cell) => (cell.match(/\bT\d+\b/g) ?? [])

// Plan-document checks; returns every failure message.
const lintPlan = (md, designMd) => {
  const errs = []
  const byId = new Map(tasks.map((t) => [t.id, t]))
  const blocks = new Set([...md.matchAll(/^### Task (\d+)\b/gm)].map((m) => m[1]))
  const jsonNums = new Set()
  for (const t of tasks) {
    const m = /^T(\d+)$/.exec(t.id)
    if (!m) errs.push(`plan: JSON task ${t.id} is not of the form T<n>`)
    else jsonNums.add(m[1])
  }
  for (const n of blocks) if (!jsonNums.has(n)) errs.push(`plan: task block "Task ${n}" has no JSON task T${n}`)
  for (const n of jsonNums) if (!blocks.has(n)) errs.push(`plan: JSON task T${n} has no "### Task ${n}" block`)

  const brief = section(md, 'Project brief')
  if (brief === null) errs.push('plan: missing section ## Project brief')
  else {
    for (const label of ['What', 'How', 'Why']) {
      if (!new RegExp(`^${label}:\\s*\\S`, 'm').test(brief)) errs.push(`plan: Project brief is missing ${label}`)
    }
  }

  const coverage = section(md, 'Decision coverage')
  const contracts = section(md, 'Contracts')
  for (const [name, text] of [['Decision coverage', coverage], ['Contracts', contracts]]) {
    if (text === null) {
      errs.push(`plan: missing section ## ${name}`)
      continue
    }
    for (const id of new Set(ids(text))) if (!byId.has(id)) errs.push(`plan: ## ${name} names unknown task ${id}`)
  }

  if (contracts !== null) {
    const rows = contracts.split('\n').filter((l) => l.trim().startsWith('|')).slice(2)
    for (const row of rows) {
      const [part, owner, consumers = ''] = cells(row)
      if (!byId.get(owner)?.owns?.includes(part)) errs.push(`plan: contract ${part} owner ${owner} does not own it`)
      if (/^(none)?$/i.test(consumers)) continue
      for (const c of consumers.split(',').map((x) => x.trim()).filter(Boolean)) {
        if (!byId.get(c)?.uses?.includes(part)) errs.push(`plan: contract ${part} consumer ${c} does not use it`)
      }
    }
  }

  if (designMd !== undefined && coverage !== null) {
    const covered = new Set(coverage.match(/\bD\d+\b/g) ?? [])
    for (const m of designMd.matchAll(/^### D(\d+):/gm)) {
      if (!covered.has(`D${m[1]}`)) errs.push(`plan: design decision D${m[1]} has no row in Decision coverage`)
    }
  }
  return errs
}

// Approval-ledger checks; returns every failure message.
const lintApprovals = (entries, designMd) => {
  const errs = []
  const taskIds = new Set(tasks.map((t) => t.id))
  const designIds = designMd === undefined ? undefined : new Set([...designMd.matchAll(/^### D(\d+):/gm)].map((m) => `D${m[1]}`))
  const seen = new Set()
  const named = new Set()
  const list = (v) => (Array.isArray(v) ? v : [])
  for (const e of entries) {
    if (seen.has(e.id)) errs.push(`approvals: duplicate id ${e.id}`)
    seen.add(e.id)
    if (typeof e.text !== 'string' || !e.text.trim()) errs.push(`approvals: item ${e.id} has empty text`)
    if (!list(e.tasks).length) errs.push(`approvals: item ${e.id} maps to no task`)
    for (const t of list(e.tasks)) if (!deriveError && !taskIds.has(t)) errs.push(`approvals: item ${e.id} names unknown task ${t}`)
    if (e.status !== 'approved') errs.push(`approvals: item ${e.id} has status ${e.status}, only approved items are planned`)
    if (!designIds) continue
    if (!list(e.decisions).length) errs.push(`approvals: item ${e.id} names no decision`)
    for (const d of list(e.decisions)) {
      named.add(d)
      if (!designIds.has(d)) errs.push(`approvals: item ${e.id} names unknown decision ${d}`)
    }
  }
  for (const d of designIds ?? []) if (!named.has(d)) errs.push(`approvals: design decision ${d} is covered by no approved item`)
  return errs
}

// --- epic mode ---------------------------------------------------------------
const frontmatterKeys = (md) => {
  const m = /^---\n([\s\S]*?)\n---/.exec(md)
  const out = new Map()
  for (const line of m ? m[1].split('\n') : []) {
    const kv = /^([A-Za-z_][\w-]*):\s*(.*)$/.exec(line)
    if (kv) out.set(kv[1], kv[2].trim().replace(/^(["'])\1$/, ''))
  }
  return out
}
// A section is empty when it is blank, an unfilled `{{placeholder}}`, or the template's own guidance.
const sectionEmpty = (text, templateText) => {
  const t = text.trim()
  return !t || /^\{\{[^}]*\}\}$/.test(t) || (templateText != null && t === templateText.trim())
}
const taskSlugsOf = (v) => (v ?? '').match(/[a-z0-9][a-z0-9-]*/g) ?? []

const lintReadme = (md) => {
  const errs = []
  const fm = frontmatterKeys(md)
  for (const k of ['title', 'stage', 'created']) if (!fm.get(k)) errs.push(`epic: README frontmatter is missing ${k}`)
  for (const k of ['blockers', 'repos']) if (!fm.has(k)) errs.push(`epic: README frontmatter is missing ${k}`)
  const brief = section(md, 'Project brief')
  if (brief === null) errs.push('epic: README is missing ## Project brief')
  else {
    for (const label of ['What', 'How', 'Why']) {
      const m = new RegExp(`^${label}:[ \t]*(.*)$`, 'm').exec(brief)
      if (!m || sectionEmpty(m[1])) errs.push(`epic: README Project brief is missing ${label}`)
    }
  }
  for (const name of ['Description', 'Goals', 'Non-goals']) {
    const text = section(md, name)
    if (text === null) errs.push(`epic: README ## ${name} is missing`)
    else if (sectionEmpty(text)) errs.push(`epic: README ## ${name} is empty`)
  }
  return errs
}

const lintTaskFiles = () => {
  const errs = []
  const tpl = readFileSync(join(SD, 'templates', 'task.md'), 'utf8')
  const dir = join(epicDir, 'tasks')
  const files = existsSync(dir) ? readdirSync(dir).filter((f) => f.endsWith('.md')).sort() : []
  if (!files.length) errs.push('epic: no task files under tasks/')
  for (const f of files) {
    const md = readFileSync(join(dir, f), 'utf8')
    for (const name of ['Requirement', 'Acceptance conditions', 'Files', 'Expected outcome', 'Steps']) {
      const text = section(md, name)
      if (text === null) errs.push(`epic: task ${basename(f, '.md')}: ## ${name} is missing`)
      else if (sectionEmpty(text, section(tpl, name))) errs.push(`epic: task ${basename(f, '.md')}: ## ${name} is empty`)
    }
  }
  return errs
}

// Decision coverage, contracts and ledger-to-decision links of design.md, with task slugs as ids.
const lintDesign = (designMd) => {
  const errs = []
  const byId = new Map(tasks.map((t) => [t.id, t]))
  const coverage = section(designMd, 'Decision coverage')
  const contracts = section(designMd, 'Contracts')
  const rowsOf = (text) => text.split('\n').filter((l) => l.trim().startsWith('|')).slice(2).map(cells)
  const covered = new Set()
  if (coverage === null) errs.push('design: missing section ## Decision coverage')
  else {
    for (const [decision = '', taskCell = ''] of rowsOf(coverage)) {
      const d = /^D\d+\b/.exec(decision)
      if (d) covered.add(d[0])
      for (const id of taskSlugsOf(taskCell)) if (!deriveError && !byId.has(id)) errs.push(`design: Decision coverage names unknown task ${id}`)
    }
    for (const m of designMd.matchAll(/^### D(\d+):/gm)) {
      if (!covered.has(`D${m[1]}`)) errs.push(`design: decision D${m[1]} has no row in Decision coverage`)
    }
  }
  if (contracts === null) errs.push('design: missing section ## Contracts')
  else if (!deriveError) {
    for (const row of rowsOf(contracts)) {
      const [part = '', owner = '', consumers = ''] = row
      if (!byId.get(owner)?.owns?.includes(part)) errs.push(`design: contract ${part} owner ${owner} does not own it`)
      if (/^(none)?$/i.test(consumers)) continue
      for (const c of consumers.split(',').map((x) => x.trim()).filter(Boolean)) {
        if (!byId.get(c)?.uses?.includes(part)) errs.push(`design: contract ${part} consumer ${c} does not use it`)
      }
    }
  }
  return errs
}

// ticket.py check --epic: every hard failure is one line.
const lintCheck = () => {
  const r = ticket('check', '--epic', basename(epicDir), '--root', plansRoot)
  if (r.status === 0) return []
  const out = r.stderr.split('\n').filter((l) => l.startsWith('ticket.py: ')).map((l) => `check: ${l.slice('ticket.py: '.length)}`)
  return out.length ? out : [`check: ticket.py check failed (exit ${r.status})`]
}

// D6: each test ref must have a runner (scripts/lib/workbench.py runner), resolved in the task's checkout.
const WORKBENCH_PY = join(PLUGIN, 'scripts', 'lib', 'workbench.py')
const checkoutFor = (repo) => {
  if (repo) for (let d = plansRoot; ; d = dirname(d)) {
    if (existsSync(join(d, 'code', repo))) return join(d, 'code', repo)
    if (dirname(d) === d) break
  }
  const r = spawnSync('git', ['-C', plansRoot, 'rev-parse', '--show-toplevel'], { encoding: 'utf8' })
  return r.status === 0 && r.stdout.trim() ? r.stdout.trim() : null
}
const lintRefRunners = () => {
  const errs = []
  for (const t of tasks) {
    const refs = (Array.isArray(t.ac) ? t.ac : []).filter((a) => a?.evidence?.kind === 'test' && a.evidence.ref)
    if (!refs.length) continue
    const checkout = checkoutFor(t.repo)
    if (!checkout) {
      console.error(`warning: task ${t.id}: repo checkout not found, test refs not checked`)
      continue
    }
    for (const a of refs) {
      const r = spawnSync('python3', [WORKBENCH_PY, 'runner', a.evidence.ref, '--repo', checkout], { encoding: 'utf8' })
      const file = a.evidence.ref.split('::')[0]
      if (r.status === 2) errs.push(`ac: task ${t.id} ${a.id}: no runner for ${file}; add a refRunners entry or use a command: ref`)
      else if (r.status !== 0) errs.push(`ac: task ${t.id} ${a.id}: runner check failed for ${file}: ${(r.error?.message || r.stderr || `exit ${r.status}`).trim().split('\n')[0]}`)
    }
  }
  return errs
}

const lintEpic = (designMd) => {
  const readme = join(epicDir, 'README.md')
  return [
    ...(existsSync(readme) ? lintReadme(readFileSync(readme, 'utf8')) : ['epic: missing README.md']),
    ...lintTaskFiles(),
    ...(ledger === undefined ? ['approvals: missing approvals.json in the epic directory'] : []),
    ...(designMd !== undefined ? lintDesign(designMd) : []),
    ...(deriveError ? [deriveError] : lintAc(tasks, { require: true })),
    ...lintCheck(),
    ...(deriveError ? [] : lintRefRunners()),
  ]
}

const agent = async () => {
  throw new Error('VALIDATION_OK')
}
const script = fileURLToPath(new URL('./plan-execute.js', import.meta.url))
// plan-execute's agent calls swallow a throw per task, so reaching the first agent is read
// from the recorded calls, not from the probe's own throw.
// --epic: the per-repo overlapIgnore (built-in doc globs plus the repo's config) goes to the harness run.
const overlapIgnore = []
if (epicMode) {
  for (const repo of new Set(tasks.map((t) => t.repo).filter(Boolean))) {
    const r = spawnSync('python3', [WORKBENCH_PY, 'config', '--plans-root', plansRoot, '--repo-name', repo], { encoding: 'utf8' })
    if (r.status !== 0) fail(`workbench config for ${repo}: ${(r.stderr.trim().split('\n')[0] || 'failed')}`)
    for (const g of JSON.parse(r.stdout).overlapIgnore || []) if (!overlapIgnore.includes(g)) overlapIgnore.push(g)
  }
}
const harness = async (extra = {}) => {
  const r = await runWorkflow(script, { args: { tasks, existing, doNotBuild, overlapIgnore, name: 'lint', brief: { what: '(lint)', how: '(lint)', why: '(lint)' }, ...extra }, agent })
  return r.calls.length && !r.error ? { ...r, error: new Error('VALIDATION_OK') } : r
}
const passed = (error) => Boolean(error && String(error.message).includes('VALIDATION_OK'))
// The tasks first, without the ledger, so the ledger lint below reports every
// entry's failures; then plan-execute's own ledger validation on {id, text, tasks}.
const { error } = deriveError ? { error: null } : await harness()
if (epicMode) {
  const designFile = join(epicDir, 'design.md')
  const designMd = existsSync(designFile) ? readFileSync(designFile, 'utf8') : undefined
  const ledgerRun = ledger && !deriveError && passed(error) ? await harness({ approvals: ledger.map(({ id, text, tasks: ts }) => ({ id, text, tasks: ts })) }) : null
  const errs = [
    ...(deriveError || passed(error) ? [] : [error ? error.message : 'plan-execute finished without reaching an agent']),
    ...lintEpic(designMd),
    ...(ledger ? lintApprovals(ledger, designMd) : []),
    ...(ledgerRun && !passed(ledgerRun.error) ? [ledgerRun.error ? ledgerRun.error.message : 'plan-execute finished without reaching an agent'] : []),
  ]
  if (errs.length) fail(errs.join('\n'))
  // Split hint next to the 8-file rule; a warning, never a failure.
  for (const t of tasks) if (t.estimate > MAX_ESTIMATE_MIN) console.error(`warning: task ${t.id}: estimate ${t.estimate} > ${MAX_ESTIMATE_MIN} minutes; consider splitting`)
  console.log(`ok: ${tasks.length} task(s), epic checked, approvals checked${designMd === undefined ? '' : ', design checked'}`)
} else if (passed(error)) {
  const designMd = designPath ? readText(designPath) : undefined
  const ledgerRun = ledger ? await harness({ approvals: ledger.map(({ id, text, tasks: ts }) => ({ id, text, tasks: ts })) }) : null
  const errs = [
    ...(planPath ? lintPlan(readText(planPath), designMd) : []),
    ...(ledger ? lintApprovals(ledger, designMd) : []),
    ...(ledgerRun && !passed(ledgerRun.error) ? [ledgerRun.error ? ledgerRun.error.message : 'plan-execute finished without reaching an agent'] : []),
  ]
  if (errs.length) fail(errs.join('\n'))
  const checked = [planPath && 'plan checked', ledger && 'approvals checked', designPath && 'design checked'].filter(Boolean)
  const suffix = checked.map((c) => `, ${c}`).join('')
  console.log(`ok: ${tasks.length} task(s)${suffix}`)
} else {
  fail(error ? error.message : 'plan-execute finished without reaching an agent')
}
