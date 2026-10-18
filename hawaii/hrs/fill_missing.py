"""Fetch HRS sections that the official Legislature server has but this copy lacks.

The Legislature publishes the HRS on two hosts with the same files: www.capitol.hawaii.gov (which blocks many
cloud servers) and its data server, data.capitol.hawaii.gov, whose folders can be listed. With --all this lists
every chapter folder on the data server, compares every section file with the database, and fetches the ones
that are not here. Every section keeps the www.capitol.hawaii.gov URL of the page it came from.

  python3 hrs/fill_missing.py --all           # every section on the Legislature's server that is not here
  python3 hrs/fill_missing.py                 # just the sections listed by hrs/check.py
  python3 hrs/fill_missing.py 92F-11 26-1     # just these
  python3 hrs/fill_missing.py --all --dry-run # count what it would fetch
  python3 hrs/fill_missing.py --refresh       # re-fetch sections whose text here predates a 2025 act

Output: data/law/hrs_fill.jsonl, hrs/hrs_fill_log.csv, and with --all hrs/server_sections.csv (every section page
on the server). build.py loads the sections; it never replaces a section that is already present.
"""
import csv
import json
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE.parent / "data"
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/126.0 Safari/537.36"}
BASE = "https://www.capitol.hawaii.gov/hrscurrent"
DATA_BASE = "https://data.capitol.hawaii.gov/hrscurrent"
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


DASHES = str.maketrans({"\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2212": "-", "\u00ad": ""})


def clean_text(t):
    """The Legislature's pages often print section numbers with a non-breaking hyphen (U+2011)."""
    return (t or "").translate(DASHES)


def parse_page(raw, num):
    p = Paras()
    p.feed(raw)
    paras = [clean_text(x) for x in p.out if x]
    marks = [i for i, x in enumerate(paras) if re.match(r"^\[?\s*§+\s*\d", x)]
    want = num.upper()
    start = next((i for i in marks if want in re.sub(r"\s+", "", paras[i]).upper()), None)
    printed = None
    if start is None and len(marks) == 1:
        start = marks[0]                       # the page's only section, printed with a different number (a typo)
        m = re.match(r"^\[?\s*§+\s*([\w:.\-]+)", paras[start])
        printed = m.group(1) if m else None
    rule = None
    if start is None:
        start = next((i for i, x in enumerate(paras) if re.match(r"^\[?Rule\s+\d+(?:\.\d+)?\]?\s+\S", x)), None)
        if start is None:
            return None
        rule = re.match(r"^\[?Rule\s+(\d+(?:\.\d+)?)", paras[start]).group(1)
    first = paras[start]
    headings = paras[:start]
    body_first = re.sub(r"^(?:\[?\s*§+\s*[\w:.\-]+\]?|\[?Rule\s+[\d.]+\]?)\s*", "", first)
    hm = re.match(r"^(.{1,200}?\.)\s+(.*)$", body_first)
    heading, lead = (hm.group(1), hm.group(2)) if hm else (body_first[:200], "")
    lines, history = [lead] if lead else [], None
    for x in paras[start + 1:]:
        low = x.lower().rstrip(":. ")
        if any(low == n or low.startswith(n + " ") for n in NOTES) or (low.startswith("rule") and "commentary" in low):
            break
        if re.match(r"^\[(?:Am\s+)?L\s*(?:Sp\s*)?\d{4}", x) or re.match(r"^\[L ", x):
            history = x
            break
        lines.append(x)
    text = "\n\n".join(lines)
    if history:
        text += "\n\n" + history
    m = re.search(r"\b(repealed|reserved|renumbered)\b", heading.lower())
    status = m.group(1) if m and len(text) < 200 else "in_force"
    rec = {"heading": heading, "text": text, "headings_above": headings, "status": status}
    if printed:
        rec["printed_number"] = printed
    if rule:
        rec["rule"] = rule
    return rec


def fetch(url, tries=4):
    raw = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                raw = r.read()
            break
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None
            time.sleep(2 ** i)
        except Exception:
            time.sleep(2 ** i)
    if raw is None:
        return None
    for enc in ("utf-8-sig", "windows-1252"):
        try:
            body = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if "Attention Required" in body and "Cloudflare" in body:
        return None
    return body


def listing(url):
    body = fetch(url)
    return re.findall(r'HREF="([^"]+)"', body or "", re.I)


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


def server_inventory(workers=4):
    """Every section page on the Legislature's data server: ({number: path}, [chapter folders with no section pages])."""
    sys.path.insert(0, str(HERE.parent))
    from cite import hrs_number_from_url
    vols = [h for h in listing(DATA_BASE + "/") if re.search(r"/hrscurrent/Vol\d+[^/]*/$", h)]
    chapters = []
    for v in vols:
        chapters += [h for h in listing("https://data.capitol.hawaii.gov" + v) if re.search(r"/HRS\d+[A-Z]*/$", h)]
    print(f"{len(vols)} volumes, {len(chapters)} chapter folders on data.capitol.hawaii.gov")
    found, empty = {}, []
    with ThreadPoolExecutor(workers) as ex:
        for folder, files in zip(chapters, ex.map(lambda c: listing("https://data.capitol.hawaii.gov" + c), chapters)):
            n = 0
            for f in files:
                num = hrs_number_from_url(f)
                if num and f.lower().endswith(".htm"):
                    found.setdefault(num, f)
                    n += 1
            if not n:
                empty.append(folder)
    return found, empty


def chapter_note(folder):
    """What a chapter's own index page says when the chapter has no section pages (e.g. 'REPEALED. L 2025, c 201, §2.')."""
    files = [f for f in listing("https://data.capitol.hawaii.gov" + folder) if f.lower().endswith("-.htm")]
    if not files:
        return ""
    p = Paras()
    p.feed(fetch("https://data.capitol.hawaii.gov" + files[0]) or "")
    lines = [clean_text(x) for x in p.out if x]
    keep = [x for x in lines if re.search(r"repealed|renumbered|transferred|see chapter|present provisions", x, re.I)]
    return " ".join(keep[:3])[:400]


def one(num, path, by_chapter, ranges):
    if path:
        data_url = "https://data.capitol.hawaii.gov" + path
        www_url = "https://www.capitol.hawaii.gov" + path
    else:
        www_url = url_for(num, by_chapter, ranges)
        if not www_url:
            return num, "no_url", None, None
        data_url = www_url.replace("https://www.capitol.hawaii.gov", "https://data.capitol.hawaii.gov")
    for url in (data_url, www_url):
        raw = fetch(url)
        if raw:
            rec = parse_page(raw, num)
            if rec:
                cite = f"Haw. R. Evid. {rec['rule']}" if rec.get("rule") and num.startswith("626:") else f"Haw. Rev. Stat. § {num}"
                rec.update(number=num, citation=cite, source_url=www_url, fetched_from=url,
                           fetched=time.strftime("%Y-%m-%d"))
                return num, "ok", www_url, rec
            return num, "page_has_no_matching_section", www_url, None
    raw, src = wayback(www_url)
    rec = parse_page(raw, num) if raw else None
    if rec:
        rec.update(number=num, citation=f"Haw. Rev. Stat. § {num}", source_url=www_url, fetched_from=src,
                   fetched=time.strftime("%Y-%m-%d"))
        return num, "ok", www_url, rec
    return num, "not_found", www_url, None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry, everything = "--dry-run" in sys.argv, "--all" in sys.argv
    con = sqlite3.connect(DATA / "hawaii.db")
    by_chapter, ranges = volume_folders(con)
    have = {r[0] for r in con.execute("select number from section where corpus='hrs'")}
    out_path = DATA / "law" / "hrs_fill.jsonl"
    done = set()
    if out_path.exists():
        done = {json.loads(l)["number"] for l in open(out_path)}
    paths = {}
    if everything:
        paths, empty = server_inventory()
        with open(HERE / "server_sections.csv", "w", newline="") as sf:
            w = csv.writer(sf)
            w.writerow(["number", "path"])
            w.writerows(sorted(paths.items()))
        with open(HERE / "server_chapter_notes.csv", "w", newline="") as nf:
            w = csv.writer(nf)
            w.writerow(["chapter", "folder", "note"])
            for folder in sorted(empty):
                chap = re.search(r"/HRS0*(\d+[A-Z]*)/$", folder).group(1)
                w.writerow([chap, folder, chapter_note(folder)])
        print(f"{len(empty)} chapter folders have no section pages; their index notes are in server_chapter_notes.csv")
        wanted = sorted(n for n in paths if n not in have)
        print(f"{len(paths)} section pages on the server; {len(wanted)} are not in the database")
    else:
        wanted = [n for n in (args or targets_from_checks()) if n not in have]
    todo = [n for n in wanted if n not in done]
    print(f"{len(wanted)} sections wanted, {len(done)} already fetched, {len(todo)} to go")
    if "--refresh" in sys.argv:
        stale = []
        for name in ("slh2025_amendments_not_in_history_note", "slh2025_repeals_still_in_force"):
            path = HERE / "checks" / f"{name}.csv"
            if path.exists():
                stale += [r["target"] for r in csv.DictReader(open(path))]
        stale = list(dict.fromkeys(stale))
        refresh_path = DATA / "law" / "hrs_refresh.jsonl"
        print(f"refreshing {len(stale)} sections whose text in this database predates a 2025 act")
        n = 0
        with open(refresh_path, "w") as f, ThreadPoolExecutor(4) as ex:
            for num, status, url, rec in ex.map(lambda x: one(x, None, by_chapter, ranges), stale):
                if rec:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    n += 1
        print(f"refreshed {n} of {len(stale)}; saved to {refresh_path}. Run build.py to apply them.")
        return
    if dry:
        for n in todo[:50]:
            print(" ", n, paths.get(n) or url_for(n, by_chapter, ranges))
        return
    got, log = 0, []
    with open(out_path, "a") as f, ThreadPoolExecutor(4) as ex:
        futs = [ex.submit(one, n, paths.get(n), by_chapter, ranges) for n in todo]
        for i, fut in enumerate(as_completed(futs), 1):
            num, status, url, rec = fut.result()
            log.append((num, status, url))
            if rec:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                got += 1
            if i % 100 == 0:
                print(f"  {i}/{len(todo)}  ({got} fetched)", flush=True)
    log_path = HERE / "hrs_fill_log.csv"
    latest = {r["number"]: (r["number"], r["status"], r["url"]) for r in csv.DictReader(open(log_path))} if log_path.exists() else {}
    latest.update({n: (n, st, u) for n, st, u in log})
    with open(log_path, "w", newline="") as lf:
        w = csv.writer(lf)
        w.writerow(["number", "status", "url"])
        w.writerows(sorted(latest.values()))
    print(f"fetched {got} of {len(todo)}; saved to {out_path}. Run build.py to include them.")


if __name__ == "__main__":
    main()
