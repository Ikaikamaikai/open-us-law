# Usage: python build_database_2026-10-18.py --laws <folder with the us_hi_*.parquet files> --pdfs <folder made by the download script> --out <new database file, e.g. hawaii-public-info_2026-10-18.duckdb>
# Builds the local database from the schema, then re-checks every count, size and SHA-256 fingerprint. Needs: pip install duckdb
import argparse, csv, glob, hashlib, html, os, re, sys, urllib.parse
from datetime import date
import duckdb

LAW_FILES = ["us_hi_statutes", "us_hi_court_rules", "us_hi_ag_opinion", "us_hi_guidance", "us_hi_constitutions"]
LAW_COLUMNS = ["act_id", "citation", "citation_short", "state", "jurisdiction", "document_type", "title_number", "title_name",
               "chapter", "chapter_name", "section_number", "section_title", "breadcrumb", "display_path", "act_status", "text",
               "word_count", "source_url", "last_amended_year", "subsection_count", "cross_references_usc", "cross_references_cfr",
               "public_laws_referenced", "year", "official_status", "currency_note"]
STATE_SITE = "https://web3.dcca.hawaii.gov"
SEARCH_PAGE = STATE_SITE + "/oah/public/result?search=&cat=All"

ap = argparse.ArgumentParser()
ap.add_argument("--laws", required=True)
ap.add_argument("--pdfs", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--schema", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "schema", "hawaii-public-info-schema_2026-10-18.sql"))
a = ap.parse_args()
if os.path.exists(a.out):
    sys.exit(f"{a.out} already exists. Nothing was changed. Give the new database a new name.")

report, problems = [], []
def note(line):
    print(line); report.append(line)

con = duckdb.connect(a.out)
con.execute(open(a.schema, encoding="utf-8").read())
note(f"Database: {os.path.abspath(a.out)}")
note(f"Schema: {os.path.abspath(a.schema)}")
note(f"Built on: {date.today().isoformat()}")

note("\n== Laws (Open US Law v2026.09.1 files)")
for name in LAW_FILES:
    path = os.path.join(a.laws, name + ".parquet")
    if not os.path.exists(path):
        problems.append(f"missing law file {path}"); note(f"MISSING {path}"); continue
    in_file = con.execute("select count(*) from read_parquet(?)", [path]).fetchone()[0]
    before = con.execute("select count(*) from law_sections").fetchone()[0]
    con.execute(f"""insert into law_sections select {', '.join(LAW_COLUMNS)},
        case when adopting_citations is null then null else to_json(adopting_citations)::varchar end,
        'Vaquill Open US Law v2026.09.1', DATE '2026-09-30', NULL from read_parquet(?)""", [path])
    loaded = con.execute("select count(*) from law_sections").fetchone()[0] - before
    note(f"{name}: {loaded} of {in_file} rows loaded")
    if loaded != in_file: problems.append(f"{name}: loaded {loaded} of {in_file}")

note("\n== OAH search page snapshots")
snapshots = sorted(glob.glob(os.path.join(a.pdfs, "hi-dcca-oah-search-page-snapshot_*.html")))
if not snapshots: problems.append("no search page snapshot found in --pdfs folder")
for snap in snapshots:
    seen_on = re.search(r"_(\d{4}-\d{2}-\d{2})\.html$", snap).group(1)
    page = open(snap, encoding="utf-8", errors="replace").read()
    rows = re.findall(r'<tr tabindex="0">(.*?)</tr>', page, re.S)
    for i, r in enumerate(rows, 1):
        fname = html.unescape(re.search(r'href="/oah/public/docs/([^"]+)"', r).group(1))
        title = html.unescape(re.search(r"<h5>(.*?)</h5>", r, re.S).group(1)).strip()
        program = html.unescape(re.sub(r"<[^>]+>", "", r.split("PDF_24.png")[-1].split(">", 1)[-1])).strip()
        con.execute("insert into oah_listing_entries values (?,?,?,?,?,?)", [seen_on, i, title, program, fname, SEARCH_PAGE])
    links = len(re.findall(r'<a href="/oah/public/docs/[^"]+" target="_blank">\s*<h5>', page))
    note(f"{os.path.basename(snap)}: {len(rows)} entries read, {links} entries on the page")
    if len(rows) != links: problems.append(f"{os.path.basename(snap)}: read {len(rows)} of {links} entries")
con.execute(f"""insert into oah_decisions (pdf_filename, pdf_url, listing_title, first_seen_on)
    select pdf_filename, '{STATE_SITE}/oah/public/docs/' || pdf_filename, min_by(listing_title, seen_on), min(seen_on)
    from oah_listing_entries group by pdf_filename""")
for (fname,) in con.execute("select pdf_filename from oah_decisions").fetchall():
    con.execute("update oah_decisions set pdf_url=? where pdf_filename=?", [f"{STATE_SITE}/oah/public/docs/{urllib.parse.quote(fname)}", fname])
listed = con.execute("select count(*) from oah_decisions").fetchone()[0]
note(f"Distinct PDFs listed: {listed}")

note("\n== Downloaded PDFs (checked against the manifest)")
manifest = os.path.join(a.pdfs, "hi-dcca-oah-pdf-manifest.csv")
latest = {}
for row in csv.DictReader(open(manifest, encoding="utf-8")) if os.path.exists(manifest) else []:
    latest[row["pdf_filename"]] = row
if not os.path.exists(manifest): problems.append("manifest not found in --pdfs folder")
verified = 0
for fname, row in latest.items():
    path = os.path.join(a.pdfs, fname)
    if not os.path.exists(path):
        problems.append(f"in manifest but not in folder: {fname}"); continue
    data = open(path, "rb").read()
    sha = hashlib.sha256(data).hexdigest()
    if len(data) != int(row["size_bytes"]) or sha != row["sha256"]:
        problems.append(f"file changed since download (size or fingerprint differs): {fname}"); continue
    if not con.execute("select 1 from oah_decisions where pdf_filename=?", [fname]).fetchone():
        problems.append(f"downloaded but not on any saved search page: {fname}"); continue
    con.execute("insert into source_files values (?,?,?,?,?,?,?,?,?,?,?)",
        [sha, fname, row["source_url"], "Hawaii DCCA Office of Administrative Hearings", row["retrieved_on"], len(data), "application/pdf", fname, None, None, None])
    con.execute("update oah_decisions set source_file_sha256=? where pdf_filename=?", [sha, fname])
    verified += 1
note(f"PDFs verified (size and fingerprint match the manifest): {verified} of {len(latest)} in the manifest")

recorded = set()
for p in glob.glob(os.path.join(a.pdfs, "hi-dcca-oah-pdf-download-problems_*.txt")):
    for line in open(p, encoding="utf-8", errors="replace"):
        if line.strip(): recorded.add(line.split("  (")[0].strip())
missing = [r[0] for r in con.execute("select pdf_filename from oah_decisions where source_file_sha256 is null order by 1").fetchall()]
note(f"Listed PDFs not downloaded: {len(missing)}")
for m in missing:
    known = m in recorded
    note(f"  {m}  ({'recorded in the download problems file' if known else 'NOT recorded anywhere'})")
    if not known: problems.append(f"not downloaded and not recorded: {m}")

note("\n== Result")
if problems:
    note(f"CHECKS FAILED: {len(problems)} problem(s)")
    for p in problems[:200]: note(f"  - {p}")
else:
    note("ALL CHECKS PASSED")
con.close()
rep = os.path.splitext(a.out)[0] + f"_build-report_{date.today().isoformat()}.txt"
open(rep, "w", encoding="utf-8").write("\n".join(report) + "\n")
print(f"\nReport saved: {rep}")
sys.exit(1 if problems else 0)
