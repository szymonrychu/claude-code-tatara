// Acceptance-condition lint. The parking words live once, in plan-execute.js
// (the DEBT_MARKERS line); this module reads them from there, never copies them.
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

const PLAN_EXECUTE = fileURLToPath(new URL('./plan-execute.js', import.meta.url))
const CODE_MARKERS = new Set(['TODO', 'FIXME', 'XXX', 'HACK'])
const ROUND_N = 'round N (any number)'

export function debtMarkers() {
  const m = /^const DEBT_MARKERS = '(.*)'$/m.exec(readFileSync(PLAN_EXECUTE, 'utf8'))
  if (!m) throw new Error('ac-lint: no one-line `const DEBT_MARKERS = ...` in plan-execute.js')
  return m[1].split(',').map((w) => w.trim()).filter(Boolean)
}

const escapeRe = (w) => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

// Matches in text order; backtick spans are ignored so the phase name `todo` never hits.
export function parkingMatches(text) {
  const plain = String(text ?? '').replace(/`[^`]*`/g, ' ')
  const hits = []
  for (const w of debtMarkers()) {
    const code = CODE_MARKERS.has(w)
    const src = w === ROUND_N ? '\\bround \\d+\\b' : code ? `\\b${w}\\b` : escapeRe(w)
    for (const m of plain.matchAll(new RegExp(src, code ? 'g' : 'gi'))) hits.push({ at: m.index, match: w === ROUND_N || !code ? m[0].toLowerCase() : m[0] })
  }
  return hits.sort((a, b) => a.at - b.at).map((h) => h.match)
}

export function lintAc(tasks, { require = false } = {}) {
  const msgs = []
  for (const t of tasks) {
    const acs = Array.isArray(t.ac) ? t.ac : []
    if (!acs.length) {
      if (require) msgs.push(`tasks: ${t.id} has no acceptance conditions (ac)`)
      continue
    }
    const texts = [t.requirement, ...acs.map((a) => a?.text), t.notes]
    for (const text of texts) for (const m of parkingMatches(text)) msgs.push(`tasks: ${t.id} parks work: "${m}"`)
  }
  return msgs
}
