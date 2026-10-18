"""Citation keys: one normalized form for every way a citation gets written."""
import re

HRS_NUM = r"\d+[A-Z]?(?::\d+[A-Z]?)?-[\d.]*\d[A-Z]?"
HAR_NUM = r"\d{1,2}-\d+(?:\.\d+)?[A-Z]?-[\d.]*\d[A-Z]?"

ROMAN = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100}


def to_roman(n):
    out = ""
    for v, s in ((50, "l"), (40, "xl"), (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")):
        while n >= v:
            out += s
            n -= v
    return out


# Short names people actually type -> the published citation prefix.
ALIASES = [
    (r"\bh\.?\s*r\.?\s*s\.?(?=\s|§|\d|$)", "haw rev stat"),
    (r"\bhaw(?:ai['ʻ]?i)?\.?\s+rev(?:ised)?\.?\s+stat(?:utes|s)?\.?", "haw rev stat"),
    (r"\bh\.?\s*a\.?\s*r\.?(?=\s|§|\d|$)", "har"),
    (r"\bhaw(?:ai['ʻ]?i)?\.?\s+admin(?:istrative)?\.?\s+r(?:ules?)?\.?", "har"),
    (r"\bhrcp\b", "haw r civ p"),
    (r"\bhrpp\b", "haw r penal p"),
    (r"\bhrap\b", "haw r app p"),
    (r"\bhfcr\b", "haw fam ct r"),
    (r"\brcch\b", "haw r cir ct"),
    (r"\bdcrcp\b", "haw dist ct r civ p"),
    (r"\bhrpc\b", "haw r prof conduct"),
    (r"\brsch\b", "haw r sup ct"),
    (r"\bfrcp\b", "fed r civ p"),
    (r"\bfrcrp\b", "fed r crim p"),
    (r"\bfrap\b", "fed r app p"),
    (r"\bfre\b", "fed r evid"),
    (r"\bfrbp\b", "fed r bankr p"),
    (r"\bu\.?\s*s\.?\s*c\.?\s*a?\.?(?=\s|§|$)", "usc"),
    (r"\bc\.?\s*f\.?\s*r\.?(?=\s|§|$)", "cfr"),
    (r"\b(?:haw(?:ai['ʻ]?i)?|hi)\.?\s+const(?:itution)?\.?", "haw const"),
    (r"\b(?:u\.?\s*s\.?|us|united states|federal)\s+const(?:itution)?\.?", "us const"),
    (r"\bhaw\.?\s+op\.?\s+att'?y\s+gen\.?(?:\s+no\.?)?", "ag op"),
    (r"\b(?:ag|attorney general)\s+op(?:inion)?s?\.?(?:\s+no\.?)?", "ag op"),
]


def norm(s):
    """Normalize a published citation into its lookup key."""
    s = s.lower().replace("’", "'").replace("ʻ", "'")
    s = re.sub(r"\(\d{4}\)\s*$", "", s)
    s = s.replace("§", " ").replace("¶", " ")
    s = re.sub(r"\bno\.\s*", " ", s)
    s = re.sub(r"\barticle\b", "art", s)
    s = re.sub(r"\bamendment\b", "amend", s)
    s = re.sub(r"\bsec(?:tion)?\b\.?", " ", s)
    s = re.sub(r"(?<=[a-z])\.(?=\s|$)", " ", s)
    s = re.sub(r"(?<=[a-z])\.(?=[a-z])", "", s)
    s = re.sub(r"[,;]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"^(\d+) u s c ", r"\1 usc ", s)
    s = re.sub(r"^(\d+) c f r ", r"\1 cfr ", s)
    s = re.sub(r"^u s const ", "us const ", s)
    s = re.sub(r"\bart ([ivxl]+) (\d+)", r"art \1 \2", s)
    return s


def _roman_fix(s):
    """art 6 -> art vi, amend 14 -> amend xiv."""
    return re.sub(r"\b(art|amend) (\d+)\b", lambda m: f"{m.group(1)} {to_roman(int(m.group(2)))}", s)


def keys_for_query(q):
    """Candidate cite keys for what a person typed. Empty if it does not look like a citation."""
    raw = q.strip()
    s = raw.lower().replace("’", "'").replace("ʻ", "'")
    for pat, rep in ALIASES:
        s = re.sub(pat, rep + " ", s, flags=re.I)
    s = re.sub(r"\b(\d+)\s+usc\b", r"\1 usc", s)
    s = re.sub(r"\b(\d+)\s+cfr\b", r"\1 cfr", s)
    s = norm(s)
    s = _roman_fix(s)
    keys = []
    m = re.fullmatch(rf"({HAR_NUM})", s, re.I)
    if m:
        keys.append(f"har {m.group(1)}")
    m = re.fullmatch(rf"({HRS_NUM})", s, re.I)
    if m:
        keys.append(f"haw rev stat {m.group(1)}")
    m = re.fullmatch(r"(?:chapter|ch) (\d+[a-z]?)", s)
    if m:
        keys.append(f"chapter {m.group(1)}")
    m = re.fullmatch(r"(\d+) (usc|cfr) (.+)", s)
    if m:
        keys.append(f"{m.group(1)} {m.group(2)} {m.group(3)}")
    m = re.fullmatch(r"(haw const|us const) (?:art )?([ivxl]+) (\d+)", s)
    if m:
        keys.append(f"{m.group(1)} art {m.group(2)} {m.group(3)}")
    m = re.fullmatch(r"us const amend ([ivxl]+)", s)
    if m:
        keys.append(f"us const amend {m.group(1)}")
    m = re.fullmatch(r"ag op (\d{2}-\d+)", s)
    if m:
        keys.append(f"haw op att'y gen {m.group(1)}")
    if re.match(r"^(haw|har|fed|sup ct|haw const|us const)\b", s) and re.search(r"\d", s):
        keys.append(s)
    return [k.lower() for k in dict.fromkeys(keys)]


# ---- references inside text -------------------------------------------------------
ANY_NUM = rf"(?:{HAR_NUM}|{HRS_NUM})"
TXT_HRS_SECTIONS = re.compile(rf"\bsections?\s+({ANY_NUM}(?:(?:,\s*|,?\s+(?:and|or|to|through)\s+){ANY_NUM})*)", re.I)
TXT_HRS_CHAPTER = re.compile(r"\bchapters?\s+(\d+[A-Z]?)\b(?!\s*,?\s*(?:of\s+)?title)")
TXT_USC = re.compile(r"\b(\d{1,2})\s+U\.?\s?S\.?\s?C\.?(?:A\.?)?\s*(?:§+|sec(?:tion)?\.?)?\s*([\dA-Za-z]+(?:[-–.][\dA-Za-z]+)*)")
TXT_CFR = re.compile(r"\b(\d{1,2})\s+C\.?\s?F\.?\s?R\.?\s*(?:§+|part|sec(?:tion)?\.?)?\s*(\d+(?:\.\d+[a-z]?)?)", re.I)
TXT_HAR = re.compile(rf"\b(?:section|§)\s*({HAR_NUM})\b")


def refs_in_text(text, own_corpus):
    """Yield (to_key, kind) for every citation written in a section's text."""
    if not text:
        return
    t = re.sub(r"\s+", " ", text)
    for m in TXT_HRS_SECTIONS.finditer(t):
        for num in re.findall(ANY_NUM, m.group(1)):
            if re.fullmatch(HAR_NUM, num):
                yield f"har {num.lower()}", "cites"
            elif own_corpus in ("hrs", "hi-const", "hi-rules", "hi-ag", "hi-guidance", "har"):
                yield f"haw rev stat {num.lower()}", "cites"
    for m in TXT_HAR.finditer(t):
        yield f"har {m.group(1).lower()}", "cites"
    if own_corpus in ("hrs", "har", "hi-ag", "hi-guidance", "hi-rules"):
        for m in TXT_HRS_CHAPTER.finditer(t):
            yield f"chapter {m.group(1).lower()}", "chapter"
    for m in TXT_USC.finditer(t):
        yield f"{m.group(1)} usc {m.group(2).lower().replace('–', '-')}", "cites"
    for m in TXT_CFR.finditer(t):
        yield f"{m.group(1)} cfr {m.group(2).lower()}", "cites"


HRS_IN_NOTE = re.compile(HRS_NUM)


def hrs_in_note(note):
    """'HRS §§431:2-201, 431:10A-304' -> ['431:2-201', '431:10a-304'] (HRS numbers only)."""
    if not note or "HRS" not in note.upper():
        return []
    part = note.split("HRS", 1)[1]
    part = re.split(r"\b(?:U\.?S\.?C|C\.?F\.?R|SLH|Pub\.? ?L)\b", part)[0]
    return [n.lower() for n in HRS_IN_NOTE.findall(part)]
