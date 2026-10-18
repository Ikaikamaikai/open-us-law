"""Build hawaii.db: law + rules + government map + document structures, all local.

Usage: python3 build.py [--data DIR]
Needs: duckdb (to read parquet). The resulting database needs only Python's sqlite3.
"""
import csv
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

import duckdb

from cite import HRS_NUM_PARTS, hrs_in_note, hrs_number_from_url, hrs_order, norm, refs_in_text

HERE = Path(__file__).parent
CORPORA = {
    "hrs":         ("Hawaii Revised Statutes", "HI", "statute", "Hawaii State Legislature"),
    "hi-const":    ("Constitution of the State of Hawaii", "HI", "constitution", "Legislative Reference Bureau"),
    "hi-rules":    ("Hawaii court rules", "HI", "court_rule", "Hawaii State Judiciary"),
    "hi-ag":       ("Hawaii Attorney General opinions", "HI", "ag_opinion", "Department of the Attorney General"),
    "hi-guidance": ("Hawaii Insurance Division memoranda", "HI", "guidance", "DCCA Insurance Division"),
    "har":         ("Hawaii Administrative Rules", "HI", "regulation", "State agencies, filed with the Lieutenant Governor"),
    "us-const":    ("Constitution of the United States", "US", "constitution", "National Archives"),
    "fed-rules":   ("Federal court rules", "US", "court_rule", "U.S. Courts"),
    "usc":         ("United States Code", "US", "statute", "Office of the Law Revision Counsel"),
    "cfr":         ("Code of Federal Regulations (selected parts)", "US", "regulation", "Office of the Federal Register (eCFR)"),
}
JUNK_TITLE = {"HI Code", "Hawaii Code"}


def ord_of(num):
    m = re.search(r"([\d]+(?:\.\d+)?)[A-Za-z]?$", num or "")
    return float(m.group(1)) if m else None


def section_id(corpus, number, citation):
    if corpus in ("hrs", "har", "usc", "cfr") and number:
        return f"{corpus}:{number}"
    return f"{corpus}:{norm(citation)}"


def load_parquet(db, path, corpus, snapshot):
    con = duckdb.connect()
    cols = {r[0] for r in con.sql(f"describe select * from '{path}'").fetchall()}
    q = f"""select citation, section_number, section_title, title_number, title_name, chapter, chapter_name,
                   display_path, act_status, {'year' if 'year' in cols else 'null'}, last_amended_year, text, source_url
            from '{path}'"""
    seen, n = set(), 0
    for row in con.sql(q).fetchall():
        (citation, number, heading, tnum, tname, chap, cname, path_, status, year, amended, text, url) = row
        prov = f"vaquill open-us-law {snapshot}"
        if corpus == "hrs" and not HRS_NUM_PARTS.match((number or "").upper()):
            fixed = hrs_number_from_url(url)
            if fixed:
                prov += f"; section number repaired from source URL (was '{number}')"
                number, citation = fixed, f"Haw. Rev. Stat. § {fixed}"
                chap = re.split(r"[-:]", fixed)[0]
        if corpus == "usc" and number is None:
            m = re.match(r"^(\d+) U\.S\.C\. § (\S+)", citation or "")
            number = f"{m.group(1)}-{m.group(2)}" if m else None
        elif corpus == "usc":
            number = f"{tnum}-{number}"
        elif corpus == "cfr":
            m = re.match(r"^(\d+) C\.F\.R\. § (\S+)", citation or "")
            number = f"{m.group(1)}-{m.group(2)}" if m else number
        sid = section_id(corpus, number, citation)
        base, k = sid, 1
        while sid in seen:
            k += 1
            sid = f"{base}#{k}"
        seen.add(sid)
        db.execute(
            "insert into section(id,corpus,jurisdiction,citation,cite_key,number,heading,title_number,title_name,chapter,"
            "chapter_name,path,ord,status,year,last_amended_year,text,source_url,provenance) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (sid, corpus, CORPORA[corpus][1], re.sub(r"\s*\(\d{4}\)$", "", citation or ""), norm(citation or ""), number,
             heading, tnum, None if tname in JUNK_TITLE else tname, chap, cname, path_, ord_of(number), status, year,
             amended, text, url or "", prov))
        n += 1
    return n


def load_har(db, data):
    chapters = list(csv.DictReader(open(HERE / "har" / "har_chapters.csv")))
    names = {}
    for c in chapters:
        db.execute("insert into har_chapter values (?,?,?,?,?,?,?,?,?,0)",
                   (c["title"], c["listed_under"], c["title_name"], c["subtitle"] or None, c["subtitle_name"] or None,
                    c["chapter"], c["chapter_to"] or None, c["chapter_name"],
                    None if c["repealed"] == "" else int(c["repealed"])))
        names[f"{c['title']}-{c['chapter']}"] = (c["chapter_name"], c["title_name"])
    path = data / "har" / "har_sections.jsonl"
    if not path.exists():
        path = HERE / "har" / "har_sections.jsonl.gz"     # the collected copy kept in the repository
    n = 0
    if path.exists():
        import gzip
        for line in (gzip.open(path, "rt") if path.suffix == ".gz" else open(path)):
            s = json.loads(line)
            cname, tname = names.get(s["chapter"], (None, None))
            db.execute(
                "insert or ignore into section(id,corpus,jurisdiction,citation,cite_key,number,heading,title_number,title_name,"
                "chapter,chapter_name,path,ord,status,text,source_url,provenance) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (s["id"], "har", "HI", s["citation"], norm(s["citation"]), s["section_number"], s["heading"],
                 s["title_number"], tname, s["chapter"], cname,
                 f"HAR Title {s['title_number']} / Chapter {s['chapter']} / § {s['section_number']}",
                 ord_of(s["section_number"]), s["status"], s["text"], s["source_url"],
                 "har-scrape" + (" (ocr)" if s.get("ocr") else "")))
            for num in hrs_in_note(s.get("imp")):
                db.execute("insert into ref values (?,?,?,?,?)", (s["id"], f"haw rev stat {num}", None, "implements", "imp-note"))
            for num in hrs_in_note(s.get("auth")):
                db.execute("insert into ref values (?,?,?,?,?)", (s["id"], f"haw rev stat {num}", None, "authority", "auth-note"))
            n += 1
        db.execute("""update har_chapter set have_text = 1 where title || '-' || chapter in
                      (select distinct chapter from section where corpus = 'har')""")
    for r in csv.DictReader(open(HERE / "har" / "hrs_to_har.csv")):
        hrs = r["hrs_section"]
        if hrs.startswith("C "):
            continue
        db.execute("insert into ref values (?,?,?,?,?)",
                   (f"har:{r['har_section']}", f"haw rev stat {hrs.lower()}", None, "implements", "lrb-2025-table"))
    return n, len(chapters)


def load_hrs_fill(db, data):
    """Sections fetched by hrs/fill_missing.py. Never replaces a section already loaded."""
    path = data / "law" / "hrs_fill.jsonl"
    n = 0
    if not path.exists():
        return 0
    for line in open(path):
        r = json.loads(line)
        num = r["number"]
        chap = re.split(r"[-:]", num)[0]
        cur = db.execute(
            "insert or ignore into section(id,corpus,jurisdiction,citation,cite_key,number,heading,chapter,ord,status,"
            "last_amended_year,text,source_url,provenance) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (f"hrs:{num}", "hrs", "HI", r["citation"], norm(r["citation"]), num, r["heading"], chap, ord_of(num),
             r.get("status", "in_force"), None, r["text"], r["source_url"],
             f"fetched {r.get('fetched', '')} from {r.get('fetched_from', r['source_url'])}"))
        n += cur.rowcount
    return n


def load_hrs_outline(db):
    """Official HRS Table of Contents and the 2025 Table of Disposition (both in hrs/)."""
    chapters = list(csv.DictReader(open(HERE / "hrs" / "hrs_chapters.csv")))
    parts = list(csv.DictReader(open(HERE / "hrs" / "hrs_parts.csv")))
    for c in chapters:
        db.execute("insert into hrs_chapter values (?,?,?,?,?,?,?,?,?,?,?,?,0)",
                   (c["division"], c["division_name"], c["title"], c["title_name"], c["subtitle"] or None,
                    c["subtitle_name"] or None, c["chapter"], c["chapter_to"] or None, c["chapter_name"], c["status"],
                    c["first_section"] or None, int(c["page"])))
    for p in parts:
        db.execute("insert into hrs_part values (?,?,?,?,?,?,?,?,?)",
                   (p["chapter"], p["kind"], p["article"] or None, p["article_name"] or None, p["part"] or None,
                    p["part_name"] or None, p["status"], p["first_section"] or None, int(p["page"])))
    by_chapter = {c["chapter"]: c for c in chapters}
    # A part or article printed without a section number (its subparts carry them) starts where the next
    # numbered entry under it starts; TOC order breaks the tie so the part precedes its first subpart.
    marks, pending = {}, {}
    for i, p in enumerate(parts):
        k = hrs_order(p["first_section"])
        if k is None:
            if p["status"] == "in_force" and p["kind"] in ("part", "article"):
                pending.setdefault(p["chapter"], []).append((i, p))
            continue
        for j, q in pending.pop(p["chapter"], []):
            marks.setdefault(p["chapter"], []).append((k, j, q))
        marks.setdefault(p["chapter"], []).append((k, i, p))
    for v in marks.values():
        v.sort(key=lambda kp: (kp[0], kp[1]))

    def label(p):
        if p["kind"] == "article":
            return f"Article {p['article']}. {p['article_name']}"
        if p["kind"] == "unnumbered":
            return p["part_name"]
        if p["kind"] == "subpart":
            return f"{p['part']}. {p['part_name']}"
        pre = f"Article {p['article']}. {p['article_name']} / " if p["article"] and p["article_name"] else ""
        return f"{pre}Part {p['part']}. {p['part_name']}"

    rows = db.execute("select rowid, number, chapter from section where corpus = 'hrs'").fetchall()
    for rowid, num, chap in rows:
        c = by_chapter.get(chap)
        if not c:
            continue
        key = hrs_order(num)
        major = sub = None
        for k, _, p in marks.get(chap, []):
            if key is None or k > key:
                break
            if p["kind"] == "subpart":
                sub = p
            else:
                major, sub = p, None
        part = " / ".join(label(x) for x in (major, sub) if x) or None
        path = " / ".join(x for x in (f"Title {c['title']}. {c['title_name']}", f"Chapter {chap}. {c['chapter_name']}",
                                       part, f"§ {num}") if x)
        db.execute("update section set chapter_name=?, title_name=?, part=?, division=?, path=? where rowid=?",
                   (c["chapter_name"], c["title_name"], part, f"Division {c['division']}. {c['division_name']}", path, rowid))
    db.execute("""update hrs_chapter set sections_here =
                  (select count(*) from section s where s.corpus='hrs' and s.chapter = hrs_chapter.chapter)""")

    n = 0
    for r in csv.DictReader(open(HERE / "hrs" / "slh_disposition.csv")):
        sid, noted = None, None
        if r["kind"] == "section":
            row = db.execute("select id, text from section where cite_key = ?", (f"haw rev stat {r['target'].lower()}",)).fetchone()
            if row:
                sid = row[0]
                noted = int(bool(re.search(rf"\bL\s*{r['year']},\s*c\s*{r['act']}\b", row[1] or "")))
        db.execute("insert into session_law values (?,?,?,?,?,?,?,?,?,?,?,?)",
                   (int(r["year"]), int(r["act"]), r["act_section"] or None, r["kind"], r["target"], r["chapter"] or None,
                    int(r["repealed"]), int(r["heading_only"]), sid, noted, r["raw"], int(r["page"])))
        n += 1
    return len(chapters), len(parts), n


def build_refs(db):
    rows = db.execute("select id, corpus, text from section").fetchall()
    batch = []
    for sid, corpus, text in rows:
        for key in {k for k in refs_in_text(text, corpus)}:
            batch.append((sid, key[0], None, key[1], "text"))
        if len(batch) > 50000:
            db.executemany("insert into ref values (?,?,?,?,?)", batch)
            batch = []
    db.executemany("insert into ref values (?,?,?,?,?)", batch)
    db.execute("""update ref set to_id = (select s.id from section s where s.cite_key = ref.to_key limit 1)
                  where kind != 'chapter'""")
    db.execute("delete from ref where to_id = from_id")


# ---------------------------------------------------------------- government map
def find(db, cite):
    return db.execute("select id, text, source_url, citation from section where cite_key = ? limit 1", (norm(cite),)).fetchone()


def flat(s):
    return re.sub(r"\s+", " ", (s or "")).lower().replace("’", "'")


def verify(db, cite, quote):
    row = find(db, cite)
    if not row:
        return None, None, 0, "basis not in local corpus"
    ok = flat(quote) in flat(row[1])
    return row[0], row[2], int(ok), None if ok else "quote not found in basis text"


def build_map(db):
    spine = json.loads((HERE / "map" / "spine.json").read_text())
    problems = []

    def add_body(n, origin="spine"):
        sid, url, ok, why = verify(db, n["basis"], n["quote"]) if n.get("basis") else (None, None, 0, "no basis")
        if why:
            problems.append(f"{n['id']}: {why} ({n.get('basis')})")
        db.execute("insert or replace into body values (?,?,?,?,?,?,?,?,?,?,?,?)",
                   (n["id"], n["name"], n["level"], n.get("branch"), n.get("kind"), n.get("parent"),
                    n.get("basis"), sid, n.get("quote"), url, ok, origin))

    for n in spine["nodes"]:
        add_body(n)

    # State departments: listed in HRS 26-4, each created by its own section 26-x.
    s264 = find(db, "Haw. Rev. Stat. § 26-4")
    if s264:
        for name, sec in re.findall(r"\(\d+\)\s*((?:Department of|University of)[^()]+?)\s*\(Section (26-[\d.]+)\)", s264[1]):
            name = re.sub(r"\s+", " ", name).strip()
            did = f"hi.exec.dept.{sec}"
            add_body({"id": did, "name": name[0].upper() + name[1:], "level": "state", "branch": "executive",
                      "kind": "department", "parent": "hi.exec.depts", "basis": f"Haw. Rev. Stat. § {sec}",
                      "quote": f"{name.lower()} shall be headed by"})
            own = find(db, f"Haw. Rev. Stat. § {sec}")
            m = re.search(r"headed by (?:a single executive|an executive board) to be known as (?:the )?([^,.;]+)", flat(own[1])) if own else None
            if m:
                head = m.group(1).strip()
                add_body({"id": f"{did}.head", "name": head[0].upper() + head[1:], "level": "state", "branch": "executive",
                          "kind": "head", "parent": did, "basis": f"Haw. Rev. Stat. § {sec}", "quote": f"to be known as the {head}"
                          if f"to be known as the {head}" in flat(own[1]) else f"to be known as {head}"})
            db.execute("insert into link values (?,?,?,?,?,?,?)",
                       (did, "hi.exec.depts", "listed_in", "Haw. Rev. Stat. § 26-4", s264[0], name, int(flat(name) in flat(s264[1]))))

    # Federal executive departments: 5 U.S.C. 101.
    s101 = find(db, "5 U.S.C. § 101")
    if s101:
        body = re.split(r"\(\s*(?:Pub|Aug|Sept|June)", s101[1])[0]
        for name in re.findall(r"The (Department of [A-Z][A-Za-z ,]+?)\.", body):
            slug = re.sub(r"[^a-z]+", "-", name.lower()).strip("-")
            add_body({"id": f"us.dept.{slug}", "name": name, "level": "federal", "branch": "executive", "kind": "department",
                      "parent": "us.depts", "basis": "5 U.S.C. § 101", "quote": f"The {name}"})

    for l in spine["links"]:
        sid, _, ok, why = verify(db, l["basis"], l["quote"])
        if why:
            problems.append(f"link {l['from']}->{l['to']}: {why} ({l['basis']})")
        db.execute("insert into link values (?,?,?,?,?,?,?)", (l["from"], l["to"], l["relation"], l["basis"], sid, l["quote"], ok))

    for a in spine["access"]:
        sid, _, ok, why = verify(db, a["basis"], a["quote"])
        if why:
            problems.append(f"{a['id']}: {why} ({a['basis']})")
        db.execute("insert into access_rule values (?,?,?,?,?,?,?)", (a["id"], a["record_kind"], a["body"], a["basis"], sid, a["quote"], ok))

    mined = mine_bodies(db)
    return problems, mined


MINE_P1 = re.compile(
    r"[Tt]here is (?:hereby )?(?:established|created)(?: (?:with)?in the ((?:department|office) of [a-z ,'&-]+?|university of hawaii)"
    r"(?:,)?(?: for administrative purposes(?: only)?)?)?,? (?:an?|the) ([A-Za-z ,'&-]{4,120}?)"
    r"(?:,| to be known as| which| that| consisting| composed| for the| hereinafter|\.)")
MINE_P2 = re.compile(
    r"[Tt]he ([a-z][a-z ,'&-]{3,100}?) (?:is|shall be) (?:hereby )?(?:established|placed|created)(?:,)? (?:with)?in the "
    r"((?:department|office) of [a-z ,'&-]+?|university of hawaii)(?:,)? for administrative purposes")
KINDS = ["special fund", "revolving fund", "trust fund", "fund", "commission", "board", "council", "authority", "corporation",
         "committee", "task force", "office", "agency", "division", "center", "program", "position"]


def mine_bodies(db):
    depts = {flat(n): i for i, n in db.execute("select id, name from body where kind = 'department' and level = 'state'").fetchall()}
    out = []
    for sid, cite, text, url in db.execute("select id, citation, text, source_url from section where corpus='hrs' and status='in_force'"):
        t = re.sub(r"\s+", " ", text or "")
        for m, name, parent in ([(m, m.group(2), m.group(1)) for m in MINE_P1.finditer(t)] +
                                [(m, m.group(1), m.group(2)) for m in MINE_P2.finditer(t)]):
            name = re.sub(r"\s+(?:within the (?:department|state|judiciary|office)\b.*|into|from|within|in|to be administered by.*|to)$", "", name.strip()).strip(" ,")
            low = name.lower()
            kind = next((k for k in KINDS if low.endswith(k) or f" {k} " in f" {low} "), None)
            if not kind or len(name.split()) > 14:
                continue
            pid = depts.get(flat(parent or "")) if parent else None
            bid = f"hi.mined.{sid.split(':', 1)[1]}.{re.sub(r'[^a-z0-9]+', '-', low).strip('-')[:60]}"
            quote = t[m.start():m.end()]
            db.execute("insert or ignore into body values (?,?,?,?,?,?,?,?,?,?,?,?)",
                       (bid, name[0].upper() + name[1:], "state", "executive", kind.split()[-1] if "fund" in kind else kind,
                        pid, cite, sid, quote, url, 1, "mined"))
            out.append((bid, name, kind, pid or "", cite, quote))
    return out


def build_structures(db):
    spine = json.loads((HERE / "map" / "spine.json").read_text())
    for st in spine.get("structures", []):
        row = find(db, st["basis"])
        db.execute("insert or replace into structure values (?,?,?,?,?,?)",
                   (st["id"], st["name"], st["basis"], row[0] if row else None, row[2] if row else None, st.get("note")))
        if not row:
            continue
        t = re.sub(r"\s+", " ", row[1])
        items = list(re.finditer(r"\(([a-w])\)\s*Item\s+(\d+)\s*:\s*", t))
        for i, m in enumerate(items):
            end = items[i + 1].start() if i + 1 < len(items) else len(t)
            chunk = t[m.end():end].strip()
            hm = re.match(r"^(.+?\.)\s+(.*)$", chunk)
            heading, body = (hm.group(1), hm.group(2)) if hm else (chunk[:120], chunk)
            db.execute("insert or replace into structure_part values (?,?,?,?,?)",
                       (st["id"], int(m.group(2)), f"Item {m.group(2)}", heading.rstrip("."), body))


def main():
    data = Path(sys.argv[sys.argv.index("--data") + 1]) if "--data" in sys.argv else HERE / "data"
    src = json.loads((HERE / "sources.json").read_text())
    out = data / "hawaii.db"
    tmp = data / "hawaii.db.building"
    for p in (tmp, Path(str(tmp) + "-wal"), Path(str(tmp) + "-shm")):
        p.unlink(missing_ok=True)
    t0 = time.time()
    db = sqlite3.connect(tmp)
    db.executescript((HERE / "schema" / "schema.sql").read_text())
    counts = {}
    files = [(e["file"], e["corpus"]) for e in src["files"]] + [(f"{s['name']}.parquet", "cfr") for s in src.get("cfr_slices", [])]
    for fname, corpus in files:
        p = data / "law" / fname
        if not p.exists():
            print(f"skip    {fname} (run fetch.py)")
            continue
        counts[corpus] = counts.get(corpus, 0) + load_parquet(db, p, corpus, src["snapshot"])
        print(f"loaded  {fname}: {counts[corpus]}")
    if counts.get("hrs"):
        filled = load_hrs_fill(db, data)
        if filled:
            print(f"filled  {filled} HRS sections from hrs/fill_missing.py")
            counts["hrs"] += filled
        print("outline HRS TOC %d chapters, %d parts; 2025 session law table %d rows" % load_hrs_outline(db))
    har_n, har_ch = load_har(db, data)
    counts["har"] = har_n
    print(f"loaded  HAR: {har_n} sections, {har_ch} chapters in directory")
    for cid, n in counts.items():
        name, jur, kind, pub = CORPORA[cid]
        prov = "LRB 2025 directory + agency PDFs" if cid == "har" else f"vaquill open-us-law {src['snapshot']}"
        db.execute("insert into corpus values (?,?,?,?,?,?,?)", (cid, name, jur, kind, pub, prov, n))
    build_refs(db)
    print(f"refs    {db.execute('select count(*), count(to_id) from ref').fetchone()} (all, resolved)")
    db.execute("insert into section_fts(section_fts) values ('rebuild')")
    problems, mined = build_map(db)
    build_structures(db)
    from hi import insert_records
    for f in sorted((data / "records").glob("*.jsonl")) if (data / "records").exists() else []:
        print(f"records {f.name}: {insert_records(db, f)}")
    db.commit()
    db.execute("pragma optimize")
    db.close()
    for p in (Path(str(out) + "-wal"), Path(str(out) + "-shm"), Path(str(out) + "-journal")):
        p.unlink(missing_ok=True)
    tmp.replace(out)
    with open(HERE / "map" / "bodies_mined.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "name", "kind", "parent_id", "basis_cite", "quote"])
        w.writerows(sorted(mined))
    print(f"map     {len(mined)} bodies mined from HRS; {len(problems)} spine items not verified")
    for p in problems:
        print(f"        - {p}")
    print(f"built   {out} in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
