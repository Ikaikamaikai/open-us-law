# Hawaii Public Info: project file

Updated 2026-10-18. This file lists every part of the project: what exists, where it is, and what each next step is.
Anyone working on the project (a person, Claude, Antigravity) starts here and updates this file when a step changes.

## The project

Hawaii Public Info (hawaiipublicinfo.com and publicinfohawaii.com) puts Hawaii public records in one searchable place,
each linked to the original it came from. It provides what is public, as published. It does not give legal advice,
act as the government or a regulator, or comment on the records.

## Where everything is

| What | Where |
|---|---|
| This project folder | GitHub `Ikaikamaikai/open-us-law`, branch `claude/tangent-session-4ss0zq`, folder `hawaii-public-info/` (the repo is public) |
| Table layout (schema) | `schema/hawaii-public-info-schema_2026-10-18.sql` |
| Scripts | `scripts/` |
| Reference material | `reference/` |
| OAH decision PDFs | Owner's Windows computer, `C:\Users\<owner>\hi-dcca-oah-pdfs_2026-10-18\` |
| Hawaii law files (Open US Law v2026.09.1) | Owner's computer, downloaded 2026-10-16 |
| OAH decision list (names people) | Owner's copy, in `hawaii-public-info-work-files_2026-10-18.zip`; kept off this public repo |
| Domains | Cloudflare, owner's account |

## Steps

### 1. OAH decision list: done 2026-10-18
- 3,030 entries on the state's search page, pointing to 2,970 distinct PDFs.
- File: `hi-dcca-oah-decision-list_2026-10-18.csv` (owner's zip). Rebuild with `scripts/build_oah_decision_list.py`.

### 2. Download every OAH PDF to the owner's computer: in progress (Antigravity)
- Script: `scripts/download-hi-dcca-oah-pdfs_2026-10-18.ps1`. Run: `powershell -ExecutionPolicy Bypass -File <path to script>`.
- It keeps the state's file names, checks each file is a complete PDF, and writes `hi-dcca-oah-pdf-manifest.csv`
  (size, SHA-256, address, date) and a dated copy of the search page. Run it again to resume.
- Done when: it prints `In the folder: 2969 of the 2970`, and the problems file lists only
  `IC-26-020+ FIRST INDEMNITY INSURANCE OF HAWAII ET AL.PDF` (the state's own link returns 404, checked 2026-10-18).

### 3. Build the local database: ready to run after step 2
- Script: `scripts/build_database_2026-10-18.py`. Needs Python and `pip install duckdb`.
- Run: `python build_database_2026-10-18.py --laws <law files folder> --pdfs <PDF folder> --out hawaii-public-info_<date>.duckdb`
- Loads all 20,853 law sections, every search-page entry and every downloaded PDF, re-checks each PDF's size and
  fingerprint against the manifest, and saves a dated build report. It never overwrites an existing database.
- Done when: it prints `ALL CHECKS PASSED`.

### 4. Pull text out of each PDF: not started (needs step 3)
- Fill `oah_decisions.full_text` from PDFs that contain text (`text_source = 'embedded'`), and set
  `source_files.page_count` and `has_text_layer`.
- PDFs with no text layer (most recent ones are page images) are marked `has_text_layer = false` for OCR. The owner does OCR.
- Done when: every downloaded PDF has either text or `has_text_layer = false`.

### 5. Fill dockets, parties, document titles, dates and sections: not started (needs step 4)
- Tables: `oah_docket_numbers`, `oah_parties`, `oah_decision_sections`, plus `document_titles` and `decision_date` in `oah_decisions`.
- Copy everything exactly as printed into the `_as_printed` columns. Nothing is summarized or interpreted.

### 6. Citation mentions: not started (needs step 4)
- Table: `citation_mentions`. Record each citation exactly as printed and where it appears;
  set `matched_act_id` only when it matches exactly one law section.

### 7. Franchise Disclosure Documents (FDDs): not started
- Table `fdd_documents` is ready, with the 23 items required by 16 CFR 436.5 (`reference/fdd-23-items_from-16-cfr-436.5_2026-10-18.txt`).
- Where the FDD files come from: owner to decide.

### 8. Own compilation of Hawaii law: not started
- The law rows loaded today come from Open US Law. Its text is public domain; its compilation is CC BY-NC 4.0 (non-commercial).
  Each row records `compiled_by`, so these rows can be replaced by rows compiled from the state's own sites.
- Related sessions: "Yo" (branch `claude/yo-2sxegb`), parsing the HRS table of contents; "Hawaii scraper"
  (branch `claude/hawaii-scraper-39no5y`), blocked: Cloudflare blocked the scraper, 2 commits not yet pushed.

### 9. Website search: not started
- How the public search runs: owner to decide. Prices checked 2026-10-18 are in `reference/storage-and-database-options_price-check_2026-10-18.md`.

### 10. PDF hosting for the website: not started
- PDFs stay on the owner's computer for now (owner's decision, 2026-10-18).

### 11. Private project repo `hawaiipublicinfo`: waiting on owner
- Claude's GitHub access cannot create repositories. Owner creates it at github.com/new (private, empty).
  Then this folder and the OAH decision list move there.

### 12. Naming rules: on hold (owner's decision)

## Facts found so far (2026-10-18)

- One OAH PDF can hold several documents, e.g. a Board's Final Order followed by the Hearings Officer's recommended order.
- Many decisions are settlements, with headings such as "Uncontested Facts" and "Terms of Settlement" instead of
  "Findings of Fact" and "Conclusions of Law".
- The newest PDFs (2026) have no text layer and need OCR. Older ones have text, sometimes with OCR errors.
- Every OAH PDF carries the state's notice: "This decision has been redacted and reformatted for publication purposes".
- 58 PDFs are listed twice on the state's page; 3 of them under two different programs.
- The 27 columns in the Open US Law files are listed in `reference/open-us-law-27-columns_from-hawaii-files_2026-10-18.csv`.
  An earlier 27-column list from Gemini did not match the real files.

## Files

| File | What it is |
|---|---|
| `schema/hawaii-public-info-schema_2026-10-18.sql` | Table layout, draft. Tested in DuckDB and SQLite |
| `scripts/download-hi-dcca-oah-pdfs_2026-10-18.ps1` | Step 2 |
| `scripts/build_database_2026-10-18.py` | Step 3 |
| `scripts/build_oah_decision_list.py` | Step 1 |
| `scripts/write_column_list.py` | Makes the 27-column reference list |
| `reference/open-us-law-27-columns_from-hawaii-files_2026-10-18.csv` | The 27 Open US Law columns with examples |
| `reference/fdd-23-items_from-16-cfr-436.5_2026-10-18.txt` | The 23 FDD items, from the federal rule |
| `reference/storage-and-database-options_price-check_2026-10-18.md` | Storage and database prices, with sources |
