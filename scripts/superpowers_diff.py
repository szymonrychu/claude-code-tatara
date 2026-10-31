#!/usr/bin/env python3
"""Print the vendored superpowers skill files an upstream release changed, added or removed.

Usage: superpowers_diff.py <version> [--upstream URL]

Reads plugins/superpowers/UPSTREAM.md for the upstream URL, the tag pattern, the base
version and the vendored skills; shallow-clones the base tag and the tag of <version> into a
temp dir and prints, one per line and sorted, every file under a vendored skill dir
(`skills/<name>/...`) that differs between the two. Prints nothing when none does. Reports
only: nothing under plugins/superpowers is written. --upstream overrides the URL (tests).
Exit 0 on a report, 1 when UPSTREAM.md or a clone fails.
"""

import argparse
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM_MD = ROOT / "plugins" / "superpowers" / "UPSTREAM.md"
URL_RE = re.compile(r"^- Upstream URL: (\S+)$", re.M)
TAG_RE = re.compile(r"^- Tag pattern: `([^`]+)`$", re.M)
BASE_RE = re.compile(r"^- Base version: `([^`]+)`$", re.M)
SKILL_RE = re.compile(r"^- `([a-z0-9-]+)`: ", re.M)


class UpstreamError(Exception):
    """UPSTREAM.md is incomplete or a clone failed."""


@dataclass(frozen=True)
class Upstream:
    """What UPSTREAM.md records.

    Attributes:
        url (str): the upstream git URL.
        tag_pattern (str): the tag of a version, with `{version}` in it.
        base (str): the upstream version the vendored copy was taken from.
        skills (tuple[str, ...]): the vendored skill names.
    """

    url: str
    tag_pattern: str
    base: str
    skills: tuple[str, ...]


def read_upstream(path: Path) -> Upstream:
    """Parse UPSTREAM.md.

    Args:
        path (Path): the UPSTREAM.md file.

    Returns:
        Upstream: the recorded URL, tag pattern, base version and vendored skills.

    Raises:
        UpstreamError: a field or the skill list is missing.
    """
    text = path.read_text()
    fields = {}
    for name, pattern in (("url", URL_RE), ("tag_pattern", TAG_RE), ("base", BASE_RE)):
        m = pattern.search(text)
        if not m:
            raise UpstreamError(f"{path}: no {name} recorded")
        fields[name] = m.group(1)
    skills = tuple(SKILL_RE.findall(text))
    if not skills:
        raise UpstreamError(f"{path}: no vendored skills listed")
    return Upstream(skills=skills, **fields)


def clone(url: str, tag: str, dest: Path) -> None:
    """Shallow-clone one tag of url into dest.

    Args:
        url (str): the upstream git URL or path.
        tag (str): the tag to check out.
        dest (Path): the clone directory (must not exist).

    Raises:
        UpstreamError: git clone failed (for example an unknown tag).
    """
    proc = subprocess.run(
        ["git", "clone", "-q", "--depth", "1", "--branch", tag, "--", url, str(dest)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise UpstreamError(f"cannot clone {tag} of {url}: {proc.stderr.strip()}")


def skill_files(tree: Path, skills: tuple[str, ...]) -> dict[str, bytes]:
    """Map every file under the vendored skill dirs of a clone to its content.

    Args:
        tree (Path): the clone root.
        skills (tuple[str, ...]): the vendored skill names.

    Returns:
        dict[str, bytes]: `skills/<name>/...` path -> file bytes.
    """
    files = {}
    for name in skills:
        for path in (tree / "skills" / name).rglob("*"):
            if path.is_file():
                files[path.relative_to(tree).as_posix()] = path.read_bytes()
    return files


def changed(old: dict[str, bytes], new: dict[str, bytes]) -> list[str]:
    """The paths changed, added or removed between two file maps, sorted.

    Args:
        old (dict[str, bytes]): path -> content at the base version.
        new (dict[str, bytes]): path -> content at the new version.

    Returns:
        list[str]: the differing paths.
    """
    return sorted(p for p in old.keys() | new.keys() if old.get(p) != new.get(p))


def diff(upstream: Upstream, version: str, url: str | None = None) -> list[str]:
    """Clone the base and the given version and list the vendored files that differ.

    Args:
        upstream (Upstream): the UPSTREAM.md record.
        version (str): the newer upstream version.
        url (str | None): an upstream URL overriding the recorded one.

    Returns:
        list[str]: the differing `skills/<name>/...` paths, sorted.
    """
    source = url or upstream.url
    with tempfile.TemporaryDirectory(prefix="superpowers-diff-") as tmp:
        trees = []
        for side, v in (("base", upstream.base), ("new", version)):
            dest = Path(tmp) / side
            clone(source, upstream.tag_pattern.format(version=v), dest)
            trees.append(skill_files(dest, upstream.skills))
    return changed(*trees)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("version", help="the upstream version to compare with the base")
    ap.add_argument("--upstream", help="override the upstream URL recorded in UPSTREAM.md")
    args = ap.parse_args(argv)
    try:
        paths = diff(read_upstream(UPSTREAM_MD), args.version, args.upstream)
    except UpstreamError as e:
        print(f"superpowers-diff: {e}", file=sys.stderr)
        return 1
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
