#!/usr/bin/env python3
"""Judge the semver bump from commits, write the changelog, commit and tag locally.

For maintainers of the template's workbench plugin. Bumps the `workbench` entry of the
root `.claude-plugin/marketplace.json`, `plugins/workbench/.claude-plugin/plugin.json`
and `plugins/workbench/CHANGELOG.md`. The template root is found from this file's own
location. Never pushes. Output is ASCII only.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "_lib"))

from common import run  # noqa: E402

LEVELS = ("patch", "minor", "major")
SUBJECT = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]*)\))?(?P<bang>!)?: (?P<desc>.+)$")
OMIT = re.compile(r"^(chore\(ticket\)|docs\((record|plan)\)|chore\(release\))")
PLUGIN = "workbench"
PLUGIN_DIR = f"plugins/{PLUGIN}"
PLUGIN_JSON = f"{PLUGIN_DIR}/.claude-plugin/plugin.json"
MARKETPLACE = ".claude-plugin/marketplace.json"
CHANGELOG = f"{PLUGIN_DIR}/CHANGELOG.md"
REMOVED = re.compile(rf"^{re.escape(PLUGIN_DIR)}/(skills/[^/]+/SKILL\.md|agents/[^/]+\.md)$")
GROUPS = (("Breaking", "breaking"), ("Features", "feat"), ("Fixes", "fix"), ("Other", "other"))


class ReleaseError(Exception):
    pass


def find_template_root() -> Path:
    """Template root: the plugin's own location, verified by the root marketplace."""
    here = Path(__file__).resolve()
    if len(here.parents) < 6:
        raise ReleaseError(f"{here} is not inside a workbench template tree")
    root = here.parents[5]
    if not (root / MARKETPLACE).is_file() or not (root / PLUGIN_JSON).is_file():
        raise ReleaseError(f"not inside a workbench template tree: no {MARKETPLACE} at {root}")
    return root


def ascii_only(text: str) -> str:
    return text.encode("ascii", "replace").decode("ascii")


def git(repo: Path, *args: str) -> str:
    r = run(["git", *args], cwd=repo, check=False)
    if r.returncode:
        raise ReleaseError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout.strip()


def parse_version(text: str) -> tuple[int, int, int]:
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", text)
    if not m:
        raise ReleaseError(f"version {text!r} is not X.Y.Z")
    return int(m[1]), int(m[2]), int(m[3])


def bump(version: str, level: str) -> str:
    major, minor, patch = parse_version(version)
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def range_start(repo: Path) -> str | None:
    """Newest v* tag, else the last commit touching "version" in plugin.json, else root."""
    tags = git(repo, "tag", "--list", "v*", "--sort=-v:refname").split()
    if tags:
        return tags[0]
    sha = git(repo, "log", "-1", "--format=%H", "-G", '"version"', "--", PLUGIN_JSON)
    return sha or None


def commits_since(repo: Path, start: str | None) -> list[dict]:
    rng = [f"{start}..HEAD"] if start else ["HEAD"]
    out = git(repo, "log", "--no-merges", "--reverse", "--format=%H%x1f%s%x1f%b%x1e", *rng)
    commits = []
    for rec in out.split("\x1e"):
        rec = rec.strip("\n")
        if not rec.strip():
            continue
        sha, subject, body = (rec.split("\x1f") + ["", ""])[:3]
        deleted = git(
            repo, "show", "--no-renames", "--diff-filter=D", "--name-only", "--format=", sha
        ).split()
        m = SUBJECT.match(subject)
        breaking = bool(m and m["bang"]) or bool(re.search(r"^BREAKING[ -]CHANGE:", body, re.M))
        removal = any(REMOVED.match(f) for f in deleted)
        commits.append(
            {
                "sha": sha[:7],
                "subject": subject,
                "type": m["type"] if m else "other",
                "desc": m["desc"] if m else subject,
                "scope": (m["scope"] or "") if m else "",
                "breaking": breaking,
                "removal": removal,
            }
        )
    return commits


def judge(commits: list[dict]) -> tuple[str, list[dict]]:
    major = [c for c in commits if c["breaking"] or c["removal"]]
    if major:
        return "major", major
    minor = [c for c in commits if c["type"] == "feat"]
    if minor:
        return "minor", minor
    return "patch", commits


def section(version: str, commits: list[dict], date: str) -> str:
    buckets: dict[str, list[str]] = {key: [] for _, key in GROUPS}
    seen: set[str] = set()
    for c in commits:
        if OMIT.match(c["subject"]) or c["subject"] in seen:
            continue
        seen.add(c["subject"])
        if c["breaking"] or c["removal"]:
            key = "breaking"
        elif c["type"] in ("feat", "fix"):
            key = c["type"]
        else:
            key = "other"
        label = f"{c['scope']}: {c['desc']}" if c["scope"] else c["desc"]
        if c["type"] not in ("feat", "fix") and c["type"] != "other":
            label = f"{c['type']}: {label}"
        buckets[key].append(f"- {label} ({c['sha']})")
    lines = [f"## v{version} - {date}", ""]
    for title, key in GROUPS:
        if buckets[key]:
            lines += [f"### {title}", "", *buckets[key], ""]
    return ascii_only("\n".join(lines).rstrip() + "\n")


def prepend_changelog(path: Path, sec: str) -> None:
    if not path.exists():
        path.write_text("# Changelog\n\n" + sec)
        return
    text = path.read_text()
    m = re.search(r"^## ", text, re.M)
    if m:
        text = text[: m.start()] + sec + "\n" + text[m.start() :]
    else:
        text = text.rstrip("\n") + "\n\n" + sec
    path.write_text(text)


def plan_versions(repo: Path, new: str) -> list[tuple[Path, str]]:
    """Validate and compute the new file texts; writes nothing."""
    plugin = repo / PLUGIN_JSON
    text, n = re.subn(r'("version":\s*")[^"]*(")', rf"\g<1>{new}\2", plugin.read_text(), count=1)
    if not n:
        raise ReleaseError("plugin.json has no version key")
    market = repo / MARKETPLACE
    data = json.loads(market.read_text())
    entries = [e for e in data.get("plugins", []) if e.get("name") == PLUGIN]
    if not entries:
        raise ReleaseError(f"marketplace.json has no plugin entry named {PLUGIN}")
    entries[0]["version"] = new
    return [(plugin, text), (market, json.dumps(data, indent=2, ensure_ascii=False) + "\n")]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--level", choices=LEVELS, help="override the judged bump size")
    ap.add_argument("--dry-run", action="store_true", help="print only, write nothing")
    args = ap.parse_args(argv)
    try:
        return release(find_template_root(), args.level, args.dry_run)
    except ReleaseError as e:
        print(ascii_only(f"release: {e}"), file=sys.stderr)
        return 1


def release(repo: Path, override: str | None, dry: bool) -> int:
    if Path(git(repo, "rev-parse", "--show-toplevel")).resolve() != repo:
        raise ReleaseError(f"template root {repo} is not the git toplevel")
    if not dry:
        if git(repo, "branch", "--show-current") != "main":
            raise ReleaseError("refusing: not on branch main")
        if git(repo, "status", "--porcelain"):
            raise ReleaseError("refusing: working tree is dirty")
    start = range_start(repo)
    commits = commits_since(repo, start)
    if not commits:
        raise ReleaseError("nothing to release: no commits since " + (start or "the root"))
    judged, drivers = judge(commits)
    level = override or judged
    current = json.loads((repo / PLUGIN_JSON).read_text())["version"]
    new = bump(current, level)
    if git(repo, "tag", "--list", f"v{new}"):
        raise ReleaseError(f"refusing: tag v{new} already exists")
    sec = section(new, commits, datetime.date.today().isoformat())
    writes = plan_versions(repo, new)
    note = ""
    if override:
        note = f"level override: {override} (judged {judged})"
    print(f"range: {(start or 'root')[:12]}..HEAD ({len(commits)} commits)")
    print(f"level: {level}")
    if note:
        print(note)
    print("drivers:" if not override else f"drivers (judged {judged}):")
    for c in drivers:
        print(ascii_only(f"  {c['sha']} {c['subject']}"))
    print(f"next: {new}")
    print()
    print(sec, end="")
    if dry:
        return 0
    for path, text in writes:
        path.write_text(text)
    prepend_changelog(repo / CHANGELOG, sec)
    git(repo, "add", PLUGIN_JSON, MARKETPLACE, CHANGELOG)
    msg = f"chore(release): v{new}" + (f"\n\n{note}" if note else "")
    git(repo, "commit", "-q", "-m", msg)
    git(
        repo,
        "tag",
        "-a",
        f"v{new}",
        "--cleanup=verbatim",
        "-m",
        sec + (f"\n{note}\n" if note else ""),
    )
    print(f"\ntagged v{new} locally; nothing pushed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
