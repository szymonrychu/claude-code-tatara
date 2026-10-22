export const meta = {
  name: 'plan-execute',
  description: 'Execute an approved plan across worktrees: implement each task (queued on its dependencies, shared parts built once by their owner), review->fix (max 3 rounds, then escalate), then one scope audit of delivered vs planned plus a cross-task duplicate sweep',
  whenToUse: 'Phase 4 of start-development, after the single approval gate and after the per-task worktrees exist. Deterministic orchestration: the script drives the implement/review/audit loop, so it cannot lose the thread mid-run. Pass the approved plan tasks via args - the script has no filesystem access.',
  phases: [
    { title: 'Implement', detail: 'one agent per plan task, writing into its worktree; each task starts when its dependsOn finish clean; context-ceiling handoffs get fresh continuations' },
    { title: 'Verify', detail: 'a fresh agent re-runs the verification command on the committed HEAD after every implementer and fixer, and scans the diff for debt markers' },
    { title: 'Review', detail: 'review -> fix, at most 3 rounds; repeats and external blockers escalate' },
    { title: 'Scope audit', detail: 'adversarial check that every planned item actually landed' },
    { title: 'Land', detail: 'with args.epic and args.mainCheckout, each released task lands on the epic branch, one at a time, before its dependents start' },
    { title: 'Merge', detail: 'a clean remediation is merged forward into its same-repo dependents before the re-audit' },
  ],
}

// ---------------------------------------------------------------- args
// args = {
//   overlapIgnore: [glob]?       shared files matching a glob never trip the same-repo overlap rule
//                                (default none; validate-tasks --epic fills it from workbench config)
//   name:        string?         run name, the prefix of every agent label
//                                (default 'pe'); a lowercase slug
//   tasks:       [{ id, title, repo, worktree, requirement, value, files?, notes?,
//                   value,         REQUIRED non-empty string: what this task is worth to
//                                  the project; every prompt for the task carries it as
//                                  "Value of this task: <value>"
//                   short?,        very short title for agent labels; derived
//                                  from the title when absent
//                   verify?,       targeted test + lint command for this task
//                   model?,        'opus' to raise implement + fix, only for the
//                                  most problematic tasks (default sonnet). Opus
//                                  work is reviewed and audited on opus only
//                   size?,         'large' lifts the MAX_TASK_FILES cap on `files`;
//                                  needs sizeReason
//                   sizeReason?,   why this task cannot be split (non-empty string,
//                                  required with size: 'large')
//                   review?,       true forces review on a small task, false skips it
//                   owns?,         shared parts only this task may build (kebab names
//                                  from the plan's shared-parts map)
//                   uses?,         shared parts it consumes; one another task owns
//                                  needs that task in dependsOn (directly or not)
//                   dependsOn? }]  task ids that must finish clean first; the task
//                                  starts the moment they do and merges their branches
//   brief:       { what, how, why }  REQUIRED, three non-empty strings: the project
//                                in one sentence each (what it is, how it is built, why it
//                                exists). Every agent prompt carries it as "Project brief:"
//   planText:    string          THIS run's scope, for the scope auditor
//   lenses:      [string]        optional review lenses; defaults below
//   existing:    [{ name, where }]  optional parts already in the codebase (both
//                                strings); every prompt lists them as "reuse, do
//                                not rebuild" and the audit flags a rebuild as a
//                                duplicate
//   doNotBuild:  [{ name, reason }]  optional things research found unnecessary (both
//                                strings); impl, fix, review and the first audit prompt
//                                list them, and the audit flags building one as `missing`
//   contextPack: string          optional path to the discovery brief; every
//                                implementer and reviewer reads it first
//   designDoc:   string          optional path to the design doc; every impl, fix,
//                                review and audit prompt carries "Spec (design doc): <path>"
//   planDoc:     string          optional path to the plan; the same four prompts carry
//                                "Plan: <path> - read the section for your task, not the
//                                whole file."
//   verifierAgent: string|null? the agent type the verifier runs as (default 'workbench:verifier'; null runs it as a plain prompt role)
//   tasks[].forkPoint  a SHA (optional): the <epic> commit a task landed from in an earlier run;
//                                seeds its fork point. A landing in this run records the base merge.py
//                                reports as the fork point. Once a task has one, every diff base
//                                in its prompts (reviewer, verifier --base, TDD revert recipe,
//                                remediation and audit re-review, forward-merge re-verify) is that
//                                SHA, so a landed task's diff stays exactly its own change. The
//                                return carries `landed: [{id, head, forkPoint}]` and tasks[].forkPoint.
//   baseRef:     string?         the ref a task's branch forked from (default 'main'); the
//                                independent verifier diffs against its merge-base to scan
//                                for debt markers
//   approvals:   [{ id, text, tasks }]  optional approval ledger: id and text non-empty
//                                strings, tasks a non-empty array of task ids in this run
//                                (a remediation run keys on its root id). Impl and fix
//                                prompts of a mapped task name its items; an `undelivered`
//                                entry on any task is a finding, only a deliverable `blocked`
//                                (reason, whoCanClear) stops it; the audit reports every
//                                item by id; the return carries each item's status
//   epic:        string?         the epic slug this run executes; it turns the per-run audit
//                                off by default, since the epic-close audit covers scope once
//   audit:       'run'|'off'?    the per-run scope audit and its remediation (default 'run',
//                                or 'off' with args.epic); 'off' dispatches neither
//                                With args.epic: args.name must equal it, every task's short equals
//                                its id, and its worktree ends in <epic>-<id>[/<repo>]; the return
//                                carries `epic`.
//   auditOnly:   true?           epic close: no implement, verify or review. One audit over the
//                                given tasks (worktree, branch?, verifiedHead?, ac?,
//                                acsForAudit? - as `ticket.py tasks` emits them), returning
//                                {auditOnly: true, gaps, approvals, duplicates}; no remediation
//   epicReadme:  string          required with auditOnly: the epic README path, whose Goals
//                                and Non-goals are the definition of done
//   rulingsFile: string?         the absolute path of <epic dir>/rulings.json in the main checkout
//                                (`ticket.py rule` writes it). At each wave boundary one haiku agent
//                                reads it; an accept ruling on a verified escalated task releases its
//                                dependents mid-run. The return then carries `rulingsIgnored`
//   mainCheckout: string?        the absolute path of the main checkout (`ticket.py run` emits it).
//                                With args.epic, and not auditOnly, it turns landing on: every
//                                released task is landed on args.baseRef (the epic branch) by one
//                                workbench:worktree-merger agent running merge.py from this checkout,
//                                one landing at a time, before any dependent counts it as released.
//                                Dependents then merge args.baseRef once instead of each dependency
//                                branch. A failed landing ends the task 'land-failed' and fails its
//                                dependents; the return carries `landed: [{id, head, forkPoint}]`
// }
const ARGS = (typeof args !== 'undefined' && args) || {}
// Workflow agents' shells have no CLAUDE_PLUGIN_ROOT, so every script path is built from this.
const PLUGIN_ROOT = ARGS.pluginRoot
if (typeof PLUGIN_ROOT !== 'string' || !PLUGIN_ROOT.startsWith('/')) {
  throw new Error('plan-execute: args.pluginRoot must be an absolute path (named-copy.mjs embeds it)')
}
const TASKS = ARGS.tasks || []
const PLAN_TEXT = ARGS.planText || ''
const LENSES = ARGS.lenses || ['correctness', 'requirements-coverage']
const CONTEXT_PACK = ARGS.contextPack || ''
const NAME = ARGS.name || 'pe'
const EXISTING = ARGS.existing || []
const DO_NOT_BUILD = ARGS.doNotBuild || []
const DESIGN_DOC = ARGS.designDoc || ''
const PLAN_DOC = ARGS.planDoc || ''
const BASE_REF = ARGS.baseRef || 'main'
// A landed task's fork point (by root id): the epic commit it landed from. After landing,
// merge-base(HEAD, <epic>) is the task's own HEAD, so its diffs are taken from here instead.
const FORK_POINTS = new Map()
for (const x of Array.isArray(ARGS.tasks) ? ARGS.tasks : []) if (x && x.forkPoint) FORK_POINTS.set(x.rootId || x.id, String(x.forkPoint))
const forkPointOf = (t) => FORK_POINTS.get(t.rootId || t.id)
// The one diff base: the fork point when recorded, else the merge-base with the base ref.
const diffBase = (t, ref = false) => forkPointOf(t) || (ref ? BASE_REF : `$(git merge-base HEAD ${BASE_REF})`)
const VERIFIER_AGENT = ARGS.verifierAgent === undefined ? 'workbench:verifier' : ARGS.verifierAgent
const BRIEF = ARGS.brief || {}
const APPROVALS = ARGS.approvals || []
const EPIC = ARGS.epic || ''
const AUDIT_MODE = ARGS.audit === undefined ? (EPIC ? 'off' : 'run') : ARGS.audit
const AUDIT_ONLY = Boolean(ARGS.auditOnly === true)
const EPIC_README = ARGS.epicReadme || ''
const RULINGS_FILE = ARGS.rulingsFile === undefined ? '' : ARGS.rulingsFile
const MAIN_CHECKOUT = ARGS.mainCheckout === undefined ? '' : ARGS.mainCheckout
// In-run landing (D4): only an epic run that names its main checkout, never the epic-close audit.
const LANDING = Boolean(EPIC && MAIN_CHECKOUT && !AUDIT_ONLY)
// Every audit runs as this agent type: its method lives in agents/scope-auditor.md,
// the prompt carries only the inputs.
const SCOPE_AUDITOR = 'workbench:scope-auditor'
// Every implementation and fixer call runs as this agent type: its method lives in
// agents/implementer.md, the prompt carries only the per-call inputs. The per-call
// model still wins over the agent's default.
const IMPLEMENTER = 'workbench:implementer'
// Every review call runs as this agent type: its method lives in agents/reviewer.md,
// which reads skills/start-review/references/review-checklist.md, the one checklist
// every reviewer in this plugin applies; the prompt carries only the per-call inputs.
const REVIEWER = 'workbench:reviewer'

// The review loop's hard cap. Every real catch measured came from round 1 or 2;
// rounds 3+ only ever re-raised something no fixer could clear.
const MAX_REVIEW_ROUNDS = 3
// Every finding the script creates (not the reviewer) carries one of these as its
// `gate`, naming its source; a gate finding is one with a gate tag. A round whose
// findings are all gate findings needs no LLM review once the last one was clean.
// Mechanical gates are fixed by bookkeeping; a work gate's fix writes code, so it is re-read.
const MECHANICAL_GATES = ['verify-failed', 'dirty-tree', 'parking', 'tests-changed', 'no-red-evidence', 'tdd-skipped']
const WORK_GATES = ['debt-marker', 'ac-unmet', 'undelivered', 'approved-item']
const GATES = [...MECHANICAL_GATES, ...WORK_GATES, 'review-shallow']
const isGate = (f) => GATES.includes(f && f.gate)
// Bookkeeping gates: a task whose only open findings carry one of these, and whose
// final verification passed clean on its HEAD, releases its dependents.
const PROCESS_GATES = ['no-red-evidence', 'tdd-skipped', 'review-shallow']
const isProcessFinding = (f) => PROCESS_GATES.includes(f && f.gate)
// verified() already folds clean in: the verifier's passed is stored as passed && clean.
const processOnly = (impl, findings) =>
  verified(impl) && !isBlocked(impl) && Array.isArray(findings) && findings.length > 0 && findings.every(isProcessFinding)
// Medium-only results (design D8): verified, not blocked, and every open finding (one triage
// did not reject as false) is a reviewer's medium with no gate. It releases its dependents
// and still escalates for a ruling. Every script-made gate finding is high and carries a gate.
const openFindings = (findings) => (Array.isArray(findings) ? findings.filter((f) => f.verdict !== 'false') : [])
const mediumOnly = (impl, findings) => {
  const open = openFindings(findings)
  return verified(impl) && !isBlocked(impl) && open.length > 0 && open.every((f) => f.severity === 'medium' && !f.gate)
}
// Per-task review tiers, lowest to highest. See reviewTier().
const TIERS = ['skip', 'light', 'full', 'panel']
// A changed path matching this is never below full.
const RISK_PATH = /auth|secret|sops|rbac|migration|lock|mutex|thread|concurren|\.github\/|\.gitlab-ci|hooks\/|permission/i
// An AC counts as evidenced for a skip only through one of these kinds.
const SKIP_EVIDENCE = ['test', 'symbol', 'command', 'doc-section']
const SKIP_MAX_ADDED = 150
const SKIP_MAX_FILES = 4
// More files than this in one task is a task that should be split (by test
// file), unless it declares size: 'large' with a reason.
const MAX_TASK_FILES = 8

// Fail before any agent is spent. A `files` string instead of an array once made
// every pipeline throw and ran a whole wave through remediation.
const AC_KINDS = ['test', 'symbol', 'command', 'doc-section', 'judgement']
if (!TASKS.length) throw new Error('plan-execute: args.tasks is empty - nothing to execute')
if (!['run', 'off'].includes(AUDIT_MODE)) throw new Error("plan-execute: args.audit must be 'run' or 'off'")
if (AUDIT_ONLY && !(typeof EPIC_README === 'string' && EPIC_README.trim())) {
  throw new Error('plan-execute: args.auditOnly needs args.epicReadme (the epic README path)')
}
if (ARGS.rulingsFile !== undefined && !(typeof RULINGS_FILE === 'string' && RULINGS_FILE.startsWith('/') && RULINGS_FILE.endsWith('/rulings.json'))) {
  throw new Error('plan-execute: args.rulingsFile must be the absolute path of <epic dir>/rulings.json')
}
if (ARGS.mainCheckout !== undefined && !(typeof MAIN_CHECKOUT === 'string' && MAIN_CHECKOUT.startsWith('/'))) {
  throw new Error('plan-execute: args.mainCheckout must be the absolute path of the main checkout')
}
if (!['what', 'how', 'why'].every((k) => typeof BRIEF[k] === 'string' && BRIEF[k].trim())) {
  throw new Error('plan-execute: args.brief needs what, how and why')
}
for (const t of TASKS) {
  for (const k of ['id', 'title', 'repo', 'worktree', 'requirement', 'value']) {
    if (typeof t[k] !== 'string' || !t[k]) throw new Error(`plan-execute: task ${t.id || '?'} needs a string ${k === 'value' ? k : `\`${k}\``}`)
  }
  if (t.files !== undefined && !(Array.isArray(t.files) && t.files.every((f) => typeof f === 'string'))) {
    throw new Error(`plan-execute: task ${t.id} \`files\` must be an array of strings`)
  }
  if (t.ac !== undefined) {
    if (!Array.isArray(t.ac)) throw new Error(`plan-execute: task ${t.id} \`ac\` must be an array of {id, text, evidence}`)
    const seen = new Set()
    for (const [i, a] of t.ac.entries()) {
      const nonEmpty = (v) => typeof v === 'string' && v.trim() !== ''
      if (!a || typeof a !== 'object' || !nonEmpty(a.id)) throw new Error(`plan-execute: task ${t.id} ac entry ${i} needs a non-empty \`id\``)
      if (seen.has(a.id)) throw new Error(`plan-execute: task ${t.id} has a duplicate AC id ${a.id}`)
      seen.add(a.id)
      if (!nonEmpty(a.text)) throw new Error(`plan-execute: task ${t.id} AC ${a.id} needs a non-empty \`text\``)
      const ev = a.evidence
      if (!ev || !AC_KINDS.includes(ev.kind)) throw new Error(`plan-execute: task ${t.id} AC ${a.id} evidence.kind must be one of ${AC_KINDS.join(', ')}`)
      if (ev.kind !== 'judgement' && !nonEmpty(ev.ref)) throw new Error(`plan-execute: task ${t.id} AC ${a.id} needs a non-empty evidence.ref for kind ${ev.kind}`)
    }
  }
  if (t.size === 'large') {
    if (typeof t.sizeReason !== 'string' || !t.sizeReason.trim()) {
      throw new Error(`plan-execute: task ${t.id} is size 'large' but has no sizeReason`)
    }
  } else if ((t.files || []).length > MAX_TASK_FILES) {
    throw new Error(`plan-execute: task ${t.id} lists ${t.files.length} files (max ${MAX_TASK_FILES}); split it by test file, or set size: 'large' with a sizeReason`)
  }
}
if (new Set(TASKS.map((t) => t.id)).size !== TASKS.length) throw new Error('plan-execute: task ids must be unique')
if (!Array.isArray(EXISTING) || !EXISTING.every((e) => e && typeof e.name === 'string' && typeof e.where === 'string')) {
  throw new Error('plan-execute: args.existing must be an array of {name, where} strings')
}
if (!Array.isArray(DO_NOT_BUILD) || !DO_NOT_BUILD.every((e) => e && typeof e.name === 'string' && typeof e.reason === 'string')) {
  throw new Error('plan-execute: args.doNotBuild must be an array of {name, reason} strings')
}

// The approval ledger: every entry well-formed, ids unique, every task in this run.
const nonEmpty = (v) => typeof v === 'string' && v.trim() !== ''
if (!Array.isArray(APPROVALS) || !APPROVALS.every((a) => a && nonEmpty(a.id) && nonEmpty(a.text) && Array.isArray(a.tasks) && a.tasks.length && a.tasks.every((x) => typeof x === 'string'))) {
  throw new Error('plan-execute: args.approvals must be an array of {id, text, tasks}')
}
for (const [i, a] of APPROVALS.entries()) {
  if (APPROVALS.findIndex((b) => b.id === a.id) !== i) throw new Error(`plan-execute: duplicate approval id ${a.id}`)
  for (const x of a.tasks) {
    if (!TASKS.some((t) => t.id === x)) throw new Error(`plan-execute: approval ${a.id} names task ${x} which is not in this run`)
  }
}
// Ids of the approved items a task (or a task id) delivers; a remediation run keys on its root.
const approvalsFor = (t) => {
  const id = typeof t === 'string' ? t : t.rootId || t.id
  return APPROVALS.filter((a) => a.tasks.includes(id)).map((a) => a.id)
}

// Shared parts and dependencies. A past run split
// tasks by card, so two parallel tasks each built their own reader for the same
// rule, differently. Every shared part has one owner, and a task that uses it
// waits for that owner instead of building its own.
const strings = (v) => Array.isArray(v) && v.every((x) => typeof x === 'string')
for (const t of TASKS) {
  for (const k of ['owns', 'uses', 'dependsOn']) {
    if (t[k] !== undefined && !strings(t[k])) throw new Error(`plan-execute: task ${t.id} \`${k}\` must be an array of strings`)
  }
  for (const d of t.dependsOn || []) {
    if (d === t.id || !TASKS.some((x) => x.id === d)) throw new Error(`plan-execute: task ${t.id} dependsOn unknown task ${d}`)
  }
}
const OWNER = new Map()
for (const t of TASKS) {
  for (const p of t.owns || []) {
    if (OWNER.has(p)) throw new Error(`plan-execute: shared part ${p} is owned by both ${OWNER.get(p)} and ${t.id}; give it one owner`)
    OWNER.set(p, t.id)
  }
}
const byId = new Map(TASKS.map((t) => [t.id, t]))
// Transitive dependencies per task, memoised; throws on a cycle.
const ANCESTORS = new Map()
function ancestors(id, path = []) {
  if (path.includes(id)) throw new Error(`plan-execute: dependency cycle ${[...path, id].join(' -> ')}`)
  if (!ANCESTORS.has(id)) {
    const seen = new Set()
    for (const d of byId.get(id).dependsOn || []) {
      seen.add(d)
      for (const a of ancestors(d, [...path, id])) seen.add(a)
    }
    ANCESTORS.set(id, seen)
  }
  return ANCESTORS.get(id)
}
for (const t of TASKS) {
  const up = ancestors(t.id)
  for (const p of t.uses || []) {
    const owner = OWNER.get(p)
    if (owner && owner !== t.id && !up.has(owner)) {
      throw new Error(`plan-execute: task ${t.id} uses ${p}, which ${owner} owns; add ${owner} to its dependsOn`)
    }
  }
}

// Two parallel tasks editing one file in one repo collide at merge. They may
// share a file only when one is an ancestor of the other.
// Files matching args.overlapIgnore (doc files) are skipped; the list is the caller's, none by default.
// Same semantics as overlap_ignored in scripts/lib/workbench.py: `**/` spans zero or more dirs,
// a slash-free glob matches the basename.
const OVERLAP_IGNORE = ARGS.overlapIgnore ?? []
if (!Array.isArray(OVERLAP_IGNORE) || OVERLAP_IGNORE.some((g) => typeof g !== 'string')) {
  throw new Error('plan-execute: args.overlapIgnore must be an array of glob strings')
}
const globRe = (pat) => {
  let out = ''
  for (let i = 0; i < pat.length; ) {
    if (pat.startsWith('**/', i)) { out += '(?:.*/)?'; i += 3 }
    else if (pat.startsWith('**', i)) { out += '.*'; i += 2 }
    else if (pat[i] === '*') { out += '[^/]*'; i++ }
    else if (pat[i] === '?') { out += '[^/]'; i++ }
    else { out += pat[i].replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); i++ }
  }
  return new RegExp(`^${out}$`)
}
const IGNORE_RES = OVERLAP_IGNORE.map((g) => ({ slash: g.includes('/'), re: globRe(g) }))
const overlapIgnored = (f) => {
  const path = f.startsWith('./') ? f.slice(2) : f
  const base = path.slice(path.lastIndexOf('/') + 1)
  return IGNORE_RES.some((g) => g.re.test(g.slash ? path : base))
}
for (const [i, a] of TASKS.entries()) {
  for (const b of TASKS.slice(i + 1)) {
    if (a.repo !== b.repo || ancestors(a.id).has(b.id) || ancestors(b.id).has(a.id)) continue
    const shared = (a.files || []).find((f) => (b.files || []).includes(f) && !overlapIgnored(f))
    if (shared) throw new Error(`plan-execute: tasks ${a.id} and ${b.id} both list ${shared}; order them with dependsOn or give the file one owner`)
  }
}

// Agent labels are <name>:<role>:<short>, so a run's agents read as what they
// are working on instead of impl:G1 / rev:G3. Slugs keep ':' '#' '+' free for
// the label's own separators.
const SLUG = /^[a-z0-9][a-z0-9-]*$/
if (typeof NAME !== 'string' || !SLUG.test(NAME)) throw new Error(`plan-execute: args.name must be a lowercase slug, got ${JSON.stringify(NAME)}`)
for (const t of TASKS) {
  if (t.short !== undefined && (typeof t.short !== 'string' || !SLUG.test(t.short))) {
    throw new Error(`plan-execute: task ${t.id} \`short\` must be a lowercase slug, got ${JSON.stringify(t.short)}`)
  }
}
const deriveShort = (title) =>
  title.toLowerCase().split(/[^a-z0-9]+/).filter(Boolean).slice(0, 3).join('-').slice(0, 20).replace(/-+$/, '') || 'task'
const derived = TASKS.map((t) => t.short || deriveShort(t.title))
// An epic run names everything after the ticket: run = epic slug, task short = task id,
// worktree = <epic>-<id> (optionally with the repo subdir), so a tree maps to one ticket.
// Separator of the pre-single-hyphen trees; ticket.py worktrees keeps a live one's record.
const LEGACY_SEP = '--'
if (EPIC) {
  if (!SLUG.test(EPIC) || NAME !== EPIC) throw new Error(`plan-execute: args.name must equal args.epic (${EPIC})`)
  for (const [i, t] of TASKS.entries()) {
    if (derived[i] !== t.id) throw new Error(`plan-execute: task ${t.id} short must equal its id, got ${JSON.stringify(derived[i])}`)
    const want = `${EPIC}-${t.id}`
    const legacy = `${EPIC}${LEGACY_SEP}${t.id}`
    const wt = t.worktree.replace(/\/+$/, '')
    const endsIn = (tail) => wt === tail || wt.split('/').slice(-tail.split('/').length).join('/') === tail
    const tails = (name) => [name, `${name}/${t.repo}`]
    if (tails(want).some(endsIn)) {
      if (want.length > 57) throw new Error(`plan-execute: task ${t.id} worktree name ${want} is ${want.length} chars; the cap is 57`)
      continue
    }
    // A live tree of an epic claimed before the single-hyphen names keeps its recorded legacy name.
    if (tails(legacy).some(endsIn)) {
      if (legacy.length > 58) throw new Error(`plan-execute: task ${t.id} worktree name ${legacy} is ${legacy.length} chars; the cap is 58`)
      continue
    }
    throw new Error(`plan-execute: task ${t.id} worktree ${t.worktree} must be ${want}`)
  }
}
for (const [i, t] of TASKS.entries()) {
  const clash = derived.filter((d) => d === derived[i]).length > 1
  t.short = clash ? `${derived[i]}-${t.id.toLowerCase().replace(/[^a-z0-9]+/g, '-')}` : derived[i]
}
const label = (role, t) => `${NAME}:${role}:${t.short}`
const TASK_IDS = TASKS.map((t) => t.id)

function targetedVerify(t) {
  return [
    'Run targeted tests, not the full suite:',
    t.verify
      ? `  ${t.verify}`
      : '  the test files you added or touched, plus the repo\'s lint command.',
    'The full suite runs once over the integrated branch before merge. A full run here costs',
    'minutes per agent and contends with the sibling agents running theirs.',
  ].join('\n')
}

// Context ceiling. The Workflow runtime's agent() takes no turn or token budget
// (its options are label/phase/schema/model/effort/isolation/agentType), so the
// ceiling (~300k context or 150 tool calls, stated in agents/implementer.md) is
// enforced by the agent itself, and the script enforces the rest:
// every handoff gets a fresh continuation, bounded by MAX_CONTINUATIONS, then
// escalation. peer-token-review 2026-09-27: implement agents start near 50k and
// ran a median 172 turns at a 229k mean / 353k peak context, so ~150 tool calls
// is where a typical agent crosses 300k. Context above 300k was 4.5B of 19B
// tokens; cost scales with turns x context.
const MAX_CONTINUATIONS = 2

const NOTES_BY_GREP =
  'status.md and MEMORY.md files are large: grep them by topic (the task id, the mechanic, the file ' +
  'name) and read only the matching lines - never read them whole.'

const contextPackLine = () =>
  CONTEXT_PACK ? `Read the discovery brief first, it has the verified facts about this codebase: ${CONTEXT_PACK}` : ''

// The design and plan docs, for the impl, fix, review and audit prompts.
const docLines = () => [
  ...(DESIGN_DOC ? [`Spec (design doc): ${DESIGN_DOC}`] : []),
  ...(PLAN_DOC ? [`Plan: ${PLAN_DOC} - read the section for your task, not the whole file.`] : []),
]

const SPLIT_HINT = 'split the remaining conditions into tasks of at most 8 files each'

// ---------------------------------------------------------------- schemas
// An external blocker no agent in this run can clear; reviewers and deliverables share it.
const blockedSchema = (description) => ({
  type: 'object',
  required: ['reason', 'whoCanClear'],
  properties: { reason: { type: 'string' }, whoCanClear: { type: 'string' } },
  description,
})

const DELIVERABLE = {
  type: 'object',
  required: ['taskId', 'complete', 'summary', 'filesChanged', 'branch', 'tests', 'verification', 'undelivered', 'discovered'],
  properties: {
    taskId: { type: 'string' },
    complete: { type: 'boolean', description: 'true only if EVERY requirement of this task is implemented AND verification passed' },
    summary: { type: 'string' },
    branch: { type: 'string', description: 'the branch you committed to inside your own worktree' },
    filesChanged: { type: 'array', items: { type: 'string' } },
    tests: {
      type: 'object',
      required: ['added', 'wroteTestFirst'],
      description: 'TDD evidence. A behaviour change with no test is an incomplete task.',
      properties: {
        added: { type: 'array', items: { type: 'string' }, description: 'test files added or extended' },
        wroteTestFirst: { type: 'boolean', description: 'true if the test was written and seen failing before the implementation' },
        note: { type: 'string', description: 'if wroteTestFirst is false, why' },
        red: {
          type: 'object',
          required: ['command', 'output'],
          properties: { command: { type: 'string' }, output: { type: 'string' } },
          description: 'the failing run before the implementation: the command and the real tail naming the failing test',
        },
      },
    },
    acs: {
      type: 'array',
      description: 'your own claim per acceptance condition of the task; the verifier checks it and your claim never outranks it',
      items: {
        type: 'object',
        required: ['id', 'met'],
        properties: { id: { type: 'string' }, met: { type: 'boolean' }, ref: { type: 'string', description: 'file:line or test name that shows it' } },
      },
    },
    acEvidence: {
      type: 'object',
      description: 'optional: maps each test: AC id to the final file::name of the test that proves it',
      additionalProperties: { type: 'string' },
    },
    verification: {
      type: 'object',
      required: ['command', 'passed', 'evidence'],
      description: 'You MUST have actually run this. Never assert a pass you did not observe.',
      properties: {
        command: { type: 'string' },
        passed: { type: 'boolean' },
        evidence: { type: 'string', description: 'the tail of the real output, including the pass/fail summary line' },
      },
    },
    status: {
      type: 'string',
      enum: ['complete', 'incomplete', 'handoff'],
      description: '"handoff" when you stopped at the context ceiling and committed WIP; the other fields keep their meaning',
    },
    handoff: {
      type: 'object',
      required: ['doneSoFar', 'remaining', 'nextStep', 'testState', 'wipCommit'],
      description: 'set ONLY with status "handoff": what a fresh continuation agent needs',
      properties: {
        doneSoFar: { type: 'string', description: 'cumulative, including earlier handoffs' },
        remaining: { type: 'array', items: { type: 'string' }, description: 'every acceptance condition not yet met' },
        nextStep: { type: 'string' },
        testState: { type: 'string', description: 'the last real test run and what fails' },
        wipCommit: { type: 'string', description: 'sha of the WIP: commit on your branch' },
        readSet: {
          type: 'array',
          description: 'files and line ranges you read that the successor would otherwise re-read',
          items: {
            type: 'object',
            required: ['path'],
            properties: {
              path: { type: 'string' },
              lines: { type: 'string', description: 'line ranges read, e.g. 1-120,300-340; omit when read whole' },
              note: { type: 'string', description: 'what was learned, at most 25 words' },
            },
          },
        },
      },
    },
    provides: {
      type: 'array',
      description:
        'a reusable part you built that the plan did not list and other tasks plausibly need (a ' +
        'reader, helper, or subsystem); tasks that start later are told to reuse it',
      items: {
        type: 'object',
        required: ['name', 'where'],
        properties: {
          name: { type: 'string', description: 'kebab name of the part' },
          where: { type: 'string', description: 'file:symbol' },
        },
      },
    },
    reimplemented: {
      type: 'array',
      description:
        'a shared part another task owns or built that you nonetheless built your own version of; ' +
        'only when reuse genuinely could not work, with the reason',
      items: {
        type: 'object',
        required: ['name', 'why'],
        properties: { name: { type: 'string' }, why: { type: 'string' } },
      },
    },
    undelivered: {
      type: 'array',
      description:
        'scope of THIS task that you did not deliver. Every entry is a high finding, approved or not; ' +
        'a gap inside your owned files is fixed now, not listed here. Empty array when everything landed.',
      items: {
        type: 'object',
        required: ['what', 'why'],
        properties: { what: { type: 'string' }, why: { type: 'string' } },
      },
    },
    discovered: {
      type: 'array',
      description:
        'a bug or gap you found outside your file ownership (another task\'s files, another repo). Never ' +
        'a finding: it becomes a new todo task in the same epic. Empty array when you found none.',
      items: {
        type: 'object',
        required: ['what', 'why'],
        properties: { what: { type: 'string' }, why: { type: 'string' }, where: { type: 'string' } },
      },
    },
    blocked: blockedSchema(
      'set ONLY for an external blocker no agent in this run can clear (a credential, a permission, a human merge); it ends the loop and escalates',
    ),
  },
}

// A task is only done when its own verification actually ran and passed.
// This is checked in code, not left to the reviewer's judgement.
function verified(d) {
  return Boolean(d && d.verification && d.verification.passed === true && d.verification.evidence)
}

// The independent verifier's report: the command re-run on the committed HEAD,
// not the implementer's own claim.
const VERIFY = {
  type: 'object',
  required: ['head', 'clean', 'command', 'passed', 'evidence'],
  properties: {
    head: { type: 'string', description: 'output of git rev-parse HEAD' },
    clean: { type: 'boolean', description: 'true only when git status --porcelain printed nothing' },
    command: { type: 'string', description: 'the exact command you ran' },
    exit: { type: 'integer', description: "the script's exit field, relayed as is; pass is exit 0" },
    passed: { type: 'boolean', description: "the script's passed field, relayed as is" },
    evidence: { type: 'string', description: 'the real output tail, including the pass/fail summary line; at most 150 words' },
    debtMarkers: {
      type: 'array',
      description: 'debt markers on lines the diff adds',
      items: {
        type: 'object',
        required: ['file', 'line', 'marker'],
        properties: { file: { type: 'string' }, line: { type: 'integer' }, marker: { type: 'string' } },
      },
    },
    changed: {
      type: 'array',
      description: 'git diff --name-status from the base to HEAD, the whole task diff',
      items: {
        type: 'object',
        required: ['file', 'status'],
        properties: { file: { type: 'string' }, status: { type: 'string' } },
      },
    },
    changedSincePrevious: {
      type: 'array',
      description: 'git diff --name-status from the previous verified head to HEAD; fix rounds only',
      items: {
        type: 'object',
        required: ['file', 'status'],
        properties: { file: { type: 'string' }, status: { type: 'string' } },
      },
    },
    parking: {
      type: 'array',
      description: 'added lines that defer part of the task to later',
      items: {
        type: 'object',
        required: ['file', 'line', 'text'],
        properties: { file: { type: 'string' }, line: { type: 'integer' }, text: { type: 'string' }, reason: { type: 'string' } },
      },
    },
    acs: {
      type: 'array',
      description: 'the script verdict per acceptance condition: met true, false or null (left to the auditor)',
      items: {
        type: 'object',
        required: ['id'],
        properties: { id: { type: 'string' }, met: { type: ['boolean', 'null'] }, exit: { type: ['integer', 'null'], description: 'the script exit field of a command AC' }, how: { type: 'string' }, plausible: { type: ['string', 'null'] } },
      },
    },
    diffstat: { type: 'object', description: 'the script diffstat, relayed as is' },
    tierHint: { type: ['string', 'null'] },
    triageUsage: {
      type: 'object',
      description: 'the script triage cost, relayed as is',
      properties: { calls: { type: 'integer' }, input_tokens: { type: 'integer' }, output_tokens: { type: 'integer' } },
    },
    tdd: {
      type: ['object', 'null'],
      description: 'the revert proof, present only when --tdd-revert ran',
      properties: { ran: { type: 'boolean' }, failedOnBase: { type: ['boolean', 'null'] }, passedOnHead: { type: ['boolean', 'null'] }, files: { type: 'array', items: { type: 'string' } } },
    },
    note: { type: 'string' },
  },
}

const REVIEW = {
  type: 'object',
  required: ['clean', 'findings', 'filesRead'],
  properties: {
    clean: { type: 'boolean' },
    diffRead: { type: 'boolean', description: 'true when your first step, the one git diff of the non-test changed files, ran' },
    diffLines: { type: 'integer', description: 'lines of that git diff output; 0 or absent means nothing was read' },
    filesRead: {
      type: 'array',
      items: { type: 'string' },
      description: 'every file you opened to make the judgement, repo-relative as in filesChanged',
    },
    processGaps: {
      type: 'array',
      description: 'bookkeeping the work is missing (notes, sweeps, ratchets, approval lines); never findings',
      items: {
        type: 'object',
        required: ['what', 'where'],
        properties: { what: { type: 'string' }, where: { type: 'string' } },
      },
    },
    blocked: blockedSchema(
      'set ONLY for an external blocker no agent in this run can clear (a PR needing a human merge, a credential only the user holds, a permission the session lacks), instead of a finding; it ends the loop and goes to the orchestrator',
    ),
    declined: {
      type: 'array',
      description: 'every behaviour you chose not to judge, each with the reason',
      items: {
        type: 'object',
        required: ['what', 'why'],
        properties: { what: { type: 'string' }, why: { type: 'string' } },
      },
    },
    cannotVerify: {
      type: 'array',
      description: 'every requirement the diff and the tree cannot show (live behaviour, an external system)',
      items: { type: 'string' },
    },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        required: ['severity', 'kind', 'file', 'summary', 'requirement', 'evidence'],
        properties: {
          severity: { type: 'string', enum: ['critical', 'high', 'medium'] },
          kind: { type: 'string', enum: ['missing', 'extra', 'wrong', 'quality'] },
          file: { type: 'string' },
          line: { type: 'integer' },
          summary: { type: 'string' },
          requirement: { type: 'string', description: 'which plan requirement or correctness property this violates' },
          evidence: { type: 'string', description: 'file:line or the command output that shows it' },
        },
      },
    },
  },
}

// A forward merge of a remediated dependency into a dependent's tree.
const MERGE = {
  type: 'object',
  required: ['merged', 'conflict', 'head', 'verification'],
  properties: {
    merged: { type: 'boolean' },
    conflict: { type: 'boolean' },
    head: { type: 'string', description: 'output of git rev-parse HEAD after the merge' },
    verification: {
      type: 'object',
      required: ['command', 'passed', 'evidence'],
      properties: {
        command: { type: 'string' },
        passed: { type: 'boolean' },
        evidence: { type: 'string', description: 'the real output tail, including the pass/fail summary line' },
      },
    },
  },
}

// One task landed on the epic branch by merge.py (the land step, D4).
const LAND = {
  type: 'object',
  required: ['landed', 'head', 'conflict', 'verification', 'notes'],
  properties: {
    landed: { type: 'boolean', description: 'true only when merge.py exited 0: the epic branch now contains the task' },
    head: { type: 'string', description: 'the epic branch SHA after the landing (git rev-parse in the task tree)' },
    conflict: { type: 'boolean', description: 'true when the rebase hit a conflict you did not resolve' },
    base: { type: 'string', description: 'merge.py baseBefore: the epic branch commit the task was rebased onto and fast-forwarded from; empty when it did not land' },
    contained: { type: 'boolean', description: 'true when merge.py reported contained: true (the task is already in the epic branch); head is then the task tree HEAD' },
    verification: {
      type: 'object',
      required: ['command', 'passed', 'evidence'],
      properties: {
        command: { type: 'string', description: 'the --verify command merge.py ran' },
        passed: { type: 'boolean', description: "merge.py's verify line, relayed as is: pass is true" },
        evidence: { type: 'string', description: 'the real output tail, including the verify line' },
      },
    },
    notes: { type: 'string', description: "merge.py's notes lines, and the conflicted files when conflict is true" },
  },
}

const AUDIT = {
  type: 'object',
  required: ['complete', 'missing'],
  properties: {
    complete: { type: 'boolean' },
    missing: {
      type: 'array',
      items: {
        type: 'object',
        required: ['item', 'evidence'],
        properties: {
          item: { type: 'string' },
          taskId: { type: 'string', enum: TASK_IDS },
          evidence: { type: 'string', description: 'why you conclude it did not land' },
        },
      },
    },
    waveLevel: {
      type: 'array',
      description: 'gaps that belong to no single task (landing, merging, shared baselines)',
      items: {
        type: 'object',
        required: ['item', 'evidence'],
        properties: { item: { type: 'string' }, evidence: { type: 'string' } },
      },
    },
    outOfScope: { type: 'array', items: { type: 'string' } },
    approvals: {
      type: 'array',
      items: {
        type: 'object',
        required: ['id', 'landed', 'evidence'],
        properties: { id: { type: 'string' }, landed: { type: 'boolean' }, evidence: { type: 'string' } },
      },
    },
    duplicates: {
      type: 'array',
      description: 'the same part (reader, helper, rule, subsystem) built separately in more than one task',
      items: {
        type: 'object',
        required: ['part', 'taskIds', 'evidence'],
        properties: {
          part: { type: 'string' },
          taskIds: { type: 'array', items: { type: 'string' } },
          evidence: { type: 'string', description: 'file:symbol in each task tree' },
        },
      },
    },
  },
}

// ---------------------------------------------------------------- shared parts
// Parts an implementer built that the plan did not list, first claim wins. Tasks
// that start later are told to reuse them; the audit catches the ones that raced.
const PROVIDED = []

// A part is in a task's tree only when its owner or builder is one of the
// task's (same-repo) dependencies, merged in before it starts. Parts elsewhere
// are listed so the task does not quietly build a second one.
const existingBlock = () =>
  EXISTING.length
    ? ['Already in the codebase - reuse, do not rebuild:', ...EXISTING.map((e) => `- ${e.name}: exists at ${e.where}`)].join('\n')
    : ''

const doNotBuildBlock = () =>
  DO_NOT_BUILD.length
    ? ['Do not build - research found these unnecessary:', ...DO_NOT_BUILD.map((e) => `- ${e.name}: ${e.reason}`)].join('\n')
    : ''

function sharedParts(t) {
  const parts = [
    ...[...OWNER].map(([p, owner]) => ({ from: owner, line: `- ${p}: owned by ${owner}` })),
    ...PROVIDED.map((x) => ({ from: x.taskId, line: `- ${x.name}: built by ${x.taskId} at ${x.where}` })),
  ]
  if (!t) return parts.length || EXISTING.length ? ['Shared parts in this run:', ...parts.map((x) => x.line), existingBlock()].filter(Boolean).join('\n') : ''
  const self = t.rootId || t.id
  const up = byId.has(self) ? ancestors(self) : new Set()
  const here = (from) => up.has(from) && byId.get(from).repo === t.repo
  const inTree = parts.filter((x) => x.from !== self && here(x.from)).map((x) => x.line)
  const elsewhere = parts.filter((x) => x.from !== self && !here(x.from)).map((x) => x.line)
  const mine = t.owns || []
  if (!inTree.length && !elsewhere.length && !mine.length && !EXISTING.length) return ''
  return [
    'Shared parts in this run:',
    mine.length ? `You own: ${mine.join(', ')}. Build them once, general enough for every task that uses them.` : '',
    existingBlock(),
    inTree.length ? 'In your tree (merged from your dependencies) - reuse these:' : '',
    ...inTree,
    elsewhere.length
      ? 'Not in your tree (other tasks build them in parallel) - do not build these. If you cannot do without one, build the minimum and list it in `reimplemented` naming the owner, so integration keeps one:'
      : '',
    ...elsewhere,
  ]
    .filter(Boolean)
    .join('\n')
}

// Same-repo dependency branches get merged into the dependent's tree before it
// starts, so it builds on the owner's code instead of next to it.
const DEP_RESULTS = new Map()

// The only place a worktree and a repo are joined. A workbench worktree holds the
// repo at <worktree>/<repo>; a plain repo's worktree IS the repo root. Run 1 stalled
// on the first layout being assumed for the second, so the emitted shell decides.
function repoDir(t) {
  const nested = `${t.worktree}/${t.repo}`
  return `$(if [ -d "${nested}" ]; then echo "${nested}"; else echo "${t.worktree}"; fi)`
}

// cd into the task's checkout, assert it is the git toplevel, then merge. A mismatch
// short-circuits before the merge, so nothing lands in the main checkout.
const mergeCommand = (t, branch) =>
  `D="${repoDir(t)}"; cd "$D" && [ "$(git rev-parse --show-toplevel)" = "$(pwd -P)" ] && git merge --no-edit ${branch}`

const OWN_CHECKOUT_ONLY =
  '`git merge`, `git commit` and `git reset` run only inside this task\'s own checkout, never in the main checkout or another task\'s tree. If `git rev-parse --show-toplevel` is not that checkout, stop and report instead of running them.'

// The same-repo dependency branches dependencyLines tells the task to merge. An epic run has none,
// except a held medium-only dependency: its diff base is the epic branch, which does not carry it.
function mergedDependencyBranches(t) {
  return (t.dependsOn || []).flatMap((d) => {
    if (EPIC && !mediumHeldDep(d)) return []
    const r = DEP_RESULTS.get(d)
    const branch = r && r.impl && r.impl.branch
    return byId.get(d).repo === t.repo && branch ? [branch] : []
  })
}

// A medium-only task no ruling accepted: released to its dependents but not on the epic branch.
const mediumHeldDep = (d) => {
  const r = DEP_RESULTS.get(d)
  return Boolean(r && r.mediumOnly && !RULED_ACCEPT.has(d))
}

function dependencyLines(t) {
  const deps = t.dependsOn || []
  if (!deps.length) return ''
  const lines = ['Dependencies - these tasks finished clean before you started:']
  // Landing: every same-repo dependency is already on the epic branch, so one merge of it carries all of them.
  const landed = LANDING ? deps.filter((d) => byId.get(d).repo === t.repo && !mediumHeldDep(d)) : []
  if (landed.length) {
    lines.push(`- FIRST, before anything else, run \`${mergeCommand(t, BASE_REF)}\`. It merges ${BASE_REF}, the epic branch that carries every landed dependency: ${landed.map((d) => `${d} (${byId.get(d).title})`).join(', ')}. If it does not merge because the toplevel check fails, stop and report; do not merge anywhere else.`)
  }
  for (const d of deps) {
    if (landed.includes(d)) continue
    const r = DEP_RESULTS.get(d)
    const dt = byId.get(d)
    const branch = r && r.impl && r.impl.branch
    if (dt.repo === t.repo && branch) {
      lines.push(`- ${d} (${dt.title}): FIRST, before anything else, run \`${mergeCommand(t, branch)}\`. If it does not merge because the toplevel check fails, stop and report; do not merge anywhere else.`)
    } else {
      lines.push(`- ${d} (${dt.title}): in ${dt.repo} on branch ${branch || '(unknown)'}; it lands with the integration. Code against the interface its requirement describes; do not merge it here.`)
    }
  }
  lines.push('Build on their code. If a merge conflicts, resolve it keeping both sides\' intent and say so in your summary.')
  return lines.join('\n')
}

// ---------------------------------------------------------------- prompts
const briefBlock = () => ['Project brief:', `- What: ${BRIEF.what}`, `- How: ${BRIEF.how}`, `- Why: ${BRIEF.why}`].join('\n')
const valueLine = (t) => `Value of this task: ${t.value}`

// Helper-subagent rules per role. impl and fix keep the original lines; the
// other roles get the same permission, with the tree rule that fits them.
const HELPER_MODELS = "- Helper models per the user's table: sonnet for lookups and mechanical work, opus only for hard reasoning; cap each helper's report with a word limit."
function helperRules(role) {
  if (role === 'impl' || role === 'fix') {
    return [
      '- You MAY spawn helper subagents, and should when it genuinely gets the task done faster at',
      '  the same quality - independent files, a wide search, a mechanical sweep.',
      '- Helpers do NOT get worktrees of their own. They work inside yours and inherit its',
      '  isolation. Partition their work by file: never have two helpers editing the same file at',
      '  once, because within one tree they can still overwrite each other.',
      '- You remain accountable. Verify what they return before folding it in; their unfinished',
      '  work is your unfinished work.',
      HELPER_MODELS,
    ].join('\n')
  }
  const tree =
    role === 'merge'
      ? "Helpers work in this task's tree and never in another."
      : 'Helpers are read-only like you: they read, grep and run commands, never edit or commit.'
  return `You MAY spawn helper subagents when that gets the job done faster at the same quality (a wide read, a parallel file sweep). ${tree} Partition their work by file. You remain accountable: verify what they return before using it. Helper models per the user's table: sonnet for lookups and mechanical work, opus only for hard reasoning; cap each helper's report with a word limit.`
}

// The other tasks that deliver the same approved items as t.
function otherTasksOf(t, ids) {
  const self = t.rootId || t.id
  return [...new Set(APPROVALS.filter((a) => ids.includes(a.id)).flatMap((a) => a.tasks))].filter((x) => x !== self)
}

// The approved items a task delivers, for its impl and fix prompts.
function approvalBlock(t) {
  const ids = approvalsFor(t)
  if (!ids.length) return ''
  return [
    `This task delivers approved item(s) ${ids.join(', ')}:`,
    ...ids.map((id) => `- ${id}: ${APPROVALS.find((a) => a.id === id).text}`),
    ...(otherTasksOf(t, ids).length
      ? [`Your share of it is your requirement below; the rest is delivered by tasks ${otherTasksOf(t, ids).join(', ')}. Do not list their parts in \`undelivered\`.`]
      : []),
    'Approved means delivered in full. The only acceptable non-delivery is an external blocker no agent in this run can clear, named in blocked (reason, whoCanClear); never deferred, never "later".',
  ].join('\n')
}

// Per-call inputs only; the method (tree rules, TDD, verify, committing, the
// deliverable fields, reuse rules, ceiling, report cap) is agents/implementer.md.
// One line per acceptance condition, so the implementer sees the exact test refs it must satisfy.
function acBlock(t) {
  if (!Array.isArray(t.ac) || !t.ac.length) return ''
  return [
    'Acceptance conditions (prove each; return acEvidence):',
    ...t.ac.map((a) => `${a.id}: ${a.text} [${(a.evidence && a.evidence.kind) || a.kind || ''}: ${(a.evidence && a.evidence.ref) || a.ref || ''}]`),
  ].join('\n')
}

function implPrompt(t) {
  return [
    `Your worktree: ${t.worktree}`,
    `Every command begins \`cd "${repoDir(t)}" && ...\`.`,
    `Repo: ${t.repo}`,
    `Task ${t.id}: ${t.title}`,
    briefBlock(),
    valueLine(t),
    contextPackLine(),
    ...docLines(),
    NOTES_BY_GREP,
    '',
    'Requirement (deliver ALL of it):',
    t.requirement,
    t.files ? `\nFiles the plan expects you to touch:\n${t.files.join('\n')}` : '',
    t.notes ? `\nNotes:\n${t.notes}` : '',
    approvalBlock(t) ? `\n${approvalBlock(t)}` : '',
    acBlock(t) ? `\n${acBlock(t)}` : '',
    '',
    dependencyLines(t),
    sharedParts(t),
    doNotBuildBlock(),
    '',
    targetedVerify(t),
    '',
    helperRules('impl'),
  ]
    .filter(Boolean)
    .join('\n')
}

// The reviewer's first step: one diff call over the non-test changed files, which
// the read gate then counts as a read of all of them (diffRead, diffLines).
function diffReadStep(files, range) {
  const paths = nonTestPaths(files)
  return paths.length
    ? [
        'First step, before anything else: read the change with ONE call, and report diffRead: true and diffLines (the lines of its output):',
        `git diff ${range} -- ${paths.join(' ')}`,
      ].join('\n')
    : ''
}

// Per-call inputs only; the method (completeness first, the checklist, what makes
// a finding) is agents/reviewer.md and the review-checklist.md it reads.
// scope: a gate-only round's re-review, { files, prev, head } - only the non-test
// files the last fix changed outside every finding's file.
function reviewPrompt(t, impl, round, preFindings = [], scope = null) {
  // Static blocks first (identical across tasks and rounds, so the prompt prefix caches);
  // the task, then the findings, the scope and the round number last.
  return [
    'Review the implementation of one plan task. The task, its findings, its scope and the round are at the end of this prompt.',
    briefBlock(),
    contextPackLine(),
    ...docLines(),
    NOTES_BY_GREP,
    '',
    `Review through these lenses only: ${LENSES.join(', ')}.`,
    '',
    helperRules('review'),
    '',
    'Each finding summary is at most 60 words. Keep the whole report to at most 400 words.',
    '',
    '=== The task under review ===',
    `Review plan task ${t.id} in the worktree at: ${t.worktree}`,
    valueLine(t),
    '',
    `Task requirement:\n${t.requirement}`,
    '',
    `What the implementer reports it did:\n${impl.summary}`,
    `Files changed: ${(impl.filesChanged || []).join(', ') || '(none reported)'}`,
    ownUndelivered(t, impl).length
      ? `Implementer left undelivered: ${ownUndelivered(t, impl).map((d) => `${d.what} (${d.why})`).join('; ')}`
      : '',
    impl.discovered && impl.discovered.length
      ? `Implementer discovered (outside its files, becomes a task in the epic, not a finding): ${impl.discovered.map((d) => `${d.what} (${d.why})`).join('; ')}`
      : '',
    '',
    sharedParts(t),
    doNotBuildBlock(),
    impl.reimplemented && impl.reimplemented.length
      ? `Implementer reimplemented: ${impl.reimplemented.map((x) => `${x.name} (${x.why})`).join('; ')}`
      : '',
    '',
    targetedVerify(t),
    diffReadStep(scope ? scope.files : impl.filesChanged, scope ? `${scope.prev || '<previous head>'}..${scope.head || 'HEAD'}` : `${diffBase(t)}..HEAD`),
    '',
    ...(preFindings.length
      ? ['Independent verification found:', ...preFindings.map((f) => `- [${f.severity}] ${f.file}${f.line ? ':' + f.line : ''} - ${f.summary}`), '']
      : []),
    ...(scope
      ? [
          `Scoped re-review: the last fix changed these non-test files (a work gate's own file, or outside every mechanical finding it was fixing). Judge only them, and only that change (git diff ${scope.prev || '<previous head>'}..${scope.head || 'HEAD'} -- <file>):`,
          ...scope.files.map((f) => `- ${f}`),
          'The rest of this task was already reviewed clean; the gate findings above are the fixer\'s, not yours.',
        ]
      : []),
    `Round ${round} of at most ${MAX_REVIEW_ROUNDS}.`,
  ]
    .filter(Boolean)
    .join('\n')
}

// rev: { findings, readSet } - readSet is what earlier agents already read, so this
// fixer opens only the ranges of the findings.
function fixPrompt(t, rev) {
  const readSet = mergeReadSets(rev.readSet)
  // Static blocks first for prefix caching; the task, the read set and the findings last.
  // The fixer method (judge each finding, failing test first) is agents/implementer.md.
  return [
    'Fix review findings for one plan task. The task and its findings are at the end of this prompt.',
    briefBlock(),
    ...docLines(),
    NOTES_BY_GREP,
    '',
    helperRules('fix'),
    '',
    '=== The task and its findings ===',
    `Fix plan task ${t.id} in the worktree at: ${t.worktree}`,
    `Every command begins \`cd "${repoDir(t)}" && ...\`.`,
    valueLine(t),
    '',
    `Original task requirement (the fix must still satisfy all of it):\n${t.requirement}`,
    ...(approvalBlock(t) ? ['', approvalBlock(t)] : []),
    ...(acBlock(t) ? ['', acBlock(t)] : []),
    '',
    sharedParts(t),
    doNotBuildBlock(),
    '',
    targetedVerify(t),
    '',
    ...(readSet.length
      ? [READ_HEADING, ...readSet.map(readLine), 'Open only the ranges the findings below name; everything above is already read.', '']
      : []),
    'Findings to fix:',
    rev.findings
      .map(
        (f, i) =>
          `${i + 1}. [${f.severity}${f.kind ? `/${f.kind}` : ''}] ${f.file}${f.line ? ':' + f.line : ''} - ${f.summary}\n   violates: ${f.requirement}` +
          (f.evidence ? `\n   evidence: ${f.evidence}` : ''),
      )
      .join('\n'),
  ].join('\n')
}

// ---------------------------------------------------------------- independent verify
// Round-1 evidence (flow-quality): a commit made after the agent's test run broke
// a test, and the self-reported green hid it. A fresh sonnet agent re-runs the
// command on the committed HEAD after every implementer and every fixer.
const DEBT_MARKERS = 'TODO, FIXME, XXX, HACK, NotImplementedError, unimplemented!, .skip(, pytest.mark.skip, xfail, t.Skip(, follow-up, for later, next round, round N (any number), phase 2, out of scope for this pass, left as an exercise, nice to have'
// A fresh worktree has no installed dependencies: one verify failed with "vite not found".
const INSTALL_DEPS =
  'Install missing dependencies first: a package.json with no node_modules beside it, or a pyproject.toml ' +
  'with no .venv, gets the repo\'s own setup task if it has one, else the lockfile install (npm ci, ' +
  'pnpm install --frozen-lockfile, yarn install --immutable, uv sync --frozen). Installing is not an edit.'
// The task's own verify, never the implementer's free-text command (D1): with none, verify-task
// builds the targeted command from the AC test refs and the changed test files (--targeted).
const verifyCommand = (t) => t.verify || ''
// The command the verifier's script last ran for a task: what a land re-runs when the task has no verify.
const VERIFIED_COMMAND_BY_ID = new Map()
const landVerify = (t) => verifyCommand(t) || VERIFIED_COMMAND_BY_ID.get(t.id) || ''
const SHA_RE = /^[0-9a-f]{7,40}$/

const shq = (x) => `'${String(x).replace(/'/g, `'\\''`)}'`
// The verify-task.py invocation shared by the verifier and a forward-merge re-verify.
const verifyTaskCommand = (t, worktree, flags = []) =>
  `python3 ${shq(PLUGIN_ROOT + '/scripts/verify-task.py')} ${[
    `--worktree ${worktree}`,
    `--base ${diffBase(t, true)}`,
    verifyCommand(t) ? `--cmd ${shq(verifyCommand(t))}` : '--targeted',
    `--markers ${shq(DEBT_MARKERS)}`,
    `--test-re ${shq(TEST_FILE_RE.source)}`,
    ...flags,
  ].join(' ')}`
const noRed = (impl) => {
  const tests = (impl && impl.tests) || {}
  return tests.wroteTestFirst === false || !(tests.red && String(tests.red.output || '').trim())
}

// The checks are a script, not an agent's judgement: the agent runs it once and relays its JSON.
// verify-task bounds each run at 480 s, so the call fits the Bash tool's 600 s maximum (D1).
const RUN_ONCE = 'Run this command once and only once, in ONE Bash call with `timeout: 600000`:'
// The final test refs the implementer or fixer named per AC; a later result that names none keeps the earlier ones.
const AC_EVIDENCE_BY_ID = new Map()
function verifyPrompt(t, impl, prev) {
  const acs = Array.isArray(t.ac) && t.ac.length ? t.ac : null
  const ace = acs ? AC_EVIDENCE_BY_ID.get(t.id) : null
  // A previous head that is not a sha is never put on a command line; the tier was still read.
  const flags = [
    ...(acs ? ['--acs "$ACS"'] : []),
    ...(ace ? ['--ac-evidence "$ACE"'] : []),
    '--install',
    ...(prev && SHA_RE.test(prev) ? [`--prev-head ${shq(prev)}`] : []),
    // The tier call runs on the first verify only; it sees the requirement (D9).
    ...(prev ? ['--no-tier'] : [`--requirement ${shq(t.requirement || '')}`]),
    ...(noRed(impl) ? ['--tdd-revert'] : []),
    ...mergedDependencyBranches(t).map((b) => `--exclude-ref ${shq(b)}`),
  ]
  return [
    `Independently verify plan task ${t.id} on its committed HEAD. You are a checker, not an implementer: a script does the checking.`,
    briefBlock(),
    valueLine(t),
    `1. D="${repoDir(t)}"`,
    ...(acs
      ? [
          '2. Write this acceptance-condition JSON to a temp file outside the worktree (mktemp), exactly as given, and call its path $ACS:',
          JSON.stringify(acs),
          ...(ace
            ? [
                '3. Write this JSON to a second temp file outside the worktree (mktemp), exactly as given, and call its path $ACE:',
                JSON.stringify(ace),
              ]
            : []),
          `${ace ? '4' : '3'}. ${RUN_ONCE}`,
        ]
      : [`2. ${RUN_ONCE}`]),
    `   ${verifyTaskCommand(t, '"$D"', flags)}`,
    `${3 + (acs ? 1 : 0) + (ace ? 1 : 0)}. The script prints one JSON object: relay the JSON verbatim as your result. Change nothing, add nothing, run no other check, write no gloss of your own (at most 0 words of yours). A command is judged by its exit code only: 0 is met and passed, anything else is not; never set passed or met differently from the script.`,
    '',
    'Do not edit, commit, stash, reset or switch branches. If the script cannot run, report passed=false with the error as evidence.',
    helperRules('verify'),
  ].join('\n')
}

const VERIFY_BY_ID = new Map()
const PREV_HEAD_BY_ID = new Map()
const VERIFY_BY_ROOT = new Map()
const TRIAGE_USAGE_BY_ROOT = new Map()
const NO_USAGE = { calls: 0, input_tokens: 0, output_tokens: 0 }
const addUsage = (a, b) => ({
  calls: a.calls + ((b && b.calls) || 0),
  input_tokens: a.input_tokens + ((b && b.input_tokens) || 0),
  output_tokens: a.output_tokens + ((b && b.output_tokens) || 0),
})
const ACS_FOR_AUDIT = new Map()
const bump = (m, k) => {
  m.set(k, (m.get(k) || 0) + 1)
  return m.get(k)
}
const tail = (s, n = 400) => String(s || '').trim().slice(-n)

// Every agent() call goes through safeAgent: a throw ends that one task, never the run (D14).
// A StructuredOutput retry-cap failure on an impl/fix/review/verify call marks the task
// agent-output-invalid (message kept, 300 chars); any other throw is "returned nothing", which
// the caller maps to the role's own died reason. Audits (t = null) record auditError instead.
// Triage, parking and merge throws only log: their callers have a safe fallback.
const AGENT_ERRORS = new Map()
const AUDIT_ERRORS = []
const TASK_ROLES = ['impl', 'fix', 'review', 'verify']
async function safeAgent(t, role, prompt, opts) {
  try {
    return await agent(prompt, opts)
  } catch (e) {
    const msg = String((e && e.message) || e)
    log(`${t ? t.id : 'run'}: ${role} agent threw: ${msg}`)
    if (!t && role === 'audit') AUDIT_ERRORS.push(msg.slice(0, 300))
    else if (t && TASK_ROLES.includes(role) && msg.includes('StructuredOutput retry cap')) AGENT_ERRORS.set(t.id, msg.slice(0, 300))
    return null
  }
}
// The reason a task that got no agent result ends with, and its message when the output was invalid.
const diedReason = (t, died) => (AGENT_ERRORS.has(t.id) ? 'agent-output-invalid' : died)
const diedExtra = (t) => (AGENT_ERRORS.has(t.id) ? { agentError: AGENT_ERRORS.get(t.id) } : {})

// At most VERIFY_CAP verifier agents run at once per repo (D12): 3-4 concurrent suites in one repo
// pinned verifies at the 600 s cap. A per-repo FIFO queue; an ending verify hands its slot straight
// to the next queued one. Only the verifier call holds a slot, so a queued verify always starts.
const VERIFY_CAP = 2
const VERIFY_SLOTS = new Map()
async function withVerifySlot(repo, fn) {
  if (!VERIFY_SLOTS.has(repo)) VERIFY_SLOTS.set(repo, { active: 0, queue: [] })
  const slot = VERIFY_SLOTS.get(repo)
  if (slot.active < VERIFY_CAP) slot.active++
  else await new Promise((start) => slot.queue.push(start))
  try {
    return await fn()
  } finally {
    const next = slot.queue.shift()
    if (next) next()
    else slot.active--
  }
}

// Dispatches the verifier for the deliverable `impl` and returns { impl, findings },
// where impl.verification is now the verifier's result and the implementer's own
// claim moves to impl.selfVerification. Null when the verifier returns nothing.
async function independentVerify(t, impl) {
  bump(VERIFY_BY_ROOT, t.rootId || t.id)
  if (impl && impl.acEvidence && typeof impl.acEvidence === 'object' && !Array.isArray(impl.acEvidence)) {
    AC_EVIDENCE_BY_ID.set(t.id, { ...(AC_EVIDENCE_BY_ID.get(t.id) || {}), ...impl.acEvidence })
  }
  const prev = PREV_HEAD_BY_ID.get(t.id)
  let v = await withVerifySlot(t.repo, () =>
    safeAgent(t, 'verify', verifyPrompt(t, impl, prev), {
      label: `${NAME}:verify:${t.short}#${bump(VERIFY_BY_ID, t.id)}`,
      phase: 'Verify',
      schema: VERIFY,
      model: 'haiku',
      effort: 'low',
      ...(VERIFIER_AGENT ? { agentType: VERIFIER_AGENT } : {}),
    }),
  )
  // A partial result (the turn cap hit before the report was complete) is no result.
  if (!v || typeof v.head !== 'string' || typeof v.passed !== 'boolean') {
    log(`${t.id}: verify agent returned ${v ? 'a partial result' : 'nothing'}`)
    return null
  }
  PREV_HEAD_BY_ID.set(t.id, v.head)
  if (v.command) VERIFIED_COMMAND_BY_ID.set(t.id, v.command)
  // The script is the authority (D12): pass and each command AC follow its exit code, never the relay's wording.
  const scriptPassed = Number.isInteger(v.exit) ? v.exit === 0 : v.passed
  if (v.passed !== scriptPassed) log(`${t.id}: verifier passed=${v.passed} contradicts script exit ${v.exit}; the script value wins`)
  v = { ...v, passed: scriptPassed }
  v.acs = (v.acs || []).map((a) => {
    if (!Number.isInteger(a.exit)) return a
    const met = a.exit === 0
    if (a.met !== met) log(`${t.id}: verifier AC ${a.id} met=${a.met} contradicts script exit ${a.exit}; the script value wins`)
    return { ...a, met }
  })
  TRIAGE_USAGE_BY_ROOT.set(t.rootId || t.id, addUsage(TRIAGE_USAGE_BY_ROOT.get(t.rootId || t.id) || NO_USAGE, v.triageUsage))
  const file = (impl.filesChanged && impl.filesChanged[0]) || '(unknown)'
  const requirement = 'every task must pass its verification command on the committed HEAD'
  const findings = []
  if (v.passed !== true) {
    findings.push({ severity: 'high', kind: 'wrong', file, summary: 'Independent verification failed: ' + tail(v.evidence), requirement, evidence: v.evidence, gate: 'verify-failed' })
  }
  if (v.clean !== true) {
    findings.push({ severity: 'high', kind: 'wrong', file, summary: 'Worktree not clean at verification: ' + tail(v.evidence), requirement, evidence: v.evidence, gate: 'dirty-tree' })
  }
  for (const m of v.debtMarkers || []) {
    findings.push({
      severity: 'high',
      kind: 'quality',
      file: m.file,
      line: m.line,
      summary: 'Debt marker introduced: ' + m.marker,
      requirement: 'no TODO, stub or skipped test stands in for the work',
      evidence: m.file + ':' + m.line,
      gate: 'debt-marker',
    })
  }
  for (const m of v.parking || []) {
    findings.push({
      severity: 'high',
      kind: 'quality',
      file: m.file,
      line: m.line,
      summary: 'Parking wording introduced: ' + m.text,
      requirement: 'no TODO, stub or skipped test stands in for the work',
      evidence: m.file + ':' + m.line,
      gate: 'parking',
    })
  }
  const acText = new Map((Array.isArray(t.ac) ? t.ac : []).map((a) => [a.id, a.text]))
  const forAudit = []
  for (const a of v.acs || []) {
    if (a.met === false) {
      findings.push({
        severity: 'high',
        kind: 'missing',
        file,
        summary: `Acceptance condition ${a.id} not met: ${acText.get(a.id) || a.how || ''}`,
        requirement: 'every acceptance condition of the task is met',
        evidence: a.how || String(a.id),
        gate: 'ac-unmet',
      })
    } else if (a.matchedBy === 'substring' || a.met === null || a.met === undefined || a.plausible === 'no' || a.plausible === 'unsure') {
      forAudit.push(String(a.id))
    }
  }
  ACS_FOR_AUDIT.set(t.rootId || t.id, forAudit)
  return {
    prev,
    head: v.head,
    tdd: v.tdd || null,
    diffstat: v.diffstat || null,
    acs: v.acs || [],
    tierHint: v.tierHint || null,
    changed: Array.isArray(v.changed) ? v.changed : null,
    changedSincePrevious: v.changedSincePrevious || [],
    // false when the verifier reported no change list: what a fix touched is then unknown
    changedKnown: Array.isArray(v.changedSincePrevious),
    impl: {
      ...impl,
      selfVerification: impl.verification,
      verification: { command: v.command, passed: v.passed === true && v.clean === true, evidence: v.evidence, head: v.head },
    },
    findings,
  }
}

// ---------------------------------------------------------------- TDD gate
// wroteTestFirst was a boolean nobody checked. Now a test-first claim needs the
// red run, and a skipped cycle needs one of the narrow exceptions or the revert
// recipe that proves the tests catch the change after the fact.
const TDD_EXCEPTIONS = /formatting|comment|docs?-only|documentation|prose|dependency bump|spike|generated/i
// "deletion pinned by a retirement test" is exempt only when the diff proves it: every non-test
// entry of the verifier's changed list is a plain deletion (D; a rename or A/M voids it) and a
// test file was added or modified.
const DELETION_EXCEPTION = /deletion pinned by a retirement test/i
function deletionPinned(changed) {
  if (!Array.isArray(changed) || !changed.length) return false
  const nonTest = changed.filter((c) => !TEST_FILE_RE.test(c.file))
  return nonTest.every((c) => /^D/.test(c.status || '')) &&
    changed.some((c) => TEST_FILE_RE.test(c.file) && /^[AM]/.test(c.status || ''))
}
const TDD_REQUIREMENT = 'every behaviour change is written test-first and the red run is reported'
const revertRecipe = (base) =>
  `commit first, then for each changed non-test file: git show ${base}:<path> > <path>; run the test (must fail); ` +
  `git show HEAD:<path> > <path>; run again (must pass); paste both tails into tests.red and verification.evidence`

function tddFindings(impl, tdd, changed, t) {
  if (tdd && tdd.ran && tdd.failedOnBase && tdd.passedOnHead) return []
  const tests = (impl && impl.tests) || {}
  const file = (tests.added && tests.added[0]) || '(tests)'
  if (tests.wroteTestFirst === true) {
    if (tests.red && String(tests.red.output || '').trim()) return []
    return [{
      severity: 'high',
      kind: 'quality',
      file,
      summary: 'No red evidence: tests.red must carry the failing run before the implementation',
      requirement: TDD_REQUIREMENT,
      evidence: 'tests.red missing',
      gate: 'no-red-evidence',
    }]
  }
  const note = String(tests.note || '')
  if (tests.wroteTestFirst === false && DELETION_EXCEPTION.test(note) && deletionPinned(changed)) return []
  if (tests.wroteTestFirst === false && !TDD_EXCEPTIONS.test(note)) {
    return [{
      severity: 'high',
      kind: 'quality',
      file,
      summary: `TDD skipped without a listed exception; prove the tests catch the change - ${revertRecipe(forkPointOf(t) || '<merge-base>')}`,
      requirement: TDD_REQUIREMENT,
      evidence: tests.note || '(no note)',
      gate: 'tdd-skipped',
    }]
  }
  return []
}

// ---------------------------------------------------------------- approvals gate
// `undelivered` is a finding the moment it appears, on any task. On a task that
// delivers approved items the finding names the item; only a named external
// blocker (`blocked`) lets the task stop short. `discovered` is never a finding.
// An entry naming another task of this run, or a path another task owns, is that
// task's share, not a gap here: it is recorded in MISATTRIBUTED, never dropped.
const MISATTRIBUTED = []
function ownerOfUndelivered(t, d) {
  const self = t.rootId || t.id
  const text = `${d.what || ''} ${d.where || ''}`
  const escaped = (x) => x.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  for (const o of TASKS) {
    if (o.id === self || o.id === t.id) continue
    if (new RegExp(`(^|[^A-Za-z0-9_-])${escaped(o.id)}(?![A-Za-z0-9_-])`).test(text)) return o.id
  }
  const names = (p) => new RegExp(`(^|[^A-Za-z0-9_./-])${escaped(p)}(?![A-Za-z0-9_-])`).test(text)
  const mine = TASKS.find((o) => o.id === self)
  const myFiles = new Set((mine && mine.files) || [])
  for (const [p, owner] of OWNER) if (owner !== self && names(p)) return owner
  for (const o of TASKS) if (o.id !== self && (o.files || []).some((f) => !myFiles.has(f) && names(f))) return o.id
  return null
}
// The undelivered entries that are this task's own gap: misattributed ones are not.
function ownUndelivered(t, impl) {
  const all = (impl && impl.undelivered) || []
  return Array.isArray(all) ? all.filter((d) => !ownerOfUndelivered(t, d)) : []
}
function approvalFindings(t, impl) {
  const ids = approvalsFor(t)
  const all = (impl && impl.undelivered) || []
  if (!Array.isArray(all) || !all.length || isBlocked(impl)) return []
  const undelivered = []
  for (const d of all) {
    const ownerTaskId = ownerOfUndelivered(t, d)
    if (!ownerTaskId) {
      undelivered.push(d)
      continue
    }
    const taskId = t.rootId || t.id
    if (!MISATTRIBUTED.some((m) => m.taskId === taskId && m.what === d.what)) MISATTRIBUTED.push({ taskId, ownerTaskId, what: d.what })
  }
  return undelivered.map((d) => ({
    severity: 'high',
    kind: 'missing',
    file: ids.length ? '(approved scope)' : '(task scope)',
    summary: ids.length
      ? 'Approved item ' + ids.join(', ') + ' not delivered (undelivered): ' + d.what + ' (' + d.why + ')'
      : 'Task scope not delivered (undelivered): ' + d.what + ' (' + d.why + ')',
    requirement: ids.length
      ? 'approved items are delivered in full; only a named external blocker (blocked with whoCanClear) is accepted'
      : 'the task requirement is delivered in full; only a named external blocker (blocked with whoCanClear) is accepted',
    evidence: 'undelivered: ' + d.why,
    gate: ids.length ? 'approved-item' : 'undelivered',
  }))
}

// A deliverable or review naming an external blocker no agent in this run can clear.
const isBlocked = (d) => Boolean(d && d.blocked && nonEmpty(d.blocked.reason))

// ---------------------------------------------------------------- continuation
// The continuation gets the ORIGINAL prompt verbatim (full requirement, rules,
// verify command, ceiling) with the latest handoff appended, so quality is the
// same as a single agent's. Its result then flows into review as usual.
const NOT_REPORTED = '(not reported - read git log and the diff)'

const READ_HEADING = 'Already read by the previous agent - do not re-read these unless you need a range not listed:'
const readKey = (e) => `${e.path}\u0000${e.lines || ''}`

// Inherited entries first, then new ones; an entry with the same path+lines is kept once.
function mergeReadSets(...sets) {
  const seen = new Set()
  return sets.flatMap((s) => (Array.isArray(s) ? s : [])).filter((e) => {
    if (!e || !nonEmpty(e.path) || seen.has(readKey(e))) return false
    seen.add(readKey(e))
    return true
  })
}

const readLine = (e) => `- ${e.path}${e.lines ? `:${e.lines}` : ''}${e.note ? ` - ${e.note}` : ''}`

function continuationPrompt(basePrompt, h = {}, n) {
  const f = (v) => (v === undefined || v === null || v === '' ? NOT_REPORTED : v)
  const readSet = mergeReadSets(h.readSet)
  const remaining = Array.isArray(h.remaining) && h.remaining.length ? h.remaining.map((x) => `- ${x}`).join('\n') : NOT_REPORTED
  return [
    `=== CONTINUATION ${n} of at most ${MAX_CONTINUATIONS} ===`,
    'Deliver ONLY the remaining acceptance conditions below; everything else is done and committed:',
    remaining,
    `WIP commit: ${f(h.wipCommit)}`,
    `Done so far: ${f(h.doneSoFar)}`,
    `Next step: ${f(h.nextStep)}`,
    `Test state: ${f(h.testState)}`,
    ...(readSet.length ? [READ_HEADING, ...readSet.map(readLine)] : []),
    'The requirement below is still binding in full; read `git log` and the diff, trust the files over this summary. Finish it, or hand off again at the ceiling.',
    '',
    basePrompt,
  ].join('\n')
}

// status "handoff" is the signal even when the handoff object is missing; a
// handoff object with no status (and not complete) is read the same way.
const isHandoff = (d) => Boolean(d && (d.status === 'handoff' || (!d.status && d.handoff && d.complete !== true)))

// Runs an implement or fix agent, re-dispatching a fresh continuation for each
// handoff. Returns { d, handoffCap } - handoffCap true when the last result is
// still a handoff after MAX_CONTINUATIONS; the caller escalates it.
// A deliverable from an agent still using the old `deferred` field: its entries are
// `undelivered`, so they reach the gate. Missing arrays become empty ones.
function splitDeferred(d) {
  if (!d || typeof d !== 'object') return d
  const { deferred, ...rest } = d
  const arr = (x) => (Array.isArray(x) ? x : [])
  return { ...rest, undelivered: [...arr(rest.undelivered), ...arr(deferred)], discovered: arr(rest.discovered) }
}

async function runWithContinuation(t, role, prompt, opts) {
  let d = await safeAgent(t, role, prompt, opts)
  let readSet = []
  for (let n = 1; isHandoff(d) && n <= MAX_CONTINUATIONS; n++) {
    readSet = mergeReadSets(readSet, d.handoff && d.handoff.readSet)
    log(`${opts.label}: handed off at the context ceiling (WIP ${(d.handoff && d.handoff.wipCommit) || '?'}) - continuation ${n}`)
    d = await safeAgent(t, role, continuationPrompt(prompt, { ...d.handoff, readSet }, n), { ...opts, label: `${opts.label}+${n}` })
  }
  return { d: splitDeferred(d), handoffCap: isHandoff(d), readSet }
}

// ---------------------------------------------------------------- review loop
// Capped at MAX_REVIEW_ROUNDS, and it ends early on these signals, each of which
// hands the task back to the orchestrator instead of dispatching another fixer:
// - the reviewer reports a blocker no agent can clear (a PR needing a human merge)
// - a gate finding seen in two consecutive rounds (gate-repeat): a fixer that could
//   not clear a deterministic gate once will not clear it on a third round
// - two consecutive rounds raise the same reviewer findings, however they are
//   worded (no-progress, judged by the Haiku triage agent)
// - an agent returns nothing
// Two loops once ran 9 and 5 rounds re-discovering that a human had to click
// merge; that was 20% of a session. Escalating is not dropping the work: the
// orchestrator judges the findings and decides the next step.
//
// Gate-only rounds: once the last LLM review was clean (light: once its single
// review ran), a round whose findings all come from the gates runs the fixer,
// the verifier and the gates only. About 110 later-round reviews ran only because
// a gate finding existed, and came back clean 97% of the time. The reviewer comes
// back, scoped, only for non-test files the fix touched outside every finding's file.
const firstWords = (s, n) => String(s || '').toLowerCase().split(/\s+/).filter(Boolean).slice(0, n).join(' ')

// Keyed on what a finding is about, not how it is phrased. The old key used the
// reviewer's free-text summary, so any rewording reset it and it never fired.
// The gate is part of it: a failed run and a dirty tree share file and requirement.
const findingKey = (fs) =>
  fs
    .map((f) => `${f.file}|${f.severity}|${f.gate || ''}|${firstWords(f.requirement, 8)}`)
    .sort()
    .join('||')

// Test files do not need to be read by the reviewer: the tests are not the claim.
const TEST_FILE_RE = /(^|\/)(tests?\/|test_[^/]*\.py$|[^/]*\.(test|spec)\.[^/]*$|[^/]*_(test|spec)\.[^/]*$)/
const isTestFile = (f) => TEST_FILE_RE.test(f)
const DOC_FILE_RE = /\.md$/i

// One path matcher for the read gate and the read-only-tests rule: equal after
// dropping a leading './', or one is the other under a directory prefix.
const stripDot = (f) => String(f).replace(/^\.\//, '')
function pathMatches(a, b) {
  const x = stripDot(a)
  const y = stripDot(b)
  return x === y || x.endsWith(`/${y}`) || y.endsWith(`/${x}`)
}

// Non-test paths in `files`; entries with a glob or an annotation
// (`gone.py (deleted)`) are not paths and are skipped.
const nonTestPaths = (files) =>
  (files || []).filter((f) => !f.includes('*') && !f.includes(' (')).map(stripDot).filter((f) => !isTestFile(f))

// Non-test files in `files` the review never opened. One diff read (diffRead true,
// diffLines > 0) counts every changed file as read.
function missingReads(files, rev) {
  if (rev.diffRead === true && rev.diffLines > 0) return []
  const read = (rev.filesRead || []).map(stripDot).filter(Boolean)
  return nonTestPaths(files)
    .filter((f) => !read.some((r) => pathMatches(r, f)))
}

// Non-test files the last fix changed outside every file its mechanical findings named
// (a work gate's file is not excluded: its fix wrote code): code a gate-only round
// would otherwise ship without any reviewer having read it.
function changedOutside(changed, findings) {
  const named = findings.filter((f) => !WORK_GATES.includes(f.gate)).map((f) => f.file).filter(nonEmpty)
  const seen = new Set()
  return (changed || []).filter((c) => {
    if (!c || !nonEmpty(c.file)) return false
    const f = stripDot(c.file)
    if (isTestFile(f) || named.some((n) => pathMatches(n, f)) || seen.has(f)) return false
    seen.add(f)
    return true
  })
}

// The changed files a light-tier fix touched among the files its reviewer findings named:
// the one scoped re-review reads them before the task settles.
function changedReviewerNamed(changed, reviewerFindings) {
  const named = reviewerFindings.map((f) => f.file).filter(nonEmpty)
  const seen = new Set()
  return (changed || []).filter((c) => {
    if (!c || !nonEmpty(c.file)) return false
    const f = stripDot(c.file)
    if (seen.has(f) || !named.some((n) => pathMatches(n, f))) return false
    seen.add(f)
    return true
  })
}

// Tests are read-only in a fix round: a modified, deleted or renamed existing test
// that no finding and no tests.added names is a finding (ImpossibleBench: agents
// rewrite the test to match the code).
function readOnlyTestFindings(prevFindings, fixed, v) {
  const named = [...prevFindings.map((f) => f.file), ...(((fixed && fixed.tests) || {}).added || [])]
    .filter(Boolean)
  const isNamed = (f) => named.some((n) => pathMatches(n, f))
  return (v.changedSincePrevious || [])
    .filter((c) => isTestFile(c.file) && /^[MDR]/.test(c.status) && !isNamed(c.file))
    .map((c) => ({
      severity: 'high',
      kind: 'quality',
      file: c.file,
      summary: 'Tests changed in a fix round without a finding or tests.added naming them: ' + c.file,
      requirement: 'tests are read-only in a fix round unless a finding or tests.added names them',
      evidence: c.status + ' ' + c.file + ' (git diff --name-status ' + v.prev + '..' + v.head + ')',
      gate: 'tests-changed',
    }))
}

// ---------------------------------------------------------------- triage
// Whether a reviewer finding repeats one from the round before is a meaning
// question, so one Haiku agent runs triage.py equivalence on the two lists.
const TRIAGE = {
  type: 'object',
  required: ['repeated'],
  properties: {
    repeated: {
      type: ['array', 'null'],
      items: { type: 'object', properties: { cur: { type: 'object' }, prev: { type: 'object' } } },
    },
    reason: { type: 'string' },
    error: { type: 'string' },
  },
}
const TRIAGE_BY_ID = new Map()
const leanFinding = (f) => ({ file: f.file, ...(f.line ? { line: f.line } : {}), severity: f.severity, summary: f.summary, requirement: f.requirement })

function triagePrompt(t, prev, cur) {
  return [
    `Decide which review findings of plan task ${t.id} repeat across two consecutive rounds. A script decides; you only run it.`,
    '1. Write this JSON to a temp file outside any worktree (mktemp), exactly as given, and call its path $IN:',
    JSON.stringify({ prev: prev.map(leanFinding), cur: cur.map(leanFinding) }),
    '2. Run this command once and only once:',
    `   python3 ${shq(PLUGIN_ROOT + '/scripts/triage.py')} equivalence --input "$IN"`,
    '3. The script prints one JSON object: relay it verbatim as your result. Change nothing, add nothing, run no other command.',
    'Do not edit, commit or switch anything. If the script cannot run, return repeated=null with the error in error.',
  ].join('\n')
}

// The current reviewer findings that repeat a previous one. A missing, failed or
// fallen-back triage result (triage.py's own `reason`) falls back to findingKey.
async function repeatedFindings(t, prev, cur) {
  const res = await safeAgent(t, 'triage', triagePrompt(t, prev, cur), {
    label: `${label('triage', t)}#${bump(TRIAGE_BY_ID, t.id)}`,
    phase: 'Review',
    schema: TRIAGE,
    model: 'haiku',
    effort: 'low',
  })
  if (res && Array.isArray(res.repeated) && !res.reason && !res.error) return res.repeated
  log(`${t.id}: triage ${res ? 'result unusable' : 'returned nothing'} - falling back to findingKey`)
  const keyed = new Map(prev.map((f) => [findingKey([f]), f]))
  return cur.filter((f) => keyed.has(findingKey([f]))).map((f) => ({ cur: f, prev: keyed.get(findingKey([f])) }))
}

// ---------------------------------------------------------------- false-finding triage
// A task stopped on a verified HEAD whose open findings the verifier's own output may
// refute: one Haiku agent runs triage.py false-finding. When every non-process finding
// comes back false the task releases its dependents (it still escalates for the record).
const FALSE_FINDING_BY_ID = new Map()
const TRIAGE_FALSE = {
  type: 'object',
  required: ['verdicts'],
  properties: { verdicts: { type: ['array', 'null'] }, error: { type: 'string' } },
}

function falseFindingPrompt(t, impl, findings) {
  const v = impl.verification || {}
  const input = {
    findings: findings.map(leanFinding),
    verification: { how: v.command, exit: v.passed ? 0 : 1, tail: v.evidence },
  }
  return [
    `Decide which open review findings of plan task ${t.id} the passing verification refutes. A script decides; you only run it.`,
    '1. Write this JSON to a temp file outside any worktree (mktemp), exactly as given, and call its path $IN:',
    JSON.stringify(input),
    '2. Run this command once and only once:',
    `   python3 ${shq(PLUGIN_ROOT + '/scripts/triage.py')} false-finding --input "$IN"`,
    '3. The script prints one JSON object: relay it verbatim as your result. Change nothing, add nothing, run no other command.',
    'Do not edit, commit or switch anything. If the script cannot run, return verdicts=null with the error in error.',
  ].join('\n')
}

// One verdict per finding ({verdict, reason}), or null when the classifier gave nothing usable
// (a throw, a bad shape): the caller then keeps today's behaviour. A missing or odd verdict is real.
async function falseFindings(t, impl, findings) {
  const res = await safeAgent(t, 'triage', falseFindingPrompt(t, impl, findings), {
    label: `${label('false-finding', t)}#${bump(FALSE_FINDING_BY_ID, t.id)}`,
    phase: 'Review',
    schema: TRIAGE_FALSE,
    model: 'haiku',
    effort: 'low',
  })
  if (!res || !Array.isArray(res.verdicts) || res.error) {
    log(`${t.id}: false-finding triage ${res ? 'result unusable' : 'returned nothing'} - keeping the findings`)
    return null
  }
  return findings.map((_, i) => {
    const v = res.verdicts.find((x) => x && x.index === i)
    return v && v.verdict === 'false'
      ? { verdict: 'false', reason: String(v.reason || '') }
      : { verdict: 'real', reason: String((v && v.reason) || 'no usable verdict') }
  })
}

// ---------------------------------------------------------------- declined gate second opinion
// A debt-marker or parking gate finding that repeats after the fixer declined it with
// evidence (its summary or a declined entry names file:line) may be prose that documents
// the rule. One Haiku agent runs triage.py parking on the flagged lines; no parking lines
// back drops the finding. A flag, a failure or no evidence leaves it to gate-repeat.
const PROSE_GATES = ['debt-marker', 'parking']
const TRIAGE_PARKING = {
  type: 'object',
  required: ['lines'],
  properties: { lines: { type: ['array', 'null'] }, reason: { type: ['string', 'null'] }, error: { type: 'string' } },
}

function declineEvidence(fixed, f) {
  if (!f.line || !PROSE_GATES.includes(f.gate) || !fixed) return false
  const at = `${f.file}:${f.line}`
  const said = [fixed.summary, ...(fixed.declined || []).flatMap((d) => [d.what, d.why])]
  return said.some((x) => typeof x === 'string' && x.includes(at))
}

function parkingPrompt(t, fs) {
  return [
    `Get a second opinion on gate findings of plan task ${t.id}. A script decides; you only run it.`,
    `1. For each location below read that line of the file inside ${t.worktree} (sed -n '<line>p' <file>).`,
    fs.map((f) => `   ${f.file}:${f.line}`).join('\n'),
    '2. Write a JSON array of {file, line, text} (text = that line, trimmed) to a temp file outside any worktree (mktemp), and call its path $IN.',
    '3. Run this command once and only once:',
    `   python3 ${shq(PLUGIN_ROOT + '/scripts/triage.py')} parking --input "$IN" --with-reason`,
    '4. The script prints one JSON object {lines, reason}: relay it verbatim as your result. Change nothing, add nothing, run no other command.',
    'Do not edit, commit or switch anything. If the script cannot run, return lines=null with the error in error.',
  ].join('\n')
}

// The subset of `fs` the classifier does not flag as parking. Any failure drops nothing.
async function unflaggedByClassifier(t, fs) {
  const res = await safeAgent(t, 'parking', parkingPrompt(t, fs), {
    label: `${label('triage', t)}#${bump(TRIAGE_BY_ID, t.id)}`,
    phase: 'Review',
    schema: TRIAGE_PARKING,
    model: 'haiku',
    effort: 'low',
  })
  if (!res || !Array.isArray(res.lines) || res.reason || res.error) {
    log(`${t.id}: parking triage ${res ? 'result unusable' : 'returned nothing'} - keeping the gate findings`)
    return []
  }
  const flagged = new Set(res.lines.map((l) => `${l.file}:${l.line}`))
  return fs.filter((f) => !flagged.has(`${f.file}:${f.line}`))
}

async function reviewUntilClean(t, firstImpl, firstPre = [], tier = 'full', implReads = []) {
  // Everything earlier agents read (implementer handoffs, reviewers, fixers): the fixer opens only the findings' ranges.
  let readSet = mergeReadSets(implReads)
  const light = tier === 'light'
  let impl = firstImpl
  let preFindings = firstPre
  // The previous round's findings, all of them and the reviewer's own.
  let prev = null
  const clearedGates = new Set() // gate findings the classifier ruled documentation: stay dropped on every following round
  // The last LLM review raised nothing (light: its single review has run).
  let reviewSettled = false
  // Light tier: the one scoped re-review of a fix to reviewer findings has run.
  let lightRereviewed = false
  // The verifier's view of the last fix: what changed between which heads.
  let lastFix = null
  // The fixer's last deliverable: its summary and declined list are the decline evidence.
  let lastFixer = null
  let reviewsSkippedGateOnly = 0
  const history = []
  const processGaps = []
  const declined = []
  const cannotVerify = []
  // Accumulated across rounds, de-duplicated, so a later round cannot silently drop
  // what an earlier one said it did not judge.
  const addGaps = (rev) => {
    for (const g of rev.processGaps || []) {
      if (!processGaps.some((x) => x.what === g.what && x.where === g.where)) processGaps.push({ what: g.what, where: g.where })
    }
    for (const d of rev.declined || []) {
      if (!declined.some((x) => x.what === d.what && x.why === d.why)) declined.push({ what: d.what, why: d.why })
    }
    for (const c of rev.cannotVerify || []) if (!cannotVerify.includes(c)) cannotVerify.push(c)
  }
  const result = (round, extra) => ({ task: t, impl, rounds: round, history, processGaps, declined, cannotVerify, reviewsSkippedGateOnly, ...extra })
  const stop = async (round, reason, extra = {}) => {
    if (reason !== 'blocked' && processOnly(impl, extra.findings)) {
      const gaps = extra.findings.map((f) => ({ what: f.summary, where: f.file, gate: f.gate }))
      log(`${t.id}: verified, only process findings open (${[...new Set(gaps.map((g) => g.gate))].join(', ')}) - releasing dependents`)
      return result(round, { clean: false, reason, processOnly: true, processGaps: [...processGaps, ...gaps] })
    }
    if (reason !== 'blocked' && verified(impl) && !isBlocked(impl) && Array.isArray(extra.findings) && extra.findings.length > 0) {
      const tr = await falseFindings(t, impl, extra.findings)
      if (tr) {
        const findings = extra.findings.map((f, i) => ({ ...f, verdict: tr[i].verdict, verdictReason: tr[i].reason }))
        const released = findings.every((f) => isProcessFinding(f) || f.verdict === 'false')
        if (released) log(`${t.id}: verified, every open non-process finding rejected by triage - releasing dependents`)
        return medium(result(round, { clean: false, reason, ...extra, findings, ...(released ? { triageRejected: true } : {}) }))
      }
    }
    return medium(result(round, { clean: false, reason, ...extra }))
  }
  // Marks a verified, unblocked stop whose only open findings are medium as mediumOnly.
  const medium = (r) => {
    if (r.reason === 'blocked' || r.triageRejected || !mediumOnly(impl, r.findings)) return r
    log(`${t.id}: verified, only medium findings open - releasing dependents, escalating for a ruling`)
    return { ...r, mediumOnly: true }
  }
  const review = (prompt, name) =>
    safeAgent(t, 'review', prompt, {
      label: name,
      phase: 'Review',
      schema: REVIEW,
      agentType: REVIEWER,
      // Sonnet always, whatever implemented the work; light reviews think less.
      model: 'sonnet',
      effort: light ? 'medium' : 'high',
    })

  for (let round = 1; ; round++) {
    // A fix that moved HEAD without a change list could have touched anything: full review.
    const unknownChange = Boolean(lastFix && !lastFix.known && lastFix.head !== lastFix.prev)
    if (round > 1 && reviewSettled && unknownChange) log(`${t.id}: round ${round} - the verifier reported no changedSincePrevious - full review`)
    const gateOnly = round > 1 && reviewSettled && !unknownChange && preFindings.every(isGate)
    let outside = gateOnly ? changedOutside(lastFix && lastFix.changed, prev.findings) : []
    if (light && gateOnly && !lightRereviewed && prev.reviewer.length) {
      const fixedNamed = changedReviewerNamed(lastFix && lastFix.changed, prev.reviewer).filter((c) => !isTestFile(stripDot(c.file)))
      if (fixedNamed.length) {
        lightRereviewed = true
        const have = new Set(outside.map((c) => stripDot(c.file)))
        outside = [...outside, ...fixedNamed.filter((c) => !have.has(stripDot(c.file)))]
        log(`${t.id}: light tier - one scoped re-review of the fix to ${fixedNamed.map((c) => c.file).join(', ')}`)
      }
    }
    let reviewerFindings = []
    if (gateOnly && !outside.length) {
      reviewsSkippedGateOnly++
      log(`${t.id}: round ${round} is gate-only after a clean review - fixer, verifier and gates only, no reviewer`)
    } else {
      const scope = gateOnly ? { files: outside.map((c) => c.file), prev: lastFix.prev, head: lastFix.head } : null
      if (scope) log(`${t.id}: round ${round} is gate-only, but the fix touched ${scope.files.join(', ')} - scoped re-review`)
      const mustRead = scope ? outside.filter((c) => !/^D/.test(c.status || '')).map((c) => c.file) : impl.filesChanged
      const prompt = reviewPrompt(t, impl, round, preFindings, scope)
      let rev = await review(prompt, `${label('review', t)}#${round}`)
      // A reread is dispatched at most once per round; blocked wins over shallow.
      for (let reread = false; ; reread = true) {
        if (!rev) {
          log(`${t.id}: review agent returned nothing on round ${round} - stopping this task's loop`)
          return await stop(round, diedReason(t, 'review-agent-died'), diedExtra(t))
        }
        addGaps(rev)
        if (isBlocked(rev)) {
          log(`${t.id}: blocked on round ${round} (${rev.blocked.whoCanClear}): ${rev.blocked.reason}`)
          return await stop(round, 'blocked', { blocked: rev.blocked })
        }
        const missing = missingReads(mustRead, rev)
        if (!missing.length) break
        if (reread) {
          log(`${t.id}: review-shallow - round ${round} still did not read: ${missing.join(', ')} - escalating`)
          const shallow = {
            severity: 'high',
            kind: 'quality',
            file: missing[0],
            summary: 'The review did not read: ' + missing.join(', '),
            requirement: 'the reviewer reads every non-test file the task changed before judging it',
            evidence: 'filesRead: ' + ((rev.filesRead || []).join(', ') || '(none)'),
            gate: 'review-shallow',
          }
          return await stop(round, 'review-shallow', { findings: [...preFindings, ...(rev.findings || []), shallow], unread: missing })
        }
        log(`${t.id}: review-shallow - round ${round} did not read: ${missing.join(', ')} - re-running the review once`)
        rev = await review(
          [prompt, 'You must read these before judging - the previous review did not:', ...missing.map((f) => `- ${f}`)].join('\n'),
          `${label('review', t)}#${round}-reread`,
        )
      }
      reviewerFindings = rev.findings || []
      readSet = mergeReadSets(readSet, (rev.filesRead || []).map((path) => ({ path })))
      reviewSettled = light || reviewerFindings.length === 0
    }

    let findings = [...preFindings, ...reviewerFindings].filter((f) => !(isGate(f) && clearedGates.has(findingKey([f]))))
    if (findings.length === 0 && verified(impl)) {
      log(`${t.id}: clean after ${round} round(s) (verified: ${impl.verification.command})`)
      return result(round, { clean: true })
    }
    if (findings.length === 0) {
      // Nothing was found but the work never demonstrated a passing run.
      // Not a judgement call - send it back for evidence.
      log(`${t.id}: no findings but verification did not pass; sending back for evidence`)
      findings.push({
        severity: 'high',
        kind: 'missing',
        file: (impl.filesChanged && impl.filesChanged[0]) || '(unknown)',
        summary:
          'No passing verification was reported. Run the targeted tests and report the real ' +
          'output tail, including the pass/fail summary line.',
        requirement: 'every task must demonstrate a passing verification run before it is accepted',
        evidence: tail(impl.verification && impl.verification.evidence) || 'verification.evidence empty',
        gate: 'verify-failed',
      })
    }
    history.push({ round, findings: findings.length, reviewed: !(gateOnly && !outside.length) })

    // No progress, judged per class against the round before.
    if (prev) {
      const prevGates = new Set(prev.findings.filter(isGate).map((f) => findingKey([f])))
      let repeatedGates = findings.filter((f) => isGate(f) && prevGates.has(findingKey([f])))
      const declinedGates = repeatedGates.filter((f) => declineEvidence(lastFixer, f))
      if (declinedGates.length) {
        const dropped = await unflaggedByClassifier(t, declinedGates)
        if (dropped.length) {
          log(`${t.id}: round ${round} - classifier sees no parking in ${dropped.map((f) => `${f.file}:${f.line}`).join(', ')}; dropping the declined gate finding(s)`)
          for (const f of dropped) clearedGates.add(findingKey([f]))
          findings = findings.filter((f) => !dropped.includes(f))
          repeatedGates = repeatedGates.filter((f) => !dropped.includes(f))
          if (findings.length === 0 && verified(impl)) {
            log(`${t.id}: clean after ${round} round(s) (verified: ${impl.verification.command})`)
            return result(round, { clean: true })
          }
        }
      }
      if (repeatedGates.length) {
        log(`${t.id}: round ${round} repeats gate finding(s) ${[...new Set(repeatedGates.map((f) => f.gate))].join(', ')} from round ${round - 1} - escalating`)
        return await stop(round, 'gate-repeat', { findings })
      }
      if (prev.reviewer.length && reviewerFindings.length) {
        const repeated =
          findingKey(reviewerFindings) === findingKey(prev.reviewer) ? reviewerFindings : await repeatedFindings(t, prev.reviewer, reviewerFindings)
        if (repeated.length) {
          log(`${t.id}: round ${round} raised the same findings as round ${round - 1} - escalating`)
          return await stop(round, 'no-progress', { findings })
        }
      }
    }
    if (round >= MAX_REVIEW_ROUNDS) {
      log(`${t.id}: still not clean after ${round} rounds - escalating`)
      return await stop(round, 'round-cap', { findings })
    }
    prev = { findings, reviewer: reviewerFindings }

    const { d: fixed, handoffCap, readSet: fixerReads } = await runWithContinuation(t, 'fix', fixPrompt(t, { findings, readSet }), {
      label: `${label('fix', t)}#${round}`,
      phase: 'Review',
      schema: DELIVERABLE,
      model: t.model || 'sonnet',
      agentType: IMPLEMENTER,
    })
    readSet = mergeReadSets(readSet, fixerReads)
    if (handoffCap) {
      impl = fixed
      log(`${t.id}: fixer still handing off after ${MAX_CONTINUATIONS} continuations - escalating`)
      return await stop(round, 'handoff-cap', { findings, handoff: fixed.handoff || {}, split: SPLIT_HINT })
    }
    if (!fixed) {
      log(`${t.id}: fix agent returned nothing on round ${round} - stopping this task's loop`)
      return await stop(round, diedReason(t, 'fix-agent-died'), diedExtra(t))
    }
    const v = await independentVerify(t, fixed)
    if (!v) {
      impl = fixed
      return await stop(round, diedReason(t, 'verify-agent-died'), diedExtra(t))
    }
    impl = v.impl
    if (isBlocked(impl)) {
      log(`${t.id}: fixer blocked on round ${round} (${impl.blocked.whoCanClear}): ${impl.blocked.reason}`)
      return await stop(round, 'blocked', { blocked: impl.blocked })
    }
    lastFixer = fixed
    lastFix = { changed: v.changedSincePrevious, known: v.changedKnown, prev: v.prev, head: v.head }
    preFindings = [...v.findings, ...tddFindings(v.impl, v.tdd, v.changed, t), ...approvalFindings(t, v.impl), ...readOnlyTestFindings(findings, fixed, v)]
  }
}

// The per-task review tier. An explicit t.review wins (true = full, false = skip);
// then a risk path means full; then skip only for a small, fully evidenced,
// finding-free change with at least one evidenced ac, else light. The verifier's tierHint can only raise it.
function reviewTier(t, impl, v, pre) {
  const explicit = t.review === true ? 'full' : t.review === false ? 'skip' : TIERS.includes(t.review) ? t.review : null
  let tier = explicit
  if (!tier) {
    const paths = (impl && impl.filesChanged) || []
    const ds = v.diffstat || {}
    const acs = Array.isArray(t.ac) ? t.ac : []
    const acsMet = acs.every((a) => {
      const r = (v.acs || []).find((x) => x.id === a.id)
      return r && r.met === true && SKIP_EVIDENCE.includes(a.evidence && a.evidence.kind)
    })
    // A settled doc-only or test-only diff has nothing a reviewer reads for, whatever its size.
    const settledKind = paths.length > 0 && (paths.every((p) => DOC_FILE_RE.test(p)) || paths.every((p) => TEST_FILE_RE.test(p)))
    if (paths.some((p) => RISK_PATH.test(p))) tier = 'full'
    else if (pre.length === 0 && acs.length > 0 && acsMet && (settledKind || (ds.addedNonTest <= SKIP_MAX_ADDED && ds.files <= SKIP_MAX_FILES))) tier = 'skip'
    else tier = 'light'
  }
  const hint = TIERS.indexOf(v.tierHint)
  return hint > TIERS.indexOf(tier) ? TIERS[hint] : tier
}

// ---------------------------------------------------------------- run
// implement -> review (unless small) -> ONE scope audit (unless args.audit is off;
// auditOnly runs just the epic-close audit). If the audit finds task
// gaps, one remediation round per affected task, then a second audit scoped to
// just those gaps. Whatever is still open after that goes back to the
// orchestrator. Auditing once per remediation round made 12 audits where 5 did.
// One task: implement (with continuations), then the review loop unless small.
async function runOne(t) {
  const { d: impl, handoffCap, readSet: implReads } = await runWithContinuation(t, 'impl', implPrompt(t), {
    label: label('impl', t),
    phase: 'Implement',
    schema: DELIVERABLE,
    // "implementation (writing code, tests, docs from a plan) - sonnet". The
    // plan is designed and gated by now; a task that still needs real
    // reasoning sets model: 'opus'.
    model: t.model || 'sonnet',
    agentType: IMPLEMENTER,
    // No isolation option here on purpose: the orchestrator already created a
    // named worktree per task with the worktree-create skill, and the prompt
    // pins the agent to it by absolute path. Setting isolation as well would
    // put the agent in a second, different tree and strand the work.
  })
  if (handoffCap) {
    log(`${t.id}: still handing off after ${MAX_CONTINUATIONS} continuations - escalating`)
    return { task: t, impl, rounds: 0, clean: false, reason: 'handoff-cap', history: [], processGaps: [], handoff: impl.handoff || {}, split: SPLIT_HINT }
  }
  if (!impl) {
    log(`${t.id}: implementation agent returned nothing`)
    return { task: t, impl: null, rounds: 0, clean: false, reason: diedReason(t, 'impl-agent-died'), history: [], processGaps: [], ...diedExtra(t) }
  }
  for (const x of impl.provides || []) {
    if (!PROVIDED.some((y) => y.name === x.name)) PROVIDED.push({ taskId: t.rootId || t.id, name: x.name, where: x.where })
  }
  const v = await independentVerify(t, impl)
  if (!v) return { task: t, impl, rounds: 0, clean: false, reason: diedReason(t, 'verify-agent-died'), history: [], processGaps: [], ...diedExtra(t) }
  if (isBlocked(v.impl)) {
    log(`${t.id}: implementer blocked (${v.impl.blocked.whoCanClear}): ${v.impl.blocked.reason}`)
    return { task: t, impl: v.impl, rounds: 0, clean: false, reason: 'blocked', blocked: v.impl.blocked, history: [], processGaps: [], declined: [], cannotVerify: [] }
  }
  const pre = [...v.findings, ...tddFindings(v.impl, v.tdd, v.changed, t), ...approvalFindings(t, v.impl)]
  const tier = reviewTier(t, v.impl, v, pre)
  if (tier === 'skip' && pre.length === 0 && verified(v.impl)) {
    log(`${t.id}: skip tier, verified - no per-task review; the scope audit still reads it`)
    return { task: t, impl: v.impl, rounds: 0, clean: true, history: [], processGaps: [] }
  }
  // An explicit skip that is not verified or has findings still gets one light pass.
  const use = tier === 'skip' ? 'light' : tier
  log(`${t.id}: review tier ${use}`)
  const r = await reviewUntilClean(t, v.impl, pre, use, implReads)
  return use === 'panel' ? { ...r, panel: true } : r
}

// ---------------------------------------------------------------- mid-run rulings (D1)
// The script has no filesystem, so one haiku agent reads args.rulingsFile (<epic dir>/rulings.json,
// written by `ticket.py rule`) at each wave boundary. An accept ruling on a verified task releases
// its dependents as processOnly does; the task still escalates, with the ruling attached.
const RULINGS = {
  type: 'object',
  required: ['rulings'],
  properties: { rulings: { type: ['array', 'null'] }, error: { type: 'string' } },
}
// Root id -> the last ruling applied to it, {accept, reason}.
const RULED = new Map()
// Root ids an accept ruling released: kept for the run, never revoked.
const RULED_ACCEPT = new Set()
// Rulings already applied, by content, so a re-read never applies one twice.
const RULINGS_APPLIED = new Set()
// Rulings for unknown or unverified tasks, by content: {task, accept, reason, why}.
const RULINGS_IGNORED = new Map()
let rulingsReads = 0

function rulingsPrompt() {
  return [
    'Read the orchestrator rulings file of this plan run and relay it. You only read; the script decides what the rulings do.',
    `1. Run this command once and only once: cat ${shq(RULINGS_FILE)}`,
    '2. If cat reports that the file does not exist, return rulings=[] (no rulings yet).',
    '3. Otherwise the file holds a JSON array of {task, accept, reason, at}: return that array verbatim as rulings. Change nothing, add nothing, run no other command.',
    'Do not edit, commit or switch anything. If the file exists but is not a JSON array, or cat fails for another reason, return rulings=null with the error in error.',
  ].join('\n')
}

// The rulings in the file, or null when the reader threw or returned something unusable.
async function readRulings() {
  const res = await safeAgent(null, 'rulings', rulingsPrompt(), {
    label: `${NAME}:rulings:run#${++rulingsReads}`,
    phase: 'Implement',
    schema: RULINGS,
    model: 'haiku',
    effort: 'low',
  })
  if (!res || !Array.isArray(res.rulings) || res.error) {
    log(`rulings reader ${res ? `result unusable${res.error ? `: ${res.error}` : ''}` : 'returned nothing'} - no release`)
    return null
  }
  return res.rulings
}

// Applies every ruling not applied yet against the tasks settled so far. A ruling for an
// unknown or (not yet) verified task is ignored and listed; a later read applies it once
// its task has settled verified.
function applyRulings(rulings, settled) {
  for (const x of rulings) {
    if (!x || typeof x.task !== 'string' || typeof x.accept !== 'boolean') {
      log(`rulings: skipping a malformed entry ${JSON.stringify(x)}`)
      continue
    }
    const ruling = { accept: x.accept, reason: String(x.reason || '') }
    const key = JSON.stringify([x.task, ruling.accept, ruling.reason, String(x.at || '')])
    if (RULINGS_APPLIED.has(key)) continue
    const r = settled.get(x.task)
    const why = !TASKS.some((t) => t.id === x.task) ? 'unknown task' : !(r && verified(r.impl)) ? 'task not verified' : ''
    if (why) {
      RULINGS_IGNORED.set(key, { task: x.task, ...ruling, why })
      continue
    }
    RULINGS_IGNORED.delete(key)
    RULINGS_APPLIED.add(key)
    RULED.set(x.task, ruling)
    if (ruling.accept) RULED_ACCEPT.add(x.task)
    log(`${x.task}: ruling ${ruling.accept ? 'accept' : 'reject'} applied: ${ruling.reason}`)
  }
}

// ---------------------------------------------------------------- in-run landing (D4)
// With LANDING, a released task is landed on BASE_REF (the epic branch) before any dependent
// counts it as released: merge.py rebases its branch onto the epic branch, runs the task verify
// in the rebased tree, and only then fast-forwards the epic branch in the integration tree.
// --keep leaves the task tree for remediation and the epic-close audit (D9).
const LANDED = []
// A component task's tree is <...>/<epic>-<id>/<repo>; merge.py then needs --repo.
const treePath = (t) => t.worktree.replace(/\/+$/, '')
const componentTree = (t) => treePath(t).split('/').pop() === t.repo
// merge.py --name is the task's recorded worktree name (last path component without the /<repo>
// suffix), so a legacy <epic>--<id> tree recorded before the upgrade lands through the same step.
const landName = (t) => (componentTree(t) ? treePath(t).split('/').slice(0, -1) : treePath(t).split('/')).pop()

function landPrompt(t) {
  const flags = [
    `--name ${shq(landName(t))}`,
    `--base ${shq(BASE_REF)}`,
    ...(componentTree(t) ? [`--repo ${shq(t.repo)}`] : []),
    '--keep',
    '--no-suites',
    `--verify ${shq(landVerify(t))}`,
  ]
  return [
    `Land plan task ${t.id} on the epic branch ${BASE_REF}: merge.py rebases its branch onto ${BASE_REF}, runs the task verify in the rebased tree, and only on a pass fast-forwards ${BASE_REF} in the integration tree.`,
    briefBlock(),
    valueLine(t),
    `Task worktree: ${t.worktree}`,
    `Main checkout: ${MAIN_CHECKOUT}`,
    '1. Run exactly this one command; a cd does not persist between Bash calls, so it is one line with absolute paths:',
    `   cd ${shq(MAIN_CHECKOUT)} && python3 ${shq(PLUGIN_ROOT + '/skills/worktree-merge/scripts/merge.py')} ${flags.join(' ')}`,
    '2. Relay its output: landed is true only when it exited 0. verification.command is the --verify command, verification.passed is its `verify: pass` line, verification.evidence the output tail including that line. notes carries its notes lines.',
    `3. When it landed, run \`git -C "${repoDir(t)}" rev-parse ${BASE_REF}\` and report the SHA as head; otherwise report head as an empty string.`,
    `   Also report base: the baseBefore value merge.py prints (the ${BASE_REF} commit the task was rebased onto and fast-forwarded from); empty when it did not land.`,
    `   Contained: when merge.py exits 0 printing \`merged 0 commit(s)\` and a note that there is nothing to merge because every commit is already in ${BASE_REF}, and its verify line is pass, the task is landed: report landed true, contained true, and head as the task tree HEAD (\`git -C "${repoDir(t)}" rev-parse HEAD\`). It is never a failure.`,
    `4. A rebase conflict can be a re-conflict: rebasing a dependent onto ${BASE_REF} drops its merge-of-${BASE_REF} commit, so conflicts that merge had resolved can come back. merge.py has already aborted its rebase, so the task worktree is clean. First reproduce the conflict: run \`git -C "${repoDir(t)}" rebase ${BASE_REF}\` in the task worktree and list the conflicted files with \`git -C "${repoDir(t)}" diff --name-only --diff-filter=U\`. Resolve a conflicted file only when the resolution is unambiguous: both sides carry the same change, or one side's hunk is exactly the dependency text already on ${BASE_REF}. For each resolved file run \`git -C "${repoDir(t)}" add <file>\`, then \`git -C "${repoDir(t)}" rebase --continue\` (with GIT_EDITOR=true), repeating until the rebase is finished and no rebase is in progress. Then re-run the task verify there (\`cd "${repoDir(t)}" && ${landVerify(t)}\`), and re-run the step 1 command once.`,
    '   Otherwise (any ambiguous file) run `git rebase --abort` in the task worktree and report landed=false, conflict=true, with notes listing every conflicting file. If the re-run of the step 1 command conflicts again, merge.py has aborted its own rebase: run `git rebase --abort` only if a rebase is still in progress, and report landed=false, conflict=true with every conflicting file listed in notes.',
    `   ${OWN_CHECKOUT_ONLY}`,
    '   Never run `git checkout` in the main checkout, and never switch a branch in any tree. A failing verify is reported, not fixed.',
    helperRules('merge'),
    'Keep the whole report to at most 150 words.',
  ].join('\n')
}

// One landing; returns the task's settled result after it: the landed head as the verification
// head on success, else clean false with reason land-failed and the land result attached.
async function landTask(t, r) {
  // A land with no command to verify would fast-forward unchecked: it fails instead.
  if (!landVerify(t)) {
    log(`${t.id}: no task verify and no verifier command to land with - escalating`)
    return { ...r, clean: false, reason: 'land-failed', processOnly: false, triageRejected: false, land: null }
  }
  const dispatch = (model) =>
    safeAgent(t, 'land', landPrompt(t), {
      label: label('land', t),
      phase: 'Land',
      schema: LAND,
      agentType: 'workbench:worktree-merger',
      model,
    })
  // The mechanical land runs on haiku; a reported conflict is re-dispatched once on sonnet.
  let res = await dispatch('haiku')
  if (res && res.conflict === true && res.landed !== true) {
    log(`${t.id}: land agent reported a conflict on haiku - re-dispatching once on sonnet`)
    res = (await dispatch('sonnet')) || res
  }
  const ok = res && (res.landed === true || res.contained === true) && res.verification && res.verification.passed === true
  if (ok) {
    const id = t.rootId || t.id
    if (res.landed === true && res.base) FORK_POINTS.set(id, String(res.base))
    LANDED.push({ id, head: res.head, ...(FORK_POINTS.has(id) ? { forkPoint: FORK_POINTS.get(id) } : {}) })
    log(`${t.id}: landed on ${BASE_REF} at ${res.head}`)
    const prior = r.impl.verification || {}
    return { ...r, land: res, impl: { ...r.impl, verification: { ...prior, ...res.verification, evidence: res.verification.evidence || prior.evidence, head: res.head } } }
  }
  log(`${t.id}: landing on ${BASE_REF} failed${res ? `: ${res.notes || tail(res.verification && res.verification.evidence)}` : ' - the land agent returned nothing'} - escalating`)
  return { ...r, clean: false, reason: 'land-failed', processOnly: false, triageRejected: false, mediumOnly: false, land: res || null }
}

// Every task starts the moment its own dependencies are released - per-task edge triggers,
// never "when the whole wave is done", so the slowest sibling sets no one else's latency.
// A dependency is released when it settles verified and clean, processOnly, triageRejected,
// accepted by a ruling, or mediumOnly (released to its dependents, escalated, never landed in-run). A task whose dependency failed is escalated, not run.
// With args.rulingsFile, a dependent of a verified but unreleased dependency waits for a
// ruling. The file is read once per wave boundary: a task settles verified-not-released
// while another waits on it, or nothing runs while dependents wait. An idle read that
// releases none of the waiters fails them, so the run always reaches its end.
// With LANDING a clean-or-accepted task is queued for landing first and counts as
// released only once it landed; one land agent runs at a time, and a failed landing
// (reason land-failed) fails its dependents.
// Transitive dependents of a task's root: the critical-path proxy (plan-execute reads no task size).
const DEPENDENTS = new Map()
const dependentCount = (t) => {
  const id = t.rootId || t.id
  if (!DEPENDENTS.has(id)) DEPENDENTS.set(id, byId.has(id) ? TASK_IDS.filter((d) => ancestors(d).has(id)).length : 0)
  return DEPENDENTS.get(id)
}

function runTasks(batch) {
  const ids = new Set(batch.map((t) => t.id))
  const depsOf = (t) => (t.dependsOn || []).filter((d) => ids.has(d))
  const settled = new Map()
  const running = new Set()
  // Neither started nor failed yet.
  const pending = new Set(ids)
  const landFailed = (d) => settled.has(d) && settled.get(d).reason === 'land-failed'
  // Releasable (and, with LANDING, landable): a clean, processOnly, triageRejected or ruled-accept task.
  const releasable = (d) => {
    const r = settled.get(d)
    return Boolean(r && verified(r.impl) && !landFailed(d) && (r.clean || r.processOnly || r.triageRejected || RULED_ACCEPT.has(d)))
  }
  // A mediumOnly task releases its dependents (they merge its task branch) but is never queued
  // for landing until a ruling accepts it (D8, amended 2026-10-22).
  const mediumHeld = (d) => {
    const r = settled.get(d)
    return Boolean(r && r.mediumOnly && verified(r.impl) && !landFailed(d) && !releasable(d))
  }
  const landed = new Set()
  const released = (d) => mediumHeld(d) || (releasable(d) && (!LANDING || landed.has(d)))
  // Releasable but not landed yet: queued or landing now.
  const landPending = (d) => LANDING && releasable(d) && !landed.has(d)
  // Settled verified but not releasable; only a ruling can release it.
  const rulable = (d) => Boolean(RULINGS_FILE) && settled.has(d) && verified(settled.get(d).impl) && !releasable(d) && !landFailed(d)
  const landQueue = []
  let landing = false
  const waitedOn = (d) => batch.some((t) => pending.has(t.id) && depsOf(t).includes(d))
  const waiters = () => batch.filter((t) => pending.has(t.id) && depsOf(t).every((d) => settled.has(d)))
  // Bumps on every settle: an idle read is final only when nothing settled since it began.
  let epoch = 0
  let lastReadAt = -1
  let reading = false
  let needRead = false
  return new Promise((resolve, reject) => {
    const settle = (t, r) => {
      pending.delete(t.id)
      running.delete(t.id)
      settled.set(t.id, r)
      epoch++
    }
    const fail = (t) => {
      const waitingOn = depsOf(t).filter((d) => !released(d))
      log(`${t.id}: not started - dependency ${waitingOn.join(', ')} did not finish clean`)
      settle(t, { task: t, impl: null, rounds: 0, clean: false, reason: 'dependency-failed', waitingOn, history: [], processGaps: [] })
    }
    const begin = (t) => {
      pending.delete(t.id)
      running.add(t.id)
      const deps = depsOf(t)
      if (deps.length) log(`${t.id}: dependencies ${deps.join(', ')} clean - starting`)
      runOne(t).then((r) => {
        DEP_RESULTS.set(t.id, r)
        settle(t, r)
        if (rulable(t.id) && waitedOn(t.id)) needRead = true
        pump()
      }, reject)
    }
    const read = () => {
      reading = true
      needRead = false
      const at = epoch
      readRulings().then((rulings) => {
        if (rulings) applyRulings(rulings, settled)
        lastReadAt = at
        reading = false
        pump()
      }, reject)
    }
    // At most one land agent at a time: the next queued task lands when the last one returned.
    const land = () => {
      for (const t of batch) if (landPending(t.id) && !landQueue.includes(t) && landing !== t.id) landQueue.push(t)
      if (landing || !landQueue.length) return
      const t = landQueue.shift()
      landing = t.id
      landTask(t, settled.get(t.id)).then((r) => {
        settled.set(t.id, r)
        DEP_RESULTS.set(t.id, r)
        if (r.reason !== 'land-failed') landed.add(t.id)
        landing = false
        epoch++
        pump()
      }, reject)
    }
    const pump = () => {
      land()
      for (let moved = true; moved; ) {
        moved = false
        const ready = []
        for (const t of waiters()) {
          const deps = depsOf(t)
          if (deps.every(released)) ready.push(t)
          else if (deps.some((d) => !released(d) && !rulable(d) && !landPending(d))) fail(t)
          else continue
          moved = true
        }
        // Longest chain first (D12): sort is stable, so ties keep input order.
        ready.sort((a, b) => dependentCount(b) - dependentCount(a)).forEach(begin)
      }
      if (reading) return
      const idle = running.size === 0 && !landing && !landQueue.length
      const held = waiters()
      if (needRead || (idle && held.length && lastReadAt !== epoch)) return read()
      if (idle && held.length) {
        // The last read saw this very state and released none of them.
        for (const t of held) fail(t)
        return pump()
      }
      if (idle && !pending.size) resolve(batch.map((t) => settled.get(t.id)))
    }
    pump()
  })
}

function describeDelivered(rs) {
  return rs
    .map((r) => {
      const d = r.impl
      return [
        `Task ${r.task.id}: ${r.task.title}`,
        TASK_FILES ? '' : `  requirement: ${r.task.requirement}`,
        `  value: ${r.task.value}`,
        `  claimed complete: ${d ? d.complete : 'NO RESULT'}`,
        `  summary: ${d ? d.summary : '(none)'}`,
        `  files: ${d && d.filesChanged ? d.filesChanged.join(', ') : '(none)'}`,
        ownUndelivered(r.task, d).length
          ? `  UNDELIVERED: ${ownUndelivered(r.task, d).map((x) => `${x.what} (${x.why})`).join('; ')}`
          : '',
        `  review rounds: ${r.rounds}, clean: ${r.clean}${r.reason ? ', stopped: ' + r.reason : ''}`,
        `  verified: ${verified(d)}`,
      ]
        .filter(Boolean)
        .join('\n')
    })
    .join('\n\n')
}

// The ledger block, shared by every audit prompt.
const ledgerBlock = () =>
  APPROVALS.length
    ? [
        '',
        '=== APPROVED ITEMS (the ledger) ===',
        ...APPROVALS.map((a) => `- ${a.id} (tasks ${a.tasks.join(', ')}): ${a.text}`),
        'For every approved item, report {id, landed, evidence} in approvals; landed is false when any part of it is missing in the trees.',
      ]
    : []

// The duplicate-sweep inputs; the sweep's method is in agents/scope-auditor.md.
const duplicateSweepBlock = () => [
  '',
  'Run the duplicate sweep across these task trees.',
  sharedParts(null),
  ...(EXISTING.length ? ['A new implementation of any of these is a duplicates entry.'] : []),
  doNotBuildBlock(),
  ...(DO_NOT_BUILD.length ? ['Building any of them is a `missing` finding on the task that built it, naming the file:symbol.'] : []),
]

// The output contract every audit shares: where a gap goes, and how long its evidence is.
const auditContract = () => [
  helperRules('audit'),
  'Every `missing` entry names the plan task it belongs to. Legal taskId values: ' + TASK_IDS.join(', '),
  'A gap no single task owns goes in `waveLevel`, never in `missing`; anything delivered that the plan did not ask for goes in `outOfScope`.',
]

// Same-repo dependency pairs, for the auditor's ancestry check.
const ancestryPairs = () => {
  const pairs = TASKS.flatMap((t) => (t.dependsOn || []).filter((d) => byId.has(d) && byId.get(d).repo === t.repo).map((d) => `${d} -> ${t.id}`))
  return pairs.length ? ['Same-repo dependencies to check for ancestry (dependency -> dependent): ' + pairs.join(', ')] : []
}

// When every task carries its task file, an audit prompt names the files and inlines no
// requirement text (D11); the auditor reads the Requirement and AC sections itself.
const TASK_FILES = TASKS.length > 0 && TASKS.every((t) => typeof t.taskFile === 'string' && t.taskFile)
const taskFileLines = (extra) => [
  '=== TASKS ===',
  'Read each task file\'s `## Requirement` and `## Acceptance conditions` sections (only those sections, not the whole file or other docs):',
  ...TASKS.map((t) => `- ${t.id}: ${t.title} | tree ${t.worktree} | task file ${t.taskFile}`),
  ...(extra ? TASKS.flatMap((t) => extra(t)) : []),
]

// Inputs only: the method (what to look for, how to read, the duplicate sweep,
// the ancestry check) is the scope-auditor agent's.
function auditPrompt(rs, gaps) {
  const scope = gaps
    ? [
        'This is the re-check after a remediation round. Re-check ONLY these items from the',
        'previous audit, and report each one still not landed. Do not re-audit anything else.',
        gaps.map((g) => `- [${g.taskId}] ${g.item}`).join('\n'),
      ]
    : ['=== APPROVED PLAN ===', PLAN_TEXT || '(plan text not supplied - audit against the per-task requirements below)']
  return [
    'Audit this run: compare the approved scope below against what the worktrees actually contain.',
    briefBlock(),
    ...docLines(),
    '',
    ...scope,
    ...ledgerBlock(),
    ...(TASK_FILES ? ['', ...taskFileLines()] : []),
    '',
    '=== WHAT WAS REPORTED DELIVERED ===',
    describeDelivered(rs),
    '',
    'Worktrees to inspect:',
    [...new Set(TASKS.map((t) => `${t.repo}: ${t.worktree}`))].join('\n'),
    ...ancestryPairs(),
    '',
    ...auditContract(),
    ...(gaps ? [] : duplicateSweepBlock()),
    'Each evidence entry is at most 80 words.',
  ].join('\n')
}

// A task whose every AC the verifier settled: each AC met, backed by test, symbol, command or
// doc-section evidence, none matched by substring, and none left in acsForAudit (D12).
const SETTLED_KINDS = ['test', 'symbol', 'command', 'doc-section']
const settledTask = (t) =>
  Array.isArray(t.ac) &&
  t.ac.length > 0 &&
  !(t.acsForAudit || []).length &&
  t.ac.every((a) => a.met !== false && a.matchedBy !== 'substring' && a.evidence && SETTLED_KINDS.includes(a.evidence.kind))

// One row per acceptance condition; a task without any gets one empty row. An id
// in acsForAudit is one the verifier could not settle, so the auditor judges it.
// `only` narrows the rows to the settled tasks (true) or the rest (false).
function acTable(only) {
  const cell = (s) => String(s == null ? '' : s).replace(/\|/g, '/').replace(/\s+/g, ' ').trim()
  const evidence = (e) => (!e ? '' : e.ref ? `${e.kind}: ${e.ref}` : e.kind || '')
  const rows = TASKS.filter((t) => only === undefined || settledTask(t) === only).flatMap((t) => {
    const open = new Set((t.acsForAudit || []).map(String))
    const acs = Array.isArray(t.ac) ? t.ac : []
    if (!acs.length) return [`| ${t.id} | (none) | | | |`]
    return acs.map((a) => `| ${t.id} | ${cell(a.id)} | ${cell(a.text)} | ${cell(evidence(a.evidence))} | ${open.has(String(a.id)) ? 'open: judge it' : 'verifier settled'} |`)
  })
  return ['=== ACCEPTANCE CONDITIONS ===', '| task | AC | text | evidence | status |', '|---|---|---|---|---|', ...rows]
}

// The epic-close audit (auditOnly): inputs only, like auditPrompt.
// With `split` the verifier-settled rows go to settledAuditPrompt and are left out here.
function epicAuditPrompt(split) {
  const taskLine = (t) => `- ${t.id}: ${t.title} | worktree ${t.worktree} | branch ${t.branch || '(none)'} | verified head ${t.verifiedHead || '(none)'}`
  return [
    `Audit epic ${EPIC || NAME} at close: is every goal, acceptance condition and approved item delivered in the task trees?`,
    briefBlock(),
    ...docLines(),
    '',
    `Epic README (its Goals and Non-goals are the definition of done): ${EPIC_README}`,
    '',
    ...(TASK_FILES
      ? taskFileLines((t) => [`  ${t.id} branch ${t.branch || '(none)'}, verified head ${t.verifiedHead || '(none)'}`])
      : ['=== TASKS ===', ...TASKS.map(taskLine), ...TASKS.map((t) => `  ${t.id} requirement: ${t.requirement}`)]),
    '',
    ...(split ? ['Acceptance conditions of tasks the verifier fully settled are confirmed by a separate auditor; only the rows below are yours.'] : []),
    ...acTable(split ? false : undefined),
    ...ledgerBlock(),
    ...ancestryPairs(),
    '',
    ...auditContract(),
    ...duplicateSweepBlock(),
    'Each evidence entry is at most 80 words.',
  ].join('\n')
}

// The settled rows only: the haiku auditor confirms each row's evidence exists at the landed head.
function settledAuditPrompt() {
  const settled = TASKS.filter(settledTask)
  return [
    `Settled-rows mode, epic ${EPIC || NAME}: the verifier already settled every acceptance condition of the tasks below. Confirm only that each row's evidence (test, symbol, command or doc section) exists at the task's verified head in its tree. A row whose evidence is missing is a \`missing\` entry on its task; do nothing else.`,
    briefBlock(),
    '',
    ...(TASK_FILES ? ['Task files (read only the `## Acceptance conditions` section):'] : []),
    ...settled.map((t) => `- ${t.id}: tree ${t.worktree} | branch ${t.branch || '(none)'} | verified head ${t.verifiedHead || '(none)'}${t.taskFile ? ` | task file ${t.taskFile}` : ''}`),
    '',
    ...acTable(true),
    '',
    'Every `missing` entry names the plan task it belongs to. Legal taskId values: ' + settled.map((t) => t.id).join(', '),
    'Each evidence entry is at most 80 words.',
  ].join('\n')
}

// The epic-close audit: settled rows on one haiku call, everything else on sonnet; the results merge.
async function runEpicAudit() {
  if (!TASKS.some(settledTask)) return safeAgent(null, 'audit', epicAuditPrompt(), auditOpts('epic'))
  const [main, settled] = await Promise.all([
    safeAgent(null, 'audit', epicAuditPrompt(true), auditOpts('epic')),
    safeAgent(null, 'audit', settledAuditPrompt(), { ...auditOpts('settled'), model: 'haiku', effort: 'low' }),
  ])
  if (!main) return null
  const lost = settled ? [] : [{ item: 'settled-row audit did not run', evidence: 'haiku auditor returned nothing', taskId: null }]
  return { ...main, complete: main.complete === true && !!settled && settled.complete === true, missing: [...(main.missing || []), ...((settled && settled.missing) || []), ...lost] }
}

// Every audit dispatch: the scope-auditor agent type, on sonnet (a read-and-compare
// job against files; the review row of the model policy, whatever implemented it).
const auditOpts = (labelSuffix) => ({
  label: `${NAME}:audit:${labelSuffix}`,
  phase: 'Scope audit',
  schema: AUDIT,
  effort: 'high',
  model: 'sonnet',
  agentType: SCOPE_AUDITOR,
})

async function runAudit(rs, gaps, suffix) {
  phase('Scope audit')
  return safeAgent(null, 'audit', auditPrompt(rs, gaps), auditOpts(`scope${suffix}`))
}

// The latest result per task, set once the tasks have run; empty before (auditOnly).
let RESULTS = new Map()

// Split an audit into task gaps (remediable in that task's tree) and wave-level
// gaps (returned to the orchestrator, never dispatched).
function splitAudit(a) {
  const missing = (a && a.missing) || []
  const taskGaps = missing.filter((m) => TASK_IDS.includes(m.taskId))
  // An approved item not landed is one gap: on the mapped task whose files own the
  // evidence path, else the first mapped task that is not clean, else the first mapped.
  for (const x of (a && a.approvals) || []) {
    const entry = x && x.landed !== true && APPROVALS.find((e) => e.id === x.id)
    if (!entry || !entry.tasks.length) continue
    const item = `Approved item ${x.id} not landed: ${x.evidence}`
    const evidence = String(x.evidence || '')
    const owns = (id) => ((byId.get(id) || {}).files || []).filter((f) => !f.includes('*') && !f.includes(' (')).some((f) => evidence.includes(stripDot(f)))
    const taskId =
      entry.tasks.find(owns) ||
      entry.tasks.find((id) => !(RESULTS.get(id) && RESULTS.get(id).clean)) ||
      entry.tasks[0]
    if (!taskGaps.some((g) => g.taskId === taskId && g.item === item)) taskGaps.push({ item, evidence: x.evidence, taskId })
  }
  const waveLevel = [
    ...((a && a.waveLevel) || []),
    ...missing.filter((m) => !TASK_IDS.includes(m.taskId)).map((m) => ({ item: m.item, evidence: m.evidence, taskId: m.taskId || null })),
  ]
  return { taskGaps, waveLevel }
}

const ESCALATE = ['round-cap', 'no-progress', 'gate-repeat', 'handoff-cap', 'review-shallow', 'dependency-failed', 'verify-agent-died', 'impl-agent-died', 'fix-agent-died', 'review-agent-died', 'agent-output-invalid', 'forward-merge-failed', 'land-failed']

// ---------------------------------------------------------------- forward merge
// Round-1 evidence: audit:scope-r2 found two remediation commits only on their
// task branches, never in the trees of the tasks built on them, so a dependent's
// green verify was measured without the fix. A clean remediation is merged into
// every same-repo dependent, dependencies first, and re-verified there.
const forwardMerged = []
const escalated = []
// Dependencies before dependents: an ancestor has strictly fewer ancestors.
const topo = (ids) => [...ids].sort((a, b) => ancestors(a).size - ancestors(b).size)

// The re-verify after a forward merge follows the verifier's rule: the task verify, else verify-task --targeted.
function mergeVerifySteps(d) {
  if (verifyCommand(d)) {
    return [
      `5. Run exactly this command: ${verifyCommand(d)}`,
      '   Set verification.passed from its real exit status and paste the tail, including the pass/fail',
      '   summary line, into verification.evidence.',
    ]
  }
  const acs = Array.isArray(d.ac) && d.ac.length ? d.ac : null
  const ace = acs ? AC_EVIDENCE_BY_ID.get(d.id) : null
  return [
    ...(acs ? ['5. Write this acceptance-condition JSON to a temp file outside the worktree (mktemp), exactly as given, and call its path $ACS:', JSON.stringify(acs)] : []),
    ...(ace ? ['6. Write this JSON to a second temp file outside the worktree (mktemp), exactly as given, and call its path $ACE:', JSON.stringify(ace)] : []),
    `${5 + (acs ? 1 : 0) + (ace ? 1 : 0)}. ${RUN_ONCE}`,
    `   ${verifyTaskCommand(d, `"${repoDir(d)}"`, [...(acs ? ['--acs "$ACS"'] : []), ...(ace ? ['--ac-evidence "$ACE"'] : []), '--no-triage'])}`,
    '   It prints one JSON object: verification.passed is its passed field, verification.command its command,',
    '   and verification.evidence its evidence tail, including the pass/fail summary line.',
  ]
}

function mergePrompt(d, branch) {
  return [
    `Merge a remediated dependency forward into plan task ${d.id}'s tree, then re-verify it.`,
    briefBlock(),
    valueLine(d),
    ...(forkPointOf(d) ? [`${d.id}'s own change is the diff from its fork point: git diff ${forkPointOf(d)}..HEAD.`] : []),
    `1. Run: ${mergeCommand(d, branch)}`,
    `   ${OWN_CHECKOUT_ONLY}`,
    '2. If the merge conflicts, stop: run git merge --abort, report conflict=true and merged=false.',
    '   Do not resolve a conflict by discarding either side; report it.',
    '3. Run `git rev-parse HEAD` and report it as head.',
    `4. ${INSTALL_DEPS}`,
    ...mergeVerifySteps(d),
    'Do not edit any file, amend, reset, rebase or switch branches. A command you did not run is passed=false.',
    helperRules('merge'),
    'Keep the whole report to at most 150 words.',
  ].join('\n')
}

// Lands a task again through the land step without moving its recorded fork point: the diff of
// everything it changed still starts where it first forked from the epic branch (D14).
async function relandTask(t, r) {
  const id = t.rootId || t.id
  const prior = FORK_POINTS.get(id)
  const out = await landTask(t, r)
  if (prior === undefined) FORK_POINTS.delete(id)
  else {
    FORK_POINTS.set(id, prior)
    const entry = LANDED.findLast((x) => x.id === id)
    if (entry) entry.forkPoint = prior
  }
  return out
}

// With LANDING a remediated dependency R is landed again first (rebased onto the epic branch, the
// epic branch fast-forwarded, verified in the integration tree); each live same-repo dependent then
// merges the epic branch rather than R's branch, re-verifies, and is landed again. A failed landing
// leaves the task land-failed in `latest`; the escalation sweep reports it.
async function forwardMerge(latest, remediated) {
  const live = (id) => {
    const r = latest.get(id)
    return r && r.impl && !ESCALATE.includes(r.reason) && r.reason !== 'blocked'
  }
  for (const R of topo(remediated)) {
    let rr = latest.get(R)
    if (!(rr && rr.clean && verified(rr.impl))) continue
    const from = byId.get(R)
    if (LANDING) {
      rr = await relandTask(rr.task, rr)
      latest.set(R, rr)
      if (rr.reason === 'land-failed') continue
    }
    const branch = LANDING ? BASE_REF : rr.impl.branch
    const dependents = TASK_IDS.filter((D) => D !== R && byId.get(D).repo === from.repo && ancestors(D).has(R) && live(D))
    for (const D of topo(dependents)) {
      const d = byId.get(D)
      let dr = latest.get(D)
      const result = await safeAgent(d, 'merge', mergePrompt(d, branch), {
        label: label('merge', d),
        phase: 'Merge',
        schema: MERGE,
        model: 'haiku',
      })
      if (result && result.merged === true && result.conflict !== true && result.verification && result.verification.passed === true) {
        forwardMerged.push({ into: D, from: R, branch, head: result.head })
        dr.impl = { ...dr.impl, verification: { ...result.verification, head: result.head } }
        log(`${D}: merged ${R}'s remediation (${branch}) forward, verified at ${result.head}`)
        if (LANDING) {
          dr = await relandTask(dr.task, dr)
          latest.set(D, dr)
        }
      } else {
        escalated.push({ id: D, reason: 'forward-merge-failed', findings: [], merge: result || null })
        log(`${D}: forward merge of ${branch} failed - escalating`)
      }
    }
  }
}

// ---------------------------------------------------------------- epic close
// auditOnly: the one scope audit of an epic, over tasks already built and
// verified. Nothing is implemented, verified, reviewed or remediated here: the
// gaps go back to the orchestrator, which turns them into new tasks in the epic.
if (AUDIT_ONLY) {
  log(`Epic-close audit of ${TASKS.length} task(s)`)
  phase('Scope audit')
  const a = await runEpicAudit()
  if (!a) {
    return {
      auditOnly: true,
      gaps: [{ item: 'epic-close audit did not run', evidence: 'auditor agent returned nothing', taskId: null }],
      approvals: [],
      duplicates: [],
      ...(AUDIT_ERRORS.length ? { auditError: AUDIT_ERRORS.join('; ') } : {}),
    }
  }
  const { taskGaps, waveLevel: wave } = splitAudit(a)
  return {
    auditOnly: true,
    gaps: [...taskGaps.map((g) => ({ item: g.item, evidence: g.evidence, taskId: g.taskId })), ...wave.map((w) => ({ item: w.item, evidence: w.evidence, taskId: w.taskId || null }))],
    approvals: a.approvals || [],
    duplicates: a.duplicates || [],
  }
}

log(`Executing ${TASKS.length} plan task(s) across ${new Set(TASKS.map((t) => t.repo)).size} repo(s)`)

const done = (await runTasks(TASKS)).filter(Boolean)
// latest result per plan task: a remediation run supersedes the original
const latest = new Map(done.map((r) => [r.task.rootId || r.task.id, r]))
RESULTS = latest

// audit 'off' (an epic run's default): no audit and no remediation; the epic-close
// audit covers scope once.
let audit = AUDIT_MODE === 'run' ? await runAudit(done, null, '') : null
// Only the first audit sweeps for duplicates; the re-check is scoped to the gaps.
const duplicates = (audit && audit.duplicates) || []
let rounds = 1
let waveLevel = []

if (AUDIT_MODE === 'off') {
  log('per-run scope audit off - the epic-close audit covers scope')
} else if (!audit) {
  log('scope auditor returned nothing - stopping rather than assuming the work is complete')
} else {
  const first = splitAudit(audit)
  waveLevel = first.waveLevel
  for (const w of waveLevel) log(`wave-level gap, returning it to the orchestrator: ${w.item}`)

  // One remediation task per plan task, carrying all of its gaps. Several agents
  // on one task's gaps would share its worktree, which has already cost a fight.
  const byTask = new Map()
  // A task that never started because a dependency failed stays escalated:
  // remediating it alone would run it without the code it was waiting for.
  const waiting = (id) => latest.get(id) && latest.get(id).reason === 'dependency-failed'
  for (const g of first.taskGaps) if (!waiting(g.taskId)) byTask.set(g.taskId, [...(byTask.get(g.taskId) || []), g])
  for (const r of latest.values()) {
    if (!verified(r.impl) && !ESCALATE.includes(r.reason) && r.reason !== 'blocked' && !byTask.has(r.task.id)) {
      byTask.set(r.task.id, [])
    }
  }

  if (byTask.size) {
    rounds = 2
    const batch = [...byTask.entries()].map(([id, gs]) => {
      const orig = TASKS.find((x) => x.id === id)
      return {
        ...orig,
        rootId: id,
        id: `${id}-r1`,
        short: `${orig.short}-r1`,
        title: `Finish: ${orig.title}`,
        requirement: [
          gs.length ? 'The scope audit found this unfinished:' : 'This task never demonstrated a passing verification run.',
          ...gs.map((g) => `- ${g.item}\n  evidence: ${g.evidence}`),
          `\nOriginal task requirement, still binding in full:\n${orig.requirement}`,
        ].join('\n'),
        notes: 'A previous round returned this as done when it was not. Deliver it completely this time.',
        // its dependencies already landed in the first round
        dependsOn: [],
      }
    })
    log(`Remediation round: ${batch.length} task(s) the audit found unfinished`)
    const rs = (await runTasks(batch)).filter(Boolean)
    done.push(...rs)
    for (const r of rs) latest.set(r.task.rootId, r)
    await forwardMerge(latest, [...byTask.keys()])

    const gaps = first.taskGaps.filter((g) => !waiting(g.taskId))
    if (gaps.length) {
      audit = await runAudit([...latest.values()], gaps, '-r2')
      const second = audit ? splitAudit(audit) : { taskGaps: gaps, waveLevel: [] }
      waveLevel.push(...second.waveLevel)
      for (const g of second.taskGaps) {
        escalated.push({ id: g.taskId, reason: 'audit-gap-persisted', findings: [{ item: g.item, evidence: g.evidence }] })
      }
    }
  }
}

for (const r of latest.values()) {
  if (ESCALATE.includes(r.reason) && (!r.processOnly || r.reason === 'review-shallow')) escalated.push({
      id: r.task.rootId || r.task.id,
      reason: r.reason,
      rounds: r.rounds,
      findings: r.findings || [],
      ...(r.mediumOnly ? { mediumOnly: true } : {}),
      ...(r.handoff ? { handoff: r.handoff } : {}),
      ...(r.split ? { split: r.split } : {}),
      ...(r.unread ? { unread: r.unread } : {}),
      ...(r.waitingOn ? { waitingOn: r.waitingOn } : {}),
      ...(r.agentError ? { agentError: r.agentError } : {}),
      ...(r.reason === 'land-failed' ? { land: r.land } : {}),
      ...(RULED.has(r.task.rootId || r.task.id) ? { ruling: RULED.get(r.task.rootId || r.task.id) } : {}),
    })
}
const blocked = [...latest.values()]
  .filter((r) => r.reason === 'blocked')
  .map((r) => ({ id: r.task.rootId || r.task.id, ...r.blocked, approvals: approvalsFor(r.task) }))

// ---------------------------------------------------------------- return
const finals = [...latest.values()]
const withTask = (key) => finals.flatMap((r) => ((r.impl && r.impl[key]) || []).map((d) => ({ taskId: r.task.rootId || r.task.id, ...d })))
const undelivered = withTask('undelivered').filter((d) => !MISATTRIBUTED.some((m) => m.taskId === d.taskId && m.what === d.what))
// Gaps outside a task's files: never findings; `ticket.py apply-run` makes each a todo task in the epic.
const discovered = withTask('discovered')
const auditClean =
  AUDIT_MODE === 'off' || (Boolean(audit) && splitAudit(audit).taskGaps.length === 0 && (rounds === 1 ? audit.complete : true))
// Each approved item's status, worst first: a blocked, then an escalated, then an
// unverified mapped task decides it.
const approvalStatus = (a) => {
  const any = (ids) => a.tasks.some((id) => ids.includes(id))
  if (any(blocked.map((b) => b.id))) return 'blocked'
  if (any(escalated.map((e) => e.id))) return 'escalated'
  const r = (id) => latest.get(id)
  if (a.tasks.some((id) => !verified(r(id) && r(id).impl))) return 'unverified'
  if (a.tasks.some((id) => !(r(id).clean || r(id).processOnly))) return 'unverified'
  return 'delivered'
}
const approvals = APPROVALS.map((a) => ({ id: a.id, text: a.text, tasks: a.tasks, status: approvalStatus(a) }))
const finished =
  approvals.every((a) => a.status === 'delivered') &&
  auditClean && duplicates.length === 0 && waveLevel.length === 0 && escalated.length === 0 && blocked.length === 0 && finals.every((r) => verified(r.impl)) &&
  finals.every((r) => r.clean || (r.processOnly && r.reason !== 'review-shallow'))

log(
  `Done: ${done.length} task-runs, ${finals.filter((r) => r.clean).length}/${finals.length} clean, ` +
    `${escalated.length} escalated, ${blocked.length} blocked, ${waveLevel.length} wave-level gap(s)`,
)

return {
  ...(EPIC ? { epic: EPIC } : {}),
  tasks: done.map((r) => ({
    id: r.task.id,
    repo: r.task.repo,
    worktree: r.task.worktree,
    clean: r.clean,
    rounds: r.rounds,
    stopped: r.reason || null,
    ...(forkPointOf(r.task) ? { forkPoint: forkPointOf(r.task) } : {}),
    ...(r.agentError ? { agentError: r.agentError } : {}),
    ...(r.panel ? { panel: true } : {}),
    complete: r.impl ? r.impl.complete : false,
    filesChanged: r.impl ? r.impl.filesChanged : [],
    branch: r.impl ? r.impl.branch : null,
    tests: r.impl ? r.impl.tests : null,
    verified: verified(r.impl),
    processOnly: r.processOnly === true,
    triageRejected: r.triageRejected === true,
    mediumOnly: r.mediumOnly === true,
    ...(RULED.has(r.task.id) ? { ruling: RULED.get(r.task.id) } : {}),
    ...('land' in r ? { land: r.land } : {}),
    verification: r.impl ? r.impl.verification : null,
    selfVerification: (r.impl && r.impl.selfVerification) || null,
    acsForAudit: ACS_FOR_AUDIT.get(r.task.rootId || r.task.id) || [],
    verifyRuns: VERIFY_BY_ROOT.get(r.task.rootId || r.task.id) || 0,
    triageUsage: TRIAGE_USAGE_BY_ROOT.get(r.task.rootId || r.task.id) || NO_USAGE,
    reviewsSkippedGateOnly: r.reviewsSkippedGateOnly || 0,
    processGaps: r.processGaps || [],
    declined: r.declined || [],
    cannotVerify: r.cannotVerify || [],
    misattributed: MISATTRIBUTED.filter((m) => m.taskId === (r.task.rootId || r.task.id)),
  })),
  // bookkeeping gaps reviewers found (notes, sweeps, ratchets, approvals): the orchestrator places these
  processGaps: done.flatMap((r) => (r.processGaps || []).map((g) => ({ taskId: r.task.rootId || r.task.id, ...g }))),
  // behaviours reviewers chose not to judge, and requirements they could not verify from the tree
  declined: done.flatMap((r) => (r.declined || []).map((d) => ({ taskId: r.task.rootId || r.task.id, what: d.what, why: d.why }))),
  cannotVerify: done.flatMap((r) => (r.cannotVerify || []).map((item) => ({ taskId: r.task.rootId || r.task.id, item }))),
  // tasks the loop handed back, each with its reason (gate-repeat, no-progress, round-cap, ...):
  // judge the findings, then fix, re-plan, or drop them
  escalated,
  // with args.rulingsFile: rulings read mid-run for unknown or unverified tasks, each with why
  ...(RULINGS_FILE ? { rulingsIgnored: [...RULINGS_IGNORED.values()] } : {}),
  // with landing (args.epic and args.mainCheckout): every task landed on the epic branch, in landing order
  ...(LANDING ? { landed: LANDED } : {}),
  // the verify script's Haiku triage cost (claude -p subprocesses), summed over every task
  triageUsage: [...TRIAGE_USAGE_BY_ROOT.values()].reduce(addUsage, NO_USAGE),
  // fix rounds that ran fixer, verifier and gates only, with no LLM review
  reviewsSkippedGateOnly: done.reduce((n, r) => n + (r.reviewsSkippedGateOnly || 0), 0),
  // external blockers no agent can clear, with who can
  blocked,
  // gaps that belong to no single task: the orchestrator places these
  waveLevel,
  // audit agents that threw (scope, remediation, epic-close); the run still returned
  ...(AUDIT_ERRORS.length ? { auditError: AUDIT_ERRORS.join('; ') } : {}),
  // remediated dependencies merged forward into their same-repo dependents
  forwardMerged,
  // the same part built in more than one task: reconcile to one before merging
  duplicates,
  // unplanned reusable parts implementers built, first claim per name
  provides: PROVIDED,
  unverified: finals.filter((r) => !verified(r.impl)).map((r) => r.task.rootId || r.task.id),
  branchesToCollect: finals.filter((r) => r.impl && r.impl.branch).map((r) => ({ id: r.task.rootId || r.task.id, repo: r.task.repo, branch: r.impl.branch })),
  undelivered,
  // undelivered entries that name another task's share or a path it owns: moved here, not findings
  misattributed: MISATTRIBUTED,
  discovered,
  // every approved item and whether it was delivered, blocked, escalated or left unverified
  approvals,
  // 'run' or 'off'; with 'off' no audit ran and scopeAudit is null
  audit: AUDIT_MODE,
  scopeAudit: AUDIT_MODE === 'off' ? null : audit || { complete: false, missing: [{ item: 'scope audit did not run', evidence: 'auditor agent returned nothing' }] },
  rounds,
  // true only when the audit confirmed everything landed, every task verified,
  // and nothing was escalated, blocked or left wave-level
  finished,
}
