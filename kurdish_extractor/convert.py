"""
Post-process mapped Arabic-script text into clean, normalized Unicode Kurdish.

After glyph_map.py turns font slots into Kurdish letters, two things remain:
  1. Fix legacy letter choices that AliK fonts overload
     (ث->پ, ض->چ, ظ->ڤ, ط->گ, ك->ک, ي/ى->ی, ة->ە, ل+mark->ڵ, ...).
  2. Normalize Unicode (NFC, unify yeh/heh/kaf, strip stray marks).

Both are done by AsoSoft's well-tested Kurdish library, so we don't reinvent
the linguistic rules. Falls back to a no-op if asosoft isn't installed.
"""
try:
    import asosoft
    _HAVE = True
except ImportError:
    _HAVE = False


def to_unicode_kurdish(text: str) -> str:
    if not _HAVE:
        return text
    # AliK2Unicode fixes the overloaded legacy letters; Normalize cleans Unicode.
    text = asosoft.AliK2Unicode(text)
    try:
        text = asosoft.Normalize(text)
    except Exception:
        pass
    return text


if __name__ == "__main__":
    import sys
    print(to_unicode_kurdish(sys.stdin.read()))
