"""Deliver a pill PDF into a Kubernetes pod that mounts the books library, or discover that pod.

Usage:
  deliver.py send FILE [-n NS] [--pod P | -l SELECTOR] [-c C] [--dir D] [--name N]
                       [--match M] [--dry-run]
  deliver.py discover [-n NS] [-l SELECTOR] [--match M]

Defaults come from the environment: PILL_K8S_NAMESPACE (default media),
PILL_K8S_POD (exact pod name or name prefix), PILL_K8S_SELECTOR (label selector),
PILL_K8S_CONTAINER, PILL_K8S_DIR (in-pod dir). Unset values are filled from the
best writable `discover` candidate.

`discover` is read-only: one `kubectl get pods -o json`. For every running
container it joins each volumeMount with its volume source (hostPath path, with
subPath, or PVC claim) and prints the mounts whose mountPath or hostPath
contains the match pattern (default "books"). A parent hostPath mount (node
/media/hdd at /media) that holds a matching node dir seen in any pod (node
/media/hdd/books) yields the derived in-pod dir /media/books. Writable mounts
rank first; read-only ones are listed but never chosen.

`send` checks that `tar` runs in the container (kubectl cp needs it), runs
`mkdir -p` on the target dir only when the dir lies under a writable mount of
that container, copies with `kubectl cp`, compares the remote size (`stat -c %s`,
`ls -ln` fallback) with the local one and prints the in-pod and node paths.
It changes nothing else in the cluster.

Exit 0 on success, 1 on a kubectl, transfer or verify failure, 2 on a usage error.
"""

import argparse
import json
import os
import posixpath
import shlex
import subprocess
import sys
from dataclasses import dataclass

DEFAULT_NAMESPACE = "media"
DEFAULT_MATCH = "books"
# Apps that read the books library: tiebreak among equally good writable mounts.
PREFERRED_APPS = ("jellyfin", "audiobookshelf", "calibre", "kavita", "komga")


@dataclass
class Mount:
    pod: str
    container: str
    mount_path: str
    read_only: bool
    host_path: str | None  # node path, subPath applied
    pvc: str | None


@dataclass
class Candidate:
    pod: str
    container: str
    dir: str  # in-pod path
    node_path: str | None
    read_only: bool
    source: str  # "direct" or "derived"
    mount_path: str


def run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def fail(step: str, proc: subprocess.CompletedProcess) -> int:
    err = (proc.stderr or proc.stdout or "").strip().splitlines()[-5:]
    print(f"deliver: {step} failed (exit {proc.returncode})", file=sys.stderr)
    for line in err:
        print(f"  {line}", file=sys.stderr)
    return 1


def under(path: str, base: str) -> str | None:
    """Return path relative to base ("" when equal), or None when not under it."""
    base = base.rstrip("/") or "/"
    path = path.rstrip("/") or "/"
    if path == base:
        return ""
    if base == "/":
        return path.lstrip("/")
    if path.startswith(base + "/"):
        return path[len(base) + 1 :]
    return None


def get_pods(
    ns: str, selector: str | None
) -> tuple[list[dict] | None, subprocess.CompletedProcess]:
    cmd = ["kubectl", "-n", ns, "get", "pods", "-o", "json"]
    if selector:
        cmd += ["-l", selector]
    proc = run(cmd)
    if proc.returncode != 0:
        return None, proc
    return json.loads(proc.stdout or "{}").get("items", []), proc


def running(pod: dict) -> bool:
    return pod.get("status", {}).get("phase") == "Running" and not pod.get("metadata", {}).get(
        "deletionTimestamp"
    )


def mounts_of(pods: list[dict]) -> list[Mount]:
    out = []
    for pod in pods:
        if not running(pod):
            continue
        name = pod["metadata"]["name"]
        vols = {v["name"]: v for v in pod.get("spec", {}).get("volumes", [])}
        for c in pod.get("spec", {}).get("containers", []):
            for m in c.get("volumeMounts", []):
                v = vols.get(m["name"], {})
                host = v.get("hostPath", {}).get("path")
                pvc_src = v.get("persistentVolumeClaim") or {}
                if host and m.get("subPath"):
                    host = posixpath.join(host, m["subPath"])
                out.append(
                    Mount(
                        pod=name,
                        container=c["name"],
                        mount_path=m["mountPath"],
                        read_only=bool(m.get("readOnly") or pvc_src.get("readOnly")),
                        host_path=host,
                        pvc=pvc_src.get("claimName"),
                    )
                )
    return out


def app_rank(pod: str) -> int:
    return next((i for i, a in enumerate(PREFERRED_APPS) if a in pod.lower()), len(PREFERRED_APPS))


def holder_of(mounts: list[Mount], pod: str, container: str, path: str) -> Mount | None:
    """The container's mount that holds path: the one with the longest mountPath."""
    own = [m for m in mounts if m.pod == pod and m.container == container]
    return max(
        (m for m in own if under(path, m.mount_path) is not None),
        key=lambda m: len(m.mount_path),
        default=None,
    )


def candidates(mounts: list[Mount], match: str) -> list[Candidate]:
    """Direct matches plus dirs derived through parent hostPath mounts, best first."""
    pat = match.lower()
    out: dict[tuple[str, str, str], Candidate] = {}

    def add(c: Candidate) -> None:
        key = (c.pod, c.container, c.dir)
        if key not in out or (out[key].source == "derived" and c.source == "direct"):
            out[key] = c

    node_dirs = set()
    for m in mounts:
        if pat in m.mount_path.lower() or (m.host_path and pat in m.host_path.lower()):
            add(
                Candidate(
                    m.pod,
                    m.container,
                    m.mount_path,
                    m.host_path,
                    m.read_only,
                    "direct",
                    m.mount_path,
                )
            )
            if m.host_path:
                node_dirs.add(m.host_path.rstrip("/"))
    for m in mounts:
        if not m.host_path:
            continue
        for nd in node_dirs:
            rel = under(nd, m.host_path)
            if rel:
                d = posixpath.join(m.mount_path, rel)
                add(Candidate(m.pod, m.container, d, nd, m.read_only, "derived", m.mount_path))

    def rank(c: Candidate):
        text = f"{c.dir} {c.node_path or ''}".lower()
        audio = "audio" in text and "audio" not in pat
        return (c.read_only, audio, app_rank(c.pod), c.pod, c.container, c.dir)

    return sorted(out.values(), key=rank)


def cmd_discover(args) -> int:
    pods, proc = get_pods(args.namespace, args.selector)
    if pods is None:
        return fail("kubectl get pods", proc)
    cands = candidates(mounts_of(pods), args.match)
    if not cands:
        print(
            f"deliver: no running pod in namespace {args.namespace} mounts a path matching "
            f"{args.match!r}",
            file=sys.stderr,
        )
        return 1
    print("access\tpod\tcontainer\tin_pod_dir\tnode_path\tvia")
    for c in cands:
        via = c.source if c.source == "direct" else f"derived from {c.mount_path}"
        acc = "ro" if c.read_only else "rw"
        print(f"{acc}\t{c.pod}\t{c.container}\t{c.dir}\t{c.node_path or '(no hostPath)'}\t{via}")
    best = next((c for c in cands if not c.read_only), None)
    if best:
        print(
            f"suggested: PILL_K8S_NAMESPACE={args.namespace} PILL_K8S_POD={best.pod} "
            f"PILL_K8S_CONTAINER={best.container} PILL_K8S_DIR={best.dir}"
        )
    else:
        print("note: every matching mount is read-only; no writable target", file=sys.stderr)
    return 0


def resolve_pod(pods: list[dict], want: str | None) -> list[dict]:
    live = sorted((p for p in pods if running(p)), key=lambda p: p["metadata"]["name"])
    if not want:
        return live
    exact = [p for p in live if p["metadata"]["name"] == want]
    return exact or [p for p in live if p["metadata"]["name"].startswith(want)]


def node_path_for(dir_: str, mount: Mount | None) -> str | None:
    if not mount or not mount.host_path:
        return None
    rel = under(dir_, mount.mount_path)
    return posixpath.join(mount.host_path, rel) if rel else mount.host_path


def cmd_send(args) -> int:
    if not os.path.isfile(args.file):
        print(f"deliver: no such file: {args.file}", file=sys.stderr)
        return 2
    name = args.name or os.path.basename(args.file)
    if "/" in name or name in ("", ".", ".."):
        print(f"deliver: --name must be a plain file name, got {name!r}", file=sys.stderr)
        return 2
    ns = args.namespace
    pods, proc = get_pods(ns, args.selector)
    if pods is None:
        return fail("kubectl get pods", proc)
    live = resolve_pod(pods, args.pod)
    if not live:
        what = f"pod {args.pod!r}" if args.pod else "pod"
        sel = f" with selector {args.selector!r}" if args.selector else ""
        print(f"deliver: no running {what}{sel} in namespace {ns}", file=sys.stderr)
        return 2
    mounts = mounts_of(live)
    if args.dir:
        dir_ = args.dir
        holders = []
        for pod_name, cont in dict.fromkeys((m.pod, m.container) for m in mounts):
            if args.container and cont != args.container:
                continue
            h = holder_of(mounts, pod_name, cont, dir_)
            if h and not h.read_only:
                holders.append(h)
        holders.sort(key=lambda m: (app_rank(m.pod), m.pod, m.container))
        if holders:
            pod, container = holders[0].pod, holders[0].container
        elif (args.pod or args.selector) and args.container:
            pod, container = live[0]["metadata"]["name"], args.container
        else:
            print(
                f"deliver: no selected container mounts {dir_} writable; pass --pod and "
                "--container, or run\n  deliver.py discover",
                file=sys.stderr,
            )
            return 2
    else:
        cands = [
            c
            for c in candidates(mounts, args.match)
            if not c.read_only and (not args.container or c.container == args.container)
        ]
        if not cands:
            print(
                f"deliver: no writable mount matching {args.match!r} in the selected pods; "
                "pass --dir, or run\n  deliver.py discover",
                file=sys.stderr,
            )
            return 2
        pod, container, dir_ = cands[0].pod, cands[0].container, cands[0].dir
    dir_ = dir_.rstrip("/") or "/"

    holder = holder_of(mounts, pod, container, dir_)
    if holder and holder.read_only:
        print(
            f"deliver: {dir_} is on a read-only mount ({holder.mount_path}) in {pod}/{container}",
            file=sys.stderr,
        )
        return 2
    remote_path = posixpath.join(dir_, name)
    node = node_path_for(remote_path, holder)
    size = os.path.getsize(args.file)

    kexec = ["kubectl", "-n", ns, "exec", pod, "-c", container, "--"]
    steps = [("tar check", kexec + ["tar", "--version"])]
    if holder and dir_ != holder.mount_path.rstrip("/"):
        steps.append(("mkdir", kexec + ["mkdir", "-p", "--", dir_]))
    steps.append(
        ("kubectl cp", ["kubectl", "cp", args.file, f"{ns}/{pod}:{remote_path}", "-c", container])
    )
    stat_cmd = kexec + ["stat", "-c", "%s", remote_path]
    if args.dry_run:
        for _, cmd in steps:
            print(shlex.join(cmd))
        print(shlex.join(stat_cmd))
        return 0
    for step, cmd in steps:
        proc = run(cmd)
        if proc.returncode != 0:
            if step == "tar check" and run(kexec + ["tar", "--help"]).returncode != 0:
                print(
                    f"deliver: no tar in {pod}/{container}; kubectl cp needs tar in the "
                    "container. Pick another pod/container that mounts the same dir.",
                    file=sys.stderr,
                )
                return 1
            if step != "tar check":
                return fail(step, proc)
    proc = run(stat_cmd)
    got = proc.stdout.strip()
    if proc.returncode != 0 or not got.isdigit():
        proc = run(kexec + ["ls", "-ln", remote_path])
        fields = proc.stdout.split()
        got = fields[4] if proc.returncode == 0 and len(fields) > 4 else ""
        if not got:
            return fail("verify", proc)
    if got != str(size):
        print(
            f"deliver: size mismatch for {ns}/{pod}:{remote_path}: local {size}, remote {got!r}",
            file=sys.stderr,
        )
        return 1
    print(f"delivered: {ns}/{pod}:{remote_path} (container {container}, {size} bytes)")
    print(f"node path: {node or '(not a hostPath mount)'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    env = os.environ.get
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("send", "discover"):
        p = sub.add_parser(name)
        p.add_argument(
            "-n",
            "--namespace",
            default=env("PILL_K8S_NAMESPACE") or DEFAULT_NAMESPACE,
            help=f"namespace (env PILL_K8S_NAMESPACE, default {DEFAULT_NAMESPACE})",
        )
        p.add_argument(
            "-l",
            "--selector",
            default=env("PILL_K8S_SELECTOR"),
            help="label selector (env PILL_K8S_SELECTOR)",
        )
        p.add_argument(
            "--match",
            default=DEFAULT_MATCH,
            help=f"path substring to look for (default {DEFAULT_MATCH})",
        )
        if name == "send":
            p.add_argument("file", help="local PDF to deliver")
            p.add_argument(
                "--pod",
                default=env("PILL_K8S_POD"),
                help="pod name or name prefix (env PILL_K8S_POD)",
            )
            p.add_argument(
                "-c",
                "--container",
                default=env("PILL_K8S_CONTAINER"),
                help="env PILL_K8S_CONTAINER",
            )
            p.add_argument(
                "--dir", default=env("PILL_K8S_DIR"), help="in-pod target dir (env PILL_K8S_DIR)"
            )
            p.add_argument("--name", help="remote file name (default: local basename)")
            p.add_argument(
                "--dry-run",
                action="store_true",
                help="read the pods, print the write commands only",
            )
    args = ap.parse_args(argv)
    return cmd_send(args) if args.cmd == "send" else cmd_discover(args)


if __name__ == "__main__":
    sys.exit(main())
