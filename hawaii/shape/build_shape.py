#!/usr/bin/env python3
"""The shape of everything: each body of law and each set of public records, starting at home in Hawaii and going
outward, with how much of it is here.

  python3 shape/build_shape.py            writes shape/shape.json, shape/SHAPE.md and web/index.html
  python3 shape/build_shape.py --recount  first re-reads the open dataset's row counts (needs the network and duckdb)

What is here is counted from data/hawaii.db. What the open dataset holds is counted from its own files
(shape/dataset_rows.json: the row count in each parquet file's footer). Sources outside the dataset are listed with
their publisher and are counted when they are collected. Nothing is estimated.

web/index.html is web/page.html with the fonts in web/fonts/ and this data put inside it, so the page works when it
is opened as a file, with no server and no network.
"""
import base64
import datetime
import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
DB = HERE / "data" / "hawaii.db"
ROWS = HERE / "shape" / "dataset_rows.json"
WEB = HERE / "web"

STATES = {
    "ak": "Alaska", "al": "Alabama", "ar": "Arkansas", "az": "Arizona", "ca": "California", "co": "Colorado",
    "ct": "Connecticut", "dc": "District of Columbia", "de": "Delaware", "fl": "Florida", "ga": "Georgia",
    "ia": "Iowa", "id": "Idaho", "il": "Illinois", "in": "Indiana", "ks": "Kansas", "ky": "Kentucky",
    "la": "Louisiana", "ma": "Massachusetts", "md": "Maryland", "me": "Maine", "mi": "Michigan", "mn": "Minnesota",
    "mo": "Missouri", "ms": "Mississippi", "mt": "Montana", "nc": "North Carolina", "nd": "North Dakota",
    "ne": "Nebraska", "nh": "New Hampshire", "nj": "New Jersey", "nm": "New Mexico", "nv": "Nevada",
    "ny": "New York", "oh": "Ohio", "ok": "Oklahoma", "or": "Oregon", "pa": "Pennsylvania", "pr": "Puerto Rico",
    "ri": "Rhode Island", "sc": "South Carolina", "sd": "South Dakota", "tn": "Tennessee", "tx": "Texas",
    "ut": "Utah", "va": "Virginia", "vt": "Vermont", "wa": "Washington", "wi": "Wisconsin", "wv": "West Virginia",
    "wy": "Wyoming",
}
KIND = {
    "constitutions": "Constitution", "statutes": "Statutes", "regulations": "Regulations", "court_rules": "Court rules",
    "ag_opinion": "Attorney General opinions", "guidance": "Agency guidance",
    "adjudication": "Agency adjudications", "administrative_guidance": "Administrative guidance",
    "bia_precedent_decision": "Board of Immigration Appeals precedent decisions", "board_decision": "Board decisions",
    "cfpb_enforcement_action": "CFPB enforcement actions", "cfr_annual": "Code of Federal Regulations, annual edition",
    "enforcement_action": "Enforcement actions", "executive_order": "Executive orders", "faq": "Agency FAQs",
    "ftc_administrative_decision": "FTC administrative decisions", "guideline": "Guidelines",
    "irs_announcement": "IRS announcements", "irs_notice": "IRS notices", "irs_rev_proc": "IRS revenue procedures",
    "irs_rev_rul": "IRS revenue rulings", "irs_written_determination": "IRS written determinations",
    "memorandum": "Memoranda", "mspb_decision": "Merit Systems Protection Board decisions", "notice": "Notices",
    "presidential_document": "Presidential documents", "private_law": "Private laws", "proclamation": "Proclamations",
    "proposed_regulation": "Proposed regulations", "resolution": "Resolutions", "ruling": "Rulings",
    "sec_adjudication": "SEC adjudications", "session_law": "Session laws", "statute_compilation": "Statute compilations",
    "treaty": "Treaties",
}
FEDERAL_NAMES = {"constitutions": "U.S. Constitution", "statutes": "United States Code",
                 "court_rules": "Federal court rules", "regulations": "Code of Federal Regulations"}
FONTS = [("DraftingMono-Light.woff2", 300, "normal"), ("DraftingMono-Regular.woff2", 400, "normal"),
         ("DraftingMono-Italic.woff2", 400, "italic"), ("DraftingMono-SemiBold.woff2", 600, "normal")]


def leaf(name, status, have=None, of=None, unit="sections", note=None, url=None, url_note=None, how=None, file=None):
    """status: done (all of it is here), part (some is here), ready (one step away), todo (not started)."""
    return {k: v for k, v in dict(name=name, status=status, have=have, of=of, unit=unit, note=note, url=url,
                                  url_note=url_note, how=how, file=file).items() if v is not None}


def group(name, children, note=None):
    g = {"name": name, "children": children}
    if note:
        g["note"] = note
    return g


def lines(path):
    with open(path, encoding="utf-8") as f:
        return sum(1 for _ in f) - 1


def recount():
    """Read every file's row count from its parquet footer (one small ranged request per file)."""
    import concurrent.futures as cf
    import urllib.request
    import duckdb
    src = json.loads((HERE / "sources.json").read_text())
    with urllib.request.urlopen(urllib.request.Request(src["base_url"] + "/index.json",
                                                       headers={"User-Agent": "Mozilla/5.0"}), timeout=60) as r:
        idx = json.load(r)
    files = [f for f in idx["files"] if f["file"].endswith(".parquet")]

    def rows(f):
        con = duckdb.connect()
        con.execute("load httpfs")
        return f["file"], con.execute("select sum(num_rows) from parquet_file_metadata(?)", [f["url"]]).fetchone()[0]

    with cf.ThreadPoolExecutor(16) as ex:
        counted = dict(ex.map(rows, files))
    ROWS.write_text(json.dumps({
        "dataset": idx["dataset"], "snapshot": idx["version"], "snapshot_date": idx["snapshot_date"],
        "index_url": src["base_url"] + "/index.json", "counted_on": datetime.date.today().isoformat(),
        "how_counted": "num_rows from each parquet file's footer (duckdb parquet_file_metadata over HTTPS)",
        "files": {f["file"]: {"rows": counted[f["file"]], "bytes": f["bytes"]} for f in files}}, indent=1))


def build(con, ds):
    rows = lambda f: ds["files"].get(f, {}).get("rows")
    one = lambda sql, *a: con.execute(sql, a).fetchone()
    n = dict(con.execute("select corpus, count(*) from section group by corpus").fetchall())
    har_all, har_repealed, har_text = one("select count(*), sum(repealed), sum(have_text > 0) from har_chapter")
    acts, entries = one("select count(distinct act), count(*) from session_law where year = 2025")
    spine, mined = (one("select count(*) from body where origin = ?", o)[0] for o in ("spine", "mined"))
    links, access = one("select count(*) from link")[0], one("select count(*) from access_rule")[0]
    fdd = one("select count(*) from structure_part where structure_id = 'fdd'")[0]
    records = one("select count(*) from record")[0]
    server_pages = lines(HERE / "hrs" / "server_sections.csv")
    hrs_to_har = lines(HERE / "har" / "hrs_to_har.csv")
    from_dataset = rows("us_hi_statutes.parquet")
    dataset_url = ds["index_url"].replace("index.json", "index.html")

    state_law = group("State law", [
        leaf("Constitution of the State of Hawaii", "done", n.get("hi-const"), rows("us_hi_constitutions.parquet"),
             file="us_hi_constitutions.parquet"),
        group("Hawaii Revised Statutes", [
            leaf("Sections", "done", n.get("hrs"), None,
                 note=f"Checked against all {server_pages:,} section pages on the Legislature's server; every one is "
                      f"here except one empty [RESERVED] page. {from_dataset:,} came from the open dataset, the rest "
                      f"from the Legislature's server. Details: hrs/COMPLETENESS.md",
                 url="https://data.capitol.hawaii.gov/hrscurrent/", how="python3 hrs/fill_missing.py --all"),
            leaf("Chapters in the official Table of Contents (Feb. 10, 2025)", "done",
                 one("select count(*) from hrs_chapter")[0], unit="chapters"),
            leaf("Parts, subparts and articles", "done", one("select count(*) from hrs_part")[0], unit="parts"),
        ]),
        group("Session Laws of Hawaii", [
            leaf("2025 Table of Disposition: what each act changed", "done", entries, unit="entries",
                 note=f"{acts:,} acts of 2025. Earlier years' tables are not loaded.", file="hrs/slh_disposition.csv"),
            leaf("Text of the acts", "todo", unit="acts", url="https://lrb.hawaii.gov/",
                 note="Published by the Legislature and the Legislative Reference Bureau."),
        ]),
        leaf("Hawaii Administrative Rules: text", "part", har_text, har_all - har_repealed, unit="active chapters",
             note=f"{n.get('har', 0):,} rule sections of text. The LRB directory lists {har_all:,} chapters "
                  f"({har_repealed:,} repealed) and {hrs_to_har:,} links from statutes to the rules that implement them.",
             url="https://ltgov.hawaii.gov/the-office/administrative-rules/", how="python3 har/scrape_har.py data/har"),
        leaf("Hawaii court rules", "done", n.get("hi-rules"), rows("us_hi_court_rules.parquet"),
             note="31 rule sets.", file="us_hi_court_rules.parquet"),
        leaf("Attorney General opinions", "done", n.get("hi-ag"), rows("us_hi_ag_opinion.parquet"), unit="opinions",
             note="Every opinion in the open dataset. The Department's older opinions are not counted here.",
             file="us_hi_ag_opinion.parquet"),
        leaf("Insurance Division memoranda", "done", n.get("hi-guidance"), rows("us_hi_guidance.parquet"),
             unit="memoranda", file="us_hi_guidance.parquet"),
        leaf("Appellate opinions (Supreme Court, Intermediate Court of Appeals)", "todo", unit="opinions",
             url="https://www.courtlistener.com/?type=o&court=haw",
             note="Not in the open dataset. On CourtListener: court=haw (Supreme Court) and court=hawapp (ICA).",
             url_note="The Judiciary's own site, courts.state.hi.us, refused requests from the machine that built this."),
        leaf("Office of Information Practices opinions", "todo", unit="opinions",
             url="https://oip.hawaii.gov/laws-rules-opinions/opinions/"),
        leaf("State Ethics Commission opinions", "todo", unit="opinions", url="https://ethics.hawaii.gov/"),
        leaf("Governor's executive orders and proclamations", "todo", unit="documents", url="https://governor.hawaii.gov/"),
        group("Agency decisions", [
            leaf("DCCA Office of Administrative Hearings decisions", "ready", None, 2970, unit="decision PDFs",
                 note="3,030 entries on the state's search page point to 2,970 PDFs (read 2026-10-18). "
                      "The downloader is ready and runs on Windows.",
                 url="https://web3.dcca.hawaii.gov/oah/public/result?search=&cat=All",
                 how="powershell -ExecutionPolicy Bypass -File oah/download-hi-dcca-oah-pdfs_2026-10-18.ps1"),
            leaf("Public Utilities Commission dockets and decisions", "todo", unit="documents",
                 url="https://puc.hawaii.gov/"),
            leaf("Land Use Commission decisions", "todo", unit="documents", url="https://luc.hawaii.gov/"),
        ]),
    ])
    government = group("Government of Hawaii", [
        leaf("Parts of government, each tied to the law that creates it", "done", spine, spine, unit="parts",
             note="Every quote was found in the cited law when the database was built. Shown in map/GOVERNMENT.md."),
        leaf("Boards and commissions found in the statutes' own words", "done", mined, unit="bodies",
             note="Each keeps the exact sentence that creates it.", file="map/bodies_mined.csv"),
        leaf("Legal links between parts (appeals, supervision, appointment)", "done", links, unit="links"),
        leaf("Laws that open records and meetings to the public", "done", access, unit="laws"),
    ])
    counties = group("Counties", [
        leaf("City and County of Honolulu: Revised Ordinances of Honolulu", "todo", unit="sections",
             url="https://www.honolulu.gov/ocs/", note="The Office of Council Services is the revisor of the ROH."),
        leaf("County of Hawaii: Hawaii County Code", "todo", unit="sections", note="Published by the County of Hawaii."),
        leaf("County of Maui: Maui County Code", "todo", unit="sections", note="Published by the County of Maui."),
        leaf("County of Kauai: Kauai County Code", "todo", unit="sections", note="Published by the County of Kauai."),
    ])
    public_records = group("Public records", [
        leaf("Your records", "ready" if not records else "part", records, unit="records",
             note="Court records, filings, parcels and documents you collect, stored as published.",
             how="python3 hi.py load <file.jsonl>   (format: README.md, Add your records)"),
        leaf("Franchise Disclosure Document layout", "done", fdd, 23, unit="items",
             note="The 23 items 16 C.F.R. § 436.5 requires, read from the rule itself."),
        leaf("Court dockets (Judiciary, eCourt Kokua)", "todo", unit="cases", note="Published by the Hawaii State Judiciary."),
        leaf("Real property records: Honolulu", "todo", unit="parcels", url="https://www.qpublic.net/hi/honolulu/"),
        leaf("Real property records: Hawaii, Maui and Kauai counties", "todo", unit="parcels",
             note="Published by each county."),
        leaf("Land records: Bureau of Conveyances", "todo", unit="documents", url="https://dlnr.hawaii.gov/boc/"),
        leaf("Business registrations (DCCA Business Registration Division)", "todo", unit="entities",
             note="Published by the Department of Commerce and Consumer Affairs."),
    ])
    hawaii = group("Hawaii", [state_law, government, counties, public_records], note="Home. Everything starts here.")

    fed_files = sorted(f for f in ds["files"] if f.startswith("us_federal_"))
    loaded = {"us_federal_constitutions.parquet": "us-const", "us_federal_statutes.parquet": "usc",
              "us_federal_court_rules.parquet": "fed-rules"}
    here_now = [leaf(FEDERAL_NAMES[f[11:-8]], "done", n.get(c), rows(f), file=f) for f, c in loaded.items()]
    here_now.append(leaf("Code of Federal Regulations", "part", n.get("cfr"), rows("us_federal_regulations.parquet"),
                         note="Only 16 C.F.R. Part 436 (the FTC Franchise Rule) so far. Add a part with one line in "
                              "sources.json (cfr_slices), then python3 fetch.py and python3 build.py.",
                         file="us_federal_regulations.parquet"))
    in_dataset = [leaf(KIND.get(f[11:-8], f[11:-8]), "ready", None, rows(f), file=f, url=dataset_url)
                  for f in fed_files if f not in loaded and f != "us_federal_regulations.parquet"]
    federal = group("United States", [
        group("Here now", here_now),
        group("In the open dataset, not pulled yet", in_dataset,
              note="Each is one file of the open dataset. They are pulled the way the files above were: "
                   "sources.json, then fetch.py and build.py."),
        leaf("Federal court opinions (Supreme Court, Ninth Circuit, District of Hawaii)", "todo", unit="opinions",
             url="https://www.courtlistener.com/", note="Not in the open dataset."),
    ])

    others = []
    for code, name in sorted(STATES.items(), key=lambda kv: kv[1]):
        files = sorted(f for f in ds["files"] if f.startswith(f"us_{code}_"))
        if files:
            others.append(group(name, [leaf(KIND.get(f[len(code) + 4:-8], f[len(code) + 4:-8]), "ready", None,
                                            rows(f), file=f) for f in files]))
    outward = group("Other states and territories", others,
                    note="Everything the open dataset holds for each jurisdiction. Not pulled yet.")
    return [hawaii, federal, outward]


def rollup(node):
    """Count leaves by status and add up what is here, for every group."""
    if "children" not in node:
        return {node["status"]: 1}, node.get("have") or 0
    tally, have = {}, 0
    for c in node["children"]:
        t, h = rollup(c)
        have += h
        for k, v in t.items():
            tally[k] = tally.get(k, 0) + v
    node["tally"], node["have_total"] = tally, have
    return tally, have


MARK = {"done": "[x]", "part": "[ ] ◐", "ready": "[ ] ↓", "todo": "[ ] ○"}


def amount(n):
    have, of, unit = n.get("have"), n.get("of"), n.get("unit", "")
    if have is not None and of is not None:
        return f"{have:,} of {of:,} {unit}"
    if have is not None:
        return f"{have:,} {unit}"
    if of is not None:
        return f"{of:,} {unit} published"
    return f"{unit}: counted when collected"


def markdown(shape):
    out = ["# The shape of everything", "",
           f"Every body of law and set of public records, starting at home in Hawaii and going outward. "
           f"Counted {shape['generated']} from data/hawaii.db and the open-us-law {shape['dataset']['snapshot']} index.", "",
           "[x] here, complete · ◐ here in part · ↓ ready: one step away · ○ not started", ""]

    def walk(node, depth):
        if "children" in node:
            t = node["tally"]
            done, total = t.get("done", 0), sum(t.values())
            out.append(f"{'#' * min(depth + 2, 6)} {node['name']}  ({done} of {total} checked off)" if depth < 2
                       else f"{'  ' * (depth - 2)}- **{node['name']}** ({done} of {total} checked off)")
            if node.get("note") and depth < 2:
                out.extend([node["note"], ""])
            for c in node["children"]:
                walk(c, depth + 1)
            if depth < 2:
                out.append("")
            return
        bits = [amount(node)]
        if node.get("note"):
            bits.append(node["note"])
        if node.get("url"):
            bits.append(node["url"])
        if node.get("how"):
            bits.append(f"`{node['how']}`")
        if node.get("file"):
            bits.append(f"file: {node['file']}")
        out.append(f"{'  ' * max(depth - 2, 0)}- {MARK[node['status']]} {node['name']}: " + " · ".join(bits))

    for top in shape["tree"]:
        walk(top, 0)
    return "\n".join(out) + "\n"


def page(shape):
    """web/page.html + embedded fonts + embedded shape = web/index.html (one file, works offline)."""
    faces = []
    for f, weight, style in FONTS:
        p = WEB / "fonts" / f
        if p.exists():
            b64 = base64.b64encode(p.read_bytes()).decode()
            faces.append(f'@font-face{{font-family:"Drafting Mono";src:url(data:font/woff2;base64,{b64}) format("woff2");'
                         f'font-weight:{weight};font-style:{style};font-display:swap}}')
    html = (WEB / "page.html").read_text(encoding="utf-8")
    data = json.dumps(shape, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = html.replace("/*@fonts*/", "\n".join(faces), 1)
    html = html.replace('<script id="shape-data" type="application/json"></script>',
                        f'<script id="shape-data" type="application/json">{data}</script>', 1)
    (WEB / "index.html").write_text(html, encoding="utf-8")


def main():
    if "--recount" in sys.argv:
        recount()
    ds = json.loads(ROWS.read_text())
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    tree = build(con, ds)
    for top in tree:
        rollup(top)
    shape = {"generated": datetime.date.today().isoformat(), "tree": tree,
             "dataset": {k: ds[k] for k in ("dataset", "snapshot", "snapshot_date", "index_url", "counted_on")}}
    (HERE / "shape" / "shape.json").write_text(json.dumps(shape, ensure_ascii=False, indent=1), encoding="utf-8")
    (HERE / "shape" / "SHAPE.md").write_text(markdown(shape), encoding="utf-8")
    page(shape)
    for top in tree:
        t = top["tally"]
        print(f"{top['name']:<30} here: {top['have_total']:>9,}   " + "  ".join(f"{k} {v}" for k, v in sorted(t.items())))
    print("wrote shape/shape.json, shape/SHAPE.md, web/index.html")


if __name__ == "__main__":
    main()
