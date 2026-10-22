"""The end of init (design D9, D2, D12, D13): marketplace, packs, harness targets, deploy,
template history, license, collision override and the one init commit. Idempotent."""

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import owned
from gitops import Refusal, git

TEMPLATE_MARKET = "workbench-template"
PACKS = ("infra", "observability", "secrets")


@dataclass
class Options:
    project: str
    packs: list[str] = field(default_factory=list)
    harness: list[str] = field(default_factory=list)
    deploy_command: str | None = None
    deploy_verify: str | None = None
    license: str | None = None
    license_holder: str | None = None
    license_file: str | None = None
    user_settings: Path = Path("~/.claude/settings.json")


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def load_wb(root: Path):
    path = root / "plugins" / "workbench" / "scripts" / "lib" / "workbench.py"
    if not path.is_file():
        raise Refusal(f"{path} is missing; cannot resolve the config dir")
    spec = importlib.util.spec_from_file_location("workbench_lib_for_init", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text())
    except (OSError, ValueError) as e:
        raise Refusal(f"{path}: {e}") from e
    if not isinstance(data, dict):
        raise Refusal(f"{path}: must be a JSON object")
    return data


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def validate(opts: Options, root: Path) -> None:
    if not slug(opts.project):
        raise Refusal(f"project name {opts.project!r} has no letters or digits")
    bad = sorted(set(opts.packs) - set(PACKS))
    if bad:
        raise Refusal(f"unknown --pack {', '.join(bad)} (allowed: {', '.join(PACKS)})")
    wb = load_wb(root)
    bad = sorted(set(opts.harness) - set(wb.HARNESS_TARGETS))
    if bad:
        raise Refusal(
            f"unknown --harness {', '.join(bad)} (allowed: {', '.join(wb.HARNESS_TARGETS)})"
        )
    if opts.deploy_verify and not opts.deploy_command:
        raise Refusal("--deploy-verify needs --deploy-command")
    if opts.license_file and not Path(opts.license_file).is_file():
        raise Refusal(f"--license-file {opts.license_file}: no such file")
    if opts.license_file and opts.license:
        raise Refusal("--license and --license-file are exclusive")


def marketplace_and_settings(root: Path, cfg_dir: Path, opts: Options) -> bool:
    """Rename the marketplace and set packs. Returns True when this was the first run."""
    mpath = root / ".claude-plugin" / "marketplace.json"
    market = read_json(mpath)
    old = market.get("name", TEMPLATE_MARKET)
    first = old == TEMPLATE_MARKET
    new = f"{slug(opts.project)}-workbench" if first else old
    market["name"] = new
    write_json(mpath, market)

    spath = cfg_dir / "settings.json"
    settings = read_json(spath)

    def rename(key: str) -> str:
        return key[: -len(old)] + new if key.endswith(f"@{old}") else key

    known = settings.get("extraKnownMarketplaces", {})
    settings["extraKnownMarketplaces"] = {new if k == old else k: v for k, v in known.items()}
    enabled = {rename(k): v for k, v in settings.get("enabledPlugins", {}).items()}
    if first or opts.packs:
        chosen = {f"workbench-{p}@{new}" for p in opts.packs}
        for key in enabled:
            if key.startswith("workbench-") and key.endswith(f"@{new}"):
                enabled[key] = key in chosen
        for key in chosen:
            enabled.setdefault(key, True)
    settings["enabledPlugins"] = enabled
    write_json(spath, settings)
    return first


def workbench_json(cfg_dir: Path, opts: Options) -> None:
    if not (opts.harness or opts.deploy_command):
        return
    path = cfg_dir / "workbench.json"
    cfg = read_json(path) if path.is_file() else {}
    if opts.harness:
        harness = cfg.setdefault("harness", {})
        harness["targets"] = list(dict.fromkeys(opts.harness))
    if opts.deploy_command:
        cfg["deploy"] = {"command": opts.deploy_command, "verify": opts.deploy_verify or ""}
    write_json(path, cfg)


def clear_template_history(root: Path) -> None:
    for rel, kind in owned.INSTANCE_OWNED:
        if kind == "rewritten":
            continue
        target = root / rel
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink(missing_ok=True)
        if kind == "phase":
            target.mkdir(parents=True)
            (target / ".gitkeep").write_text("")


def generate_harness(root: Path, targets: list[str]) -> None:
    """Write the recorded harness targets so the init commit already matches lint:harness."""
    if not targets:
        return
    setup = root / "scripts" / "harness" / "setup.py"
    proc = subprocess.run(
        [sys.executable, str(setup), "--root", str(root), *targets],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise Refusal(f"harness-setup failed: {(proc.stderr or proc.stdout).strip()}")


def default_holder(root: Path) -> str:
    proc = git("var", "GIT_AUTHOR_IDENT", cwd=root, check=False)
    m = re.match(r"^(.*?) <", proc.stdout)
    if proc.returncode != 0 or not m or not m.group(1).strip():
        raise Refusal("--license-holder is required (no git user.name to default to)")
    return m.group(1).strip()


def license_file(root: Path, opts: Options, first: bool) -> None:
    """Rewrite the root LICENSE and every plugins/*/LICENSE with one holder.

    --license none removes only the root LICENSE; plugin licenses stay and are rewritten.
    """
    root_license = root / "LICENSE"
    plugin_licenses = sorted((root / "plugins").glob("*/LICENSE"))
    if opts.license_file:
        for target in (root_license, *plugin_licenses):
            shutil.copyfile(opts.license_file, target)
        return
    if opts.license == "none":
        root_license.unlink(missing_ok=True)
    elif opts.license == "mit" and not root_license.is_file():
        raise Refusal("LICENSE is missing; cannot keep MIT")
    if opts.license == "mit" or (first and opts.license in (None, "none")):
        holder = opts.license_holder or default_holder(root)
        for target in (root_license, *plugin_licenses):
            if target.is_file():
                target.write_text(
                    re.sub(
                        r"^Copyright \(c\) .*$",
                        f"Copyright (c) {date.today().year} {holder}",
                        target.read_text(),
                        count=1,
                        flags=re.MULTILINE,
                    )
                )


def collision_override(root: Path, opts: Options, market: str) -> None:
    """Run doctor's own collision rule so init and doctor cannot drift apart."""
    path = root / "scripts" / "doctor.py"
    if not path.is_file():
        raise Refusal(f"{path} is missing; cannot run the collision check")
    spec = importlib.util.spec_from_file_location("doctor_for_init", path)
    doctor = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = doctor
    spec.loader.exec_module(doctor)
    try:
        keys = doctor.collisions(opts.user_settings.expanduser(), market)
        if keys:
            doctor.write_overrides(root, keys)
    except doctor.Broken as e:
        raise Refusal(str(e)) from e


def load_check_personal(root: Path):
    """The workbench's own check_personal module, or None when it ships no personal lint."""
    path = root / "scripts" / "check_personal.py"
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location("check_personal_for_init", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def allow_vocabulary(root: Path, *, tracked: bool = False) -> None:
    """Allow the project's own vocabulary (design D2): stage everything, scan the staged files
    with check_personal's own digests, record each denylisted digest hit as a project-owned
    allow entry and stage that file too. Literal pattern hits are never auto-allowed.
    With tracked=True every file in the index is scanned, not only the freshly staged ones
    (refresh on a workbench initialised before the allow file existed)."""
    cp = load_check_personal(root)
    if cp is None:
        return
    if not tracked:
        git("add", "-A", cwd=root)
    cfg_path = root / cp.DENYLIST
    if not cfg_path.is_file():
        cfg_path = root / "scripts" / "personal-denylist.json"
    if not cfg_path.is_file():
        return
    cfg = read_json(cfg_path)
    hashes = set(cfg.get("hashes", []))
    local = root / cp.LOCAL_ALLOW
    existing = read_json(local).get("allow", []) if local.is_file() else []
    rules_all = [
        (cp._glob(a["path"]), a.get("pattern"), a.get("line_contains")) for a in cfg["allow"]
    ]
    rules_all += [(cp._glob(a["path"]), a.get("pattern"), a.get("line_contains")) for a in existing]
    scan = ("ls-files", "-z") if tracked else ("diff", "--cached", "--name-only", "-z")
    staged = git(*scan, cwd=root).stdout.split("\0")
    found: set[str] = set()
    for rel in filter(None, staged):
        text = cp._text(root / rel)
        if text is None:
            continue
        rules = [r for r in rules_all if r[0].match(rel)]
        for line in text.splitlines():
            for digest in {cp._digest(c) for c in cp._candidates(line)} & hashes:
                if not cp._allowed(rules, digest, line):
                    found.add(digest)
    if not found:
        return
    entries = {(a["path"], a.get("pattern"), a.get("line_contains")): a for a in existing}
    for digest in found:
        entries[("**", digest, None)] = {"path": "**", "pattern": digest}
    merged = sorted(entries.values(), key=lambda a: json.dumps(a, sort_keys=True))
    write_json(local, {"allow": merged})
    git("add", "--", cp.LOCAL_ALLOW, cwd=root)


def finalize(root: Path, opts: Options) -> None:
    root = root.resolve()
    validate(opts, root)
    wb = load_wb(root)
    try:
        cfg_dir = wb.config_dir(root)
    except wb.ConfigError as e:
        raise Refusal(str(e)) from e
    first = marketplace_and_settings(root, cfg_dir, opts)
    workbench_json(cfg_dir, opts)
    if first:
        clear_template_history(root)
    license_file(root, opts, first)
    market = read_json(root / ".claude-plugin" / "marketplace.json")["name"]
    collision_override(root, opts, market)
    generate_harness(root, list(dict.fromkeys(opts.harness)))
    allow_vocabulary(root)
    git("add", "-A", cwd=root)
    if git("diff", "--cached", "--quiet", cwd=root, check=False).returncode != 0:
        git("commit", "-m", f"chore(workbench): initialise {opts.project}", cwd=root)
        print(f"committed: chore(workbench): initialise {opts.project}")
