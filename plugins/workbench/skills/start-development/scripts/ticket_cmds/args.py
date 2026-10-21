"""ticket.py args: build the plan-execute args JSON and its named copy from one command.

build_args is the one builder of the run args (D10, D13); `continue` reuses it. Done tasks
leave the run: they are dropped from tasks, from dependsOn and from the approval ledger,
because plan-execute rejects approvals and dependencies that name tasks outside the run.
"""

import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[4]
LENSES = ["correctness", "requirements-coverage"]
FACTS = Path("docs") / "plans" / "facts.md"
_BRIEF = re.compile(r"^(What|How|Why):[ \t]*(.*)$", re.M)


def _workbench():
    p = PLUGIN_ROOT / "scripts" / "lib" / "workbench.py"
    spec = importlib.util.spec_from_file_location("workbench_args", p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("workbench_args", mod)
    spec.loader.exec_module(mod)
    return mod


def _brief(readme: Path, t) -> dict:
    body = t._read_doc(readme).body if readme.is_file() else ""
    sec = re.search(r"^## Project brief\s*\n(.*?)(?=^## |\Z)", body, re.M | re.S)
    text = sec.group(1) if sec else ""
    out = {"what": "", "how": "", "why": ""}
    marks = list(_BRIEF.finditer(text))
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out[m.group(1).lower()] = (m.group(2) + text[m.end() : end]).strip()
    return out


def _plan_text(epic: str, brief: dict, done: list[dict], open_: list[dict]) -> str:
    def line(x):
        return f"- {x['id']}: {x['title']}"

    lines = [
        f"THIS run's scope: {len(open_)} open task(s) of epic {epic}. {brief['what']}".strip(),
        "",
        "OPEN (this run builds and audits these):",
    ]
    lines += [line(x) for x in open_]
    lines += ["", "DONE (do not re-audit, do not rebuild):"]
    lines += [line(x) for x in done] or ["- none"]
    return "\n".join(lines)


def build_args(epic_dir, context_pack=None, t=None) -> dict:
    if t is None:
        import ticket as t
    epic_dir = Path(epic_dir)
    epic = epic_dir.name
    plans_root = epic_dir.parent.parent
    all_tasks = t.derive_tasks(epic_dir)
    status = {p.stem: t._read_doc(p).meta.get("status", "todo") for p in t._task_files(epic_dir)}
    done_ids = {x["id"] for x in all_tasks if status.get(x["id"]) == "done"}
    open_ = [
        dict(x, dependsOn=[d for d in x["dependsOn"] if d not in done_ids])
        for x in all_tasks
        if x["id"] not in done_ids
    ]
    if not open_:
        raise t.TicketError(f"no open tasks in {epic}; nothing to run")
    done = [x for x in all_tasks if x["id"] in done_ids]
    approvals = []
    path = epic_dir / "approvals.json"
    for entry in json.loads(path.read_text()) if path.is_file() else []:
        left = [i for i in entry.get("tasks", []) if i not in done_ids]
        if left:
            approvals.append(dict(entry, tasks=left))
    brief = _brief(epic_dir / "README.md", t)
    wb = _workbench()
    repos = sorted({x["repo"] for x in open_ if x["repo"]})
    top = plans_root.parent.parent
    pack = context_pack or (str(top / FACTS) if (top / FACTS).is_file() else "")
    return {
        "epic": epic,
        "name": epic,
        "brief": brief,
        "tasks": open_,
        "approvals": approvals,
        "planText": _plan_text(epic, brief, done, open_),
        "designDoc": str(epic_dir / "design.md"),
        "planDoc": str(epic_dir / "README.md"),
        "contextPack": pack,
        "overlapIgnore": sorted(
            {g for r in repos for g in wb.config_for_repo(plans_root, r)["overlapIgnore"]}
        ),
        "rulingsFile": str(epic_dir / "rulings.json"),
        "baseRef": t.integration_branch(epic),
        "mainCheckout": str(top.resolve()),
        "verifierAgent": "workbench:verifier",
        "lenses": list(LENSES),
    }


def write_args_and_copy(epic_dir, out_dir, context_pack, t) -> str:
    """Write <out_dir>/<epic>-args.json and the named copy; return the copy's script path."""
    data = build_args(epic_dir, context_pack, t)
    epic = data["epic"]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    f = out_dir / f"{epic}-args.json"
    f.write_text(json.dumps(data, indent=2) + "\n")
    r = subprocess.run(
        [
            "node",
            str(PLUGIN_ROOT / "workflows" / "named-copy.mjs"),
            "plan-execute",
            epic,
            str(out_dir),
            "--args",
            str(f),
        ],
        capture_output=True,
        text=True,
    )
    if r.returncode != 0:
        raise t.TicketError(f"named-copy failed: {r.stderr.strip()}")
    return r.stdout.strip().splitlines()[-1]


def run(a, t) -> int:
    epic_dir = t.resolve_epic(a.epic, Path(a.root))
    print(write_args_and_copy(epic_dir, a.out_dir, a.context_pack, t))
    return 0


def register(sub, t) -> None:
    sp = sub.add_parser("args", help="write the plan-execute args JSON and its named copy")
    sp.set_defaults(fn=lambda a: run(a, t))
    sp.add_argument("epic")
    sp.add_argument("--out-dir", required=True)
    sp.add_argument("--context-pack", default=None)
