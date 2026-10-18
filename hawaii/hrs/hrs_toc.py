"""Parse the official HRS Table of Contents into CSVs.

Source: "Hawaii Revised Statutes, Table of Contents (Updated: 2/10/2025)", hrs/source/hrstoc.pdf.

Outputs (in OUTDIR):
  hrs_chapters.csv  division, division_name, title, title_name, subtitle, subtitle_name, chapter, chapter_to,
                    chapter_name, status, first_section, page
  hrs_parts.csv     chapter, kind, article, article_name, part, part_name, status, first_section, page
                    kind: part | article | subpart (lettered "A." under a part) | unnumbered (an indented heading with no number)

status is the TOC's own marker: in_force | repealed | renumbered | reserved.
Usage: python3 hrs_toc.py PDF OUTDIR
"""
import csv
import re
import subprocess
import sys
from pathlib import Path

CHAP_NUM = r"\d{1,3}[A-Z]{0,2}"
CHAPTER = re.compile(rf"^\s{{0,4}}({CHAP_NUM})(?:\s+to\s+({CHAP_NUM}))?\s+(\S.*)$")
PART = re.compile(r"^\s+Part\s+([IVXLC]+[A-Z]?|\d+[A-Z]?)\.\s*(\S.*)$")
ARTICLE = re.compile(r"^\s{0,3}Article\s+([IVXLC]+[A-Z]?|\d+[A-Z]?)\s+(.*)$")
SMALL = {"and", "of", "the", "for", "to", "in", "on", "or", "a", "an", "by", "with"}
WRAP_COL = 48
DIVISION = re.compile(r"^\s*DIVISION\s+(\d+)\.\s+(.+?)\s*$")
TITLE = re.compile(r"^\s*TITLE\s+(\d+[A-Z]?)\s*$")
SUBTITLE = re.compile(r"^\s*Subtitle\s+(\d+)\.\s+(.+?)\s*$")
SECNUM = r"\d+[A-Z]{0,2}(?::\d+[A-Z]{0,2})?-\d+(?:\.\d+)?[A-Z]?"
LEADER = re.compile(rf"(?:\.+\s*|\s+)({SECNUM})\s*$")
LETTERED = re.compile(r"^\s+(?:Subpart\s+)?([A-Z]|\d{1,2})\.\s+(\S.*)$")
HEADER = re.compile(r"^\s*Chapter(?:\s+Section)?\s*$")
FOOTER = re.compile(r"^\s*\d{1,3}\s*$")


def page_lines(pdf):
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout).group(1))
    for p in range(1, n + 1):
        text = subprocess.run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), pdf, "-"],
                              capture_output=True, text=True).stdout
        for line in text.split("\n"):
            yield p, line.rstrip()


def status_of(name):
    low = name.lower()
    if "(repealed)" in low:
        return "repealed"
    if "(renumbered)" in low or "--(renumbered" in low:
        return "renumbered"
    if "reserved for expansion" in low or re.fullmatch(r"\(?reserved\)?\.?", low.strip()):
        return "reserved"
    return "in_force"


def title_case(s):
    words = s.lower().split()
    return " ".join(w if (i and w in SMALL) else w[:1].upper() + w[1:] for i, w in enumerate(words))


def is_open(line):
    """The line's length if its text may continue on the next line, else 0."""
    t = line.rstrip()
    closed = LEADER.search(t) or re.search(r"\((?:Repealed|Renumbered|Reserved)\)$", t, re.I)
    return 0 if closed else len(t)


def name_col(line, name):
    return line.find(name[:12]) if name else -1


def continues(entry, line):
    """A wrapped line either ran to the margin, or is indented one space past where the name starts (hanging indent)."""
    last = entry["_open"]
    if not last or LETTERED.match(line):
        return False
    indent = len(line) - len(line.lstrip())
    reach = 2 if entry["_kind"] == "chapter" else 3   # "Part VIII." pushes its name left of its siblings'
    if not entry["_col"] + 1 <= indent <= entry["_col"] + reach:
        return False
    return bool(LEADER.search(line)) or last >= 34


def clean(name):
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(rf"(?:\.+\s*|\s+){SECNUM}\s*$", "", name).strip()
    name = re.sub(r"\.{2,}.*$", "", name).strip()
    name = re.sub(r"\s*-*\(?(Repealed|Renumbered)\)?\s*$", "", name, flags=re.I).strip(" -")
    if re.search(r"\bEtc$", name):
        return name + "."
    return name.rstrip(".").strip()


def parse(pdf):
    chapters, parts = [], []
    div = div_name = title = title_name = sub = sub_name = None
    chap = art = None
    entry = None            # the entry whose name may continue on the next line
    started = False
    expect_title_name = False

    def finish():
        nonlocal entry
        if entry is None:
            return
        e, entry = entry, None
        raw = e.pop("_raw")
        e.pop("_open", None)
        e.pop("_col", None)
        m = LEADER.search(raw)
        e["first_section"] = m.group(1) if m else ""
        e["status"] = status_of(raw)
        name = clean(raw)
        if e.get("kind") == "unnumbered":
            sm = re.match(r"^([A-Z]|\d{1,2})\.\s+(.*)$", name)
            if sm:
                e["kind"], e["part"], name = "subpart", sm.group(1), sm.group(2)
        if e["_kind"] == "chapter":
            e["chapter_name"] = name
            chapters.append(e)
        else:
            e["part_name" if e["_kind"] == "part" else "article_name"] = name
            parts.append(e)
        e.pop("_kind")

    in_appendix = subtitle_open = False
    for page, line in page_lines(pdf):
        if not started:
            if DIVISION.match(line):
                started = True
            else:
                continue
        if not line.strip() or FOOTER.match(line):
            continue
        if line.strip() == "Appendix":
            finish()
            in_appendix = True
            continue
        if HEADER.match(line):
            finish()
            expect_title_name = subtitle_open = False
            continue
        m = DIVISION.match(line)
        if m:
            finish()
            in_appendix = False
            div, div_name = m.group(1), title_case(m.group(2))
            continue
        m = TITLE.match(line)
        if m:
            finish()
            in_appendix = False
            title, title_name, sub, sub_name, chap, art = m.group(1), None, None, None, None, None
            expect_title_name = True
            continue
        if in_appendix:
            continue
        m = SUBTITLE.match(line)
        if m:
            finish()
            expect_title_name = False
            sub, sub_name = m.group(1), m.group(2)
            subtitle_open = True
            continue
        if subtitle_open and not CHAPTER.match(line):
            sub_name = f"{sub_name} {line.strip()}"     # a centered subtitle heading that wraps
            continue
        subtitle_open = False
        if expect_title_name and line.strip().isupper():
            title_name = line.strip() if not title_name else f"{title_name} {line.strip()}"
            continue
        if entry is not None and continues(entry, line) and not PART.match(line) and not ARTICLE.match(line) \
                and not CHAPTER.match(line):
            entry["_raw"] += " " + line.strip()
            entry["_open"] = is_open(line)
            continue
        m = ARTICLE.match(line)
        if m and chap:
            finish()
            art = m.group(1)
            entry = {"_kind": "article", "_raw": m.group(2), "_open": is_open(line), "_col": name_col(line, m.group(2)), "chapter": chap, "article": art,
                     "article_name": "", "part": "", "part_name": "", "kind": "article", "page": page}
            continue
        m = PART.match(line)
        if m and chap:
            finish()
            entry = {"_kind": "part", "_raw": m.group(2), "_open": is_open(line), "_col": name_col(line, m.group(2)), "chapter": chap, "article": art or "",
                     "article_name": "", "part": m.group(1), "part_name": "", "kind": "part", "page": page}
            continue
        m = CHAPTER.match(line)
        if m and title:
            finish()
            chap, art = m.group(1), None
            entry = {"_kind": "chapter", "_raw": m.group(3), "_open": is_open(line), "_col": name_col(line, m.group(3)), "division": div,
                     "division_name": div_name, "title": title,
                     "title_name": title_case(title_name) if title_name else "", "subtitle": sub or "",
                     "subtitle_name": sub_name or "", "chapter": chap, "chapter_to": m.group(2) or "", "page": page}
            continue
        m = LETTERED.match(line)
        if m and chap:
            finish()
            entry = {"_kind": "part", "_raw": m.group(2), "_open": is_open(line), "_col": name_col(line, m.group(2)),
                     "chapter": chap, "article": art or "", "article_name": "", "part": m.group(1), "part_name": "",
                     "kind": "subpart", "page": page}
            continue
        if chap and line.strip().isupper() and not re.search(r"\d", line):
            finish()
            continue            # e.g. "REFERENCE TABLE": a caption, not part of the outline
        if chap and line.startswith(" "):
            # an indented heading without a Part number (e.g. "Preamble", or ch. 231's unnumbered groups)
            finish()
            entry = {"_kind": "part", "_raw": line.strip(), "_open": is_open(line), "_col": name_col(line, line.strip()), "chapter": chap, "article": art or "",
                     "article_name": "", "part": "", "part_name": "", "kind": "unnumbered", "page": page}
            continue
    finish()
    # article rows carry their own name into their parts
    names = {}
    for p in parts:
        if p["article"] and not p["part"]:
            names[(p["chapter"], p["article"])] = p["article_name"]
    for p in parts:
        if p["article"] and p["part"]:
            p["article_name"] = names.get((p["chapter"], p["article"]), p["article_name"])
    return chapters, parts


def main():
    pdf, out = sys.argv[1], Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    chapters, parts = parse(pdf)
    ccols = ["division", "division_name", "title", "title_name", "subtitle", "subtitle_name", "chapter", "chapter_to",
             "chapter_name", "status", "first_section", "page"]
    pcols = ["chapter", "kind", "article", "article_name", "part", "part_name", "status", "first_section", "page"]
    with open(out / "hrs_chapters.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ccols)
        w.writeheader()
        w.writerows({k: c.get(k, "") for k in ccols} for c in chapters)
    with open(out / "hrs_parts.csv", "w", newline="") as f:
        w = csv.DictWriter(f, pcols)
        w.writeheader()
        w.writerows({k: p.get(k, "") for k in pcols} for p in parts)
    titles = {c["title"] for c in chapters}
    print(f"{len(chapters)} chapters in {len(titles)} titles, {len(parts)} parts/articles")


if __name__ == "__main__":
    main()
