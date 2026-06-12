# Kurdish legacy-font PDF → Unicode extractor

Extract clean, logical-order Unicode Kurdish (Sorani) from PDFs built with
non-Unicode legacy fonts (the **Ali_K / AliK** family, **KDylan**, Zarnegar …).
These PDFs return junk like `ÈdÖñW!` on copy/paste because they embed an 8-bit
font whose byte slots hold Kurdish *glyphs* (in visual order, with positional
forms) and carry no `/ToUnicode` map.

## Why generic "font fixers" fail here
* The text is stored **visually reversed**, so RTL words come out backwards.
* Letters are **positional forms**, not base letters.
* Your viewer decodes the font's slots through a **Latin** codepage, so the
  output isn't even Arabic script yet — it's `È W ñ Ö ﬁ …`.

This tool addresses all three by reading the font slots **with their x/y
positions and font name straight from the PDF** (not the lossy clipboard),
re-ordering each line RTL, mapping slots → letters, then normalizing with the
[AsoSoft](https://github.com/AsoSoft/AsoSoft-Library-py) Kurdish library.

## Usage
```bash
pip install -r requirements.txt

# 1. See which fonts are embedded and a raw sample (pick the right map):
python extract.py BOOK.pdf --inspect

# 2. Extract the first chapter to verify zero-error before the whole book:
python extract.py BOOK.pdf --pages 1-12
```

## How the per-book map is finalized
`glyph_map.py` ships a calibration map proven against a known sample
(`test_calibration.py` → `ÈdÖñW!` → `بەرگری`). For a real book the **complete**
slot→letter table is built from the embedded font's own Encoding/Differences
array (dumped by `--inspect`); we validate it page-by-page against the page
images, so the chapter-1 output is checked to be exact before batching.

## Pipeline
```
PDF ─▶ PyMuPDF rawdict (slot + font + x,y)
    ─▶ RTL re-order per line (Latin runs kept LTR)
    ─▶ glyph_map: slot → Kurdish letter
    ─▶ AsoSoft AliK2Unicode + Normalize  ─▶ Unicode Kurdish
```
Output feeds straight into `compiler.html` (the JSON authoring tool).
