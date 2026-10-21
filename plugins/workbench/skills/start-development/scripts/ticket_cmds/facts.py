"""ticket.py facts: write the repo facts pack docs/plans/facts.md (D8).

One generated, gitignored file that planners and implementers read instead of each
re-deriving verify commands, AC ref conventions, registries and file owners. Rerunning
replaces it; the header carries the git HEAD it was generated at.
"""

import importlib.util
import re
import subprocess
from pathlib import Path

try:
    import tomllib
except ImportError:  # python < 3.11
    tomllib = None

FILE = "facts.md"
_T = None
_WB = None
_CONTRACT = None
_SAMPLES = {
    "pyproject.toml": "tests/test_sample.py",
    "package.xml": "tests/test_sample.py",
    "package.json": "sample.test.js",
}
_KINDS = [
    (
        "test",
        "a test name or `file::name` that passes; verify-task re-runs it with the runner "
        "for the ref's package root when the command output lacks it",
    ),
    ("symbol", "a function or class the diff adds or changes; ref is `file::symbol` or the symbol"),
    ("command", "a shell command run with `bash -lc`; passes on exit 0"),
    ("doc-section", "`<file>#<heading>` exists as a markdown heading"),
    ("judgement", "no mechanical proof; a reviewer decides"),
]


def _workbench():
    global _WB
    if _WB is None:
        p = Path(__file__).resolve().parents[4] / "scripts" / "lib" / "workbench.py"
        spec = importlib.util.spec_from_file_location("workbench_lib", p)
        _WB = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_WB)
    return _WB


def _contracts(root):
    global _CONTRACT
    if _CONTRACT is None:
        p = Path(__file__).resolve().with_name("contract.py")
        spec = importlib.util.spec_from_file_location("ticket_cmds.contract_facts", p)
        _CONTRACT = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_CONTRACT)
    return _CONTRACT.load_contracts(root)


def _git(d, *args) -> str:
    r = subprocess.run(["git", "-C", str(d), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def _repo_dirs(root: Path, epics: list) -> dict:
    """{repo name: checkout dir} for every repo the live epics name; the plans repo if none."""
    wb = _workbench()
    top = Path(_git(root, "rev-parse", "--show-toplevel") or root)
    names = sorted({r for e in epics for r in (e.meta.get("repos") or [])})
    found = wb.find_root(root)
    out = {}
    for n in names:
        d = wb.resolve(found[0], found[1], n) if found else None
        out[n] = d or top
    return out or {top.name: top}


def _mise_tasks(repo: Path) -> dict:
    out = {}
    for name in (".mise.toml", "mise.toml"):
        f = repo / name
        if not f.is_file():
            continue
        text = f.read_text()
        if tomllib:
            try:
                tasks = tomllib.loads(text).get("tasks", {})
            except ValueError:
                tasks = {}
            for k in ("test", "lint"):
                t = tasks.get(k)
                if isinstance(t, dict) and t.get("run") is not None:
                    run = t["run"]
                    out[k] = " && ".join(run) if isinstance(run, list) else str(run)
                elif isinstance(t, str):
                    out[k] = t
        else:
            for k in ("test", "lint"):
                m = re.search(rf'^\[tasks\.{k}\]\s*\n(?:.*\n)*?run\s*=\s*"([^"]*)"', text, re.M)
                if m:
                    out[k] = m.group(1)
        break
    return out


def _verify_section(repos: dict) -> list:
    wb = _workbench()
    lines = ["## Verify commands", ""]
    for name, d in repos.items():
        d = Path(d)
        top = Path(_git(d, "rev-parse", "--show-toplevel") or d)
        lines.append(f"### {name}")
        for k, v in _mise_tasks(top).items():
            lines.append(f"- {k}: {v}")
        for s in wb.load_config(top)["suites"]:
            lines.append(f"- suite: {s}")
        for f in _git(top, "ls-files").splitlines():
            marker = Path(f).name
            if marker not in _SAMPLES:
                continue
            pkg = Path(f).parent
            ref = (pkg / _SAMPLES[marker]).as_posix().removeprefix("./")
            r = wb.runner_for(ref, top)
            runner = (
                f"cd {Path(r['cwd']).relative_to(top) or '.'} && {' '.join(r['argv'])}"
                if r
                else "none"
            )
            lines.append(f"- package {f} ({marker}): {runner}")
        lines.append("")
    return lines


def _ref_section(repos: dict) -> list:
    wb = _workbench()
    lines = ["## AC ref conventions", "", "Evidence kinds (`evidence: {kind, ref}`):"]
    lines += [f"- `{k}`: {d}" for k, d in _KINDS]
    lines += [
        "",
        "A `test` ref is `file::name` with the file path relative to the repo. A ref whose "
        "path is not a file is looked up by basename among the diff's changed files, then "
        "`git ls-files`.",
        "Package runner rule: the ref runs from its package root (the nearest dir holding "
        "pyproject.toml, package.json or package.xml): pytest (uv run --frozen when uv.lock "
        "exists) for .py, vitest or `node --test` for .js/.mjs/.cjs/.ts, bats for .bats.",
        "",
        "refRunners (override the built-in runners):",
    ]
    any_rr = False
    for name, d in repos.items():
        for glob, cmd in wb.load_config(Path(d))["refRunners"].items():
            lines.append(f"- {name}: `{glob}` -> `{cmd}`")
            any_rr = True
    if not any_rr:
        lines.append("- none configured")
    lines.append("")
    return lines


def _registry_section(root: Path) -> list:
    lines = ["## Registries", ""]
    cs = _contracts(root)
    for c in cs:
        lines.append(
            f"- {c['name']} ({c['kind']}) owner={c['owner']} file={c['file']} "
            f"consumers={','.join(c.get('consumers', []))}"
            + (f" - {c['note']}" if c.get("note") else "")
        )
    if not cs:
        lines.append("- none registered")
    lines.append("")
    return lines


def _owners_section(tickets: list) -> list:
    lines = ["## File owners", ""]
    rows = []
    for t in tickets:
        if (
            t.kind != "task"
            or t.phase not in ("todo", "in-progress")
            or t.meta.get("status") == "done"
        ):
            continue
        for f in [*t.meta.get("owns", []), *t.meta.get("files", [])]:
            rows.append(f"{f} {t.epic}/{t.slug}")
    lines += sorted(set(rows)) or ["none"]
    lines.append("")
    return lines


def build(root: Path) -> str:
    tickets = _T.scan(root)
    epics = [t for t in tickets if t.kind == "epic" and t.phase in ("todo", "in-progress")]
    repos = _repo_dirs(root, epics)
    top = _git(root, "rev-parse", "--show-toplevel") or str(root)
    head = _git(top, "rev-parse", "HEAD") or "unknown"
    lines = [
        "# Repo facts pack",
        "",
        f"Generated by `ticket.py facts` at git HEAD {head}. Do not edit; rerun to refresh.",
        "",
    ]
    lines += (
        _verify_section(repos)
        + _ref_section(repos)
        + _registry_section(root)
        + _owners_section(tickets)
    )
    return "\n".join(lines).rstrip() + "\n"


def cmd_facts(a) -> int:
    root = Path(a.root)
    out = root / FILE
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(root))
    print(out.resolve())
    return 0


def register(sub, t) -> None:
    global _T
    _T = t
    sp = sub.add_parser("facts")
    sp.set_defaults(fn=cmd_facts)
