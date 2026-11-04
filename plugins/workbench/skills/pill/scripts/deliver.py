"""Deliver a pill PDF to the NAS books directory over ssh/scp, or discover that directory.

Usage:
  deliver.py send FILE [--host H] [--user U] [--dir D] [--name N] [--port P] [--dry-run]
  deliver.py discover [--host H] [--user U] [--port P]

Defaults come from the environment: PILL_NAS_HOST (default nas.lan), PILL_NAS_USER
(default: whatever ssh picks, e.g. from ~/.ssh/config), PILL_NAS_DIR (no default:
`send` refuses to guess and points at `discover`), PILL_NAS_PORT.

`send` runs `mkdir -p` on the remote dir, copies the file with scp in BatchMode,
then compares the remote size with the local one and prints the exact remote
path as `delivered: [user@]host:/dir/name (N bytes)`.

`discover` is read-only: over one ssh session it lists the Jellyfin and
Audiobookshelf containers' docker mounts, reads the Jellyfin library paths
(root/default/*/options.xml and *.mblink under the config dir) and the
Audiobookshelf library folders (absdatabase.sqlite, opened read-only), maps the
container paths back to host paths and prints candidates, books first.

Exit 0 on success, 1 on a transfer, verify or ssh failure, 2 on a usage error.
"""

import argparse
import os
import posixpath
import shlex
import subprocess
import sys
from dataclasses import dataclass

DEFAULT_HOST = "nas.lan"
SSH_OPTS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=15"]

# POSIX sh run on the NAS by `discover`. Read-only: docker ps/inspect, find, grep,
# cat and a read-only sqlite open. Each step retries with `sudo -n` (never prompts).
DISCOVER_SH = r"""
rd() { "$@" 2>/dev/null || sudo -n "$@" 2>/dev/null; }
D=""
if command -v docker >/dev/null 2>&1; then
  if docker ps >/dev/null 2>&1; then D="docker"
  elif sudo -n docker ps >/dev/null 2>&1; then D="sudo -n docker"; fi
fi
jf_dirs="/var/lib/jellyfin /config"
abs_dirs="/usr/share/audiobookshelf/config /config"
if [ -n "$D" ]; then
  mounts=""
  for c in $($D ps --format '{{.Names}}'); do
    img=$($D inspect -f '{{.Config.Image}}' "$c")
    case "$c $img" in
      *jellyfin*) app=jellyfin ;;
      *audiobookshelf*) app=audiobookshelf ;;
      *) continue ;;
    esac
    m=$($D inspect -f '{{range .Mounts}}{{.Source}}|{{.Destination}}{{"\n"}}{{end}}' "$c")
    mounts="$mounts$(printf '%s\n' "$m" | sed "s#^#$app|$c|#")
"
  done
  while IFS='|' read -r app c s d; do
    [ -n "$s" ] || continue
    printf 'MOUNT\t%s\t%s\t%s\t%s\n' "$app" "$c" "$s" "$d"
    case "$app|$d" in
      jellyfin\|/config) jf_dirs="$s $jf_dirs" ;;
      audiobookshelf\|/config) abs_dirs="$s $abs_dirs" ;;
    esac
  done <<EOF_MOUNTS
$mounts
EOF_MOUNTS
else
  printf 'NOTE\tdocker not usable (missing or no permission); checking native install paths\n'
fi
for dir in $jf_dirs; do
  [ -d "$dir" ] || continue
  for f in $(rd find "$dir" -maxdepth 6 -path '*/root/default/*/options.xml'); do
    lib=$(basename "$(dirname "$f")")
    rd cat "$f" | grep -o '<Path>[^<]*</Path>' | sed 's#</*Path>##g' |
      while IFS= read -r p; do printf 'JELLYFIN\t%s\t%s\n' "$lib" "$p"; done
  done
  for f in $(rd find "$dir" -maxdepth 6 -path '*/root/default/*' -name '*.mblink'); do
    lib=$(basename "$(dirname "$f")")
    printf 'JELLYFIN\t%s\t%s\n' "$lib" "$(rd cat "$f")"
  done
done
for dir in $abs_dirs; do
  db="$dir/absdatabase.sqlite"
  rd test -f "$db" || continue
  q="select l.name, f.path from libraryFolders f join libraries l on l.id = f.libraryId"
  if command -v sqlite3 >/dev/null 2>&1; then
    rd sqlite3 -readonly -separator "$(printf '\t')" "$db" "$q" | sed 's/^/ABS\t/'
  elif command -v python3 >/dev/null 2>&1; then
    rd python3 -c 'import sqlite3, sys
c = sqlite3.connect("file:" + sys.argv[1] + "?mode=ro", uri=True)
for n, p in c.execute(sys.argv[2]): print("ABS\t%s\t%s" % (n, p))' "$db" "$q"
  else
    printf 'NOTE\tfound %s but neither sqlite3 nor python3 to read it\n' "$db"
  fi
done
"""


@dataclass
class Target:
    host: str
    user: str | None
    port: str | None

    @property
    def dest(self) -> str:
        return f"{self.user}@{self.host}" if self.user else self.host

    def ssh(self, remote_cmd: str) -> list[str]:
        port = ["-p", self.port] if self.port else []
        return ["ssh", *SSH_OPTS, *port, self.dest, remote_cmd]

    def scp(self, local: str, remote_path: str) -> list[str]:
        port = ["-P", self.port] if self.port else []
        return ["scp", *SSH_OPTS, *port, local, f"{self.dest}:{remote_path}"]


def target_from(args) -> Target:
    return Target(
        host=args.host or os.environ.get("PILL_NAS_HOST") or DEFAULT_HOST,
        user=args.user or os.environ.get("PILL_NAS_USER") or None,
        port=args.port or os.environ.get("PILL_NAS_PORT") or None,
    )


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def fail(step: str, proc: subprocess.CompletedProcess) -> int:
    err = (proc.stderr or proc.stdout or "").strip().splitlines()[-5:]
    print(f"deliver: {step} failed (exit {proc.returncode})", file=sys.stderr)
    for line in err:
        print(f"  {line}", file=sys.stderr)
    return 1


def cmd_send(args) -> int:
    if not os.path.isfile(args.file):
        print(f"deliver: no such file: {args.file}", file=sys.stderr)
        return 2
    remote_dir = args.dir or os.environ.get("PILL_NAS_DIR")
    if not remote_dir:
        print(
            "deliver: no remote dir. Pass --dir or set PILL_NAS_DIR; find the books dir with\n"
            "  deliver.py discover",
            file=sys.stderr,
        )
        return 2
    t = target_from(args)
    name = args.name or os.path.basename(args.file)
    if "/" in name or name in ("", ".", ".."):
        print(f"deliver: --name must be a plain file name, got {name!r}", file=sys.stderr)
        return 2
    remote_path = posixpath.join(remote_dir, name)
    size = os.path.getsize(args.file)
    steps = [
        ("mkdir", t.ssh(f"mkdir -p -- {shlex.quote(remote_dir)}")),
        ("scp", t.scp(args.file, remote_path)),
        ("verify", t.ssh(f"wc -c < {shlex.quote(remote_path)}")),
    ]
    if args.dry_run:
        for _, cmd in steps:
            print(shlex.join(cmd))
        return 0
    for step, cmd in steps:
        proc = run(cmd)
        if proc.returncode != 0:
            return fail(step, proc)
    got = proc.stdout.strip()
    if got != str(size):
        print(
            f"deliver: size mismatch for {t.dest}:{remote_path}: local {size}, remote {got!r}",
            file=sys.stderr,
        )
        return 1
    print(f"delivered: {t.dest}:{remote_path} ({size} bytes)")
    return 0


def to_host_path(path: str, mounts: list[tuple[str, str]]) -> str | None:
    """Map a container path to a host path through the longest matching mount."""
    best = None
    for src, dst in mounts:
        d = dst.rstrip("/") or "/"
        if path == d or path.startswith(d + "/") or d == "/":
            if best is None or len(d) > len(best[1]):
                best = (src, d)
    if best is None:
        return None
    src, d = best
    rest = path[len(d) :].lstrip("/") if d != "/" else path.lstrip("/")
    return posixpath.join(src, rest) if rest else src


def book_score(lib: str, path: str) -> int:
    text = f"{lib} {path}".lower()
    if "book" not in text:
        return 0
    return 1 if "audio" in text else 2


def parse_discover(output: str) -> tuple[list[dict], list[str]]:
    """Turn the remote script output into ranked candidates plus notes."""
    mounts: dict[str, list[tuple[str, str]]] = {}
    libs: list[tuple[str, str, str]] = []
    notes: list[str] = []
    for line in output.splitlines():
        parts = line.split("\t")
        kind = parts[0]
        if kind == "MOUNT" and len(parts) == 5:
            mounts.setdefault(parts[1], []).append((parts[3], parts[4]))
        elif kind == "JELLYFIN" and len(parts) == 3:
            libs.append(("jellyfin", parts[1], parts[2]))
        elif kind == "ABS" and len(parts) == 3:
            libs.append(("audiobookshelf", parts[1], parts[2]))
        elif kind == "NOTE" and len(parts) >= 2:
            notes.append("\t".join(parts[1:]))
    out, seen = [], set()
    for app, lib, path in libs:
        app_mounts = mounts.get(app)
        host = to_host_path(path, app_mounts) if app_mounts else path
        key = (app, lib, path)
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "app": app,
                "library": lib,
                "container_path": path,
                "host_path": host,
                "score": book_score(lib, path),
            }
        )
    out.sort(key=lambda c: (-c["score"], c["app"], c["library"]))
    return out, notes


def cmd_discover(args) -> int:
    t = target_from(args)
    proc = run(t.ssh("sh -s"), input=DISCOVER_SH)
    if proc.returncode != 0 and not proc.stdout.strip():
        return fail("discover", proc)
    cands, notes = parse_discover(proc.stdout)
    for n in notes:
        print(f"note: {n}")
    if not cands:
        print(
            f"deliver: no Jellyfin or Audiobookshelf library paths found on {t.dest}",
            file=sys.stderr,
        )
        return 1
    print("host_path\tapp\tlibrary\tcontainer_path")
    for c in cands:
        host = c["host_path"] or "(unmapped)"
        print(f"{host}\t{c['app']}\t{c['library']}\t{c['container_path']}")
    best = next((c for c in cands if c["score"] and c["host_path"]), None)
    if best:
        print(f"suggested: PILL_NAS_DIR={best['host_path']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("send", "discover"):
        p = sub.add_parser(name)
        p.add_argument("--host", help=f"NAS host (env PILL_NAS_HOST, default {DEFAULT_HOST})")
        p.add_argument("--user", help="ssh user (env PILL_NAS_USER)")
        p.add_argument("--port", help="ssh port (env PILL_NAS_PORT)")
        if name == "send":
            p.add_argument("file", help="local PDF to deliver")
            p.add_argument("--dir", help="remote books dir (env PILL_NAS_DIR)")
            p.add_argument("--name", help="remote file name (default: local basename)")
            p.add_argument("--dry-run", action="store_true", help="print the commands only")
    args = ap.parse_args(argv)
    return cmd_send(args) if args.cmd == "send" else cmd_discover(args)


if __name__ == "__main__":
    sys.exit(main())
