---
name: pill
description: "Produce a study PDF (a 'pill') on a topic: cited primary-source research via research subagents, optional in-pod measurements for empirical questions, pandoc-style markdown with numbered references and hand-written SVG diagrams, rendered to PDF with a pure-pip stack and delivered by scp to the NAS books directory. Use when the user asks for a pill, a study PDF, a reading pack or an explainer document on a topic."
---

# pill

Turns a topic (and an optional list of questions) into a short, cited study PDF and
drops it into the NAS books library, so it shows up in the e-reader apps. The
research is fanned out to the workbench research agents, the writing and the
diagrams are done in the calling thread, and three scripts do the mechanical
parts:

| Script | Does | Needs |
|---|---|---|
| `scripts/lint_text.py` | fails on em dashes, smart quotes and unicode arrows | stdlib |
| `scripts/render.py` | markdown + SVG figures -> PDF with cover, contents, page numbers, captions | the venv |
| `scripts/deliver.py` | `send`: mkdir, scp, size check, prints the remote path; `discover`: finds the books dir | ssh, scp |

`S=${CLAUDE_PLUGIN_ROOT}/skills/pill/scripts` below.

## Arguments

- `topic` (required): one line.
- `questions` (optional): the questions the pill must answer, in order.
- `page`: `a4` (default) or `phone` (100x178 mm, fills a phone screen).
- `host`, `user`, `dir`: delivery overrides; otherwise `PILL_NAS_HOST` (default
  `nas.lan`), `PILL_NAS_USER` (default: what ssh picks, e.g. `~/.ssh/config`),
  `PILL_NAS_DIR` (no default, see step 6), `PILL_NAS_PORT`.

## Procedure

1. **Scope.** Restate the topic in one line, list the questions (write 3-6 yourself
   when none were given, and say so), pick a kebab-case `<slug>`. The pill's working
   dir is `W=$(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lib/workbench.py scratchpad pill-<slug>)`
   with `research/`, `measurements/` and `figures/` under it. Tool logs go to
   `$(python3 ${CLAUDE_PLUGIN_ROOT}/scripts/lib/workbench.py logs pill-<slug>)`.

2. **Research (parallel).** In ONE message, dispatch the research agents with
   `model: opus`, each told the topic, the questions and its output file
   `$W/research/<lens>.md`:
   - `workbench:research-docs-purist`: specs, official docs, man pages, source code.
   - `workbench:research-paper-scout`: when the topic has a scientific core.
   - `workbench:research-practitioner`: when operational reality matters.
   Every claim in a brief carries a numbered source: title, URL, publisher or
   author, date, and the exact section or line. Primary sources only (specs, RFCs,
   official docs, papers, source code at a tag); a blog may point at a primary
   source but is never cited for the claim itself. Then dispatch
   `workbench:research-reviewer` (`model: sonnet`) over the briefs to verify each
   claim against its source; drop or fix what it refutes. Mechanics as in
   `workbench:start-research`, without writing to `docs/research/`.

3. **Measure (only for empirical questions).** When a question asks how fast,
   how big or how often, measure in the pod instead of quoting folklore:
   - Record the environment first: `uname -a`, `nproc`, the CPU model from
     `/proc/cpuinfo`, the cgroup CPU and memory limits
     (`/sys/fs/cgroup/cpu.max`, `/sys/fs/cgroup/memory.max`).
   - Use `time` / `/usr/bin/time -v`, `vmstat 1 5`, `perf stat -e ...` (check
     `/proc/sys/kernel/perf_event_paranoid`; when perf is missing or denied, say so in
     the pill, never invent counters), `hyperfine` if installed.
   - At least 3 runs; report median and range. Save each command and its raw
     output to `$W/measurements/<n>-<name>.txt` and quote it in the pill.
   - State the caveat: a shared node in a pod is noisy and capped by cgroups.

4. **Write `$W/pill.md`.** Start from `references/pill-template.md`; `references/example-figure.svg` shows the SVG conventions. Rules:
   - Front matter: `title`, `subtitle`, `author`, `date` (becomes the cover).
   - Answer every question under its own `#` or `##` heading; `#` and `##`
     headings make the contents page.
   - Cite as `[n]`, numbered in order of first use, matching the numbered
     `# References` list at the end (title, author or publisher, date, URL).
     Footnotes (`[^x]`) are for asides, not sources.
   - Plain hyphens and straight quotes, no em dashes, no smart quotes, no
     unicode arrows (`->` is fine). Keep code lines under ~70 columns (`a4`) or
     ~40 (`phone`); `pre` blocks do not wrap.
   - **Figures** are hand-written SVG files in `$W/figures/`, included as
     `![Caption text](figures/name.svg)` alone on a line, which becomes
     "Figure N. Caption text". Draw what the text explains (a data path, a
     state machine, a timeline), one idea per figure. The renderer (svglib) has
     limits, so:
     - set `width`, `height` and `viewBox` on the root; figures wider than the
       text column are scaled down;
     - use presentation attributes (`fill=`, `stroke=`), not `<style>` blocks or
       CSS classes;
     - draw arrowheads as `<polygon>`s: `marker-end` is silently ignored;
     - `font-family="Helvetica"` (or `Courier`), ASCII text only;
     - no `<foreignObject>`, filters, masks or embedded raster images.

5. **Render.**
   ```
   PY=$(bash $S/setup_venv.sh)                      # creates/reuses the venv, prints its python
   python3 $S/lint_text.py $W/pill.md $W/figures/*.svg
   $PY $S/render.py $W/pill.md -o $W/<date>-<slug>.pdf [--page phone] [--html $W/pill.html]
   ```
   `render.py` runs the same lint itself and refuses to render on a hit; fix the
   text rather than passing `--skip-lint`. The stack is pure pip (markdown ->
   HTML with print CSS -> xhtml2pdf/reportlab, SVG via svglib): no pandoc, typst,
   LaTeX, chromium or pango needed. `setup_venv.sh` puts the venv at `$PILL_VENV`,
   else `<scratchpad>/pill/venv`. A "No font ... has a glyph" warning means a
   character outside Latin-1 slipped in; replace it.
   Read the PDF back (page count, contents page, a figure page) before delivering.

6. **Deliver.** When neither `dir` nor `PILL_NAS_DIR` is set, find the books dir first:
   ```
   python3 $S/deliver.py discover [--host H] [--user U]
   ```
   Read-only, over ssh: lists the Jellyfin and Audiobookshelf containers' docker
   mounts, the Jellyfin library paths (`root/default/<library>/options.xml` and
   `*.mblink` under the config dir; native installs under `/var/lib/jellyfin`),
   and the Audiobookshelf library folders (`absdatabase.sqlite`, opened
   read-only), maps container paths to host paths and prints candidates, books
   before audiobooks before the rest, with a `suggested: PILL_NAS_DIR=...` line.
   Use the suggestion when it is a books (not audiobooks or video) library;
   otherwise ask the user in writing, with the candidates. Then:
   ```
   python3 $S/deliver.py send $W/<date>-<slug>.pdf --dir <books dir> [--host H] [--user U]
   ```
   It runs `mkdir -p` remotely, copies with scp in BatchMode (never prompts),
   compares the remote byte count with the local one and prints
   `delivered: [user@]host:/dir/<file>.pdf (N bytes)`. `--dry-run` prints the
   three commands only. A BatchMode auth failure means no usable key: report it,
   do not retry interactively.

7. **Report** in a few lines: the exact remote path from the `delivered:` line,
   page count, the questions answered, and any question left open (with why).

## Never

- Cite a source you did not read, or a number you did not measure or find in a
  cited source.
- Hardcode a private host or path in a pill or a script: hosts and dirs come from
  arguments or `PILL_NAS_*`.
- Write to the NAS outside the chosen books dir; `discover` changes nothing.
