# Hawaii public information shell

A local, offline search and reference tool for Hawaii public law and the structure of Hawaii government, built on the
Open US Law corpus in this repository. It runs entirely on your computer: no API, no account, no network after setup.

It does what the paid legal APIs do (resolve a citation, search the law, read a section with its neighbors,
definitions, citations in and out, and the rules that implement it), and adds:

- **The government map.** Every branch, department, court, county and office, each tied to the provision of law that
  creates it, with the law's own words quoted and checked against the text. See [map/GOVERNMENT.md](map/GOVERNMENT.md).
- **Hawaii Administrative Rules.** The official LRB directory of all 1,605 HAR chapters, the 33,931 links from HRS
  sections to the rules that implement them, and a collector for the rule text itself.
- **Document structures.** Layouts the law requires, starting with the 23 items of a Franchise Disclosure Document
  (16 C.F.R. § 436.5).
- **Your records.** Court records, filings, parcels and documents you collect, stored as published, linked to the
  court or agency that holds them and to the law they cite.

It shows published text and where it came from. It does not characterize, score, or advise.

## Set up once

```sh
cd hawaii
pip install duckdb pdfplumber          # needed only to build; the finished tool uses plain Python
python3 fetch.py                       # downloads ~95 MB of law, checks every file's published sha256
python3 har/scrape_har.py data/har     # optional: re-collects HAR text from agency sites (hours; a collected copy is included)
python3 build.py                       # builds data/hawaii.db (about a minute)
```

After that, nothing needs the internet.

## Use it

```sh
python3 hi.py serve          # one search bar at http://127.0.0.1:8808
python3 hi.py <anything>     # same thing in the terminal
```

| You type | It does |
|---|---|
| `HRS 92F-12`, `Haw. Rev. Stat. § 26-4`, `26-4` | reads the statute, with neighbors, what cites it, and the rules that implement it |
| `HAR 16-37-3`, `16-37-3` | reads the administrative rule |
| `HRCP 23`, `FRCP 23`, `42 USC 1983`, `16 CFR 436.5`, `haw const art 6 sec 1` | reads that rule, code section or constitutional provision |
| `define franchise` | every definition of the term written in the law |
| `who regulates public utilities` | the part of government, the law that creates it, what it belongs to and contains |
| `appeal from district court` | each step a decision can take next, and the law for each step |
| `public records` | the laws that open records and meetings, and who administers them |
| `rules for HRS 482E-3` | the administrative rules that implement a statute |
| `fdd` | the 23 required items of a Franchise Disclosure Document |
| `class action in court rules` | full-text search, limited to one source |
| anything else | full-text search across everything, including your records |

Terminal commands: `find`, `read`, `near`, `defs`, `citedby`, `rules`, `cites`, `browse`, `map`, `access`, `structure`,
`coverage`, `load`, `serve`, `mcp`. Run `python3 hi.py help` for the list.

## Use it from Claude or another AI app (MCP)

`hi.py mcp` is an MCP server over stdio. The AI app sends questions to your local database instead of a paid API.

Claude Code:

```sh
claude mcp add hawaii-law -- python3 /full/path/to/hawaii/hi.py mcp
```

Claude Desktop (`claude_desktop_config.json`):

```json
{ "mcpServers": { "hawaii-law": { "command": "python3", "args": ["/full/path/to/hawaii/hi.py", "mcp"] } } }
```

Tools: `ask`, `search`, `resolve_citation`, `read_section`, `define`, `extract_citations`, `government`,
`appeal_path`, `public_access`, `document_structure`, `coverage`. Every result carries its official `source_url`.

## Add your records

Put records in a JSONL file, one per line, then `python3 hi.py load myfile.jsonl`. The file is kept in `data/records/`
so every rebuild includes it. Only `id`, `kind` and `source_url` are required; everything else is stored as published.

```json
{"id": "court:<case number>", "kind": "court_case", "jurisdiction": "HI", "body_id": "hi.jud.circuit",
 "number": "<case number>", "title": "<caption as published>", "date": "YYYY-MM-DD", "status": "<as published>",
 "text": "<docket text or document text>", "source_url": "<where the public can see it>",
 "parties": [{"name": "<name as published>", "kind": "person|organization|government", "role": "<role as published>"}],
 "sections": ["HRS 480-2", "HRCP 23"],
 "parts": [{"label": "Item 19", "text": "...", "page_from": 61, "page_to": 64}]}
```

`kind` can be anything you use: `court_case`, `filing`, `parcel`, `deed`, `permit`, `contract`, `disclosure`, `document`.
`body_id` is any id from the government map (`hi.jud.circuit`, `hi.exec.dept.26-9`, `co.honolulu`, …).
`structure_id` (for example `fdd`) marks a document that follows a mandated layout, and `parts` holds its sections.

Two more optional keys record where a record came from:

```json
"files": [{"sha256": "<SHA-256 of the file>", "original_filename": "<name as published>", "source_url": "<download address>",
           "retrieved": "YYYY-MM-DD", "size_bytes": 123, "media_type": "application/pdf", "local_path": "<path on your computer>"}],
"listings": [{"source_page_url": "<listing page>", "seen_on": "YYYY-MM-DD", "listing_order": 1,
              "listing_title": "<title as shown>", "program": "<category as shown>"}]
```

### Office of Administrative Hearings decisions

1. Download every decision PDF on Windows: `powershell -ExecutionPolicy Bypass -File oah/download-hi-dcca-oah-pdfs_2026-10-18.ps1`.
   It keeps the state's file names, checks each file is a complete PDF, and writes a manifest with each file's size,
   SHA-256 and download date, plus a dated copy of the search page. Run it again to resume.
2. Turn them into records: `python oah/oah_records.py --pdfs <download folder> --out data/records/hi-dcca-oah-decisions_<date>.jsonl`.
   It re-checks every PDF against the manifest and writes the records file only if every check passes.
3. `python hi.py load data/records/hi-dcca-oah-decisions_<date>.jsonl`, or rebuild.

## What is in it

| Source | Sections | From |
|---|---:|---|
| Hawaii Revised Statutes | 22,980 | Open US Law v2026.09.1, plus 3,783 sections it lacked and 195 sections updated to 2025 law, fetched from the Legislature's server (`hrs/fill_missing.py`; kept in `hrs/hrs_fill.jsonl.gz` and `hrs/hrs_refresh.jsonl.gz`). Checked against all 22,971 section pages on the server: [hrs/COMPLETENESS.md](hrs/COMPLETENESS.md) |
| Hawaii Constitution | 160 | Open US Law v2026.09.1 |
| Hawaii court rules (31 rule sets) | 1,259 | Open US Law v2026.09.1 |
| Hawaii Attorney General opinions | 66 | Open US Law v2026.09.1 |
| Hawaii Insurance Division memoranda | 171 | Open US Law v2026.09.1 |
| Hawaii Administrative Rules | 12,707 (545 of 1,001 active chapters) | agency PDFs listed by the Lieutenant Governor; kept in `har/har_sections.jsonl.gz`, crawl log in `har/har_pdfs.csv` |
| HAR directory and HRS→HAR table | 1,605 chapters, 33,931 links | LRB, *2025 Table of Statutory Sections Implemented and Directory* |
| United States Code | 60,667 | Open US Law v2026.09.1 |
| U.S. Constitution | 74 | Open US Law v2026.09.1 |
| Federal court rules | 1,130 | Open US Law v2026.09.1 |
| CFR (selected parts: 16 C.F.R. Part 436) | 11 | Open US Law v2026.09.1, read remotely |

Add a CFR part by adding a line to `cfr_slices` in [sources.json](sources.json) and running `fetch.py` again.

## How "verified" works

The government map is defined in [map/spine.json](map/spine.json): each part names a provision and quotes it. The 19
state departments and their heads are read from HRS §§ 26-4 to 26-21, and the federal departments from 5 U.S.C. § 101.
When `build.py` runs, it looks up each provision in the database and checks that the quoted words are in its text.
If they are, the part is marked verified; if not, it is marked ✗ and listed in the build output. Nothing is filled in
from memory. Boards and commissions found by pattern (`origin = mined`) keep the exact sentence that creates them.

## Files

```
hawaii/
  hi.py              the shell: terminal, web page, MCP server
  cite.py            citation parsing: one key for every way a citation is written
  fetch.py           downloads and checks the law files
  build.py           builds data/hawaii.db
  sources.json       which files and CFR parts to include
  schema/            the database schema and its explanation
  map/               the government map: definition, generated diagrams, mined bodies
  har/               HAR directory, HRS→HAR table, and the rule-text collector
  hrs/               HRS table of contents, 2025 table of disposition, completeness checks, the section fetcher
  shape/             the shape of everything: every body of law and record set, how much of each is here
  web/page.html      the page's source; build_shape.py turns it into web/index.html with fonts and the shape inside
  web/index.html     the page (one file: opens by itself as the Shape, searches everything when hi.py serve runs)
  web/previous.html  the earlier page, at http://127.0.0.1:8808/previous
  web/fonts/         Drafting Mono (SIL Open Font License) and the Lab Mono declaration
  oah/               the OAH decision downloader (Windows) and its records converter
  data/              downloads and the built database (not committed)
```

`build.py` runs `shape/build_shape.py` at the end, so the page's counts match the database. Run it yourself after
`hi.py load` or after editing `web/page.html`.

## Sources and licences

Law text from Open US Law (Vaquill AI) is published under CC BY-NC 4.0: free for non-commercial use with attribution;
commercial use needs a licence from contact@vaquill.ai. The HAR directory and table come from the Hawaii Legislative
Reference Bureau, and rule text from the issuing agencies. US law is not subject to copyright
(*Georgia v. Public.Resource.Org, Inc.*, 140 S. Ct. 1498 (2020)). Every section, rule and map entry carries the URL of its
official publisher; check the original before relying on it.
