#!/usr/bin/env python3
"""Workbench instantiation engine. Exit 0 ok, 1 refusal, 2 usage error."""

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import adopt  # noqa: E402
import component  # noqa: E402
import finalize  # noqa: E402
import project_files  # noqa: E402
import scaffold  # noqa: E402
import update  # noqa: E402
from gitops import DEFAULT_TEMPLATE_URL, Refusal, git  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]


def answers_of(args: argparse.Namespace, langs: dict[str, str] | None = None):
    return project_files.Answers(
        purpose=args.purpose,
        hard_rules=args.hard_rule,
        risk=args.risk,
        roles=project_files.parse_roles(args.role),
        langs=langs or {},
    )


def add_answer_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument("--purpose", action="append", default=[], help="what the project builds")
    p.add_argument("--hard-rule", action="append", default=[], help="a rule every component obeys")
    p.add_argument("--risk", help="the highest-risk surface")
    p.add_argument(
        "--role", action="append", default=[], metavar="COMPONENT=TEXT", help="a component's role"
    )


def add_finalize_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--pack", action="append", default=[], help="enable a pack: infra|observability|secrets"
    )
    p.add_argument(
        "--harness", action="append", default=[], help="harness target (repeat or comma)"
    )
    p.add_argument("--deploy-command", help="record a deploy command in workbench.json")
    p.add_argument("--deploy-verify", help="command that verifies a deploy")
    p.add_argument("--license", choices=["mit", "none"], help="mit keeps MIT; none removes LICENSE")
    p.add_argument("--license-holder", help="copyright holder for --license mit")
    p.add_argument("--license-file", help="copy this text over LICENSE")
    p.add_argument("--user-settings", default="~/.claude/settings.json", help=argparse.SUPPRESS)


def finalize_options(args: argparse.Namespace, project: str) -> finalize.Options:
    return finalize.Options(
        project=project,
        packs=args.pack,
        harness=[h.strip() for v in args.harness for h in v.split(",") if h.strip()],
        deploy_command=args.deploy_command,
        deploy_verify=args.deploy_verify,
        license=args.license,
        license_holder=args.license_holder,
        license_file=args.license_file,
        user_settings=Path(args.user_settings),
    )


def cmd_new(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    answers = answers_of(args)
    if not scaffold.NAME_RE.match(args.name):
        raise Refusal(f"invalid project name {args.name!r}: lowercase letters, digits, hyphen")
    specs = component.add_new(
        root,
        args.name,
        args.component,
        args.remote,
        args.forge_owner,
        args.public,
        args.confirm_forge,
        args.origin_is_template,
    )
    answers.langs = dict(specs)
    project_files.write_all(root, answers, method=f"new scaffold, remote {args.remote}")
    finalize.finalize(root, finalize_options(args, args.name))
    return 0


def cmd_adopt(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    answers = answers_of(args)
    if args.path:
        rc = adopt.adopt_path(root, args.path, args.name, args.remote, args.origin_is_template)
        method = "adopt --path (checkout moved in)"
    else:
        if args.remote is not None:
            raise Refusal("--remote applies to --path only; a --url is already a remote")
        rc = adopt.adopt_url(root, args.url, args.name, args.origin_is_template)
        method = "adopt --url (fresh clone)"
    project_files.write_all(root, answers, method=method)
    finalize.finalize(root, finalize_options(args, args.project or root.name))
    return rc


def code_dirs(root: Path) -> set[str]:
    code = root / "code"
    return {p.name for p in code.iterdir() if p.is_dir()} if code.is_dir() else set()


def cmd_component_add(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    forms = [bool(args.component), bool(args.path), bool(args.url)]
    if sum(forms) != 1:
        raise Refusal("give exactly one of --component, --path or --url")
    answers = answers_of(args)
    before = code_dirs(root)
    rc = 0
    if args.component:
        if not args.remote:
            raise Refusal("--component needs --remote")
        specs = component.add_new(
            root,
            args.project or root.name,
            args.component,
            args.remote,
            args.forge_owner,
            args.public,
            args.confirm_forge,
            args.origin_is_template,
        )
        answers.langs = dict(specs)
        method = "component add (new scaffold)"
    elif args.path:
        rc = adopt.adopt_path(root, args.path, args.name, args.remote, args.origin_is_template)
        method = "component add --path"
    else:
        if args.remote is not None:
            raise Refusal("--remote applies to --path only; a --url is already a remote")
        rc = adopt.adopt_url(root, args.url, args.name, args.origin_is_template)
        method = "component add --url"
    project_files.write_all(root, answers, method=method)
    finalize.allow_vocabulary(root)
    git("add", "-A", cwd=root)
    label = ", ".join(sorted(code_dirs(root) - before)) or "components"
    if git("diff", "--cached", "--quiet", cwd=root, check=False).returncode != 0:
        git("commit", "-m", f"chore(workbench): add component {label}", cwd=root)
        print(f"committed chore(workbench): add component {label}")
    return rc


def cmd_component_remove(args: argparse.Namespace) -> int:
    component.remove(Path(args.root).resolve(), args.name)
    return 0


def cmd_refresh(args: argparse.Namespace) -> int:
    """Re-run the idempotent project writers, then sync the AGENTS.md blocks and harnesses."""
    root = Path(args.root).resolve()
    if not project_files.is_initialised(root):
        raise Refusal("this workbench is not initialised; run init (new or adopt) first")
    project_files.write_all(root, method="init:refresh", event=args.event)
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "harness" / "setup.py"), "--root", str(root)],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise Refusal(f"harness-setup failed: {(proc.stderr or proc.stdout).strip()}")
    print("refreshed: project files, AGENTS.md blocks, harness targets")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="init_engine")
    p.add_argument("--root", default=str(ROOT), help=argparse.SUPPRESS)
    sub = p.add_subparsers(dest="command", required=True)
    n = sub.add_parser("new", help="create a new project with components")
    n.add_argument("--name", required=True)
    n.add_argument("--component", action="append", default=[], metavar="NAME[:LANG]")
    n.add_argument("--remote", required=True, metavar="url:<url>|local-bare[:<dir>]|github|gitlab")
    n.add_argument(
        "--forge-owner", help="github owner or gitlab group (default: authenticated user)"
    )
    n.add_argument("--public", action="store_true", help="forge repos public (default private)")
    n.add_argument(
        "--confirm-forge", action="store_true", help="the user confirmed forge repo creation"
    )
    n.add_argument("--origin-is-template", action="store_true")
    add_answer_flags(n)
    add_finalize_flags(n)
    n.set_defaults(func=cmd_new)
    a = sub.add_parser("adopt", help="adopt an existing checkout or repo URL as a component")
    src = a.add_mutually_exclusive_group(required=True)
    src.add_argument("--path", help="checkout outside the workbench; moved to code/<name>")
    src.add_argument("--url", help="repo URL; a fresh clone is added at code/<name>")
    a.add_argument("--name", help="component and submodule name (default: from path or url)")
    a.add_argument(
        "--remote",
        metavar="local-bare[:<dir>]",
        help="with --path and no origin: create a local bare origin and push to it first",
    )
    a.add_argument("--origin-is-template", action="store_true")
    a.add_argument("--project", help="project name (default: the workbench directory name)")
    add_answer_flags(a)
    add_finalize_flags(a)
    a.set_defaults(func=cmd_adopt)
    rf = sub.add_parser("refresh", help="re-run the writers after merging a template update")
    rf.add_argument("--event", help=argparse.SUPPRESS)
    rf.set_defaults(func=cmd_refresh)
    u = sub.add_parser("update", help="merge template tooling into this workbench, minus its docs")
    u.add_argument(
        "--url",
        help=f"template URL (default {DEFAULT_TEMPLATE_URL}); refused when it differs "
        "from an existing template remote",
    )
    u.add_argument("--branch", default="main", help="template branch (default main)")
    u.add_argument(
        "--base",
        metavar="SHA",
        help="template commit the project was copied from; needed once when no history is shared",
    )
    u.add_argument("--lint-command", default="mise run lint", help=argparse.SUPPRESS)
    u.set_defaults(func=update.cmd_update)
    c = sub.add_parser("component", help="add or remove a component after init")
    csub = c.add_subparsers(dest="action", required=True)
    ca = csub.add_parser("add", help="add a new scaffolded component or adopt one")
    ca.add_argument("--component", action="append", default=[], metavar="NAME[:LANG]")
    ca.add_argument("--path", help="checkout outside the workbench; moved to code/<name>")
    ca.add_argument("--url", help="repo URL; a fresh clone is added at code/<name>")
    ca.add_argument("--name", help="with --path or --url: component name")
    ca.add_argument("--remote", metavar="url:<url>|local-bare[:<dir>]|github|gitlab")
    ca.add_argument("--forge-owner")
    ca.add_argument("--public", action="store_true")
    ca.add_argument("--confirm-forge", action="store_true")
    ca.add_argument("--origin-is-template", action="store_true")
    ca.add_argument("--project", help="project name for scaffolds (default: directory name)")
    add_answer_flags(ca)
    ca.set_defaults(func=cmd_component_add)
    cr = csub.add_parser("remove", help="remove a component that holds no unpushed work")
    cr.add_argument("--name", required=True)
    cr.set_defaults(func=cmd_component_remove)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except Refusal as e:
        if e.printed:
            print(e)
        else:
            print(f"refused: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
