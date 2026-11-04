"""lint_text: em dashes, smart quotes and unicode arrows fail; plain text passes."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import lint_text  # noqa: E402


def test_clean_file_passes(tmp_path, capsys):
    f = tmp_path / "ok.md"
    f.write_text("# Title\n\nPlain - hyphens, 'quotes' and \"doubles\" -> arrows.\n")
    assert lint_text.main([str(f)]) == 0
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize(
    "ch",
    [chr(c) for c in (0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2192, 0x21D2, 0x27F6, 0x2B95)],
)
def test_banned_char_fails_with_location(tmp_path, capsys, ch):
    f = tmp_path / "bad.md"
    f.write_text(f"line one\nab{ch}cd\n")
    assert lint_text.main([str(f)]) == 1
    out = capsys.readouterr().out
    assert f"{f}:2:3: U+{ord(ch):04X}" in out


def test_every_hit_reported_across_files(tmp_path, capsys):
    a = tmp_path / "a.md"
    b = tmp_path / "b.svg"
    em = chr(0x2014)
    a.write_text(f"x{em}y{em}z\n")
    b.write_text(f"<text>{chr(0x201C)}q{chr(0x201D)}</text>\n")
    assert lint_text.main([str(a), str(b)]) == 1
    assert len(capsys.readouterr().out.strip().splitlines()) == 4


def test_en_dash_and_ascii_arrows_allowed():
    assert lint_text.scan_text("a -> b <- c => d", "x") == []


def test_usage_and_missing_file(tmp_path):
    assert lint_text.main([]) == 2
    assert lint_text.main([str(tmp_path / "nope.md")]) == 2
