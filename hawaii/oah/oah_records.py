# Usage: python oah_records.py --pdfs <folder made by download-hi-dcca-oah-pdfs_2026-10-18.ps1> --out <new .jsonl, e.g. ../data/records/hi-dcca-oah-decisions_2026-10-18.jsonl>
# Turns the saved OAH search page(s) and the downloaded PDFs into records for `hi.py load` / build.py,
# after re-checking every PDF's size and SHA-256 against the download manifest. Writes a dated report.
import argparse, csv, glob, hashlib, html, json, os, re, sys, urllib.parse
from datetime import date

STATE_SITE = "https://web3.dcca.hawaii.gov"
SEARCH_PAGE = STATE_SITE + "/oah/public/result?search=&cat=All"
BODY_ID = "hi.exec.dept.26-9"  # Department of Commerce and Consumer Affairs, as printed in every decision caption

ap = argparse.ArgumentParser()
ap.add_argument("--pdfs", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()
if os.path.exists(a.out):
    sys.exit(f"{a.out} already exists. Nothing was changed. Give the new file a new name.")

report, problems = [], []
def note(line):
    print(line); report.append(line)

note(f"Made on: {date.today().isoformat()}")
note(f"PDF folder: {os.path.abspath(a.pdfs)}")

listings = {}
snapshots = sorted(glob.glob(os.path.join(a.pdfs, "hi-dcca-oah-search-page-snapshot_*.html")))
if not snapshots: problems.append("no search page snapshot found in the PDF folder")
for snap in snapshots:
    seen_on = re.search(r"_(\d{4}-\d{2}-\d{2})\.html$", snap).group(1)
    page = open(snap, encoding="utf-8", errors="replace").read()
    rows = re.findall(r'<tr tabindex="0">(.*?)</tr>', page, re.S)
    for i, r in enumerate(rows, 1):
        name = html.unescape(re.search(r'href="/oah/public/docs/([^"]+)"', r).group(1))
        title = html.unescape(re.search(r"<h5>(.*?)</h5>", r, re.S).group(1)).strip()
        program = html.unescape(re.sub(r"<[^>]+>", "", r.split("PDF_24.png")[-1].split(">", 1)[-1])).strip()
        listings.setdefault(name, []).append({"source_page_url": SEARCH_PAGE, "seen_on": seen_on, "listing_order": i,
                                              "listing_title": title, "program": program})
    on_page = len(re.findall(r'<a href="/oah/public/docs/[^"]+" target="_blank">\s*<h5>', page))
    note(f"{os.path.basename(snap)}: {len(rows)} entries read, {on_page} entries on the page")
    if len(rows) != on_page: problems.append(f"{os.path.basename(snap)}: read {len(rows)} of {on_page} entries")
note(f"Distinct PDFs listed: {len(listings)}")

manifest = os.path.join(a.pdfs, "hi-dcca-oah-pdf-manifest.csv")
latest = {}
if os.path.exists(manifest):
    for row in csv.DictReader(open(manifest, encoding="utf-8")):
        latest[row["pdf_filename"]] = row
else:
    problems.append("download manifest not found in the PDF folder")
files = {}
for name, row in latest.items():
    path = os.path.join(a.pdfs, name)
    if not os.path.exists(path):
        problems.append(f"in the manifest but not in the folder: {name}"); continue
    data = open(path, "rb").read()
    sha = hashlib.sha256(data).hexdigest()
    if len(data) != int(row["size_bytes"]) or sha != row["sha256"]:
        problems.append(f"file changed since download (size or fingerprint differs): {name}"); continue
    if name not in listings:
        problems.append(f"downloaded but not on any saved search page: {name}"); continue
    files[name] = {"sha256": sha, "original_filename": name, "source_url": row["source_url"], "retrieved": row["retrieved_on"],
                   "size_bytes": len(data), "media_type": "application/pdf", "local_path": name}
note(f"PDFs verified (size and fingerprint match the manifest): {len(files)} of {len(latest)} in the manifest")

recorded = set()
for p in glob.glob(os.path.join(a.pdfs, "hi-dcca-oah-pdf-download-problems_*.txt")):
    for line in open(p, encoding="utf-8", errors="replace"):
        if line.strip(): recorded.add(line.split("  (")[0].strip())
missing = sorted(n for n in listings if n not in files)
note(f"Listed PDFs not downloaded: {len(missing)}")
for m in missing:
    known = m in recorded
    note(f"  {m}  ({'recorded in the download problems file' if known else 'NOT recorded anywhere'})")
    if not known: problems.append(f"not downloaded and not recorded: {m}")

if problems:
    note("Records file NOT written, because the checks below failed.")
else:
  os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
  with open(a.out, "w", encoding="utf-8") as out:
    for name in sorted(listings):
        entries = listings[name]
        f = files.get(name)
        rec = {"id": "hi-dcca-oah:" + name, "kind": "administrative_decision", "jurisdiction": "HI", "body_id": BODY_ID,
               "title": entries[0]["listing_title"],
               "source_url": f"{STATE_SITE}/oah/public/docs/{urllib.parse.quote(name)}",
               "retrieved": f["retrieved"] if f else None,
               "meta": {"pdf_filename": name, "programs": sorted({e["program"] for e in entries})},
               "files": [f] if f else [], "listings": entries}
        out.write(json.dumps(rec, ensure_ascii=False) + "\n")
  note(f"Records written: {len(listings)} to {os.path.abspath(a.out)}")

note("")
if problems:
    note(f"CHECKS FAILED: {len(problems)} problem(s)")
    for p in problems[:200]: note(f"  - {p}")
else:
    note("ALL CHECKS PASSED")
rep = os.path.splitext(a.out)[0] + f"_report_{date.today().isoformat()}.txt"
os.makedirs(os.path.dirname(os.path.abspath(rep)), exist_ok=True)
open(rep, "w", encoding="utf-8").write("\n".join(report) + "\n")
print(f"Report saved: {rep}")
sys.exit(1 if problems else 0)
