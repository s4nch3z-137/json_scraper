#!/usr/bin/env python3
"""
OCR-based recovery of logical-order Unicode Kurdish (Sorani) from biology-text
PDFs built with legacy non-Unicode fonts (the Ali_K family).

Why OCR and not a glyph->letter table (the original plan)
--------------------------------------------------------
The first approach (extract.py + glyph_map.py) assumed simple 8-bit fonts with
an Encoding/Differences array of *meaningful* glyph names (reh, beh, ...) we
could dump and turn into an exact slot->letter map.

Inspecting THIS PDF showed a different reality (see `--inspect` in extract.py):

  * Every font is a subsetted CID TrueType (`CIDFont+F1..F18`, Identity-H).
  * Their embedded cmaps map the junk codepoints (È ñ Ö W ...) to *standard
    Latin glyph names* (Egrave, ntilde, Odieresis, W ...). Those names are the
    ORIGINAL Latin slots that were repurposed to hold Kurdish letter outlines.
  * So the font carries NO Kurdish information to dump - the only ground truth
    for what a slot looks like is the glyph OUTLINE itself.

The decisive observation: when the page is rendered, the outlines draw as
perfectly-shaped Kurdish. So the robust, font-independent recovery is to
render each page and OCR the image with a Arabic-script model. Embedded Latin
runs (ATP, HIV, Muscle fatigue) already extract correctly from the PDF text
layer, so we pull those verbatim and list them alongside the OCR text.

Pipeline
--------
1. Render each page at high DPI (default 300) with PyMuPDF.
2. OCR with Tesseract using an Arabic-script model and PSM 3 (auto page
   segmentation - this keeps multi-column question blocks in reading order).
3. Clean: drop the running page header, normalize to proper Sorani Unicode with
   AsoSoft (ك->ک, ي/ى->ی, ه‌->ە, NFC), collapse blank runs.
4. Pull the exact embedded Latin terms straight from the PDF text layer.

Setup
-----
    pip install pymupdf asosoft
    apt-get install tesseract-ocr            # the engine
    # Arabic-script "best" model (handles Persian/Kurdish extended letters):
    #   download Arabic.traineddata from tesseract-ocr/tessdata_best/script/
    #   into a folder and pass it with --tessdata, or install tesseract-ocr-ara.

Usage
-----
    python ocr_extract.py FILE.pdf --pages 1-5 --tessdata ./td -l Arabic
    python ocr_extract.py FILE.pdf --out out_dir            # write per-page txt
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
import unicodedata

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("PyMuPDF required:  pip install pymupdf")

try:
    import asosoft
    _HAVE_ASOSOFT = True
except ImportError:
    _HAVE_ASOSOFT = False


# Running header stamped on every page, e.g. "Chapter 1   1/16/18 10:00 AM   Page 22".
# OCR may split it across lines or reorder it, so match any of its signatures:
# a standalone "Chapter N", a m/d/yy date stamp, or a "Page N" run.
_HEADER_RE = re.compile(
    r"(?i)^\s*(?:chapter\s+\d+\s*$"          # "Chapter 1"
    r"|.*\d{1,2}/\d{1,2}/\d{2,4}.*$"          # "...1/16/18 10:00 AM..."
    r"|.*\bpage\s+\d+\b.*$)"                  # "...Page 22..."
)
# A line that is only OCR noise (lone digits/punct left over from rules/marks).
_NOISE_RE = re.compile(r"^[\s\d.،؛•·ـ‌‏‏‎©]+$")


def parse_pages(spec, n):
    if not spec:
        return list(range(n))
    out = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a) - 1, int(b)))
        else:
            out.append(int(part) - 1)
    return [p for p in out if 0 <= p < n]


def render_page(page, dpi):
    pix = page.get_pixmap(dpi=dpi)
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    pix.save(path)
    return path


def ocr_image(path, lang, psm, tessdata):
    cmd = ["tesseract", path, "stdout", "-l", lang, "--psm", str(psm)]
    if tessdata:
        cmd += ["--tessdata-dir", tessdata]
    env = dict(os.environ)
    res = subprocess.run(cmd, capture_output=True, text=True, env=env)
    if res.returncode != 0:
        sys.stderr.write(res.stderr)
    return res.stdout


def clean_text(raw):
    """Drop header/noise lines, normalize to Sorani Unicode, collapse blanks."""
    lines = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or _HEADER_RE.match(line) or _NOISE_RE.match(line):
            continue
        lines.append(line)
    text = "\n".join(lines)
    text = unicodedata.normalize("NFC", text)
    if _HAVE_ASOSOFT:
        try:
            text = asosoft.Normalize(text)
        except Exception:
            pass
    # Collapse 3+ newlines to a single blank line.
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


_HEADER_WORDS = {"chapter", "page", "am", "pm"}


def latin_terms(page):
    """Exact embedded Latin runs from the PDF text layer (already correct).

    These are the scientific terms (ATP, HIV, Muscle fatigue, ...) that OCR of
    an Arabic-script model tends to mangle; here we get them verbatim. The
    running header ("Chapter 1 ... Page 22") is skipped by its top y position
    and a small stop-word set.
    """
    page_top = page.rect.y0
    header_cut = page_top + page.rect.height * 0.06  # top 6% is the header band
    words = []
    for w in page.get_text("words"):  # x0,y0,x1,y1,word,block,line,wordno
        token = w[4].strip()
        if w[1] < header_cut or token.lower() in _HEADER_WORDS:
            continue
        if len(token) >= 2 and re.fullmatch(r"[A-Za-z][A-Za-z0-9\-/]*", token):
            words.append(token)
    # de-dup, preserve order
    seen, out = set(), []
    for t in words:
        if t.lower() not in seen:
            seen.add(t.lower())
            out.append(t)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--pages", help="e.g. 1-5 or 1,3,7 (default: all)")
    ap.add_argument("--dpi", type=int, default=300)
    ap.add_argument("-l", "--lang", default="Arabic",
                    help="tesseract language/script model (default: Arabic)")
    ap.add_argument("--psm", type=int, default=3,
                    help="tesseract page-seg mode (default 3: auto, keeps columns)")
    ap.add_argument("--tessdata", help="custom tessdata dir holding the model")
    ap.add_argument("--out", help="write per-page <out>/page_NN.txt files")
    ap.add_argument("--no-latin", action="store_true",
                    help="don't append the exact embedded Latin terms")
    args = ap.parse_args()

    doc = fitz.open(args.pdf)
    if args.out:
        os.makedirs(args.out, exist_ok=True)

    for p in parse_pages(args.pages, doc.page_count):
        page = doc[p]
        img = render_page(page, args.dpi)
        try:
            raw = ocr_image(img, args.lang, args.psm, args.tessdata)
        finally:
            os.unlink(img)
        text = clean_text(raw)

        if not args.no_latin:
            terms = latin_terms(page)
            if terms:
                text += "\n\n[Latin terms in page, verbatim from PDF]: " + ", ".join(terms)

        block = f"\n===== page {p + 1} =====\n{text}\n"
        print(block)
        if args.out:
            with open(os.path.join(args.out, f"page_{p + 1:02d}.txt"), "w",
                      encoding="utf-8") as fh:
                fh.write(text + "\n")


if __name__ == "__main__":
    main()
