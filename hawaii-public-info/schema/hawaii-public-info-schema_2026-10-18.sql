-- Hawaii Public Info: table layout (schema), draft of 2026-10-18. Not final.
-- Plain SQL. Tested in DuckDB and SQLite. Every column has a one-line description.
-- Each record says where it came from (source_url, a file fingerprint, and dates).
-- Links between tables are noted in comments, not enforced, because DuckDB cannot update a row that another table points to.

-- 1. Original files exactly as collected (PDFs, web pages). One row per distinct file.
CREATE TABLE source_files (
    file_sha256        TEXT PRIMARY KEY,  -- the file's digital fingerprint (SHA-256); changes if even one byte changes
    original_filename  TEXT NOT NULL,     -- the file name exactly as the publisher gave it
    source_url         TEXT NOT NULL,     -- the address it was downloaded from
    publisher          TEXT NOT NULL,     -- who published it, e.g. 'Hawaii DCCA Office of Administrative Hearings'
    retrieved_on       DATE NOT NULL,     -- the day it was downloaded
    size_bytes         BIGINT NOT NULL,   -- file size
    media_type         TEXT NOT NULL,     -- kind of file, e.g. 'application/pdf', 'text/html'
    local_path         TEXT,              -- where the file sits on your computer, relative to your documents folder
    page_count         INTEGER,           -- number of pages (PDFs)
    has_text_layer     BOOLEAN,           -- true if text can be copied out directly; false if pages are images that need OCR
    notes              TEXT               -- anything unusual about the file
);

-- 2. Laws and legal documents: statutes, court rules, constitution, AG opinions, agency guidance.
--    Columns 1-27 use the same names, order and meaning as Open US Law v2026.09.1, so those files load as-is.
--    Columns 28-30 record who compiled each row and when, so rows can be told apart and replaced later.
CREATE TABLE law_sections (
    act_id                 TEXT PRIMARY KEY, -- ID of the row (for Open US Law rows this is their ID)
    citation               TEXT NOT NULL,    -- full citation, e.g. 'Haw. Rev. Stat. § 90D-5'
    citation_short         TEXT,             -- shorter citation
    state                  TEXT NOT NULL,    -- two-letter state code, lower case, e.g. 'hi'
    jurisdiction           TEXT NOT NULL,    -- country code; 'US' on every Open US Law row
    document_type          TEXT NOT NULL,    -- 'statute', 'court_rule', 'constitution', 'ag_opinion', 'guidance'
    title_number           TEXT,             -- title number in the code (statutes)
    title_name             TEXT,             -- name of the collection the row belongs to
    chapter                TEXT,             -- chapter number (statutes)
    chapter_name           TEXT,             -- chapter name
    section_number         TEXT,             -- section number, or opinion number for AG opinions
    section_title          TEXT,             -- section heading, or opinion subject line
    breadcrumb             TEXT,             -- position in the hierarchy, stored as JSON text
    display_path           TEXT,             -- same hierarchy as one readable line
    act_status             TEXT,             -- 'in_force', 'repealed', 'reserved', etc.
    text                   TEXT NOT NULL,    -- full text of the section or document
    word_count             BIGINT,           -- words in text
    source_url             TEXT,             -- government page or PDF the text came from
    last_amended_year      BIGINT,           -- year last amended, where found
    subsection_count       BIGINT,           -- number of subsections
    cross_references_usc   TEXT,             -- US Code citations found in the text, stored as JSON text
    cross_references_cfr   TEXT,             -- federal regulation (CFR) citations found in the text, stored as JSON text
    public_laws_referenced TEXT,             -- federal public laws found in the text, stored as JSON text
    year                   BIGINT,           -- a year (year issued for AG opinions; snapshot year for Open US Law statutes)
    official_status        TEXT,             -- publisher's own label such as 'unofficial'
    currency_note          TEXT,             -- publisher's statement of how current the text is
    adopting_citations     TEXT,             -- what adopted or amended the rule, stored as JSON text
    compiled_by            TEXT NOT NULL,    -- who produced this row, e.g. 'Vaquill Open US Law v2026.09.1' or 'Hawaii Public Info'
    compiled_on            DATE NOT NULL,    -- the date that version of the text was current as of
    source_file_sha256     TEXT              -- links to source_files.file_sha256: the saved original page, when you collected it yourself
);

-- 3. Office of Administrative Hearings (OAH) decisions. One row per PDF the state publishes.
--    The key is the state's own PDF file name.
CREATE TABLE oah_decisions (
    pdf_filename             TEXT PRIMARY KEY, -- PDF file name exactly as the state names it
    pdf_url                  TEXT NOT NULL,    -- the PDF's address on the state website
    listing_title            TEXT NOT NULL,    -- the title shown for it on the state's search page
    first_seen_on            DATE NOT NULL,    -- the first day it was seen on the state's search page
    source_file_sha256       TEXT,             -- links to source_files.file_sha256: the downloaded PDF, once downloaded
    redaction_notice         TEXT,             -- the state's own redaction stamp, word for word, if present
    board_or_agency          TEXT,             -- board or agency named in the caption, as printed
    document_titles          TEXT,             -- titles of the documents inside the PDF, as printed, in order, separated by ' | '
    decision_date            DATE,             -- date the final order was signed
    decision_date_as_printed TEXT,             -- that date exactly as printed
    full_text                TEXT,             -- all text in the PDF
    text_source              TEXT,             -- 'embedded' (text was in the PDF) or 'ocr' (read from page images)
    text_extracted_on        DATE,             -- the day the text was pulled out
    text_extracted_with      TEXT              -- program and version used, e.g. 'pypdf 6.1'
);

-- 3a. Each entry on the state's OAH search page, as seen on a given day. Some PDFs are listed more than once.
CREATE TABLE oah_listing_entries (
    seen_on         DATE NOT NULL,     -- the day the search page was read
    listing_order   INTEGER NOT NULL,  -- position on the page that day
    listing_title   TEXT NOT NULL,     -- title as shown
    program         TEXT NOT NULL,     -- program as shown, e.g. 'REAL ESTATE'
    pdf_filename    TEXT NOT NULL,     -- links to oah_decisions.pdf_filename: the PDF the entry links to
    source_page_url TEXT NOT NULL,     -- the search page address
    PRIMARY KEY (seen_on, listing_order)
);

-- 3b. Docket numbers printed on each decision. One PDF can carry several.
CREATE TABLE oah_docket_numbers (
    pdf_filename             TEXT NOT NULL, -- links to oah_decisions.pdf_filename
    docket_number_as_printed TEXT NOT NULL, -- e.g. 'ATX-2013-090'
    PRIMARY KEY (pdf_filename, docket_number_as_printed)
);

-- 3c. Parties named in each decision's caption, with the role printed next to the name.
CREATE TABLE oah_parties (
    pdf_filename    TEXT NOT NULL, -- links to oah_decisions.pdf_filename
    name_as_printed TEXT NOT NULL, -- e.g. 'KURT W. WILLIAMS'
    role_as_printed TEXT NOT NULL, -- e.g. 'Respondent', 'Claimant', 'Petitioner'
    PRIMARY KEY (pdf_filename, name_as_printed, role_as_printed)
);

-- 3d. Headed sections inside each decision, whatever headings that document actually uses
--     (e.g. 'FINDINGS OF FACT', 'UNCONTESTED FACTS', 'TERMS OF SETTLEMENT').
CREATE TABLE oah_decision_sections (
    pdf_filename       TEXT NOT NULL,    -- links to oah_decisions.pdf_filename
    section_order      INTEGER NOT NULL, -- 1 for the first heading in the PDF, 2 for the next, and so on
    heading_as_printed TEXT NOT NULL,    -- the heading exactly as printed
    section_text       TEXT,             -- text under that heading
    page_start         INTEGER,          -- PDF page where the section starts
    page_end           INTEGER,          -- PDF page where it ends
    PRIMARY KEY (pdf_filename, section_order)
);

-- 4. Franchise Disclosure Documents (FDDs). One row per FDD file.
--    The 23 item columns follow the 23 items required by the FTC Franchise Rule, 16 CFR 436.5 (a) to (w).
CREATE TABLE fdd_documents (
    source_file_sha256       TEXT PRIMARY KEY, -- links to source_files.file_sha256: the FDD file this row was read from
    franchisor_name          TEXT,  -- franchisor's legal name as printed
    brand_name               TEXT,  -- brand or trade name as printed
    issuance_date            DATE,  -- issuance date on the cover page
    issuance_date_as_printed TEXT,  -- that date exactly as printed
    obtained_from            TEXT,  -- where the FDD was obtained, e.g. the state agency it was filed with
    compiled_on              DATE,  -- the day the items were read out of the file
    item_01_franchisor                         TEXT, -- Item 1: The Franchisor, and any Parents, Predecessors, and Affiliates
    item_02_business_experience                TEXT, -- Item 2: Business Experience
    item_03_litigation                         TEXT, -- Item 3: Litigation
    item_04_bankruptcy                         TEXT, -- Item 4: Bankruptcy
    item_05_initial_fees                       TEXT, -- Item 5: Initial Fees
    item_06_other_fees                         TEXT, -- Item 6: Other Fees
    item_07_estimated_initial_investment       TEXT, -- Item 7: Estimated Initial Investment
    item_08_restrictions_on_sources            TEXT, -- Item 8: Restrictions on Sources of Products and Services
    item_09_franchisee_obligations             TEXT, -- Item 9: Franchisee's Obligations
    item_10_financing                          TEXT, -- Item 10: Financing
    item_11_franchisor_assistance              TEXT, -- Item 11: Franchisor's Assistance, Advertising, Computer Systems, and Training
    item_12_territory                          TEXT, -- Item 12: Territory
    item_13_trademarks                         TEXT, -- Item 13: Trademarks
    item_14_patents_copyrights_proprietary     TEXT, -- Item 14: Patents, Copyrights, and Proprietary Information
    item_15_obligation_to_participate          TEXT, -- Item 15: Obligation to Participate in the Actual Operation of the Franchise Business
    item_16_restrictions_on_what_may_be_sold   TEXT, -- Item 16: Restrictions on What the Franchisee May Sell
    item_17_renewal_termination_transfer       TEXT, -- Item 17: Renewal, Termination, Transfer, and Dispute Resolution
    item_18_public_figures                     TEXT, -- Item 18: Public Figures
    item_19_financial_performance              TEXT, -- Item 19: Financial Performance Representations
    item_20_outlets_and_franchisee_information TEXT, -- Item 20: Outlets and Franchisee Information
    item_21_financial_statements               TEXT, -- Item 21: Financial Statements
    item_22_contracts                          TEXT, -- Item 22: Contracts
    item_23_receipts                           TEXT  -- Item 23: Receipts
);

-- 5. Places where a legal citation is printed inside any record. This only records that the
--    citation appears, and where; it makes no claim about what the appearance means.
CREATE TABLE citation_mentions (
    found_in_table        TEXT NOT NULL,    -- 'law_sections', 'oah_decisions' or 'fdd_documents'
    found_in_key          TEXT NOT NULL,    -- that record's key: act_id, pdf_filename or source_file_sha256
    mention_number        INTEGER NOT NULL, -- 1 for the first citation found in that record, 2 for the next, and so on
    page_number           INTEGER,          -- PDF page where it appears, when known
    cited_text_as_printed TEXT NOT NULL,    -- the citation exactly as printed, e.g. 'HRS § 437B-15'
    matched_act_id        TEXT,             -- law_sections.act_id when the citation matches exactly one section; otherwise empty
    found_on              DATE NOT NULL,    -- the day the citation was found
    found_with            TEXT,             -- program and version used to find it
    PRIMARY KEY (found_in_table, found_in_key, mention_number)
);
