# Kurdish legacy-font PDF → Unicode extractor

Recover clean, logical-order Unicode Kurdish (Sorani) from PDFs built with
non-Unicode legacy fonts (the **Ali_K / AliK** family). These PDFs return junk
like `ÈdÖñW!` on copy/paste because their byte/CID slots hold Kurdish *glyphs*
(visual order, positional forms) with no usable `/ToUnicode` map. Output feeds
straight into `compiler.html` (the JSON authoring tool).

## Two approaches — and which one to use

### 1. OCR pipeline — `ocr_extract.py`  ← **use this**
Inspecting the real book (`partial_zinda.pdf`) revealed the fonts are **subsetted
CID TrueType** (`CIDFont+F1..F18`, Identity-H). Their cmaps map the junk
codepoints (`È ñ Ö W …`) to **standard Latin glyph names** (`Egrave`, `ntilde`,
`Odieresis`, `W`): a Latin font whose slots were repurposed to hold Kurdish
letter *outlines*. So **the font carries no Kurdish information to dump** — the
only ground truth is the glyph outline itself.

The robust, font-independent fix is therefore to **render each page and OCR the
image**. When rendered, the outlines draw as perfectly-shaped Kurdish, so an
Arabic-script OCR model reads correct, logical-order Sorani — RTL, ligatures and
multi-column question blocks all handled. Embedded Latin runs (ATP, HIV, Muscle
fatigue) already extract correctly from the PDF text layer, so we pull those
**verbatim** and list them next to the OCR text.

```bash
pip install -r requirements.txt
apt-get install tesseract-ocr            # OCR engine

# Arabic-script "best" model (covers Persian/Kurdish extended letters):
#   Arabic.traineddata from tesseract-ocr/tessdata_best/script/ → ./td/

python ocr_extract.py BOOK.pdf --tessdata ./td -l Arabic --pages 1-6 --out out/
```

Pipeline:
```
PDF page ─▶ PyMuPDF render @300dpi ─▶ Tesseract (Arabic, --psm 3)
         ─▶ drop header/noise · AsoSoft Normalize (ك→ک, ي/ى→ی, ه‌→ە, NFC)
         ─▶ logical-order Sorani  +  exact Latin terms from the PDF text layer
```
`sample_output/` holds the verified per-page text for `partial_zinda.pdf`.

### 2. Glyph-map pipeline — `extract.py` (fallback for *encoded* fonts)
If a PDF's legacy font ships **meaningful** glyph names (`reh`, `beh`, `uni0631`)
or a simple 8-bit Encoding/Differences array, an exact, reversible slot→letter
map is preferable to OCR. That path lives in `extract.py` + `glyph_map.py` +
`convert.py`, with a calibration self-test (`test_calibration.py` →
`ÈdÖñW!` → `بەرگری`). It does **not** apply to `partial_zinda.pdf` (Latin glyph
names only), but is kept for books that do expose a real encoding.

```bash
python extract.py BOOK.pdf --inspect      # list fonts + raw sample first
python extract.py BOOK.pdf --pages 1-12
```

## Accuracy notes (OCR)
* Body Sorani is faithful; occasional slips are `ڤ→ق`, `ێ↔ی`, `پ↔ب`.
* Latin scientific terms inside Kurdish lines are best taken from the
  `[Latin terms …]` appendix (verbatim from the PDF), not from OCR.
* Validate chapter 1 against the rendered page before batching the whole book.
