#!/usr/bin/env python3
"""Verify one task's worktree: the exact checks an LLM verifier used to approximate.

Prints one JSON object and exits 0 whenever it produced it (2 on usage errors):
  head, clean, command, exit, passed, evidence, installed, debtMarkers, parking,
  changedSincePrevious, diffstat, acs, tierHint, tdd, note

The script holds no marker list and no test-file pattern: --markers (plan-execute's
DEBT_MARKERS) and --test-re (its TEST_FILE_RE source) are both required. A marker
containing " N (any number)" matches that word followed by digits.
It never commits, stashes, resets or switches branches. --tdd-revert rewrites files
in the tree and always puts the HEAD state back, then re-checks that the tree is clean.
Judgement calls go to triage.py (Haiku); --no-triage skips them.
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import time
import tokenize
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "lib"))

import workbench  # noqa: E402

PASS_RE = re.compile("(?<!not )(?<!\\w)(PASSED|ok|pass|\u2714)(?!\\w)")  # \u2714 = node pass
FAIL_RE = re.compile("\\bFAILED\\b|\\bnot ok\\b|\u2716")
MD_EXT = {".md", ".markdown", ".rst", ".txt"}
HASH_EXT = {".sh", ".bash", ".bats", ".yml", ".yaml", ".toml", ".rb", ".tf", ".mk", ".cfg", ".ini"}
SLASH_EXT = {".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".go", ".java", ".rs", ".c", ".h", ".kt"}
HASH_COMMENT = re.compile(r"(?:^|\s)#(?!!)\s*(.*)")
SLASH_COMMENT = re.compile(r"(?://|^\s*/\*+|^\s*\*(?!/))\s*(.*)")


# ---- process helpers ----


DEFAULT_TIMEOUT = 540
TIMEOUT_EXIT = 124
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


class Deadline:
    """One wall-clock budget shared by every command a call runs, from construction on."""

    def __init__(self, seconds: float):
        self.seconds = seconds
        self.end = time.monotonic() + seconds
        self.skipped: list = []

    def remaining(self) -> float:
        return max(0.0, self.end - time.monotonic())


def _left(t):
    """Seconds a command may still run: the deadline's remainder, or a plain number as given."""
    return t.remaining() if isinstance(t, Deadline) else t


def _secs(t):
    return t.seconds if isinstance(t, Deadline) else t


def _expired(t, step: str) -> bool:
    """True (and `step` recorded in t.skipped) when the shared deadline is already spent."""
    if isinstance(t, Deadline) and t.remaining() <= 0:
        t.skipped.append(step)
        return True
    return False


class Output(str):
    """Combined command output; `timed_out` is True when the time limit killed the run."""

    timed_out = False


def _popen_bounded(argv: list, cwd: str, timeout: float | None, **kw) -> tuple:
    """(exit, stdout or None, timed_out). On expiry the whole process group is killed."""
    p = subprocess.Popen(argv, cwd=cwd, start_new_session=True, **kw)
    try:
        out, _ = p.communicate(timeout=timeout)
        return p.returncode, out, False
    except subprocess.TimeoutExpired as e:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        partial = e.output
        if isinstance(partial, bytes):
            partial = partial.decode(errors="replace")
        try:
            rest, _ = p.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            rest = None
        # e.output and the post-kill read both hold the full capture on POSIX; keep the longer.
        return TIMEOUT_EXIT, max(partial or "", rest or "", key=len), True


def run_shell(cmd: str, cwd: str, timeout: float | None = None) -> tuple[int, str]:
    """`bash -lc cmd` in cwd, stdout and stderr merged. Exit 124 (output.timed_out) on expiry."""
    code, out, timed_out = _popen_bounded(
        ["bash", "-lc", cmd],
        cwd,
        timeout,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
    )
    res = Output(out or "")
    res.timed_out = timed_out
    return code, res


def output_tail(out: str, lines: int = 10, chars: int = 1000) -> str:
    """Last `lines` lines of combined output, at most `chars` characters."""
    return "\n".join(out.rstrip("\n").splitlines()[-lines:])[-chars:]


def run_argv(argv: list, cwd: str, timeout: float | None = None) -> int:
    """Exec argv directly (no shell). 127 when the program is missing, 124 on expiry."""
    try:
        return _popen_bounded(
            argv, cwd, timeout, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )[0]
    except FileNotFoundError:
        return 127


def git(cwd: str, *args: str, raw: bool = False, check: bool = True):
    p = subprocess.run(["git", *args], cwd=cwd, capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr.decode(errors='replace').strip()}")
    return p.stdout if raw else p.stdout.decode(errors="replace")


def is_clean(cwd: str) -> bool:
    return git(cwd, "status", "--porcelain").strip() == ""


# ---- install ----


def _install_cmds(root: Path, locked_only: bool) -> list:
    """Install commands for one package root; `locked_only` demands a lockfile (ref roots)."""
    cmds = []
    if (root / "package.json").exists() and not (root / "node_modules").exists():
        if (root / "pnpm-lock.yaml").exists():
            cmds.append(["pnpm", "install", "--frozen-lockfile"])
        elif (root / "yarn.lock").exists():
            cmds.append(["yarn", "install", "--immutable"])
        elif (root / "package-lock.json").exists() or not locked_only:
            cmds.append(["npm", "ci"])
    if (root / "pyproject.toml").exists() and not (root / ".venv").exists():
        if (root / "uv.lock").exists():
            cmds.append(["uv", "sync", "--frozen"])
    return cmds


def _uv_unlocked(root: Path) -> bool:
    """A [project] pyproject.toml with no uv.lock and no .venv: nothing to sync reproducibly."""
    py = root / "pyproject.toml"
    if not py.exists() or (root / ".venv").exists() or (root / "uv.lock").exists():
        return False
    return re.search(r"^\[project\]", py.read_text(errors="replace"), re.M) is not None


def ref_package_roots(cwd: str, specs: list) -> list:
    """Package roots (other than the worktree root) of the test refs in `specs`, in order."""
    top, roots = Path(cwd).resolve(), []
    for a in specs:
        ev = a.get("evidence") or {}
        if (ev.get("kind") or a.get("kind")) != "test":
            continue
        path = _name_of(ev.get("ref") or a.get("ref") or "")[0].removeprefix("./")
        if not path:
            continue
        r = workbench.package_root(top / path, top)
        if r != top and r not in roots:
            roots.append(r)
    return roots


def install_deps(cwd: str, extra_roots: list = (), timeout: float | None = None) -> list:
    """Install at the worktree root, then once at each distinct ref package root."""
    out = []
    for root, strict in [(Path(cwd), False), *[(Path(r), True) for r in extra_roots]]:
        for c in _install_cmds(root, strict):
            if _expired(timeout, "install: " + " ".join(c)):
                continue
            code = run_argv(c, str(root), _left(timeout))
            out.append({"cmd": " ".join(c), "exit": code})
            if code == TIMEOUT_EXIT:
                out[-1]["timeout"] = {"command": " ".join(c), "seconds": _secs(timeout)}
        if _uv_unlocked(Path(root)):
            why = f"no uv.lock in {root}: nothing to sync reproducibly"
            out.append({"cmd": "uv sync --frozen", "skipped": why})
    return out


# ---- diff ----


def added_lines(cwd: str, base: str, head: str = "HEAD") -> list:
    """[{file, line, text}] for every line added since `base` (git diff -U0)."""
    out, path, n = [], None, 0
    for raw in git(cwd, "diff", "-U0", "--no-renames", base, head).splitlines():
        if raw.startswith("+++ "):
            path = None if raw == "+++ /dev/null" else raw[6:]
        elif raw.startswith("@@"):
            m = re.match(r"@@ -\S+ \+(\d+)", raw)
            n = int(m.group(1)) if m else 0
        elif raw.startswith("+") and path:
            out.append({"file": path, "line": n, "text": raw[1:]})
            n += 1
    return out


_PLACEHOLDER = "\x00"
_MOVED_MIN = 12


def _moved_norm(text: str) -> str:
    """Text normalized for moved-text comparison: JS string quoting, `+` concatenation,
    backslash escapes, `${...}` (-> placeholder), heading/list markers, case and whitespace gone."""
    t = re.sub(r"\$\{[^}]*\}", _PLACEHOLDER, text)
    t = re.sub(r"['\"`]\s*\+\s*['\"`]", "", t)
    t = t.replace("\\n", " ").replace("\\t", " ")
    t = re.sub(r"\\(.)", r"\1", t)
    t = t.strip(" \t'\"`+,:")
    t = re.sub(r"^(#+|[-*])\s+", "", t)
    return re.sub(r"\s+", " ", t).strip().lower()


def removed_keys(cwd: str, base: str) -> list:
    """One normalized corpus per file: all text the diff since `base` removes from it, joined.
    Each corpus is paired with a copy that has the interpolation placeholders dropped."""
    per, path = {}, None
    for raw in git(cwd, "diff", "-U0", "--no-renames", base, "HEAD").splitlines():
        if raw.startswith("--- "):
            path = raw[4:]
        elif raw.startswith("-") and path:
            k = _moved_norm(raw[1:])
            if k:
                per.setdefault(path, []).append(k)
    out = []
    for parts in per.values():
        c = " ".join(parts)
        out += [c, re.sub(r"\s+", " ", c.replace(_PLACEHOLDER, ""))]
    return out


def drop_moved(lines: list, removed: list) -> list:
    """The added lines whose text is not also in the removed corpus (moved, not new)."""

    def moved(x: dict) -> bool:
        k = _moved_norm(x["text"])
        return len(k) >= _MOVED_MIN and any(k in c for c in removed)

    return [x for x in lines if not moved(x)]


def ref_added_keys(cwd: str, refs: list, base: str) -> set:
    """(file, normalized text) of every line each ref adds relative to merge-base(ref, base)."""
    keys = set()
    for ref in refs:
        mb = git(cwd, "merge-base", ref, base).strip()
        keys |= {(x["file"], _moved_norm(x["text"])) for x in added_lines(cwd, mb, ref)}
    return keys


def drop_excluded(lines: list, keys: set) -> tuple:
    """(kept, dropped count): lines whose (file, normalized text) a merged dependency added go."""
    kept = [x for x in lines if (x["file"], _moved_norm(x["text"])) not in keys]
    return kept, len(lines) - len(kept)


def name_status(cwd: str, a: str, b: str = "HEAD") -> list:
    rows = []
    for raw in git(cwd, "diff", "--name-status", "--no-renames", a, b).splitlines():
        status, _, path = raw.partition("\t")
        if path:
            rows.append({"file": path, "status": status[0]})
    return rows


def marker_regexes(markers: str) -> list:
    out = []
    for m in (x.strip() for x in markers.split(",")):
        if not m:
            continue
        if " N (any number)" in m:
            pat = re.escape(m).replace(re.escape(" N (any number)"), r" \d+")
            out.append((m, re.compile(r"\b" + pat + r"\b", re.I)))
        elif re.fullmatch(r"[A-Z]+", m):
            out.append((m, re.compile(rf"\b{m}\b")))
        else:
            out.append((m, re.compile(re.escape(m), re.I)))
    return out


QUOTED_SPAN = re.compile(r'`[^`]*`|"[^"]*"')


def scannable(x: dict) -> str:
    """The text of an added line that the debt and parking checks look at.

    Markdown prose that quotes a word (inline code, straight double quotes) is
    documenting it, not using it, so quoted spans are blanked; code files are untouched.
    """
    if Path(x["file"]).suffix.lower() in MD_EXT:
        return QUOTED_SPAN.sub(" ", x["text"])
    return x["text"]


def blank_string_literals(text: str, hash_comments: bool) -> str:
    """`text` with the inside of '...', "..." and `...` literals blanked; comments are kept."""
    out, quote, i = [], None, 0
    while i < len(text):
        c = text[i]
        if quote:
            if c == "\\":
                out.append("  "[: len(text[i : i + 2])])
                i += 2
                continue
            out.append(quote if c == quote else " ")
            quote = None if c == quote else quote
        elif c in "'\"`":
            quote = c
            out.append(c)
        elif text.startswith("//", i) or (hash_comments and c == "#"):
            out.append(text[i:])
            break
        else:
            out.append(c)
        i += 1
    return "".join(out)


def find_debt(lines: list, markers: str, test_re=None) -> list:
    """Debt markers on added lines. In test files a marker word that sits only inside a
    string literal is fixture data, not debt; comments and code outside literals still count."""
    regs = marker_regexes(markers)

    def text_of(x: dict) -> str:
        t = scannable(x)
        if test_re and test_re.search(x["file"]) and Path(x["file"]).suffix.lower() not in MD_EXT:
            return blank_string_literals(t, Path(x["file"]).suffix.lower() not in SLASH_EXT)
        return t

    return [
        {"file": x["file"], "line": x["line"], "marker": m}
        for x in lines
        for m, rx in regs
        if rx.search(text_of(x))
    ]


# ---- parking candidates ----


def _py_comment_and_doc_lines(src: str) -> dict:
    """{line: text} for comments (tokenize) and docstring lines (ast) of Python source."""
    found = {}
    try:
        for tok in tokenize.generate_tokens(io.StringIO(src).readline):
            if tok.type == tokenize.COMMENT:
                found[tok.start[0]] = tok.string.lstrip("# ").strip()
        tree = ast.parse(src)
        lines = src.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef):
                body = node.body
                if body and isinstance(body[0], ast.Expr):
                    v = body[0].value
                    if isinstance(v, ast.Constant) and isinstance(v.value, str):
                        for i in range(body[0].lineno, body[0].end_lineno + 1):
                            found[i] = lines[i - 1].strip()
    except (tokenize.TokenError, SyntaxError, IndentationError):
        pass
    return found


def parking_candidates(cwd: str, lines: list) -> list:
    cache, out = {}, []
    for x in lines:
        ext = Path(x["file"]).suffix.lower()
        text = x["text"]
        if ext in MD_EXT:
            text = scannable(x)
            if text.strip():
                out.append({**x, "text": text.strip()})
        elif ext == ".py":
            if x["file"] not in cache:
                cache[x["file"]] = _py_comment_and_doc_lines(
                    git(cwd, "show", f"HEAD:{x['file']}", check=False)
                )
            t = cache[x["file"]].get(x["line"])
            if t:
                out.append({**x, "text": t})
        else:
            rx = HASH_COMMENT if ext in HASH_EXT else SLASH_COMMENT if ext in SLASH_EXT else None
            m = rx.search(text) if rx else None
            if m and m.group(1).strip():
                out.append({**x, "text": m.group(1).strip()})
    return out


# ---- acceptance conditions ----


def _name_of(ref: str) -> tuple:
    path, _, name = ref.partition("::")
    return path, name


def _passing_line(output: str, ref: str) -> str | None:
    path, name = _name_of(ref)
    for line in output.splitlines():
        if (ref in line or (name and name in line)) and PASS_RE.search(line):
            if not FAIL_RE.search(line):
                return line.strip()
    return None


def _resolve_path(cwd: str, path: str, changed: list) -> tuple:
    """(path, problem) for a ref's path part. A path that is not a repo-relative file is
    looked up by basename among the diff's changed files, then `git ls-files`."""
    if not path or Path(cwd, path).is_file():
        return path, ""
    base = Path(path).name
    for pool in (
        [c["file"] for c in changed if c["status"] != "D"],
        git(cwd, "ls-files", check=False).splitlines(),
    ):
        hits = sorted({f for f in pool if Path(f).name == base})
        if len(hits) == 1:
            return hits[0], ""
        if hits:
            return path, f"ambiguous ref: {len(hits)} files named {base}"
    return path, f"no file named {base}"


def _section(cwd: str, ref: str) -> tuple:
    """(exists, text) of the markdown-style heading `<file>#<heading>`."""
    path, _, heading = ref.partition("#")
    f = Path(cwd, path)
    if not heading or not f.is_file():
        return False, ""
    want = heading.strip().lower()
    lines = f.read_text(errors="replace").splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^#{1,6}\s+(.*?)\s*#*\s*$", line)
        if m and m.group(1).strip().lower() == want:
            body = []
            for nxt in lines[i + 1 : i + 41]:
                if re.match(r"^#{1,6}\s", nxt):
                    break
                body.append(nxt)
            return True, "\n".join(body)
    return False, ""


def _test_name_missing(cwd: str, path: str, name: str) -> bool:
    """True when a .py/.js/.mjs ref names a test its file lacks (or the file is missing)."""
    ext = Path(path).suffix
    if not name or ext not in (".py", ".js", ".mjs"):
        return False
    f = Path(cwd, path)
    if not f.is_file():
        return True
    text = f.read_text(errors="replace")
    if ext == ".py":
        *classes, func = re.sub(r"\[.*\]$", "", name).split("::")
        if classes:
            m = re.search(rf"^class {re.escape(classes[-1])}\b.*?(?=^class |\Z)", text, re.M | re.S)
            text = m.group(0) if m else ""
        return not re.search(rf"\bdef {re.escape(func)}\(", text)
    return not re.search(rf"\b(?:test|it)\(\s*(['\"`]){re.escape(name)}\1", text)


def _test_names(cwd: str, path: str) -> list:
    """The test names a .py/.js/.mjs file defines."""
    f = Path(cwd, path)
    if not f.is_file():
        return []
    text = f.read_text(errors="replace")
    if f.suffix == ".py":
        return re.findall(r"^[ \t]*(?:async\s+)?def (test\w*)\(", text, re.M)
    if f.suffix in (".js", ".mjs"):
        return [m[1] for m in re.findall(r"\b(?:test|it)\(\s*(['\"`])(.+?)\1", text)]
    return []


def resolve_test_ref(
    cwd: str, ac_id: str, ref: str, output: str, changed: list, ace: dict
) -> tuple:
    """(ref, rpath, problem, matchedBy) for a `test:` AC: the acEvidence entry for its id when
    that file defines the name, else the exact ref, else the single test in the ref's file whose
    name contains the ref's name or is contained in it (D2). No match keeps the exact ref."""
    entry = ace.get(ac_id)
    if isinstance(entry, str) and "::" in entry:
        epath, problem = _resolve_path(cwd, _name_of(entry)[0], changed)
        if not _test_name_missing(cwd, epath, _name_of(entry)[1]):
            return epath + entry[len(_name_of(entry)[0]) :], epath, problem, "acEvidence"
    path, name = _name_of(ref)
    rpath, problem = _resolve_path(cwd, path, changed)
    if _passing_line(output, ref) or not _test_name_missing(cwd, rpath, name):
        return ref, rpath, problem, "exact"
    plain = bool(name) and "::" not in name and "[" not in name
    hits = sorted({n for n in _test_names(cwd, rpath) if plain and (name in n or n in name)})
    if len(hits) == 1:
        return f"{path}::{hits[0]}", rpath, problem, "substring"
    return ref, rpath, problem, ""


def _runner_cmd(argv: list) -> str:
    """The command a runner executes: a refRunners `bash -c <cmd>` shows as <cmd>."""
    return argv[2] if argv[:2] == ["bash", "-c"] else " ".join(argv)


def _config_file(cwd: str) -> str:
    """The repo-relative workbench.json path (config dir resolved per harness)."""
    try:
        return f"{workbench.config_dir(Path(cwd)).name}/workbench.json"
    except workbench.ConfigError:
        return "workbench.json"


def check_ac(
    cwd: str,
    ac: dict,
    output: str,
    changed: list,
    timeout: float | None = None,
    ace: dict | None = None,
) -> dict:
    ev = ac.get("evidence") or {}
    kind = ev.get("kind") or ac.get("kind")
    ref = ev.get("ref") or ac.get("ref") or ""
    res = {"id": ac["id"], "kind": kind, "ref": ref, "met": False, "how": "", "snippet": ""}
    if kind == "test":
        ref, rpath, problem, matched = resolve_test_ref(
            cwd, ac["id"], ref, output, changed, ace or {}
        )
        if matched:
            res.update(matchedBy=matched, resolvedRef=ref)
        line = _passing_line(output, ref)
        runner = workbench.runner_for(rpath + ref[len(_name_of(ref)[0]) :], Path(cwd))
        tname = _name_of(ref)[1]
        if line:
            res.update(met=True, how="ref passed in command output", snippet=line)
        elif _test_name_missing(cwd, rpath, tname):
            res.update(
                refMissing=True,
                how=f"ref-missing: no test named `{tname}` in {rpath}; "
                "add or rename a test to exactly this name and file"
                + (f" ({problem})" if problem else ""),
            )
        elif runner and _expired(timeout, f"ac {ac['id']}: {_runner_cmd(runner['argv'])}"):
            res["how"] = "skipped: shared deadline reached"
        elif runner:
            code = run_argv(runner["argv"], runner["cwd"], _left(timeout))
            where = os.path.relpath(runner["cwd"], Path(cwd).resolve())
            cmd = _runner_cmd(runner["argv"])
            res.update(
                met=code == 0,
                how=f"re-ran ({runner['source']}, {where}) {cmd}: exit {code}"
                + (f" ({problem})" if problem else ""),
            )
            if code == TIMEOUT_EXIT:
                res["timeout"] = {"command": cmd, "seconds": _secs(timeout)}
        else:
            res["how"] = (
                f"ref not in command output and no runner for {rpath}: "
                f"add a refRunners entry in {_config_file(cwd)}"
            )
    elif kind == "symbol":
        path, _, sym = ref.partition("::")
        files = [c["file"] for c in changed if c["status"] != "D"]
        if sym and path in files:
            files, ref_sym = [path], sym
        else:
            ref_sym = ref
        for f in files:
            lines = (
                Path(cwd, f).read_text(errors="replace").splitlines()
                if Path(cwd, f).is_file()
                else []
            )
            for i, line in enumerate(lines):
                if ref_sym in line:
                    ctx = "\n".join(lines[max(0, i - 2) : i + 3])
                    res.update(met=True, how=f"found in {f}:{i + 1}", snippet=ctx)
                    break
            if res["met"]:
                break
        if not res["met"]:
            res["how"] = "not found in any file the diff adds or changes"
    elif kind == "command":
        if _expired(timeout, f"ac {ac['id']}: {ref}"):
            res["how"] = "skipped: shared deadline reached"
            return res
        code, out = run_shell(ref, cwd, _left(timeout))
        if out.timed_out:
            res["timeout"] = {"command": ref, "seconds": _secs(timeout)}
        res.update(
            met=code == 0,
            how=f"ran {ref} verbatim: whole command exit {code}",
            snippet=out[-500:],
            exit=code,
            tail=output_tail(out),
        )
    elif kind == "doc-section":
        ok, body = _section(cwd, ref)
        res.update(
            met=ok,
            how="heading found" if ok else "heading or file missing",
            snippet=body,
        )
    else:
        res.update(met=None, how="judgement: left to the reviewer")
    return res


def plausibility_asks(acs: list, texts: dict, diff_text: str) -> list:
    """The ACs whose evidence needs a judgement call; obvious matches are answered without one."""
    from triage import _tokens

    ask = []
    for a in acs:
        text = texts[a["id"]]
        if a["kind"] in ("doc-section", "judgement") or (
            a["kind"] in ("test", "symbol") and not (_tokens(a["ref"]) & _tokens(text))
        ):
            snippet = a["snippet"] or (diff_text if a["kind"] == "judgement" else "")
            ask.append(
                {
                    "id": a["id"],
                    "text": text,
                    "kind": a["kind"],
                    "ref": a["ref"],
                    "snippet": snippet[:2000],
                    "met": a["met"],
                }
            )
    return ask


def set_plausibility(acs: list, asked: set, got: dict | None) -> None:
    """got maps id -> verdict; None means the call failed, so asked ACs stay unjudged (null)."""
    for a in acs:
        if a["id"] not in asked:
            a["plausible"] = None
        else:
            a["plausible"] = None if got is None else got.get(a["id"], "unsure")
        del a["snippet"]


# ---- targeted commands ----


def _spec_test_files(specs: list) -> list:
    """The `file` part of every AC test: ref, in order, deduplicated."""
    files = []
    for a in specs:
        ev = a.get("evidence") or {}
        if (ev.get("kind") or a.get("kind")) != "test":
            continue
        path = _name_of(ev.get("ref") or a.get("ref") or "")[0]
        if path and path not in files:
            files.append(path)
    return files


def runner_commands(cwd: str, files: list, changed: list) -> list:
    """One runner command per test file (check_ac's runner resolution), deduplicated.
    A runner that starts outside the worktree root is prefixed with `cd <dir> &&`."""
    top, cmds = Path(cwd).resolve(), []
    for f in files:
        rpath, _ = _resolve_path(cwd, f, changed)
        runner = workbench.runner_for(rpath, Path(cwd))
        if not runner:
            continue
        cmd = _runner_cmd(runner["argv"])
        where = os.path.relpath(runner["cwd"], top)
        if where != ".":
            cmd = f"(cd {shlex.quote(where)} && {cmd})"
        if cmd not in cmds:
            cmds.append(cmd)
    return cmds


def targeted_command(cwd: str, specs: list, changed: list, test_re) -> str:
    """Runner commands of the AC test refs and the changed test files, joined with ` && `."""
    files = _spec_test_files(specs)
    for c in changed:
        if c["status"] != "D" and test_re.search(c["file"]) and c["file"] not in files:
            files.append(c["file"])
    return " && ".join(runner_commands(cwd, files, changed))


# ---- diffstat and tdd revert ----


def diffstat(cwd: str, base: str, test_re) -> dict:
    stat = {"files": 0, "addedNonTest": 0, "addedTest": 0}
    for raw in git(cwd, "diff", "--numstat", "--no-renames", base, "HEAD").splitlines():
        added, _, rest = raw.partition("\t")
        path = rest.partition("\t")[2]
        n = int(added) if added.isdigit() else 0
        stat["files"] += 1
        stat["addedTest" if test_re.search(path) else "addedNonTest"] += n
    return stat


def _head_modes(cwd: str) -> dict:
    modes = {}
    for line in git(cwd, "ls-tree", "-r", "HEAD").splitlines():
        meta, _, path = line.partition("\t")
        modes[path] = meta.split()[0]
    return modes


def _merge_module():
    """worktree-merge's module: the one empty-directory pruner."""
    import importlib.util

    p = Path(__file__).resolve().parents[1] / "skills" / "worktree-merge" / "scripts" / "merge.py"
    spec = importlib.util.spec_from_file_location("worktree_merge", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def prune_deleted_dirs(cwd: str, changes: list) -> list:
    """Remove directories left empty by the diff's deletions."""
    gone = [c["file"] for c in changes if c["status"] == "D"]
    return _merge_module().prune_empty_dirs(Path(cwd), gone) if gone else []


def _put(cwd: str, rev: str, path: str, mode: str | None, made: list | None = None) -> None:
    f = Path(cwd, path)
    if made is not None:
        d = f.parent
        while not d.exists() and d != Path(cwd):
            made.append(d)
            d = d.parent
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(git(cwd, "show", f"{rev}:{path}", raw=True))
    if mode:
        f.chmod(0o755 if mode == "100755" else 0o644)


def _restore(cwd: str, changes: list, modes: dict, made: list | None = None) -> None:
    for c in changes:
        if c["status"] == "D":
            Path(cwd, c["file"]).unlink(missing_ok=True)
        else:
            _put(cwd, "HEAD", c["file"], modes.get(c["file"]))
    prune_deleted_dirs(cwd, changes)
    for d in sorted(set(made or []), key=lambda p: len(p.parts), reverse=True):
        try:
            d.rmdir()
        except OSError:
            pass


def tdd_revert(
    cwd: str,
    base: str,
    base_command: str,
    test_re,
    head_exit: int,
    timeout: float | None = None,
) -> dict:
    """Run `base_command` on the base state; passedOnHead reuses the main run's exit code."""
    changes = [c for c in name_status(cwd, base) if not test_re.search(c["file"])]
    res = {
        "ran": False,
        "failedOnBase": None,
        "passedOnHead": None,
        "files": [],
        "baseCommand": base_command,
    }
    res["files"] = sorted(c["file"] for c in changes)
    if not changes or _expired(timeout, f"tdd-revert: {base_command}"):
        return res
    modes = _head_modes(cwd)
    made: list = []
    try:
        for c in changes:
            if c["status"] == "A":
                Path(cwd, c["file"]).unlink(missing_ok=True)
            else:
                _put(cwd, base, c["file"], None, made)
        code, out = run_shell(base_command, cwd, _left(timeout))
        res["failedOnBase"] = code != 0
        if out.timed_out:
            res["timeout"] = {"command": base_command, "seconds": _secs(timeout)}
        _restore(cwd, changes, modes, made)
        res["passedOnHead"] = head_exit == 0
        res["ran"] = True
    except Exception as e:
        res["error"] = f"{type(e).__name__}: {e}"
    finally:
        _restore(cwd, changes, modes, made)
    return res


# ---- main ----


def build(argv: list, triage_run=None) -> tuple:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--cmd", help="run exactly as given via bash -lc (default: --targeted)")
    ap.add_argument(
        "--targeted",
        action="store_true",
        help="build the command from the runners of the AC test refs and changed test files",
    )
    ap.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="one shared deadline in seconds, measured from the start of the call, across "
        "the main run, AC ref runs, the tdd-revert base run and triage; the running "
        "command's process group is killed when it is reached and later steps are listed "
        f"in `skipped` ({DEFAULT_TIMEOUT})",
    )
    ap.add_argument("--base", required=True, help="ref whose merge-base with HEAD is the base")
    ap.add_argument("--markers", required=True, help="comma-separated debt markers")
    ap.add_argument("--test-re", required=True, help="regex matching test file paths")
    ap.add_argument("--worktree", default=".", help="worktree (default: current directory)")
    ap.add_argument("--triage-log", help="JSONL file triage.py appends one line per call to")
    ap.add_argument("--install", action="store_true", help="install missing dependencies first")
    ap.add_argument("--acs", help="JSON file: list of {id, text, evidence: {kind, ref}}")
    ap.add_argument("--ac-evidence", help="JSON file: {AC id: final file::name of its test}")
    ap.add_argument("--prev-head", help="previous round's HEAD, for changedSincePrevious")
    ap.add_argument("--requirement", default="", help="task requirement, for the tier hint")
    ap.add_argument(
        "--exclude-ref",
        action="append",
        default=[],
        help="ref of a merged dependency (repeatable): the lines it adds are not gated here",
    )
    ap.add_argument("--no-triage", action="store_true", help="skip every Haiku call")
    ap.add_argument("--no-tier", action="store_true", help="skip the tier call")
    ap.add_argument("--tdd-revert", action="store_true", help="run the command on the base state")
    args = ap.parse_args(argv)
    if args.prev_head is not None and not SHA_RE.match(args.prev_head):
        return 2, {
            "passed": False,
            "error": f"prev-head is not a sha: {args.prev_head[:40]}",
        }
    try:
        test_re = re.compile(args.test_re)
    except re.error as e:
        ap.error(f"--test-re: {e}")
    deadline = Deadline(args.timeout)
    cwd = str(Path(args.worktree).resolve())
    usage = {"calls": 0, "input_tokens": 0, "output_tokens": 0}
    if not args.no_triage and triage_run is None:
        import triage

        def triage_run(mode, data):
            return triage.run(mode, data, log=args.triage_log, usage=usage)

    notes = ["triage skipped (--no-triage)"] if args.no_triage else []

    clean_before = is_clean(cwd)
    specs = json.loads(Path(args.acs).read_text()) if args.acs else []
    installed = install_deps(cwd, ref_package_roots(cwd, specs), deadline) if args.install else []
    base = git(cwd, "merge-base", "HEAD", args.base).strip()
    changed = name_status(cwd, base)
    prune_deleted_dirs(cwd, changed)
    targeted = args.targeted or not args.cmd
    command = targeted_command(cwd, specs, changed, test_re) if targeted else args.cmd
    if not command:
        return 0, {
            "head": git(cwd, "rev-parse", "HEAD").strip(),
            "command": "",
            "commandScope": "targeted",
            "passed": False,
            "error": "no targeted tests",
        }
    timeout = None
    if _expired(deadline, f"verify: {command}"):
        code, output = TIMEOUT_EXIT, Output("")
        timeout = {"command": command, "seconds": args.timeout}
    else:
        code, output = run_shell(command, cwd, deadline.remaining())
        if getattr(output, "timed_out", False):
            timeout = {"command": command, "seconds": args.timeout}
    lines = added_lines(cwd, base)
    stat = diffstat(cwd, base, test_re)

    excluded = {k for k in ref_added_keys(cwd, args.exclude_ref, base) if k[1]}
    gated, excluded_by_ref = drop_excluded(lines, excluded)
    scan = [
        x
        for x in drop_moved(gated, removed_keys(cwd, base))
        if not x["file"].startswith("docs/plans/")
    ]
    parts = {}
    if not args.no_triage:
        cands = parking_candidates(cwd, scan)
        if cands:
            parts["parking"] = cands

    acs, asks = [], []
    if args.acs:
        texts = {a["id"]: a.get("text", "") for a in specs}
        ace = json.loads(Path(args.ac_evidence).read_text()) if args.ac_evidence else {}
        acs = [check_ac(cwd, a, output, changed, deadline, ace) for a in specs]
        diff_text = "\n".join(f"{x['file']}:{x['line']}: {x['text']}" for x in lines)
        if not args.no_triage:
            asks = plausibility_asks(acs, texts, diff_text)
            if asks:
                parts["acs"] = asks
    if not args.no_triage and not args.no_tier:
        parts["tier"] = {
            "requirement": args.requirement,
            "files": [c["file"] for c in changed],
            "diffstat": stat,
        }

    parking, tier, got = [], None, None
    if parts and _expired(deadline, "triage"):
        notes.append("triage skipped: shared deadline reached")
    elif parts:
        try:
            res = triage_run("verify", parts)
            if res.get("error"):
                raise RuntimeError(res["error"])
            parking = list(res.get("parking") or [])
            tier = res.get("classifierTier") if "tier" in parts else None
            got = {v["id"]: v["verdict"] for v in res.get("acs") or []}
        except Exception as e:
            parking, tier, got = [], None, None
            notes.append(f"triage verify failed: {e}")
    if "acs" not in parts:
        got = {}
    set_plausibility(acs, {x["id"] for x in asks}, got)

    tdd = None
    if args.tdd_revert:
        base_command = " && ".join(runner_commands(cwd, _spec_test_files(specs), changed))
        tdd = tdd_revert(cwd, base, base_command or command, test_re, code, deadline)
    if tdd and tdd.get("error"):
        notes.append(f"tdd-revert error: {tdd['error']}")
    timeout = (
        timeout
        or next((a["timeout"] for a in acs if a.get("timeout")), None)
        or (tdd or {}).get("timeout")
    )
    result = {
        "head": git(cwd, "rev-parse", "HEAD").strip(),
        "clean": clean_before and is_clean(cwd),
        "command": command,
        "commandScope": "targeted" if targeted else "command",
        "exit": code,
        "passed": code == 0 and timeout is None and not deadline.skipped,
        "evidence": "\n".join(output.splitlines()[-40:]),
        "installed": installed,
        "debtMarkers": find_debt(scan, args.markers, test_re),
        "parking": parking,
        "excludedByRef": excluded_by_ref,
        "changed": changed,
        "changedSincePrevious": (name_status(cwd, args.prev_head) if args.prev_head else None),
        "diffstat": stat,
        "acs": [{k: v for k, v in a.items() if k != "ref" or v} for a in acs],
        "tierHint": tier,
        "triageUsage": usage,
        "tdd": tdd,
        "timeout": timeout,
        "skipped": deadline.skipped,
        "note": "; ".join(notes),
    }
    return 0, result


def main(argv: list) -> int:
    try:
        code, result = build(argv)
    except RuntimeError as e:
        print(f"verify-task: {e}", file=sys.stderr)
        return 2
    print(json.dumps(result))
    return code


if __name__ == "__main__":
    os.environ.setdefault("GIT_OPTIONAL_LOCKS", "0")
    sys.exit(main(sys.argv[1:]))
