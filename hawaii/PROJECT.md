# Hawaii Public Info: project file

Updated 2026-10-18. This file lists every part of the project: what exists, where it is, and what each next step is.
Anyone working on the project (a person, Claude, Antigravity) starts here and updates this file when a step changes.

## The project

Hawaii Public Info (hawaiipublicinfo.com and publicinfohawaii.com) puts Hawaii public records in one searchable place,
each linked to the original it came from. It provides what is public, as published. It does not give legal advice,
act as the government or a regulator, or comment on the records.

## One place

Everything is in this `hawaii/` folder: GitHub `Ikaikamaikai/open-us-law`, branch `claude/tangent-session-4ss0zq`.
That branch holds the "Yo" session's work (branch `claude/yo-2sxegb`, merged in on 2026-10-18) plus the OAH additions.
There is one schema: `schema/schema.sql`, explained in `schema/SCHEMA.md`. How to set up and use the tool is in `README.md`.

| What | Where |
|---|---|
| Search tool | `hi.py` (see `README.md`) |
| Building the database | `fetch.py`, then `build.py`, which makes `data/hawaii.db` |
| Schema | `schema/schema.sql`, `schema/SCHEMA.md` |
| Map of Hawaii government | `map/` (`map/GOVERNMENT.md`) |
| HRS outline, 2025 disposition table, completeness checks | `hrs/` |
| HAR chapter directory and HRS-to-HAR links | `har/` |
| OAH decisions: download script and records script | `oah/` |
| Reference material | `reference/` |
| Your records (not on GitHub) | `data/records/` on your computer |
| OAH PDFs (not on GitHub) | `C:\Users\<you>\hi-dcca-oah-pdfs_2026-10-18\` on your computer |
| OAH decision list (names people; not on this public repo) | Your copy in `hawaii-public-info-work-files_2026-10-18.zip`; `oah/oah_records.py` also rebuilds it from the saved search page |
| Domains | Cloudflare, your account |

## Done

- Law from Open US Law v2026.09.1: HRS, Hawaii Constitution, court rules, AG opinions, agency guidance (`fetch.py`, `build.py`).
- Official HRS outline (updated 2/10/2025) and the 2025 session-law Table of Disposition (`hrs/`).
- LRB directory of 1,605 HAR chapters and 33,931 links from HRS sections to the rules that implement them (`har/`).
- Map of Hawaii government, each body tied to the law that creates it (`map/`).
- FDD layout: the 23 items, read from 16 C.F.R. § 436.5 at build time; the `fdd_items` view shows them as 23 columns.
- OAH decision list: 3,030 entries on the state's search page, pointing to 2,970 PDFs (read 2026-10-18).
- OAH download script and records script, tested 2026-10-18.

## In progress

- Downloading every OAH PDF to your computer (Antigravity): `oah/download-hi-dcca-oah-pdfs_2026-10-18.ps1`.
  Done when it prints `In the folder: 2969 of the 2970`, and the problems file lists only
  `IC-26-020+ FIRST INDEMNITY INSURANCE OF HAWAII ET AL.PDF` (the state's own link returns 404, checked 2026-10-18).
- The "Yo" session is still running on its own branch (`claude/yo-2sxegb`), last noted as parsing the HRS table of contents.
  Anything it adds after 2026-10-18 has to be merged into this branch again.

## Next steps

1. **OAH records.** After the download: `python oah/oah_records.py --pdfs <download folder> --out data/records/hi-dcca-oah-decisions_<date>.jsonl`,
   then `python hi.py load <that file>`. Done when it prints `ALL CHECKS PASSED` and the load reports 2,970 records.
2. **Text from the PDFs.** Fill `record.text`, and `source_file.page_count` and `has_text_layer`. PDFs that are only page
   images get `has_text_layer = 0`; you do the OCR. Done when every downloaded PDF has text or `has_text_layer = 0`.
3. **Details from the text, exactly as printed.** Docket numbers (`record.number`), decision date (`record.date`),
   parties and their roles (`record_party`), headed sections with page numbers (`record_part`), laws cited (`record_section`).
4. **FDDs.** Where the FDD files come from: your decision. Each loads as a record with `structure_id = 'fdd'` and parts `Item 1` … `Item 23`.
5. **Your own compilation of Hawaii law.** The Open US Law compilation is CC BY-NC 4.0 (non-commercial); the law text itself is
   public domain. The "Hawaii scraper" session (branch `claude/hawaii-scraper-39no5y`) has 2 commits that are not on GitHub,
   and its scraper was blocked by Cloudflare. Those commits have to be pushed before they can be brought in.
6. **Office of Administrative Hearings in the government map.** Not there yet, so OAH records point to the Department of
   Commerce and Consumer Affairs (`hi.exec.dept.26-9`), the department every decision's caption names. Adding OAH needs the
   provision that creates it, checked against the text.
7. **Website.** How the public search on hawaiipublicinfo.com runs: your decision. The tool already has a local search page (`web/`).
   Prices checked 2026-10-18 are in `reference/storage-and-database-options_price-check_2026-10-18.md`.
8. **PDF hosting for the website.** The PDFs stay on your computer for now (your decision, 2026-10-18).
9. **Private repo `hawaiipublicinfo`.** Claude's GitHub access cannot create repositories. You create it at github.com/new
   (private, empty); then this folder and the OAH decision list move there.
10. **Naming rules.** On hold (your decision).

## Facts found so far (2026-10-18)

- One OAH PDF can hold several documents, e.g. a Board's Final Order followed by the Hearings Officer's recommended order.
- Many decisions are settlements, with headings such as "Uncontested Facts" and "Terms of Settlement" instead of
  "Findings of Fact" and "Conclusions of Law".
- The newest PDFs (2026) have no text layer and need OCR. Older ones have text, sometimes with OCR errors.
- Every OAH PDF carries the state's notice: "This decision has been redacted and reformatted for publication purposes".
- 58 PDFs are listed twice on the state's page; 3 of them under two different programs.
- The real Open US Law columns are in `reference/open-us-law-27-columns_from-hawaii-files_2026-10-18.csv`.
  An earlier 27-column list from Gemini did not match the real files.

## Changes on 2026-10-18

- Merged the "Yo" session's `hawaii/` folder into this branch.
- Added to its schema: `source_file`, `record_file`, `listing_entry` and the `fdd_items` view. Its record loader (`hi.py`)
  now also reads each record's `files` and `listings`.
- Added `oah/` and `reference/`.
- Removed the separate `hawaii-public-info/` folder, with its own schema and build script, so there is one schema.
