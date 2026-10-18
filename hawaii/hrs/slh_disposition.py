"""Parse the HRS Table of Disposition (Table 2: Session Laws to Hawaii Revised Statutes) into a CSV.

Source: hrs/source/tablesofdisposition_2025.pdf ("TABLE OF DISPOSITION", Session Laws of 2025).

Output: slh_disposition.csv with one row per HRS target:
  year, act, act_section, kind, target, chapter, repealed, heading_only, omitted, raw, page
    kind      section | chapter | part | subpart | article | omitted
    target    "803-6", "c 663J", "c 92 pt VII", "c 431 art 33"
    repealed  1 when the table marks the target (R)
    raw       the table's own text for the whole entry, so nothing is lost when a line is ambiguous
Usage: python3 slh_disposition.py PDF OUTDIR
"""
import csv
import re
import sys
from pathlib import Path

import pdfplumber

SEC = re.compile(r"^(\d+[A-Z]{0,2}(?::\d+[A-Z]?)?)-([\d.]+[A-Z]?)$")


def rows_from_pdf(pdf_path):
    """Yield (page, side, act, section_text, hrs_text, hrs_is_continuation) in reading order."""
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            words = page.extract_words()
            hdr = [w for w in words if w["text"] in ("Act", "Section", "HRS") and w["top"] < 200]
            acts = sorted(w["x0"] for w in hdr if w["text"] == "Act")
            secs = sorted(w["x0"] for w in hdr if w["text"] == "Section")
            hrss = sorted(w["x0"] for w in hdr if w["text"] == "HRS")
            if len(acts) < 2 or len(secs) < 2 or len(hrss) < 2:
                continue
            header_top = max(w["top"] for w in hdr)
            lines = {}
            for w in words:
                if w["top"] <= header_top + 2 or w["top"] > page.height - 50:
                    continue
                lines.setdefault(round(w["top"] / 3), []).append(w)
            keys = sorted(lines)
            if keys and len(lines[keys[-1]]) == 1 and lines[keys[-1]][0]["text"].isdigit():
                keys = keys[:-1]
            for key in keys:
                ws = sorted(lines[key], key=lambda w: w["x0"])
                text = " ".join(w["text"] for w in ws)
                if "SESSION LAWS OF" in text:
                    yield pno, None, "YEAR", re.search(r"(\d{4})", text).group(1), "", False
                    continue
                for side in (0, 1):
                    lo = acts[side] - 6
                    hi = acts[1] - 6 if side == 0 else page.width
                    sw = [w for w in ws if lo <= w["x0"] < hi]
                    if not sw:
                        continue
                    act = " ".join(w["text"] for w in sw if w["x0"] < secs[side] - 6)
                    sec = " ".join(w["text"] for w in sw if secs[side] - 6 <= w["x0"] < hrss[side] - 6)
                    hrs_w = [w for w in sw if w["x0"] >= hrss[side] - 6]
                    hrs = " ".join(w["text"] for w in hrs_w)
                    cont = bool(hrs_w) and not act and not sec and hrs_w[0]["x0"] > hrss[side] + 5
                    yield pno, side, act, sec, hrs, cont


def expand_numbers(text):
    """'1, 2' -> ['1','2']; '17 to 21' -> ['17',...,'21']."""
    out = []
    for part in re.split(r",\s*", text.strip()):
        m = re.fullmatch(r"(\d+)\s+to\s+(\d+)", part.strip())
        if m:
            out.extend(str(n) for n in range(int(m.group(1)), int(m.group(2)) + 1))
        elif part.strip():
            out.append(part.strip())
    return out


def expand_targets(raw):
    """HRS column text -> list of dicts (kind, target, chapter, repealed, heading_only).
    A "(R)" or "(heading)" marker applies to everything its comma-separated token names."""
    raw = re.sub(r"\s+", " ", raw).strip()
    raw = re.sub(r"([\dA-Z])- (\d)", r"\1-\2", raw)
    raw = re.sub(r"\bto(\d)", r"to \1", raw)
    if raw == "O":
        return [{"kind": "omitted", "target": "O", "chapter": "", "repealed": 0, "heading_only": 0}]
    items, chapter, part = [], None, None
    for tok in (t.strip() for t in re.split(r"[,;]\s*", raw) if t.strip()):
        rep, head = int("(R)" in tok), int("(heading)" in tok)
        t = tok.replace("(R)", "").replace("(heading)", "").strip()
        new = []
        m = re.fullmatch(r"c (\d+[A-Z]{0,2})(?: pt ([IVXLC]+[A-Z]?))?", t)
        if t == "O":
            new.append({"kind": "omitted", "target": "O"})
        elif m:
            chapter, part = m.group(1), m.group(2)
            new.append({"kind": "part", "target": f"c {chapter} pt {part}"} if part
                       else {"kind": "chapter", "target": f"c {chapter}"})
        elif re.fullmatch(r"pt [IVXLC]+[A-Z]?", t) and chapter:
            part = t.split()[1]
            if items and items[-1]["kind"] == "chapter" and items[-1]["target"] == f"c {chapter.split(':')[0]}":
                items.pop()
            new.append({"kind": "part", "target": f"c {chapter.split(':')[0]} pt {part}"})
        elif re.fullmatch(r"subpt [A-Z]", t) and chapter:
            if items and items[-1]["kind"] == "part" and items[-1]["target"].endswith(f"pt {part}") and not items[-1].get("_sub"):
                items.pop()
            new.append({"kind": "subpart", "target": f"c {chapter.split(':')[0]} pt {part} {t}", "_sub": True})
        elif re.fullmatch(r"Art\. \d+[A-Z]?", t) and chapter:
            new.append({"kind": "article", "target": f"c {chapter.split(':')[0]} art {t.split()[1]}"})
        else:
            rng = re.fullmatch(r"(\S+?)(?: to (\S+))?", t)
            first, last = (rng.group(1), rng.group(2)) if rng else (t, None)
            sm = SEC.match(first)
            if sm:
                chapter, first = sm.group(1), sm.group(2)
            if chapter and re.fullmatch(r"[\d.]+[A-Z]?", first) and (last is None or re.fullmatch(r"[\d.]+[A-Z]?", last)):
                nums = [first]
                if last:
                    if first.isdigit() and last.isdigit() and 0 < int(last) - int(first) < 400:
                        nums = [str(n) for n in range(int(first), int(last) + 1)]
                    else:
                        nums = [first, last]
                new.extend({"kind": "section", "target": f"{chapter}-{n}"} for n in nums)
            else:
                new.append({"kind": "unparsed", "target": t})
        for it in new:
            it.update(chapter=chapter or "", repealed=rep, heading_only=head)
        items.extend(new)
    for it in items:
        it.pop("_sub", None)
    return items


def parse(pdf_path):
    """Read each page's left column top to bottom, then its right column: the table's own reading order."""
    raw_rows = list(rows_from_pdf(pdf_path))
    year = next((r[3] for r in raw_rows if r[2] == "YEAR"), None)
    ordered = sorted((r for r in raw_rows if r[2] != "YEAR"), key=lambda r: (r[0], r[1]))  # stable: keeps line order
    entries, act_now, current = [], None, None
    for page, side, act, sec, hrs, _cont in ordered:
        if act:
            act_now = act
        if not act and not sec:
            if hrs and current is not None:
                current["raw"] += " " + hrs
            continue
        current = {"year": year, "act": act_now, "act_section": sec, "raw": hrs, "page": page}
        entries.append(current)
    out = []
    for e in entries:
        targets = expand_targets(e["raw"])
        secs = expand_numbers(e["act_section"]) if e["act_section"] else []
        pairs = list(zip(secs, targets)) if secs and len(secs) == len(targets) else [(e["act_section"], t) for t in targets]
        for s_, t in pairs:
            out.append({"year": e["year"], "act": e["act"], "act_section": s_, "kind": t["kind"], "target": t["target"],
                        "chapter": t["chapter"], "repealed": t["repealed"], "heading_only": t["heading_only"],
                        "omitted": int(t["kind"] == "omitted"), "raw": re.sub(r"\s+", " ", e["raw"]), "page": e["page"]})
    return out


def main():
    pdf, outdir = sys.argv[1], Path(sys.argv[2])
    rows = parse(pdf)
    cols = ["year", "act", "act_section", "kind", "target", "chapter", "repealed", "heading_only", "omitted", "raw", "page"]
    with open(outdir / "slh_disposition.csv", "w", newline="") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        w.writerows(rows)
    acts = {r["act"] for r in rows}
    print(f"{len(rows)} rows, {len(acts)} acts, {sum(r['kind'] == 'section' for r in rows)} section targets, "
          f"{sum(r['kind'] == 'unparsed' for r in rows)} unparsed")


if __name__ == "__main__":
    main()
