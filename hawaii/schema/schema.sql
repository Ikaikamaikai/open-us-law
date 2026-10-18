-- Hawaii public information: one local database for law, rules, government structure,
-- mandated document structures, and the public records you add.
--
-- Rules the whole schema follows:
--   1. Every row that states something about the world carries source_url: the
--      public place a person can read the original.
--   2. Nothing is inferred into a fact column. If a value was not found, it is NULL.
--      Facts derived by parsing are tagged in `provenance` so they can be re-checked.
--   3. Records are stored as published. No scores, labels, or characterizations.

------------------------------------------------------------------------------------
-- LAW: statutes, constitutions, court rules, administrative rules, AG opinions,
-- agency guidance, federal code and regulations. One row per section.
------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS corpus (
  id            TEXT PRIMARY KEY,   -- hrs, har, hi-const, hi-rules, hi-ag, hi-guidance, usc, us-const, fed-rules, cfr
  name          TEXT NOT NULL,      -- "Hawaii Revised Statutes"
  jurisdiction  TEXT NOT NULL,      -- HI | US
  kind          TEXT NOT NULL,      -- statute | constitution | court_rule | regulation | ag_opinion | guidance
  publisher     TEXT,               -- who officially publishes it
  provenance    TEXT,               -- how it got here: "vaquill open-us-law v2026.09.1", "har-scrape 2026-10-18"
  sections      INTEGER
);

CREATE TABLE IF NOT EXISTS section (
  rowid             INTEGER PRIMARY KEY,
  id                TEXT UNIQUE NOT NULL,  -- hrs:26-4  har:16-12-1  usc:42-1983 ...
  corpus            TEXT NOT NULL REFERENCES corpus(id),
  jurisdiction      TEXT NOT NULL,
  citation          TEXT NOT NULL,         -- as published: "Haw. Rev. Stat. § 26-4"
  cite_key          TEXT NOT NULL,         -- normalized lookup key: "haw rev stat 26-4"
  number            TEXT,                  -- "26-4"
  heading           TEXT,                  -- "Structure of government."
  title_number      TEXT,
  title_name        TEXT,
  chapter           TEXT,
  chapter_name      TEXT,
  part              TEXT,                  -- "Part II. Freedom of Information" (HRS, from the official TOC)
  division          TEXT,                  -- "Division 1. Government" (HRS)
  path              TEXT,                  -- "Title 4 / Chapter 26 / § 26-4"
  ord               REAL,                  -- order of the section inside its chapter
  status            TEXT,                  -- in_force | repealed | reserved | expired | omitted | transferred ...
  year              INTEGER,
  last_amended_year INTEGER,
  text              TEXT,
  source_url        TEXT NOT NULL,
  provenance        TEXT                   -- e.g. "ocr" when the text came from a scanned PDF
);
CREATE INDEX IF NOT EXISTS section_cite    ON section(cite_key);
CREATE INDEX IF NOT EXISTS section_chapter ON section(corpus, chapter, ord);

CREATE VIRTUAL TABLE IF NOT EXISTS section_fts USING fts5(
  citation, heading, path, text,
  content = 'section', content_rowid = 'rowid', tokenize = 'porter unicode61'
);

-- Links between sections, each extracted from the text or an official table.
--   cites       : section text names another section ("section 26-5", "42 U.S.C. § 1983")
--   implements  : a rule section names the statute it implements ("Imp:" note / LRB table)
--   authority   : a rule section names the statute that authorized it ("Auth:" note)
--   chapter     : section text names a whole chapter ("chapter 92F")
CREATE TABLE IF NOT EXISTS ref (
  from_id   TEXT NOT NULL,
  to_key    TEXT NOT NULL,     -- normalized key of the target (resolved below when possible)
  to_id     TEXT,              -- section.id when the target exists in this database
  kind      TEXT NOT NULL,
  basis     TEXT               -- where the link came from: "text", "imp-note", "lrb-2025-table"
);
CREATE INDEX IF NOT EXISTS ref_from ON ref(from_id);
CREATE INDEX IF NOT EXISTS ref_to   ON ref(to_id);

-- The official list of Hawaii Administrative Rules chapters (LRB 2025 directory).
CREATE TABLE IF NOT EXISTS har_chapter (
  title         TEXT NOT NULL,
  listed_under  TEXT,          -- title the LRB lists it under (differs for attached agencies)
  title_name    TEXT,
  subtitle      TEXT,
  subtitle_name TEXT,
  chapter       TEXT NOT NULL,
  chapter_to    TEXT,          -- for ranges: "5 to 9 Repealed"
  chapter_name  TEXT,
  repealed      INTEGER,       -- 1 | 0 | NULL when the directory does not say
  have_text     INTEGER DEFAULT 0
);

-- The official HRS outline (Table of Contents, updated 2/10/2025): every chapter, including
-- repealed ones and chapters not present in the section table.
CREATE TABLE IF NOT EXISTS hrs_chapter (
  division      TEXT,
  division_name TEXT,
  title         TEXT NOT NULL,
  title_name    TEXT,
  subtitle      TEXT,
  subtitle_name TEXT,
  chapter       TEXT NOT NULL,
  chapter_to    TEXT,          -- for "807 to 830 RESERVED FOR EXPANSION"
  chapter_name  TEXT,
  status        TEXT,          -- in_force | repealed | renumbered | reserved, as the TOC marks it
  first_section TEXT,
  page          INTEGER,       -- page of the TOC PDF
  sections_here INTEGER        -- how many sections of this chapter are in the section table
);
CREATE TABLE IF NOT EXISTS hrs_part (
  chapter       TEXT NOT NULL,
  kind          TEXT,          -- part | article | subpart | unnumbered
  article       TEXT,
  article_name  TEXT,
  part          TEXT,
  part_name     TEXT,
  status        TEXT,
  first_section TEXT,
  page          INTEGER
);

-- Session laws to HRS (Table of Disposition, Table 2). One row per HRS target an act section touched.
CREATE TABLE IF NOT EXISTS session_law (
  year         INTEGER NOT NULL,
  act          INTEGER NOT NULL,
  act_section  TEXT,
  kind         TEXT,           -- section | chapter | part | subpart | article | omitted
  target       TEXT,           -- "803-6", "c 663J", "c 92 pt VII"
  chapter      TEXT,
  repealed     INTEGER,        -- the table marks it (R)
  heading_only INTEGER,        -- the table marks it (heading)
  section_id   TEXT,           -- section.id when the target section is in the section table
  noted_in_text INTEGER,       -- 1 when that section's own history note cites "L <year>, c <act>"
  raw          TEXT,
  page         INTEGER
);
CREATE INDEX IF NOT EXISTS session_law_section ON session_law(section_id);
CREATE INDEX IF NOT EXISTS session_law_act ON session_law(year, act);

------------------------------------------------------------------------------------
-- GOVERNMENT: who exists, what created them, and how they connect.
-- Every body and every link cites the provision of law that establishes it.
------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS body (
  id          TEXT PRIMARY KEY,   -- hi.exec.dept.health
  name        TEXT NOT NULL,
  level       TEXT NOT NULL,      -- federal | state | county | person
  branch      TEXT,               -- legislative | executive | judicial | independent | local | people
  kind        TEXT,               -- branch | office | department | court | board | commission | authority | agency | county | fund | program | right
  parent_id   TEXT REFERENCES body(id),
  basis_cite  TEXT,               -- "Haw. Rev. Stat. § 26-13"
  basis_id    TEXT,               -- section.id of that provision
  basis_quote TEXT,               -- the words of the provision that create it
  source_url  TEXT,
  verified    INTEGER NOT NULL DEFAULT 0, -- 1 = basis_quote was found in basis_id's text at build time
  origin      TEXT                -- "spine" (listed by hand, verified against text) | "mined" (found by pattern)
);

CREATE TABLE IF NOT EXISTS link (
  from_id     TEXT NOT NULL REFERENCES body(id),
  to_id       TEXT NOT NULL REFERENCES body(id),
  relation    TEXT NOT NULL,      -- part_of | attached_to | appeals_to | appoints | confirms | audits | funds | oversees
  basis_cite  TEXT,
  basis_id    TEXT,
  basis_quote TEXT,
  verified    INTEGER NOT NULL DEFAULT 0
);

-- Public-access law: which law gives the public a right to see which kind of record.
CREATE TABLE IF NOT EXISTS access_rule (
  id          TEXT PRIMARY KEY,
  record_kind TEXT NOT NULL,      -- government_records | meetings | court_records | ...
  body_id     TEXT REFERENCES body(id),
  basis_cite  TEXT NOT NULL,
  basis_id    TEXT,
  basis_quote TEXT,
  verified    INTEGER NOT NULL DEFAULT 0
);

------------------------------------------------------------------------------------
-- STRUCTURES: layouts that the law requires a document to follow
-- (e.g. the 23 items of a Franchise Disclosure Document, 16 C.F.R. § 436.5).
------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS structure (
  id          TEXT PRIMARY KEY,   -- fdd
  name        TEXT NOT NULL,
  basis_cite  TEXT NOT NULL,
  basis_id    TEXT,
  source_url  TEXT,
  note        TEXT
);
CREATE TABLE IF NOT EXISTS structure_part (
  structure_id TEXT NOT NULL REFERENCES structure(id),
  ord          INTEGER NOT NULL,
  label        TEXT NOT NULL,     -- "Item 7"
  heading      TEXT,              -- "Estimated Initial Investment"
  text         TEXT,              -- what the law says must be disclosed under this part
  PRIMARY KEY (structure_id, ord)
);

------------------------------------------------------------------------------------
-- RECORDS: the public records you load (court dockets, filings, parcels, documents).
-- Empty until you add them with `hi load`. Stored as published.
------------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS record (
  rowid        INTEGER PRIMARY KEY,
  id           TEXT UNIQUE NOT NULL,  -- your stable id, e.g. "court:1CCV-24-0001234" or "parcel:1-2-3-004-005"
  kind         TEXT NOT NULL,         -- court_case | filing | parcel | deed | permit | contract | disclosure | document
  jurisdiction TEXT,                  -- HI | US | Honolulu | Maui | Hawaii County | Kauai
  body_id      TEXT REFERENCES body(id), -- the court or agency that holds the record
  number       TEXT,                  -- case number, TMK, document number
  title        TEXT,
  date         TEXT,                  -- ISO date as published
  status       TEXT,                  -- as published by the holder
  structure_id TEXT REFERENCES structure(id), -- if the document follows a mandated structure
  text         TEXT,
  meta         TEXT,                  -- JSON of any other published fields
  source_url   TEXT NOT NULL,
  retrieved    TEXT                   -- when you got it
);
CREATE INDEX IF NOT EXISTS record_kind ON record(kind, jurisdiction);

CREATE VIRTUAL TABLE IF NOT EXISTS record_fts USING fts5(
  number, title, text, content = 'record', content_rowid = 'rowid', tokenize = 'porter unicode61'
);

CREATE TABLE IF NOT EXISTS party (
  id    TEXT PRIMARY KEY,
  name  TEXT NOT NULL,
  kind  TEXT                         -- person | organization | government
);
CREATE TABLE IF NOT EXISTS record_party (
  record_id TEXT NOT NULL REFERENCES record(id),
  party_id  TEXT NOT NULL REFERENCES party(id),
  role      TEXT                     -- plaintiff | defendant | owner | grantor | grantee | franchisor ... as published
);
CREATE TABLE IF NOT EXISTS record_section (
  record_id  TEXT NOT NULL REFERENCES record(id),
  section_id TEXT NOT NULL,          -- law cited in or governing the record
  relation   TEXT                    -- cited | governed_by | filed_under
);
-- One record part per mandated structure part (e.g. Item 19 of a specific FDD).
CREATE TABLE IF NOT EXISTS record_part (
  record_id TEXT NOT NULL REFERENCES record(id),
  ord       INTEGER NOT NULL,
  label     TEXT,
  text      TEXT,
  page_from INTEGER,
  page_to   INTEGER,
  PRIMARY KEY (record_id, ord)
);
