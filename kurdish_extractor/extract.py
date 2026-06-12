#!/usr/bin/env python3
"""
Extract logical-order Unicode Kurdish (Sorani) text from PDFs that were made
with legacy non-Unicode fonts (the "Ali_K" / AliK family, KDylan, etc.).

Why the usual copy/paste gives junk
-----------------------------------
These PDFs embed an 8-bit font whose byte slots hold Kurdish *glyphs* (often
positional forms) instead of Unicode letters, and they ship with no /ToUnicode
map. So any viewer extracts the raw font slots -> you get characters like
È W ñ Ö ﬁ … ¨ instead of letters, in visual (reversed) order.

Strategy
--------
1. Read every glyph WITH its font name and x/y position (PyMuPDF rawdict).
2. Re-order each line right-to-left (RTL) into logical order, keeping embedded
   Latin runs (e.g. "Immunity") in their own left-to-right order.
3. Map each font slot -> Kurdish base letter via a font-specific table
   (glyph_map.py). The table is seeded from a calibration sample and is
   completed/validated from the embedded font's own Encoding/Differences array
   (dumped by `inspect_fonts`).
4. Normalize letter choices and Unicode with AsoSoft (AliK2Unicode + Normalize).

Run `python extract.py FILE.pdf --inspect` first to see the fonts and a raw
sample, then `python extract.py FILE.pdf --pages 1-5` to extract.
"""
import argparse
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("PyMuPDF required:  pip install pymupdf")

from glyph_map import FONT_MAPS, default_map
from convert import to_unicode_kurdish


def parse_pages(spec, n):
    if not spec:
        return range(n)
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a) - 1, int(b)))
        else:
            out.append(int(part) - 1)
    return [p for p in out if 0 <= p < n]


def inspect_fonts(doc):
    """List embedded fonts and their Encoding/Differences glyph names.

    Meaningful glyph names (e.g. 'reh', 'beh', 'uni0631') let us build an exact
    map automatically.  Opaque names ('g37', 'c12') mean we calibrate against
    the page image instead.
    """
    seen = set()
    for page in doc:
        for f in page.get_fonts(full=True):
            xref = f[0]
            name = f[3]
            if xref in seen:
                continue
            seen.add(xref)
            print(f"\nFONT xref={xref}  name={name!r}  type={f[1]} enc={f[5]!r}")
            try:
                _buf = doc.extract_font(xref)
                print(f"  embedded font bytes: {len(_buf[3]) if _buf[3] else 0}")
            except Exception as e:
                print("  (could not extract font:", e, ")")
    print("\n--- raw first-page sample (font slots, visual order) ---")
    print(doc[0].get_text("text")[:600])


def line_to_logical(spans):
    """Re-order one visual line into logical RTL order and map glyph slots.

    spans: list of (text, font_name, x0) for one line, left-to-right.
    """
    # Sort left-to-right by x, then walk right-to-left for RTL logical order.
    spans = sorted(spans, key=lambda s: s[2])
    pieces = []
    for text, font, _x in reversed(spans):
        gmap = FONT_MAPS.get(font, default_map)
        if text.strip().isascii() and any(c.isalpha() for c in text):
            pieces.append(text)               # Latin run: keep as-is
        else:
            pieces.append("".join(gmap.get(c, c) for c in reversed(text)))
    return "".join(pieces)


def extract_page(page):
    raw = page.get_text("rawdict")
    out_lines = []
    for block in raw.get("blocks", []):
        for line in block.get("lines", []):
            spans = []
            for span in line.get("spans", []):
                chars = "".join(c["c"] for c in span.get("chars", []))
                if chars:
                    spans.append((chars, span.get("font", ""), span["bbox"][0]))
            if spans:
                out_lines.append(line_to_logical(spans))
    return "\n".join(out_lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--pages", help="e.g. 1-5 or 1,3,7")
    ap.add_argument("--inspect", action="store_true",
                    help="list fonts + raw sample, then exit")
    ap.add_argument("--no-normalize", action="store_true")
    args = ap.parse_args()

    doc = fitz.open(args.pdf)
    if args.inspect:
        inspect_fonts(doc)
        return

    for p in parse_pages(args.pages, doc.page_count):
        text = extract_page(doc[p])
        if not args.no_normalize:
            text = to_unicode_kurdish(text)
        print(f"\n===== page {p + 1} =====")
        print(text)


if __name__ == "__main__":
    main()
