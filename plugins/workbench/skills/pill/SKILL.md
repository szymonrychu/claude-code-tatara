---
name: pill
description: "Produce a study PDF (a 'pill') on a topic: cited primary-source research via research subagents, optional in-pod measurements for empirical questions, pandoc-style markdown with numbered references and hand-written SVG diagrams, rendered to PDF with a pure-pip stack and delivered by kubectl cp into a pod that mounts the books library writable. Use when the user asks for a pill, a study PDF, a reading pack or an explainer document on a topic."
---

# pill

Turns a topic (and an optional list of questions) into a short, cited study PDF and
drops it into the books library through a pod that mounts it, so it shows up in the e-reader apps. The
research is fanned out to the workbench research agents, the writing and the
diagrams are done in the calling thread, and three scripts do the mechanical
parts:

| Script | Does | Needs |
|---|---|---|
| `scripts/lint_text.py` | fails on em dashes, smart quotes and unicode arrows | stdlib |
| `scripts/render.py` | markdown + SVG figures -> PDF with cover, contents, page numbers, captions | the venv |
| `scripts/deliver.py` | `send`: kubectl cp, size check, prints the in-pod and node paths; `discover`: finds a pod mounting the books dir writable | kubectl |

`S=${CLAUDE_PLUGIN_ROOT}/skills/pill/scripts` below.

## Arguments

- `topic` (required): one line.
- `questions` (optional): the questions the pill must answer, in order.
- `page`: `a4` (default) or `phone` (100x178 mm, fills a phone screen).
- `namespace`, `pod`, `container`, `dir`: delivery overrides; otherwise
  `PILL_K8S_NAMESPACE` (default `media`), `PILL_K8S_POD` (pod name or name
  prefix) or `PILL_K8S_SELECTOR` (label selector), `PILL_K8S_CONTAINER`,
  `PILL_K8S_DIR` (in-pod dir). Unset values come from the best writable
  `discover` candidate (step 6).

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

6. **Deliver.** Check the target first:
   ```
   python3 $S/deliver.py discover [-n NS] [-l SELECTOR] [--match books]
   ```
   Read-only, one `kubectl get pods -o json`: for every running container it
   joins the volumeMounts with their volume source (hostPath with subPath, or
   PVC), and lists the mounts whose mountPath or hostPath contains `books`, as
   `rw|ro  pod  container  in_pod_dir  node_path  via`. A parent hostPath mount
   (node `/media/hdd` at `/media`) that holds a books node dir seen in any pod
   yields the derived dir `/media/books`. Writable mounts rank first, books
   before audiobooks, reader apps (Jellyfin, Audiobookshelf) before the rest;
   read-only ones are listed but never chosen. The last line is
   `suggested: PILL_K8S_NAMESPACE=... PILL_K8S_POD=... PILL_K8S_CONTAINER=... PILL_K8S_DIR=...`.
   Use it when it is a books (not audiobooks or video) dir; otherwise ask the
   user in writing, with the candidates. Then:
   ```
   python3 $S/deliver.py send $W/<date>-<slug>.pdf [-n NS] [--pod P | -l SEL] [-c C] [--dir D]
   ```
   It checks that `tar` runs in the container (kubectl cp needs it; with no tar,
   pick another pod mounting the same node dir), runs `mkdir -p` only for a dir
   under a writable mount of that container, copies with `kubectl cp`, compares
   the remote size (`stat -c %s`, `ls -ln` fallback) with the local one and
   prints `delivered: <ns>/<pod>:<dir>/<file>.pdf (container C, N bytes)` and
   `node path: <hostPath>/<file>.pdf`. `--dry-run` reads the pods and prints the
   write commands only.

7. **Report** in a few lines: the in-pod and node paths from the `send` output,
   page count, the questions answered, and any question left open (with why).

## Never

- Cite a source you did not read, or a number you did not measure or find in a
  cited source.
- Hardcode a private host or path in a pill or a script: namespaces, pods and
  dirs come from arguments or `PILL_K8S_*`.
- Change the cluster beyond the one file in the chosen books dir: no applies,
  restarts or exec writes elsewhere; `discover` changes nothing.
