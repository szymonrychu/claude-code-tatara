"""ticket.py migrate: convert old epic dirs to plans, keeping each in its phase folder.

An old epic dir holds README.md and no plan.md, plus any of design.md, tasks/, RETRO.md,
record.md, approvals.json, rulings.json and close.json. `migrate <epic>` or `migrate --all`
writes, per epic:

- plan.md: frontmatter title, repos, created, owner from the README, `rung` "1" in
  in-progress and done and "" in todo (a todo plan passes the gate before it can be claimed).
  Project brief and Description become What and why; Goals become one rung, `Rung 1: agreed
  scope (migrated)`; Non-goals stay; design.md Decisions, Open questions, Research (plus
  Research inputs) and Irreversible operations map to their sections; every other README or
  design.md section, and approvals.json as a list, is kept under `## Migrated notes` as
  `### <file>: <heading>`. README `## Time` is dropped (estimates are retired).
- implementation-plan.md, when the epic has tasks: one chunk (opus when any task was opus,
  else sonnet) of steps in dependency order, each with its status, files, verify, verified
  head and every task body section one level deeper; rulings.json as `## Rulings (migrated)`.
- retro.md, when RETRO.md or record.md existed: the Retro table split into What went well and
  What went wrong or could improve, Improvements as Recommendations, the generated block
  dropped, record.md under `## Delivery record (migrated)`.

Every epic is parsed before anything is written; any problem exits 1 listing all of them.
`--dry-run` writes nothing, runs in any checkout and prints what it would write and remove.
A real run (main checkout only) `git rm`s the old files, keeps close.json and commits each
plan alone as `chore(ticket): <plan> migrate`. Plan dirs holding plan.md are never touched.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path
from typing import NamedTuple

OLD_FILES = (
    "README.md",
    "design.md",
    "tasks",
    "RETRO.md",
    "record.md",
    "approvals.json",
    "rulings.json",
)
README_MAPPED = ("Project brief", "Description", "Goals", "Non-goals")
README_DROPPED = ("Time",)
DESIGN_MAPPED = (
    "Decisions",
    "Open questions",
    "Research",
    "Research inputs",
    "Irreversible operations in scope",
    "Irreversible operations",
)
RETRO_GENERATED = re.compile(
    r"<!-- retro:generated:begin -->.*?<!-- retro:generated:end -->\n?", re.S
)
RETRO_MAPPED = ("Retro", "Improvements")
NOT_RECORDED = "none recorded in the epic format"
FENCE = re.compile(r"^\s*(```|~~~)")


class Converted(NamedTuple):
    name: str
    dir: Path
    files: dict[str, str]  # file name -> text
    remove: list[str]  # old names present, "tasks/" for the dir
    steps: int


def register(sub, t) -> None:
    sp = sub.add_parser("migrate", help="convert old epic dirs to plan.md and friends")
    sp.set_defaults(fn=lambda a: run(a, t))
    sp.add_argument("epic", nargs="?")
    sp.add_argument("--all", action="store_true", help="every epic in todo, in-progress, done")
    sp.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")


# ---------------------------------------------------------------- markdown helpers


def split_sections(text: str) -> tuple[str, list[tuple[str, str]]]:
    """(preamble, [(H2 heading, text)]) of a markdown body; `## ` inside code fences is
    content. Texts are stripped of surrounding blank lines."""
    pre: list[str] = []
    out: list[tuple[str, list[str]]] = []
    fenced = False
    for line in text.split("\n"):
        if FENCE.match(line):
            fenced = not fenced
        m = None if fenced else re.match(r"^## (.+?)\s*$", line)
        if m:
            out.append((m.group(1), []))
        elif out:
            out[-1][1].append(line)
        else:
            pre.append(line)
    return "\n".join(pre).strip("\n"), [(h, "\n".join(ls).strip("\n")) for h, ls in out]


def shift(text: str, levels: int) -> str:
    """Every markdown heading outside code fences `levels` deeper."""
    out, fenced = [], False
    for line in text.split("\n"):
        if FENCE.match(line):
            fenced = not fenced
        if not fenced and re.match(r"^#{1,6} ", line):
            line = "#" * levels + line
        out.append(line)
    return "\n".join(out)


def drop_h1(text: str) -> str:
    return re.sub(r"\A\s*# [^\n]*\n?", "", text).strip("\n")


def number_goals(text: str) -> str:
    """Top-level `- ` bullets become `- 1.<m>: ` rung items; other lines stay."""
    out, k = [], 0
    for line in text.split("\n"):
        if line.startswith("- "):
            k += 1
            line = f"- 1.{k}: {line[2:]}"
        out.append(line)
    return "\n".join(out)


def _value(v) -> str:
    if isinstance(v, list):
        return ", ".join(_value(x) for x in v)
    if isinstance(v, str):
        return v
    return json.dumps(v)


def approval_lines(items: list) -> str:
    out = []
    for it in items:
        if isinstance(it, dict) and "id" in it and "text" in it:
            extra = "".join(
                f" [{k}: {_value(v)}]" for k, v in it.items() if k not in ("id", "text")
            )
            out.append(f"- {it['id']}: {it['text']}{extra}")
        else:
            out.append(f"- {json.dumps(it)}")
    return "\n".join(out)


def ruling_lines(items: list) -> str:
    out = []
    for it in items:
        if isinstance(it, dict) and {"task", "accept", "reason"} <= set(it):
            at = f", at {it['at']}" if "at" in it else ""
            rest = {k: v for k, v in it.items() if k not in ("task", "accept", "reason", "at")}
            extra = "".join(f" [{k}: {_value(v)}]" for k, v in rest.items())
            out.append(f"- {it['task']}: accept {_value(it['accept'])}{at}: {it['reason']}{extra}")
        else:
            out.append(f"- {json.dumps(it)}")
    return "\n".join(out)


def table_cells(row: str) -> list[str]:
    inner = row.strip()
    inner = inner[1:] if inner.startswith("|") else inner
    inner = inner[:-1] if inner.endswith("|") and not inner.endswith("\\|") else inner
    return [c.strip() for c in re.split(r"(?<!\\)\|", inner)]


def dependency_order(deps: dict[str, list[str]], t) -> list[str]:
    """Task slugs with every dependency first, ties in slug order; a cycle is an error."""
    left = {k: {d for d in v if d in deps and d != k} for k, v in deps.items()}
    selfloops = sorted(k for k, v in deps.items() if k in v)
    out: list[str] = []
    while left and not selfloops:
        ready = sorted(k for k, v in left.items() if not v)
        if not ready:
            break
        for k in ready:
            out.append(k)
            del left[k]
        for v in left.values():
            v.difference_update(ready)
    if selfloops or left:
        raise t.TicketError(f"dependency cycle among tasks: {', '.join(selfloops or sorted(left))}")
    return out


# ---------------------------------------------------------------- conversion


def _load_json(path: Path, problems: list[str]):
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text())
    except ValueError as e:
        problems.append(f"{path}: not valid JSON: {e}")
        return None
    if not isinstance(data, list):
        problems.append(f"{path}: expected a JSON list")
        return None
    return data


def _plan_md(t, d: Path, phase: str, readme, design: dict, approvals) -> str:
    m = readme.meta
    title = str(m.get("title") or d.name)
    pre, secs = split_sections(drop_h1(readme.body))
    rs = dict(secs)
    what = "\n\n".join(x for x in (rs.get("Project brief", ""), rs.get("Description", "")) if x)
    goals = rs.get("Goals", "")
    agreed = (
        "not agreed yet"
        if phase == "todo"
        else "Rung 1, migrated from the epic format: the epic's goals were its agreed scope."
    )
    research = design.get("Research", "")
    if design.get("Research inputs"):
        research = f"{research}\n\n### Research inputs\n\n{design['Research inputs']}".strip()
    irreversible = design.get("Irreversible operations in scope") or design.get(
        "Irreversible operations", ""
    )
    notes = []
    if pre:
        notes.append(("README.md: preamble", pre))
    notes += [(f"README.md: {h}", x) for h, x in secs if h not in README_MAPPED + README_DROPPED]
    notes += [(f"design.md: {h}", x) for h, x in design.items() if h not in DESIGN_MAPPED]
    if approvals is not None:
        notes.append(("approvals.json", approval_lines(approvals)))
    design_note = (
        "Migrated from the epic format; the design sections without a plan.md heading are "
        "under Migrated notes."
        if design
        else NOT_RECORDED
    )
    sections = [
        ("What and why", what or NOT_RECORDED),
        (
            "Scope ladder",
            f"### Rung 1: agreed scope (migrated)\n\n{number_goals(goals) or NOT_RECORDED}",
        ),
        ("Agreed scope", agreed),
        ("Non-goals", rs.get("Non-goals") or NOT_RECORDED),
        ("Design", design_note),
        ("Decisions", design.get("Decisions") or NOT_RECORDED),
        ("Open questions", design.get("Open questions") or "none"),
        ("Research", research or NOT_RECORDED),
        ("Irreversible operations", irreversible or "none"),
        (
            "Migrated notes",
            "\n\n".join(f"### {h}\n\n{shift(x, 1)}".rstrip() for h, x in notes) or "none",
        ),
    ]
    meta = {
        "title": title,
        "repos": list(m.get("repos") or []),
        "created": str(m.get("created") or ""),
        "owner": str(m.get("owner") or ""),
        "rung": "" if phase == "todo" else "1",
    }
    body = f"\n# {title}\n\n" + "".join(f"## {h}\n\n{x.strip()}\n\n" for h, x in sections)
    return t.dump(t.Doc(meta, body.rstrip("\n") + "\n"))


def _step(n: int, doc) -> str:
    m = doc.meta
    files = list(m.get("files") or []) or list(
        dict.fromkeys(list(m.get("owns") or []) + list(m.get("uses") or []))
    )
    verify = str(m.get("verify") or "")
    fields = [
        f"- Status: {m.get('status') or 'unknown'}",
        "- Files: " + (", ".join(f"`{f}`" for f in files) if files else "none"),
        f"- Verify: `{verify}`" if verify else "- Verify: none",
        f"- Verified head: {m.get('verified_head') or 'none'}",
    ]
    body = shift(drop_h1(doc.body), 2)
    title = str(m.get("title") or "")
    return f"### S{n}: {title}\n\n" + "\n".join(fields) + (f"\n\n{body}" if body else "")


def _implementation_md(title: str, phase: str, tasks: list, rulings, close) -> str:
    model = "opus" if any(str(d.meta.get("model")) == "opus" for d in tasks) else "sonnet"
    agreed = (
        "Not agreed yet: a draft migrated from the epic's tasks; the plan-writer revises it "
        "after the gate."
        if phase == "todo"
        else "Rung 1 of plan.md, migrated from the epic format: the steps are the epic's tasks."
    )
    verify = ((close or {}).get("integrationVerify") or {}).get("command", "")
    sections = [
        ("Agreed rung", agreed),
        (
            "Approach",
            "Migrated from the epic format: one step per task file, in dependency order, each "
            "with its status, files, verify, verified head and every body section.",
        ),
        (
            f"Chunk 1: migrated tasks (model: {model})",
            "\n\n".join(_step(i, d) for i, d in enumerate(tasks, 1)),
        ),
        ("Files to delete", NOT_RECORDED),
        ("Final verify", f"`{verify}`" if verify else NOT_RECORDED),
        ("After merge", "none"),
    ]
    if rulings is not None:
        sections.append(("Rulings (migrated)", ruling_lines(rulings) or "none"))
    return (
        f"# {title} implementation plan\n\n"
        + "".join(f"## {h}\n\n{x.strip()}\n\n" for h, x in sections).rstrip("\n")
        + "\n"
    )


def _retro_md(title: str, retro_text: str | None, record_text: str | None) -> str:
    review = ["Migrated from the epic format."]
    well: list[str] = []
    wrong: list[str] = []
    recs = ""
    if retro_text is not None:
        _, secs = split_sections(drop_h1(RETRO_GENERATED.sub("", retro_text)))
        for h, x in secs:
            if h == "Retro":
                rows = [ln for ln in x.split("\n") if ln.strip().startswith("|")]
                for row in rows[1:]:
                    if re.fullmatch(r"[\s|:-]*", row):
                        continue
                    cells = table_cells(row) + ["", ""]
                    for cell, bucket in ((cells[0], well), (cells[1], wrong)):
                        if cell and cell != "...":
                            bucket.append(f"- {cell}")
                rest = "\n".join(ln for ln in x.split("\n") if not ln.strip().startswith("|"))
                if rest.strip():
                    review.append(f"### RETRO.md: Retro\n\n{shift(rest.strip(), 1)}")
            elif h == "Improvements":
                recs = x
            elif h not in ("Tasks", "Deltas"):
                review.append(f"### RETRO.md: {h}\n\n{shift(x, 1)}")
    sections = [
        ("Review", "\n\n".join(review)),
        ("What went well", "\n".join(well) or NOT_RECORDED),
        ("What went wrong or could improve", "\n".join(wrong) or NOT_RECORDED),
        ("Recommendations", recs or "none"),
    ]
    if record_text is not None:
        sections.append(("Delivery record (migrated)", shift(drop_h1(record_text), 1)))
    return (
        f"# {title} retro\n\n"
        + "".join(f"## {h}\n\n{x.strip()}\n\n" for h, x in sections).rstrip("\n")
        + "\n"
    )


def convert(t, d: Path, problems: list[str]) -> Converted | None:
    """One old epic dir to its plan files, in memory; problems are appended, never raised."""
    before = len(problems)
    phase = d.parent.name
    readme = None
    try:
        readme = t.read_doc(d / "README.md")
    except t.TicketError as e:
        problems.append(str(e))
    design: dict[str, str] = {}
    if (d / "design.md").is_file():
        design = dict(split_sections(drop_h1((d / "design.md").read_text()))[1])
    tasks = {}
    for p in sorted((d / "tasks").glob("*.md")) if (d / "tasks").is_dir() else []:
        try:
            tasks[p.stem] = t.read_doc(p)
        except t.TicketError as e:
            problems.append(str(e))
    approvals = _load_json(d / "approvals.json", problems)
    rulings = _load_json(d / "rulings.json", problems)
    close = None
    if (d / "close.json").is_file():
        try:
            close = json.loads((d / "close.json").read_text())
        except ValueError as e:
            problems.append(f"{d / 'close.json'}: not valid JSON: {e}")
    try:
        order = dependency_order(
            {k: list(v.meta.get("depends_on") or []) for k, v in tasks.items()}, t
        )
    except t.TicketError as e:
        problems.append(f"{d}: {e}")
        order = []
    if len(problems) > before or readme is None:
        return None
    title = str(readme.meta.get("title") or d.name)
    files = {"plan.md": _plan_md(t, d, phase, readme, design, approvals)}
    ordered = [tasks[k] for k in order]
    if ordered:
        files["implementation-plan.md"] = _implementation_md(
            title, phase, ordered, rulings, close if isinstance(close, dict) else None
        )
    retro = d / "RETRO.md"
    record = d / "record.md"
    if retro.is_file() or record.is_file():
        files["retro.md"] = _retro_md(
            title,
            retro.read_text() if retro.is_file() else None,
            record.read_text() if record.is_file() else None,
        )
    remove = sorted(n + ("/" if (d / n).is_dir() else "") for n in OLD_FILES if (d / n).exists())
    return Converted(d.name, d, files, remove, len(ordered))


# ---------------------------------------------------------------- the command


def candidates(t, root: Path, epic: str | None, problems: list[str]) -> list[Path]:
    """Old epic dirs to migrate, phase then slug order."""
    if epic:
        d = t.find_plan(epic, root)
        if d is None:
            raise t.TicketError(f"unknown epic {epic!r} under {root}")
        return [] if (d / t.PLAN_FILE).is_file() else [d]
    out = []
    for phase in t.PHASES:
        base = root / phase
        for d in sorted(p for p in base.iterdir() if p.is_dir()) if base.is_dir() else []:
            if (d / t.PLAN_FILE).is_file():
                continue
            if not (d / "README.md").is_file():
                problems.append(f"{d}: no README.md or plan.md")
                continue
            out.append(d)
    return out


def _apply(t, c: Converted, root: Path) -> None:
    in_git = t._in_git(root)
    old = [c.dir / n.rstrip("/") for n in c.remove]
    if in_git:
        r = t._git(c.dir, "rm", "-r", "-q", "--ignore-unmatch", "--", *map(str, old))
        if r.returncode != 0:
            raise t.TicketError(f"git rm failed in {c.dir}: {r.stderr.strip()}")
    for p in old:
        if p.is_dir():
            shutil.rmtree(p)
        elif p.exists():
            p.unlink()
    for name, text in c.files.items():
        (c.dir / name).write_text(text)
    if in_git:
        _commit(t, c)


def _commit(t, c: Converted) -> None:
    """Commit the plan dir alone. Not a pathspec commit: on a case-insensitive checkout
    `git commit -- <dir>` refuses retro.md next to the RETRO.md still in HEAD, so the index
    is checked to hold nothing staged outside the dir instead."""
    top = Path(t._git(c.dir, "rev-parse", "--show-toplevel").stdout.strip())
    rel = c.dir.resolve().relative_to(top.resolve()).as_posix() + "/"
    add = t._git(top, "add", "-A", "--", rel)
    if add.returncode != 0:
        raise t.TicketError(f"git add failed: {add.stderr.strip()}")
    staged = t._git(top, "diff", "--cached", "--name-only").stdout.split("\n")
    outside = [f for f in staged if f and not f.startswith(rel)]
    if outside:
        raise t.TicketError(
            f"staged changes outside {rel}: {', '.join(outside)}; commit or unstage them first"
        )
    done = t._git(top, "commit", "-q", "-m", f"chore(ticket): {c.name} migrate")
    if done.returncode != 0:
        raise t.TicketError(f"git commit failed: {(done.stderr or done.stdout).strip()}")


def run(a, t) -> int:
    root = Path(a.root)
    if not a.epic and not a.all:
        raise t.TicketError("migrate needs <epic> or --all")
    if not a.dry_run:
        t.require_main_checkout(root)
    problems: list[str] = []
    dirs = candidates(t, root, None if a.all else a.epic, problems)
    converted = [c for c in (convert(t, d, problems) for d in dirs) if c]
    if problems:
        for p in problems:
            print(f"ticket.py: migrate: {p}", file=sys.stderr)
        return 1
    if not converted:
        print("migrate: nothing to change")
        return 0
    for c in converted:
        if a.dry_run:
            print(f"{c.name}: would write {', '.join(c.files)}; would remove {', '.join(c.remove)}")
            continue
        _apply(t, c, root)
        extra = ", retro.md" if "retro.md" in c.files else ""
        print(f"{c.name}: migrated ({c.steps} steps{extra})")
    return 0
