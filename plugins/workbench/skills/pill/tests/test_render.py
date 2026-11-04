"""render: a tiny markdown file with an SVG figure renders to a valid PDF."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import render  # noqa: E402

SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="160" viewBox="0 0 400 160">'
    '<rect x="10" y="10" width="150" height="80" fill="#cde" stroke="#333"/>'
    '<text x="20" y="55" font-family="Helvetica" font-size="16">RUNQUEUE</text>'
    '<polygon points="200,50 180,40 180,60" fill="#333"/></svg>'
)

MD = """---
title: Tiny pill
subtitle: A render test
author: tests
date: 2026-01-01
---

# Intro

Text with a citation [1] and a footnote.[^n]

![A run queue box](figures/rq.svg)

| a | b |
|---|---|
| 1 | 2 |

# References

1. Example source. https://example.org/doc

[^n]: The note.
"""


def _write(tmp_path, md=MD):
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "rq.svg").write_text(SVG)
    src = tmp_path / "pill.md"
    src.write_text(md)
    return src


def test_parse_meta_front_matter():
    meta, body = render.parse_meta("---\ntitle: T\nauthor: 'A'\n---\n# H\n")
    assert meta == {"title": "T", "author": "A"}
    assert body.strip() == "# H"


def test_parse_meta_pandoc_title_block():
    meta, body = render.parse_meta("% The title\n% Someone\n% 2026-01-01\n\nBody\n")
    assert meta == {"title": "The title", "author": "Someone", "date": "2026-01-01"}
    assert body.strip() == "Body"


def test_svg_size_from_attrs_and_viewbox(tmp_path):
    a = tmp_path / "a.svg"
    a.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="50mm"/>')
    w, h = render.svg_size_pt(a)
    assert round(w) == 283 and round(h) == 142
    b = tmp_path / "b.svg"
    b.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 200"/>')
    assert render.svg_size_pt(b) == (300.0, 150.0)
    c = tmp_path / "c.svg"
    c.write_text('<svg xmlns="http://www.w3.org/2000/svg"/>')
    with pytest.raises(ValueError):
        render.svg_size_pt(c)


@pytest.fixture
def pdf_deps():
    for mod in ("markdown", "xhtml2pdf", "svglib", "reportlab"):
        pytest.importorskip(mod)
    return pytest.importorskip("pypdf")


@pytest.mark.parametrize("page,width_pt", [("a4", 595), ("phone", 283)])
def test_renders_valid_pdf_with_figure(tmp_path, pdf_deps, page, width_pt):
    src = _write(tmp_path)
    out = tmp_path / "out" / "pill.pdf"
    html = tmp_path / "out" / "pill.html"
    assert render.main([str(src), "-o", str(out), "--page", page, "--html", str(html)]) == 0
    assert out.read_bytes()[:5] == b"%PDF-"
    reader = pdf_deps.PdfReader(str(out))
    assert len(reader.pages) >= 3  # cover, contents, body
    assert round(float(reader.pages[0].mediabox.width)) == width_pt
    text = "\n".join(p.extract_text() for p in reader.pages)
    assert "Tiny pill" in reader.pages[0].extract_text()
    assert "Contents" in reader.pages[1].extract_text()
    assert "Figure 1. A run queue box" in text
    assert "RUNQUEUE" in text  # the SVG is drawn as vectors, its text survives
    assert "page 1 of" in text
    assert "pdf:toc" in html.read_text()


def test_lint_hit_blocks_render(tmp_path, pdf_deps, capsys):
    src = _write(tmp_path, MD.replace("Text with", f"Text {chr(0x2014)} with"))
    out = tmp_path / "pill.pdf"
    assert render.main([str(src), "-o", str(out)]) == 1
    assert "U+2014" in capsys.readouterr().out
    assert not out.exists()
    assert render.main([str(src), "-o", str(out), "--skip-lint"]) == 0


def test_lint_hit_in_svg_blocks_render(tmp_path, pdf_deps, capsys):
    src = _write(tmp_path)
    svg = tmp_path / "figures" / "rq.svg"
    svg.write_text(SVG.replace("RUNQUEUE", f"A {chr(0x2192)} B"))
    assert render.main([str(src), "-o", str(tmp_path / "p.pdf")]) == 1
    assert "rq.svg" in capsys.readouterr().out


def test_missing_image_is_an_error(tmp_path, pdf_deps, capsys):
    src = tmp_path / "p.md"
    src.write_text("# A\n\n![x](figures/missing.svg)\n")
    assert render.main([str(src), "-o", str(tmp_path / "p.pdf")]) == 1
    assert "image not found" in capsys.readouterr().err


def test_remote_image_is_an_error(tmp_path, pdf_deps, capsys):
    src = tmp_path / "p.md"
    src.write_text("# A\n\n![x](https://example.org/x.svg)\n")
    assert render.main([str(src), "-o", str(tmp_path / "p.pdf")]) == 1
    assert "remote image" in capsys.readouterr().err


def test_figure_outside_pill_dir_is_drawn(tmp_path, pdf_deps):
    shared = tmp_path / "shared"
    shared.mkdir()
    (shared / "f.svg").write_text(SVG)
    pill = tmp_path / "pill"
    pill.mkdir()
    (pill / "p.md").write_text("# A\n\n![Shared](../shared/f.svg)\n")
    out = tmp_path / "p.pdf"
    assert render.main([str(pill / "p.md"), "-o", str(out)]) == 0
    text = "\n".join(p.extract_text() for p in pdf_deps.PdfReader(str(out)).pages)
    assert "RUNQUEUE" in text


def test_shipped_template_and_example_figure_render(tmp_path, pdf_deps):
    refs = Path(__file__).resolve().parents[1] / "references"
    md = (refs / "pill-template.md").read_text()
    (tmp_path / "figures").mkdir()
    (tmp_path / "figures" / "q1-mechanism.svg").write_text(
        (refs / "example-figure.svg").read_text()
    )
    (tmp_path / "pill.md").write_text(md)
    out = tmp_path / "pill.pdf"
    assert render.main([str(tmp_path / "pill.md"), "-o", str(out), "--page", "phone"]) == 0
    text = "\n".join(p.extract_text() for p in pdf_deps.PdfReader(str(out)).pages)
    for needle in ("{Question 1}", "{Question 2}", "producer", "Figure 1.", "References"):
        assert needle in text, needle
