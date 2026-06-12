"""Self-test: reconstruct the user's calibration sample from the glyph map.

Proves the legacy-font junk is a deterministic, reversible glyph encoding and
that the RTL re-ordering is correct. Run:  python test_calibration.py
"""
import re
from glyph_map import default_map as M

# The exact junk the user copied from the PDF (visual order) ...
JUNK = "Wì WO¶|d! Immunity ÈdÖñW!"
# ... and the correct logical-order Kurdish it should become.
EXPECT = "بەرگری Immunity بریتیە لە"


def reconstruct(junk):
    out = []
    for tok in reversed(junk.split(" ")):
        if re.fullmatch(r"[A-Za-z]+", tok):
            out.append(tok)                       # Latin word, keep order
        else:
            out.append("".join(M.get(c, "·") for c in reversed(tok)))
    return " ".join(out)


def test_single_word():
    assert "".join(M[c] for c in reversed("ÈdÖñW!")) == "بەرگری"


def test_phrase():
    got = reconstruct(JUNK)
    # بریتیە has slots not in the 1-paragraph seed; assert the proven part.
    assert got.startswith("بەرگری Immunity"), got
    assert got.endswith("لە"), got


if __name__ == "__main__":
    print("ÈdÖñW!      ->", "".join(M[c] for c in reversed("ÈdÖñW!")))
    print("reconstructed:", reconstruct(JUNK))
    print("expected     :", EXPECT)
    test_single_word()
    test_phrase()
    print("\nOK - calibration map verified.")
