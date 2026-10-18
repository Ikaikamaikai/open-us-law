"""Fetch HRS sections that the Table of Contents or the 2025 Table of Disposition name but this copy lacks.

Run this on your own computer (capitol.hawaii.gov blocks most cloud servers). For each section it tries the
Legislature's page first, then the Internet Archive's copy of that page. Every section keeps the URL it came from.

  python3 hrs/fill_missing.py                 # the sections listed by hrs/check.py
  python3 hrs/fill_missing.py 92F-11 26-1     # just these
  python3 hrs/fill_missing.py --dry-run       # print the URLs it would fetch

Output: data/law/hrs_fill.jsonl (build.py loads it; sections already present are never replaced).
"""
import csv
import html
import json
import re
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE.parent / "data"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0 Safari/537.36"}
BASE = "https://www.capitol.hawaii.gov/hrscurrent"
NUM = re.compile(r"^(\d+)([A-Z]*)(?::(\d+)([A-Z]*))?-(\d+)(?:\.(\d+))?([A-Z]*)$")
NOTES = ("attorney general opinions", "law journals and reviews", "case notes", "rules of court", "cross references",
         "revision note", "compiler's note", "hawaii administrative rules", "note", "notes", "effect of amendments")


def filename(num):
    """'412:2-100.5' -> 'HRS_0412-0002-0100_0005.htm' (the Legislature's own naming)."""
    m = NUM.match(num.upper())
    if not m:
        return None
    chap = f"{int(m.group(1)):04d}{m.group(2)}"
    parts = [f"{int(m.group(3)):04d}{m.group(4)}"] if m.group(3) else []
    sec = f"{int(m.group(5)):04d}{m.group(7)}"
    dec = "".join(f"_{int(d):04d}" for d in (m.group(6) or ""))
    return f"HRS_{chap}-" + "-".join(parts + [sec]) + dec + ".htm"


def volume_folders(con):
    """chapter -> 'VolNN_ChXXXX-YYYY' from URLs already in the database, plus the volume ranges."""
    by_chapter, ranges = {}, set()
    for chap, url in con.execute("select chapter, source_url from section where corpus='hrs'"):
        m = re.search(r"/hrscurrent/(Vol\d+_Ch(\d+)([A-Z]*)-(\d+)([A-Z]*))/", url or "")
        if m:
            by_chapter.setdefault(chap, m.group(1))
            ranges.add((m.group(1), (int(m.group(2)), m.group(3)), (int(m.group(4)), m.group(5))))
    return by_chapter, sorted(ranges)


def chapter_key(chap):
    m = re.match(r"^(\d+)([A-Z]*)$", chap)
    return (int(m.group(1)), m.group(2)) if m else (0, "")


def url_for(num, by_chapter, ranges):
    chap = num.split("-")[0].split(":")[0]
    vol = by_chapter.get(chap)
    if not vol:
        k = chapter_key(chap)
        vol = next((v for v, lo, hi in ranges if lo <= k <= hi), None)
    fn = filename(num)
    if not vol or not fn:
        return None
    return f"{BASE}/{vol}/HRS{fn[4:fn.index('-')]}/{fn}"


class Paras(HTMLParser):
    def __init__(self):
        super().__init__()
        self.out, self.buf, self.inp = [], [], False

    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.inp, self.buf = True, []
        elif tag == "br" and self.inp:
            self.buf.append(" ")

    def handle_endtag(self, tag):
        if tag == "p" and self.inp:
            self.out.append(re.sub(r"\s+", " ", "".join(self.buf).replace("\xa0", " ")).strip())
            self.inp = False

    def handle_data(self, data):
        if self.inp:
            self.buf.append(data)


def parse_page(raw, num):
    p = Paras()
    p.feed(raw)
    paras = [x for x in p.out if x]
    start = next((i for i, x in enumerate(paras) if re.match(r"^\[?\s*§+\s*\d", x)), None)
    if start is None:
        return None
    first = paras[start]
    if num.upper() not in re.sub(r"\s+", "", first).upper():
        return None
    headings = paras[:start]
    body_first = re.sub(r"^\[?\s*§+\s*[\w:.\-]+\]?\s*", "", first)
    hm = re.match(r"^(.{1,200}?\.)\s+(.*)$", body_first)
    heading, lead = (hm.group(1), hm.group(2)) if hm else (body_first[:200], "")
    lines, history = [lead] if lead else [], None
    for x in paras[start + 1:]:
        low = x.lower().rstrip(":. ")
        if any(low == n or low.startswith(n + " ") for n in NOTES):
            break
        if re.match(r"^\[(?:Am\s+)?L\s*(?:Sp\s*)?\d{4}", x) or re.match(r"^\[L ", x):
            history = x
            break
        lines.append(x)
    text = "\n\n".join(lines)
    if history:
        text += "\n\n" + history
    status = "repealed" if re.search(r"\b(repealed|reserved)\b", heading.lower()) and len(text) < 200 else "in_force"
    return {"heading": heading, "text": text, "headings_above": headings, "status": status}


def fetch(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
            body = r.read().decode("windows-1252", "replace")
            if "Attention Required" in body and "Cloudflare" in body:
                return None
            return body
    except Exception:
        return None


def wayback(url):
    api = "https://archive.org/wayback/available?url=" + urllib.parse.quote(url.split("://", 1)[1], safe="")
    try:
        with urllib.request.urlopen(urllib.request.Request(api, headers=UA), timeout=60) as r:
            snap = json.load(r).get("archived_snapshots", {}).get("closest")
    except Exception:
        return None, None
    if not snap or not snap.get("available"):
        return None, None
    raw_url = re.sub(r"/web/(\d+)/", r"/web/\1id_/", snap["url"]).replace("http://", "https://", 1)
    return fetch(raw_url), snap["url"]


def targets_from_checks():
    out = []
    for name, col in (("opening_sections_not_present", "first_section"), ("slh2025_targets_not_present", "target")):
        path = HERE / "checks" / f"{name}.csv"
        if path.exists():
            out += [r[col] for r in csv.DictReader(open(path)) if r[col]]
    return list(dict.fromkeys(out))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry-run" in sys.argv
    con = sqlite3.connect(DATA / "hawaii.db")
    by_chapter, ranges = volume_folders(con)
    wanted = args or targets_from_checks()
    out_path = DATA / "law" / "hrs_fill.jsonl"
    done = set()
    if out_path.exists():
        done = {json.loads(l)["number"] for l in open(out_path)}
    todo = [n for n in wanted if n not in done]
    print(f"{len(wanted)} sections wanted, {len(done)} already fetched, {len(todo)} to go")
    got = 0
    with open(out_path, "a") as f:
        for i, num in enumerate(todo, 1):
            url = url_for(num, by_chapter, ranges)
            if dry:
                print(num, url)
                continue
            if not url:
                print(f"  {num}: no URL")
                continue
            raw, src = fetch(url), url
            if raw is None:
                raw, src = wayback(url)
            rec = parse_page(raw, num) if raw else None
            if not rec:
                print(f"  {num}: not found ({url})")
                continue
            rec.update(number=num, citation=f"Haw. Rev. Stat. § {num}", source_url=url, fetched_from=src,
                       fetched=time.strftime("%Y-%m-%d"))
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            got += 1
            if i % 25 == 0:
                print(f"  {i}/{len(todo)}  ({got} fetched)")
            time.sleep(0.5)
    if not dry:
        print(f"fetched {got}; saved to {out_path}. Run build.py to include them.")


if __name__ == "__main__":
    main()
