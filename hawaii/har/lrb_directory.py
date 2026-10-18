"""Parse the LRB's Hawaii Administrative Rules publication into CSVs.

Source: Legislative Reference Bureau, "Hawaii Administrative Rules: 2025 Table of
Statutory Sections Implemented and Directory" (July 2026),
https://lrb.hawaii.gov/wp-content/uploads/2025AdminRules_Supplement.pdf

Outputs:
  har_chapters.csv     title, listed_under, title_name, subtitle, subtitle_name, chapter, chapter_name, repealed
  hrs_to_har.csv       hrs_section, har_section, repealed_hrs   (HRS section -> rule section that implements it)

Usage: python3 lrb_directory.py PDF OUTDIR
"""
import csv
import re
import sys
from pathlib import Path

import pdfplumber

HAR_PREFIX = re.compile(r"^(\d+)-(\d+(?:\.\d+)?)-([\w.]+),?$")
NUM = re.compile(r"^[\w.]+,?$")


def lines_by_column(page, splits):
    """Group words into (column_index, top, [words]) lines; splits are x boundaries."""
    out = {}
    for w in page.extract_words(keep_blank_chars=False, use_text_flow=False):
        col = sum(1 for s in splits if w["x0"] >= s)
        key = (col, round(w["top"] / 2))
        out.setdefault(key, []).append(w)
    return [(k[0], k[1], sorted(v, key=lambda w: w["x0"])) for k, v in sorted(out.items())]


def expand_refs(tokens):
    """'3-177-53, 55 to 57, 150' -> ['3-177-53','3-177-55','3-177-56','3-177-57','3-177-150']."""
    out, prefix, prev, i = [], None, None, 0
    toks = [t.rstrip(",") for t in tokens if t not in (",",)]
    while i < len(toks):
        t = toks[i]
        m = HAR_PREFIX.match(t)
        if m:
            prefix = f"{m.group(1)}-{m.group(2)}"
            prev = m.group(3)
            out.append(f"{prefix}-{prev}")
        elif t == "to" and prefix and prev and i + 1 < len(toks):
            hi = toks[i + 1]
            try:
                a, b = float(prev), float(hi)
                if a.is_integer() and b.is_integer() and 0 < b - a < 500:
                    out.extend(f"{prefix}-{n}" for n in range(int(a) + 1, int(b) + 1))
                else:
                    out.append(f"{prefix}-{hi}")
            except ValueError:
                out.append(f"{prefix}-{hi}")
            prev = hi
            i += 1
        elif prefix and NUM.match(t) and re.match(r"^\d", t):
            prev = t
            out.append(f"{prefix}-{t}")
        i += 1
    return out


def parse_table(pdf):
    rows = []
    for page in pdf.pages:
        text = page.extract_text() or ""
        if "HRS Section" not in text or "Administrative Rules" not in text:
            continue
        words = page.extract_words()
        hrs_x = sorted({round(w["x0"]) for w in words if w["text"] == "HRS"})
        adm_x = sorted({round(w["x0"]) for w in words if w["text"] == "Administrative"})
        if not hrs_x or not adm_x:
            continue
        adm_x = [min((a for a in adm_x if a > h), default=h + 80) for h in hrs_x]
        splits = [x - 3 for x in hrs_x[1:]]
        cur = None
        last_col = None
        for col, top, ws in lines_by_column(page, splits):
            if col != last_col:
                cur = None
                last_col = col
            ws = [w for w in ws if w["text"] not in ("HRS", "Section", "Administrative", "Rules", "Sections")]
            if not ws:
                continue
            first = ws[0]
            if abs(first["x0"] - hrs_x[col]) < 4 and first["x0"] < adm_x[col] - 4:
                key_words = [w["text"] for w in ws if w["x0"] < adm_x[col] - 4]
                rest = [w["text"] for w in ws if w["x0"] >= adm_x[col] - 4]
                key = " ".join(key_words)
                repealed = "[R]" in key
                key = key.replace("[R]", "").strip()
                if not re.match(r"^(C\s+)?\d", key):
                    cur = None
                    continue
                cur = {"hrs": key, "repealed": repealed, "refs": rest}
                rows.append(cur)
            elif cur is not None:
                cur["refs"].extend(w["text"] for w in ws)
    out = []
    for r in rows:
        for har in expand_refs(r["refs"]):
            out.append((r["hrs"], har, int(r["repealed"])))
    return out


TITLE_HDR = re.compile(r"^TITLE (\d+)$")


def parse_directory(pdf):
    start = None
    for i, page in enumerate(pdf.pages):
        t = page.extract_text() or ""
        if "HAWAII ADMINISTRATIVE RULES" in t and "DIRECTORY" in t and "TITLE 1" in t:
            start = i
            break
    chapters = []
    title = title_name = sub = sub_name = None
    expect_title_name = False
    for page in pdf.pages[start:]:
        mid = page.width / 2
        for col in (0, 1):
            crop = page.crop((0 if col == 0 else mid, 0, mid if col == 0 else page.width, page.height - 60))
            lines = [l.strip() for l in (crop.extract_text() or "").split("\n")]
            pending = None
            for ln in lines:
                if not ln or ln in ("HAWAII ADMINISTRATIVE RULES", "DIRECTORY", "Chapter") or re.fullmatch(r"\d{3}", ln) or ln.startswith("http"):
                    continue
                m = TITLE_HDR.match(ln) or re.match(r"^TITLE (\d+):\s*(.+)$", ln)
                if m:
                    if m.group(1) != title:
                        title, sub, sub_name = m.group(1), None, None
                        title_name = m.group(2).strip() if m.lastindex and m.lastindex > 1 else None
                        expect_title_name = title_name is None
                    pending = None
                    continue
                if expect_title_name and ln.isupper():
                    title_name = ln if not title_name else f"{title_name} {ln}"
                    continue
                expect_title_name = False
                ms = re.match(r"^Subtitle (\d+)\s*(.*)$", ln)
                if ms:
                    sub, sub_name = ms.group(1), ms.group(2).strip() or None
                    pending = None
                    continue
                mt = re.match(r"^(\d+)-(\d+(?:\.\d+)?[A-H]?)(?=\s|$)(.*)$", ln)
                own_title = title
                if mt and title:
                    own_title = mt.group(1)
                    ln = f"{mt.group(2)}{mt.group(3)}"
                mc = re.match(r"^(\d{1,4}(?:\.\d+)?)([A-H])?(?=\s|$)(?: to (\d+(?:\.\d+)?))?\s*(.*)$", ln)
                if mc and title:
                    pending = {
                        "title": own_title, "listed_under": title, "title_name": title_name, "subtitle": sub, "subtitle_name": sub_name,
                        "chapter": mc.group(1) + (mc.group(2) or ""), "chapter_to": mc.group(3), "chapter_name": mc.group(4).strip(),
                    }
                    chapters.append(pending)
                    continue
                if pending is not None and not pending["chapter_name"].startswith("Repealed"):
                    pending["chapter_name"] = (pending["chapter_name"] + " " + ln).strip()
                elif pending is not None:
                    pass
                elif sub and not sub_name:
                    sub_name = ln
                elif sub and sub_name and chapters and chapters[-1]["subtitle"] == sub:
                    pass
                elif sub:
                    sub_name = f"{sub_name} {ln}"
    chapters = [c for c in chapters if c["title"].isdigit() and 1 <= int(c["title"]) <= 30]
    for c in chapters:
        c["repealed"] = "1" if c["chapter_name"].lower().startswith("repealed") else ("" if not c["chapter_name"] else "0")
    return chapters


def main():
    pdf_path, outdir = sys.argv[1], Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)
    with pdfplumber.open(pdf_path) as pdf:
        chapters = parse_directory(pdf)
        table = parse_table(pdf)
    with open(outdir / "har_chapters.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["title", "listed_under", "title_name", "subtitle", "subtitle_name", "chapter", "chapter_to", "chapter_name", "repealed"])
        for c in chapters:
            w.writerow([c["title"], c["listed_under"], c["title_name"], c["subtitle"], c["subtitle_name"], c["chapter"], c["chapter_to"], c["chapter_name"], c["repealed"]])
    with open(outdir / "hrs_to_har.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["hrs_section", "har_section", "hrs_repealed"])
        w.writerows(table)
    print(f"{len(chapters)} chapters, {len(table)} HRS->HAR links")


if __name__ == "__main__":
    main()
