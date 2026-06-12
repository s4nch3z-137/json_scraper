"""
Font slot -> Kurdish base-letter maps for legacy Kurdish PDFs.

`default_map` is SEEDED from the calibration sample the user provided
(one paragraph of junk + its correct text). It is intentionally partial:
the authoritative, complete table is built per-document from the embedded
font's Encoding/Differences array (see extract.py --inspect). Each entry maps
ONE extracted font slot to ONE Kurdish base letter; positional-form merging,
lam-alef ligatures and letter fixes happen afterwards in convert.py.

Keys are the characters that PyMuPDF emits for this font. Values are Kurdish
Arabic-script letters. '' means the slot is a spacing/zero-width artifact.
"""

# Calibration map derived from the sample paragraph (بەرگری Immunity بریتیە ...).
# Verified: "ÈdÖñW!" -> "بەرگری".  Extend/replace from the embedded encoding.
default_map = {
    "!": "ب",
    "W": "ە",
    "ñ": "ر",
    "d": "ر",
    "Ö": "گ",
    "È": "ی",
    "ì": "ل",
    "ï": "ن",
    "U": "ا",
    "«": "ا",
    "ë": "ک",
    "œ": "م",
    "…": "ە",
    "O": "ی",
    "|": "ی",
    "¶": "ت",
    "Å": "ش",
    "8": "خ",
    "Ù": "ۆ",
    "u": "و",
    "z": "م",
    "X": "د",
    # diacritic / vowel-mark slots seen in the sample (resolved in convert.py)
    ":": "ٗ",   # small high mark used by ۆ / ێ clusters (placeholder)
    "?": "",          # soft-hyphen / kashida artifact between clusters
    "¨": "",          # spacing artifact
}

# Per-font overrides keyed by the exact embedded font name (from --inspect).
# e.g. FONT_MAPS["Ali_K_Samik"] = {...}
FONT_MAPS = {}
