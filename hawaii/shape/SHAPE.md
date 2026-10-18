# The shape of everything

Every body of law and set of public records, starting at home in Hawaii and going outward. Counted 2026-10-18 from data/hawaii.db and the open-us-law v2026.09.1 index.

[x] here, complete · ◐ here in part · ↓ ready: one step away · ○ not started

## Hawaii  (13 of 32 checked off)
Home. Everything starts here.

### State law  (8 of 17 checked off)
- [x] Constitution of the State of Hawaii: 160 of 160 sections · file: us_hi_constitutions.parquet
- **Hawaii Revised Statutes** (3 of 3 checked off)
  - [x] Sections: 22,980 sections · Checked against all 22,971 section pages on the Legislature's server; every one is here except one empty [RESERVED] page. 19,197 came from the open dataset, the rest from the Legislature's server. Details: hrs/COMPLETENESS.md · https://data.capitol.hawaii.gov/hrscurrent/ · `python3 hrs/fill_missing.py --all`
  - [x] Chapters in the official Table of Contents (Feb. 10, 2025): 1,100 chapters
  - [x] Parts, subparts and articles: 1,850 parts
- **Session Laws of Hawaii** (1 of 2 checked off)
  - [x] 2025 Table of Disposition: what each act changed: 1,405 entries · 313 acts of 2025. Earlier years' tables are not loaded. · file: hrs/slh_disposition.csv
  - [ ] ○ Text of the acts: acts: counted when collected · Published by the Legislature and the Legislative Reference Bureau. · https://lrb.hawaii.gov/
- [ ] ◐ Hawaii Administrative Rules: text: 545 of 1,001 active chapters · 12,707 rule sections of text. The LRB directory lists 1,605 chapters (604 repealed) and 33,931 links from statutes to the rules that implement them. · https://ltgov.hawaii.gov/the-office/administrative-rules/ · `python3 har/scrape_har.py data/har`
- [x] Hawaii court rules: 1,259 of 1,259 sections · 31 rule sets. · file: us_hi_court_rules.parquet
- [x] Attorney General opinions: 66 of 66 opinions · Every opinion in the open dataset. The Department's older opinions are not counted here. · file: us_hi_ag_opinion.parquet
- [x] Insurance Division memoranda: 171 of 171 memoranda · file: us_hi_guidance.parquet
- [ ] ○ Appellate opinions (Supreme Court, Intermediate Court of Appeals): opinions: counted when collected · Not in the open dataset. On CourtListener: court=haw (Supreme Court) and court=hawapp (ICA). · https://www.courtlistener.com/?type=o&court=haw
- [ ] ○ Office of Information Practices opinions: opinions: counted when collected · https://oip.hawaii.gov/laws-rules-opinions/opinions/
- [ ] ○ State Ethics Commission opinions: opinions: counted when collected · https://ethics.hawaii.gov/
- [ ] ○ Governor's executive orders and proclamations: documents: counted when collected · https://governor.hawaii.gov/
- **Agency decisions** (0 of 3 checked off)
  - [ ] ↓ DCCA Office of Administrative Hearings decisions: 2,970 decision PDFs published · 3,030 entries on the state's search page point to 2,970 PDFs (read 2026-10-18). The downloader is ready and runs on Windows. · https://web3.dcca.hawaii.gov/oah/public/result?search=&cat=All · `powershell -ExecutionPolicy Bypass -File oah/download-hi-dcca-oah-pdfs_2026-10-18.ps1`
  - [ ] ○ Public Utilities Commission dockets and decisions: documents: counted when collected · https://puc.hawaii.gov/
  - [ ] ○ Land Use Commission decisions: documents: counted when collected · https://luc.hawaii.gov/

### Government of Hawaii  (4 of 4 checked off)
- [x] Parts of government, each tied to the law that creates it: 95 of 95 parts · Every quote was found in the cited law when the database was built. Shown in map/GOVERNMENT.md.
- [x] Boards and commissions found in the statutes' own words: 295 bodies · Each keeps the exact sentence that creates it. · file: map/bodies_mined.csv
- [x] Legal links between parts (appeals, supervision, appointment): 32 links
- [x] Laws that open records and meetings to the public: 7 laws

### Counties  (0 of 4 checked off)
- [ ] ○ City and County of Honolulu: Revised Ordinances of Honolulu: sections: counted when collected · The Office of Council Services is the revisor of the ROH. · https://www.honolulu.gov/ocs/
- [ ] ○ County of Hawaii: Hawaii County Code: sections: counted when collected · Published by the County of Hawaii.
- [ ] ○ County of Maui: Maui County Code: sections: counted when collected · Published by the County of Maui.
- [ ] ○ County of Kauai: Kauai County Code: sections: counted when collected · Published by the County of Kauai.

### Public records  (1 of 7 checked off)
- [ ] ↓ Your records: 0 records · Court records, filings, parcels and documents you collect, stored as published. · `python3 hi.py load <file.jsonl>   (format: README.md, Add your records)`
- [x] Franchise Disclosure Document layout: 23 of 23 items · The 23 items 16 C.F.R. § 436.5 requires, read from the rule itself.
- [ ] ○ Court dockets (Judiciary, eCourt Kokua): cases: counted when collected · Published by the Hawaii State Judiciary.
- [ ] ○ Real property records: Honolulu: parcels: counted when collected · https://www.qpublic.net/hi/honolulu/
- [ ] ○ Real property records: Hawaii, Maui and Kauai counties: parcels: counted when collected · Published by each county.
- [ ] ○ Land records: Bureau of Conveyances: documents: counted when collected · https://dlnr.hawaii.gov/boc/
- [ ] ○ Business registrations (DCCA Business Registration Division): entities: counted when collected · Published by the Department of Commerce and Consumer Affairs.


## United States  (3 of 35 checked off)
### Here now  (3 of 4 checked off)
- [x] U.S. Constitution: 74 of 74 sections · file: us_federal_constitutions.parquet
- [x] United States Code: 60,667 of 60,667 sections · file: us_federal_statutes.parquet
- [x] Federal court rules: 1,130 of 1,130 sections · file: us_federal_court_rules.parquet
- [ ] ◐ Code of Federal Regulations: 11 of 342,351 sections · Only 16 C.F.R. Part 436 (the FTC Franchise Rule) so far. Add a part with one line in sources.json (cfr_slices), then python3 fetch.py and python3 build.py. · file: us_federal_regulations.parquet

### In the open dataset, not pulled yet  (0 of 30 checked off)
Each is one file of the open dataset. They are pulled the way the files above were: sources.json, then fetch.py and build.py.

- [ ] ↓ Agency adjudications: 1,371 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_adjudication.parquet
- [ ] ↓ Administrative guidance: 10 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_administrative_guidance.parquet
- [ ] ↓ Board of Immigration Appeals precedent decisions: 3,292 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_bia_precedent_decision.parquet
- [ ] ↓ Board decisions: 66,594 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_board_decision.parquet
- [ ] ↓ CFPB enforcement actions: 386 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_cfpb_enforcement_action.parquet
- [ ] ↓ Code of Federal Regulations, annual edition: 886,066 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_cfr_annual.parquet
- [ ] ↓ Enforcement actions: 146 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_enforcement_action.parquet
- [ ] ↓ Executive orders: 737 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_executive_order.parquet
- [ ] ↓ Agency FAQs: 1,990 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_faq.parquet
- [ ] ↓ FTC administrative decisions: 17,973 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_ftc_administrative_decision.parquet
- [ ] ↓ Agency guidance: 40,692 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_guidance.parquet
- [ ] ↓ Guidelines: 1,281 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_guideline.parquet
- [ ] ↓ IRS announcements: 83 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_irs_announcement.parquet
- [ ] ↓ IRS notices: 769 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_irs_notice.parquet
- [ ] ↓ IRS revenue procedures: 378 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_irs_rev_proc.parquet
- [ ] ↓ IRS revenue rulings: 248 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_irs_rev_rul.parquet
- [ ] ↓ IRS written determinations: 45,368 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_irs_written_determination.parquet
- [ ] ↓ Memoranda: 401 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_memorandum.parquet
- [ ] ↓ Merit Systems Protection Board decisions: 5,461 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_mspb_decision.parquet
- [ ] ↓ Notices: 17,633 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_notice.parquet
- [ ] ↓ Presidential documents: 639 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_presidential_document.parquet
- [ ] ↓ Private laws: 49,460 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_private_law.parquet
- [ ] ↓ Proclamations: 1,833 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_proclamation.parquet
- [ ] ↓ Proposed regulations: 76,865 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_proposed_regulation.parquet
- [ ] ↓ Resolutions: 406 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_resolution.parquet
- [ ] ↓ Rulings: 7,278 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_ruling.parquet
- [ ] ↓ SEC adjudications: 5,790 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_sec_adjudication.parquet
- [ ] ↓ Session laws: 375,967 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_session_law.parquet
- [ ] ↓ Statute compilations: 80,288 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_statute_compilation.parquet
- [ ] ↓ Treaties: 1,243 sections published · https://oss-data-us.vaquill.ai/index.html · file: us_federal_treaty.parquet

- [ ] ○ Federal court opinions (Supreme Court, Ninth Circuit, District of Hawaii): opinions: counted when collected · Not in the open dataset. · https://www.courtlistener.com/

## Other states and territories  (0 of 269 checked off)
Everything the open dataset holds for each jurisdiction. Not pulled yet.

### Alabama  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 11,926 sections published · file: us_al_ag_opinion.parquet
- [ ] ↓ Constitution: 381 sections published · file: us_al_constitutions.parquet
- [ ] ↓ Court rules: 870 sections published · file: us_al_court_rules.parquet
- [ ] ↓ Agency guidance: 207 sections published · file: us_al_guidance.parquet
- [ ] ↓ Regulations: 18,864 sections published · file: us_al_regulations.parquet
- [ ] ↓ Statutes: 46,614 sections published · file: us_al_statutes.parquet

### Alaska  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 532 sections published · file: us_ak_ag_opinion.parquet
- [ ] ↓ Constitution: 238 sections published · file: us_ak_constitutions.parquet
- [ ] ↓ Court rules: 763 sections published · file: us_ak_court_rules.parquet
- [ ] ↓ Agency guidance: 398 sections published · file: us_ak_guidance.parquet
- [ ] ↓ Regulations: 25,717 sections published · file: us_ak_regulations.parquet
- [ ] ↓ Statutes: 17,935 sections published · file: us_ak_statutes.parquet

### Arizona  (0 of 4 checked off)
- [ ] ↓ Attorney General opinions: 147 sections published · file: us_az_ag_opinion.parquet
- [ ] ↓ Constitution: 323 sections published · file: us_az_constitutions.parquet
- [ ] ↓ Agency guidance: 235 sections published · file: us_az_guidance.parquet
- [ ] ↓ Statutes: 24,956 sections published · file: us_az_statutes.parquet

### Arkansas  (0 of 5 checked off)
- [ ] ↓ Attorney General opinions: 10,292 sections published · file: us_ar_ag_opinion.parquet
- [ ] ↓ Constitution: 493 sections published · file: us_ar_constitutions.parquet
- [ ] ↓ Court rules: 774 sections published · file: us_ar_court_rules.parquet
- [ ] ↓ Agency guidance: 359 sections published · file: us_ar_guidance.parquet
- [ ] ↓ Regulations: 22,392 sections published · file: us_ar_regulations.parquet

### California  (0 of 5 checked off)
- [ ] ↓ Attorney General opinions: 1,962 sections published · file: us_ca_ag_opinion.parquet
- [ ] ↓ Constitution: 372 sections published · file: us_ca_constitutions.parquet
- [ ] ↓ Court rules: 1,521 sections published · file: us_ca_court_rules.parquet
- [ ] ↓ Agency guidance: 464 sections published · file: us_ca_guidance.parquet
- [ ] ↓ Statutes: 161,428 sections published · file: us_ca_statutes.parquet

### Colorado  (0 of 3 checked off)
- [ ] ↓ Attorney General opinions: 109 sections published · file: us_co_ag_opinion.parquet
- [ ] ↓ Court rules: 1,194 sections published · file: us_co_court_rules.parquet
- [ ] ↓ Regulations: 1,155 sections published · file: us_co_regulations.parquet

### Connecticut  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 626 sections published · file: us_ct_ag_opinion.parquet
- [ ] ↓ Constitution: 146 sections published · file: us_ct_constitutions.parquet
- [ ] ↓ Court rules: 1,724 sections published · file: us_ct_court_rules.parquet
- [ ] ↓ Agency guidance: 369 sections published · file: us_ct_guidance.parquet
- [ ] ↓ Regulations: 24,331 sections published · file: us_ct_regulations.parquet
- [ ] ↓ Statutes: 16,082 sections published · file: us_ct_statutes.parquet

### Delaware  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 843 sections published · file: us_de_ag_opinion.parquet
- [ ] ↓ Constitution: 207 sections published · file: us_de_constitutions.parquet
- [ ] ↓ Court rules: 1,385 sections published · file: us_de_court_rules.parquet
- [ ] ↓ Agency guidance: 303 sections published · file: us_de_guidance.parquet
- [ ] ↓ Regulations: 1,164 sections published · file: us_de_regulations.parquet
- [ ] ↓ Statutes: 22,669 sections published · file: us_de_statutes.parquet

### District of Columbia  (0 of 6 checked off)
- [ ] ↓ Administrative guidance: 1 sections published · file: us_dc_administrative_guidance.parquet
- [ ] ↓ Attorney General opinions: 37 sections published · file: us_dc_ag_opinion.parquet
- [ ] ↓ Court rules: 1,128 sections published · file: us_dc_court_rules.parquet
- [ ] ↓ Agency guidance: 27 sections published · file: us_dc_guidance.parquet
- [ ] ↓ Regulations: 27,401 sections published · file: us_dc_regulations.parquet
- [ ] ↓ Statutes: 24,036 sections published · file: us_dc_statutes.parquet

### Florida  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 20,960 sections published · file: us_fl_ag_opinion.parquet
- [ ] ↓ Constitution: 213 sections published · file: us_fl_constitutions.parquet
- [ ] ↓ Court rules: 943 sections published · file: us_fl_court_rules.parquet
- [ ] ↓ Agency guidance: 100 sections published · file: us_fl_guidance.parquet
- [ ] ↓ Regulations: 28,913 sections published · file: us_fl_regulations.parquet
- [ ] ↓ Statutes: 25,020 sections published · file: us_fl_statutes.parquet

### Georgia  (0 of 5 checked off)
- [ ] ↓ Attorney General opinions: 525 sections published · file: us_ga_ag_opinion.parquet
- [ ] ↓ Constitution: 287 sections published · file: us_ga_constitutions.parquet
- [ ] ↓ Court rules: 1,174 sections published · file: us_ga_court_rules.parquet
- [ ] ↓ Agency guidance: 66 sections published · file: us_ga_guidance.parquet
- [ ] ↓ Regulations: 19,691 sections published · file: us_ga_regulations.parquet

### Idaho  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 151 sections published · file: us_id_ag_opinion.parquet
- [ ] ↓ Constitution: 234 sections published · file: us_id_constitutions.parquet
- [ ] ↓ Court rules: 766 sections published · file: us_id_court_rules.parquet
- [ ] ↓ Agency guidance: 75 sections published · file: us_id_guidance.parquet
- [ ] ↓ Regulations: 8,672 sections published · file: us_id_regulations.parquet
- [ ] ↓ Statutes: 22,754 sections published · file: us_id_statutes.parquet

### Illinois  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 1,451 sections published · file: us_il_ag_opinion.parquet
- [ ] ↓ Constitution: 140 sections published · file: us_il_constitutions.parquet
- [ ] ↓ Court rules: 426 sections published · file: us_il_court_rules.parquet
- [ ] ↓ Agency guidance: 159 sections published · file: us_il_guidance.parquet
- [ ] ↓ Regulations: 55,076 sections published · file: us_il_regulations.parquet
- [ ] ↓ Statutes: 72,251 sections published · file: us_il_statutes.parquet

### Indiana  (0 of 5 checked off)
- [ ] ↓ Attorney General opinions: 9,760 sections published · file: us_in_ag_opinion.parquet
- [ ] ↓ Constitution: 195 sections published · file: us_in_constitutions.parquet
- [ ] ↓ Court rules: 879 sections published · file: us_in_court_rules.parquet
- [ ] ↓ Agency guidance: 282 sections published · file: us_in_guidance.parquet
- [ ] ↓ Statutes: 83,148 sections published · file: us_in_statutes.parquet

### Iowa  (0 of 5 checked off)
- [ ] ↓ Constitution: 190 sections published · file: us_ia_constitutions.parquet
- [ ] ↓ Court rules: 1,294 sections published · file: us_ia_court_rules.parquet
- [ ] ↓ Agency guidance: 83 sections published · file: us_ia_guidance.parquet
- [ ] ↓ Regulations: 27,587 sections published · file: us_ia_regulations.parquet
- [ ] ↓ Statutes: 28,223 sections published · file: us_ia_statutes.parquet

### Kansas  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 56 sections published · file: us_ks_ag_opinion.parquet
- [ ] ↓ Constitution: 213 sections published · file: us_ks_constitutions.parquet
- [ ] ↓ Court rules: 436 sections published · file: us_ks_court_rules.parquet
- [ ] ↓ Agency guidance: 79 sections published · file: us_ks_guidance.parquet
- [ ] ↓ Regulations: 18,848 sections published · file: us_ks_regulations.parquet
- [ ] ↓ Statutes: 24,361 sections published · file: us_ks_statutes.parquet

### Kentucky  (0 of 5 checked off)
- [ ] ↓ Attorney General opinions: 692 sections published · file: us_ky_ag_opinion.parquet
- [ ] ↓ Constitution: 274 sections published · file: us_ky_constitutions.parquet
- [ ] ↓ Agency guidance: 231 sections published · file: us_ky_guidance.parquet
- [ ] ↓ Regulations: 4,780 sections published · file: us_ky_regulations.parquet
- [ ] ↓ Statutes: 21,194 sections published · file: us_ky_statutes.parquet

### Louisiana  (0 of 4 checked off)
- [ ] ↓ Attorney General opinions: 3,718 sections published · file: us_la_ag_opinion.parquet
- [ ] ↓ Constitution: 326 sections published · file: us_la_constitutions.parquet
- [ ] ↓ Court rules: 481 sections published · file: us_la_court_rules.parquet
- [ ] ↓ Statutes: 43,213 sections published · file: us_la_statutes.parquet

### Maine  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 832 sections published · file: us_me_ag_opinion.parquet
- [ ] ↓ Constitution: 153 sections published · file: us_me_constitutions.parquet
- [ ] ↓ Court rules: 721 sections published · file: us_me_court_rules.parquet
- [ ] ↓ Agency guidance: 228 sections published · file: us_me_guidance.parquet
- [ ] ↓ Regulations: 1,717 sections published · file: us_me_regulations.parquet
- [ ] ↓ Statutes: 25,316 sections published · file: us_me_statutes.parquet

### Maryland  (0 of 5 checked off)
- [ ] ↓ Attorney General opinions: 601 sections published · file: us_md_ag_opinion.parquet
- [ ] ↓ Constitution: 303 sections published · file: us_md_constitutions.parquet
- [ ] ↓ Agency guidance: 677 sections published · file: us_md_guidance.parquet
- [ ] ↓ Regulations: 12,773 sections published · file: us_md_regulations.parquet
- [ ] ↓ Statutes: 39,552 sections published · file: us_md_statutes.parquet

### Massachusetts  (0 of 5 checked off)
- [ ] ↓ Attorney General opinions: 529 sections published · file: us_ma_ag_opinion.parquet
- [ ] ↓ Constitution: 100 sections published · file: us_ma_constitutions.parquet
- [ ] ↓ Court rules: 972 sections published · file: us_ma_court_rules.parquet
- [ ] ↓ Agency guidance: 417 sections published · file: us_ma_guidance.parquet
- [ ] ↓ Statutes: 23,144 sections published · file: us_ma_statutes.parquet

### Michigan  (0 of 5 checked off)
- [ ] ↓ Constitution: 275 sections published · file: us_mi_constitutions.parquet
- [ ] ↓ Court rules: 1,025 sections published · file: us_mi_court_rules.parquet
- [ ] ↓ Agency guidance: 151 sections published · file: us_mi_guidance.parquet
- [ ] ↓ Regulations: 22,154 sections published · file: us_mi_regulations.parquet
- [ ] ↓ Statutes: 42,355 sections published · file: us_mi_statutes.parquet

### Minnesota  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 77 sections published · file: us_mn_ag_opinion.parquet
- [ ] ↓ Constitution: 137 sections published · file: us_mn_constitutions.parquet
- [ ] ↓ Court rules: 958 sections published · file: us_mn_court_rules.parquet
- [ ] ↓ Agency guidance: 35 sections published · file: us_mn_guidance.parquet
- [ ] ↓ Regulations: 15,401 sections published · file: us_mn_regulations.parquet
- [ ] ↓ Statutes: 27,747 sections published · file: us_mn_statutes.parquet

### Mississippi  (0 of 5 checked off)
- [ ] ↓ Attorney General opinions: 524 sections published · file: us_ms_ag_opinion.parquet
- [ ] ↓ Constitution: 298 sections published · file: us_ms_constitutions.parquet
- [ ] ↓ Court rules: 794 sections published · file: us_ms_court_rules.parquet
- [ ] ↓ Agency guidance: 240 sections published · file: us_ms_guidance.parquet
- [ ] ↓ Regulations: 21,270 sections published · file: us_ms_regulations.parquet

### Missouri  (0 of 4 checked off)
- [ ] ↓ Attorney General opinions: 8,449 sections published · file: us_mo_ag_opinion.parquet
- [ ] ↓ Constitution: 402 sections published · file: us_mo_constitutions.parquet
- [ ] ↓ Agency guidance: 106 sections published · file: us_mo_guidance.parquet
- [ ] ↓ Statutes: 29,363 sections published · file: us_mo_statutes.parquet

### Montana  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 3,527 sections published · file: us_mt_ag_opinion.parquet
- [ ] ↓ Constitution: 161 sections published · file: us_mt_constitutions.parquet
- [ ] ↓ Court rules: 238 sections published · file: us_mt_court_rules.parquet
- [ ] ↓ Agency guidance: 149 sections published · file: us_mt_guidance.parquet
- [ ] ↓ Regulations: 50,009 sections published · file: us_mt_regulations.parquet
- [ ] ↓ Statutes: 30,515 sections published · file: us_mt_statutes.parquet

### Nebraska  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 1,191 sections published · file: us_ne_ag_opinion.parquet
- [ ] ↓ Constitution: 208 sections published · file: us_ne_constitutions.parquet
- [ ] ↓ Court rules: 734 sections published · file: us_ne_court_rules.parquet
- [ ] ↓ Agency guidance: 120 sections published · file: us_ne_guidance.parquet
- [ ] ↓ Regulations: 13,545 sections published · file: us_ne_regulations.parquet
- [ ] ↓ Statutes: 28,502 sections published · file: us_ne_statutes.parquet

### Nevada  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 41 sections published · file: us_nv_ag_opinion.parquet
- [ ] ↓ Constitution: 233 sections published · file: us_nv_constitutions.parquet
- [ ] ↓ Court rules: 1,340 sections published · file: us_nv_court_rules.parquet
- [ ] ↓ Agency guidance: 200 sections published · file: us_nv_guidance.parquet
- [ ] ↓ Regulations: 30,978 sections published · file: us_nv_regulations.parquet
- [ ] ↓ Statutes: 49,745 sections published · file: us_nv_statutes.parquet

### New Hampshire  (0 of 5 checked off)
- [ ] ↓ Constitution: 156 sections published · file: us_nh_constitutions.parquet
- [ ] ↓ Court rules: 972 sections published · file: us_nh_court_rules.parquet
- [ ] ↓ Agency guidance: 178 sections published · file: us_nh_guidance.parquet
- [ ] ↓ Regulations: 38,515 sections published · file: us_nh_regulations.parquet
- [ ] ↓ Statutes: 25,375 sections published · file: us_nh_statutes.parquet

### New Jersey  (0 of 5 checked off)
- [ ] ↓ Attorney General opinions: 16 sections published · file: us_nj_ag_opinion.parquet
- [ ] ↓ Constitution: 205 sections published · file: us_nj_constitutions.parquet
- [ ] ↓ Court rules: 1,685 sections published · file: us_nj_court_rules.parquet
- [ ] ↓ Agency guidance: 523 sections published · file: us_nj_guidance.parquet
- [ ] ↓ Statutes: 55,048 sections published · file: us_nj_statutes.parquet

### New Mexico  (0 of 5 checked off)
- [ ] ↓ Constitution: 265 sections published · file: us_nm_constitutions.parquet
- [ ] ↓ Court rules: 3,462 sections published · file: us_nm_court_rules.parquet
- [ ] ↓ Agency guidance: 275 sections published · file: us_nm_guidance.parquet
- [ ] ↓ Regulations: 36,339 sections published · file: us_nm_regulations.parquet
- [ ] ↓ Statutes: 31,115 sections published · file: us_nm_statutes.parquet

### New York  (0 of 5 checked off)
- [ ] ↓ Attorney General opinions: 536 sections published · file: us_ny_ag_opinion.parquet
- [ ] ↓ Constitution: 202 sections published · file: us_ny_constitutions.parquet
- [ ] ↓ Court rules: 1,088 sections published · file: us_ny_court_rules.parquet
- [ ] ↓ Agency guidance: 1,200 sections published · file: us_ny_guidance.parquet
- [ ] ↓ Statutes: 40,162 sections published · file: us_ny_statutes.parquet

### North Carolina  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 1,106 sections published · file: us_nc_ag_opinion.parquet
- [ ] ↓ Constitution: 155 sections published · file: us_nc_constitutions.parquet
- [ ] ↓ Court rules: 495 sections published · file: us_nc_court_rules.parquet
- [ ] ↓ Agency guidance: 117 sections published · file: us_nc_guidance.parquet
- [ ] ↓ Regulations: 45,826 sections published · file: us_nc_regulations.parquet
- [ ] ↓ Statutes: 41,290 sections published · file: us_nc_statutes.parquet

### North Dakota  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 5,550 sections published · file: us_nd_ag_opinion.parquet
- [ ] ↓ Constitution: 203 sections published · file: us_nd_constitutions.parquet
- [ ] ↓ Court rules: 2,261 sections published · file: us_nd_court_rules.parquet
- [ ] ↓ Agency guidance: 235 sections published · file: us_nd_guidance.parquet
- [ ] ↓ Regulations: 14,343 sections published · file: us_nd_regulations.parquet
- [ ] ↓ Statutes: 29,042 sections published · file: us_nd_statutes.parquet

### Ohio  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 1,406 sections published · file: us_oh_ag_opinion.parquet
- [ ] ↓ Constitution: 226 sections published · file: us_oh_constitutions.parquet
- [ ] ↓ Court rules: 1,167 sections published · file: us_oh_court_rules.parquet
- [ ] ↓ Agency guidance: 111 sections published · file: us_oh_guidance.parquet
- [ ] ↓ Regulations: 19,407 sections published · file: us_oh_regulations.parquet
- [ ] ↓ Statutes: 33,158 sections published · file: us_oh_statutes.parquet

### Oklahoma  (0 of 5 checked off)
- [ ] ↓ Attorney General opinions: 3,052 sections published · file: us_ok_ag_opinion.parquet
- [ ] ↓ Constitution: 456 sections published · file: us_ok_constitutions.parquet
- [ ] ↓ Agency guidance: 144 sections published · file: us_ok_guidance.parquet
- [ ] ↓ Regulations: 19,594 sections published · file: us_ok_regulations.parquet
- [ ] ↓ Statutes: 35,330 sections published · file: us_ok_statutes.parquet

### Oregon  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 114 sections published · file: us_or_ag_opinion.parquet
- [ ] ↓ Constitution: 384 sections published · file: us_or_constitutions.parquet
- [ ] ↓ Court rules: 605 sections published · file: us_or_court_rules.parquet
- [ ] ↓ Agency guidance: 103 sections published · file: us_or_guidance.parquet
- [ ] ↓ Regulations: 40,870 sections published · file: us_or_regulations.parquet
- [ ] ↓ Statutes: 72,664 sections published · file: us_or_statutes.parquet

### Pennsylvania  (0 of 5 checked off)
- [ ] ↓ Attorney General opinions: 653 sections published · file: us_pa_ag_opinion.parquet
- [ ] ↓ Constitution: 186 sections published · file: us_pa_constitutions.parquet
- [ ] ↓ Court rules: 2,641 sections published · file: us_pa_court_rules.parquet
- [ ] ↓ Regulations: 48,233 sections published · file: us_pa_regulations.parquet
- [ ] ↓ Statutes: 14,617 sections published · file: us_pa_statutes.parquet

### Puerto Rico  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 81 sections published · file: us_pr_ag_opinion.parquet
- [ ] ↓ Constitution: 102 sections published · file: us_pr_constitutions.parquet
- [ ] ↓ Court rules: 1,528 sections published · file: us_pr_court_rules.parquet
- [ ] ↓ Agency guidance: 1,641 sections published · file: us_pr_guidance.parquet
- [ ] ↓ Regulations: 126,853 sections published · file: us_pr_regulations.parquet
- [ ] ↓ Statutes: 24,763 sections published · file: us_pr_statutes.parquet

### Rhode Island  (0 of 4 checked off)
- [ ] ↓ Constitution: 118 sections published · file: us_ri_constitutions.parquet
- [ ] ↓ Court rules: 1,032 sections published · file: us_ri_court_rules.parquet
- [ ] ↓ Agency guidance: 134 sections published · file: us_ri_guidance.parquet
- [ ] ↓ Statutes: 21,107 sections published · file: us_ri_statutes.parquet

### South Carolina  (0 of 5 checked off)
- [ ] ↓ Constitution: 178 sections published · file: us_sc_constitutions.parquet
- [ ] ↓ Court rules: 557 sections published · file: us_sc_court_rules.parquet
- [ ] ↓ Agency guidance: 319 sections published · file: us_sc_guidance.parquet
- [ ] ↓ Regulations: 6,189 sections published · file: us_sc_regulations.parquet
- [ ] ↓ Statutes: 30,489 sections published · file: us_sc_statutes.parquet

### South Dakota  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 1,652 sections published · file: us_sd_ag_opinion.parquet
- [ ] ↓ Constitution: 270 sections published · file: us_sd_constitutions.parquet
- [ ] ↓ Court rules: 155 sections published · file: us_sd_court_rules.parquet
- [ ] ↓ Agency guidance: 27 sections published · file: us_sd_guidance.parquet
- [ ] ↓ Regulations: 29,000 sections published · file: us_sd_regulations.parquet
- [ ] ↓ Statutes: 39,589 sections published · file: us_sd_statutes.parquet

### Tennessee  (0 of 4 checked off)
- [ ] ↓ Attorney General opinions: 2,651 sections published · file: us_tn_ag_opinion.parquet
- [ ] ↓ Constitution: 151 sections published · file: us_tn_constitutions.parquet
- [ ] ↓ Court rules: 626 sections published · file: us_tn_court_rules.parquet
- [ ] ↓ Agency guidance: 173 sections published · file: us_tn_guidance.parquet

### Texas  (0 of 5 checked off)
- [ ] ↓ Attorney General opinions: 3,502 sections published · file: us_tx_ag_opinion.parquet
- [ ] ↓ Constitution: 503 sections published · file: us_tx_constitutions.parquet
- [ ] ↓ Court rules: 1,050 sections published · file: us_tx_court_rules.parquet
- [ ] ↓ Agency guidance: 1,284 sections published · file: us_tx_guidance.parquet
- [ ] ↓ Statutes: 122,630 sections published · file: us_tx_statutes.parquet

### Utah  (0 of 5 checked off)
- [ ] ↓ Constitution: 189 sections published · file: us_ut_constitutions.parquet
- [ ] ↓ Court rules: 919 sections published · file: us_ut_court_rules.parquet
- [ ] ↓ Agency guidance: 168 sections published · file: us_ut_guidance.parquet
- [ ] ↓ Regulations: 19,949 sections published · file: us_ut_regulations.parquet
- [ ] ↓ Statutes: 27,556 sections published · file: us_ut_statutes.parquet

### Vermont  (0 of 4 checked off)
- [ ] ↓ Attorney General opinions: 16 sections published · file: us_vt_ag_opinion.parquet
- [ ] ↓ Constitution: 98 sections published · file: us_vt_constitutions.parquet
- [ ] ↓ Agency guidance: 214 sections published · file: us_vt_guidance.parquet
- [ ] ↓ Statutes: 23,521 sections published · file: us_vt_statutes.parquet

### Virginia  (0 of 5 checked off)
- [ ] ↓ Constitution: 130 sections published · file: us_va_constitutions.parquet
- [ ] ↓ Court rules: 358 sections published · file: us_va_court_rules.parquet
- [ ] ↓ Agency guidance: 89 sections published · file: us_va_guidance.parquet
- [ ] ↓ Regulations: 22,396 sections published · file: us_va_regulations.parquet
- [ ] ↓ Statutes: 33,861 sections published · file: us_va_statutes.parquet

### Washington  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 4,430 sections published · file: us_wa_ag_opinion.parquet
- [ ] ↓ Constitution: 270 sections published · file: us_wa_constitutions.parquet
- [ ] ↓ Court rules: 1,183 sections published · file: us_wa_court_rules.parquet
- [ ] ↓ Agency guidance: 24 sections published · file: us_wa_guidance.parquet
- [ ] ↓ Regulations: 51,026 sections published · file: us_wa_regulations.parquet
- [ ] ↓ Statutes: 52,002 sections published · file: us_wa_statutes.parquet

### West Virginia  (0 of 6 checked off)
- [ ] ↓ Attorney General opinions: 151 sections published · file: us_wv_ag_opinion.parquet
- [ ] ↓ Constitution: 204 sections published · file: us_wv_constitutions.parquet
- [ ] ↓ Court rules: 1,116 sections published · file: us_wv_court_rules.parquet
- [ ] ↓ Agency guidance: 174 sections published · file: us_wv_guidance.parquet
- [ ] ↓ Regulations: 39,372 sections published · file: us_wv_regulations.parquet
- [ ] ↓ Statutes: 25,664 sections published · file: us_wv_statutes.parquet

### Wisconsin  (0 of 5 checked off)
- [ ] ↓ Constitution: 161 sections published · file: us_wi_constitutions.parquet
- [ ] ↓ Court rules: 395 sections published · file: us_wi_court_rules.parquet
- [ ] ↓ Agency guidance: 232 sections published · file: us_wi_guidance.parquet
- [ ] ↓ Regulations: 17,882 sections published · file: us_wi_regulations.parquet
- [ ] ↓ Statutes: 18,158 sections published · file: us_wi_statutes.parquet

### Wyoming  (0 of 5 checked off)
- [ ] ↓ Constitution: 316 sections published · file: us_wy_constitutions.parquet
- [ ] ↓ Court rules: 1,020 sections published · file: us_wy_court_rules.parquet
- [ ] ↓ Agency guidance: 62 sections published · file: us_wy_guidance.parquet
- [ ] ↓ Regulations: 13,348 sections published · file: us_wy_regulations.parquet
- [ ] ↓ Statutes: 20,995 sections published · file: us_wy_statutes.parquet


