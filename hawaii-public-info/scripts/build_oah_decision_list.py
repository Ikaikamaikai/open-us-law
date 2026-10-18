# Usage: python build_oah_decision_list.py <saved OAH search page .html> <output .csv> <date page was saved, YYYY-MM-DD>
import csv, html, re, sys, urllib.parse
src, out, retrieved_on = sys.argv[1], sys.argv[2], sys.argv[3]
source_page = "https://web3.dcca.hawaii.gov/oah/public/result?search=&cat=All"
page = open(src, encoding="utf-8", errors="replace").read()
rows = re.findall(r'<tr tabindex="0">(.*?)</tr>', page, re.S)
base = "https://web3.dcca.hawaii.gov"
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["listing_order", "listing_title", "program", "pdf_filename", "pdf_url", "retrieved_on", "source_page_url"])
    for i, r in enumerate(rows, 1):
        href = re.search(r'href="([^"]+)"', r).group(1)
        title = html.unescape(re.search(r"<h5>(.*?)</h5>", r, re.S).group(1)).strip()
        program = html.unescape(re.sub(r"<[^>]+>", "", r.split("PDF_24.png")[-1].split(">", 1)[-1])).strip()
        path = html.unescape(href)
        w.writerow([i, title, program, path.rsplit("/", 1)[-1], base + urllib.parse.quote(path), retrieved_on, source_page])
print(len(rows), "records")
