"""Collect Hawaii Administrative Rules text from the departments that publish it.

Starts at the Lieutenant Governor's list of department rule pages
(https://ltgov.hawaii.gov/the-office/administrative-rules/), follows each
department's own rules pages one level deep, downloads every PDF that is a HAR
chapter, and splits it into sections at the "§T-C-S Heading" lines.

Every section keeps the URL of the PDF it came from. A chapter whose number
cannot be read from the PDF itself is skipped, not guessed.

Output: OUT/har_sections.jsonl (one section per line), OUT/har_pdfs.csv (crawl log).
Progress is saved to OUT/har_partial.jsonl after every PDF; rerunning resumes where it stopped.
Usage:  python3 scrape_har.py OUT [--workers 4]
        python3 scrape_har.py OUT --merge-only   (use what has been collected so far)
"""
import csv
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

INDEX = "https://ltgov.hawaii.gov/the-office/administrative-rules/"
UA = {"User-Agent": "Mozilla/5.0 (open-us-law hawaii HAR collector)"}
SKIP_HOSTS = ("facebook", "twitter", "instagram", "x.com", "flickr", "indigov", "ehawaii.gov", "youtube")
HREF = re.compile(r'href="([^"#]+)"[^>]*>(.*?)</a>', re.S | re.I)
SECTION = re.compile(r"^\s*§\s*(\d{1,2}-\d+(?:\.\d+)?[A-Z]?-[\d.]+[A-Z]?)[ \t]+([A-Z(\[].*)$", re.M)
CHAPTER_HDR = re.compile(r"TITLE\s+(\d{1,2})\b.{0,400}?CHAPTER\s+(\d+(?:\.\d+)?[A-Z]?)\b", re.S)


def get(url, binary=False, tries=3):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
                return data if binary else data.decode("utf-8", "ignore")
        except Exception:
            if i == tries - 1:
                return None
            time.sleep(2 ** i)


def links(page_url, body):
    for href, label in HREF.findall(body or ""):
        u = urllib.parse.urljoin(page_url, html.unescape(href.strip()))
        if u.startswith("http") and not any(s in u for s in SKIP_HOSTS):
            yield u, re.sub(r"<[^>]+>|\s+", " ", html.unescape(label)).strip()


def is_rules_page(url, label):
    t = (url + " " + label).lower()
    return any(k in t for k in ("rule", "har", "admin"))


def crawl():
    idx = get(INDEX)
    starts = sorted({u for u, _ in links(INDEX, idx)
                     if urllib.parse.urlparse(u).netloc not in ("ltgov.hawaii.gov",) and is_rules_page(u, "")})
    starts.append("https://ltgov.hawaii.gov/forms/olg-rules/")
    seen, pdfs = set(), {}
    frontier = [(u, 0) for u in starts]
    while frontier:
        url, depth = frontier.pop()
        if url in seen:
            continue
        seen.add(url)
        body = get(url)
        if not body:
            continue
        host = urllib.parse.urlparse(url).netloc
        for u, label in links(url, body):
            if u.lower().split("?")[0].endswith(".pdf"):
                pdfs.setdefault(u, (label, url))
            elif depth < 1 and urllib.parse.urlparse(u).netloc == host and is_rules_page(u, label) and u not in seen:
                frontier.append((u, depth + 1))
    return pdfs


OCR_ENV = {**os.environ, "OMP_THREAD_LIMIT": "1"}
MAX_OCR_PAGES = 400


def ocr_page(pdf, page, d):
    stem = Path(d) / f"p{page}"
    subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", "150", "-gray", "-scale-to", "2200",
                    "-png", "-singlefile", str(pdf), str(stem)], capture_output=True, timeout=120)
    png = stem.with_suffix(".png")
    if not png.exists():
        return ""
    try:
        return subprocess.run(["tesseract", str(png), "-", "--psm", "6"], capture_output=True, timeout=180,
                              env=OCR_ENV).stdout.decode("utf-8", "ignore")
    except subprocess.TimeoutExpired:
        return ""
    finally:
        png.unlink(missing_ok=True)


def pdf_text(data):
    """Text layer if the PDF has one; else OCR, but only when page 1 reads like a HAR chapter. Returns (text, used_ocr)."""
    p = subprocess.run(["pdftotext", "-layout", "-", "-"], input=data, capture_output=True)
    text = p.stdout.decode("utf-8", "ignore")
    if len(text.strip()) > 200:
        return text, False
    with tempfile.TemporaryDirectory() as d:
        pdf = Path(d) / "in.pdf"
        pdf.write_bytes(data)
        info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
        m = re.search(r"Pages:\s+(\d+)", info)
        pages = int(m.group(1)) if m else 1
        first = ocr_page(pdf, 1, d)
        if not re.search(r"TITLE\s+\d|CHAPTER\s+\d|§\s*\d|\$\s*\d{1,2}-\d", first, re.I) or pages > MAX_OCR_PAGES:
            return first, None
        return "\n".join([first] + [ocr_page(pdf, i, d) for i in range(2, pages + 1)]), True


def fix_heading(heading, body):
    """A heading that wraps in the PDF ends at its first period; pull the rest back from the body."""
    if heading.rstrip().endswith((".", ":", "]", ")")) or not body:
        return heading, body
    m = re.match(r"^([^.\n]{1,120}?\.)\s*(.*)$", body, re.S)
    if not m or "\n\n" in m.group(1):
        return heading, body
    return f"{heading.rstrip()} {re.sub(chr(10), ' ', m.group(1)).strip()}", m.group(2).strip()


NOISE = re.compile(r"^[ \t]*(?:§[ \t]*)?\d{1,2}-\d+(?:\.\d+)?[A-Z]?(?:-[\d.]+[A-Z]?)?[ \t]*$", re.M)


def split_sections(text):
    text = re.sub(r"^([ \t]*)\$[ \t]*(?=\d{1,2}-\d)", r"\1§", text.replace("\f", "\n"), flags=re.M)
    text = NOISE.sub("", text)
    hits = list(SECTION.finditer(text))
    best = {}
    for i, m in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(text)
        body = text[m.end():end]
        sid = m.group(1).rstrip(".")
        line = re.sub(r"\s+", " ", m.group(2)).strip()
        hm = re.match(r"^(.+?\.)(?:\s+(.*))?$", line)
        heading, lead = (hm.group(1), hm.group(2) or "") if hm else (line, "")
        chunk = re.sub(r"\n\s*\n+", "\n", lead + "\n" + re.sub(r"[ \t]+", " ", body)).strip()
        heading, chunk = fix_heading(heading, chunk)
        if sid not in best or len(chunk) > len(best[sid][1]):
            best[sid] = (heading, chunk)
    return best


def process(item):
    url, (label, from_page) = item
    data = get(url, binary=True)
    if not data or not data[:5] == b"%PDF-":
        return url, from_page, label, "fetch_failed", None, []
    text, ocr = pdf_text(data)
    if ocr is None:
        return url, from_page, label, "scanned_not_rule", None, []
    m = CHAPTER_HDR.search(text[:6000])
    secs = split_sections(text)
    if not secs:
        return url, from_page, label, "no_sections", None, []
    chapters = {sid.rsplit("-", 1)[0] for sid in secs}
    chap = f"{m.group(1)}-{m.group(2)}" if m else (chapters.pop() if len(chapters) == 1 else None)
    if not chap:
        return url, from_page, label, "chapter_unknown", None, []
    sha = hashlib.sha256(data).hexdigest()
    out = []
    for sid, (heading, body) in secs.items():
        if not sid.startswith(chap + "-"):
            continue
        status = "repealed" if re.match(r"^\(?Repealed", heading + " " + body[:40], re.I) else "in_force"
        imp = re.search(r"\(Imp:\s*([^)]*)\)", body)
        auth = re.search(r"\(Auth:\s*([^)]*)\)", body)
        out.append({
            "id": f"har:{sid}", "citation": f"HAR § {sid}", "title_number": sid.split("-")[0],
            "chapter": chap, "section_number": sid, "heading": heading, "status": status, "text": body,
            "auth": auth.group(1).strip() if auth else None, "imp": imp.group(1).strip() if imp else None,
            "source_url": url, "pdf_sha256": sha, "ocr": ocr,
        })
    return url, from_page, label, "ok", chap, out


NOT_RULE = re.compile(r"agenda|minutes|testimony|newsletter|brochure|annual[-_ ]?report|flyer|presentation|"
                      r"application|\bform\b|-form|_form|map\b|budget|invoice|contract|bid|rfp|award", re.I)
LOOKS_LIKE_RULE = re.compile(r"(?<!\d)\d{1,2}[-_ .]\d{1,4}(?:\.\d+)?[A-Za-z]?(?!\d)|\bhar\b|har[-_]|chapter|chap|rule|title", re.I)


def is_candidate(url, label):
    name = urllib.parse.unquote(url.rsplit("/", 1)[-1])
    t = f"{name} {label}"
    return bool(LOOKS_LIKE_RULE.search(t)) and not NOT_RULE.search(t)


def main():
    out = Path(sys.argv[1])
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    out.mkdir(parents=True, exist_ok=True)
    links_path, partial = out / "pdf_links.json", out / "har_partial.jsonl"
    if "--merge-only" in sys.argv:
        merge(out, partial)
        return
    if links_path.exists():
        pdfs = {u: tuple(v) for u, v in json.loads(links_path.read_text()).items()}
    else:
        pdfs = crawl()
        links_path.write_text(json.dumps(pdfs, indent=0))
    todo = {u: v for u, v in pdfs.items() if is_candidate(u, v[0])}
    done = set()
    if partial.exists():
        for line in open(partial):
            done.add(json.loads(line)["url"])
    work = [(u, v) for u, v in todo.items() if u not in done]
    print(f"{len(pdfs)} PDFs found, {len(todo)} look like rule chapters, {len(work)} left to process", flush=True)
    with ThreadPoolExecutor(workers) as ex, open(partial, "a") as pf:
        futs = [ex.submit(process, item) for item in work]
        for n, fut in enumerate(as_completed(futs), 1):
            try:
                url, page, label, status, chap, secs = fut.result()
            except Exception as e:
                continue
            pf.write(json.dumps({"url": url, "page": page, "label": label, "status": status, "chapter": chap,
                                 "sections": secs}, ensure_ascii=False) + "\n")
            pf.flush()
            if n % 25 == 0:
                print(f"{n}/{len(work)}", flush=True)
    merge(out, partial)


def merge(out, partial):
    """Write har_sections.jsonl (best PDF per chapter) and har_pdfs.csv from the progress file."""
    by_chapter, log = {}, []
    for line in open(partial):
        r = json.loads(line)
        log.append((r["url"], r["page"], r["label"], r["status"], r["chapter"], len(r["sections"])))
        for sec in r["sections"]:
            sec["heading"], sec["text"] = fix_heading(sec["heading"], sec["text"])
        if r["sections"] and (r["chapter"] not in by_chapter or len(r["sections"]) > len(by_chapter[r["chapter"]])):
            by_chapter[r["chapter"]] = r["sections"]
    with open(out / "har_sections.jsonl", "w") as f:
        for chap in sorted(by_chapter):
            for s in by_chapter[chap]:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
    with open(out / "har_pdfs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pdf_url", "found_on", "link_text", "status", "chapter", "sections"])
        w.writerows(sorted(log))
    print(f"done: {len(by_chapter)} chapters, {sum(len(v) for v in by_chapter.values())} sections", flush=True)


if __name__ == "__main__":
    main()
