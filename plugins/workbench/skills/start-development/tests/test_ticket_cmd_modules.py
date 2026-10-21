"""ticket.py loads subcommands from sibling modules in ticket_cmds/ (D18)."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "skills" / "start-development" / "scripts" / "ticket.py"
sys.path.insert(0, str(SCRIPT.parent))
import ticket  # noqa: E402

MOD = """
import sys
def register(sub, t):
    sp = sub.add_parser("{name}")
    sp.set_defaults(fn=run)
    sp.add_argument("--word", default="hi")
def run(a):
    {body}
"""


def make(tmp_path, **mods):
    d = tmp_path / "ticket_cmds"
    d.mkdir()
    (d / "__init__.py").write_text("")
    for fname, (name, body) in mods.items():
        (d / f"{fname}.py").write_text(MOD.format(name=name, body=body))
    return d


def test_package_exists():
    init = SCRIPT.parent / "ticket_cmds" / "__init__.py"
    assert init.is_file()


def test_module_subcommand_registers(tmp_path):
    d = make(tmp_path, b_mod=("bcmd", "return 3"), a_mod=("acmd", "return 0"))
    ap = ticket.build_parser(d)
    names = list(ap._subparsers._group_actions[0].choices)
    assert names.index("acmd") < names.index("bcmd")
    assert names.index("slug") < names.index("acmd")
    a = ap.parse_args(["acmd", "--root", "/x"])
    assert a.root == "/x"


def test_t_is_ticket_module(tmp_path):
    d = tmp_path / "ticket_cmds"
    d.mkdir()
    (d / "__init__.py").write_text("")
    (d / "m.py").write_text(
        "def register(sub, t):\n    sp = sub.add_parser('m')\n"
        "    sp.set_defaults(fn=lambda a: t.TicketError and 0, t=t)\n"
    )
    a = ticket.build_parser(d).parse_args(["m"])
    assert a.t is ticket


def test_name_clash_fails(tmp_path):
    d = make(tmp_path, dup=("slug", "return 0"))
    with pytest.raises(ticket.TicketError) as e:
        ticket.build_parser(d)
    assert "slug" in str(e.value) and "dup" in str(e.value) and "built-in" in str(e.value)


def test_clash_between_modules_raises_naming_both(tmp_path):
    d = make(tmp_path, a=("same", "return 0"), b=("same", "return 0"))
    with pytest.raises(ticket.TicketError) as e:
        ticket.build_parser(d)
    assert "a" in str(e.value) and "b" in str(e.value) and "same" in str(e.value)


def test_module_ticket_error_exit_1(tmp_path, monkeypatch, capsys):
    d = make(tmp_path, bad=("boom", "raise __import__('ticket').TicketError('nope')"))
    monkeypatch.setattr(ticket, "CMD_DIR", d)
    assert ticket.main(["boom", "--root", str(tmp_path)]) == 1
    assert "ticket.py: nope" in capsys.readouterr().err


def test_builtin_cli_still_works():
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "slug", "Hello World"], capture_output=True, text=True
    )
    assert r.stdout.strip() == "hello-world"
