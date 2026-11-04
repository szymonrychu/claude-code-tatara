"""Render a pill: pandoc-style markdown plus SVG figures to a PDF.

Pure pip stack, no pandoc, typst, LaTeX, chromium or pango needed:
markdown (tables, fenced_code, toc, footnotes, attr_list, sane_lists) -> HTML with
print CSS -> xhtml2pdf (reportlab), SVG figures drawn as vectors through svglib.

Usage:
  render.py INPUT.md -o OUTPUT.pdf [--page a4|phone] [--html OUT.html] [--skip-lint]

The title block is YAML-ish front matter (`title:`, `subtitle:`, `author:`,
`date:` between `---` lines) or a pandoc title block (`% title`, `% author`,
`% date`). It becomes the cover page; a table of contents follows, then the
body, with `Page N of M` in every footer. An image alone in its paragraph,
`![Caption](figures/x.svg)`, becomes a numbered figure with that caption.
Relative image paths resolve against the markdown file's directory.

Exit 0 on success, 1 on a lint hit or render error, 2 on a usage error.
"""

import argparse
import datetime
import html
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import lint_text  # noqa: E402

MISSING_DEPS = (
    "render: missing python packages ({}). Create the venv first:\n"
    "  bash {}/setup_venv.sh   # then run render.py with that venv's python"
)


@dataclass(frozen=True)
class Page:
    width_mm: float
    height_mm: float
    margin_mm: float
    font_pt: float


PAGES = {
    # A4 at a comfortable reading size
    "a4": Page(210, 297, 20, 12),
    # 9:16 page that fills a phone screen without zooming
    "phone": Page(100, 178, 8, 11),
}

MM_TO_PT = 72 / 25.4
UNIT_TO_PT = {"": 0.75, "px": 0.75, "pt": 1.0, "mm": MM_TO_PT, "cm": 10 * MM_TO_PT, "in": 72.0}


def parse_meta(text: str) -> tuple[dict[str, str], str]:
    """Split a front-matter or pandoc title block off the markdown."""
    meta: dict[str, str] = {}
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i, line in enumerate(lines[1:], 1):
            if line.strip() in ("---", "..."):
                for raw in lines[1:i]:
                    key, sep, value = raw.partition(":")
                    if sep and key.strip():
                        meta[key.strip().lower()] = value.strip().strip("\"'")
                return meta, "\n".join(lines[i + 1 :])
        return meta, text
    if lines and lines[0].startswith("%"):
        keys = ("title", "author", "date")
        n = 0
        while n < len(lines) and n < 3 and lines[n].startswith("%"):
            value = lines[n][1:].strip()
            if value:
                meta[keys[n]] = value
            n += 1
        return meta, "\n".join(lines[n:])
    return meta, text


def _length_pt(value: str | None) -> float | None:
    if not value:
        return None
    m = re.fullmatch(r"\s*([0-9.]+)\s*([a-z]*)\s*", value)
    if not m or m.group(2) not in UNIT_TO_PT:
        return None
    return float(m.group(1)) * UNIT_TO_PT[m.group(2)]


def svg_size_pt(path: Path) -> tuple[float, float]:
    """Intrinsic size of an SVG in points, from width/height or the viewBox."""
    root = ET.parse(path).getroot()
    w, h = _length_pt(root.get("width")), _length_pt(root.get("height"))
    if w and h:
        return w, h
    vb = (root.get("viewBox") or "").replace(",", " ").split()
    if len(vb) == 4:
        vw, vh = float(vb[2]), float(vb[3])
        if w:
            return w, w * vh / vw
        if h:
            return h * vw / vh, h
        return vw * 0.75, vh * 0.75
    raise ValueError(f"{path}: SVG needs width and height or a viewBox")


def figure_extension(base: Path, max_width_pt: float, images: list[Path]):
    """A markdown extension turning a lone image into a numbered, captioned figure."""
    from markdown.extensions import Extension
    from markdown.treeprocessors import Treeprocessor

    class Figures(Treeprocessor):
        def run(self, root):
            count = 0
            for parent in root.iter():
                for idx, child in enumerate(list(parent)):
                    if child.tag != "p" or len(child) != 1 or child[0].tag != "img":
                        continue
                    img = child[0]
                    if (child.text or "").strip() or (img.tail or "").strip():
                        continue
                    count += 1
                    fig = self._figure(img, count)
                    fig.tail = child.tail
                    parent.remove(child)
                    parent.insert(idx, fig)
            for img in root.iter("img"):
                self._resolve(img)

        def _resolve(self, img):
            src = img.get("src", "")
            if src.startswith("data:"):
                return
            if re.match(r"^[a-z]+://", src):
                raise ValueError(f"remote image {src}: save figures next to the markdown")
            path = (base / src).resolve()
            if not path.is_file():
                raise FileNotFoundError(f"image not found: {src} (resolved to {path})")
            images.append(path)
            img.set("src", str(path))
            if path.suffix.lower() == ".svg" and not img.get("width"):
                w, h = svg_size_pt(path)
                scale = min(1.0, max_width_pt / w)
                # CSS, not width/height attributes: xhtml2pdf reads those as
                # px and scales them by 0.75, so a figure came out 75% wide
                img.set("style", f"width: {w * scale:.1f}pt; height: {h * scale:.1f}pt")

        def _figure(self, img, n):
            fig = ET.Element("div", {"class": "figure"})
            fig.append(img)
            img.tail = None
            cap = ET.SubElement(fig, "p", {"class": "caption"})
            alt = img.get("alt", "").strip()
            cap.text = f"Figure {n}. {alt}" if alt else f"Figure {n}."
            return fig

    class FigureExtension(Extension):
        def extendMarkdown(self, md):  # noqa: N802 - markdown API name
            md.treeprocessors.register(Figures(md), "pill_figures", 5)

    return FigureExtension()


LINE_HEIGHT = 1.35
FOOTER_SCALE = 0.8
# room for a title long enough to wrap the footer onto a second line
FOOTER_LINES = 2


def css(page: Page) -> str:
    footer_font = page.font_pt * FOOTER_SCALE
    footer_mm = (FOOTER_LINES * footer_font * LINE_HEIGHT + 2) / MM_TO_PT
    footer_bottom = page.margin_mm / 2
    bottom = footer_bottom + footer_mm + page.margin_mm / 2
    return f"""
@page {{
  size: {page.width_mm}mm {page.height_mm}mm;
  margin: {page.margin_mm}mm {page.margin_mm}mm {bottom:.1f}mm {page.margin_mm}mm;
  @frame footer {{
    -pdf-frame-content: footer;
    bottom: {footer_bottom:.1f}mm; height: {footer_mm:.1f}mm;
    margin-left: {page.margin_mm}mm; margin-right: {page.margin_mm}mm;
  }}
}}
body {{ font-family: Helvetica; font-size: {page.font_pt}pt; line-height: {LINE_HEIGHT};
  overflow-wrap: break-word; }}
h1 {{ font-size: {page.font_pt * 1.7:.1f}pt; margin-top: 10pt; }}
h2 {{ font-size: {page.font_pt * 1.35:.1f}pt; margin-top: 8pt; }}
h3 {{ font-size: {page.font_pt * 1.15:.1f}pt; }}
h1, h2, h3 {{ -pdf-keep-with-next: true; }}
p, li {{ text-align: left; }}
code, pre {{ font-family: Courier; font-size: {page.font_pt * 0.85:.1f}pt; }}
pre {{ background-color: #f2f2f2; padding: 4pt; border: 0.5pt solid #cccccc; }}
table {{ border: 0.5pt solid #888888; padding: 2pt; }}
th {{ background-color: #e6e6e6; font-weight: bold; }}
.figure {{ text-align: center; margin: 6pt 0; }}
.caption {{ font-size: {page.font_pt * 0.9:.1f}pt; font-style: italic; text-align: center; }}
.footer {{ text-align: center; font-size: {footer_font:.1f}pt; color: #555555; }}
.cover-title {{ font-size: {page.font_pt * 2.4:.1f}pt; font-weight: bold;
  margin-top: {page.height_mm / 4:.0f}mm; text-align: center; }}
.cover-sub {{ font-size: {page.font_pt * 1.3:.1f}pt; text-align: center; margin-top: 8pt; }}
.cover-meta {{ font-size: {page.font_pt}pt; text-align: center; margin-top: 20pt; color: #444444; }}
.toc-title {{ font-size: {page.font_pt * 1.7:.1f}pt; font-weight: bold; margin-bottom: 8pt; }}
pdftoc {{ color: #000000; }}
pdftoc.pdftoclevel0 {{ font-weight: bold; margin-top: 4pt; }}
pdftoc.pdftoclevel1 {{ margin-left: 12pt; }}
pdftoc.pdftoclevel2 {{ margin-left: 24pt; }}
pdftoc.pdftoclevel3, pdftoc.pdftoclevel4, pdftoc.pdftoclevel5 {{ display: none; }}
"""


def build_html(md_text: str, base: Path, page: Page, images: list[Path]) -> str:
    import markdown

    meta, body_md = parse_meta(md_text)
    max_width = (page.width_mm - 2 * page.margin_mm) * MM_TO_PT
    md = markdown.Markdown(
        extensions=[
            "tables",
            "fenced_code",
            "toc",
            "footnotes",
            "attr_list",
            "sane_lists",
            figure_extension(base, max_width, images),
        ],
        extension_configs={"footnotes": {"BACKLINK_TEXT": "^"}},
        output_format="xhtml",
    )
    body = md.convert(body_md)
    esc = {k: html.escape(v) for k, v in meta.items()}
    title = esc.get("title", "Untitled pill")
    cover_meta = " - ".join(
        x for x in (esc.get("author"), esc.get("date", datetime.date.today().isoformat())) if x
    )
    sub = f'<p class="cover-sub">{esc["subtitle"]}</p>' if "subtitle" in esc else ""
    return f"""<html><head><meta charset="utf-8"/><title>{title}</title>
<style>{css(page)}</style></head><body>
<div id="footer" class="footer">{title} - page <pdf:pagenumber/> of <pdf:pagecount/></div>
<p class="cover-title">{title}</p>{sub}<p class="cover-meta">{cover_meta}</p>
<pdf:nextpage/>
<p class="toc-title">Contents</p>
<pdf:toc/>
<pdf:nextpage/>
{body}
</body></html>"""


def render(
    src: Path,
    out: Path,
    page_name: str = "a4",
    html_out: Path | None = None,
    skip_lint: bool = False,
) -> int:
    try:
        import markdown  # noqa: F401
        from xhtml2pdf import pisa
        from xhtml2pdf.config.resources import ResourceAccessPolicy
    except ImportError as e:
        print(MISSING_DEPS.format(e.name, Path(__file__).resolve().parent), file=sys.stderr)
        return 1
    text = src.read_text(encoding="utf-8")
    images: list[Path] = []
    try:
        doc = build_html(text, src.parent.resolve(), PAGES[page_name], images)
    except (FileNotFoundError, ValueError, ET.ParseError) as e:
        print(f"render: {e}", file=sys.stderr)
        return 1
    if not skip_lint:
        hits = lint_text.scan_text(text, str(src))
        for img in images:
            if img.suffix.lower() == ".svg":
                hits += lint_text.scan_text(img.read_text(encoding="utf-8"), str(img))
        if hits:
            print("\n".join(hits))
            print("render: fix the banned characters above (or pass --skip-lint)", file=sys.stderr)
            return 1
    if html_out:
        html_out.parent.mkdir(parents=True, exist_ok=True)
        html_out.write_text(doc, encoding="utf-8")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("wb") as fh:
        # local reads confined to the pill dir and the figure dirs; no network
        policy = ResourceAccessPolicy(
            allow_remote=False,
            base_dir=src.parent.resolve(),
            extra_roots=tuple({img.parent for img in images}),
        )
        result = pisa.CreatePDF(doc, dest=fh, encoding="utf-8", resource_policy=policy)
    if result.err:
        print(f"render: xhtml2pdf reported {result.err} error(s)", file=sys.stderr)
        return 1
    with out.open("rb") as fh:
        if fh.read(5) != b"%PDF-":
            print(f"render: {out} is not a PDF", file=sys.stderr)
            return 1
    print(f"{out} ({out.stat().st_size} bytes, page {page_name}, {len(images)} image(s))")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("input", type=Path, help="pill markdown file")
    ap.add_argument("-o", "--output", type=Path, help="PDF path (default: INPUT with .pdf)")
    ap.add_argument("--page", choices=sorted(PAGES), default="a4")
    ap.add_argument("--html", type=Path, help="also write the intermediate HTML here")
    ap.add_argument("--skip-lint", action="store_true", help="do not run lint_text first")
    args = ap.parse_args(argv)
    if not args.input.is_file():
        ap.error(f"no such file: {args.input}")
    out = args.output or args.input.with_suffix(".pdf")
    return render(args.input, out, args.page, args.html, args.skip_lint)


if __name__ == "__main__":
    sys.exit(main())
