#!/usr/bin/env python3
"""hi: a local, offline shell over Hawaii and federal law, rules, government structure, and your records.

  hi <anything>                 read a citation, or answer a plain question, or search
  hi find <words> [--in C] [--all] [-n N]   full-text search (C: hrs har hi-const hi-rules hi-ag hi-guidance usc us-const fed-rules cfr records)
  hi read <citation>            full text of a section
  hi near <citation>            the sections before and after it
  hi defs <citation>            the definitions that govern it (its chapter's definitions sections)
  hi citedby <citation>         sections whose text cites it, and rules that implement it
  hi rules <HRS citation>       Hawaii Administrative Rules that implement a statute
  hi cites <text | @file>       find and resolve every citation in a text
  hi browse [corpus [chapter]]  walk the hierarchy
  hi chapter <n>                the official outline of an HRS chapter, and which sections this copy has
  hi act <n> [year]             what a session law changed in the HRS (2025 Table of Disposition)
  hi gaps                       how this copy compares with the official TOC and Table of Disposition
  hi map [name]                 government structure, each part with the law that creates it
  hi access                     the laws that open records and meetings to the public
  hi structure [id]             document layouts the law requires (e.g. fdd)
  hi coverage                   what is in the database
  hi load <file.jsonl>          add your public records (court cases, parcels, filings, documents)
  hi serve [--port 8808]        local search page at http://127.0.0.1:8808
  hi mcp                        MCP server on stdio, for AI apps on this machine

Needs only Python 3 and the database built by build.py. No network, no keys.
"""
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from cite import keys_for_query, norm, refs_in_text  # noqa: E402

DB_PATH = Path(os.environ.get("HI_DB", HERE / "data" / "hawaii.db"))
CORPUS_WORDS = {
    "hrs": "hrs", "statute": "hrs", "statutes": "hrs", "har": "har", "rule": "har", "administrative rules": "har",
    "regulations": "har", "constitution": "hi-const", "court rules": "hi-rules", "court rule": "hi-rules",
    "ag opinions": "hi-ag", "attorney general": "hi-ag", "insurance": "hi-guidance", "guidance": "hi-guidance",
    "federal": "usc", "usc": "usc", "us code": "usc", "federal rules": "fed-rules", "cfr": "cfr", "records": "records",
}
STOP = set("a an the of to in on for and or is are was be by with what which who whom how does do i my me can about "
           "under from that this there their any all as at it its say says said tell show find".split())


def db():
    if not DB_PATH.exists():
        sys.exit(f"no database at {DB_PATH}. Run: python3 fetch.py && python3 build.py")
    con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


# ============================================================ core (used by CLI, web, MCP)
def resolve(con, q):
    """Citation text -> section rows (exact)."""
    for key in keys_for_query(q):
        rows = con.execute("select * from section where cite_key = ?", (key,)).fetchall()
        if rows:
            return [dict(r) for r in rows]
        if key.startswith("chapter "):
            ch = key.split(" ", 1)[1].upper()
            rows = con.execute("select * from section where corpus='hrs' and upper(chapter)=? order by ord", (ch,)).fetchall()
            if rows:
                return [dict(r) for r in rows]
    row = con.execute("select * from section where id = ?", (q.strip(),)).fetchone()
    return [dict(row)] if row else []


def fts_query(words, mode="and"):
    toks = [t for t in re.findall(r"[\w'-]+", words.lower()) if t not in STOP and len(t) > 1]
    if not toks:
        return None
    toks = [f'"{t}"' for t in toks]
    toks[-1] = toks[-1] + "*"
    return (" OR " if mode == "or" else " AND ").join(toks)


def search(con, words, corpus=None, include_all=False, limit=15):
    out = []
    phrase = re.findall(r'"([^"]+)"', words)
    for mode in ("and", "or"):
        q = " AND ".join(f'"{p}"' for p in phrase) if phrase else fts_query(words, mode)
        if not q:
            return []
        sql = """select s.id, s.citation, s.heading, s.status, s.corpus, s.source_url, s.path, s.provenance,
                        snippet(section_fts, 3, '[', ']', ' … ', 18) as snip,
                        bm25(section_fts, 10.0, 6.0, 1.0, 1.0) as score
                 from section_fts join section s on s.rowid = section_fts.rowid
                 where section_fts match ?"""
        args = [q]
        if corpus and corpus != "records":
            sql += " and s.corpus = ?"
            args.append(corpus)
        if not include_all:
            sql += " and coalesce(s.status,'in_force') not in ('repealed','reserved','omitted','transferred','renumbered','vacant','expired')"
        sql += " order by score limit ?"
        args.append(limit)
        try:
            out = [dict(r) for r in con.execute(sql, args)] if corpus != "records" else []
        except sqlite3.OperationalError:
            out = []
        recs = search_records(con, q, limit) if corpus in (None, "records") else []
        if out or recs or phrase:
            return recs + out
    return out


def search_records(con, q, limit):
    try:
        return [dict(r) | {"corpus": "records"} for r in con.execute(
            """select r.id, r.number as citation, r.title as heading, r.status, r.source_url, r.kind as path,
                      snippet(record_fts, 2, '[', ']', ' … ', 18) as snip
               from record_fts join record r on r.rowid = record_fts.rowid where record_fts match ? limit ?""", (q, limit))]
    except sqlite3.OperationalError:
        return []


def neighbors(con, sec):
    prev = con.execute("select id, citation, heading from section where corpus=? and chapter is ? and ord < ? order by ord desc limit 1",
                       (sec["corpus"], sec["chapter"], sec["ord"])).fetchone()
    nxt = con.execute("select id, citation, heading from section where corpus=? and chapter is ? and ord > ? order by ord limit 1",
                      (sec["corpus"], sec["chapter"], sec["ord"])).fetchone()
    return dict(prev) if prev else None, dict(nxt) if nxt else None


def definitions(con, sec):
    rows = con.execute("""select id, citation, heading, text, source_url from section
                          where corpus=? and chapter is ? and (lower(heading) like 'definition%' or lower(heading) like '%; definitions%'
                                or lower(heading) like 'general definitions%')
                          order by ord""", (sec["corpus"], sec["chapter"])).fetchall()
    return [dict(r) for r in rows]


def define_term(con, term, limit=10):
    term = term.strip().strip('"').lower()
    q = f'"{term}" AND (means OR includes)'
    rows = con.execute("""select s.id, s.citation, s.heading, s.text, s.source_url from section_fts
                          join section s on s.rowid = section_fts.rowid
                          where section_fts match ? and coalesce(s.status,'in_force')='in_force'
                          order by bm25(section_fts, 1, 4, 1, 1) limit 200""", (q,)).fetchall()
    out = []
    pat = re.compile(r'["“]' + re.escape(term) + r'["”]\s+(?:means|includes|shall mean|has the meaning)[^.]*\.', re.I)
    for r in rows:
        m = pat.search(re.sub(r"\s+", " ", r["text"] or ""))
        if m:
            out.append({"id": r["id"], "citation": r["citation"], "heading": r["heading"], "definition": m.group(0),
                        "source_url": r["source_url"]})
        if len(out) >= limit:
            break
    return out


def cited_by(con, sec_id, limit=60):
    rows = con.execute("""select r.kind, r.basis, s.id, s.citation, s.heading, s.corpus from ref r join section s on s.id = r.from_id
                          where r.to_id = ? order by r.kind, s.corpus, s.ord limit ?""", (sec_id, limit)).fetchall()
    return [dict(r) for r in rows]


def cites_from(con, sec_id):
    rows = con.execute("""select r.kind, r.to_key, r.to_id, s.citation, s.heading from ref r left join section s on s.id = r.to_id
                          where r.from_id = ? order by r.kind""", (sec_id,)).fetchall()
    return [dict(r) for r in rows]


def implementing_rules(con, sec_id):
    rows = con.execute("""select distinct r.from_id, r.basis, s.citation, s.heading, s.source_url from ref r
                          left join section s on s.id = r.from_id
                          where r.to_id = ? and r.kind = 'implements' order by r.from_id""", (sec_id,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        if not d["citation"]:
            d["citation"] = "HAR § " + d["from_id"].split(":", 1)[1]
            d["heading"] = "(listed by the LRB 2025 table; text not collected yet)"
        out.append(d)
    return out


def session_laws_for(con, sec_id):
    return [dict(r) for r in con.execute(
        """select year, act, act_section, repealed, heading_only, noted_in_text from session_law
           where section_id = ? order by year desc, act""", (sec_id,))]


def session_law_act(con, act, year=2025):
    rows = con.execute(
        """select l.*, s.citation, s.heading, s.status as section_status from session_law l
           left join section s on s.id = l.section_id where l.year = ? and l.act = ? order by l.rowid""",
        (year, act)).fetchall()
    return [dict(r) for r in rows]


def outline(con, chapter):
    ch = con.execute("select * from hrs_chapter where upper(chapter) = upper(?)", (chapter,)).fetchone()
    if not ch:
        return None
    parts = [dict(r) for r in con.execute("select * from hrs_part where upper(chapter) = upper(?) order by rowid", (chapter,))]
    for p in parts:
        p["present"] = bool(p["first_section"]) and con.execute(
            "select 1 from section where cite_key = ?", ("haw rev stat " + (p["first_section"] or "").lower(),)).fetchone() is not None
    secs = [dict(r) for r in con.execute(
        "select id, number, heading, status, part from section where corpus='hrs' and upper(chapter)=upper(?) order by ord",
        (chapter,))]
    return {"chapter": dict(ch), "parts": parts, "sections": secs}


def not_here(con, q):
    """What the official directories say about a citation this database does not hold."""
    key = (keys_for_query(q) or [norm(q)])[0]
    info = {"citation": q.strip(), "key": key, "listed": None, "how_to_get": None}
    m = re.match(r"^har (\d+)-([\d.]+[a-z]?)-", key)
    if m:
        row = con.execute("select * from har_chapter where title=? and lower(chapter)=?", (m.group(1), m.group(2))).fetchone()
        if row:
            info["listed"] = (f"HAR chapter {row['title']}-{row['chapter']} is listed by the LRB directory as "
                              f"“{row['chapter_name']}” ({row['title_name']})"
                              + (", repealed" if row["repealed"] == 1 else "") + ".")
        info["how_to_get"] = ("Its text has not been collected yet. Run har/scrape_har.py data/har (it resumes) "
                              "and then build.py.")
        return info
    m = re.match(r"^haw rev stat ([\w:.]+)-", key)
    if m:
        chap = m.group(1).split(":")[0].upper()
        row = con.execute("select * from hrs_chapter where upper(chapter)=?", (chap,)).fetchone()
        if row:
            info["listed"] = (f"HRS chapter {row['chapter']} is “{row['chapter_name']}” (Title {row['title']}, "
                              f"{row['title_name']}), {row['status'].replace('_', ' ')} in the official Table of Contents.")
        info["how_to_get"] = ("This copy of the HRS does not have this section. Run hrs/fill_missing.py "
                              f"{key.split(' ')[-1].upper()} on your computer, then build.py.")
        return info
    info["how_to_get"] = "Not in the sources loaded here."
    return info


def gaps(con):
    q = {
        "chapters listed in force with no sections here":
            "select count(*) from hrs_chapter where status='in_force' and sections_here=0",
        "opening sections of chapters/parts not here":
            """select count(*) from (select p.first_section f from hrs_part p join hrs_chapter c on c.chapter = p.chapter
               where p.status='in_force' and c.status='in_force' and p.first_section is not null and c.sections_here>0
               union select first_section from hrs_chapter where status='in_force' and first_section is not null and sections_here>0)
               where not exists (select 1 from section s where s.cite_key = 'haw rev stat ' || lower(f))""",
        "2025 act targets not here":
            "select count(*) from session_law where year=2025 and kind='section' and repealed=0 and section_id is null",
        "2025 repeals still in force here":
            """select count(*) from session_law l join section s on s.id=l.section_id
               where l.year=2025 and l.repealed=1 and s.status='in_force'""",
        "2025 amendments not cited in the section's history note":
            """select count(*) from session_law where year=2025 and kind='section' and repealed=0 and heading_only=0
               and section_id is not null and noted_in_text=0""",
        "section numbers repaired from source URLs":
            "select count(*) from section where provenance like '%repaired from source URL%'",
        "sections filled by hrs/fill_missing.py":
            "select count(*) from section where corpus='hrs' and provenance like 'fetched %'",
    }
    return {k: con.execute(v).fetchone()[0] for k, v in q.items()}


def extract_citations(con, text):
    found = {}
    for key, kind in refs_in_text(text, "hrs"):
        if kind == "chapter":
            continue
        row = con.execute("select id, citation, heading, status, source_url from section where cite_key=? limit 1", (key,)).fetchone()
        found[key] = dict(row) if row else {"citation": key, "status": "not found in local database"}
    for m in re.finditer(r"(?:HRS|Haw\. Rev\. Stat\.|HAR|HRCP|FRCP|Fed\. R\. Civ\. P\.|Haw\. R\. Civ\. P\.)\s*§*\s*[\w:.-]+", text):
        for row in resolve(con, m.group(0))[:1]:
            found[row["cite_key"]] = {k: row[k] for k in ("id", "citation", "heading", "status", "source_url")}
    return list(found.values())


def body_rows(con, where="1=1", args=()):
    return [dict(r) for r in con.execute(f"select * from body where {where} order by level, branch, kind, name", args)]


def find_body(con, name):
    """Exact name or id first; then every word present, ranked: whole phrase, state level, spine before mined, shorter name."""
    name = name.strip().lower()
    rows = body_rows(con, "lower(name) = ? or id = ?", (name, name))
    if rows:
        return rows
    words = [w.rstrip("s") for w in re.findall(r"\w+", name) if w not in STOP]
    if not words:
        return []
    rows = body_rows(con, " and ".join(["lower(name) like ?"] * len(words)), tuple(f"%{w}%" for w in words))
    phrase = " ".join(words)
    return sorted(rows, key=lambda b: (phrase not in b["name"].lower(), b["level"] != "state", b["origin"] != "spine", len(b["name"])))


def body_detail(con, b):
    kids = body_rows(con, "parent_id = ?", (b["id"],))
    parent = con.execute("select * from body where id = ?", (b["parent_id"],)).fetchone() if b["parent_id"] else None
    links = [dict(r) for r in con.execute(
        """select l.*, f.name as from_name, t.name as to_name from link l join body f on f.id=l.from_id join body t on t.id=l.to_id
           where l.from_id = ? or l.to_id = ?""", (b["id"], b["id"]))]
    access = [dict(r) for r in con.execute("select * from access_rule where body_id = ?", (b["id"],))]
    records = [dict(r) for r in con.execute("select id, kind, number, title, date, source_url from record where body_id = ? limit 50", (b["id"],))]
    return {"body": b, "parent": dict(parent) if parent else None, "children": kids, "links": links, "access": access, "records": records}


def structure(con, sid=None):
    if not sid:
        return [dict(r) for r in con.execute("select * from structure")]
    st = con.execute("select * from structure where id = ?", (sid,)).fetchone()
    if not st:
        return None
    parts = [dict(r) for r in con.execute("select * from structure_part where structure_id = ? order by ord", (sid,))]
    return {"structure": dict(st), "parts": parts}


def coverage(con):
    corp = [dict(r) for r in con.execute("select * from corpus order by jurisdiction desc, id")]
    har = con.execute("select count(*), sum(repealed=0), sum(have_text) from har_chapter").fetchone()
    refs = con.execute("select kind, count(*), count(to_id) from ref group by kind").fetchall()
    bodies = con.execute("select origin, count(*), sum(verified) from body group by origin").fetchall()
    recs = con.execute("select kind, count(*) from record group by kind").fetchall()
    return {"corpora": corp, "har_chapters": {"listed": har[0], "active": har[1], "with_text": har[2]},
            "refs": [tuple(r) for r in refs], "bodies": [tuple(r) for r in bodies], "records": [tuple(r) for r in recs]}


# ============================================================ intent: what the person is asking
INTENTS = [
    ("act", re.compile(r"^(?:(\d{4})\s+)?(?:act|session laws?(?: act)?)\s+(\d{1,3})(?:\s*(?:of|,)?\s*(\d{4}))?\s*$", re.I)),
    ("outline", re.compile(r"^(?:hrs\s+)?(?:chapter|ch\.?|outline(?: of)?(?: chapter)?)\s+(\d{1,3}[a-z]{0,2})\s*$", re.I)),
    ("gaps", re.compile(r"^(?:gaps|completeness|what(?:'s| is) not here)\??$", re.I)),
    ("define", re.compile(r"^(?:define|definition of|meaning of|what (?:is|are) (?:the )?(?:legal )?definition of|what does (?:the term )?[\"“]?(.+?)[\"”]? mean)\s*[\"“]?(.*?)[\"”]?\??$", re.I)),
    ("who", re.compile(r"^(?:who|what agency|which agency|which department|what department)\s+(?:runs|heads|oversees|controls|regulates|handles|is in charge of|is responsible for|enforces|licenses)\s+(.+?)\??$", re.I)),
    ("appeal", re.compile(r"^(?:how (?:do i|to|can i) )?appeal(?:s)?(?: (?:from|a decision of|a))?\s*(.*?)\??$", re.I)),
    ("access", re.compile(r"\b(?:public records?|records request|open meetings?|sunshine|uipa|foia|access to (?:records|information)|court records)\b", re.I)),
    ("rules", re.compile(r"^(?:rules?|regulations?|har)\s+(?:for|under|implementing|that implement)\s+(.+?)\??$", re.I)),
    ("citedby", re.compile(r"^(?:what|who)\s+(?:cites|refers to|references)\s+(.+?)\??$", re.I)),
    ("read", re.compile(r"^(?:what does|read|show|open|text of)\s+(.+?)(?:\s+say)?\??$", re.I)),
    ("structure", re.compile(r"\b(?:franchise disclosure|fdd|disclosure document|item \d{1,2}\b)", re.I)),
    ("map", re.compile(r"^(?:map|structure of government|org chart|who is|what is the)\s*(.*?)\??$", re.I)),
]


def interpret(q):
    """Return (intent, object, filters, explanation). Plain rules, shown to the person, no guessing hidden."""
    filters = {}
    s = q.strip()
    m = re.search(r"\s+in\s+(court rules?|administrative rules|statutes?|hrs|har|constitution|ag opinions|attorney general|federal rules|federal|usc|us code|cfr|records|regulations|insurance|guidance)\s*$", s, re.I)
    if m:
        filters["corpus"] = CORPUS_WORDS[m.group(1).lower().rstrip("s") if m.group(1).lower().rstrip("s") in CORPUS_WORDS else m.group(1).lower()]
        s = s[:m.start()]
    if re.search(r"\b(?:including repealed|repealed too|all versions)\b", s, re.I):
        filters["all"] = True
        s = re.sub(r"\b(?:including repealed|repealed too|all versions)\b", "", s, flags=re.I).strip()
    for name in ("act", "outline", "gaps"):
        m = dict(INTENTS)[name].match(s)
        if m:
            if name == "act":
                return "act", f"{m.group(2)} {m.group(1) or m.group(3) or 2025}", filters
            return name, (m.group(1) if m.groups() else ""), filters
    if keys_for_query(s) and re.search(r"\d", s):
        return "read", s, filters
    for name, pat in INTENTS:
        if name in ("act", "outline", "gaps"):
            continue
        m = pat.search(s)
        if m:
            obj = next((g for g in m.groups() if g), "") if m.groups() else s
            if name == "read" and not keys_for_query(obj):
                continue
            return name, obj.strip(), filters
    return "find", s, filters


def answer(con, q):
    intent, obj, f = interpret(q)
    out = {"query": q, "intent": intent, "object": obj, "filters": f}
    if intent == "act":
        act, year = obj.split()
        out["read_as"] = f"Session Laws of {year}, Act {act}: what it changed in the HRS"
        targets = session_law_act(con, int(act), int(year))
        if not targets:
            lo, hi_, n = con.execute("select min(act), max(act), count(distinct act) from session_law where year = ?",
                                     (int(year),)).fetchone()
            out["no_match"] = (f"Act {act} of {year} is not in the Table of Disposition loaded here"
                               + (f" (it covers Acts {lo}–{hi_} of {year})." if n else f" (no table for {year} is loaded)."))
            return out
        out["act"] = {"year": int(year), "act": int(act), "targets": targets}
        return out
    if intent == "outline":
        out["outline"] = outline(con, obj)
        if out["outline"]:
            c = out["outline"]["chapter"]
            out["read_as"] = f"HRS chapter {c['chapter']}: {c['chapter_name']}"
            return out
    if intent == "gaps":
        out["gaps"] = gaps(con)
        out["read_as"] = "How this copy of the HRS compares with the official Table of Contents and 2025 Table of Disposition"
        return out
    if intent == "read":
        rows = resolve(con, obj)
        if rows:
            out["sections"] = rows[:50]
            out["read_as"] = f"Read {rows[0]['citation']}" + (f" (+{len(rows) - 1} more)" if len(rows) > 1 else "")
            return out
        out["not_here"] = not_here(con, obj)
        out["read_as"] = f"{out['not_here']['citation']} is not in this database"
        return out
    if intent == "define":
        out["definitions"] = define_term(con, obj)
        out["read_as"] = f'Definitions of "{obj}" written in the law'
        if out["definitions"]:
            return out
    if intent == "who":
        out["bodies"] = [body_detail(con, b) for b in find_body(con, obj)[:5]]
        out["read_as"] = f'Which part of government handles "{obj}"'
        if not out["bodies"]:
            out["no_match"] = (f'No part of the government map is named "{obj}". '
                               f'Below: sections of law that mention it, which may name who handles it.')
            out["results"] = search(con, obj, None, False, 10)
        return out
    if intent == "appeal":
        b = find_body(con, obj)[:1] if obj else []
        out["read_as"] = "Where decisions go next, by law"
        if obj and not b:
            out["no_match"] = (f'No court or agency named "{obj}" is in the government map. '
                               'Try a court (district court, circuit court, family court, land court, tax appeal court) '
                               'or a department (department of health).')
            return out
        out["appeal_path"] = appeal_path(con, b[0]["id"] if b else "hi.jud.district")
        return out
    if intent == "access":
        out["access"] = [dict(r) for r in con.execute("select a.*, b.name as body_name from access_rule a left join body b on b.id=a.body_id")]
        out["read_as"] = "Laws that open records and meetings to the public"
        return out
    if intent == "rules":
        rows = resolve(con, obj)
        if rows:
            out["rules"] = implementing_rules(con, rows[0]["id"])
            out["sections"] = rows[:1]
            out["read_as"] = f"Administrative rules that implement {rows[0]['citation']}"
            return out
    if intent == "citedby":
        rows = resolve(con, obj)
        if rows:
            out["cited_by"] = cited_by(con, rows[0]["id"])
            out["sections"] = rows[:1]
            out["read_as"] = f"What cites {rows[0]['citation']}"
            return out
    if intent == "structure":
        out["structure"] = structure(con, "fdd")
        out["read_as"] = "Franchise Disclosure Document: the 23 items the law requires"
        return out
    if intent == "map":
        bodies = find_body(con, obj) if obj else body_rows(con, "parent_id is null")
        out["bodies"] = [body_detail(con, b) for b in bodies[:5]]
        out["read_as"] = "Government structure"
        if bodies:
            return out
    out["intent"] = "find"
    out["results"] = search(con, obj or q, f.get("corpus"), f.get("all", False))
    out["read_as"] = f'Search for "{obj or q}"' + (f" in {f['corpus']}" if f.get("corpus") else "")
    return out


def appeal_path(con, start):
    path, cur, seen = [], start, set()
    while cur and cur not in seen:
        seen.add(cur)
        b = con.execute("select id, name, parent_id from body where id = ?", (cur,)).fetchone()
        nxt, via = None, cur
        while via and not nxt:
            nxt = con.execute("""select l.to_id, l.relation, l.basis_cite, l.basis_quote, l.verified from link l
                                 where l.from_id = ? and l.relation in ('appeals_to','certiorari_to','contested_case_review_in')
                                 order by l.relation = 'certiorari_to' limit 1""", (via,)).fetchone()
            if not nxt:
                up = con.execute("select parent_id from body where id = ?", (via,)).fetchone()
                via = up[0] if up and up[0] not in ("hi", "us", None) else None
        path.append({"id": cur, "name": b["name"] if b else cur, "next": dict(nxt) if nxt else None})
        cur = nxt["to_id"] if nxt else None
    return path


# ============================================================ terminal output
B, D, R = ("\033[1m", "\033[2m", "\033[0m") if sys.stdout.isatty() else ("", "", "")


def wrap(t, width=100, indent="  "):
    t = re.sub(r"[ \t]+", " ", t or "").strip()
    lines = []
    for para in re.split(r"\n\s*\n|\n(?=\(\w+\))", t):
        para = re.sub(r"\s*\n\s*", " ", para)
        while len(para) > width:
            cut = para.rfind(" ", 0, width)
            cut = cut if cut > 0 else width
            lines.append(indent + para[:cut])
            para = para[cut + 1:]
        lines.append(indent + para)
    return "\n".join(lines)


def p_section(s, full=True):
    st = "" if (s.get("status") or "in_force") == "in_force" else f"  [{s['status']}]"
    prov = f"  {D}({s['provenance']}){R}" if s.get("provenance") and "ocr" in s["provenance"] else ""
    print(f"{B}{s['citation']}{R}  {s.get('heading') or ''}{st}{prov}")
    if s.get("path"):
        print(f"{D}  {s['path']}{R}")
    if full:
        print(wrap(s.get("text")))
    print(f"{D}  source: {s.get('source_url')}{R}\n")


def p_results(rows):
    if not rows:
        print("  nothing found")
    for r in rows:
        st = "" if (r.get("status") or "in_force") == "in_force" else f" [{r['status']}]"
        print(f"{B}{r['citation']}{R}  {r.get('heading') or ''}{st}  {D}{r['corpus']}{R}")
        if r.get("snip"):
            print(wrap(r["snip"], 100, "    "))
    print()


def p_body(d):
    b = d["body"]
    mark = "✓" if b["verified"] else "✗ unverified"
    print(f"{B}{b['name']}{R}  {D}{b['level']} · {b.get('branch') or ''} · {b.get('kind') or ''}{R}")
    if b.get("basis_cite"):
        print(f"  created by {b['basis_cite']} {mark}: “{b.get('basis_quote')}”")
        print(f"{D}  source: {b.get('source_url')}{R}")
    if d["parent"]:
        print(f"  part of: {d['parent']['name']}")
    for k in d["children"][:40]:
        print(f"   └ {k['name']}  {D}{k.get('basis_cite') or ''}{R}")
    if len(d["children"]) > 40:
        print(f"   … {len(d['children']) - 40} more")
    for l in d["links"]:
        print(f"  {l['from_name']} —{l['relation']}→ {l['to_name']}  {D}{l['basis_cite']}{R}")
    for a in d["access"]:
        print(f"  public access ({a['record_kind']}): {a['basis_cite']}")
    print()


def p_answer(a, con):
    print(f"{D}read as: {a.get('read_as')}{R}\n")
    for s in a.get("sections", [])[:1] if a["intent"] != "read" else a.get("sections", []):
        p_section(s)
    if a["intent"] == "read" and len(a.get("sections", [])) == 1:
        s = a["sections"][0]
        prev, nxt = neighbors(con, s)
        rules = implementing_rules(con, s["id"]) if s["corpus"] == "hrs" else []
        cb = cited_by(con, s["id"], 15)
        if prev or nxt:
            print(f"{D}  ← {prev['citation'] if prev else '—'}   |   {nxt['citation'] if nxt else '—'} →{R}")
        for l in session_laws_for(con, s["id"]):
            what = "repealed" if l["repealed"] else ("heading changed" if l["heading_only"] else "added or amended")
            note = "" if l["noted_in_text"] or l["repealed"] else f"  {D}(not yet in this copy's history note){R}"
            print(f"  {l['year']} Session Laws, Act {l['act']} §{l['act_section'] or ''}: {what}{note}")
        if rules:
            print(f"  implemented by {len(rules)} administrative rule section(s): " + ", ".join(r["citation"] for r in rules[:12]))
        if cb:
            print("  cited by: " + ", ".join(c["citation"] for c in cb if c["kind"] == "cites")[:600])
    if a.get("no_match"):
        print(f"  {a['no_match']}\n")
    if a.get("not_here"):
        n = a["not_here"]
        print(f"  {B}{n['citation']}{R} is not in this database.")
        if n.get("listed"):
            print(f"  {n['listed']}")
        print(f"  {n['how_to_get']}\n")
    if a.get("act"):
        x = a["act"]
        print(f"{B}Session Laws of {x['year']}, Act {x['act']}{R}  ({len(x['targets'])} entries in the Table of Disposition)")
        for t in x["targets"]:
            mark = " (R)" if t["repealed"] else (" (heading)" if t["heading_only"] else "")
            if t["kind"] == "omitted":
                print(f"  §{t['act_section'] or ''}  not codified (O)")
            else:
                here = t.get("citation") or f"{t['target']}  {D}not in this copy{R}" if t["kind"] == "section" else t["target"]
                print(f"  §{t['act_section'] or ''}  {here}{mark}  {t.get('heading') or ''}")
        print()
    if a.get("outline"):
        o = a["outline"]
        c = o["chapter"]
        print(f"{B}HRS chapter {c['chapter']}. {c['chapter_name']}{R}  [{c['status']}]")
        print(f"  Division {c['division']}. {c['division_name']} / Title {c['title']}. {c['title_name']}"
              + (f" / Subtitle {c['subtitle']}. {c['subtitle_name']}" if c["subtitle"] else ""))
        print(f"  {c['sections_here']} sections in this copy  {D}(official TOC page {c['page']}){R}")
        for p in o["parts"]:
            lab = {"part": f"Part {p['part']}.", "article": f"Article {p['article']}.", "subpart": f"  {p['part']}.",
                   "unnumbered": ""}.get(p["kind"], "")
            name = p["part_name"] or p["article_name"] or ""
            here = "" if not p["first_section"] else ("" if p["present"] else f"  {D}§{p['first_section']} not in this copy{R}")
            print(f"   {lab} {name}  {D}{p['first_section'] or ''} {'' if p['status'] == 'in_force' else '[' + p['status'] + ']'}{R}{here}")
        print()
    if a.get("gaps"):
        for k, v in a["gaps"].items():
            print(f"  {v:>6,}  {k}")
        print(f"\n{D}  details: hrs/COMPLETENESS.md and hrs/checks/*.csv{R}\n")
    for d in a.get("definitions", []):
        print(f"{B}{d['citation']}{R}  {d['heading']}\n{wrap(d['definition'])}\n{D}  source: {d['source_url']}{R}\n")
    for d in a.get("bodies", []):
        p_body(d)
    for step in a.get("appeal_path", []):
        n = step["next"]
        print(f"  {B}{step['name']}{R}")
        if n:
            print(f"    ↓ {n['relation'].replace('_', ' ')}  {D}{n['basis_cite']}: “{n['basis_quote']}”{R}")
    for x in a.get("access", []):
        print(f"{B}{x['record_kind']}{R}  {x['basis_cite']} {'✓' if x['verified'] else '✗'}\n  “{x['basis_quote']}”  {D}→ {x.get('body_name')}{R}\n")
    for r in a.get("rules", []):
        print(f"  {r['citation']}  {r.get('heading') or ''}  {D}{r['basis']}{R}")
    for c in a.get("cited_by", []):
        print(f"  {c['kind']:<11} {c['citation']}  {c.get('heading') or ''}")
    if a.get("structure"):
        p_structure(a["structure"])
    if "results" in a:
        p_results(a["results"])


def p_structure(st):
    s = st["structure"]
    print(f"{B}{s['name']}{R}  required by {s['basis_cite']}\n{D}  source: {s['source_url']}{R}")
    if s.get("note"):
        print(wrap(s["note"]))
    for p in st["parts"]:
        print(f"  {B}{p['label']:>8}{R}  {p['heading']}")
    print()


def p_tree(con, root=None, depth=0, max_depth=4, show_mined=False):
    rows = body_rows(con, "parent_id is ?" if root is None else "parent_id = ?", (root,))
    for b in rows:
        if b["origin"] == "mined" and not show_mined:
            continue
        mark = "" if b["verified"] else " ✗"
        print(f"{'  ' * depth}{'└ ' if depth else ''}{b['name']}  {D}{b.get('basis_cite') or ''}{mark}{R}")
        if depth < max_depth:
            p_tree(con, b["id"], depth + 1, max_depth, show_mined)


# ============================================================ records you add
def insert_records(con, path):
    """Insert one JSONL file of records. Each line: {id, kind, source_url, ...} (see README)."""
    n = 0
    for lineno, line in enumerate(open(path), 1):
        if not line.strip():
            continue
        r = json.loads(line)
        if not r.get("id") or not r.get("kind") or not r.get("source_url"):
            raise ValueError(f"{path}:{lineno}: every record needs id, kind and source_url")
        con.execute("""insert or replace into record(id,kind,jurisdiction,body_id,number,title,date,status,structure_id,text,meta,source_url,retrieved)
                       values (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (r["id"], r["kind"], r.get("jurisdiction"), r.get("body_id"), r.get("number"), r.get("title"), r.get("date"),
                     r.get("status"), r.get("structure_id"), r.get("text"), json.dumps(r.get("meta") or {}), r["source_url"], r.get("retrieved")))
        con.execute("delete from record_party where record_id = ?", (r["id"],))
        con.execute("delete from record_section where record_id = ?", (r["id"],))
        for p in r.get("parties", []):
            pid = p.get("id") or "party:" + re.sub(r"[^a-z0-9]+", "-", p["name"].lower()).strip("-")
            con.execute("insert or ignore into party values (?,?,?)", (pid, p["name"], p.get("kind")))
            con.execute("insert into record_party values (?,?,?)", (r["id"], pid, p.get("role")))
        for c in r.get("sections", []):
            row = con.execute("select id from section where cite_key = ?", ((keys_for_query(c) or [norm(c)])[0],)).fetchone()
            con.execute("insert into record_section values (?,?,?)", (r["id"], row[0] if row else c, "cited"))
        for i, part in enumerate(r.get("parts", []), 1):
            con.execute("insert or replace into record_part values (?,?,?,?,?,?)",
                        (r["id"], part.get("ord", i), part.get("label"), part.get("text"), part.get("page_from"), part.get("page_to")))
        con.execute("delete from record_file where record_id = ?", (r["id"],))
        for f in r.get("files", []):
            con.execute("insert or replace into source_file values (?,?,?,?,?,?,?,?,?)",
                        (f["sha256"], f["original_filename"], f["source_url"], f["retrieved"], f["size_bytes"], f.get("media_type"),
                         f.get("local_path"), f.get("page_count"), f.get("has_text_layer")))
            con.execute("insert or ignore into record_file values (?,?)", (r["id"], f["sha256"]))
        con.execute("delete from listing_entry where record_id = ?", (r["id"],))
        for e in r.get("listings", []):
            con.execute("insert or replace into listing_entry values (?,?,?,?,?,?)",
                        (e["source_page_url"], e["seen_on"], e["listing_order"], e["listing_title"], e.get("program"), r["id"]))
        n += 1
    con.execute("insert into record_fts(record_fts) values ('rebuild')")
    return n


def load_records(path):
    """Keep a copy under data/records/ (so rebuilds reload it) and insert it now."""
    import shutil
    src = Path(path).resolve()
    keep = DB_PATH.parent / "records"
    keep.mkdir(parents=True, exist_ok=True)
    if src.parent != keep:
        shutil.copy(src, keep / src.name)
    con = sqlite3.connect(DB_PATH)
    try:
        n = insert_records(con, keep / src.name)
    except ValueError as e:
        sys.exit(str(e))
    con.commit()
    print(f"loaded {n} records from {src.name}; kept in {keep} so rebuilds include them")


# ============================================================ web: one search bar
def serve(port):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    from urllib.parse import parse_qs, urlparse
    con = db()
    page = (HERE / "web" / "index.html").read_bytes()
    previous = (HERE / "web" / "previous.html").read_bytes()

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def send(self, code, body, ctype="application/json; charset=utf-8"):
            data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False, default=str).encode()
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            u = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            try:
                if u.path == "/":
                    return self.send(200, page, "text/html; charset=utf-8")
                if u.path == "/previous":
                    return self.send(200, previous, "text/html; charset=utf-8")
                if u.path == "/favicon.ico":
                    return self.send(204, b"", "image/x-icon")
                if u.path == "/api/q":
                    return self.send(200, answer(con, q.get("q", "")))
                if u.path == "/api/section":
                    row = con.execute("select * from section where id = ?", (q.get("id", ""),)).fetchone()
                    if not row:
                        return self.send(404, {"error": "not found"})
                    s = dict(row)
                    prev, nxt = neighbors(con, s)
                    return self.send(200, {"section": s, "prev": prev, "next": nxt, "defs": definitions(con, s)[:3],
                                           "session_laws": session_laws_for(con, s["id"]),
                                           "cites": cites_from(con, s["id"]), "cited_by": cited_by(con, s["id"]),
                                           "rules": implementing_rules(con, s["id"])})
                if u.path == "/api/body":
                    row = con.execute("select * from body where id = ?", (q.get("id", ""),)).fetchone()
                    return self.send(200, body_detail(con, dict(row)) if row else {"error": "not found"})
                if u.path == "/api/coverage":
                    return self.send(200, coverage(con))
                return self.send(404, {"error": "not found"})
            except Exception as e:
                return self.send(500, {"error": str(e)})

    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    print(f"hi: http://127.0.0.1:{port}  (local only; Ctrl-C to stop)")
    srv.serve_forever()


# ============================================================ MCP over stdio
MCP_TOOLS = [
    ("ask", "Answer a plain question or citation about Hawaii/federal law, government structure, or loaded records. Returns how the question was read and the matching material, each with its official source URL.", {"q": "string"}),
    ("search", "Full-text search. corpus: hrs har hi-const hi-rules hi-ag hi-guidance usc us-const fed-rules cfr records.", {"q": "string", "corpus": "string?", "include_repealed": "boolean?", "limit": "integer?"}),
    ("resolve_citation", "Resolve a citation as written (HRS 712-1200, HAR 16-12-1, HRCP 23, 42 USC 1983, Haw. Const. art. VI § 1) to the section.", {"citation": "string"}),
    ("read_section", "Full text of a section by id or citation, with neighbors, definitions sections, citations in and out, and implementing rules.", {"ref": "string"}),
    ("define", "Definitions of a term as written in the law.", {"term": "string"}),
    ("extract_citations", "Find and resolve every citation in a passage of text.", {"text": "string"}),
    ("government", "A part of government by name or id: what law creates it, what it belongs to, what belongs to it, and its links.", {"name": "string"}),
    ("appeal_path", "Where a decision goes next, step by step, with the law for each step. start: a court or agency name.", {"start": "string"}),
    ("public_access", "The laws that open records and meetings to the public.", {}),
    ("document_structure", "Layouts the law requires a document to follow, e.g. fdd (Franchise Disclosure Document).", {"id": "string?"}),
    ("coverage", "What the local database contains.", {}),
    ("hrs_chapter_outline", "The official outline of an HRS chapter (parts, articles, first sections) and which of its sections this database holds.", {"chapter": "string"}),
    ("session_law", "What a session law act changed in the HRS, from the official Table of Disposition (2025).", {"act": "integer", "year": "integer?"}),
    ("completeness", "How this copy of the HRS compares with the official Table of Contents and 2025 Table of Disposition.", {}),
]


def mcp_call(con, name, a):
    if name == "ask":
        return answer(con, a["q"])
    if name == "search":
        return search(con, a["q"], a.get("corpus"), a.get("include_repealed", False), int(a.get("limit", 15)))
    if name == "resolve_citation":
        return resolve(con, a["citation"])[:20]
    if name == "read_section":
        rows = resolve(con, a["ref"])
        if not rows:
            return {"error": "not found"}
        s = rows[0]
        prev, nxt = neighbors(con, s)
        return {"section": s, "prev": prev, "next": nxt, "definitions_sections": [d["citation"] for d in definitions(con, s)],
                "cites": cites_from(con, s["id"]), "cited_by": cited_by(con, s["id"]), "implementing_rules": implementing_rules(con, s["id"])}
    if name == "define":
        return define_term(con, a["term"])
    if name == "extract_citations":
        return extract_citations(con, a["text"])
    if name == "government":
        return [body_detail(con, b) for b in find_body(con, a["name"])[:5]]
    if name == "appeal_path":
        b = find_body(con, a["start"])[:1]
        return appeal_path(con, b[0]["id"]) if b else {"error": "no such court or agency in the map"}
    if name == "public_access":
        return [dict(r) for r in con.execute("select * from access_rule")]
    if name == "document_structure":
        return structure(con, a.get("id"))
    if name == "coverage":
        return coverage(con)
    if name == "hrs_chapter_outline":
        return outline(con, a["chapter"]) or {"error": "no such chapter in the HRS Table of Contents"}
    if name == "session_law":
        return session_law_act(con, int(a["act"]), int(a.get("year", 2025)))
    if name == "completeness":
        return gaps(con)
    raise ValueError(f"unknown tool {name}")


def mcp():
    con = db()

    def schema(props):
        return {"type": "object",
                "properties": {k: {"type": v.rstrip("?")} for k, v in props.items()},
                "required": [k for k, v in props.items() if not v.endswith("?")]}

    def reply(i, result=None, error=None):
        msg = {"jsonrpc": "2.0", "id": i}
        msg["error" if error else "result"] = error or result
        sys.stdout.write(json.dumps(msg, ensure_ascii=False, default=str) + "\n")
        sys.stdout.flush()

    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            m = json.loads(line)
        except json.JSONDecodeError:
            continue
        i, meth, params = m.get("id"), m.get("method"), m.get("params") or {}
        if i is None:
            continue
        if meth == "initialize":
            reply(i, {"protocolVersion": params.get("protocolVersion", "2025-06-18"),
                      "capabilities": {"tools": {}},
                      "serverInfo": {"name": "hi-local-law", "version": "1.0"},
                      "instructions": "Local Hawaii + federal law database. Every answer carries the official source_url. "
                                      "Nothing here is legal advice; it is the published text."})
        elif meth == "tools/list":
            reply(i, {"tools": [{"name": n, "description": d, "inputSchema": schema(p)} for n, d, p in MCP_TOOLS]})
        elif meth == "tools/call":
            try:
                res = mcp_call(con, params["name"], params.get("arguments") or {})
                reply(i, {"content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False, default=str)}]})
            except Exception as e:
                reply(i, {"content": [{"type": "text", "text": f"error: {e}"}], "isError": True})
        elif meth == "ping":
            reply(i, {})
        else:
            reply(i, error={"code": -32601, "message": f"method not found: {meth}"})


# ============================================================ CLI
def main(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(__doc__)
        return
    cmd, rest = argv[0], argv[1:]
    opts = {"in": None, "all": False, "n": 15, "port": 8808}
    args = []
    i = 0
    while i < len(rest):
        a = rest[i]
        if a == "--in":
            opts["in"] = rest[i + 1]; i += 2; continue
        if a == "--all":
            opts["all"] = True; i += 1; continue
        if a == "-n":
            opts["n"] = int(rest[i + 1]); i += 2; continue
        if a == "--port":
            opts["port"] = int(rest[i + 1]); i += 2; continue
        args.append(a); i += 1
    text = " ".join(args)
    if cmd == "serve":
        return serve(opts["port"])
    if cmd == "mcp":
        return mcp()
    if cmd == "load":
        return load_records(text)
    con = db()
    text = re.sub(r"^(?:for|of|under|implementing|to|by)\s+", "", text, flags=re.I)
    if cmd == "find":
        return p_results(search(con, text, opts["in"], opts["all"], opts["n"]))
    if cmd in ("read", "near", "defs", "citedby", "rules"):
        rows = resolve(con, text)
        if not rows:
            print(f"  no section matches “{text}”"); return
        s = rows[0]
        if cmd == "read":
            for r in rows[:50]:
                p_section(r)
        elif cmd == "near":
            prev, nxt = neighbors(con, s)
            for x in (prev, s, nxt):
                if x:
                    print(f"  {B if x is s else ''}{x['citation']}{R if x is s else ''}  {x.get('heading') or ''}")
        elif cmd == "defs":
            for d in definitions(con, s):
                p_section(d)
            if not definitions(con, s):
                print("  no definitions section in this chapter")
        elif cmd == "citedby":
            for c in cited_by(con, s["id"], 500):
                print(f"  {c['kind']:<11} {c['citation']}  {c.get('heading') or ''}")
        elif cmd == "rules":
            for r in implementing_rules(con, s["id"]):
                print(f"  {r['citation']}  {r.get('heading') or ''}  {D}{r['basis']}{R}")
        return
    if cmd == "cites":
        body = Path(text[1:]).read_text() if text.startswith("@") else text
        for c in extract_citations(con, body):
            print(f"  {c.get('citation')}  {c.get('heading') or ''}  {D}{c.get('status') or ''}{R}")
        return
    if cmd == "browse":
        if not args:
            for c in coverage(con)["corpora"]:
                print(f"  {c['id']:<12} {c['name']}  ({c['sections']})")
        elif len(args) == 1:
            for r in con.execute("""select coalesce(chapter, title_name, title_number) g, count(*) n, max(chapter_name) from section
                                    where corpus=? group by g order by cast(g as integer), g""", (args[0],)):
                print(f"  {r[0] or '':<10} {r[2] or ''}  ({r[1]})")
        else:
            for r in con.execute("""select citation, heading, status from section where corpus=?
                                    and coalesce(chapter, title_name, title_number)=? order by ord""", (args[0], " ".join(args[1:]))):
                print(f"  {r[0]}  {r[1] or ''}{'' if (r[2] or 'in_force') == 'in_force' else '  [' + r[2] + ']'}")
        return
    if cmd == "map":
        if text:
            for b in find_body(con, text)[:5]:
                p_body(body_detail(con, b))
        else:
            p_tree(con, None)
            print(f"\n{D}✗ = the quoted words were not found in that provision. `hi map <name>` for detail; "
                  f"mined bodies: map/bodies_mined.csv{R}")
        return
    if cmd == "act":
        return p_answer(answer(con, "act " + text), con)
    if cmd in ("chapter", "outline"):
        return p_answer(answer(con, "chapter " + text), con)
    if cmd == "gaps":
        return p_answer(answer(con, "gaps"), con)
    if cmd == "access":
        return p_answer(answer(con, "public records"), con)
    if cmd == "structure":
        if text:
            st = structure(con, text)
            if not st:
                print(f"  no structure “{text}”"); return
            p_structure(st)
            if "-v" in argv:
                for p in st["parts"]:
                    print(f"{B}{p['label']}: {p['heading']}{R}\n{wrap(p['text'])}\n")
        else:
            for s in structure(con):
                print(f"  {s['id']:<8} {s['name']}  ({s['basis_cite']})")
        return
    if cmd == "coverage":
        c = coverage(con)
        for x in c["corpora"]:
            print(f"  {x['id']:<12} {x['sections']:>7}  {x['name']}  {D}{x['provenance']}{R}")
        h = c["har_chapters"]
        print(f"  HAR directory: {h['listed']} chapters listed, {h['active']} active, {h['with_text'] or 0} with text collected")
        print(f"  cross-references: " + ", ".join(f"{k} {n} ({r} resolved)" for k, n, r in c["refs"]))
        print(f"  government map: " + ", ".join(f"{o} {n} ({v} verified)" for o, n, v in c["bodies"]))
        print(f"  your records: " + (", ".join(f"{k} {n}" for k, n in c["records"]) or "none loaded yet"))
        return
    return p_answer(answer(con, " ".join(argv)), con)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except BrokenPipeError:
        pass
