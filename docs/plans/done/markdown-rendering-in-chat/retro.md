# markdown rendering in chat retro

## Review

Migrated from the epic format.

## What went well

- Both tasks (chat markdown renderer, chat rows render markdown) closed in one review round: zero fix rounds, zero escalations.
- Points held: 8 estimated, 8 post-delivery, MdAPE 0.0%.
- Whole-epic review (sonnet) clean: XSS paths (raw HTML, links, images, code), row kinds, overflow and frame parsing checked.
- Scope audit: complete, no gaps, no duplicates. Security researcher skipped with a stated reason (no secrets, RBAC, ingress, privilege, CI vars or image pins in the diff; XSS covered by the reviewer).
- Full suite on the orchestrator run: `Test Files  45 passed (45)`, `Tests  524 passed (524)`, lint clean (.logs/md-web-full.log). Epic closed in about an hour of wall clock.

## What went wrong or could improve

- One unnamed vitest failure on the whole-epic reviewer's first full run (1 failed, 523 passed); two reruns and the orchestrator's run were green and it was treated as a load flake, but the failing test name and cause were not captured, so it can neither be fixed nor ruled out.
- Minutes and tokens came in under the seed on both tasks (12 actual vs 17 expected minutes; 1907006 vs 2821797 tokens); MdAPE minutes 43.8%, tokens 70.4%. chat rows render markdown ran 0.47x tokens, so the seed was loose, not tight.
- A reviewer misread its own malformed `tail` output as a failure and reran the verify, wasting a run.
- The bundle-size delta was measured through an uncommitted temporary import, so the figure cannot be reproduced from the tree; its value is unknown here.

## Recommendations

- Code:
  - agents-web chat markdown renderer: the epic left no committed test or script that measures its bundle cost; add a bundle-size check (or record the measurement command in MEMORY.md) so the delta is reproducible.
  - agents-web vitest suite: one test is flaky under load (name unknown); once a failure is captured, fix its timing dependence.
- Delivered differently:
  - none
- Tech debt:
  - Bundle-size delta for the markdown renderer rests on an uncommitted temporary import, not on anything in the tree; a committed size budget check would remove it.
  - Unidentified vitest load flake in agents-web, closed as a flake without a name; a captured failing test name would remove it.
- Workflow:
  - recurring (file-download-in-file-browse, paste-env-contents-into-the): minutes and tokens seeds are off for small tasks; there small pure-module and UI tasks came in at 0.17-0.46x and six of seven tasks at 0.55-0.82x minutes, here both tasks came in at 0.67-0.73x minutes and 0.47-0.78x tokens. Change: calibrate minutes and tokens seeds by task kind from earlier epics' actuals (small UI and pure-module tasks lower).
  - Reviewers should capture the failing test name and the output tail when a first full run fails, and rerun only after saving it; add a line to the reviewer brief (one-off, Retro table only).
  - A reviewer misread malformed `tail` output as a failure (one-off, Retro table only).

## Delivery record (migrated)

### Asked

Render markdown in the chat window, for the user's own input and the agents' responses (GFM: headings, lists, emphasis, links, inline code, fenced code blocks, tables). Raw HTML in message text must not render (shown as text). Non-goals: no backend storage or send change, no editing toolbar or live preview.

### Shipped

agents-web 03f05da..06cfd54 (4 commits plus merge): react-markdown 10.1.0, remark-gfm 4.0.1 and remark-breaks 4.0.0; `ChatMarkdown` in `src/chat/Markdown.tsx` (MUI-mapped elements, raw HTML as text, links in a new tab with unsafe URLs dropped, images as links, fenced code with a language label and no highlighter); user, assistant, session and peer rows use it. `src/chat/chatModel.ts` unchanged. Epic review verdict: pass (2026-10-27); scope audit complete, no gaps.
PR https://github.com/szymonrychu/agents-web/pull/18 merged (CI green: web, images, chart). Not deployed: gate is one deploy epic for the four epics later.
Full suite (orchestrator run): `Test Files  45 passed (45)`, `Tests  524 passed (524)`, lint clean. Bundle main chunk 1,194.11 kB to 1,364.08 kB (+169.97 kB, gzip +50.94 kB), measured with an uncommitted temporary import in `main.tsx` (MEMORY.md).

### Tasks

| Task | Status | Verified head | Review rounds | Verification tail |
|---|---|---|---|---|
| chat-markdown-renderer | done | c2693f2310c7808442dabe7ae0e16315bf7bed62 (in epic git log) | clean at first review, 0 fix rounds | `Tests  23 passed (23)` |
| chat-rows-render-markdown | done | 12e1b773d6d5025bae927ca354712825cb2970ac (in epic git log) | clean at first review, 0 fix rounds | `Tests  50 passed (50)` |

Both task files have an empty `review:` frontmatter field and only a dated `done` line under Notes; rounds and tails are from the orchestrator's notes, not the files.

### Rulings

- Security researcher skipped. Why: the diff touches no secrets, RBAC, ingress, privilege, CI vars or image pins; the epic reviewer covered XSS paths (raw HTML, links, images, code). Cost if wrong: an unreviewed security class in the diff ships; the PR is merged and not deployed, so a finding would be fixed before the deploy epic.
- One unnamed vitest failure on the epic reviewer's first full run (1 failed, 523 passed) judged a load flake. Why: two reruns and the orchestrator's own full run were green, and the known environment note records load-dependent 5000 ms timeouts in the full suite. Cost if wrong: an intermittent real failure stays in the suite and surfaces later as a flaky main.

### Discovered and blocked

- Discovered: the failing test in the reviewer's first full run was never named and its cause not captured. Who can clear it: the next agent to run the full suite on agents-web, by capturing the failing test name from the log.
- Blocked: deploy. Waits on the later deploy epic for the four epics; the user decides when it runs.
- Epic README frontmatter lists `blockers: [file-download-in-file-browse]`; the PR is merged, so whether that blocker is cleared is for the user to confirm: unknown from the files.
- Bundle size is not measured from a committed build: the +170 kB figure comes from an uncommitted temporary import, so the real figure shows in the first production build after merge.

### Not pushed

- agents-web: nothing; `main` equals `origin/main` and contains merge 06cfd54.
- Workbench superrepo: 18 commits on local `main` are ahead of `origin/main` (ticket commits including "advance agents-web to 06cfd54", the markdown-rendering-in-chat done move and retro, and other epics' ticket commits). The superrepo working tree also had uncommitted edits under `docs/plans/todo/matrix-connector-agent-initi/` at the start of the session. The user pushes.
- `RETRO.md` still holds the template placeholders in its Retro and Improvements sections; retro-writer fills them.

### Lessons routed to

- Unnamed flake in a full-suite run: add a check to the epic-review step so the reviewer must quote the failing test name from the log before calling a failure a flake (a rule in the reviewer prompt, since it is a judgement call, not mechanical).
- Task files left `review:` empty and held only a `done` note: add a `ticket.py` check at task close that fails when `review` is empty, so the record can read rounds from the files.
- Bundle size depends on an uncommitted import: add a build-size assertion or script to agents-web (a vitest or `mise` task that reports the main chunk size) so the figure is reproducible without a temporary edit.
